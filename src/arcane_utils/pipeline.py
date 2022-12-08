"""Collection of utility functions general to initializing and handling pipelines
"""

__all__ = [
    'argflatten',
    'get_common_env_variables',
    'remove_comment',
    'init_logger',
    'init_empty_config_file_with_common_ENV_variables',
    'is_command_line_tool',
    'get_aliases_for_command_line_tools',
    'add_aliases_to_config_file',
    'add_unique_defaults_to_config_file']

import sys
import os
import logging
import configparser
import datetime
import yaml
import errno
import subprocess

from arcane_utils.globals import _VALID_LOG_LEVELS

# === Set up logging
logger = logging.getLogger(__name__)

# === Classes ===


class CustomColorFormatter(logging.Formatter):
    """Custom formatter for logging, that add different color for the different
    log levels

    stolen from: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    #format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = '%(asctime)s -- %(levelname)s: %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# === Functions ===


def init_logger(log_level='INFO', color=False,
                log_file=None, null_logger=False):
    """Initialize the logger and formatting. This is a convenience function

    Parameters
    ----------
    log_level: str, optional
        The level of the logger

    color: bool, optional
        If True the logger will be colored by levels

    log_file: str, optional
        If given the log will go to this file rather than to stdout

    Returns
    -------
    Logger object
    """
    if log_level not in _VALID_LOG_LEVELS:
        raise ValueError('Invalid log level!')

    logger = logging.getLogger()

    if log_level == 'CRITICAL':
        logger.setLevel(logging.CRITICAL)
    elif log_level == 'ERROR':
        logger.setLevel(logging.ERROR)
    elif log_level == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif log_level == 'INFO':
        logger.setLevel(logging.INFO)
    elif log_level == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.NOTSET)

    if null_logger:
        handler = logging.NullHandler()
    elif log_file is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(log_file)

    if color:
        # Add coloured ciustom for logging
        handler.setFormatter(CustomColorFormatter())
    else:
        formatter = logging.Formatter(
            '%(asctime)s -- %(levelname)s: %(message)s')
        handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def is_command_line_tool(command_name, t_args=None):
    """Function to check if a string is a valid callable command-line tool.
    Usedult to check id e.g. snakemake is isnatalled on a system...

    This is kinda a hacky code based on:
    https://stackoverflow.com/questions/11210104/check-if-a-program-exists-from-a-python-script
    https://stackoverflow.com/questions/12060863/python-subprocess-call-a-bash-alias

    Basically do a call of the command using a plane envinroment and if there
    is an error with the command, i.e. because it is an alias. The code attempts
    to load /bin/bash/ in an interactive mode (which includes .bashrc)

    NOTE: if a command

    Parameters
    ----------
    command name: str
        The command-line tool name to test

    t_args: list of string, optional
        Additional arguments that can be passed to the code to be tested. Especially
        useful for e.g. passing --nogui and --nologfile when testing casa

    Retruns
    -------
    True, if such a tool exists, False otherwise


    """

    try:
        devnull = open(os.devnull)
        #devnull =  subprocess.DEVNULL
        if t_args is None:
            subprocess.Popen([command_name], stdout=devnull,
                             stderr=devnull).communicate()
        else:
            commands = [command_name] + t_args
            subprocess.Popen(commands, stdout=devnull,
                             stderr=devnull).communicate()
    except OSError as e:
        try:
            # Open shell in interactive mode with /bin/bas/ loaded
            check_for_alias_proc = subprocess.run(
                ['/bin/bash', '-i', '-c', 'command -v {0:s} > /dev/null'.format(command_name)])

            if check_for_alias_proc.returncode != 0:
                return False
            else:
                return True
        except BaseException:
            if e.errno == errno.ENOENT:
                return False
    return True


def argflatten(arg_list):
    """Some argparser list arguments can be actually list of lists.
    This is a simple routine to flatten list of lists to a simple list.

    Parameters
    ----------
    arg_list: list of lists
        Value of a list argument needs to be flatten

    Returns
    -------
    arg_as_list: list
        The flattened list of lists

    """
    return [p for sublist in arg_list for p in sublist]


def remove_comment(arg_string, comment_character='#'):
    """Remove a comment from a string, where the comment is the end of the string
    and starts with the `comment_character`. This is useful to handle argparse
    arguments with comments

    The `comment_character` is # by default!

    NOTE: this gonna cause problems if the arparse input string contains a # character!

    Parameters
    ----------
    arg_string: str
        String to remove the comment from

    comment_character: str
        A character indicating the beginning of the comment

    Returns
    -------
    The string without the comment

    """
    return arg_string.split(comment_character)[0]


def get_common_env_variables(config_path):
    """Read environmental variables common across ALL pipelines of arcane-suite
    during initialization

    Parameters
    ----------
    config_path: str
        Path to the config file initializing the pipeline

    Returns
    -------
    working_dir: str
        Path to the working directory in which the pipeline will be initialized

    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    # Mandatory field: the working directory in which the Snakemake pipeline
    # will be build
    try:
        working_dir = config.get('ENV', 'working_dir')

        working_dir = remove_comment(working_dir).strip()

        if working_dir == '':
            raise ValueError('Missing mandatory parameter: working_dir')
    except BaseException:
        raise ValueError('Mandatory parameter working_dir has to be specified')

    return working_dir


