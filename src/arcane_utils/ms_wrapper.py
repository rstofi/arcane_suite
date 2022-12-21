"""Collection of wrapper functions working with MS files. This module is expected
to be used across several pipelines of the suite.
"""

__all__ = [
    'create_MS_table_object',
    'close_MS_table_object',
    'get_MS_subtable_path',
    'get_fieldname_and_ID_list_dict_from_MS',
    'rename_single_field',
    'get_time_based_on_field_names_and_scan_IDs']


import sys
import logging
import numpy as np
import warnings

from casacore import tables as casatables

from arcane_utils import misc
from arcane_utils.globals import _ACK
from arcane_utils import time as a_time

from arcane_utils.globals import _SUPPORTED_MS_COL_DIRECTION_KEYWORDS, \
    _SUPPORTED_MS_COL_DIR_UNITS, \
    _SUPPORTED_MS_COL_DIR_REFERENCES

# === Set up logging
logger = logging.getLogger(__name__)

# === Functions ===


def create_MS_table_object(
        mspath,
        readonly=True,
        is_table=False,
        table_name=None,
        **kwargs):
    """This function aims to speed up other bits of this module,
    by returning a ``casacore.tables.table.table`` object.
    The trick is, that the ``mspath`` argument can be either a string i.e. the path
    to the MS which will be read in and returned, **or** it can be already an
    in-memory ``casacore.tables.table.table`` object.
    This might not be the best solution, but I hope overall a check in a lot of cases will
    speed up code, rather than reading in reading the same MS again-and again.
    So ideally, only one reading in happens for each MS and all inside this function!

    Parameters
    ----------
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    readonly: bool, optional
        If True, the tables of the MS can be read only, but if set to False one can modify the MS

    is_table: bool, opt
        If the function is used to close a table opened, this should be passed so
        the logs are more readable

    table_name: str, opt
        The name of the table opened

    Returns
    -------
    MS: ``casacore.tables.table.table`` object
        The in-memory Measurement Set

    """
    # create an empty MS in-memory to check the object type: the working
    # solution
    MS_type_tmp = casatables.table('', casatables.maketabdesc(
        [casatables.makescacoldesc('DATA', 0)]), memorytable=True, ack=False)

    # if type(mspath) == 'casacore.tables.table.table': #This approach does
    # not work
    if isinstance(mspath, type(MS_type_tmp)):
        #logger.debug('MS already open...')
        MS_type_tmp.close()
        return mspath
    else:
        # We know it is a string in this case
        if is_table:
            if table_name is not None:
                logger.debug(
                    "Open MS table '{0:s}': {1:s}".format(
                        table_name, str(mspath)))

            else:
                logger.debug('Open MS table: {0:s}'.format(str(mspath)))
        else:
            logger.debug('Open MS: {0:s}'.format(str(mspath)))

        MS = casatables.table(mspath, ack=_ACK, readonly=readonly)
        MS_type_tmp.close()

        return MS


def close_MS_table_object(mspath, is_table=False, table_name=None):
    """This bit of code should be called at the end of whan working with an MS.
    Basically only closes the MS opened in the beginning. Aims to prevent memory
    leaks and just implementing good practices...

    Parameters
    ----------
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    is_table: bool, opt
        If the function is used to close a table opened, this should be passed so
        the logs are more readable

    table_name: str, opt
        The name of the table closed

    Returns
    -------
        Closes the MS

    """
    MS_type_tmp = casatables.table('', casatables.maketabdesc(
        [casatables.makescacoldesc('DATA', 0)]), memorytable=True, ack=False)

    # if type(mspath) == 'casacore.tables.table.table':
    if isinstance(mspath, type(MS_type_tmp)):

        if is_table:
            if table_name is not None:
                logger.debug("Close MS table '{0:s}'".format(table_name))
            else:
                logger.debug("Close MS table")
        else:
            logger.debug('Close MS')

        MS = create_MS_table_object(mspath)
        MS.close()
    else:
        logger.debug(
            'Input was not a <casacore.tables.table.table> object... continuing.')


