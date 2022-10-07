"""The command line tool used in the Snakemake rules: `rename_otf_pointing`,
`apply_phase_rotation` and `list_new_otf_field_names`
"""

import sys
import os
import argparse
import numpy as np
import datetime

from arcane_utils import pipeline
from arcane_utils import ms_wrapper

from arcane_pipelines.otfms import otf_pipeline_util as putil

# === Set logging
#logger = pipeline.init_logger()

# NOTE: for this app the log handler type dpends on the input parameters!

# === Functions ===


def save_names_only(yaml_path, output_fname):
    """Wrapper function for the secondary purpose of the tool: generating the names

    Basically a for loop to get the name for every ID from the yaml file

    Parameters
    ----------
    yaml_path: str
        Path to the Snakemake yaml config file

    output_fname: str
        Path to the file in which the IDs and Names are saved

    Returns
    -------
    Creates a file with the OTF IDs and names

    """
    # Get al the ID's from the config file
    otf_field_ID_mapping = pipeline.get_var_from_yaml(
        yaml_path=yaml_path, var_name='otf_field_ID_mapping')

    with open(output_fname, 'w') as namelistf:

        namelistf.write('#List of OTF IDs and field names generated by arcane-suit at {0:s}\n'.format(
            str(datetime.datetime.now())))

        for ID in otf_field_ID_mapping.keys():

            time_centre, ra_centre, dec_centre = putil.get_closest_pointing_from_yaml(
                yaml_path, ID)

            otf_field_name = putil.generate_OTF_names_from_ra_dec(
                ra=ra_centre, dec=dec_centre)

            namelistf.write('{0:s} {1:s}\n'.format(ID, otf_field_name))


def main():
    """A custom tool with three purposes:

        1. Rename the field (and the corresponding source and pointing) for a given OTF pointing
        2. Create a file with all OTF IDs and the names
        3. Output a string that is readable by `chagcentre`

    As such, this tool is used in *three* rules in the pipeline. For once, it is called
    for every OTF pointing to rename the pointing before rotation and merging.
    Then, it is called to generate the new pointing string that is passed to `chgcentre`
    to perform the rotation. Finally, to generate thie file listing all new names.

    It is most logical to have a single tool that can be used for renaming and
    generating the input for the OTF rotation as both is based on the coordinates
    of the closest pointing from the reference pointing.

    NOTE: this is a standalone tool, that could be useful in general for renaming
        a single field in an MS

    TO DO: add an argument, that allows to specify the new name acroym part

    TO DO: allow to rename not oly the first row, by adding an argument for the
        row to rename

    Keyword Arguments
    -----------------


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

    parser.add_argument('-i', '--otf_id', required=False,
                        help='The ID of the OTF pointing used',
                        action='store', type=str, default=None)

    parser.add_argument(
        '-sn',
        '--save_names_only',
        required=False,
        help='If True a file is generated with all OTF IDs and field names',
        action='store_true')

    parser.add_argument(
        '-o',
        '--output_fname',
        required=False,
        help='The output file name in which all the OTF field names being saved',
        action='store',
        type=str,
        default=None)

    parser.add_argument(
        '-ds',
        '--direction_string',
        required=False,
        help='If True a direction string is outputted in a format readable by *chgcentre*',
        action='store_true')

    parser.add_argument(
        '-l',
        '--log_file',
        required=False,
        help='The output log file name, only considered when the -ds argument is set',
        action='store',
        type=str,
        default=None)

    # ===========================================================================
    args = parser.parse_args()  # Get the arguments

    # Get parameters from the config.yaml file
    yaml_path = args.config_file

    # Run when only te names are generated
    if args.save_names_only:
        logger = pipeline.init_logger()

        logger.info("Running *otf_pointing_correction* in 'listing' mode")

        if args.output_fname is None:
            raise ValueError('No output file name is provided!')

        save_names_only(yaml_path=yaml_path, output_fname=args.output_fname)

        sys.exit(0)

    # Check if an ID is provided when working with a single data set
    if args.otf_id is None:
        raise ValueError('No OTF ID is provided!')

    if args.direction_string:
        if args.log_file:
            logger = pipeline.init_logger(log_file=args.log_file)

        else:
            # Set the logger to use the NULL handler, but in the code I still have
            # log messages for debugging
            logger = pipeline.init_logger(null_logger=True)

        logger.info("Running *otf_pointing_correction* in 'chgcentre' " +
                    "mode with OTF_ID: {0:s}".format(args.otf_id))
    else:
        logger = pipeline.init_logger()
        logger.info("Running *otf_pointing_correction* in 'renaming' " +
                    "mode with OTF_ID: {0:s}".format(args.otf_id))

    # Check if OTF directories exists or not
    output_otf_dir = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                var_name='output_otf_dir')

    # Compute the OTF pointing MS name based on the naming convenction
    otf_MS_path = os.path.join(
        output_otf_dir,
        'otf_pointing_no_{0:s}.ms'.format(
            args.otf_id))

    if os.path.isdir(otf_MS_path) == False:
        raise FileNotFoundError(
            'Single pointing OTF format MS not found as: {0:s}'.format(otf_MS_path))

    time_centre, ra_centre, dec_centre = putil.get_closest_pointing_from_yaml(
        yaml_path, args.otf_id)

    if args.direction_string:
        # Get the pointing centre string
        pointing_string = putil.generate_position_string_for_chgcentre(
            ra=ra_centre, dec=dec_centre)

        logger.info(
            'Coordinate string for chgcentre: {0:s}'.format(pointing_string))

        # Print would also work, but it adds \n automatically...
        sys.stdout.write(pointing_string)

        sys.exit(0)

    else:
        logger.info('Renaming field in {0:s}'.format(otf_MS_path))

        # Now compute the name form the RA and Dec values
        otf_field_name = putil.generate_OTF_names_from_ra_dec(ra=ra_centre,
                                                              dec=dec_centre)

        logger.info('The new field name, based on the coordinates is: {0:s}'.format(
            otf_field_name))

        # Now renaming the field
        otf_MS = ms_wrapper.create_MS_table_object(otf_MS_path)

        ms_wrapper.rename_single_field(mspath=otf_MS,
                                       field_ID=0,
                                       new_field_name=otf_field_name,
                                       source=True,
                                       pointing=True,
                                       close=True)

        sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
