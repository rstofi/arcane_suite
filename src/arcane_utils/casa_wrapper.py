"""Collection of wrapper functions working with CASA tasks externally. This module
is expected to be used across several pipelines of the suite.
"""

__all__ = ['check_casa_installation']

import sys
import logging
import warnings

from shutil import which

from arcane_utils import pipeline

from arcane_utils.globals import _CASA_BASE_NAME


# === Set up logging
logger = logging.getLogger(__name__)


# === Functions ===

def check_casa_installation(casa_alias, pedantic=False):
    """Simple routine that check if there is a CASA software installed by which,
    then it also checks if there is a casa executable defined by the `casa_alias`
    argument.

    Parameters
    ----------
    casa_alias: str
        The command-line alias to call CASA (e.g. casa, casa6)

    pedantic: bool, opt
        If set to True, the function halts the program if no CASA installation is found

    Returns
    -------
    If CASA is installed None, otherwise logs and potentiall raises an error

    """
    # Check if CASA is installed as CASA
    is_casa_installed = False

    casa_installations = which(_CASA_BASE_NAME)

    if casa_installations is not None:
        logger.debug(
            'Found CASA installation at: {}'.format(casa_installations))

        is_casa_installed = True

    if pipeline.is_command_line_tool(casa_alias,
                                     t_args=[
            '--log2term',
            '--nogui',
            '--nologfile']) == False:
        if is_casa_installed:
            logger.critical("No CASA installation found that can be called \
via the '{0:s}' command, but found a CASA installation under {1:s} . Please change \
the casa_alias in the config file!".format(
                casa_alias, casa_installations))

        else:
            if pedantic:
                raise ValueError("No CASA installation found!")
            else:
                logger.critical("No CASA installation found!")


# === MAIN ===
if __name__ == "__main__":
    pass
