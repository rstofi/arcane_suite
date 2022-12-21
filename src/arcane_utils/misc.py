"""Miscellaneous functions
"""
__all__ = ['convert_list_to_string', 'str_to_bool', 'rad_to_deg']


import sys
import logging

import numpy as np

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def convert_list_to_string(list_to_convert):
    """Litarally convert a list to a string with format:

    [element_1,...,element_N]

    Parameters
    ----------
    list_to_convert: list of anything
        The list to be converted

    Returns
    -------
    literal_list_string: str
        The string created from the list

    """
    literal_list_string = '['
    listToStr = ','.join(map(str, list_to_convert))

    literal_list_string += listToStr + ']'

    return literal_list_string


def str_to_bool(bool_string):
    """Convert a string to a boolean value. Working for the following strings:
        - True
        - true
        - False
        - false

    NOTE that VAlueERROR is raised is the string is invalid

    Parameters:
    -----------
    bool_string: str
        The string to convert

    Returns
    -------
    bool_val: bool
        The boolean equivalent of the string

    """
    if bool_string == 'True':
        bool_val = True
    elif bool_string == 'true':
        bool_val = True
    elif bool_string == 'False':
        bool_val = False
    elif bool_string == 'false':
        bool_val = False
    else:
        raise ValueError('Invalid string passed to `str_to_bool()`!')

    return bool_val


def rad_to_deg(x):
    """
    """
    return ((x * 180) / np.pi)


# === MAIN ===
if __name__ == "__main__":
    pass
