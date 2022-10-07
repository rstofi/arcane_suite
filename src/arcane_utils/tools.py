"""Simple stand-alone tools
"""

__all__ = ['estimate_RMS_level']

import sys
import logging

import numpy as np

from scipy.constants import Boltzmann as kb

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def estimate_RMS_level(Na, dnu, t_int, Np=2, Ts=50, D=13.5, eta=1.):
    """Simple routine to estimate the *naturally* weighted RMS noise level for an
    interferometer using uniform dishes. The code basically computes
    eq. 6.62 from TMS 3rd edition, but I acually use form of the equation as
    written in my doctoral thesis.

    TO DO: add the w-terms (weight factors) to beable to account for non-natural
            weighting

    Parameters
    ----------
    Na: int
        Number of antennas in the array

    dnu: float
        Observing bandwidth in units of Hz

    t_int: float
        Integrated on-source observation time in units of s

    Np: int
        Number of polarisations used in data acquisition

    Ts: float
        System temperature in units of K

    D: float
        The dish diameter in units of m

    eta: float
        Efficiency parameter in between ]0:1].

    Returns
    -------
    S_RMS: float
        The point-source sensitivity in units of Jy (or Jy/beam ... doesn't matter
        as this is the point-source sensitivity)

    """
    Nb = (Na * (Na - 1)) / 2.  # Number of baselines

    A = np.pi * np.power(D, 2) / 4.  # Dish collecting area

    S_RMS = (2 * kb * Ts) / (A * eta * np.sqrt(2 * Nb * Np * dnu * t_int))

    S_RMS *= 1e+26  # Convert to Jansky

    return S_RMS


# === MAIN ===
if __name__ == "__main__":
    pass
