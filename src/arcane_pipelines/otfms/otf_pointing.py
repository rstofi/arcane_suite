"""Collection of utility functions unique to the otfms pipeline
"""

__all__ = ['get_otfms_data_variables', 'get_otfms_data_selection_from_config',
            'init_empty_config_for_otfms']

import sys
import logging
import configparser
import re

from arcane_utils import pipeline
from arcane_utils import time as a_time

#=== Set up logging
logger = logging.getLogger(__name__)


#=== Functions ===
def init_empty_config_for_otfms(template_path, overwrite=True):
    """Generate an empty config file for the *otfms* pipeline. The resultant file
    can be filled by hand, to actually create an usable pipeline.

    NOTE that all the possible control parameters *uniqe* to the otfms pipeline
    should be in this function.

    TO DO: if too many control options are implemented re-structure the code

    Parameters
    ==========
    template_path: str
        Path and name of the template created

    overwrite: bool, opt
        If True the input file is overwritten, othervise an error is thrown

    Returns:
    ========
    Create a template config file

    """

    #Generate a basic template with the common variables used in all pipelines
    pipeline.init_empty_config_file_with_common_variables(template_path=template_path,
                                                    pipeline_name='otfms',
                                                    overwrite=overwrite)

    #Given that the config template is generated append wuth the relevant sections
    with open(template_path, 'a') as aconfig:

        aconfig.write('\n[DATA]\n')

        aconfig.write(f"{'MS':<30}" + '= #mandatory\n')
        aconfig.write(f"{'pointing_ref':<30}" + '= #mandatory\n')
        aconfig.write(f"{'calibrator_list':<30}" + '= #mandatory\n')
        aconfig.write(f"{'target_field_list':<30}" + '= #mandatory\n')
        aconfig.write(f"{'scans':<30}" + '= \n')
        aconfig.write(f"{'timerange':<30}" + '= \n')
        aconfig.write(f"{'ant1_ID':<30}" + '= \n')
        aconfig.write(f"{'ant2_ID':<30}" + '= \n')


def get_otfms_data_variables(config_path):
    """Read the environmental variables unique to initalise the otfms pipeline
    
    Parameters
    ==========
    config_path: str
        Path to the config file initializing the pipeline
    
    Return
    ======
    MS_dir: str
        Path to the input MS directory

    pointing_ref: str
        Path to the single-dish reference antenna pointing file. Should be an
        .npz file with [ra, dec, time] arrays

    """
    config = configparser.ConfigParser()
    config.read(config_path)

    MS_dir = config.get('DATA','MS')
    pointing_ref = config.get('DATA','pointing_ref')

    return MS_dir, pointing_ref

def get_otfms_data_selection_from_config(config_path):
    """Reads the data selection for the OTF to MS conversion from the config file:

    In the config file the calibrators and targets MUST be specifyed. The other
    selection options are optional. If no values are specifyed, all scans and times
    will be used for the OTF to MS conversion.

    The fields and scans have to be separated by commas in the config file, while
    the timerange should be a string specifying a CASA-compatible time selection.

    See the syntax here: https://casacore.github.io/casacore-notes/263.html#x1-80002

    NOTE: that the timerange currently can handle only a single time interval!

    NOTE: the try syntax is needed to handle the optional parameters even if they
            are not defined in the parset file!

    Parameters
    ==========
    config_path: str
        Path to the config file initializing the pipeline
    
    Return
    ======
    calibrator_list: list of str
        A list of the calibrator field names to use

    target_field_list: list of str
        A list of the traget fields

    timerange: str or None
        A timerange for which the OTF pointings will be selected

    scans: list of int or None
        A list of scans used for the data selection

    ant1_ID: int
        The ID of a reference antenna used for the baseline selection.
        This *should* be the ID of the antenna used to generate the `pointing_ref`
        data file! Default value is 0 if not specified

    ant1_ID: int
        The second antenna used for the reference baseline in data selection. The
        default value is 1 or 0 if `ant1_ID` is set to be one


    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    #Mandatory
    calibrator_list =  [s.strip() for s in config.get('DATA','calibrator_list').split(',')]
    target_field_list = [s.strip() for s in config.get('DATA','target_field_list').split(',')]
    
    #Optional
    try:
        timerange = config.get('DATA','timerange', fallback=None)

        #If no value is provided
        if timerange.strip() == '': 
            timerange = None
        else:
            #Check for format (check are inside the function)
            _ = a_time.convert_casa_timerange_selection_to_unix_times(timerange)

    except Exception as e: #Catch the error message
        logger.warning('An error occured while parsing timerange value:', exc_info=e)
        logger.info('Setting timerange to None')
        timerange = None
    
    try: #If a single scan ID is provided
        scans = list(config.getint('DATA','scans', fallback=None))
    except:
        #Check if empty string is given
        scans = str(config.get('DATA','scans'))
        if scans.strip() == '':
            scans = None
        else:
            #Tre yto get info from input
            scans = list(scans.split(','))
            try:
                scans = list(map(int,scans)) #Map str to int
            except:
                logger.warning('Invalid scan ID(s): ignoring user input and use all scans...')
                scans = None

    try:
        ant1_ID = config.getint('DATA','ant1_ID', fallback=0) 
    except ValueError:
        ant1_ID_string = config.get('DATA','ant1_ID')
        
        if ant1_ID_string.strip() != '':
            logger.warning('Invalid ID format for ant1_ID!')
            logger.info('Setting ant1_ID to 0')

        ant1_ID = 0

    try:
        ant2_ID = config.getint('DATA','ant2_ID', fallback=1)
    except ValueError:
        ant2_ID_string = config.get('DATA','ant2_ID')
        
        if ant2_ID_string.strip() != '':
            logger.warning('Invalid ID format for ant2_ID!')
            logger.info('Setting ant2_ID to 1')

        ant2_ID = 1

    if ant1_ID == ant2_ID:
        if ant1_ID != 0:
            ant2_ID = 0
        else:
            ant2_ID = 1

    return calibrator_list, target_field_list, timerange, scans, ant1_ID, ant2_ID

#=== MAIN ===
if __name__ == "__main__":
    pass