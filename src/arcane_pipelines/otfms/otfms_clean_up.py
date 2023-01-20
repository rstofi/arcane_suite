""""The command line tool for the Snakemake rule: `clean_up`
"""

import sys
import os
import argparse
import logging
import shutil

from arcane_utils import pipeline
from arcane_utils import casa_wrapper
from arcane_utils import misc as pmisc

# Load pipeline default parameters
from arcane_pipelines.otfms import otfms_defaults

# === Set logging
logger = pipeline.init_logger()

# === Functions ===


def main():
    """
    NOTE: This docstring was partially created by ChatGPT3.

    This script removes the potential CASA leftover files at the end of the ``otfms``
    pipeline run. Thes files are: *.last *pre and casa-*.log files

    If ``deep_clean`` is set to true in the config file, the /blob directory, and
    all *.py files (!) are deleted as well.


    Keyword Arguments
    -----------------
    '-c' or '--config_file': (required, str)
        Snakemake yaml configuration file for the otfms pipeline

    """
    # === Set arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c',
        '--config_file',
        required=True,
        help='Snakemake yaml configuration file for the otfms pipeline',
        action='store',
        type=str)

    # ===========================================================================
    args = parser.parse_args()  # Get the arguments

    logger.info("Running *otfms_clean_up*")

    logger.debug("Using default pipeline clean up maxdepth of {0:d}".format(
        otfms_defaults._clean_up_maxdepth))

    yaml_path = args.config_file

    # Set the log level (we know that it is in the right format)
    log_level = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                           var_name='log_level')

    if log_level != 'INFO':
        logger.info(
            "Updating logger level to '{0:s}' based on config file...".format(log_level))

        # Update the log level
        new_log_level = logging.getLevelName(log_level)

        logger.setLevel(new_log_level)

        del new_log_level

    working_dir_path = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                  var_name='working_dir')

    logger.info("Cleaning CASA leftover files")

    casa_wrapper.clean_CASA_logfiles(
        working_dir_path,
        maxdepth=otfms_defaults._clean_up_maxdepth)

    if bool(
        pipeline.get_var_from_yaml(
            yaml_path=yaml_path,
            var_name='deep_clean')):

        logger.info(
            "Deep clean enabled, removing .py files and the /blob directory!")

        pmisc.find_and_remove_files(working_dir_path, file_extension='.py',
                                    maxdepth=otfms_defaults._clean_up_maxdepth)

        # Remove the /blob directory
        blob_dir_path = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                   var_name='blob_dir')

        # This is a weird bug fix: if the /blob directory is deleted, the code fails
        # So I am gonna check if the directory exists, and if not, I raise a
        # warning
        if not os.path.exists(blob_dir_path):
            logger.warn("The /blob dir is missing, skip deleting it!")
        else:
            shutil.rmtree(blob_dir_path)

    logger.info("Exit 0")

    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