def get_MS_subtable_path(mspath, subtable_name, close=False):
    """Subroutine to generate absolute paths for MS subtables using the right
    syntax (i.e. ::SUBTABLE instead of /SUBTABLE)

    See: https://casacore.github.io/python-casacore/casacore_tables.html

    NOTE: this piece of code only works on UNIX systems!

    Parameters
    ----------
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    subtable_name: str
        FULL name of the subtable.

    close:
        If True the MS will be closed

    Returns
    -------
    subtable_path: str
        Absolute path to the subtable

    """
    MS = create_MS_table_object(mspath)

    # List of subtables:
    # print(MS.keywordnames())

    # Select all substrings containing `subtable_name` and select the first result
    # NOTE: only one table sould exist named `/subtable_name`
    subtable_path = [subtables_path for subtables_path in MS.getsubtables(
    ) if '/' + subtable_name in subtables_path][0]

    # Get the index of the dash using reverse
    subtable_dash_index = subtable_path.rindex("/")

    subtable_path = subtable_path[:subtable_dash_index] + \
        "::" + subtable_path[subtable_dash_index + 1:]

    if close:
        close_MS_table_object(MS)

    return subtable_path


def get_fieldname_and_ID_list_dict_from_MS(mspath,
                                           scan_ID=False,
                                           close=False,
                                           ant1_ID=0,
                                           ant2_ID=1):
    """Generate the field name -- ID list pairs or with `scan_ID` set to True,
    the scan IDs returned instead of the field IDs, from an MS as a dictionary.

    This is a key function as each field/scan could be queued by it's ID

    This is a core function in inspecting MS for field selection

    NOTE: a field can have different ID's attached i.e. the OTZFDUMMY field in
            the CNSS data set. The same applies to scans obviously

    NOTE: this routine is sub-optimal for scan IDs as it is working with the MAIN
            table. It uses the informatiuon in the FIELD table for getting the
            field names and IDs though.

    NOTE: to **speed up** the code, I only select data associated with one baseline.
        Since, I query the information from the MAIN table, for MS with hundreds of
        GB size could be inefficient to read in a full column to memory, and slow
        to work with later on. I *assume* that the native TAQL query language is
        optimised solutioin for data selection. Therefore, the idea is to push
        the heavy-lifting to TAQL, and only work with the sub-selected data.

    Parameters
    ----------
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    scan_ID: bool, opt
        If True, the dictionary returned will contain the field names as keys and
        the scan IDs as values, not the field IDs !

    close:
        If True the MS will be closed

    ant1_ID: int, opt
        The ID of a reference antenna used for the underlying TAQL query. This
        parameter *should* not matter for the output, as the MAIN table has all
        antennas associated with all scans and fields. However, in some cases,
        when e.g. an MS is made out from multiple observations, where one is missing
        an antenna, this parameter matters! Please be carefule na know your data
        beforehand.

    ant2_ID: int, opt
        The ID of the second antenna defining the baseline used for the selection.
        The same caveats as for `ref_ant_ID` applyes here.

    Returns
    -------
    fieldname_ID_dict: dict
        Dictionatry containing the field names and the corresponding field ID's

    """
    if ant1_ID == ant2_ID:
        raise ValueError(
            'Only cross-correltion baselines are allowed for field and scan ID queryes!')

    # Note that ANTENNA1 *always* have a smaller ID number than ANTENNA2 in an MS
    # So for a general case, we need to swap the two IDs if ant1_ID > ant2_ID
    if ant1_ID > ant2_ID:
        logger.debug(
            'Swapping ant1_ID and ant2_ID to make sure baseline exists in MS')
        # Swapping two variables without a teporary variable
        ant1_ID, ant2_ID = ant2_ID, ant1_ID

    MS = create_MS_table_object(mspath)

    fieldtable_path = get_MS_subtable_path(MS, 'FIELD', close=False)

    # Open `FIELD` table and read the list of antennas
    fieldtable = create_MS_table_object(
        fieldtable_path, is_table=True, table_name='FIELD')

    # Set up the empty list
    fieldname_ID_dict = {}

    # The row number in the ANTENNA table corresponds to the field ID
    # See: https://casaguides.nrao.edu/index.php?title=Measurement_Set_Contents

    # I *assume* the same thing is true for the FIELD ID

    # Loop trough the rows in the ANTENNA table and build the dict
    for i in fieldtable.rownumbers():

        field_name = fieldtable.getcol('NAME')[i]

        if field_name not in list(fieldname_ID_dict.keys()):
            fieldname_ID_dict[field_name] = [i]
        else:
            fieldname_ID_dict[field_name].append(i)

    del i

    close_MS_table_object(fieldtable, is_table=True, table_name='FIELD')

    # The fieldname ID dict has to be creted to generate the scanname_ID_disct:
    if scan_ID:
        # NOTE this is a really slow sub-routine!
        logger.debug(
            'Matching scan IDs to FIELD_NAMES. This can take some time...')

        scanname_ID_disct = {}

        fieldnames = list(fieldname_ID_dict.keys())

        for field_name in fieldnames:

            field_selection_string = misc.convert_list_to_string(
                list(fieldname_ID_dict[field_name]))

            # Note that string formatting (number of whitespaces or tabs) does
            # not matter
            scan_qtable = MS.query(query='FIELD_ID IN {0:s} \
                            AND ANTENNA1 == {1:d} \
                            AND ANTENNA2 == {2:d}'.format(
                field_selection_string, ant1_ID, ant2_ID),
                columns='SCAN_NUMBER')

            scanname_ID_disct[field_name] = list(
                np.unique(scan_qtable.getcol('SCAN_NUMBER')))

        del field_name

        if close:
            close_MS_table_object(MS)

        return scanname_ID_disct

    else:

        if close:
            close_MS_table_object(MS)

        return fieldname_ID_dict


