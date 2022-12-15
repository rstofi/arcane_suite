"""Collection of utility functions unique to the otfms pipeline
"""

__all__ = [
    'get_otfms_data_variables',
    'get_otfms_data_selection_from_config',
    'init_config_for_otfms',
    'get_times_from_reference_pointing_file',
    'get_pointing_from_reference_pointing_file',
    'get_pointing_and_times_from_reference_pointing_file',
    'get_otfms_output_variables']

import sys
import logging
import configparser
import numpy as np

from astropy.time import Time

from arcane_utils import pipeline
from arcane_utils import time as a_time

from astropy.coordinates import SkyCoord
from astropy import units as u

# Load pipeline default parameters
from arcane_pipelines.otfms import otfms_defaults

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def init_config_for_otfms(
        template_path,
        overwrite=True,
        create_template=False):
    """Generate an empty config file for the *otfms* pipeline. The resultant file
    can be filled by hand, to actually create an usable pipeline.

    NOTE: this is a wrapper around the default values defined in `otfms_defaults.py`

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
        template_path=template_path, pipeline_name='otfms', overwrite=overwrite)

    pipeline.add_aliases_to_config_file(
        template_path=template_path,
        aliases_list=otfms_defaults._otfms_default_aliases,
        defaults_list=otfms_defaults._otfms_default_alias_values)

    pipeline.add_unique_defaults_to_config_file(
        template_path=template_path,
        unique_defaults_dict=otfms_defaults._otfms_default_config_dict)


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

    MS_dir = config.get('DATA', 'MS')
    MS_dir = pipeline.remove_comment(MS_dir).strip()

    if MS_dir == '':
        raise ValueError("Missing mandatory parameter: 'MS'")

    pointing_ref = config.get('DATA', 'pointing_ref')
    pointing_ref = pipeline.remove_comment(pointing_ref).strip()

    if pointing_ref == '':
        raise ValueError("Missing mandatory parameter: 'pointing_ref'")

    try:
        split_calibrators = config['DATA'].getboolean('split_calibrators')
    # If there are comments in the line
    except BaseException:
        split_calibrators_string = config.get('DATA', 'split_calibrators')
        split_calibrators_string = pipeline.remove_comment(
            split_calibrators_string).strip()

        try:
            split_calibrators = pipeline.str_to_bool(split_calibrators_string)
        except BaseException:
            logger.warning(
                "Invalid argument given to 'split_calibrators', set it to False...")
            split_calibrators = False

    return MS_dir, pointing_ref, split_calibrators


def get_otfms_data_selection_from_config(config_path, split_calibrators=False):
    """Reads the data selection for the OTF to MS conversion from the config file:

    In the config file the targets MUST be specifyed, and if we awant to split the
    calibrators. If yest, the calibrator field also need to be defined. The other
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

    # === Quick routine to get the argument values that are list of strings
    # ---------------------------------------------------------------------------
    """Get a a parameter from the argparse parset file as a list of strings. This
    routine can handle comments including commas. For example

        `get_string_list(DATA, param_example)`

    will return [a,b] from a parset looking like this:


    [DATA]
    param_example = a, b #c, d

    NOTE: the code will shit the bed if the comment character is a comma. This,
    however, is a super unexpected behaviour, so I am not gonna make a check or
    exception for this case.

    Parameters:
    -----------
    arg_val: str
        The argument (variable) name in the parset file

    section: str
        The section in the parset file

    Returns:
    --------
    A list of strings (avalue) of the argument (variable)

    """
    def get_string_list(section, arg_var): return pipeline.remove_comment(
        config.get(section, arg_var)).strip().split(',')
    # ---------------------------------------------------------------------------

    # Mandatory
    #calibrator_list = get_string_list('DATA', 'calibrator_list')
    target_field_list = get_string_list('DATA', 'target_field_list')

    # if len(calibrator_list) == 1 and calibrator_list[0] == '':
    #    raise ValueError('Missing mandatory parameter: calibrator_list')
    if len(target_field_list) == 1 and target_field_list[0] == '':
        raise ValueError('Missing mandatory parameter: target_field_list')

    # Check if calibrator list is needed
    calibrator_list = get_string_list('DATA', 'calibrator_list')

    if split_calibrators:
        # Check if calibrators are not defined
        if len(calibrator_list) == 1 and calibrator_list[0] == '':
            raise ValueError(
                "Missing mandatory parameter (based on 'split_calibrators' = true): 'calibrator_list'")
    else:
        calibrator_list = []  # Return empty list

    # Optional
    try:
        timerange = config.get('DATA', 'timerange', fallback=None)
        timerange = pipeline.remove_comment(timerange)

        # If no value is provided
        if timerange.strip() == '':
            timerange = None
        else:
            # Check for format (check are inside the function)
            _ = a_time.convert_casa_timerange_selection_to_unix_times(
                timerange)

    except Exception as e:  # Catch the error message
        logger.warning(
            'An error occured while parsing timerange value:', exc_info=e)
        logger.info('Set timerange to None')
        timerange = None

    try:  # If a single scan ID is provided
        scans = list(config.getint('DATA', 'scans', fallback=None))
    except BaseException:
        # Check if empty string is given
        scans = str(config.get('DATA', 'scans'))
        scans = pipeline.remove_comment(scans)

        if scans.strip() == '':
            scans = None
        else:
            # Tre yto get info from input
            scans = list(scans.split(','))
            try:
                scans = list(map(int, scans))  # Map str to int
            except BaseException:
                logger.warning(
                    'Invalid scan ID(s): ignoring user input and use all scans...')
                scans = None

    # === ant1_ID
    default_ant1_ID = int(
        otfms_defaults._otfms_default_config_dict['DATA']['ant1_ID'][0])

    try:
        ant1_ID = config.getint('DATA', 'ant1_ID', fallback=default_ant1_ID)
        logger.debug("Set 'ant1_ID' to {0:s} ...".format(ant1_ID))
    except ValueError:  # When there is a comment
        ant1_ID_string = config.get('DATA', 'ant1_ID')
        ant1_ID_string = pipeline.remove_comment(ant1_ID_string)

        try:
            ant1_ID = int(ant1_ID_string.strip())
            logger.debug("Set 'ant1_ID' to {0:d} ...".format(ant1_ID))
        except BaseException:
            if ant1_ID_string.strip() != '':
                logger.warning("Invalid format for 'ant1_ID'!")
                logger.debug(
                    "Fallback to default and set 'ant1_ID' to {0:d} ...".format(default_ant1_ID))
                ant1_ID = default_ant1_ID
            else:
                logger.debug(
                    "No 'ant1_ID' is defined, fallback to default: {0:d} ...".format(default_ant1_ID))
                ant1_ID = default_ant1_ID

    # === ant2_ID
    default_ant2_ID = int(
        otfms_defaults._otfms_default_config_dict['DATA']['ant2_ID'][0])

    try:
        ant2_ID = config.getint('DATA', 'ant2_ID', fallback=default_ant2_ID)
        logger.debug("Set 'ant2_ID' to {0:s} ...".format(ant2_ID))
    except ValueError:
        ant2_ID_string = config.get('DATA', 'ant2_ID')
        ant2_ID_string = pipeline.remove_comment(ant2_ID_string)
        try:
            ant2_ID = int(ant2_ID_string.strip())
            logger.debug("Set 'ant2_ID' to {0:d} ...".format(ant2_ID))
        except BaseException:
            if ant2_ID_string.strip() != '':
                logger.warning("Invalid format for 'ant2_ID'!")
                logger.debug(
                    "Fallback to default and set 'ant2_ID' to {0:d} ...".format(default_ant2_ID))
                ant1_ID = default_ant2_ID
            else:
                logger.debug(
                    "No 'ant2_ID' is defined, fallback to default: {0:d} ...".format(default_ant2_ID))
                ant2_ID = default_ant2_ID

    if ant1_ID == ant2_ID:
        if ant1_ID != 0:
            logger.warning(
                "'ant1_ID' and 'ant2_ID' are equal, set 'ant2_ID' to 0")
            ant2_ID = 0
        else:
            logger.warning(
                "'ant1_ID' and 'ant2_ID' are equal, set 'ant2_ID' to 1")
            ant2_ID = 1

    # Note that ANTENNA1 *always* have a smaller ID number than ANTENNA2 in an MS
    # So for a general case, we need to swap the two IDs if ant1_ID > ant2_ID

    if ant1_ID > ant2_ID:
        logger.debug(
            "Swapping 'ant1_ID' and 'ant2_ID' to make sure baseline exists in MS")
        # Swapping two variables without a teporary variable
        ant1_ID, ant2_ID = ant2_ID, ant1_ID

    # === time_crossmatch_threshold

    # Default is to set to be 0.001 i.e. a millisecond
    default_time_crossmatch_threshold = float(
        otfms_defaults._otfms_default_config_dict['DATA']['time_crossmatch_threshold'][0])

    try:
        time_crossmatch_threshold = config.getfloat(
            'DATA',
            'time_crossmatch_threshold',
            fallback=default_time_crossmatch_threshold)
        logger.debug("Set 'time_crossmatch_threshold' to {0:.4f} ...".format(
            time_crossmatch_threshold))
    except ValueError:
        time_crossmatch_threshold_string = config.get(
            'DATA', 'time_crossmatch_threshold')
        time_crossmatch_threshold_string = pipeline.remove_comment(
            time_crossmatch_threshold_string)

        try:
            time_crossmatch_threshold = float(
                time_crossmatch_threshold_string.strip())
            logger.debug("Set 'time_crossmatch_threshold' to {0:.4f} ...".format(
                time_crossmatch_threshold))
        except BaseException:
            if time_crossmatch_threshold_string.strip() != '':
                logger.warning(
                    "Invalid format format for 'time_crossmatch_threshold' fallback to default: {0:.4f} ...".format(
                        default_time_crossmatch_threshold))

                time_crossmatch_threshold = default_time_crossmatch_threshold
            else:
                logger.debug("No 'time_crossmatch_threshold' is defined, fallback to default: {0:.4f} ...".format(
                    default_time_crossmatch_threshold))

                time_crossmatch_threshold = default_time_crossmatch_threshold

    # === split_timedelta

    default_split_timedelta = float(
        otfms_defaults._otfms_default_config_dict['DATA']['split_timedelta'][0])

    # Default is to set to be 0.5s so the time selection will happen within
    # +/- 0.25 s
    try:
        split_timedelta = config.getfloat(
            'DATA', 'split_timedelta', fallback=default_split_timedelta)
        logger.debug("Set 'split_timedelta' to {0:.4f} ...".format(
            split_timedelta))
    except ValueError:
        split_timedelta_string = config.get('DATA', 'split_timedelta')
        split_timedelta_string = pipeline.remove_comment(
            split_timedelta_string)

        try:
            split_timedelta = float(split_timedelta_string.strip())
            logger.debug("Set 'split_timedelta' to {0:.4f} ...".format(
                split_timedelta))

        except BaseException:
            if split_timedelta_string.strip() != '':
                logger.warning(
                    "Invalid format format for 'split_timedelta' fallback to default: {0:.4f} ...".format(
                        default_split_timedelta))

                split_timedelta = default_split_timedelta
            else:
                logger.debug("No 'split_timedelta' is defined, fallback to default: {0:.4f} ...".format(
                    default_split_timedelta))

                split_timedelta = default_split_timedelta

    return calibrator_list, target_field_list, timerange, scans, ant1_ID, ant2_ID, \
        time_crossmatch_threshold, split_timedelta


