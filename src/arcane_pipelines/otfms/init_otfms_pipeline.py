"""The command-line application initializing the `otfms` pipeline.
"""

import sys
import os
import shutil
import logging
import argparse
import gc
import datetime
import numpy as np

from arcane_utils import pipeline
from arcane_utils import ms_wrapper
from arcane_pipelines.otfms import otf_pointing

#=== Set logging
logger = logging.getLogger()

logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s -- %(levelname)s: %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

#Add logging from modules
utils_logger = logging.getLogger('arcane_utils')
utils_logger.setLevel(logging.INFO)

pipelines_logger = logging.getLogger('arcane_pipelines')
pipelines_logger.setLevel(logging.INFO)

#=== Functions ===
def main():
    """
    """
    #=== Set arguments
    #parser = argparse.ArgumentParser(description='Initialize the pipeline for converting \
#asynchronous OTF MS to a canonical MS format.')

    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config_file', required=True,
                    help='Required: Configuration file for the pipeline setup (not the Snakemake configuration file)',
                    action='store', type=str)

    parser.add_argument('-ca', '--clear_all', required=False,
                        help='If enabled, the working directory is overwritten completely',
                        action='store_true')

    parser.add_argument('-ol', '--overwrite_lock', required=False,
                        help='If enabled, the working directory is locked and only created if not existing',
                        action='store_true')

    #===========================================================================
    args = parser.parse_args() #Get the arguments

    logger.info('Building *otfms* pipeline from arcane-suite')

    #Check if the config file exists
    if not os.path.exists(args.config_file):
        raise FileNotFoundError('Input config file does not exists!')

    #=== Read the environment vales from the config file
    logger.info('Solving for environment...')

    working_dir = pipeline.get_common_env_variables(args.config_file)

    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    else:
        if args.overwrite_lock:
            raise FileExistsError('Specified directory {0:s} exists and overwrite lock is ON.'.format(
                    working_dir))
        elif args.clear_all:
            logger.warning('Cleaning *everything* from working directory {0:s}'.format(working_dir))
            shutil.rmtree(working_dir)
            os.mkdir(working_dir)
        else:
            logger.warning('Overwriting Sankefile and coinfig file under {0:s}'.format(working_dir))
            #Because the files under `working_dir` will be overwritten

    #Get the input data
    MS_path, pointing_ref_path = otf_pointing.get_otfms_data_variables(args.config_file)

    if not os.path.exists(MS_path):
        raise FileNotFoundError('Missing input MS directory {0:s}'.format(MS_path))

    if not os.path.exists(pointing_ref_path):
        raise FileNotFoundError('Missing input reference pointing file {0:s}'.format(pointing_ref_path))

    #Add checks here for the Snakefile if exists
    snakefile_path = os.path.join(os.path.dirname(sys.modules['arcane_pipelines.otfms'].__file__),
                                    'Snakefile')
 
    if not os.path.exists(snakefile_path):
        raise FileNotFoundError('Corrupted installation: Snakefile not found')

    output_snakefile_path = os.path.join(working_dir, 'Snakefile')

    #=== Read the data sub selection from the config file
    logger.info('Solving for OTF field initialization...')

    MS = ms_wrapper.create_MS_table_object(MS_path)

    calibrator_list, target_field_list, timerange, scans = \
                    otf_pointing.get_data_selection_from_config(args.config_file)

    #Check if calibrator and target fields are in the MS
    field_Name_ID_dict = ms_wrapper.get_fieldname_and_ID_list_dict_from_MS(MS, close=False)

    for calibrator in calibrator_list:
        if calibrator not in field_Name_ID_dict.keys():
            raise ValueError("Calibrator field '{0:s}' not found in the input MS!".format(calibrator))

    for target in target_field_list:
        if target not in field_Name_ID_dict.keys():
            raise ValueError("Target field '{0:s}' not found in the input MS!".format(target))
 
    #Check for scan data selection
    if scans != None:
        field_scan_dict = ms_wrapper.get_fieldname_and_ID_list_dict_from_MS(MS, scan_ID=True, close=False)

        target_field_scans = []

        for target in target_field_list:
            target_field_scans.extend(field_scan_dict[target])

        for sID in scans:
            if sID not in target_field_scans:
                raise ValueError('Target field(s) have no scan {0:d}'.format(sID))

        #Get times
        times = ms_wrapper.get_time_based_on_field_names_and_scan_IDs(MS,
                    target_field_list, target_field_scans, close=False)

    else:
        #Get times
        times = ms_wrapper.get_time_based_on_field_names(MS, target_field_list, close=False)
            


    otf_pointings = np.size(np.unique(times))


    logger.info('{0:d} OTF pointings selected'.format(otf_pointings))

    ms_wrapper.close_MS_table_object(MS)

    #=== Create pipeline
    logger.info('Building Snakemake pipeline...')

    #Copy Snakemake file from the template
    shutil.copyfile(snakefile_path,output_snakefile_path)

    #Create config.yaml
    snakemake_config = os.path.join(working_dir,'config.yaml')

    #Remove if exist
    with open(snakemake_config, 'w') as sconfig:
        
        #NOTE: I only using spaces and not tabs as in YAML they should not be mixed!
        #I also not using the yaml module...

        sconfig.write('# Config generated by arcane-suit at {0:s}\n'.format(
                    str(datetime.datetime.now())))

        sconfig.write('working_dir:\n  {0:s}\n'.format(
                        working_dir))
        sconfig.write('output_dir:\n  {0:s}\n'.format(
                        os.path.join(working_dir,'results')))
        sconfig.write('output_otf_dir:\n  {0:s}\n'.format(
                        os.path.join(os.path.join(working_dir,'results'),'otf_pointings')))
        sconfig.write('log_dir:\n  {0:s}\n'.format(
                        os.path.join(working_dir,'logs')))
        sconfig.write('MS:\n  {0:s}\n'.format(
                        MS_path))
        sconfig.write('pointing_ref:\n  {0:s}\n'.format(
                        pointing_ref_path))

        sconfig.write('field_ID:\n')
        sconfig.write('  - 1\n')
        sconfig.write('  - 2\n')

    #=== Garbage collection
    logger.debug('Cleaning up...')
    
    collected = gc.collect()
    logger.debug("Garbage collector: collected",
          "%d objects." % collected)

    #=== Exit
    logger.info('Pipeline created')
    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()