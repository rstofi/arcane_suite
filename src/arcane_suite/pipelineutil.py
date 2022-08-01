"""Collection of utility functions general to initialising and handling pipelines
"""

__all__ = ['argflatten', 'get_common_env_variables']


import sys
import logging
import configparser

#=== Set up logging
logger = logging.getLogger(__name__)

#=== Functions ===
def argflatten(arg_list):
    """Some argparser list arguments can be actually list of lists.
    This is a simple routine to faltten list of lists to a simple list.

    Parameters
    ==========
    arg_list: list of lists
        Value of a list argument needs to be flatten
    
    Return
    ======
    arg_as_list: list
        The flattened list of lists
    
    """
    return [p for sublist in arg_list for p in sublist]

def get_common_env_variables(config_path):
	"""
	"""
	config = configparser.ConfigParser()
	config.read(config_path)

	working_dir = config.get('ENV','working_dir')

	return working_dir

#=== MAIN ===
if __name__ == "__main__":
    pass