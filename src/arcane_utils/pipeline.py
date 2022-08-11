"""Collection of utility functions general to initializing and handling pipelines
"""

__all__ = ['argflatten', 'get_common_env_variables', 'remove_comment',
            'init_logger', 'init_empty_config_file_with_common_variables',
            'is_command_line_tool']


import sys
import os
import logging
import configparser
import datetime
import yaml
import errno
import subprocess

from arcane_utils.globals import _VALID_LOG_LEVELS

#=== Set up logging
logger = logging.getLogger(__name__)

#=== Classes ===
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

#=== Functions ===
def init_logger(log_level='INFO', color=False):
    """Initialise the logger and formatting. This is a convinience function

    Parameters
    ----------
    log_level: str, optional
        The level of the logger

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

    handler = logging.StreamHandler(sys.stdout)

    if color:
        handler.setFormatter(CustomColorFormatter()) #Add coloured ciustom for logging
    else:
        formatter = logging.Formatter('%(asctime)s -- %(levelname)s: %(message)s')
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
            if t_args == None:
                subprocess.Popen([command_name], stdout=devnull, stderr=devnull).communicate()
            else:
                commands = [command_name] + t_args
                subprocess.Popen(commands, stdout=devnull, stderr=devnull).communicate()
        except OSError as e:
            try:
                #Open shell in interactive mode with /bin/bas/ loaded
                check_for_alias_proc = subprocess.run(['/bin/bash', '-i', '-c',
                            'command -v {0:s} > /dev/null'.format(command_name)])

                if check_for_alias_proc.returncode != 0:
                    return False
                else:
                    return True
            except:
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

    #Mandatory field: the working directory in which the Snakemake pipeline will be build
    try:
        working_dir = config.get('ENV','working_dir')

        working_dir = remove_comment(working_dir).strip()

        if working_dir == '':
            raise ValueError('Missing mandatory parameter: working_dir')
    except:
        raise ValueError('Mandatory parameter working_dir has to be specifyed')

    #Optional field in case the casa installation can be called by anything thanű
    #the casa command, e.g. casa6
    try:
        casa_alias = config.get('ENV','casa_alias')
        casa_alias = remove_comment(casa_alias).strip()

        if casa_alias == '':
            casa_alias = 'casa'
    except:
        casa_alias = 'casa'

    return working_dir, casa_alias

def init_empty_config_file_with_common_variables(template_path,
                                                pipeline_name,
                                                overwrite=True):
    """Initialise config file that can be used as a basis for other code to expand
    into an empty template config file.

    Parameters
    ----------
    template_path: str
        Path and name of the template created
    
    pipeline_name: str
        The name of the pipeline. Is written in the header line as an info
    
    overwrite: bool, opt
        If True the input file is overwritten, othervise an error is thrown
    
    Returns
    -------
    Create a template config file
    
    """
    if os.path.exists(template_path):
        if overwrite:
            logger.debug('Overwriting existin config file: {0:s}'.format(
                        template_path))
        else:
            raise FileExistsError('Config templete already exists!')

    with open(template_path, 'w') as aconfig:
        aconfig.write('# Template {0:s} pieline config file generated by \
arcane-suit at {1:s}\n'.format(pipeline_name, str(datetime.datetime.now())))

        aconfig.write('\n[ENV]\n')

        aconfig.write(f"{'working_dir':<30}" + f"{'= ':<5}" + '#Mandatory, path\n')
        aconfig.write(f"{'casa_alias':<30}" + f"{'= ':<5}" + '#Optional, str\n')

def get_var_from_yaml(yaml_path, var_name):
    """
    """

    with open(yaml_path) as file:
        try:
            yaml_dict = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError('Error while parsing the yaml file: {0:s}'.format(e))

    return yaml_dict[var_name]



#=== MAIN ===
if __name__ == "__main__":
    pass