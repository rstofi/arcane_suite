"""A quick-and-dirty code to process pre-flagged OTF snapshots
(created by the otfms pipeline). This is a 'master' script to call the
`OTF_imaging_and_selfcal_worker.py` script on several OTF snapshot MS' and optionally
call them via slurm.

The code *should* be readable, but some comments are added nonetheless.

Author: K. Rozgonyi (rstofi@gmail.com)
License: GNU GPLv3
"""

import os
import configparser
import argparse
import numpy as np
import shutil
import fileinput
import subprocess
import time

# === Functions ===
def get_masters_args() -> dict:
    """
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c',
        '--config_file',
        required=True,
        help='Configuration file',
        action='store',
        type=str)

    args = parser.parse_args()

    return args.__dict__

def get_masters_params(append_master_cfg_path=False) -> dict:
    """
    """
    dict_args = get_masters_args()
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(dict_args['config_file'])

    config_params = dict(config.items('setup'))

    if append_master_cfg_path:
        config_params['master_cfg_path'] = dict_args['config_file']

    return config_params

def get_targets() -> np.ndarray:
    """
    """
    dict_args = get_masters_args()
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(dict_args['config_file'])

    targets = []

    path_items = config.items('targets')
    
    for key, target in path_items:
        targets.append(target)

    return np.array(targets)

def overwrite_line_in_slurm_script(script_path:str,
                        param_string:str,
                        new_param_string:str) -> int:
    """
    """
    for line in fileinput.input(script_path, inplace = 1): 
        if param_string in line:
            line = line[0:line.rfind(param_string) + len(param_string)] + new_param_string + os.linesep
        print(line, end='')

    return 0

def prepare_dir(dir_path:str, remove_only=False) -> int:
    """
    """
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

    if not remove_only:
        os.makedirs(dir_path)

    return 0

def populate_slurm_script(slurm_script_path:str,
                        worker_script_path:str,
                        worker_config_path:str,
                        worker_name:str) -> int:
    """
    """

    params_list = ['worker=','cfg=','#SBATCH --job-name=']
    new_params_list = [worker_script_path, worker_config_path, worker_name]

    for p, n_p in zip(params_list,new_params_list):
        overwrite_line_in_slutm_script(slurm_script_path,p,n_p,no_spaces=True)

    return 0


def configure_worker_slurm_backend(worker_output_dir_path:str,
                                    slurm_template_config:str,
                                    worker_script_path:str,
                                    worker_config_path:str,
                                    worker_run_dir_path:str,
                                    worker_target:str,
                                    skip_source_finding:str) -> int:
    """
    The slurm config file needs to have the following minimal structure:

    ```
    #SLURM commands uniform for all workers
    #SBATCH --job-name='job'

    worker=''
    cfg=''
    output_dir=''
    run_dir=''
    target=''

    #Assuming python is > v3.6
    python ${worker} -c ${cfg} -o {output_dir} -r {run_dir} -t {target}
    ```

    The code updates the job name and the worker parameters.
    """
    custom_slurm_script = os.path.join(worker_output_dir_path,'srun_worker.sh')

    shutil.copyfile(slurm_template_config,custom_slurm_script)

    #Populate the slurm script with params
    params_list = ['worker=', 'cfg=', 'output_dir=',
                    'run_dir=', 'target=', '#SBATCH --job-name=']
    
    new_params_list = [worker_script_path,
                        worker_config_path,
                        worker_output_dir_path,
                        worker_run_dir_path,
                        worker_target,
                        'worker_{0:s}'.format(worker_target)]

    for p, n_p in zip(params_list,new_params_list):
        overwrite_line_in_slurm_script(custom_slurm_script,p,n_p)

    #Skip source finding
    if skip_source_finding.lower() == 'true':
        for line in fileinput.input(custom_slurm_script, inplace = 1): 
            if 'python ' in line:
                if '-ssf' not in line:
                    line = line.rstrip() + ' -ssf' + os.linesep
            print(line, end='')

    return 0

def overwrite_target_list_in_cfg(cfg_path:str,
                                new_ids:list,
                                new_targets:list) -> int:
    """
    """
    config = configparser.ConfigParser()
    
    with open(os.path.abspath(cfg_path), 'r') as f:
        config.read_file(f)

    config.remove_section('targets')

    config.add_section('targets')

    for target_id, target_name in zip(new_ids, new_targets):
        config.set('targets', str(target_id), target_name)

    with open(os.path.abspath(cfg_path), 'w') as f:
        config.write(f)

    return 0


def generate_fields_from_otfms(master_config_file:str,
                                worker_template_cfg:str) -> int:
    """
    This script runs on the output from the `otfms` pipeline.

    NOTE: the script currently only supports when the `ski_merge` parameter is set
        False

    TO DO: enable integration without the final merging in the `otfms` pipeline

    As such, this function assumes that the `otfms` pipeline created a file called
    `otf_field_names.dat` under its rsults/ dir, which path is given as the `ms_dir` param in the worker
    config template!

    """
    tw_config = configparser.ConfigParser(allow_no_value=True)
    tw_config.read(worker_template_cfg)

    otfms_output_dir_path = dict(tw_config.items('params'))['ms_dir_path']

    otfms_filed_names_file_path = os.path.join(otfms_output_dir_path,'otf_field_names.dat')

    otfms_ids = np.loadtxt(otfms_filed_names_file_path, usecols=0, dtype=int, comments='#')
    otfms_names = np.loadtxt(otfms_filed_names_file_path, usecols=1, dtype=str, comments='#')

    overwrite_target_list_in_cfg(master_config_file,
                                otfms_ids,
                                otfms_names)

    return 0

# === MAIN ===
if __name__ == "__main__":
    config_params = get_masters_params(append_master_cfg_path=True)

    if config_params['generate_targets_from_otfms'].lower() == 'true':
        generate_fields_from_otfms(config_params['master_cfg_path'],
                                    config_params['worker_template_cfg'])

    targets = get_targets()

    if not os.path.exists(config_params['master_output_dir_path']):
        os.mkdir(config_params['master_output_dir_path'])

    use_slurm_backend = False
    if config_params['slurm_backend'].lower() == 'true':
        use_slurm_backend = True

    for worker_target in targets:
        worker_output_dir_path = os.path.join(config_params['master_output_dir_path'],
                                        worker_target)
        
        worker_run_dir_path = os.path.join(worker_output_dir_path,'caracal_run')

        prepare_dir(worker_output_dir_path)

        #Submitting slurm jobs
        if use_slurm_backend:
            configure_worker_slurm_backend(worker_output_dir_path,
                                            config_params['slurm_template'],
                                            config_params['worker_script'],
                                            config_params['worker_template_cfg'],
                                            worker_run_dir_path,
                                            worker_target,
                                            config_params['skip_source_finding'])

            crs = "echo 'sbatch {0:s}'".format(os.path.join(worker_output_dir_path,
                                                             'srun_worker.sh'))
        
        #Serial run
        else:
            if config_params['skip_source_finding'].lower() == 'true':
                crs = "python {0:s} -c {1:s} -o {2:s} -r {3:s} -t {4:s} -ssf".format(
                        config_params['worker_script'],
                        config_params['worker_template_cfg'],
                        worker_output_dir_path,
                        worker_run_dir_path,
                        worker_target)
            else:
                crs = "python {0:s} -c {1:s} -o {2:s} -r {3:s} -t {4:s} -ssf".format(
                        config_params['worker_script'],
                        config_params['worker_template_cfg'],
                        worker_output_dir_path,
                        worker_run_dir_path,
                        worker_target)

        p = subprocess.run(crs, cwd=worker_output_dir_path, shell=True)

        #Not to overflow slurm submissions
        if use_slurm_backend:
            time.sleep(1) #Wait approx 1s between job submissions

    #TO DO: move main code to a function

    #TO DO: add option for source-finding only