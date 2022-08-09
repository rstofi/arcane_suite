"""Utility functions handling time. The code works on arrays of time in UNIX format.

NOTE: UNIX time formatting is not a *true* represantation of UTC because of leap
        second overlapping. However, for our purposes it is good enough...

"""

__all__ = ['convert_MJD_to_UNIX', 'soft_check_if_time_is_UNIX',
            'casa_datetime_to_unix_time', 'unix_time_to_casa_datetime',
            'convert_casa_timerange_selection_to_unix_times']

import sys
import logging
import time
import numpy as np

from astropy.time import Time

#=== Set up logging
logger = logging.getLogger(__name__)

#=== Functions ===
def convert_MJD_to_UNIX(time_array):
    """Convert the MJD (Modified Julian Date) times to UNIX time

    MJD is the default time format in most MS, but it is more convienient to
    work with UNIX time

    Parameters:
    ===========

    time_array: <numpy.ndarray>
        The numpy array containing the time values in MJD format

    Returns:
    ========
    unix_time_array: <numpy.ndarray>
        The numpy array containing the time values in UNIX format
    """
    #Conversion
    unix_time_array = Time(time_array / 86400, format='mjd')
    unix_time_array.format = 'unix'

    #Do not return an Astropy Time object but a numpy array
    return unix_time_array.value

def soft_check_if_time_is_UNIX(time_val):
    """Code to check if a float value could be a *valid* UNIX time stamp.

    Basically if the value would give a UNIX time between 1 January 1970 (when the
    UNIX time was introduced) and the current ime (from the system time)
    the code returns True, otherwise it returns False.

    NOTE: the current time is measured in UTC zero timezone (i.e. UNIX standard),
        it is not the 'real' local time.

    Parameters:
    ===========
    time_val: float
        The time value to be checked

    Returns:
    ========
    True if `time_val` could be the time in UNIX format for a radio observation and
    False if not

    """
    #My first criteria was:
    #1933 October 1 (when Jansky published his paper on the first observation on the radio sky)
    #start_date = -1144026000

    #1 January 1970
    min_valid_UNIX_time = 0

    #Now
    max_valid_UNIX_time = time.time() #Not considering timezone

    if min_valid_UNIX_time < time_val < max_valid_UNIX_time:
        return True
    else:
        return False

def casa_datetime_to_unix_time(casa_date_string):
    """Convert a CASA format string to UNIX value

    The CASA format should be:

    yyyy/mm/dd/hh:mm:ss.ss

    NOTE: the following approach cannot deal with non-int seconds:
        
        astropy_Time = Time.strptime(casa_date_string, '%Y/%m/%d/%H:%M:%S')
    
    Parameters:
    ===========
    casa_date_string: str
        The time string in CASA format

    Returns:
    ========
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


    #print(astropy_Time.strftime('%Y/%m/%d/%H:%M:%S'))

    return astropy_Time.unix

def unix_time_to_casa_datetime(unix_time_val):
    """Create a CASA formatted time string from an UNIX format time value

    NOTE: the following approach cannot deal with non-int seconds:

        casa_format_string = astropy_Time.strftime('%Y/%m/%d/%H:%M:%S')

    Parameters:
    ===========
    unix_time_val: float
        Time value in UNIX representation

    Returns:
    ========
    The time string in CASA format


    """
    astropy_Time = Time(unix_time_val, format='unix')

    date_val_dict = astropy_Time.ymdhms

    #This is a hacky way to add leading zeros to the floating-point precise seconds...
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

    Parameters:
    ===========
    selection_string: str
        The timerange selection string in CASA format

    Returns:
    ========
    start_unix_time: float
        Start value in UNIX representation
    
    end_unix_time: float
        End value in UNIX representation
    
    """

    #Check if this is a single time range selection using the standard CASA syntax
    if selection_string.count('~') != 1:
        raise ValueError('Ivalid time range selection string: {0:s}'.format(selection_string))

    #Chunk the selection string to start and end times:
    start_date_string = selection_string.split('~')[0]
    end_date_string = selection_string.split('~')[1].strip()

    start_unix_time = casa_datetime_to_unix_time(start_date_string)
    end_unix_time = casa_datetime_to_unix_time(end_date_string)

    if start_unix_time >= end_unix_time:
        raise ValueError('Invalid timeragne selected: {0:s}'.format(selection_string))

    return start_unix_time, end_unix_time

def convert_unix_times_to_casa_timerange_selection(start_unix_time, end_unix_time):
    """From a start + end time value creates a CASA-style timerange selection string.

    The CASA timerange selection syntax is:

    yyyy/mm/dd/hh:mm:ss.ss~yyyy/mm/dd/hh:mm:ss.ss

    Parameters:
    ===========
    start_unix_time: float
        Start value in UNIX representation
    
    end_unix_time: float
        End value in UNIX representation
    
    Returns:
    ========
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

    
    Parameters:
    ===========
    times_array: list of float
        The array to subselect from

    start_time: float
        The first allowed time for the sub-selection

    end_time: float
        The last allowed time for the sub selection

    Returns:
    ========
    A sub-selection of the `times_array` in between the `start_time` and `end_time`

    """
    if start_time > end_time:
        raise ValueError('Invalid time selection boundaries!')

    if start_time > np.max(times_array) or end_time < np.min(times_array):
        raise ValueError('Invalid timerange selection')

    return np.array(times_array[np.where((times_array >= start_time) & (times_array <= end_time))])

def time_arrays_intersection(t1_array, t2_array, threshold=0.0001):
    """
    """

    #For already sorted arrays numpy is super fast allegedly...
    #So first, chek if input arrays are sorted:
    is_sorted = lambda a: np.all(a[:-1] <= a[1:]) #This is O(n)

    #TO DO: raise warning if the arrays are to large e.g. >10e+5 or something

    #Sort if not sorted
    if is_sorted(t1_array) == False:
        t1_array = np.sort(t1_array)

    if is_sorted(t2_array) == False:
        t2_array = np.sort(t2_array)
    

    #If the two arrays have the same size we can just loop trough them


    #If the arrays have the same size, just use the smaller one for the nested loops


#=== MAIN ===
if __name__ == "__main__":
    pass