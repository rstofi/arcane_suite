"""Utility functions handling time. The code works on arrays of time in UNIX format.

NOTE: UNIX time formatting is not a *true* represantation of UTC because of leap
        second overlapping. However, for our purposes it is good enough...

"""

__all__ = ['get_time_from_ISO_based_string',
           'convert_MJD_to_UNIX', 'soft_check_if_time_is_UNIX',
           'casa_datetime_to_unix_time', 'unix_time_to_casa_datetime',
           'convert_casa_timerange_selection_to_unix_times', ]

import sys
import logging
import time
import numpy as np
#from numba import jit

from astropy.time import Time

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def get_time_from_ISO_based_string(time_string, scale='utc'):
    """Simple script to convert an ISO or ISOT format time string to UNIX format
    time value.

    Ths input string format either ISO:

    ``yyyy-mm-dd hh:mm:ss.ss``

    or in ISOT (T instead of space):

    ``yyyy-mm-ddThh:mm:ss.ss``

    format.

    The time system or scaling can be also defined (e.g. utc, tt, iso...etc)

    The code returns the time value as an UNIX formatted float.

    Parameters
    ----------
    time_string: str
        The ISO or ISOT formatted time string

    scale: str, opt
        The time system scaling (e.g. utc, tt, iso...etc)

    Returns
    -------
    unix_time: float
        The time value in UNIX format

    """
    try:
        time_val = Time(time_string, format='iso', scale=scale)
        logger.debug("Input time string format is ISO")
    except BaseException:
        pass

    try:
        time_val = Time(time_string, format='isot', scale=scale)
        logger.debug("Input time string format is ISOT")
    except BaseException:
        raise ValueError(
            'The input time string is not in a valid ISO/ISOT format!')

    # Convert to UNIX time
    time_val.format = 'unix'

    if soft_check_if_time_is_UNIX(time_val.value):
        return time_val.value
    else:
        raise ValueError("Time is not in UNIX format!")


def convert_MJD_to_UNIX(time_array):
    """Convert the MJD (Modified Julian Date) times to UNIX time

    MJD is the default time format in most MS, but it is more convienient to
    work with UNIX time

    Parameters
    ----------
    time_array: numpy array of float
        The numpy array containing the time values in MJD format

    Returns
    -------
    unix_time_array: numpy array of float
        The numpy array containing the time values in UNIX format

    """
    # Conversion
    unix_time_array = Time(time_array / 86400, format='mjd')
    unix_time_array.format = 'unix'

    # Do not return an Astropy Time object but a numpy array
    return unix_time_array.value


def soft_check_if_time_is_UNIX(time_val):
    """Code to check if a float value could be a *valid* UNIX time stamp.

    Basically if the value would give a UNIX time between 1 January 1970 (when the
    UNIX time was introduced) and the current ime (from the system time)
    the code returns True, otherwise it returns False.

    NOTE: the current time is measured in UTC zero timezone (i.e. UNIX standard),
        it is not the 'real' local time.

    Parameters
    ----------
    time_val: float
        The time value to be checked

    Returns
    -------
    True if `time_val` could be the time in UNIX format for a radio observation and
    False if not

    """
    # My first criteria was:
    # 1933 October 1 (when Jansky published his paper on the first observation on the radio sky)
    #start_date = -1144026000

    # 1 January 1970
    #min_valid_UNIX_time = 0

    # Now
    # max_valid_UNIX_time = time.time()  # Not considering timezone

    if 0 < time_val < time.time():
        return True
    else:
        return False


def casa_datetime_to_unix_time(casa_date_string):
    """Convert a CASA format string to UNIX value

    The CASA format should be:

    yyyy/mm/dd/hh:mm:ss.ss

    NOTE: the following approach cannot deal with non-int seconds:

        astropy_Time = Time.strptime(casa_date_string, '%Y/%m/%d/%H:%M:%S')

    Parameters
    ----------
    casa_date_string: str
        The time string in CASA format

    Returns
    -------
    Time value in UNIX representation

    """

    date_val_array = casa_date_string.split('/')
    time_val_array = date_val_array[3].split(':')

    astropy_Time = Time({'year': int(date_val_array[0]),
                        'month': int(date_val_array[1]),
                         'day': int(date_val_array[2]),
                         'hour': int(time_val_array[0]),
                         'minute': int(time_val_array[1]),
                         'second': float(time_val_array[2])})

    # print(astropy_Time.strftime('%Y/%m/%d/%H:%M:%S'))

    return astropy_Time.unix


