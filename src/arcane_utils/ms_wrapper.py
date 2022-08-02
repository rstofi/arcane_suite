"""Collection of wrapper functions working with MS files. This module is expected
to be used across several pipelines of the suite.
"""

__all__ = ['create_MS_table_object', 'close_MS_table_object', 'get_MS_subtable_path',
        'get_fieldname_and_ID_list_dict_from_MS', 'get_time_based_on_field_names']


import sys
import logging
import numpy as np

from casacore import tables as casatables

from arcane_utils import misc
from arcane_utils.globals import _ACK

#=== Set up logging
logger = logging.getLogger(__name__)

#=== Functions ===
def create_MS_table_object(mspath, readonly=True, **kwargs):
    """This function aims to speed up other bits of this module, 
    by returning a ``casacore.tables.table.table`` object.
    The trick is, that the ``mspath`` argument can be either a string i.e. the path
    to the MS which will be read in and returned, **or** it can be already an
    in-memory ``casacore.tables.table.table`` object.
    This might not be the best solution, but I hope overall a check in a lot of cases will
    speed up code, rather than reading in reading the same MS again-and again.
    So ideally, only one reading in happens for each MS and all inside this function!

    Parameters
    ==========
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    readonly: bool, optional
        If True, the tables of the MS can be read only, but if set to False one can modify the MS

    Returns
    =======
    MS: ``casacore.tables.table.table`` object
        The in-memory Measurement Set
    """
    #create an empty MS in-memory to check the object type: the working solution
    MS_type_tmp = casatables.table('',casatables.maketabdesc([casatables.makescacoldesc('DATA',0)]),memorytable=True,ack=False)

    #if type(mspath) == 'casacore.tables.table.table': #This approach does not work
    if type(mspath) == type(MS_type_tmp):
        #logger.debug('MS already open...')
        MS_type_tmp.close()
        return mspath
    else:
        logger.debug('Open MS: {0:s}'.format(str(mspath))) #We know it is a string in this case
        MS = casatables.table(mspath, ack=_ACK, readonly=readonly)
        MS_type_tmp.close()
        return MS

def close_MS_table_object(mspath):
    """This bit of code should be called at the end of whan working with an MS.
    Basically only closes the MS opened in the beginning. Aims to prevent memory
    leaks and just implementing good practices...

    Parameters
    ==========
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    Returns
    =======
        Closes the MS

    """
    MS_type_tmp = casatables.table('',casatables.maketabdesc([casatables.makescacoldesc('DATA',0)]),memorytable=True,ack=False)

    #if type(mspath) == 'casacore.tables.table.table':
    if type(mspath) == type(MS_type_tmp):
        logger.debug('Close MS')

        MS = create_MS_table_object(mspath)
        MS.close()
    else:
        logger.debug('Input was not a <casacore.tables.table.table> object... continuing.')

def get_MS_subtable_path(mspath, subtable_name, close=False):
    """Subroutine to generate absolute paths for MS subtables using the right
    syntax (i.e. ::SUBTABLE instead of /SUBTABLE)

    See: https://casacore.github.io/python-casacore/casacore_tables.html

    NOTE: this piece of code only works on UNIX systems!

    Parameters
    ==========
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    subtable_name: str
        FULL name of the subtable.

    close:
        If True the MS will be closed

    Returns
    =======
    subtable_path: str
        Absolute path to the subtable

    """
    MS = create_MS_table_object(mspath)

    #List of subtables:
    #print(MS.keywordnames())

    #Select all substrings containing `subtable_name` and select the first result
    #NOTE: only one table sould exist named `/subtable_name`
    subtable_path = [subtables_path for subtables_path in MS.getsubtables() if '/' + subtable_name in subtables_path][0]

    #Get the index of the dash using reverse
    subtable_dash_index = subtable_path.rindex("/")

    subtable_path = subtable_path[:subtable_dash_index] + \
                    "::" + subtable_path[subtable_dash_index+1:]

    if close:
        close_MS_table_object(MS)    

    return subtable_path

