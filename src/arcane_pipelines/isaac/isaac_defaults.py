"""Default variables used by the `arcane_isaac` pipeline
"""

# === Import globals
from arcane_utils.globals import _SNAKEMAKE_BASE_NAME, _CARACAL_BASE_NAME

# Define the default alias names and values for the command line tools
# used by the pipeline

_isaac_default_aliases = ['snakemake_alias',
                          'caracal_alias']

_isaac_default_alias_values = [_SNAKEMAKE_BASE_NAME,
                               _CARACAL_BASE_NAME]

# Define the default values of the config file
_isaac_default_config_dict = {
    'ENV': {},
    'DATA_CONFIG': {
        'from_otfms': [
            'False',
            True,
            'if True, the input is generated from the output of an OTFMS pipeline'],
        'otfms_output_path': [
            '',
            False,
            'absolute path, requried if from_otfms is set to True'],
        'otfms_acronym': [
            '',
            False,
            'string (same as the OTF_acronym used to generate the data)']},
    'DATA_IDs': {
        'data_ID_0 ': [
            '',
            True,
            'data ID string (field name in MS)']},
    'MS_PATHS': {
        'MS_path_0': [
            '',
            True,
            'absolute path']},
    'CALTABLE_PATHS': {
        'caltable_path_0': [
            '',
            True,
            'absolute path to the callib solutions']},
    'OUTPUT': {
        'image_acronym': [
            'isaac',
            True,
            'string']}}
