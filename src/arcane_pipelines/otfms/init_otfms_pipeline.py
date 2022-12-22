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

from arcane_pipelines.otfms import otfms_pipeline_util as putil
from arcane_pipelines.otfms import otfms_defaults

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
            'Creating template config file for *otfms* pipeline from arcane_suite')

        if not args.overwrite_lock:
            putil.init_config_for_otfms(template_path=args.config_file)
        else:
            putil.init_config_for_otfms(template_path=args.config_file,
                                        overwrite=False)

        # TNow halt the program
        sys.exit(0)

    else:
        logger.info('Building *otfms* pipeline from arcane_suite')

    # Check if the config file exists
    if not os.path.exists(args.config_file):
        raise FileNotFoundError('Input config file does not exists!')

    # === Read the environment vales from the config file
    logger.info('Solving for environment...')

    # Get the ENV variables from config
    working_dir = pipeline.get_common_env_variables(
        args.config_file)

    # Get aliases
    command_line_tool_alias_dict = pipeline.get_aliases_for_command_line_tools(
        config_path=args.config_file,
        aliases_list=otfms_defaults._otfms_default_aliases,
        defaults_list=otfms_defaults._otfms_default_alias_values)

    # Checking for required software
    if not args.skip_snakemake_check:

        pipeline.check_snakemake_installation(
            command_line_tool_alias_dict['snakemake_alias'], pedantic=True)
    else:

        # Raise warning if Snakemake is not called as `snakemake`
        if command_line_tool_alias_dict['snakemake_alias'] != 'snakemake':
            logger.critical(
                'Snakemake is not callable via the snaklemake command in this system, based on the config file alias!')

        logger.warning('Skip checking Snakemake installation')

    if not args.skip_dependencies_check:
        # Check for chgcentre
        pipeline.check_is_installed(
            command_line_tool_alias_dict['chgcentre_alias'])

        # Check for casa installation
        casa_wrapper.check_casa_installation(
            command_line_tool_alias_dict['casa_alias'])

    else:
        logger.warning('Skip checking for chgcentre installation')
        logger.warning('Skip checking for CASA installation')

    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    else:
        if args.overwrite_lock:
            raise FileExistsError(
                'Specified directory {0:s} exists and overwrite lock is ON.'.format(working_dir))
        elif args.clear_all:
            logger.warning(
                'Cleaning *everything* from working directory {0:s}'.format(working_dir))
            shutil.rmtree(working_dir)
            os.mkdir(working_dir)
        else:
            logger.warning(
                'Overwriting Sankefile and coinfig file under {0:s}'.format(working_dir))
            # Because the files under `working_dir` will be overwritten

    # Get the input data
    MS_path, pointing_ref_path, split_calibrators = putil.get_otfms_data_variables(
        args.config_file)

    if not os.path.exists(MS_path):
        raise FileNotFoundError(
            'Missing input MS directory {0:s}'.format(MS_path))

    if not os.path.exists(pointing_ref_path):
        raise FileNotFoundError(
            'Missing input reference pointing file {0:s}'.format(pointing_ref_path))

    # Add checks here for the Snakefile if exists
    snakefile_path = os.path.join(
        os.path.dirname(
            sys.modules['arcane_pipelines.otfms'].__file__),
        'Snakefile')

    if not os.path.exists(snakefile_path):
        logger.debug("No Snakefile, found, try to import 'arcane_pipelines.otfms'")

        from arcane_pipelines import otfms

        snakefile_path = os.path.join(
        os.path.dirname(
            sys.modules['arcane_pipelines.otfms'].__file__),
        'Snakefile')

        if not os.path.exists(snakefile_path):

            raise FileNotFoundError('Corrupted installation: Snakefile not found')

    output_snakefile_path = os.path.join(working_dir, 'Snakefile')

    # === Read the data sub selection from the config file
    logger.info('Solving for OTF field initialization...')

    MS = ms_wrapper.create_MS_table_object(MS_path)

    calibrator_list, target_field_list, timerange, scans, ant1_ID, ant2_ID, \
        time_crossmatch_threshold, split_timedelta, position_crossmatch_threshold = \
        putil.get_otfms_data_selection_from_config(args.config_file,
                                                   split_calibrators=split_calibrators)

    # Check if calibrator and target fields are in the MS
    field_Name_ID_dict = ms_wrapper.get_fieldname_and_ID_list_dict_from_MS(
        MS, ant1_ID=ant1_ID, ant2_ID=ant2_ID, close=False)

    if split_calibrators:
        for calibrator in calibrator_list:
            if calibrator not in field_Name_ID_dict.keys():
                raise ValueError(
                    "Calibrator field '{0:s}' not found in the input MS!".format(calibrator))

        # The [1:-1] removes the [] from the string
        logger.info(
            "Selected calibrator field(s): {0:s} ...".format(
                str(calibrator_list)[
                    1:-1]))

        del calibrator
    else:
        logger.info('No calibrator fields are selected...')

    for target in target_field_list:
        if target not in field_Name_ID_dict.keys():
            raise ValueError(
                "Target field '{0:s}' not found in the input MS!".format(target))

    logger.info(
        "Selected OTF scan field(s): {0:s} ...".format(
            str(target_field_list)[
                1:-1]))

    if len(target_field_list) > 1:
        logger.warning(
            'Currently only single target field processing is supported!')

    del target

    # Check for scan data selection
    if scans is not None:
        field_scan_dict = ms_wrapper.get_fieldname_and_ID_list_dict_from_MS(
            MS, scan_ID=True, ant1_ID=ant1_ID, ant2_ID=ant2_ID, close=False)

        target_field_scans = []

        for target in target_field_list:
            target_field_scans.extend(field_scan_dict[target])

        del target

        for sID in scans:
            if sID not in target_field_scans:
                raise ValueError(
                    'Target field(s) have no scan {0:d}'.format(sID))

        del sID

        # Get times
        times = ms_wrapper.get_time_based_on_field_names_and_scan_IDs(
            MS,
            field_names=target_field_list,
            scan_IDs=scans,
            to_UNIX=True,
            ant1_ID=ant1_ID,
            ant2_ID=ant2_ID,
            close=False)

    else:
        # Get times
        times = ms_wrapper.get_time_based_on_field_names_and_scan_IDs(
            MS,
            field_names=target_field_list,
            scan_IDs=None,
            to_UNIX=True,
            ant1_ID=ant1_ID,
            ant2_ID=ant2_ID,
            close=False)

    if timerange is not None:
        # The format should be already checked when timerange was parsered
        time_selection_start, time_selection_end = \
            a_time.convert_casa_timerange_selection_to_unix_times(timerange)

        selected_times = copy.deepcopy(a_time.subselect_timerange_from_times_array(
            times, start_time=time_selection_start, end_time=time_selection_end))

    else:
        selected_times = copy.deepcopy(times)

    del times

    # Close MS
    ms_wrapper.close_MS_table_object(MS)

    # This case is only if the selected timerange is smaller than the
    # visibility sampling interval
    if np.size(selected_times) == 0:
        raise ValueError(
            'No OTF pointing matches the data selection criteria!')

    # Reading in the pointing reference file (existence already checked)
    pointing_times = putil.get_times_from_reference_pointing_file(
        pointing_ref_path)

    # Generate selected-only values from the pointing array
    if timerange is not None:
        selected_pointing_times = copy.deepcopy(
            a_time.subselect_timerange_from_times_array(
                pointing_times,
                start_time=time_selection_start,
                end_time=time_selection_end))

    else:
        selected_pointing_times = copy.deepcopy(pointing_times)

    # Now get the cross matching
    cross_matched_reference_times = a_time.time_arrays_injective_intersection(
        selected_pointing_times,
        selected_times,
        quick_subselect=False,
        threshold=time_crossmatch_threshold)

    del selected_pointing_times, selected_times

    # TO DO: fix this log message
    if np.size(cross_matched_reference_times) == 0:
        raise ValueError('No valid OTF pointing selection can be made!')

    logger.info('{0:d} OTF pointings are selected...'.format(
        np.size(cross_matched_reference_times)))

    # === Configure output and garbage collection
    logger.debug('Configuring output and garbage collection...')

    OTF_acronym, MS_outname = putil.get_otfms_output_variables(
        args.config_file)

    # === Create pipeline
    logger.info('Building Snakemake pipeline...')

    # Copy Snakemake file from the template
    shutil.copyfile(snakefile_path, output_snakefile_path)

    # Create config.yaml
    snakemake_config = os.path.join(working_dir, 'config.yaml')

    # NOTE: the creation of the .yml file needs to be defined separately from the
    # pipeline config file as not all the same variables are used!

    # Remove if exist
    with open(snakemake_config, 'w') as sconfig:

        # NOTE: I only using spaces and not tabs as in YAML they should not be mixed!
        # I also not using the yaml module...

        sconfig.write('# Config file generated by arcane_suite at {0:s}\n'.format(
            str(datetime.datetime.now())))

        sconfig.write('working_dir:\n  {0:s}\n'.format(
            working_dir))
        sconfig.write('output_dir:\n  {0:s}\n'.format(
            os.path.join(working_dir, 'results')))
        sconfig.write(
            'output_otf_dir:\n  {0:s}\n'.format(
                os.path.join(
                    os.path.join(
                        working_dir,
                        'results'),
                    'otf_pointings')))
        sconfig.write('log_dir:\n  {0:s}\n'.format(
            os.path.join(working_dir, 'logs')))
        sconfig.write('MS:\n  {0:s}\n'.format(
            MS_path))
        sconfig.write('pointing_ref:\n  {0:s}\n'.format(
            pointing_ref_path))
        sconfig.write("OTF_acronym:  '{0:s}'\n".format(
            OTF_acronym))
        sconfig.write("MS_outname:  '{0:s}'\n".format(
            MS_outname))
        sconfig.write('time_crossmatch_threshold:  {0:.8f}\n'.format(
            time_crossmatch_threshold))
        sconfig.write('split_timedelta:  {0:.8f}\n'.format(
            split_timedelta))
        sconfig.write('position_crossmatch_threshold:  {0:.8f}\n'.format(
            position_crossmatch_threshold))
        sconfig.write("casa_alias:  '{0:s}'\n".format(
            command_line_tool_alias_dict['casa_alias']))
        sconfig.write("chgcentre_alias:  '{0:s}'\n".format(
            command_line_tool_alias_dict['chgcentre_alias']))

        # === List of calibrators and target fields

        # Calibrator field(s)
        sconfig.write(
            'split_calibrators: {0:s}\n'.format(
                str(split_calibrators)))

        if split_calibrators:
            sconfig.write('calibrator_fields:\n')
            for i in range(0, np.size(calibrator_list)):
                sconfig.write("  - {0:s}\n".format(calibrator_list[i]))
        else:
            sconfig.write('calibrator_fields:\n')

        # Target field(s)
        sconfig.write('target_fields:\n')
        for i in range(0, np.size(target_field_list)):
            sconfig.write("  - '{0:s}'\n".format(target_field_list[i]))

        # Build field_ID dict
        sconfig.write('otf_field_ID_mapping:\n')
        for i in range(0, np.size(cross_matched_reference_times)):
            sconfig.write(
                "  '{0:d}' : {1:f}\n".format(
                    i, cross_matched_reference_times[i]))

    # === Test if build was succesfull ===
    if not args.skip_snakemake_check:
        logger.info('Testing pipeline setup via dry run...')

        # Snakemake dry run (also creates a .snakemake hidden directory under the
        # working_dir)
        snakemake_proc = subprocess.run(
            'cd {0:s};  {1:s} -np'.format(working_dir, command_line_tool_alias_dict['snakemake_alias']),
            shell=True,
            capture_output=True)
        # Capture output
        out, err = snakemake_proc.stdout, snakemake_proc.stderr
        exitcode = snakemake_proc.returncode

        if exitcode != 0:
            # Snakemake puts everything in out, and nothing to err
            logger.error(out)
            # logger.debug(err)
            raise ValueError(
                'Unexpected error occurred in pipeline setup (see the Snakemake output above)!')

    else:
        logger.warning('Skipping dry run')  # Maybe this should be CRITICAL (?)

    # === Exit
    logger.info('Pipeline created')
    logger.info('Exit 0')
    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