def get_aliases_for_command_line_tools(
        config_path, aliases_list, defaults_list):
    """This subroutine can be used to get a list of aliases from the ENV variables.

    The aliases have to be provided as a list of int, an the output is a dictionary
    with the keys as aliases, with the aliases defined in the config, being the
    values. If no values are provided, the alias name is subtracted from the `defaults_list`
    array.

    NOTE: each pipeline, should have their defaults_list defined in the `_pipeline_util.py` code

    Parameters
    ----------
    config_path: str
        Path to the config file initializing the pipeline

    aliases: list of str
        A list of the alias names that could be defined in the config file, e.g.
        `casa_alias`

    defaults_list: list of str
        A list of the default values for the command line tools that can be aliased,
        e.g. 'casa6'

    Returns
    -------
    command_line_tool_alias_dict: dict
        A dictionary with each alias paired with the alias defined in the config,
        or with the value from the `defaults_list`, if the alias is not defined
        in the config

    """
    if len(aliases_list) != len(defaults_list):
        raise ValueError(
            'The input aliases and defaults lists have different shape!')

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    command_line_tool_alias_dict = {}

    for i in range(0, len(aliases_list)):
        try:
            command_line_tool_alias = config.get('ENV', aliases_list[i])
            command_line_tool_alias = remove_comment(
                command_line_tool_alias).strip()

            if command_line_tool_alias == '':
                command_line_tool_alias = defaults_list[i]
        except BaseException:
            command_line_tool_alias = defaults_list[i]

        command_line_tool_alias_dict[aliases_list[i]] = command_line_tool_alias

    return command_line_tool_alias_dict


def init_empty_config_file_with_common_ENV_variables(template_path,
                                                     pipeline_name,
                                                     overwrite=True):
    """Initialize config file that can be used as a basis for other code to expand
    into an empty template config file.

    Parameters
    ----------
    template_path: str
        Path and name of the template config created

    pipeline_name: str
        The name of the pipeline. Is written in the header line as an info

    overwrite: bool, opt
        If True the input file is overwritten, otherwise an error is thrown

    Returns
    -------
    Create a template config file

    """
    if os.path.exists(template_path):
        if overwrite:
            logger.debug('Overwriting existing config file: {0:s}'.format(
                template_path))
        else:
            raise FileExistsError('Config template already exists!')

    with open(template_path, 'w') as aconfig:
        aconfig.write('# Template {0:s} pipeline config file generated by \
arcane_suit at {1:s}\n'.format(pipeline_name, str(datetime.datetime.now())))

        aconfig.write('\n[ENV]\n')

        aconfig.write(f"{'working_dir':<30}" +
                      f"{'= ':<5}" + '#Mandatory, absolute path\n')


