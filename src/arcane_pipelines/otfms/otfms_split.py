"""The command line tool for the Snakemake rule: `split_otf_scans_by_pointing`
"""

import sys
import os
import logging
import argparse
import subprocess
import shutil

from arcane_utils import pipeline
from arcane_utils import time as a_time

#=== Set logging
logger = pipeline.init_logger()

#=== Functions ===
def main():
    """Basically a custom wrapper around the casa task split, based on the OTF
    field ID and the corresponding time values read from the snakemake
    config.yaml file.

    Based ona the OTF `ID` and the +/- 1/2 * `split_timedelta` time range, the code
    selects visibilities around the time value corresponding to the ID in the
    config.yml file
    
    NOTE that due to path setup issues, the current strategy is to run this script to
            create a python script, which can be executed by casa, then call casa
            from Snakemake shell env, then run this script again to clean up the
            executable. The latter is to use python for cleaning up and logging,
            rather shell commands...

    The code of course could be run as a standalone program, in which case casa
    is called from this script. This works because when run in shell the .bashrc
    setup is *magically* applied to the call, but not whhen the script is called
    from Snakemake... I assume this is because of the *strict* mode of bash Snakemake
    uses....

    NOTE that the code by default only creates a python script that can be executed
            by casa

    Keyword Arguments
    -----------------


    """
    #=== Set arguments
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config_file', required=True,
                    help='Snakemake yaml configuration file for the otfms pipeline',
                    action='store', type=str)

    parser.add_argument('-i', '--otf_id', required=True,
                    help='Snakemake yaml configuration file for the otfms pipeline',
                    action='store', type=str)

    parser.add_argument('-fr', '--full_rule_run', required=False,
                        help='If set, the code attempts to call casa trough subprocess',
                        action='store_true')

    parser.add_argument('-p', '--purge_executable', required=False,
                        help='If set, the code attempts to only delete the casa executable',
                        action='store_true')

    #===========================================================================
    args = parser.parse_args() #Get the arguments

    logger.info("Running *split_otf_scans_by_pointing* with OTF_ID: {0:s}".format(args.otf_id))

    #Get parameters from the config.yaml file
    yaml_path = args.config_file

    #MS = pipeline.get_var_from_yaml(yaml_path = yaml_path,
    #                                              var_name = 'MS')

    output_otf_dir = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'output_otf_dir')

    split_timedelta = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'split_timedelta')

    otf_field_ID_mapping = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'otf_field_ID_mapping')

    #Get the output MS path and executable path
    output_MS = os.path.join(output_otf_dir,'otf_pointing_no_{0:s}.ms'.format(
                                                                    args.otf_id))

    casa_executable_path = os.path.join(output_otf_dir,
                                        'split_otf_pointing_no_{0:s}.py'.format(
                                        args.otf_id))

    #=== Create executable
    if not args.purge_executable:
        #NOTE: only a single target field is currently supported
        #TO DO: implement a check for which target field the time value belongs
        target_field = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                var_name = 'target_fields')[0]

        otf_pointing_time = otf_field_ID_mapping[args.otf_id]

        del otf_field_ID_mapping, yaml_path

        #Compute the selection range
        start_unix_time = otf_pointing_time - (split_timedelta * 0.5)
        end_unix_time = otf_pointing_time + (split_timedelta * 0.5)

        casa_timerange_selection_string = \
                a_time.convert_unix_times_to_casa_timerange_selection(start_unix_time,
                                                                        end_unix_time)

        logger.info('Set visibility selection: {0:s}'.format(
                                                    casa_timerange_selection_string))

        logger.info('Creating casa executable at {0:s}'.format(casa_executable_path))

        split_task_string = "split(vis = '{0:s}',\n outputvis = '{1:s}',\
    \n timerange = '{2:s}',\n datacolumn = 'data',\n field = '{3:s}')".format(
                    MS, output_MS,casa_timerange_selection_string,target_field)

        listobs_string = "listobs(vis = '{0:s}')".format(output_MS)

        with open(casa_executable_path, 'w') as sconfig:
            sconfig.write(split_task_string)
            sconfig.write('\n')
            sconfig.write(listobs_string)

        #Because casa does not like to overwrite MS with the split task
        if os.path.isdir(output_MS):
            logger.info('Output MS exist, deleting it before moving on to processing...')
            shutil.rmtree(output_MS)

        #This is a logging logical placement
        if not args.full_rule_run:
            logger.info('Casa executable sript created, please run it externally')

            sys.exit(0)

    #=== Attempting to run casa via subprocess
    if args.full_rule_run:
        logger.info('Runnin CASA split task...')

        #Running the split task

        casa_proc = subprocess.run("casa --log2term --nogui --nologfile --nocrashreport -c {0:s}".format(
                        casa_executable_path), shell=True, capture_output=True)

        out, err = casa_proc.stdout, casa_proc.stderr
        exitcode = casa_proc.returncode

        #Because casa logs weirdly
        logger.info(out.decode('utf-8'))
        logger.info(err.decode('utf-8'))

        if exitcode != 0:
            raise ValueError('The casa subprocess exited with non-zero exit code (see the log above for more info)!')

        del out, err, exitcode

    #=== Removing the CASA executable
    if args.purge_executable or args.full_rule_run:
        logger.info('Cleaning up...')
        if os.path.isfile(casa_executable_path):
            os.remove(casa_executable_path)
        else:
            logger.warning('No CASA executable found...')

    #=== Exit
    if args.purge_executable or args.full_rule_run:
        logger.info('The created casa executable purged')

        if os.path.isdir(output_MS):
            logger.info('Output MS found')
        else:
            logger.warning('No output MS found!')

    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()