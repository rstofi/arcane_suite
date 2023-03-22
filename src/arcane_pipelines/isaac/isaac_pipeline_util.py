"""Collection of utility functions unique to the `isaac` pipeline
"""

__all__ = ['init_config_for_otfms']

import sys
import logging
import configparser

from arcane_utils import pipeline

# Load pipeline default parameters
from arcane_pipelines.isaac import isaac_defaults

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===

def init_config_for_otfms(
        template_path:str,
        overwrite:bool=True,
        create_template:bool=False):
    """Generate an empty config file for the *otfms* pipeline. The resultant file
    can be filled by hand, to actually create an usable pipeline.

    NOTE: this is a wrapper around the default values defined in `cias_defaults.py`

    Parameters
    ----------
    template_path: str
        Path and name of the template created

    overwrite: bool, opt
        If True the input file is overwritten, othervise an error is thrown

    Returns
    -------
    Create a template config file

    """

    # Generate a basic template with the common variables used in all pipelines
    pipeline.init_empty_config_file_with_common_ENV_variables(
        template_path=template_path, pipeline_name='isaac', overwrite=overwrite)

    pipeline.add_aliases_to_config_file(
        template_path=template_path,
        aliases_list=isaac_defaults._isaac_default_aliases,
        defaults_list=isaac_defaults._isaac_default_alias_values)