"""Collection of utility functions general to initializing and handling pipelines
"""

__all__ = ['argflatten', 'get_common_env_variables', 'remove_comment',
            'init_logger', 'init_empty_config_file_with_common_variables']


import sys
import os
import logging
import configparser
import datetime
import yaml

from arcane_utils.globals import _VALID_LOG_LEVELS

#=== Set up logging
logger = logging.getLogger(__name__)

#=== Functions ===
def init_logger(log_level='INFO'):
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
    formatter = logging.Formatter('%(asctime)s -- %(levelname)s: %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

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
	config = configparser.ConfigParser()
	config.read(config_path)

	working_dir = config.get('ENV','working_dir')

	return working_dir

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

        aconfig.write(f"{'working_dir':<30}" + '= #mandatory\n')

def get_dict_from_yaml(yaml_path, dict_name):
    """
    """

    with open(yaml_path) as file:
        try:
            yaml_dict = yaml.safe_load(file)   
        except yaml.YAMLError as exc:
            print(exc)

    return yaml_dict[dict_name]



#=== MAIN ===
if __name__ == "__main__":
    pass