def add_aliases_to_config_file(
        template_path,
        aliases_list,
        defaults_list=None):
    """The pipelines defined in `arcane_suite` have the defaults stored in a
    `pipeline_name_defaults.py` file. The command-line tools can be aliased, so
    I have set up two lists in this file:

    `_pipeline_name_default_aliases` & `_pipeline_name_default_alias_values`

    This script should get these arrays and append a template config file with the
    alias names and empty strings (+ comments) or can write the default values if
    the `default_list is given`

    NOTE: in any pipeline the aliases should be optional values!

    TO DO: make sure that the aliases are appended to the [ENV] section

    NOTE: the best usage of this function is to call it after
        `init_empty_config_file_with_common_ENV_variables`, so the aliases are
        appended into the ENV section

    Parameters
    ----------
    template_path: str
        Path and name of the template config created

    aliases: list of str
        A list of the alias names that could be defined in the config file, e.g.
        `casa_alias`

    defaults_list: list of str
        A list of the default values for the command line tools that can be aliased,
        e.g. 'casa6'

    Returns
    -------
    Appends the aliases to the template config file

    """

    # The template should exist, and if not we throw an error
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            'Config template does not exists, please create it first!')

    with open(template_path, 'a') as aconfig:

        if defaults_list is None:
            for i in aliases_list:
                aconfig.write(
                    f"{'{0:s}'.format(i):<30}" +
                    f"{'= ':<5}" +
                    '#Optional, string\n')

        else:
            if len(aliases_list) != len(defaults_list):
                raise ValueError(
                    'The input aliases and defaults lists have different shape!')
            else:
                for i, j in zip(aliases_list, defaults_list):
                    aconfig.write(
                        f"{'{0:s}'.format(i):<30}" +
                        f"{'= ':<5}" +
                        '{0:s} '.format(j) +
                        '#Optional, string\n')


def add_unique_defaults_to_config_file(template_path, unique_defaults_dict):
    """The pipelines defined in `arcane_suite` have the defaults stored in a
    `pipeline_name_defaults.py` file.

    The unique sections and variables should be stored in this file in the following
    format of a nested dict:

    ```
    unique_defaults_dict = {'UNIQUE_SECTION_1':{'unique_var_1:unique_var_values_1',
                                                'unique_var_N:unique_var_values_N'},
                         'UNIQUE_SECTION_N':{'unique_var_1:unique_var_values_1',
                                            'unique_var_N:unique_var_values_N'}}

    ```

    Where the `unique_var_values` should be lists with length of 3, with the
    following values and types:

    ```
    [default value, mandatory (True = yes), description of the type]
    [str, bool, str]

    ```

    This code, gets a dictionary of the format described above and appends it
    in the proper format at the end of a template config file.

    NOTE: the EVN section of the dict is ignored!

    TO DO: add an option to use only the unique variables that should go to the ENV section

    NOTE: the best usage of this function is to call it after
        `init_empty_config_file_with_common_ENV_variables`, or after the
        `add_aliases_to_config_file` function, so the aliases are
        appended into the ENV section

    Parameters
    ----------
    template_path: str
        Path and name of the template config created

    unique_defaults_dict: dict
        The dictionary defined above

    Returns
    -------
    Appends the unique sections and variables to the template config file

    """

    # The template should exist, and if not we throw an error
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            'Config template does not exists, please create it first!')

    with open(template_path, 'a') as aconfig:
        for unique_sections in unique_defaults_dict:
            if unique_sections != 'ENV':
                aconfig.write('\n[{0:s}]\n'.format(unique_sections))

                for unique_params in unique_defaults_dict[unique_sections]:

                    if unique_defaults_dict[unique_sections][unique_params][1]:
                        aconfig.write(
                            f"{'{0:s}'.format(unique_params):<30}" +
                            f"{'= ':<5}" +
                            '#Mandatory, {0:s}\n'.format(
                                unique_defaults_dict[unique_sections][unique_params][2]))
                    else:
                        aconfig.write(
                            f"{'{0:s}'.format(unique_params):<30}" +
                            f"{'= ':<5}" +
                            '#Optional, {0:s}\n'.format(
                                unique_defaults_dict[unique_sections][unique_params][2]))


def get_var_from_yaml(yaml_path, var_name):
    """Simple routine to read variables from a .yml file

    Parameters
    ----------
    yaml_path: str
        Absolute path to the .yaml file

    var_name:
        The name of the variable which value we want to read from the file

    Returns
    -------
    The selected value

    """

    with open(yaml_path) as file:
        try:
            yaml_dict = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(
                'Error while parsing the yaml file: {0:s}'.format(e))

    return yaml_dict[var_name]


# === MAIN ===
if __name__ == "__main__":
    pass
