"""Default variables used by the `arcane_otfms` pipeline
"""

from arcane_utils.globals import _SNAKEMAKE_BASE_NAME, _CASA_BASE_NAME

# Define the default alias names and values for the command line tools
# used by the pipeline

_otfms_default_aliases = ['snakemake_alias',
                          'casa_alias',
                          'chgcentre_alias']

_otfms_default_alias_values = [_SNAKEMAKE_BASE_NAME,
                               _CASA_BASE_NAME,
                               'chgcentre']


# Define the default values of the config file
_otfms_default_config_dict = {'ENV': {
},
    'DATA': {
    'MS': ['', True, 'absolute path'],
    'pointing_ref': ['', True, 'absolute path'],
    'target_field_list': ['', True, 'comma separated list'],
    'split_calibrators': ['False', True, "boolean"],
    'calibrator_list': ['', False, 'comma separated list or none'],
    'scans': ['', False, 'comma separated list of scan IDs or none'],
    'timerange': ['', False, 'CASA-style timerange or none'],
    'ant1_ID': ['0', False, 'int or none'],
    'ant2_ID': ['1', False, 'int or none'],
    'time_crossmatch_threshold': ['0.001', False, 'float or none'],
    'split_timedelta': ['0.5', False, 'float or none'],
    'position_crossmatch_threshold': ['0.0025', False, 'float or none']},  # 9"
    'OUTPUT': {
    'OTF_acronym': ['OTFasp', True, 'string'],
    'MS_outname': ['final', True, 'string (without the .ms extension)'],
    'deep_clean': ['False', False, 'boolean']
}}

# Some misc default values
_clean_up_maxdepth = 1  # The maximum depth used by the `clean_up` rule
