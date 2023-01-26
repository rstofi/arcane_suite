"""Collection of wrapper functions working with .fits files. This module is expected
to be used across several pipelines of the suite.
"""

__all__ = [
    'get_primary_hdu_header',
    'get_Ndim_from_header',
    'get_axis_params_from_header',
    'get_synthesizeb_beam_from_header',
    'get_fits_reference_coordinates_from_header',
    'get_obs_date_from_header']


import numpy as np
import logging

from astropy.io import fits
from astropy import wcs

from astropy.coordinates import SkyCoord
from astropy import units as u

from arcane_utils import misc as a_misc
from arcane_utils import time as a_time

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def get_hdu_header(fitspath, hdu_index=0):
    """A base function to extract info from the .fits HDU header.

    This function either opens a fits file and returns the HDU header for the
    HDU with `hdu_index`, OR if the input parameter is already a fits HDU header
    object, it simply passes it.

    This routine is really similar to how the code handles MS in `ms_wrapper`

    NOTE: here, I close the fits file and not even reading the data in! As such,
        subsequent functions working with the header does not have a `close` option!

    Parameters
    ----------
    fitspath: str
        The input FITS path or an ``astropy.io.fits.header.Header`` object

    hdu_index: int, opt
        The index of the HDU from the HDU list which header is returned. Ignored
        if the input is an ``astropy.io.fits.header.Header`` object

    Returns
    -------
    An ``astropy.io.fits.header.Header`` object

    """

    if not isinstance(fitspath, type(fits.PrimaryHDU().header)):
        logger.debug("Collect HDUS from {0:s}".format(fitspath))

        hdul = fits.open(fitspath, memmap=True)

        if hdu_index >= len(hdul) or hdu_index < 0:
            raise ValueError(
                "The provided 'hdu_index' out of range of the HDU list size!")
        else:
            logger.debug(
                "Collecting header for HDU no. {0:d}".format(hdu_index))
            hdu = hdul[hdu_index]

            hdu_header = hdu.header

            # Delete data handler opened by memmap=True
            # See documentation at:
            # https://docs.astropy.org/en/stable/io/fits/index.html
            del hdul[hdu_index].data

            hdul.close()

            return hdu_header

    else:
        #logger.debug("Continue on already opened HDU header")
        return fitspath


def get_Ndim_from_header(fitspath, hdu_index=0):
    """Simple routine to get the dimension of the fits file

    Parameters
    ----------
    fitspath: str
        The input FITS path or an ``astropy.io.fits.header.Header`` object

    hdu_index: int, opt
        The index of the HDU from the HDU list which header is returned. Ignored
        if the input is an ``astropy.io.fits.header.Header`` object

    Returns
    -------
    N_dim: int
        The number of dimensions of the fits file

    """
    hdu_header = get_hdu_header(fitspath, hdu_index)

    return int(hdu_header['NAXIS'])


