"""The command-line application initializing the `otfms` pipeline.
"""

import sys
import os
import shutil
import logging
import argparse

import arcane_suite
from arcane_suite import pipelineutil

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

    parser.add_argument('-o', '--overwrite', required=False,
                        help='If enabled, the working directory is overwritten, otherwise the program halts',
                        action='store_false')

    #===========================================================================
    args = parser.parse_args() #Get the arguments

    logger.info('Building *otfms* pipeline from arcane-suite')

    #Check if the config file exists
    if not os.path.exists(args.config_file):
        raise FileNotFoundError('Input config file does not exists!')

    #=== Read the environment vales from the config file
    logger.info('Solving for environment...')

    working_dir = pipelineutil.get_common_env_variables(args.config_file)

    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    else:
        if args.overwrite:
            logger.warning('Cleaning working directory {0:s}'.format(working_dir))
            shutil.rmtree(working_dir)
            os.mkdir(working_dir)
        else:
            raise FileExistsError('Specified directory {0:s} exists and overwrite is set to False.'.format(
                    working_dir))

    #Add checks here for the data dir if exists
    path = os.path.abspath(src.__file__)

    print(path)

    #=== Read the data sub selection from the config file
    logger.info('Solving for OTF field initialization...')


    #=== Create pipeline
    logger.info('Create piepline environment...')

    logger.info('Creating config file...')

    logger.info('Copying Snakemake file...')

    #=== Garbage collection
    logger.info('Cleaning up...')


    #=== Exit
    logger.info('Pipeline created')
    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()