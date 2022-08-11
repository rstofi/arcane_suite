"""The command line tool for the Snakemake rule: `split_otf_scans_by_pointing`
"""

import sys
import os
import logging
import argparse
import subprocess

from arcane_utils import pipeline
from arcane_utils import time as a_time

#=== Set logging
logger = pipeline.init_logger()

#=== Functions ===
def main():
    """Basically a custom wrapper around the casa task split, based on the OTF
    field ID and the corresponding time values read from the snakemake
    config.yaml file.

    Based ona the OTF `ID` and the +/- 1/2 * `split_timedelta` time range, the code
    selects visibilities around the time value corresponding to the ID in the
    config.yml file
    



    """
    #=== Set arguments
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config_file', required=True,
                    help='Snakemake yaml configuration file for the otfms pipeline',
                    action='store', type=str)

    parser.add_argument('-i', '--otf_id', required=True,
                    help='Snakemake yaml configuration file for the otfms pipeline',
                    action='store', type=str)

    #===========================================================================
    args = parser.parse_args() #Get the arguments

    logger.info("Running *split_otf_scans_by_pointing* with OTF_ID: {0:s}".format(args.otf_id))

    #Get parameters from the config.yaml file
    yaml_path = args.config_file

    MS = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'MS')

    output_otf_dir = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'output_otf_dir')

    split_timedelta = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'split_timedelta')

    otf_field_ID_mapping = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'otf_field_ID_mapping')    

    otf_pointing_time = otf_field_ID_mapping[args.otf_id]

    del otf_field_ID_mapping, yaml_path

    #Compute the selection range
    start_unix_time = otf_pointing_time - (split_timedelta * 0.5)
    end_unix_time = otf_pointing_time + (split_timedelta * 0.5)

    casa_timerange_selection_string = \
            a_time.convert_unix_times_to_casa_timerange_selection(start_unix_time,
                                                                    end_unix_time)

    logger.info('Set visibility selection: {0:s}'.format(
                                                casa_timerange_selection_string))

    casa_executable_path = os.path.join(output_otf_dir,'split_otf_pointing_no_{0:s}.py'.format(
                                                                    args.otf_id))

    logger.info('Creating casa executable at {0:s}'.format(casa_executable_path))

    output_MS = os.path.join(output_otf_dir,'otf_pointing_no_{0:s}.ms'.format(
                                                                    args.otf_id))

    split_task_string = "split(vis = '{0:s}',\n outputvis = '{1:s}',\
\n timerange = '{2:s}',\n datacolumn = 'all')".format(
                MS, output_MS,casa_timerange_selection_string)

    with open(casa_executable_path, 'w') as sconfig:
        sconfig.write(split_task_string)


    logger.info('Runnin CASA split task...')

    #create a run_casa.sh script
    casa_task_path = os.path.join(output_otf_dir,'split_otf_pointing_no_{0:s}.sh'.format(
                                                                    args.otf_id))
    with open(casa_task_path, 'w') as sconfig:
        sconfig.write('#!/bin/bash\n')
        sconfig.write("casa --log2term --nogui --nologfile --nocrashreport -c {0:s}".format(
                    casa_executable_path))

    #Running the split task

    casa_proc = subprocess.run("bash {0:s}".format(
                casa_task_path), shell=True, capture_output=True)

    #casa_proc = subprocess.run("casa --log2term --nogui --nologfile --nocrashreport -c {0:s}".format(
    #                casa_executable_path), shell=True, capture_output=True,
    #                executable='/bin/bash', env=env) #None of these help

    #casa_proc = subprocess.run(['/bin/bash', '-i', '-c', 'casa', '--log2term',
    #            '--nogui', '--nologfile', '--nocrashreport', '-c', '{0:s}'.format(
    #                casa_executable_path)], shell=True, capture_output=True,
    #                executable='/bin/bash', env=dict(os.environ)) #None of these help    

    out, err = casa_proc.stdout, casa_proc.stderr
    exitcode = casa_proc.returncode

    logger.info(out.decode('utf-8'))
    logger.info(err.decode('utf-8'))

    logger.info(exitcode)

    #Now remove the CASA executable
    logger.info('Cleaning up...')
    if os.path.isfile(casa_executable_path):
        os.remove(casa_executable_path)
    else:
        logger.warning('No CASA executable found...')

    logger.info('Cleaning up...')
    if os.path.isfile(casa_task_path):
        os.remove(casa_task_path)
    else:
        logger.warning('No CASA executable found...')

    #=== Exit
    logger.info('Single OTF pointing MS created')
    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()