def get_axis_params_from_header(fitspath, hdu_index=0, indices=False):
    """Function to read out the dimension and axis information to a dictionary from
    a .fits file.

    The dictionary keys are the axis names, for example, for an interferometric image:

    ['RA--SIN','DEC--SIN','FREQ','STOKES']

    A dictionary is returned, for each axis key the following values in an array:

    [axis index, array length, reference pixel value, reference pixel index, pixel size, pixel unit]

    If the `indices` parameter is set to `True`, the dictionary keys will be the
    axis indices (starting from 1 !) and in the value array the axis name will be
    written instead of the id.

    NOTE that the units are not converted within this script!

    Parameters
    ----------
    fitspath: str
        The input FITS path or an ``astropy.io.fits.header.Header`` object

    hdu_index: int, opt
        The index of the HDU from the HDU list which header is returned. Ignored
        if the input is an ``astropy.io.fits.header.Header`` object

    indices: bool, opt
        If `True` then the dictionary keys will be indices and the value array first
        element will be the keys

    Returns
    -------
    cube_params_dict: dict
        A dictionary with all the axis info

    """
    hdu_header = get_hdu_header(fitspath, hdu_index)
    N_dim = get_Ndim_from_header(hdu_header, hdu_index)

    logger.debug("Collecting FITS axis parameter dict.")

    cube_params_dict = {}

    # Get all the axis name dimension and unit
    for d in range(1, N_dim + 1):
        axis_name = hdu_header['CTYPE{0:d}'.format(d)]

        axis_index = d

        # Note that the other parameters have to exist to define a valid WCS
        # coordinate system!
        if 'CUNIT{0:d}'.format(d) not in hdu_header:
            logger.warning(
                "No 'CUNIT{0:d} found in 'PRIMARY' header!".format(d))
            axis_unit = None
        else:
            axis_unit = hdu_header['CUNIT{0:d}'.format(d)]

        axis_reference_val = hdu_header['CRVAL{0:d}'.format(d)]
        axis_increment = hdu_header['CDELT{0:d}'.format(d)]
        axis_reference_pix = int(hdu_header['CRPIX{0:d}'.format(d)])
        axis_lenght = hdu_header['NAXIS{0:d}'.format(d)]

        # NOTE: .fits axis indexing starts from 1 !

        # Use axis indices as keys
        if indices:
            cube_params_dict[axis_index] = [axis_name,
                                            axis_lenght,
                                            axis_reference_val,
                                            axis_reference_pix,
                                            axis_increment,
                                            axis_unit]

        # Use axis names as keys
        else:
            cube_params_dict[axis_name] = [axis_index,
                                           axis_lenght,
                                           axis_reference_val,
                                           axis_reference_pix,
                                           axis_increment,
                                           axis_unit]

    return cube_params_dict


def get_synthesizeb_beam_from_header(fitspath, hdu_index=0):
    """This function attempts to read out the synthesized beam parameters from a
    fits header.

    These parameters are either in the 'PRIMARY' header as an average value over the
    whole cube, or if the frequency variance is accounted for in the image forming
    process and so in controlling the synthesized beam shape.

    This function only attempts to read the 'PRIMARY' (or any other HDU, defined
    by the `hdu_index` parameter) header and is looking for the average synthesized
    beam!

    NOTE: the current code returns the native beam values from the header that
        can be assumed to be in degrees!

    TO DO: add code to check for units (not necessary existing in the header!)

    A 'better' solution for spectral cubes, is when the synthesized beam parameters
    are stored in a dedicated 'BEAMS' HDU table for each channel.

    NOTE: this function does not read from the BEAM table, only from the 'PRIMARY'
        header!

    TO DO: write code to deal with other ways the synthesized beam info could be
        stored in fits headers (i.e. added as comment in 'HISTORY' cards within the
        header)

    TO DO: write a top-level function to deal with all cases and that can return
        beam in any case

    For more info see this tool:

    https://github.com/radio-astro-tools/radio-beam

    Parameters
    ----------
    fitspath: str
        The input FITS path or an ``astropy.io.fits.header.Header`` object

    hdu_index: int, opt
        The index of the HDU from the HDU list which header is returned. Ignored
        if the input is an ``astropy.io.fits.header.Header`` object

    Returns
    -------
    b_maj: float
        The major axis (in units of degrees)

    b_min: float
        The minor axis (in units of degrees)

    b_pa: float
        The position angle (in units of degrees)
    """
    logger.debug('Collecting synthesized beam info.')

    hdu_header = get_hdu_header(fitspath, hdu_index)

    # The values are expected to be in degrees, by definition
    if 'BMAJ' in hdu_header:
        b_maj = hdu_header['BMAJ']
    else:
        raise ValueError(
            "No 'BMAJ' key found in the 'PRIMARY' table header, beam info could be in 'HISTORY' card or 'BEAMS' HDU table (if exists)!")

    if 'BMIN' in hdu_header:
        b_min = hdu_header['BMIN']
    else:
        raise ValueError(
            "No 'BMIN' key found in the 'PRIMARY' table header, beam info could be in 'HISTORY' card or 'BEAMS' HDU table (if exists)!")

    if 'BPA' in hdu_header:
        b_pa = hdu_header['BPA']
    else:
        raise ValueError(
            "No 'BPA' key found in the 'PRIMARY' table header, beam info could be in 'HISTORY' card or 'BEAMS' HDU table (if exists)!")

    return b_maj, b_min, b_pa


