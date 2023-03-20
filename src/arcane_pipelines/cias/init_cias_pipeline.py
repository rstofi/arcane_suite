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
import copy
import subprocess

from arcane_utils import pipeline
from arcane_utils import ms_wrapper
from arcane_utils import time as a_time
from arcane_utils import casa_wrapper

from arcane_pipelines.otfms import cias_pipeline_util as putil
from arcane_pipelines.otfms import cias_defaults

# === Set logging
logger = pipeline.init_logger(color=True)
logger.setLevel(logging.INFO)

# Add logging from modules
utils_logger = logging.getLogger('arcane_utils')
utils_logger.setLevel(logging.INFO)

pipelines_logger = logging.getLogger('arcane_pipelines')
pipelines_logger.setLevel(logging.INFO)

# === Functions ===


def main():
    """The top level command-line application to build the *otfms* pipeline.

    When *only* a config file is provided, the code does what it meant to do and
    initialises the *otfms* Snakemake pipeline by building the following file structure:

    '''
    working_dir
        |
        -- Sankefile
        |
        -- config.yaml
    '''

    If the structure above exists, only these files under `working_dir` will be
    overwritten, any other files or directoryes will remain intact.

    However, there are options to *whipe out the `working_directory` completely*.

    Plus, there is a safety option to lock the code if `working_directory` already
    exists. This is reccommended when calling the `init_otfms_pipeline` task
    from an other script.

    For more info on the pipeline, see the README.rst file created.

    Furthermore the code can create an empty parset file for the user if the -t
    option is provided

    Keyword Arguments
    -----------------

    str -c or --config_file:
        String, Full path to the configuration file for the pipeline setup
        (not the Snakemake configuration file)

    optional -t or --template:
        Bool, if enabled a config file template is creted with the name specified
        by the --config_file argument.

    optional -ca or --clear_all:
        Bool, if provided the working directory is overwritten completely

    optional -ol or --overwrite-lock
        Bool, if enabled, the working directory is locked and only created if not existing

    optional -sdc or --skip_dependencies_check:
        Bool, if enabled, the code skip the checks for the dependent packages (casa, chagcentre)

    optional -ssc or skip_snakemake_check:
        Bool, if enabled, the code skip checking for Snakemake and not performing the dry run

    optional -vd or --verbosity_debug
        Bool, if enabled, the log level is set to DEBUG

    """
    # === Set arguments
    # parser = argparse.ArgumentParser(description='Initialize the pipeline for converting \
# asynchronous OTF MS to a canonical MS format.')

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c',
        '--config_file',
        required=True,
        help='Configuration file for the pipeline setup (not the Snakemake configuration file)',
        action='store',
        type=str)

    parser.add_argument(
        '-t',
        '--template',
        required=False,
        help='If enabled a config file template is created with the name specified by the --config_file argument',
        action='store_true')

    parser.add_argument(
        '-ca',
        '--clear_all',
        required=False,
        help='If enabled, the working directory is overwritten completely',
        action='store_true')

    parser.add_argument(
        '-ol',
        '--overwrite_lock',
        required=False,
        help='If enabled, the working directory is locked and only created if not existing',
        action='store_true')

    parser.add_argument(
        '-sdc',
        '--skip_dependencies_check',
        required=False,
        help='If enabled, the code skip the checks for the dependent packages (casa, chagcentre)',
        action='store_true')

    parser.add_argument(
        '-ssc',
        '--skip_snakemake_check',
        required=False,
        help='If enabled, the code skip checking for Snakemake and not performing the dry run',
        action='store_true')

    parser.add_argument(
        '-vd',
        '--verbosity_debug',
        required=False,
        help='If enabled, the log level is set to DEBUG',
        action='store_true')

    parser.add_argument(
        '-sgc',
        '--skip_rule_graph_creation',
        required=False,
        help='If enabled, the rule graph is not generated',
        action='store_true')

    # ===========================================================================
    args = parser.parse_args()  # Get the arguments

    # Set up log level
    if args.verbosity_debug:
        logger.setLevel(logging.DEBUG)
        utils_logger.setLevel(logging.DEBUG)
        pipelines_logger.setLevel(logging.DEBUG)

        logger.debug('Set log level to DEBUG ...')

    if args.template:
        logger.info(
            'Creating template config file for *cias* pipeline from arcane_suite')

        if not args.overwrite_lock:
            putil.init_config_for_otfms(template_path=args.config_file)
        else:
            putil.init_config_for_otfms(template_path=args.config_file,
                                        overwrite=False)

        # TNow halt the program
        sys.exit(0)

    else:
        logger.info('Building *cias* pipeline from arcane_suite')


    # === Exit
    logger.info('Pipeline created')
    logger.info('Exit 0')
    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
