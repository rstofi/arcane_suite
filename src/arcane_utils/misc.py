"""Miscellaneous functions
"""
__all__ = ['convert_list_to_string']


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


def rad_to_deg(x):
    """
    """
    return ((x * 180) / np.pi)


# === MAIN ===
if __name__ == "__main__":
    pass
