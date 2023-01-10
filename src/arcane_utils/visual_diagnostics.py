"""Collection of analysis functions, which outputs a simple plot. These should
be general routines.

NOTE: I mightmove some functions from here to tools
"""

__all__ = []

import sys
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

def create_field_ID_RA_Dec_plot(mspath,
                                otf_fig_path,
                                ptitle="Phase centres (with field ID's)",
                                field_ID_list=None,
                                ant1_ID=0,
                                ant2_ID=1,
                                close=False):
    """
    NOTE: This docstring was created by ChatGPT3.

    Creates a scatter plot of the phase centres of the fields in an MS file.
    Each point on the plot is labeled with the field ID.

    Parameters:
    - mspath (str): The path to the MS file or an MS table object.
    - otf_fig_path (str): The path to the output figure file.
    - ptitle (str): The title of the plot. (default: "Phase centres (with field ID's)")
    - field_ID_list (list): A list of field ID's to include in the plot. (default: None)
    - ant1_ID (int): The ID of the first antenna. (default: 0)
    - ant2_ID (int): The ID of the second antenna. (default: 1)
    - close (bool): Whether to close the MS file after reading. (default: False)

    Returns:
    None
    """

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


# === MAIN ===
if __name__ == "__main__":
    pass