def get_time_based_on_field_names_and_scan_IDs(mspath,
                                               field_names=None,
                                               scan_IDs=None,
                                               to_UNIX=True,
                                               close=False,
                                               ant1_ID=0,
                                               ant2_ID=1):
    """Get an array containing the time values for a given field and scan selection.

    This is the core function to get the TIME array for given fields and or scans.

    If no field or scan specifyed, all the fields and scans are selected. Also, works
    based on only field or scan ID selection.

    The same caveats as in `get_fieldname_and_ID_list_dict_from_MS` are True for
    the data selection used in this function.

    *Only* WARNING is thrown if the returned data size is 0!

    NOTE: the fields are defined by their names, while the scans are by their ID's!

    NOTE: the times returned are not necessarily continous!


    Parameters
    ----------
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    field_name: list of str, opt
        The list of the selected `NAME` values in the 'FIELSD' Table. If None, all
        fields are selected.

    scan_IDs: list of str, opt
        The list of the selected `SCAN_ID`s. If None, all scans are selected

    to_UNIX: bool, optional
        If False, `TIME` in the native frame values (assumed to be MJD) are returned.
        If True, the output is covrted to UNXI formatting (default).

    close:
        If True the MS will be closed

    ant1_ID: int, opt
        The reference entenna in the baseline used for query the MS

    ant2_ID: int, opt
        The other reference entenna in the baseline used for query the MS

    Returns
    -------
    times: array of float
        An array containing the time values

    """
    if not isinstance(field_names, list) and field_names is not None:
        raise TypeError('Wrong format for input field names!')

    if not isinstance(scan_IDs, list) and scan_IDs is not None:
        raise TypeError('Wrong format for input scan IDs!')

    if ant1_ID == ant2_ID:
        raise ValueError(
            'Only cross-correltion baselines are allowed for time selecttion queryes!')

    # Note that ANTENNA1 *always* have a smaller ID number than ANTENNA2 in an MS
    # So for a general case, we need to swap the two IDs if ant1_ID > ant2_ID

    if ant1_ID > ant2_ID:
        logger.debug(
            'Swapping ant1_ID and ant2_ID to make sure baseline exists in MS')
        # Swapping two variables without a teporary variable
        ant1_ID, ant2_ID = ant2_ID, ant1_ID

    MS = create_MS_table_object(mspath)

    #This is fast
    field_Name_ID_dict = get_fieldname_and_ID_list_dict_from_MS(
        mspath, ant1_ID=ant1_ID, ant2_ID=ant2_ID)

    # Get the field selection
    if field_names is None:
        field_selection_string = misc.convert_list_to_string(
            [field_Name_ID_dict[field_name][0] for field_name in field_Name_ID_dict.keys()])

    else:
        # Select the field ID based on the name(s)
        field_selection_string = misc.convert_list_to_string(
            [field_Name_ID_dict[field_name][0] for field_name in field_names])

    # Query the data based on the field and scan ID selection
    if scan_IDs is None:
        time_qtable = MS.query(query='FIELD_ID IN {0:s} \
                                AND ANTENNA1 == {1:d} \
                                AND ANTENNA2 == {2:d}'.format(
            field_selection_string, ant1_ID, ant2_ID),
            columns='TIME')

    else:
        # Select the scna ID's
        scan_selection_string = misc.convert_list_to_string(scan_IDs)

        time_qtable = MS.query(query='FIELD_ID IN {0:s} \
                                AND SCAN_NUMBER IN {1:s} \
                                AND ANTENNA1 == {2:d} \
                                AND ANTENNA2 == {3:d}'.format(
            field_selection_string, scan_selection_string,
            ant1_ID, ant2_ID),
            columns='TIME')

    # Get the time values in the native format
    times = time_qtable.getcol('TIME')

    if np.size(times) == 0:
        warnings.warn('No TIME data is selected!')
        #logger.warning('No TIME data is selected!')

    # Raise warning if not only unique times retrieved
    elif np.size(times) != np.size(np.unique(times)):
        logger.warning(
            'Not only uniqe TIME data is selected, please check your MS and data selection!')

    if close:
        close_MS_table_object(MS)

    if to_UNIX:
        # Do a 'soft' check for the input values to make sure UNIX format is
        # returned
        if a_time.soft_check_if_time_is_UNIX(
                a_time.convert_MJD_to_UNIX(times[0])):
            return a_time.convert_MJD_to_UNIX(times)
        elif a_time.soft_check_if_time_is_UNIX(times[0]):
            return times
        else:
            raise ValueError('MS time formatting is not MJD or UNIX!')

    else:
        return times


