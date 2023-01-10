"""The command line tool used to generate the phase centre position plots before
and after the phase rotation. Used in the following rules:
"""

import sys
import os
import argparse
import logging

import numpy as np

from arcane_utils import pipeline
from arcane_utils import ms_wrapper
from arcane_utils import visual_diagnostics

from arcane_utils import misc as pmisc

# === Set logging
logger = pipeline.init_logger()

logger.setLevel(logging.DEBUG)

# === Functions ===


def main():
    """
    NOTE: This docstring was created by ChatGPT3.


    This command-line tool generates (maximum) two plots: one for the target fields,
    and if provided, one for the calibrator fields.

    The input file names are starting with ``target_`` or ``calibrators_`` accordingly.

    By deafult the code genrates a diagnostics plot for the input MS defined in the
    snakemake congig.yaml file.

    If the '-om' switch is given the diagnostics plots are derived from the output
    MS, which lives under /results and it's name is derived from ``MS_outname``.

    If the input ``-o`` parameter results in a file already exists and the code is
    throwing a warning

    Parameters:
    - '-c' or '--config_file' (required, str): Snakemake yaml configuration file for the otfms pipeline
    - '-o' or '--output_fname' (optional, str): The output file name in which all the OTF field names being saved (default: None)
    - '-om' or '--output_mode' (optional, bool): If set to True, the function runs in 'output' mode (default: False)

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
        '-o',
        '--output_fname',
        required=False,
        help='The output file name in which all the OTF field names being saved',
        action='store',
        type=str,
        default=None)

    parser.add_argument(
        '-om',
        '--output_mode',
        required=False,
        help="If set to True, the function runs in 'output' mode (default: False)",
        action='store_true')

    # ===========================================================================
    args = parser.parse_args()  # Get the arguments

    # Get parameters from the config.yaml file
    yaml_path = args.config_file

    # Get the reports_dir full path

    reports_dir_path = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                  var_name='reports_dir')

    if not args.output_mode:
        logger.info("Running *otfms_position_diagnostic* in 'input' mode")

        # Get the input MS
        input_ms_path = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                   var_name='MS')

        ptitle = "Phase centres (with field ID's) before OTF correction"

    else:
        logger.info("Running *otfms_position_diagnostic* in 'output' mode")

        output_dir = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                var_name='output_dir')

        output_ms_name = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                    var_name='MS_outname') +\
            '.ms'

        input_ms_path = os.path.join(
            output_dir, output_ms_name)  # Genarte from input .yaml

        ptitle = "Phase centres (with field ID's) after OTF correction"

    # The MS used for the diagnostics plots
    logger.debug(
        "The MS used for the diagnostics plots: {0:s} ...".format(input_ms_path))

    # Get the field ID and field name diect

    field_name_and_ID_dict = ms_wrapper.get_fieldname_and_ID_list_dict_from_MS(
        mspath=input_ms_path, scan_ID=False, close=True)

    # === Generate diagnostics plots for the calibrator fields:
    # Should be the same routine for both the 'input' and 'output' mode
    if bool(
        pipeline.get_var_from_yaml(
            yaml_path=yaml_path,
            var_name='split_calibrators')):

        list_of_calibrator_fields = pipeline.get_var_from_yaml(
            yaml_path=yaml_path, var_name='calibrator_fields')

        if list_of_calibrator_fields is None:
            logger.critical(
                "No calibrator field(s) are specifyed in the Snakemake config yaml!")

            list_of_calibrator_fields = []

        else:
            # Now check if the calibrator fields are ALL in the MS!

            calibrator_field_ID_list = []

            for field_Name in list_of_calibrator_fields:
                if field_Name not in field_name_and_ID_dict.keys():
                    raise ValueError(
                        "The calibrator field {0:s} is not in the input MS!".format(field_Name))

                else:
                    calibrator_field_ID_list.append(
                        field_name_and_ID_dict[field_Name][0])

                    if np.size(field_name_and_ID_dict[field_Name]) > 1:
                        logger.critical(
                            "Target field {0:s} has more than 1 associated field ID's, using only the first!".format(field_Name))

            logger.info("Calibrator field(s) selected: {0:s}".format(
                pmisc.convert_list_to_string(list_of_calibrator_fields)))

            output_fname = "calibrator_" + args.output_fname

            outname_path = os.path.join(reports_dir_path, output_fname)

            if args.output_mode:
                if os.path.exists(outname_path):
                    logger.warn(
                        "Diagnostic plot already exis under: {0:s} ".format(outname_path))

            logger.info(
                "Generating diagnostics plot for calibrator fields under: {0:s} ".format(outname_path))

            visual_diagnostics.create_field_ID_RA_Dec_plot(
                mspath=input_ms_path,
                otf_fig_path=outname_path,
                field_ID_list=calibrator_field_ID_list,
                ptitle=ptitle)

    # === Select field ID's to plot based on the MS:
    # The field names should be different for the 'input' and 'output' mode
    if not args.output_mode:
        list_of_target_fields = pipeline.get_var_from_yaml(
            yaml_path=yaml_path, var_name='target_fields')

    else:
        # Get the list of traget fields from the ``otf_field_names.dat`` file

        output_dir = pipeline.get_var_from_yaml(
            yaml_path=yaml_path, var_name='output_dir')

        list_of_target_fields = list(
            np.loadtxt(
                os.path.join(
                    output_dir,
                    'otf_field_names.dat'),
                dtype=str,
                skiprows=1,
                comments='#',
                usecols=1).flatten())

       #logger.info(list_of_target_fields, np.shape(list_of_target_fields))

        #list_of_target_fields = []

    # Now check if the calibrator fields are ALL in the MS!
    target_field_ID_list = []

    for field_Name in list_of_target_fields:
        if field_Name not in field_name_and_ID_dict.keys():
            raise ValueError(
                "The target field {0:s} is not in the input MS!".format(field_Name))

        else:
            target_field_ID_list.append(field_name_and_ID_dict[field_Name][0])

            if np.size(field_name_and_ID_dict[field_Name]) > 1:
                logger.critical(
                    "Target field {0:s} has more than 1 associated field ID's, using only the first!".format(field_Name))

    logger.info("Target field(s) selected: {0:s}".format(
        pmisc.convert_list_to_string(list_of_target_fields)))

    logger.debug("Target field(s) selected: {0:s}".format(
        pmisc.convert_list_to_string(target_field_ID_list)))

    # === Generate the plot from the input MS

    # Define the output full path based on the reports_dir path

    output_fname = "target_" + args.output_fname

    outname_path = os.path.join(reports_dir_path, output_fname)

    if args.output_mode:
        if os.path.exists(outname_path):
            logger.warn(
                "Diagnostic plot already exis under: {0:s} ".format(outname_path))

    logger.info(
        "Generating diagnostics plot for target fields under: {0:s} ".format(outname_path))

    visual_diagnostics.create_field_ID_RA_Dec_plot(
        mspath=input_ms_path,
        otf_fig_path=outname_path,
        field_ID_list=target_field_ID_list,
        ptitle=ptitle)

    logger.info("Exit 0")

    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