def unix_time_to_casa_datetime(unix_time_val):
    """Create a CASA formatted time string from an UNIX format time value

    NOTE: the following approach cannot deal with non-int seconds:

        casa_format_string = astropy_Time.strftime('%Y/%m/%d/%H:%M:%S')

    Parameters
    ----------
    unix_time_val: float
        Time value in UNIX representation

    Returns
    -------
    The time string in CASA format


    """
    astropy_Time = Time(unix_time_val, format='unix')

    date_val_dict = astropy_Time.ymdhms

    # This is a hacky way to add leading zeros to the floating-point precise
    # seconds...
    if date_val_dict['second'] >= 10:
        casa_format_string = '{0:d}/{1:02d}/{2:02d}/{3:02d}:{4:02d}:{5:.4f}'.format(
            date_val_dict['year'],
            date_val_dict['month'],
            date_val_dict['day'],
            date_val_dict['hour'],
            date_val_dict['minute'],
            date_val_dict['second'])
    else:
        casa_format_string = '{0:d}/{1:02d}/{2:02d}/{3:02d}:{4:02d}:0{5:.4f}'.format(
            date_val_dict['year'],
            date_val_dict['month'],
            date_val_dict['day'],
            date_val_dict['hour'],
            date_val_dict['minute'],
            date_val_dict['second'])

    return casa_format_string


def convert_casa_timerange_selection_to_unix_times(selection_string):
    """Convert a CASA-style timerange selection to a UNIX format start and end date

    The CASA timerange selection syntax is:

    yyyy/mm/dd/hh:mm:ss.ss~yyyy/mm/dd/hh:mm:ss.ss

    Parameters
    ----------
    selection_string: str
        The timerange selection string in CASA format

    Returns
    -------
    start_unix_time: float
        Start value in UNIX representation

    end_unix_time: float
        End value in UNIX representation

    """

    # Check if this is a single time range selection using the standard CASA
    # syntax
    if selection_string.count('~') != 1:
        raise ValueError(
            'Ivalid time range selection string: {0:s}'.format(selection_string))

    # Chunk the selection string to start and end times:
    start_date_string = selection_string.split('~')[0]
    end_date_string = selection_string.split('~')[1].strip()

    start_unix_time = casa_datetime_to_unix_time(start_date_string)
    end_unix_time = casa_datetime_to_unix_time(end_date_string)

    if start_unix_time >= end_unix_time:
        raise ValueError(
            'Invalid timeragne selected: {0:s}'.format(selection_string))

    return start_unix_time, end_unix_time


def convert_unix_times_to_casa_timerange_selection(
        start_unix_time, end_unix_time):
    """From a start + end time value creates a CASA-style timerange selection string.

    The CASA timerange selection syntax is:

    yyyy/mm/dd/hh:mm:ss.ss~yyyy/mm/dd/hh:mm:ss.ss

    Parameters
    ----------
    start_unix_time: float
        Start value in UNIX representation

    end_unix_time: float
        End value in UNIX representation

    Returns
    -------
    casa_timerange_selection_string: str
        The timerange selection string in CASA format

    """
    if end_unix_time <= start_unix_time:
        raise ValueError('Invalid timerange selection!')

    star_time_casa_format_string = unix_time_to_casa_datetime(start_unix_time)
    end_time_casa_format_string = unix_time_to_casa_datetime(end_unix_time)

    casa_timerange_selection_string = star_time_casa_format_string \
        + '~' \
        + end_time_casa_format_string

    return casa_timerange_selection_string


