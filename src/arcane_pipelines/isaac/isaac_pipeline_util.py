"""Collection of utility functions unique to the `isaac` pipeline
"""

__all__ = [
    'generate_config_template_for_isaac',
    'get_isaac_data_config',
    'get_isaac_data_selection_from_config']

import sys
import logging
import configparser

from arcane_utils import pipeline

# Load pipeline default parameters
from arcane_pipelines.isaac import isaac_defaults

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def generate_config_template_for_isaac(
        template_path: str,
        overwrite: bool = True,
        create_template: bool = False):
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

    pipeline.add_unique_defaults_to_config_file(
        template_path=template_path,
        unique_defaults_dict=isaac_defaults._isaac_default_config_dict)


def get_isaac_data_config(config_path: str):
    """
    Parameters
    ----------
    config_path: str
        Path to the config file initializing the pipeline

    Return
    ------
    from_otfms: bool
        Tf set to True, the data configuration is based on an `otfms` pipeline output

    """
    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        from_otfms = config['DATA_CONFIG'].getboolean('from_otfms')
    # If there are comments in the line
    except BaseException:
        from_otfms = config.get('DATA_CONFIG', 'from_otfms')
        from_otfms = pipeline.remove_comment(
            from_otfms).strip()

        try:
            from_otfms = misc.str_to_bool(from_otfms)
        except BaseException:
            logger.warning(
                "Invalid argument given to 'from_otfms', set it to False...")
            split_calibrators = False

    # logger.debug("The parameter 'from_otfms' is set to True...")

    # Get the 'from_otfms' param
    if from_otfms:
        otfms_output_path = config.get('DATA_CONFIG', 'from_otfms')
        otfms_output_path = pipeline.remove_comment(otfms_output_path).strip()

        if otfms_output_path == '':
            raise ValueError(
                "Missing parameter (based on 'from_otfms' = True): 'otfms_output_path'")

    else:
        otfms_output_path == ''

    # Get the 'otfms_acronym' param
    if from_otfms:
        otfms_acronym = config.get('DATA_CONFIG', 'otfms_acronym')
        otfms_acronym = pipeline.remove_comment(otfms_acronym).strip()

        if otfms_acronym == '':
            raise ValueError(
                "Missing parameter (based on 'from_otfms' = True): 'otfms_acronym'")

    return from_otfms, otfms_output_path, otfms_acronym


def get_isaac_data_selection_from_config(config_path: str):
    """

    """

    # Get the data config part first
    from_otfms, otfms_output_path, otfms_acronym = get_isaac_data_config(
        config_path)

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    # Populate input data paths from the output folder of `otfms`
    if from_otfms:
        logger.info("Populating data paths from 'otfms' pipeline output...")

        # Here I need a function that returns the data paths and checks if
        # everything exists

    # Populate input data paths from config
    else:
        logger.info("Populating data paths from the config file provided...")

        # Here I need to get some functions that populate the MS based on the
        # config file


# === MAIN ===
if __name__ == "__main__":
    pass
