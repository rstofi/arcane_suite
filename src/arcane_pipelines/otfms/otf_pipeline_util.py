"""Collection of utility functions unique to the otfms pipeline
"""

__all__ = ['get_otfms_data_variables', 'get_otfms_data_selection_from_config',
            'init_empty_config_for_otfms', 'get_times_from_reference_pointing_file',
            'get_pointing_from_reference_pointing_file',
            'get_pointing_and_times_from_reference_pointing_file']

import sys
import logging
import configparser
import numpy as np

from astropy.time import Time

from arcane_utils import pipeline
from arcane_utils import time as a_time

from astropy.coordinates import SkyCoord
from astropy import units as u

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
    ----------
    template_path: str
        Path and name of the template created

    overwrite: bool, opt
        If True the input file is overwritten, othervise an error is thrown

    Returns
    -------
    Create a template config file

    """

    #Generate a basic template with the common variables used in all pipelines
    pipeline.init_empty_config_file_with_common_variables(template_path=template_path,
                                                    pipeline_name='otfms',
                                                    overwrite=overwrite)

    #Given that the config template is generated append wuth the relevant sections
    with open(template_path, 'a') as aconfig:

        aconfig.write('\n[DATA]\n')

        aconfig.write(f"{'MS':<30}" + f"{'= ':<5}" + '#Mandatory, path\n')
        aconfig.write(f"{'pointing_ref':<30}" + f"{'= ':<5}" + '#Mandatory, path\n')
        aconfig.write(f"{'calibrator_list':<30}" + f"{'= ':<5}" + \
            '#Mandatory, comma separated list\n')
        aconfig.write(f"{'target_field_list':<30}" + f"{'= ':<5}" + \
                                        '#Mandatory, comma separated list\n')
        aconfig.write(f"{'scans':<30}" + f"{'= ':<5}" + \
            '#Optional, comma separated list of scan IDs\n')
        aconfig.write(f"{'timerange':<30}" + f"{'= ':<5}" + '#Optional, \
 formatted as yyyy/mm/dd/hh:mm:ss.ss~yyyy/mm/dd/hh:mm:ss.ss\n')
        aconfig.write(f"{'ant1_ID':<30}" + f"{'= ':<5}" + '#Optional, int\n')
        aconfig.write(f"{'ant2_ID':<30}" + f"{'= ':<5}" + '#Optional, int\n')
        aconfig.write(f"{'time_crossmatch_threshold':<30}" + f"{'= ':<5}" + \
                '#Optional, float\n')
        aconfig.write(f"{'split_timedelta':<30}" + f"{'= ':<5}" + \
                '#Optional, float\n')

def get_otfms_data_variables(config_path):
    """Read the environmental variables unique to initalise the otfms pipeline
    
    Parameters
    ----------
    config_path: str
        Path to the config file initializing the pipeline
    
    Return
    ------
    MS_dir: str
        Path to the input MS directory

    pointing_ref: str
        Path to the single-dish reference antenna pointing file. Should be an
        .npz file with [ra, dec, time] arrays

    """
    config = configparser.ConfigParser()
    config.read(config_path)

    MS_dir = config.get('DATA','MS')
    MS_dir = pipeline.remove_comment(MS_dir).strip()

    if MS_dir == '':
        raise ValueError('Missing mandatory parameter: MS')

    pointing_ref = config.get('DATA','pointing_ref')
    pointing_ref = pipeline.remove_comment(pointing_ref).strip()

    if pointing_ref == '':
        raise ValueError('Missing mandatory parameter: pointing_ref')    

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
    ----------
    config_path: str
        Path to the config file initializing the pipeline
    
    Return
    ------
    calibrator_list: list of str
        A list of the calibrator field names to use

    target_field_list: list of str
        A list of the traget fields

    timerange: str or None, optional
        A timerange for which the OTF pointings will be selected

    scans: list of int or None
        A list of scans used for the data selection

    ant1_ID: int, optional
        The ID of a reference antenna used for the baseline selection.
        This *should* be the ID of the antenna used to generate the `pointing_ref`
        data file! Default value is 0 if not specified

    ant1_ID: int, optional
        The second antenna used for the reference baseline in data selection. The
        default value is 1 or 0 if `ant1_ID` is set to be one

    time_crossmatch_threshold: float, optional
        The treshold in which below two timestamps from the reference pointing
        and the MS are considered to be the same

    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    #Mandatory
    calibrator_list =  [pipeline.remove_comment(s).strip() for s in config.get('DATA','calibrator_list').split(',')]
    target_field_list = [pipeline.remove_comment(s).strip() for s in config.get('DATA','target_field_list').split(',')]

    if len(calibrator_list) == 1 and calibrator_list[0] == '':
        raise ValueError('Missing mandatory parameter: calibrator_list')
    if len(target_field_list) == 1 and target_field_list[0] == '':
        raise ValueError('Missing mandatory parameter: target_field_list')

    #Optional
    try:
        timerange = config.get('DATA','timerange', fallback=None)
        timerange = pipeline.remove_comment(timerange)

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
        scans = pipeline.remove_comment(scans)

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
        ant1_ID_string = pipeline.remove_comment(ant1_ID_string)

        try:
            ant1_ID = int(ant1_ID_string)
        except:
            if ant1_ID_string.strip() != '':
                logger.warning('Invalid format for ant1_ID!')
                logger.info('Setting ant1_ID to 0')

            ant1_ID = 0

    try:
        ant2_ID = config.getint('DATA','ant2_ID', fallback=1)
    except ValueError:
        ant2_ID_string = config.get('DATA','ant2_ID')
        ant2_ID_string = pipeline.remove_comment(ant2_ID_string)
        try:
            ant2_ID = int(ant2_ID_string)
        except:        
            if ant2_ID_string.strip() != '':
                logger.warning('Invalid format for ant2_ID!')
                logger.info('Setting ant2_ID to 1')

            ant2_ID = 1

    if ant1_ID == ant2_ID:
        if ant1_ID != 0:
            logger.warning('ant1_ID and ant2_ID are equal, setting ant2_ID to 0')
            ant2_ID = 0
        else:
            logger.warning('ant1_ID and ant2_ID are equal, setting ant2_ID to 1')
            ant2_ID = 1

    #Note that ANTENNA1 *always* have a smaller ID number than ANTENNA2 in an MS
    # So for a general case, we need to swap the two IDs if ant1_ID > ant2_ID

    if ant1_ID > ant2_ID:
        logger.debug('Swapping ant1_ID and ant2_ID to make sure baseline exists in MS')
        ant1_ID, ant2_ID = ant2_ID, ant1_ID #Swapping two variables without a teporary variable


    #Default is to set to be 0.001 i.e. a millisecond
    try:
        time_crossmatch_threshold = config.getfloat('DATA','time_crossmatch_threshold', fallback=0.001)
    except ValueError:
        time_crossmatch_threshold_string = config.get('DATA','time_crossmatch_threshold')
        time_crossmatch_threshold_string = pipeline.remove_comment(time_crossmatch_threshold_string)

        if time_crossmatch_threshold_string.strip() != '':
            logger.warning('Invalid format format for time_crossmatch_threshold!')
            logger.info('Setting time_crossmatch_threshold to 0.0001')

        time_crossmatch_threshold = 0.0001

    #Default is to set to be 0.5s so the time selection will happen within +/- 0.25 s 
    try:
        split_timedelta = config.getfloat('DATA','split_timedelta', fallback=0.5)
    except ValueError:
        split_timedelta_string = config.get('DATA','split_timedelta')
        split_timedelta_string = pipeline.remove_comment(split_timedelta_string)

        if split_timedelta_string.strip() != '':
            logger.warning('Invalid format format for split_timedelta!')
            logger.info('Setting split_timedelta to 1')

        split_timedelta = 0.5

    return calibrator_list, target_field_list, timerange, scans, ant1_ID, ant2_ID, \
            time_crossmatch_threshold, split_timedelta

def get_times_from_reference_pointing_file(refrence_pointing_npz):
    """Get the `time` array from the reference antenna pointing
    file. The file should be a numpy-generated .npz binary file (not pickled though!)

    The time array should be in UNIX format

    Parameters
    ----------
    reference_pointing: str
        The path to the .npz file

    Returns
    -------
    time_array: numpy array of float
        The times in Unix format

    """
    #Get the time array
    times = Time(np.load(refrence_pointing_npz)['time'], format='unix')

    if a_time.soft_check_if_time_is_UNIX(times[0].value) == False:
        logger.warning('Reference pointing times are not in UNIX format!')

    time_array = times.value

    return time_array

def get_pointing_from_reference_pointing_file(refrence_pointing_npz):
    """et the `ra` and `dec` arrays from the reference antenna pointing
    file. The file should be a numpy-generated .npz binary file (not pickled though!)

    The ra and dec arrays should be in degrees

    Parameters
    ----------
    reference_pointing: str
        The path to the .npz file

    Returns
    -------
    ra_array: numpy array of float
        The pointing RA value in degrees

    dec_array: numpy array of float

    """
    ra_array = np.load(refrence_pointing_npz)['ra']
    dec_array = np.load(refrence_pointing_npz)['dec']

    return ra_array, dec_array


def get_pointing_and_times_from_reference_pointing_file(refrence_pointing_npz):
    """Get the `time`, `ra` and `dec` arrays from the reference antenna pointing
    file. The file should be a numpy-generated .npz binary file (not pickled though!)

    The time array should be in UNIX format

    The ra and dec arrays should be in degrees

    TO DO: add .csv/text file format support
    
    Parameters
    ----------
    reference_pointing: str
        The path to the .npz file

    Returns
    -------
    time_array: numpy array of float
        The times in Unix format

    ra_array: numpy array of float
        The pointing RA value in degrees

    dec_array: numpy array of float
        The pointing Dec value in degrees

    """
    time_array = get_times_from_reference_pointing_file(refrence_pointing_npz)
    ra_array, dec_array = \
                get_pointing_from_reference_pointing_file(refrence_pointing_npz)

    return time_array, ra_array, dec_array

def get_closest_pointing_from_yaml(yaml_path, otf_ID):
    """A core function used in multiple tasks in the `otfms` pipeline.

    Basically based on the Snakemake yaml file, and an OTF field ID the closest
    pointing time, RA and Dec coordinates are retrieved from the reference pointing
    file.

    Parameters
    ----------
    yaml_path: str
        Path to the Snakemake yaml config file

    otf_ID: str
        The ID of the OTF pointing for which the values should be returned

    Returns
    -------
    time_centre: float
        The closest time value from the reference pointing file

    ra_centre: float
        The corresponding RA coordinate (in degrees)

    dec_centre: float
        The corresponding Dec coordinate (in degrees)

    """

    logger.info('Getting the closest coordinate from the reference pointing file ' \
                + 'for OTF ID: {0:s}'.format(otf_ID))

    #Get the RA and Dec values from the pointing reference fil
    pointing_ref_path = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                                  var_name = 'pointing_ref')

    times, ra, dec = get_pointing_and_times_from_reference_pointing_file(pointing_ref_path)

    #Select the time value and corresponding RA and Dec values
    otf_field_ID_mapping = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                            var_name = 'otf_field_ID_mapping')

    time_crossmatch_threshold = pipeline.get_var_from_yaml(yaml_path = yaml_path,
                                            var_name = 'time_crossmatch_threshold')

    otf_pointing_time = otf_field_ID_mapping[otf_ID]

    del otf_field_ID_mapping, yaml_path

    #So now there is a truncating issue
    #This is no slower than the exact check, which fails due to truncation issues
    closest_time_arg =  np.argmin(np.fabs(times - otf_pointing_time))

    time_centre = times[closest_time_arg]

    if np.fabs(time_centre - otf_pointing_time) > time_crossmatch_threshold:
        raise ValueError('No matching reference time found with the config time value!')

    ra_centre = ra[closest_time_arg]
    dec_centre = dec[closest_time_arg]

    return time_centre, ra_centre[0], dec_centre[0]


def generate_OTF_names_from_ra_dec(ra, dec, acronym='OTFasp'):
    """Generate a string useful for renaming the OTF pointings, based on the
    field cenral coordinates (RA, Dec, J2000, ICRS)

    The IAU guidelines: https://cdsweb.u-strasbg.fr/Dic/iau-spec.html

    My choice for naming convention:

    Acroym: OTFasf (where the asp stands for arcane-suite pointing)
    Sequence: JHHMMSS.ss+DDMMSS.ss

    So the names should look like:

        OTFasfJHHMMSS.ss+DDMMSS.ss        

    NOTE: for future naming schemes, the asp part of the acronym should be changed
        to represent the survey used

    Parameters
    ----------
    ra: float
        RA of the field centre in degrees

    dec: float
        Dec of the field centre in degrees

    acronym: str, opt
        The acronym part of the name

    Returns
    -------
    name_string: str
        The unique name string based on the acronym and coordinates

    """

    otf_pointing_coord = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')

    print(otf_pointing_coord.to_string('hmsdms', precision=4))

    name_string = '{0:s}J{1:s}{2:s}'.format(
                    acronym,
                    otf_pointing_coord.ra.to_string(unit=u.hourangle,
                                                    sep="", precision=2,
                                                    pad=True),
                    otf_pointing_coord.dec.to_string(unit=u.degree,
                                                    sep="", precision=2,
                                                    alwayssign=True, pad=True)
                    )

    return name_string

def generate_position_string_for_chgcentre(ra,dec):
    """
    """

    otf_pointing_coord = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')

    return otf_pointing_coord.to_string('hmsdms', precision=4)



#=== MAIN ===
if __name__ == "__main__":
    pass