def get_fieldname_and_ID_list_dict_from_MS(mspath, scan_ID=False, close=False):
    """Generate the field name -- ID list pairs or with `scan_ID` set to True,
    the scan IDs returned instead of the field IDs, from an MS as a dictionary.

    This is a key function as each field/scan could be queued by it's ID

    Thius is a core function in inspecting MS for field selection

    NOTE: a field can have different ID's attached i.e. the OTZFDUMMY field in
            the CNSS data set. The same applies to scans obviously

    NOTE: I am not 100% if this is how the MS works in terms of field ID's, but
            based on tests, seems legit

    Parameters
    ==========
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    Returns
    =======
    fieldname_ID_dict: dict
        Dictionatry containing the field names and the corresponding field ID's

    """
    MS = create_MS_table_object(mspath)

    fieldtable_path = get_MS_subtable_path(MS,'FIELD', close=False)

    #Open `FIELD` table and read the list of antennas
    fieldtable = create_MS_table_object(fieldtable_path)

    #Set up the empty list
    fieldname_ID_dict = {}

    #The row number in the ANTENNA table corresponds to the field ID
    #See: https://casaguides.nrao.edu/index.php?title=Measurement_Set_Contents

    #I *assume* the same thing is true for the FIELD ID

    #Loop trough the rows in the ANTENNA table and build the dict
    for i in fieldtable.rownumbers():
        
        field_name = fieldtable.getcol('NAME')[i]
        
        if field_name not in list(fieldname_ID_dict.keys()):
            fieldname_ID_dict[field_name] = [i]
        else:
            fieldname_ID_dict[field_name].append(i)
            

    close_MS_table_object(fieldtable)

    #The fieldname ID dict has to be creted to generate the scanname_ID_disct:
    if scan_ID:
        #NOTE this is a really slow sub-routine!
        logger.warning('Matching scan IDs to FIELD_NAMES. This can take some time...')

        scanname_ID_disct = {}

        fieldnames = list(fieldname_ID_dict.keys())

        for field_name in fieldnames:

            field_selection_string = misc.convert_list_to_string(list(fieldname_ID_dict[field_name]))

            scan_qtable = MS.query(query='FIELD_ID IN {0:s}'.format(
                        field_selection_string),
                        columns='SCAN_NUMBER')

            scanname_ID_disct[field_name] = list(np.unique(scan_qtable.getcol('SCAN_NUMBER')))

        if close:
            close_MS_table_object(MS)
    
        return scanname_ID_disct

    else:

        if close:
            close_MS_table_object(MS)

        return fieldname_ID_dict

def get_time_based_on_field_names(mspath, field_name):
    """Get an array containing the time values for a given field.

    NOTE that the times are not necessarily continous!

    Parameters
    ==========
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    field_name: str
        The `NAME` in the 'FIELSD' Table

    Returns
    =======
    times: array of float
        An array containing the time values in the MS' native encoding (!)

    """
    MS = create_MS_table_object(mspath)

    field_Name_ID_dict = get_fieldname_and_ID_list_dict_from_MS(mspath)

    #Select the field name(s)
    field_selection_string = misc.convert_list_to_string(list(field_Name_ID_dict[field_name]))

    time_qtable = MS.query(query='FIELD_ID IN {0:s}'.format(
                        field_selection_string),
                        columns='TIME')

    times = time_qtable.getcol('TIME')
    
    close_MS_table_object(MS)

    return times

def get_time_based_on_field_names(mspath, field_name):
    """Get an array containing the time values for a given field.

    NOTE that the times are not necessarily continous!

    Parameters
    ==========
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    field_name: str
        The `NAME` in the 'FIELSD' Table

    Returns
    =======
    times: array of float
        An array containing the time values in the MS' native encoding (!)

    """
    MS = create_MS_table_object(mspath)

    field_Name_ID_dict = get_fieldname_and_ID_list_dict_from_MS(mspath)

    #Select the field name(s)
    field_selection_string = misc.convert_list_to_string(list(field_Name_ID_dict[field_name]))

    time_qtable = MS.query(query='FIELD_ID IN {0:s}'.format(
                        field_selection_string),
                        columns='TIME')

    times = time_qtable.getcol('TIME')
    
    close_MS_table_object(MS)

    return times




#=== MAIN ===
if __name__ == "__main__":
    pass