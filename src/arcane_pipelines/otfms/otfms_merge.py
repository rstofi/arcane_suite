"""The command line tool for the Snakemake rule: `merge_scan_and_target`
"""

import sys
import os
import logging
import argparse
import subprocess
import shutil
import numpy as np

from arcane_utils import pipeline
from arcane_utils import misc as pmisc

# === Set logging
logger = pipeline.init_logger()

# === Functions ===


def main():
    """
    NOTE: This docstring was created by ChatGPT3.

    Merges multiple OTF pointings in a single Measurement Set (MS) file.
    The merge process can include also the Calibrators if the split_calibrators
    option is set to True in the config.yaml file.

    The function can also call CASA via subprocess to execute the merge task
    (if the full_rule_run flag is set to True).

    Keyword Arguments
    -----------------
    '-c' or '--config_file': (required, str)
        Snakemake yaml configuration file for the otfms pipeline

    '-fr' ot '--full_rule_run': Optional[bool], default False
        If set, the code attempts to call casa trough subprocess

    '-p' or '--purge_executable': Optional[bool], default False
        If set, the code attempts to only delete the casa executable

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

    parser.add_argument(
        '-fr',
        '--full_rule_run',
        required=False,
        help='If set, the code attempts to call casa trough subprocess',
        action='store_true')

    parser.add_argument(
        '-p',
        '--purge_executable',
        required=False,
        help='If set, the code attempts to only delete the casa executable',
        action='store_true')

    # ===========================================================================
    args = parser.parse_args()  # Get the arguments

    logger.info("Running *otfms_merge*")

    # Get parameters from the config.yaml file
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

    blob_dir = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                          var_name='blob_dir')

    output_dir = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                            var_name='output_dir')

    output_ms_name = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                var_name='MS_outname') +\
        '.ms'

    # Get the output MS path and executable path
    # Generated from input yaml
    output_MS = os.path.join(output_dir, output_ms_name)

    casa_executable_path = os.path.join(blob_dir,
                                        'merge_otf_pointings.py')

    # === Create executable
    if not args.purge_executable:

        otf_field_ID_mapping = pipeline.get_var_from_yaml(
            yaml_path=yaml_path, var_name='otf_field_ID_mapping')

        # Put all otf fields into a single list and convertthe list into a
        # string
        list_of_otf_pointings = []

        for ID in otf_field_ID_mapping.keys():
            otf_ms_path = os.path.join(
                blob_dir, 'otf_pointing_no_{0:s}.ms'.format(ID))

            list_of_otf_pointings.append(
                "'" + otf_ms_path + "'\n")  # Add quotation marks
            # The \n is to make more human readable and if we have hundreds of fields
            # not to run into errors with long single lines... if that is a
            # thing

        logger.info('Selected {0:d} OTF pointings to merge'.format(
            np.size(list_of_otf_pointings)))

        # Merge calibrators
        if bool(
            pipeline.get_var_from_yaml(
                yaml_path=yaml_path,
                var_name='split_calibrators')):

            calibrators_MS_path = os.path.join(blob_dir, 'calibrators.ms')

            logger.info(
                "Merging calibrators from {0:s}".format(calibrators_MS_path))

            # Add the calibrator MS path to the MS list

            list_of_otf_pointings.append("'" + calibrators_MS_path + "'\n")

        list_of_otf_ms_string = pmisc.convert_list_to_string(
            list_of_otf_pointings)

        logger.info('Creating casa executable at {0:s}'.format(
            casa_executable_path))

        merge_task_string = "concat(vis={0:s}, concatvis='{1:s}', ".format(
            list_of_otf_ms_string, output_MS) +\
            "respectname=True)"

        listobs_string = "listobs(vis = '{0:s}')".format(output_MS)

        with open(casa_executable_path, 'w') as sconfig:
            sconfig.write(merge_task_string)
            sconfig.write('\n')
            sconfig.write(listobs_string)

        # Because casa appends the MS with the concat task
        if os.path.isdir(output_MS):
            logger.info(
                'Output MS exist, deleting it before moving on to processing...')
            shutil.rmtree(output_MS)

        # This is a logging logical placement
        if not args.full_rule_run:
            logger.info(
                'Casa executable sript created, please run it externally')

            logger.info("Exit 0")

            sys.exit(0)

    # === Attempting to run casa via subprocess
    if args.full_rule_run:
        logger.info('Runnin CASA split task...')

        # Running the split task

        casa_proc = subprocess.run(
            "casa --log2term --nogui --nologfile " +
            "--nocrashreport -c {0:s}".format(casa_executable_path),
            shell=True,
            capture_output=True)

        out, err = casa_proc.stdout, casa_proc.stderr
        exitcode = casa_proc.returncode

        # Because casa logs weirdly
        logger.info(out.decode('utf-8'))
        logger.info(err.decode('utf-8'))

        if exitcode != 0:
            raise ValueError(
                'The casa subprocess exited with non-zero exit code (see the log above for more info)!')

        del out, err, exitcode

    # === Removing the CASA executable
    if args.purge_executable or args.full_rule_run:
        logger.info('Cleaning up...')
        if os.path.isfile(casa_executable_path):
            os.remove(casa_executable_path)
        else:
            logger.warning('No CASA executable found...')

    # === Exit
    if args.purge_executable or args.full_rule_run:
        logger.info('The created casa executable purged')

        if os.path.isdir(output_MS):
            logger.info('Output MS found')
        else:
            logger.warning('No output MS found!')

    logger.info("Exit 0")

    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
