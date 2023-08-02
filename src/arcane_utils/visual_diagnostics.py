"""Collection of analysis functions, which outputs a simple plot. These should
be general routines.

NOTE: I mightmove some functions from here to tools
"""

__all__ = ['create_field_ID_RA_Dec_plot_from_single_MS',
           'create_field_ID_RA_Dec_plot_from_MS_list']

import sys
import os
import logging
import warnings

from arcane_utils import ms_wrapper
from arcane_utils import misc


import matplotlib
import matplotlib.pyplot as plt

# === Set global figure variables for matplotlib
# RCparams for plot formatting
matplotlib.rcParams['xtick.direction'] = 'in'
matplotlib.rcParams['ytick.direction'] = 'in'

matplotlib.rcParams['xtick.major.size'] = 9
matplotlib.rcParams['ytick.major.size'] = 9

matplotlib.rcParams['xtick.major.width'] = 3
matplotlib.rcParams['ytick.major.width'] = 3

matplotlib.rcParams['axes.linewidth'] = 2

plt.rcParams['xtick.labelsize'] = 16
plt.rcParams['ytick.labelsize'] = 16

# Set automatic axis limits nicely
plt.rcParams['axes.autolimit_mode'] = 'round_numbers'

# 4 sampled colors from viridis
c0 = '#440154'  # Purple
c1 = '#30678D'  # Blue
c2 = '#35B778'  # Greenish
c3 = '#FDE724'  # Yellow

outlier_color = 'dimgrey'

# === Set up logging
logger = logging.getLogger(__name__)


# === Functions ===
def create_field_ID_RA_Dec_plot_from_single_MS(
        mspath: str,
        otf_fig_path: str,
        ptitle: str = "Phase centres",
        field_ID_list: list = None,
        display_IDs: int = False,
        ant1_ID: int = 0,
        ant2_ID: int = 1,
        close: bool = False):
    """
    NOTE: This docstring was created by ChatGPT3.

    Creates a scatter plot of the phase centres of the fields in a SINGLE MS file.
    Each point on the plot is labeled with the field ID.

    Parameters:
    -----------
    mspath: str
        The path to the MS file or an MS table object.

    otf_fig_path: str
        The path to the output figure file.

    ptitle: Optional[str], default "Phase centres (with field ID's)"
        The title of the plot.

    field_ID_list: Optional[List[int]], default None
        A list of field ID's to include in the plot.

    display_IDs: bool
        If set to True the field ID's are written on tiop of the points
        (not recommended for scanning observations as the text can be too crowded)

    ant1_ID: int, default 0
        The ID of the first antenna.

    ant2_ID: int, default 1
        The ID of the second antenna.

    close: bool, default False
        Whether to close the MS file after reading.

    Returns:
    -------
    Creates a plot
    """

    if not display_IDs:
        logger.info("Creating field IDs Ra--Dec plot")
    else:
        logger.info("Creating field IDs Ra--Dec plot with field IDs")

    # Get the phase centres and ID's from the MS
    phase_centre_ID_dict = ms_wrapper.get_phase_centres_and_field_ID_list_dict_from_MS(
        mspath=mspath, field_ID_list=field_ID_list, ant1_ID=ant1_ID, ant2_ID=ant2_ID, close=close)

    # Create the plot
    fig = plt.figure(1)
    ax = fig.add_subplot(111)

    logger.debug(
        "Selected field ID's: {0:s}".format(
            misc.convert_list_to_string(
                list(
                    phase_centre_ID_dict.keys()))))

    # Set some offset for the field ID's
    text_offset = 0.002  # In degrees

    for field_id in phase_centre_ID_dict.keys():
        ax.scatter(phase_centre_ID_dict[field_id][0],
                   phase_centre_ID_dict[field_id][1],
                   color=c1, marker='o', s=50)

        if display_IDs:
            ax.text(phase_centre_ID_dict[field_id][0] + text_offset,
                    phase_centre_ID_dict[field_id][1] + text_offset,
                    field_id, fontsize=14)

    ax.set_xlabel(r'RA -- SIN [deg]', fontsize=18)
    ax.set_ylabel('Dec -- SIN [deg]', fontsize=18)

    plt.suptitle(ptitle, fontsize=18)

    # Set figsize
    plt.gcf().set_size_inches(8, 5)  # NOT that the size is defined in inches!

    plt.savefig(otf_fig_path, bbox_inches='tight')
    plt.close()


def create_field_ID_RA_Dec_plot_from_MS_list(
        ms_IDs_list: list,
        blob_path: str,
        otf_fig_path: str,
        ptitle: str = "Phase centres",
        ant1_ID: int = 0,
        ant2_ID: int = 1,
        close: bool = True):
    """
    Creates a scatter plot of the phase centres of the fields from multiple OTF
    format MS files, from which ONLY the first field ID is considered.

    NOTE: this function cannot display IDs by default, as from each MS the field
    with 0 ID is used.

    Parameters:
    -----------
    ms_IDs_list: list of int
        A list of the IDs used to get the OTF format MS files from unde /blob

    otf_fig_path: str
        The path to the output figure file.

    ptitle: Optional[str], default "Phase centres (with field ID's)"
        The title of the plot.

    field_ID_list: Optional[List[int]], default None
        A list of field ID's to include in the plot.

    display_IDs: bool
        If set to True the field ID's are written on tiop of the points
        (not recommended for scanning observations as the text can be too crowded)

    ant1_ID: int, default 0
        The ID of the first antenna.

    ant2_ID: int, default 1
        The ID of the second antenna.

    close: bool, default False
        Whether to close the MS file after reading.

    Returns:
    -------
    Creates a plot

    """
    logger.info("Creating field IDs Ra--Dec plot")

    phase_centre_list_from_blob = []

    for ms_ID in ms_IDs_list:
        mspath = os.path.join(
            blob_path,
            'otf_pointing_no_{0:s}.ms'.format(
                str(ms_ID)))

        # All MS should have only one field with ID = 0. We create a dict and
        # get the corrsponding element
        phase_centre = ms_wrapper.get_phase_centres_and_field_ID_list_dict_from_MS(
            mspath=mspath, field_ID_list=[0], ant1_ID=ant1_ID, ant2_ID=ant2_ID, close=close)[0]

        phase_centre_list_from_blob.append(phase_centre)

    # Create the plot
    fig = plt.figure(1)
    ax = fig.add_subplot(111)

    for i in range(0, len(phase_centre_list_from_blob)):
        ax.scatter(phase_centre_list_from_blob[i][0],
                   phase_centre_list_from_blob[i][1],
                   color=c1, marker='o', s=50)

    ax.set_xlabel(r'RA -- SIN [deg]', fontsize=18)
    ax.set_ylabel('Dec -- SIN [deg]', fontsize=18)

    plt.suptitle(ptitle, fontsize=18)

    # Set figsize
    plt.gcf().set_size_inches(8, 5)  # NOT that the size is defined in inches!

    plt.savefig(otf_fig_path, bbox_inches='tight')
    plt.close()


# === MAIN ===
if __name__ == "__main__":
    pass