def rename_single_field(mspath,
                        field_ID,
                        new_field_name,
                        source=False,
                        pointing=False,
                        close=False):
    """Renaming a single field based on it's ID.

    Optionally the NAME variable in the SOURCE and the POINTING tables with the
    *same* ID can be remaned as well.

    The code literally takes the given row number and overwrite the name cell.

    NOTE: a field can have multiple sources, so set the source and pointing to True
        carefully!

    TO DO: write a separate function that can overwrite/rename the sources in the
        SOURCE table separately

    Parameters
    ----------
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    scan_ID: int
        The selected `SCAN_ID` to rename. This is equivalent to the row number in
        the FIELD table

    new_field_name: str
        The new `NAME` values written to the target tables.

    source: bool, opt
        If True, the NAME value with the same ID in the FIELD table is overwritten.

    pointing: bool, opt
        If True, the NAME value with the same ID in the POINTING table is overwritten.

    close:
        If True the MS will be closed

    Returns
    -------
    Overwite the input MS NAME cell of the specified tables and rows

    """

    MS = create_MS_table_object(mspath)

    # Seclect the tables to overwrite
    if source and pointing:
        logger.info('Renaming the NAME cell in row {0:d} '.format(
            field_ID)
            + 'in tables: FIELD, SOURCE, POINTING')
        table_list = ['FIELD', 'SOURCE', 'POINTING']
    elif source:
        logger.info('Renaming the NAME cell in row {0:d} '.format(
            field_ID)
            + 'in tables: FIELD, SOURCE')
        table_list = ['FIELD', 'SOURCE']
    elif pointing:
        logger.info('Renaming the NAME cell in row {0:d} '.format(
            field_ID)
            + 'in tables: FIELD, POINTING')
        table_list = ['FIELD', 'POINTING']
    else:
        logger.info('Renaming the NAME cell in row {0:d} '.format(
            field_ID)
            + 'in table: FIELD')
        table_list = ['FIELD']

    # Rename
    for ftable_name in table_list:
        ftable_path = get_MS_subtable_path(MS, ftable_name, close=False)

        ftable = create_MS_table_object(
            ftable_path,
            is_table=True,
            table_name=ftable_name,
            readonly=False)

        if ftable.rownumbers() == []:
            logger.warning('The table {0:s} is empty!'.format(
                ftable_name))
        else:
            if field_ID not in ftable.rownumbers():
                raise ValueError('Invalid field ID provided!')

            logger.debug('Original NAME in table {0:s}: {1:s}'.format(
                ftable_name, ftable.getcol('NAME')[field_ID]))

            ftable.putcell('NAME', field_ID, new_field_name)

            logger.debug('New NAME in table {0:s}: {1:s}'.format(
                ftable_name, ftable.getcol('NAME')[field_ID]))

        close_MS_table_object(ftable, is_table=True, table_name=ftable_name)

    if close:
        close_MS_table_object(MS)


