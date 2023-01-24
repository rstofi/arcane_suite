"""Collection of wrapper functions working with .fits files. This module is expected
to be used across several pipelines of the suite.
"""

__all__ = [
    'get_fits_Ndim',
    'get_fits_cube_axis_params',
    'get_fits_synthesiseb_beam_from_primary_table']


import numpy as np
import logging

from astropy.io import fits

from astropy.coordinates import SkyCoord
from astropy import units as u

from arcane_utils import misc as a_misc

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def get_fits_Ndim(fitspath):
    """Simple routine to get the dimension of the fits file

    Parameters
    ----------

    fitspath: str
        The input fits path

    Returns
    -------
    N_dim: int
        The number of dimensions of the fits file

    """
    logger.debug(
        "Collect dimension info from the 'PRIMARY' table for {0:s}".format(fitspath))

    hdul = fits.open(fitspath)  # Primary hdu list
    primary_table = hdul['PRIMARY']
    primary_header = primary_table.header

    N_dim = int(primary_header['NAXIS'])

    hdul.close()

    return N_dim


def get_fits_cube_axis_params(fitspath):
    """Function to read out the dimension and axis information to a dictionary from
    a .fits file.

    The axes are read from the PRIMARY header and then cosiders only the following
    axes (if present):

    ['RA--SIN','DEC--SIN','FREQ','STOKES']

    A dictionary is returned, for each axis key the following values in an array:

    [array lenght, reference pixel value, reference pixel index, pixel size, pixel unit]

    NOTE that the units are not converted within this script!

    Parameters
    ----------

    fitspath: str
        The input fits path

    Returns
    -------

    cube_params_dict: dict
        A dictionary with all the axis info

    """
    logger.debug(
        "Collect cube axis info from the 'PRIMARY' table for {0:s}".format(fitspath))

    hdul = fits.open(fitspath)  # Primary hdu list
    primary_table = hdul['PRIMARY']
    primary_header = primary_table.header

    N_dim = int(primary_header['NAXIS'])

    logger.debug(
        "The image is {0:d} dimensional, looking all supported axes!".format(N_dim))

    axis_name_array = []
    axis_unit_array = []
    axis_reference_val_array = []
    axis_reference_pix_array = []
    axis_increment_array = []
    axis_lenght_array = []

    # Get all the axis name dimension and unit
    for d in range(1, N_dim + 1):
        axis_name_array.append(primary_header['CTYPE{0:d}'.format(d)])

        # Note that the other parameters have to exist to define a valid WCS
        # coordinate system!
        if 'CUNIT{0:d}'.format(d) not in primary_header:
            logger.warning(
                "No 'CUNIT{0:d} found in 'PRIMARY' header!".format(d))
            axis_unit_array.append(None)
        else:
            axis_unit_array.append(primary_header['CUNIT{0:d}'.format(d)])

        axis_reference_val_array.append(primary_header['CRVAL{0:d}'.format(d)])
        axis_increment_array.append(primary_header['CDELT{0:d}'.format(d)])
        axis_reference_pix_array.append(
            int(primary_header['CRPIX{0:d}'.format(d)]))
        axis_lenght_array.append(primary_header['NAXIS{0:d}'.format(d)])

    hdul.close()

    # Need to convert to numpy arrays for the cross-matching to work
    axis_name_array = np.array(axis_name_array)
    axis_lenght_array = np.array(axis_lenght_array)
    axis_reference_val_array = np.array(axis_reference_val_array)
    axis_reference_pix_array = np.array(axis_reference_pix_array)
    axis_increment_array = np.array(axis_increment_array)
    axis_unit_array = np.array(axis_unit_array)

    # Re arrange the arrays to the shape [RA, Dec, Freq Stokes]
    cube_params_dict = {}

    for ax_name in axis_name_array:
        cube_params_dict[ax_name] = [axis_lenght_array[axis_name_array == ax_name][0],
                                     axis_reference_val_array[axis_name_array == ax_name][0],
                                     axis_reference_pix_array[axis_name_array == ax_name][0],
                                     axis_increment_array[axis_name_array == ax_name][0],
                                     axis_unit_array[axis_name_array == ax_name][0]]

    return cube_params_dict


def get_fits_synthesiseb_beam_from_primary_table(fitspath):
    """This function attempts to read out the synthesised beam parameters from a
    fits header.

    These parameters are either in the PRIMARY header as an average value over the
    whole cube, or if the frequency variance is accounted for in the image forming
    process and so in controlling the synthesised beam shape.

    This function only attempts to read the PRIMARY header and is looking for the
    average synthesised beam!

    NOTE: the current code returns the native beam values from the header that
        can be assumed to be in degrees!

    TO DO: add code to check for units (not necessary existing in the header!)

    A 'better' solution is when the synthesised beam parameters are stored in a
    dedicated 'BEAMS' table for each channel an associated beam.

    NOTE: this function does not read from the BEAM table, only from the PRIMARY header!

    TO DO: write code to deal with other ways the synthsised beam info could be stored in fits headers

    TO DO: write a top-level function to deal with all cases and that can return
        beam in any case

    For more info see this tool:

    https://github.com/radio-astro-tools/radio-beam

    Parameters
    ----------

    fitspath: str
        The input fits path

    Returns
    -------

    b_maj: float
        The major axis (in units of degrees)

    b_min: float
        The minor axis (in units of degrees)

    b_pa: float
        The position angle (in units of degrees)
    """
    logger.debug('Collect synthesized beam info for {0:s}'.format(fitspath))

    hdul = fits.open(fitspath)  # Primary hdu list

    # Raise warning if the 'BEAMS' table if exist
    try:
        beams_table = hdul['BEAMS']

        logger.warning("Found 'BEAMS' table!")
    except BaseException:
        logger.debug("No 'BEAMS' table found!")

    # Get the beam parameters from the primary table
    logger.debug("Collecting beam info from the 'PRIMARY' table header!")
    primary_table = hdul['PRIMARY']

    primary_header = primary_table.header

    # The values are expected to be in degrees, by definition
    if 'BMAJ' in primary_header:
        b_maj = primary_header['BMAJ']
    else:
        raise ValueError(
            "No 'BMAJ' key found in the 'PRIMARY' table header, beam info could be in 'HISTORY' or 'BEAMS' table (if exists)!")

    if 'BMIN' in primary_header:
        b_min = primary_header['BMIN']
    else:
        raise ValueError(
            "No 'BMIN' key found in the 'PRIMARY' table header, beam info could be in 'HISTORY' or 'BEAMS' table (if exists)!")

    if 'BPA' in primary_header:
        b_pa = primary_header['BPA']
    else:
        raise ValueError(
            "No 'BPA' key found in the 'PRIMARY' table header, beam info could be in 'HISTORY' or 'BEAMS' table (if exists)!")

    hdul.close()

    return b_maj, b_min, b_pa


# === MAIN ===
if __name__ == "__main__":
    pass
