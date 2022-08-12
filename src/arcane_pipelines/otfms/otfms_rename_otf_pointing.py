"""The command line tool for the Snakemake rule: `rename_otf_pointing`
"""

import sys
import os
import argparse
import numpy as np

from arcane_utils import pipeline

from arcane_pipelines.otfms import otf_pipeline_util as putil

#=== Set logging
logger = pipeline.init_logger()

#=== Functions ===
def main():
    """
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

    logger.info("Running *rename_otf_pointing* with OTF_ID: {0:s}".format(args.otf_id))

    #Get parameters from the config.yaml file
    yaml_path = args.config_file

    output_otf_dir = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'output_otf_dir')  

    #Compute the OTF pointing MS name based on the naming convenction
    otf_MS = os.path.join(output_otf_dir,'otf_pointing_no_{0:s}.ms'.format(
                                                                    args.otf_id))

    if os.path.isdir(otf_MS) == False:
        raise FileNotFoundError('Single pointing OTF format MS not found as: {0:s}'.format(otf_MS))

    #Now get the RA and Dec values from the pointing reference fil

    pointing_ref_path = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'pointing_ref')


    times, ra, dec = putil.get_pointing_and_times_from_reference_pointing_file(pointing_ref_path)

    #Select the time value and corresponding RA and Dec values

    otf_field_ID_mapping = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'otf_field_ID_mapping')

    otf_pointing_time = otf_field_ID_mapping[args.otf_id]

    del otf_field_ID_mapping, yaml_path

    #So now there is a truncating issue

    time_centre = times[np.argmin(np.fabs(times - otf_pointing_time))]
    ra_centre = ra[np.argmin(np.fabs(times - otf_pointing_time))]
    dec_centre = dec[np.argmin(np.fabs(times - otf_pointing_time))]

    #Do a check if the diff is below the time_crossmatch_threshold


    #Now I have the input MS
    print(np.min(np.fabs(times - otf_pointing_time)))
    print(otf_pointing_time, time_centre, ra_centre, dec_centre)


    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()