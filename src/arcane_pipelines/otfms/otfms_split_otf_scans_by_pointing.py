"""The command line tool for the Snakemake rule: `split_otf_scans_by_pointing`

Basically a custom wrapper around the casa task split, based on the OTF field ID
and the corresponding time values read from the snakemake config yaml file.

Based ona the OTF `ID` and the `split_timedelta` time range, the code selects
visibilities around the time value corresponding to the ID in the config.yml file
"""

import sys
import logging
import argparse

from arcane_utils import pipeline

#=== Set logging
logger = pipeline.init_logger()

#=== Functions ===
def main():
	"""
	"""
	#=== Set arguments
	parser = argparse.ArgumentParser()

	


    #=== Exit
    logger.info('Single OTF pointing MS created')
    sys.exit(0)

#=== MAIN ===
if __name__ == "__main__":
    main()