def check_dir_column_values(table_path,
                            colname,
                            table_name=None,
                            close=False):
    """A general script that checks if `arcane_suite` supports the data format and
    reference frame of coordainates in an MS trough looking at the keywords.

    The idea is, that some MS can have coordinates defined in B1950 or something
    like this, which could break other parts of the code, so I have a check looking
    at supported coordinate frames and units

    TO DO: implement a similar approact to the TIME values instead of the soft
        checks I curently doing

    Parameters
    ----------
    table_path: str
        The input path or an MS TABLE or a ``casacore.tables.table.table`` object

    colname: str
        The name of the column, for which the check is performed, since tables can
        have multiple direction-related columns such as PHASE_DIR, REFERENCE_DIR...etc.

    table_name: str, opt
        The name of the table opened

    close:
        If True the MS will be closed

    Returns
    -------

    """
    if table_name is None:
        logger.warning(
            "NO 'table_name' is provided, guessing from 'table_path'!")

        # If the table is an object the output string first line is the table path
        # If not keep the string intact. The last subfolder i.e. after last / will be
        # the table name
        # NOTE: only works on linux systems

        # TO DO: put this to separate function

        table_name = str(table_path).split('\n')[0].split('/')[-1]

    logger.debug(
        "Checking direction support in table {0:s}, column {1:s}".format(
            table_name, colname))

    # Get the table in question
    dir_table = create_MS_table_object(table_path,
                                       is_table=True,
                                       table_name=table_name,
                                       readonly=True)

    # Get the selected column
    dir_col = casatables.tablecolumn(dir_table, colname)

    i = 0
    for dir_keyword in _SUPPORTED_MS_COL_DIRECTION_KEYWORDS:

        # Here, I have some hard-coded knowledge of the MS structure!

        if i == 0:  # QuantumUnits
            keyword_val = dir_col.getkeyword(dir_keyword)

            for du in _SUPPORTED_MS_COL_DIR_UNITS:
                if du not in keyword_val:
                    raise ValueError(
                        "Not supported direction attribute {0:s} in table {1:s} column {2:s} keyword {3:s}!".format(
                            str(du), table_name, colname, dir_keyword))

        elif i == 1:  # MEASINFO
            keyword_val = dir_col.getkeyword(
                dir_keyword)  # This is a dictionary

            if keyword_val['Ref'] not in _SUPPORTED_MS_COL_DIR_REFERENCES:
                raise ValueError("Not supported direction attribute {0:s} in table {1:s} column {2:s} keyword {3:s}!".format(
                    str(keyword_val['Ref']), table_name, colname, dir_keyword))

        i += 1

    # return 0


