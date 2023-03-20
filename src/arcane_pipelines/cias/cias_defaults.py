"""Default variables used by the `arcane_cias` pipeline
"""

# === Import globals
from arcane_utils.globals import _SNAKEMAKE_BASE_NAME, _CASA_BASE_NAME

# Define the default alias names and values for the command line tools
# used by the pipeline

_cias_default_aliases = ['snakemake_alias'
                            'caracal_alias']

_cias_default_alias_values = [_SNAKEMAKE_BASE_NAME,
                                _CARACAL_BASE_NAME]

# Define the default values of the config file
_cias_default_config_dict = {'ENV': {
},
    'DATA': {
    'DATA_ID': ['', True, 'the MS name (with no extension)']},  # 9"
    'OUTPUT': {
    'OTF_acronym': ['OTFasp', True, 'string']
}}