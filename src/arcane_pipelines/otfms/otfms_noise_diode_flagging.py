"""The command line tool for the Snakemake rule: `flag_noise_diodes`

NOTE: the flags are derived from the `otf_field_names.dat` file generated by the
`list_new_otf_field_names` rule
"""

import sys
import os
import argparse
import logging


# === Set logging
logger = pipeline.init_logger()

# === Functions ===


def main():
    """
    """

    logger.info("Running *flag_noise_diodes*")

    logger.info("Exit 0")

    sys.exit(0)


# === MAIN ===
if __name__ == "__main__":
    main()
