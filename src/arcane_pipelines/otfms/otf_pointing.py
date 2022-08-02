"""Collection of utility functions unique to the otfms pipeline
"""

__all__ = ['get_otfms_data_variables', 'get_data_selection_from_config']

import sys
import logging
import configparser
import re

#=== Set up logging
logger = logging.getLogger(__name__)


#=== Functions ===
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

def get_data_selection_from_config(config_path):
	"""Reads the data selection for the OTF to MS conversion from the config file:

	In the config file the calibrators and targets MUST be specifyed. The other
	selection options are optional. If no values are specifyed, all scans and times
	will be used for the OTF to MS conversion.

	The fields and scans have to be separated by commas in the config file, while
	the timerange should be a string specifying a CASA-compatible time selection.

	See the syntax here: https://casacore.github.io/casacore-notes/263.html#x1-80002

	NOTE: that the timerange currently can handle only a single time interval!

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

	scans: list of int or

	"""
	config = configparser.ConfigParser(allow_no_value=True)
	config.read(config_path)

	#Mandatory
	calibrator_list =  [s.strip() for s in config.get('DATA','calibrator_list').split(',')]
	target_field_list = [s.strip() for s in config.get('DATA','target_field_list').split(',')]
	
	#Optional
	timerange = str(config.get('DATA','timerange'))
	if len(timerange) == 0:
		timerange = None

	scans = list(str(config.get('DATA','scans')).split(','))
	if len(scans) > 1:
		try:
			scans = list(map(int,scans)) #Map str to int
		except:
			logger.warning('Invalid scan ID(s): ignoring user input and use all scans...')
			scans = None
	else:
		try:
			scans = list(map(int,scans)) #Map str to int
		except:
			scans = None

	return calibrator_list, target_field_list, timerange, scans

#=== MAIN ===
if __name__ == "__main__":
    pass