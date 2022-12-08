"""Default variables used by the `arcane_otfms` pipeline
"""

# Define the default alias names and values for the command line tools
# used by the pipeline

_otfms_default_aliases = ['snakemake_alias', 'chgcentre_alias', 'casa_alias']
_otfms_default_alias_values = ['snakemake', 'chgcentre', 'casa']


# Define the default values of the config file
_otfms_default_config_dict = {'ENV': {
},
    'DATA': {
    'MS': ['', True, 'absolute path'],
    'pointing_ref': ['', True, 'absolute path'],
    'calibrator_list': ['', False, 'comma separated list'],
    'target_field_list': ['', True, 'comma separated list'],
    'scans': ['', False, 'comma separated list of scan IDs'],
    'timerange': ['', False, 'CASA-style timerange'],
    'ant1_ID': ['', False, 'int'],
    'ant2_ID': ['', False, 'int'],
    'time_crossmatch_threshold': ['', False, 'float'],
    'split_timedelta': ['', False, 'float']}}
