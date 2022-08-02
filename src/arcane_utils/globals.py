"""Global variables used by `arcane_utils`
"""

#Enabling messages of successful interaction with the MS e.g. successful opening of a table
global _ACK 
_ACK = False

#Define the indices for the correlator types in MSv2.
#
#See e.g.: https://github.com/SKA-ScienceDataProcessor/algorithm-reference-library/
#blob/1b2c8d6079249202864abf8c60cdea40f0f123cb/processing_components/visibility/base.py#L644
#
# 1-4: Stokes polarization frame
# 5-8: Circular polarization frame
# 9-12: Linear polarization frame
#
global _MSV2_CORR_TYPE_DICT
_MSV2_CORR_TYPE_DICT = {1:'I',
                        2:'Q',
                        3:'U',
                        4:'V',
                        5:'RR',
                        6:'RL',
                        7:'LR',
                        8:'LL',
                        9:'XX',
                        10:'XY',
                        11:'YX',
                        12:'YY'}