def get_fits_reference_coordinates_from_header(
        fitspath, hdu_index=0, origin=1):
    """This function gets the RA and Dec sky coordinates in degrees for the reference
    pixel of a .fits file.

    This is a light wrapper around `astropy` basically.

    NOTE: the .fits format uses 1-based indexing, so this is the default, but can
        changed to 0-based indexing!

    For more info, see the in-code comments!

    Parameters
    ----------
    fitspath: str
        The input FITS path or an ``astropy.io.fits.header.Header`` object

    hdu_index: int, opt
        The index of the HDU from the HDU list which header is returned. Ignored
        if the input is an ``astropy.io.fits.header.Header`` object

    origin: int, opt
        Sets the .fits image indexing (e.g. from 0 or 1)

    Returns
    -------
    ra_deg: float
        The reference pixel RA coordinates in degrees

    dec_deg: float
        The reference pixel Dec coordinates in degrees

    """

    logger.debug('Collecting reference coordinate info.')

    hdu_header = get_hdu_header(fitspath, hdu_index)

    # Generating WCS coordinate system
    w = wcs.WCS(hdu_header)

    # Get dimension, axes and the reference coordinates
    cumbe_N_dim = get_Ndim_from_header(hdu_header)

    if cumbe_N_dim < 2:
        raise ValueError(
            "Input header is not an image/cube with dimension {0:d}!".format(cumbe_N_dim))

    cube_params_dict = get_axis_params_from_header(hdu_header, indices=True)

    reference_pixel_coordinates = []

    # Generate the reference pixel array

    # NOTE: .fits axis indexing starts from 1 !
    for i in range(1, cumbe_N_dim + 1):
        reference_pixel_coordinates.append(cube_params_dict[i][3])

    logging.debug(
        "Reference pixels used to compute reference direction : {0:s}".format(
            a_misc.convert_list_to_string(reference_pixel_coordinates)))

    # I actually use only the first two (image-plane) coordinates.
    ref_coords = wcs.utils.pixel_to_skycoord(reference_pixel_coordinates[0],
                                             reference_pixel_coordinates[1],
                                             wcs=w, origin=origin)

    # Return sky coordinates in deg
    return ref_coords.ra.deg, ref_coords.dec.deg


def get_obs_date_from_header(fitspath, hdu_index=0):
    """Get the observation time from the header based on the 'DATE-OBS' card.
    If no 'DATE-OBS' card is found, the code returns None.

    If the 'DATE-OBS' card contains an ISO or ISOT format time string, the code
    returns the date in UNIX format

    The fits TIME-oBS definition in J2000: https://fits.gsfc.nasa.gov/year2000.html

    Parameters
    ----------
    fitspath: str
        The input FITS path or an ``astropy.io.fits.header.Header`` object

    hdu_index: int, opt
        The index of the HDU from the HDU list which header is returned. Ignored
        if the input is an ``astropy.io.fits.header.Header`` object

    origin: int, opt
        Sets the .fits image indexing (e.g. from 0 or 1)

    Returns
    -------
    unix_time: float or None
        The time value in UNIX format

    """
    logger.debug('Collecting obs date.')

    hdu_header = get_hdu_header(fitspath, hdu_index)

    if 'DATE-OBS' in hdu_header:
        logger.debug("Found 'DATE-OBS' card in header.")

        # Should be a CASA-compatible time string
        date_obs = hdu_header['DATE-OBS']

        if 'TIMESYS' in hdu_header:
            logger.debug(
                "Found 'TIMESYS' card with specified time scale of {0:s}".format(
                    hdu_header['TIMESYS']))

            # Convert to lower case letters for astropy time
            timesys = hdu_header['TIMESYS'].lower()

        else:
            logger.debug(
                "No 'TIMESYS' card found in header, set scaling to 'UTC'")

            timesys = 'utc'

        # Try to convert the 'DATE-OBS' string to UNIX time assuming ISO/ISOT
        # string formatting

        date_obs_val = a_time.get_time_from_ISO_based_string(
            date_obs, scale=timesys)

        return date_obs_val

    else:
        logger.warning("No 'DATE-OBS' card found in header.")

        return None


# === MAIN ===
if __name__ == "__main__":
    pass
