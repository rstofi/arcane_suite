"""Miscellaneous functions
"""
__all__ = ['convert_list_to_string',
           'str_to_bool',
           'rad_to_deg',
           'find_and_remove_files']

import sys
import os
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


def find_and_remove_files(parent_path,
                          file_extension,
                          file_pattern=None,
                          maxdepth=0):
    """
    Search for files with the specified file extension and file pattern (if provided)
    within the specified directory and its subdirectories, and removes them up to
    a certain depth.

    NOTE: maxdepth = 0 is the ``parenth_path`` directory, 1 is the first layer of
        subdirectories and so on.

    NOTE: this code removes the files matching the pattern and does not move them
        to the bin!

    NOTE: This docstring was created by ChatGPT3.

    Parameters:
    -----------
    parent_path: str
        The path of the parent directory to start searching in.

    file_extension: str
        The file extension of the files to search for.

    file_pattern: str, optional
        An optional pattern that the file name must match.

    maxdepth: int
        The maximum depth to search in. If 0, search the entire directory.

    Returns:
    -------
    Delete the selected files

    """
    cpath = parent_path.count(os.sep)  # Current path depth

    files_removed = 0

    # r = root dir, d = directories, f = files
    for r, d, f in os.walk(parent_path):
        if r.count(os.sep) - cpath <= maxdepth:
            for files in f:
                if files.endswith(file_extension):
                    if file_pattern is None:
                        logger.info(
                            "Removing file: {0:s}".format(
                                os.path.join(
                                    r, files)))
                        os.remove(os.path.join(r, files))

                        files_removed += 1

                    elif file_pattern in files:
                        logger.info(
                            "Removing file: {0:s}".format(
                                os.path.join(
                                    r, files)))
                        os.remove(os.path.join(r, files))

                        files_removed += 1

    # TO DO: add exception handling

    if file_pattern is None:
        logger.info(
            "Number of removed files with '{0:s}' extension: {1:d}".format(
                file_extension, files_removed))

    else:
        logger.info(
            "Number of removed files with '{0:s}' pattern and '{1:s}' extension: {2:d}".format(
                file_pattern,
                file_extension,
                files_removed))


# === MAIN ===
if __name__ == "__main__":
    pass
