"""The command-line application initializing the `otfms` pipeline.
"""

import sys
import os
import shutil
import logging
import argparse
import gc

from arcane_util import pipeline

#=== Set logging
logger = logging.getLogger()

logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s -- %(levelname)s: %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


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
                        help='If enabled, the working directory is overwritten, otherwise the program halts',
                        action='store_true')

    parser.add_argument('-ol', '--overwrite_lock', required=False,
                        help='If enabled, the working directory is overwritten, otherwise the program halts',
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

    #Add checks here for the Snakefile if exists
    snakefile_path = os.path.join(os.path.dirname(sys.modules['arcane_pipelines.otfms'].__file__),
                                    'Snakefile')
 
    if not os.path.exists(snakefile_path):
        raise FileNotFoundError('Corrupted installation: Snakefile not found')

    output_snakefile_path = os.path.join(working_dir, 'Snakefile')

    #=== Read the data sub selection from the config file
    logger.info('Solving for OTF field initialization...')


    #=== Create pipeline
    logger.info('Creating config file...')

    logger.info('Copying Snakemake file...')

    shutil.copyfile(snakefile_path,output_snakefile_path)

    #=== Garbage collection
    logger.info('Cleaning up...')
    
    collected = gc.collect()
    logger.debug("Garbage collector: collected",
          "%d objects." % collected)

    #=== Exit
    logger.info('Pipeline created')
    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()