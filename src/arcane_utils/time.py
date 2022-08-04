"""Utility functions handling time
"""

__all__ = ['convert_MJD_to_UNIX']

import sys
import logging
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

def casa_datetime_to_unix_time(casa_date_string):
    """

    The format should be:

    yyyy/mm/dd/hh:mm:ss.ss

    This approach cannot deal with non-int seconds:
    astropy_Time = Time.strptime(casa_date_string, '%Y/%m/%d/%H:%M:%S')

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
    """

    This approach cannot deal with non-int seconds:
    casa_format_string = astropy_Time.strftime('%Y/%m/%d/%H:%M:%S')

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
    """
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


#=== MAIN ===
if __name__ == "__main__":
    pass