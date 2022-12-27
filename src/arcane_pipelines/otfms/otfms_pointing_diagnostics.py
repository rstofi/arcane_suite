"""The command line tool used to generate the phase centre position plots before
and after the phase rotation. Used in the following rules: 
"""

import sys
import os
import argparse

from arcane_utils import pipeline
from arcane_utils import ms_wrapper
from arcane_utils import visual_diagnostics

# === Set logging
logger = pipeline.init_logger()

# === Functions ===

def main():
    """


    NOTE: by deafult the code genrates a diagnostics plot for the input MS!

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
        help='',
        action='store_true')


    # ===========================================================================
    args = parser.parse_args()  # Get the arguments

    # Get parameters from the config.yaml file
    yaml_path = args.config_file


    if not args.output_mode:
        logger.info("Running *otfms_position_diagnostic* in 'input' mode")

        # Get the input MS
        input_ms_path = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                    var_name='MS')



        #=== Select field ID's to plot based on the MS:

        list_of_target_fields = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                    var_name='target_fields')

        logger.debug("Target field(s) selected: {0:s}".format(
                misc.convert_list_to_string(list_of_calibrator_fields)))

        if bool(pipeline.get_var_from_yaml(yaml_path=yaml_path, var_name='split_calibrators')):
            list_of_calibrator_fields = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                    var_name='calibrator_fields')


            if list_of_calibrator_fields == None:
                logger.critical("No calibrator field(s) are specifyed in the Snakemake config yaml!")

                list_of_calibrator_fields = []


            logger.debug("Calibrator field(s) selected: {0:s}".format(
                misc.convert_list_to_string(list_of_calibrator_fields)))


        print(list_of_target_fields)




    sys.exit(0)



# === MAIN ===
if __name__ == "__main__":
    main()
