"""The command line tool for the Snakemake rule: `rename_otf_pointing`
"""

import sys
import os
import argparse
import numpy as np

from arcane_utils import pipeline
from arcane_utils import ms_wrapper

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
    otf_MS_path = os.path.join(output_otf_dir,'otf_pointing_no_{0:s}.ms'.format(
                                                                    args.otf_id))

    if os.path.isdir(otf_MS_path) == False:
        raise FileNotFoundError('Single pointing OTF format MS not found as: {0:s}'.format(otf_MS_path))

    #Now get the RA and Dec values from the pointing reference fil

    pointing_ref_path = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'pointing_ref')


    times, ra, dec = putil.get_pointing_and_times_from_reference_pointing_file(pointing_ref_path)

    #Select the time value and corresponding RA and Dec values

    otf_field_ID_mapping = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                            var_name = 'otf_field_ID_mapping')

    time_crossmatch_threshold = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                            var_name = 'time_crossmatch_threshold')

    otf_pointing_time = otf_field_ID_mapping[args.otf_id]

    del otf_field_ID_mapping, yaml_path

    #So now there is a truncating issue
    #This is no slower than the exact check, which fails due to truncation issues
    closest_time_arg =  np.argmin(np.fabs(times - otf_pointing_time))

    time_centre = times[closest_time_arg]

    if np.fabs(time_centre - otf_pointing_time) > time_crossmatch_threshold:
        raise ValueError('No matching reference time found with the config time value!')

    ra_centre = ra[closest_time_arg]
    dec_centre = dec[closest_time_arg]

    del times, ra, dec

    #Now compute the name form the RA and Dec values

    #TO DO: implement this

    otf_field_name = 'test_name'

    #Now renaming the field
    otf_MS = ms_wrapper.create_MS_table_object(otf_MS_path)

    fieldtable_path = ms_wrapper.get_MS_subtable_path(otf_MS, 'FIELD', close=False)

    fieldtable = ms_wrapper.create_MS_table_object(fieldtable_path, readonly=False)

    for i in fieldtable.rownumbers():
        
        print(fieldtable.getcol('NAME')[i])

        fieldtable.putcell('NAME',i,otf_field_name)

        print(fieldtable.getcol('NAME')[i])

    #TO DO: raise warning for more than one fields and sources
    #TO DO: rename the source as well!

    ms_wrapper.close_MS_table_object(fieldtable)



    #Close MS
    ms_wrapper.close_MS_table_object(otf_MS)


    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()