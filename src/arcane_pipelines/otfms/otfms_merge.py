"""The command line tool for the Snakemake rule: `merge_scan_and_target`
"""

import sys
import os
import logging
import argparse
import subprocess
import shutil

from arcane_utils import pipeline

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

	parser.add_argument('-o', '--output_ms_name', required=True,
                    help='The name of the output MS, with the .ms extension but without the absolute path',
                    action='store', type=str)

    parser.add_argument('-fr', '--full_rule_run', required=False,
                        help='If set, the code attempts to call casa trough subprocess',
                        action='store_true')

    parser.add_argument('-p', '--purge_executable', required=False,
                        help='If set, the code attempts to only delete the casa executable',
                        action='store_true')



    #===========================================================================
    args = parser.parse_args() #Get the arguments

    logger.info("Running *otfms_merge*")

    #Get parameters from the config.yaml file
    yaml_path = args.config_file

    output_otf_dir = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                              var_name = 'output_otf_dir')

    output_dir = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                              var_name = 'output_dir')


    #Get the output MS path and executable path
    output_MS = os.path.join(output_dir,'{0:s}'.format(args.output_ms_name))

    casa_executable_path = os.path.join(output_dir,
                                        'split_otf_pointing_no_{0:s}.py'.format(
                                        args.otf_id))


    #=== Create executable
    if not args.purge_executable:

    	list_of_otf_ms_string = ''

    	merge_task_string = "concat('vis={0:s}', concatvis={1:s}, ".format(
    							list_of_otf_ms_string, output_MS) +\
    						"respectname=True)"


    	print(merge_task_string)


#=== MAIN ===
if __name__ == "__main__":
    main()