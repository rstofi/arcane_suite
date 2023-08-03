"""Collection of utility functions unique to the `otfms` pipeline

TO DO: refactor the code by using a separate readin function for the variables...
    now I have waaay to much code duplication going on
"""

__all__ = [
    'generate_config_template_for_otfms',
    'get_otfms_data_variables',
    'get_otfms_data_selection_from_config',
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

from arcane_utils import misc

# Load pipeline default parameters
from arcane_pipelines.otfms import otfms_defaults

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def generate_config_template_for_otfms(
        template_path: str,
        overwrite: bool = True,
        create_template: bool = False):
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


def get_otfms_data_variables(config_path: str):
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

    split_calibrators: bool
        If True, the calibrators are split and then merged into the OTF format MS

    flag_noise_diode: bool
        If True, the noise diode affected MS' will be flagged

    """
    config = configparser.ConfigParser()
    config.read(config_path)

    # === MS_dir
    MS_dir = config.get('DATA', 'MS')
    MS_dir = pipeline.remove_comment(MS_dir).strip()

    if MS_dir == '':
        raise ValueError("Missing mandatory parameter: 'MS'")

    # === pointing_ref
    pointing_ref = config.get('DATA', 'pointing_ref')
    pointing_ref = pipeline.remove_comment(pointing_ref).strip()

    if pointing_ref == '':
        raise ValueError("Missing mandatory parameter: 'pointing_ref'")

    # === split_calibrators
    try:
        split_calibrators = config['DATA'].getboolean('split_calibrators')
    # If there are comments in the line
    except BaseException:
        split_calibrators_string = config.get('DATA', 'split_calibrators')
        split_calibrators_string = pipeline.remove_comment(
            split_calibrators_string).strip()

        try:
            split_calibrators = misc.str_to_bool(split_calibrators_string)
        except BaseException:
            logger.warning(
                "Invalid argument given to 'split_calibrators', set it to False...")
            split_calibrators = False

    # === flag_noise_diode
    try:
        flag_noise_diode = config['DATA'].getboolean('flag_noise_diode')
    # If there are comments in the line
    except BaseException:
        split_calibrators_string = config.get('DATA', 'flag_noise_diode')
        split_calibrators_string = pipeline.remove_comment(
            split_calibrators_string).strip()

        try:
            flag_noise_diode = misc.str_to_bool(split_calibrators_string)
        except BaseException:
            logger.warning(
                "Invalid argument given to 'flag_noise_diode', set it to False...")
            flag_noise_diode = False

    return MS_dir, pointing_ref, split_calibrators, flag_noise_diode


def get_otfms_data_selection_from_config(
        config_path: str):
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

    # Get the spolit calibrators variable
    MS_dir, pointing_ref, split_calibrators, flag_noise_diode = get_otfms_data_variables(
        config_path)

    del MS_dir, pointing_ref

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

    # ========================
    # === Mandatory params ===
    # ========================

    # === Target fields
    target_field_list = get_string_list('DATA', 'target_field_list')

    # if len(calibrator_list) == 1 and calibrator_list[0] == '':
    #    raise ValueError('Missing mandatory parameter: calibrator_list')
    if len(target_field_list) == 1 and target_field_list[0] == '':
        raise ValueError('Missing mandatory parameter: target_field_list')

    # === Calibrator fields

    # Check if calibrator list is needed
    if split_calibrators:
        calibrator_list = get_string_list('DATA', 'calibrator_list')

        # Check if calibrators are not defined
        if len(calibrator_list) == 1 and calibrator_list[0] == '':
            raise ValueError(
                "Missing mandatory parameter (based on 'split_calibrators' = True): 'calibrator_list'")
    else:
        calibrator_list = []  # Return empty list

    # ===================
    # === Optional params
    # ===================

    # === Noise diode flagging

    # === Scans
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

    # === timerange
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

    # === ant1_ID
    default_ant1_ID = int(
        otfms_defaults._otfms_default_config_dict['DATA']['ant1_ID'][0])

    try:
        ant1_ID = pipeline.get_valued_param_from_config(
            config_path,
            param_section='DATA',
            param_name='ant1_ID',
            param_type='int',
            param_default=default_ant1_ID)

    except BaseException:
        logger.debug(
            "Cant read 'ant1_ID' from config, fallback to default: {0:d} ...".format(default_ant1_ID))

        ant1_ID = default_ant1_ID

    # === ant2_ID
    default_ant2_ID = int(
        otfms_defaults._otfms_default_config_dict['DATA']['ant2_ID'][0])

    try:
        ant2_ID = pipeline.get_valued_param_from_config(
            config_path,
            param_section='DATA',
            param_name='ant2_ID',
            param_type='int',
            param_default=default_ant2_ID)

    except BaseException:
        logger.debug(
            "Cant read 'ant2_ID' from config, fallback to default: {0:d} ...".format(default_ant2_ID))

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
        time_crossmatch_threshold = pipeline.get_valued_param_from_config(
            config_path,
            param_section='DATA',
            param_name='time_crossmatch_threshold',
            param_type='float',
            param_default=default_time_crossmatch_threshold)

    except BaseException:
        logger.debug(
            "Cant read 'time_crossmatch_threshold' from config, fallback to default: {0:.4f} ...".format(
                default_time_crossmatch_threshold))

        time_crossmatch_threshold = default_time_crossmatch_threshold

    # === split_timedelta

    # Default is to set to be 0.5s so the time selection will happen within
    # +/- 0.25 s
    default_split_timedelta = float(
        otfms_defaults._otfms_default_config_dict['DATA']['split_timedelta'][0])

    try:
        split_timedelta = pipeline.get_valued_param_from_config(
            config_path,
            param_section='DATA',
            param_name='split_timedelta',
            param_type='float',
            param_default=default_split_timedelta)

    except BaseException:
        logger.debug(
            "Cant read 'split_timedelta' from config, fallback to default: {0:.4f} ...".format(
                default_split_timedelta))

        split_timedelta = default_split_timedelta

    # === position_crossmatch_threshold

    # Default is to set to be 0.0025 i.e. a 9 arcseconds
    default_time_crossmatch_threshold = float(
        otfms_defaults._otfms_default_config_dict['DATA']['position_crossmatch_threshold'][0])

    try:
        position_crossmatch_threshold = pipeline.get_valued_param_from_config(
            config_path,
            param_section='DATA',
            param_name='position_crossmatch_threshold',
            param_type='float',
            param_default=default_time_crossmatch_threshold)

    except BaseException:
        logger.debug(
            "Cant read 'position_crossmatch_threshold' from config, fallback to default: {0:.4f} ...".format(
                default_time_crossmatch_threshold))

        position_crossmatch_threshold = default_time_crossmatch_threshold

    return calibrator_list, target_field_list, timerange, scans, ant1_ID, ant2_ID, \
        time_crossmatch_threshold, split_timedelta, position_crossmatch_threshold


def get_otfms_output_variables(config_path: str):
    """Get the unique OUTPUT parameters defined in the config file


    Parameters
    ----------
    config_path: str
        Path to the config file initializing the pipeline

    Returns
    -------
    OTF_acronym: str
        The acronym used to name the OTF pointings

    MS_outname: str
        The outpout MS name (without the .ms extension)

    skip_merge: bool
        If True, the individual MS' directory will be kept, and the merged MS
        will not be created

    deep_clean: bool
        If true, the individual MS' directoiry (bolob/) will be deleted

    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    # === OTF_acronym

    OTF_acronym = config.get('OUTPUT', 'OTF_acronym')
    OTF_acronym = pipeline.remove_comment(OTF_acronym).strip()

    if OTF_acronym == '':
        raise ValueError("Missing mandatory parameter: 'OTF_acronym'")

        # logger.warning(
        #    "Missing mandatory parameter: 'OTF_acronym' fallback to default: {0:s}".format(
        #        otfms_defaults._otfms_default_config_dict['OUTPUT']['OTF_acronym'][0]))
        #OTF_acronym = otfms_defaults._otfms_default_config_dict['OUTPUT']['OTF_acronym'][0]

    logger.info("Set 'OTF_acronym' to {0:s} ...".format(OTF_acronym))

    # === skip merge
    try:
        skip_merge = config['OUTPUT'].getboolean('skip_merge')
    # If there are comments in the line
    except BaseException:
        skip_merge_string = config.get('OUTPUT', 'skip_merge')
        skip_merge_string = pipeline.remove_comment(
            skip_merge_string).strip()

        try:
            skip_merge = misc.str_to_bool(skip_merge_string)
        except BaseException:
            logger.warning(
                "Invalid argument given to 'skip_merge', set it to False...")
            skip_merge = False

    # === MS_outname

    if skip_merge:
        logger.info("No merged MS will be created (skip `merge_*` rule)...")
        MS_outname = None
    else:
        MS_outname = config.get('OUTPUT', 'MS_outname')
        MS_outname = pipeline.remove_comment(MS_outname).strip()

        if MS_outname == '':
            raise ValueError("Missing mandatory parameter: 'MS_outname'")

            # logger.warning(
            #    "Missing mandatory parameter: 'MS_outname' fallback to default: {0:s}".format(
            #        otfms_defaults._otfms_default_config_dict['OUTPUT']['MS_outname'][0]))
            #MS_outname = otfms_defaults._otfms_default_config_dict['OUTPUT']['MS_outname'][0]

        logger.info("Set 'MS_outname' to {0:s} ...".format(MS_outname))

    # === deep_clean
    if skip_merge:
        deep_clean = False
    else:
        try:
            deep_clean = config['OUTPUT'].getboolean('deep_clean')
        # If there are comments in the line
        except BaseException:
            deep_clean_string = config.get('OUTPUT', 'deep_clean')
            deep_clean_string = pipeline.remove_comment(
                deep_clean_string).strip()

            try:
                deep_clean = misc.str_to_bool(deep_clean_string)
            except BaseException:
                logger.warning(
                    "Invalid argument given to 'deep_clean', set it to False...")
                deep_clean = False

    return OTF_acronym, MS_outname, skip_merge, deep_clean


def get_times_from_reference_pointing_file(refrence_pointing_npz: str):
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


def get_pointing_from_reference_pointing_file(refrence_pointing_npz: str):
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


def get_closest_pointing_from_yaml(yaml_path: str, otf_ID: str):
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


def generate_OTF_names_from_ra_dec(
        ra: float,
        dec: float,
        acronym: str = 'OTFasp'):
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

    # Replace the decimal point with underscore
    name_string = name_string.replace('.', '_')

    return name_string


def generate_position_string_for_chgcentre(ra: float, dec: float):
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