def get_otfms_output_variables(config_path):
    """Get the unique OUTPUT parameters defined in the config file


    Parameters
    ----------
    config_path: str
        Path to the config file initializing the pipeline

    Returns
    -------
    OTF_acronym: str
        The acronym used to name the OTF pointings

    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    OTF_acronym = config.get('OUTPUT', 'OTF_acronym')
    OTF_acronym = pipeline.remove_comment(OTF_acronym).strip()

    if OTF_acronym == '':
        #raise ValueError("Missing mandatory parameter: 'OTF_acronym'")
        logger.warning(
            "Missing mandatory parameter: 'OTF_acronym' fallback to default: {0:s}".format(
                otfms_defaults._otfms_default_config_dict['OUTPUT']['OTF_acronym'][0]))

        OTF_acronym = otfms_defaults._otfms_default_config_dict['OUTPUT']['OTF_acronym'][0]

    logger.info("Set 'OTF_acronym' to {0:s} ...".format(OTF_acronym))

    return OTF_acronym


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
    # Get the time array
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

    logger.info(
        'Getting the closest coordinate from the reference pointing file ' +
        'for OTF ID: {0:s}'.format(otf_ID))

    # Get the RA and Dec values from the pointing reference fil
    pointing_ref_path = pipeline.get_var_from_yaml(yaml_path=yaml_path,
                                                   var_name='pointing_ref')

    times, ra, dec = get_pointing_and_times_from_reference_pointing_file(
        pointing_ref_path)

    # Select the time value and corresponding RA and Dec values
    otf_field_ID_mapping = pipeline.get_var_from_yaml(
        yaml_path=yaml_path, var_name='otf_field_ID_mapping')

    time_crossmatch_threshold = pipeline.get_var_from_yaml(
        yaml_path=yaml_path, var_name='time_crossmatch_threshold')

    otf_pointing_time = otf_field_ID_mapping[otf_ID]

    del otf_field_ID_mapping, yaml_path

    # So now there is a truncating issue
    # This is no slower than the exact check, which fails due to truncation
    # issues
    closest_time_arg = np.argmin(np.fabs(times - otf_pointing_time))

    time_centre = times[closest_time_arg]

    if np.fabs(time_centre - otf_pointing_time) > time_crossmatch_threshold:
        raise ValueError(
            'No matching reference time found with the config time value!')

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

    #print(otf_pointing_coord.to_string('hmsdms', precision=4))

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


def generate_position_string_for_chgcentre(ra, dec):
    """Generate a string that `chgcentre` can read from RA and Dec coordinates

    Parameters
    ----------
    ra: float
        RA of the field centre in degrees

    dec: float
        Dec of the field centre in degrees

    Returns
    -------
    A coordinate string of 'hm.4sdm.4s'

    """

    otf_pointing_coord = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')

    return otf_pointing_coord.to_string('hmsdms', precision=4)


# === MAIN ===
if __name__ == "__main__":
    pass
