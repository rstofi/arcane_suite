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

from arcane_pipelines.isaac import isaac_pipeline_util as putil
from arcane_pipelines.isaac import isaac_defaults

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

    parser.add_argument(
        '-sgc',
        '--skip_rule_graph_creation',
        required=False,
        help='If enabled, the rule graph is not generated',
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
            'Creating template config file for *isaac* pipeline from arcane_suite')

        if not args.overwrite_lock:
            putil.init_config_for_otfms(template_path=args.config_file)
        else:
            putil.init_config_for_otfms(template_path=args.config_file,
                                        overwrite=False)

        # TNow halt the program
        sys.exit(0)

    else:
        logger.info('Building *isaac* pipeline from arcane_suite')

    # Check if the config file exists
    if not os.path.exists(args.config_file):
        raise FileNotFoundError('Input config file does not exists!')

    # === Read the environment vales from the config file
    logger.info('Solving for environment...')

    # Get the ENV variables from config
    working_dir, log_level = pipeline.get_common_env_variables(
        args.config_file)

    # Update logger if the default log level is not INFO:
    if log_level != 'INFO':
        logger.info(
            "Updating logger level to '{0:s}' based on config file...".format(log_level))

        # Update the log level
        new_log_level = logging.getLevelName(log_level)

        logger.setLevel(new_log_level)
        utils_logger.setLevel(new_log_level)
        pipelines_logger.setLevel(new_log_level)

        del new_log_level

    # Get aliases
    command_line_tool_alias_dict = pipeline.get_aliases_for_command_line_tools(
        config_path=args.config_file,
        aliases_list=isaac_defaults._isaac_default_aliases,
        defaults_list=isaac_defaults._isaac_default_alias_values)

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
            command_line_tool_alias_dict['caracal_alias'])
    else:
        logger.warning('Skip checking for `caracal` installation')

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

    #=== Need to check for input data here!

    # Add checks here for the Snakefile if exists
    snakefile_path = os.path.join(
        os.path.dirname(
            sys.modules['arcane_pipelines.isaac'].__file__),
        'Snakefile')

    if not os.path.exists(snakefile_path):
        raise FileNotFoundError('Corrupted installation: Snakefile not found')

    output_snakefile_path = os.path.join(working_dir, 'Snakefile')

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

        sconfig.write("# Config file for 'isaac' pipeline Snakefile generated by arcane_suite at {0:s}\n".format(
            str(datetime.datetime.now())))

    # === Test if build was successful ===
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

    # === Create a DAG of the graph logic under `working_dir/reports/`

    if not args.skip_rule_graph_creation:

        logger.info("Creating workflow rule graph...")

        # Create results/ directory
        reports_dir = os.path.join(working_dir, 'reports')

        if not os.path.exists(reports_dir):
            os.mkdir(reports_dir)
        else:
            logger.debug('reports/ dir already exist, skipping creating it...')

        rule_graph_creating_process = subprocess.run(
            'cd {0:s}; {1:s} --rulegraph | dot -Tpng > {2:s}/rule_graph.png'.format(
                working_dir, command_line_tool_alias_dict['snakemake_alias'], reports_dir),
            shell=True, capture_output=True)

        out, err = rule_graph_creating_process.stdout, rule_graph_creating_process.stderr
        exitcode = rule_graph_creating_process.returncode

        if exitcode != 0:
            logger.warning(
                "Unexpected error in rulegraph creation (probably `dot` is not installed)!")

    # === Exit
    logger.info('Pipeline created')
    logger.info('Exit 0')
    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
