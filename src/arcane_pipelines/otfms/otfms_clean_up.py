""""The command line tool for the Snakemake rule: `clean_up`
"""

import sys
import os
import argparse
import logging

from arcane_utils import pipeline


# === Set logging
logger = pipeline.init_logger()

# === Functions ===


def main():
    """

    """
    # === Set arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c',
        '--config_file',
        required=True,
        help='Snakemake yaml configuration file for the otfms pipeline',
        action='store',
        type=str)

    # ===========================================================================
    args = parser.parse_args()  # Get the arguments

    logger.info("Running *otfms_clean_up*")

    logger.info("Exit 0")

    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