def subselect_timerange_from_times_array(times_array, start_time, end_time):
    """Select values from a UNIX time array in between the `start_time` and
    `end_time`

    Parameters
    ----------
    times_array: numpy array of float
        The array to subselect from

    start_time: float
        The first allowed time for the sub-selection

    end_time: float
        The last allowed time for the sub selection

    Returns
    -------
    A sub-selection of the `times_array` in between the `start_time` and `end_time`

    """
    if start_time > end_time:
        raise ValueError('Invalid time selection boundaries!')

    if start_time > np.max(times_array) or end_time < np.min(times_array):
        raise ValueError('Invalid timerange selection')

    return np.array(times_array[np.where((times_array >= start_time)
                                         & (times_array <= end_time))])


def time_arrays_injective_intersection(
        t1_array, t2_array, threshold=0.0001, quick_subselect=True):
    """Function to find all time values that are the same within a given threshold
    in two time-series array. This is a general function, and so the arrays does
    not have to be continous or ordered. They have to be in some float format,
    preferably UNIX

    NOTE: this code is pretty slow on large arrays as it goes with O(n^2) if the
            input arrays have the same size of n

    The code only works for injective (1:1) time value correspondance between the
    two input arrays. Ergo, if any value from an array is closer than the threshold
    value to more than one element in the other array, the code shits the bed and
    throws an error.

    NOTE: I've tried to wrap this function with `numba` to @njit, but it thrown
    an error. (+ del() is not compatible with numba). I made some measurements
    with wrappring this function to @jit(forceobj=True), which runs numba in
    object mode. This does not resulted in a speedup....

    TO DO: refactor the code and speed up critical parts

    Parameters
    ----------
    t1_array: numpy array of float
        The first time series array

    t2_array: numpy array of float
        The second time series array

    threshold: float, optional
        The threshold value which below the difference of two tme values is set
        to be 0 in the cross-matching process

    quick subselect: bool, optional
        If True, both input arrays are cut down based on the time intersection interval
        True by defalut to speed up processing random time arrays, but can be disabled
        if the input arrays already spanning the same timerange

    Returns
    -------
    common_times: numpy array of float
        Time values from the *`t1_array`* which have a single corresponding value
        in `t2_array`

    """
    # In a general case the two arrays can be arbitrary size and spanning
    # random intervals

    # Basically select only the time intersection values from the two arrays
    if quick_subselect:
        common_min = np.max(
            np.array([np.min(t1_array), np.min(t2_array)])) - threshold
        common_max = np.min(
            np.array([np.max(t1_array), np.max(t2_array)])) + threshold

        t1_array = subselect_timerange_from_times_array(
            t1_array, common_min, common_max)
        t2_array = subselect_timerange_from_times_array(
            t2_array, common_min, common_max)

    # TO DO: raise warning if the arrays are to large e.g. >10e+5 or something

    # This only needed if we try to be clever...
    """
    #Sort if not sorted
    #For already sorted arrays numpy is super fast allegedly...
    #So first, chek if input arrays are sorted:
    is_sorted = lambda a: np.all(a[:-1] <= a[1:]) #This is O(n)

    if is_sorted(t1_array) == False:
        t1_array = np.sort(t1_array)

    if is_sorted(t2_array) == False:
        t2_array = np.sort(t2_array)
    """

    # We are not trying to be clever and will brute-forec the problem as it can
    # handle ALL possibilities
    common_times = []

    # Loop through the rows of a boolean matrix with (N_t1, N_t2) size,
    # where each (i,j) element is True, if t1[i] - t2[j] < threshold and False
    # otherwise... maybe not memory efficient ?

    # In case the arrays have repeated values
    t1_array = np.unique(t1_array)
    t2_array = np.unique(t2_array)

    for i in range(0, np.size(t1_array)):
        match_sum = np.sum(np.where(np.fabs(np.subtract(
            t2_array, t1_array[i])) < threshold, True, False).astype(bool))

        # For check if multiple t2 values match with a single t1 value
        if match_sum > 1:
            raise ValueError('Not injective time array value matching!')
        elif match_sum == 1:
            common_times.append(t1_array[i])

    del i, match_sum  # del() doesn't work with numba....

    # Check if multiple t1 values returned as there is multiple match with a
    # single t2 value
    common_times = np.array(common_times)
    if np.size(np.unique(common_times)) != np.size(common_times):
        raise ValueError('Not injective time array value matching!')

    return common_times


# === MAIN ===
if __name__ == "__main__":
    pass