def get_phase_centres_and_field_ID_list_dict_from_MS(mspath,
                                                     field_ID_list=None,
                                                     ant1_ID=0,
                                                     ant2_ID=1,
                                                     close=False):
    """Simple function used to determine the phase centre coordinates for a given
    list (or all) of FIELD_IDs and return a dictionary of FIELD_ID and [RA, Dec].
    The latter is given in degrees.

    Parameters
    ----------
    mspath: str
        The input MS path or a ``casacore.tables.table.table`` object

    field_ID_list: list of ints, opt
        The selected `FIELD_ID`s for which the phase centre coordinates are retrieved.
        All fields are selected if not specified

    close:
        If True the MS will be closed

    ant1_ID: int, opt
        The ID of a reference antenna used for the underlying TAQL query. This
        parameter *should* not matter for the output, as the MAIN table has all
        antennas associated with all scans and fields. However, in some cases,
        when e.g. an MS is made out from multiple observations, where one is missing
        an antenna, this parameter matters! Please be carefule na know your data
        beforehand.

    ant2_ID: int, opt
        The ID of the second antenna defining the baseline used for the selection.
        The same caveats as for `ref_ant_ID` applyes here.

    Return
    ------
    phase_centres_field_IDs_dict: dict
        The {FIELD_ID:[RA,Dec]} dictionary

    """
    MS = create_MS_table_object(mspath)

    ftable_name = 'FIELD'  # Only use thr FIELD table

    # Get the field IDs if not provided
    if field_ID_list is None:

        logger.debug("Getting field ID's from MS")

        field_Name_ID_dict = get_fieldname_and_ID_list_dict_from_MS(
            MS, ant1_ID=ant1_ID, ant2_ID=ant2_ID, close=False)

        field_ID_list = [field_Name_ID_dict[field_name][0]
                         for field_name in field_Name_ID_dict.keys()]

        logger.debug("Field ID's from MS: {0:s}".format(
            misc.convert_list_to_string(field_ID_list)))

    # Define a dict in which, I will store the field_ID's and the coordinates
    phase_centres_field_IDs_dict = {}

    # Loop trough field IDs
    ftable_path = get_MS_subtable_path(MS, ftable_name, close=False)

    ftable = create_MS_table_object(
        ftable_path,
        is_table=True,
        table_name=ftable_name,
        readonly=True)

    if ftable.rownumbers() == []:
        raise ValueError('The table {0:s} is empty!'.format(
            ftable_name))

    for field_ID in field_ID_list:
        if field_ID not in ftable.rownumbers():
            raise ValueError('Invalid field ID provided!')

        # Get the RA and Dec valused from the table, but first check the
        # direction columns
        check_dir_column_values(
            ftable,
            table_name=ftable_name,
            colname='PHASE_DIR')

        # Get the RA and Dec values
        # Select the first polarisation i.e. working only for StokesI for now
        dir_coords = ftable.getcol('PHASE_DIR')[0][field_ID]

        # The dir coords should be in radians => conver to deg => convert to astropy coord
        # phase_centre_coord = SkyCoord(misc.rad_to_deg(dir_coords[0]) * u.deg,
        #                            misc.rad_to_deg(dir_coords[1]) * u.deg,
        # frame='icrs') #Since only J2000 is supported currently

        # Convert coords to deg
        phase_centres_field_IDs_dict[field_ID] = [
            misc.rad_to_deg(
                dir_coords[0]), misc.rad_to_deg(
                dir_coords[1])]

    close_MS_table_object(ftable, is_table=True, table_name=ftable_name)

    if close:
        close_MS_table_object(MS)

    return phase_centres_field_IDs_dict


# === MAIN ===
if __name__ == "__main__":
    pass
