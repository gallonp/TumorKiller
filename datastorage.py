"""Methods for storing and retrieving files in the database."""

import sqlite3


# Name of file for SQLite database.
# Note: In-memory database (":memory:") is erased after closing the connection.
SQLITE_DATABASE_FILE = 'database.db'

# Column description for table containing brain scan data.
TABLE_COLS_BRAINSCANS = '(Id TEXT, FileName TEXT, FileContents BLOB, GroupLabel TEXT)'

# Name of table containing brain scan data.
TABLE_NAME_BRAINSCANS = 'BrainScans'


def CreateSQLiteConnection(db_filename=SQLITE_DATABASE_FILE):
    """Creates a connection to the SQLite database in the specified file.

    Args:
        db_filename: Path to the SQLite database file.

    Returns:
        A database Connection object.
    """
    return sqlite3.connect(db_filename)


def _TableExists(conn, table_name):
    """Determines whether or not the given table exists in the database.
    
    Args:
        conn: A database Connection object.
        table_name: Name of table.
    
    Returns:
        True if a table the with given name is found in the database, otherwise
        returns false.
    """
    # Query for the table.
    with conn:
        cur = conn.cursor()
        cur.execute(('SELECT name FROM sqlite_master'
                     ' WHERE type="table" AND name="%s"') % table_name)
        return len(cur.fetchall()) == 1


def _CreateTableIfNotExists(conn, table_name, columns):
    """Creates a new table in the given database.
    
    Args:
        conn: A database Connection object.
        table_name: Name of the table to create.
        columns: Column definition for the table.
    """
    # Create the table.
    with conn:
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS %s%s' % (table_name, columns))


def SaveMRSData(conn, file_id, file_name, file_contents, group_label):
    """Stores given MRS data in the database.

    Args:
        conn: A database Connection object.
        file_id: Unique identifier for the file.
        file_name: Name of the file.
        file_contents: Raw file contents.
        group_label: Name of the therapy group that the given patient data belongs to.
    """
    # Create the table if it does not exist.
    _CreateTableIfNotExists(conn, TABLE_NAME_BRAINSCANS, TABLE_COLS_BRAINSCANS)
    # Try to insert a new row into the table.
    with conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO %s VALUES(?, ?, ?, ?)' % TABLE_NAME_BRAINSCANS,
            (file_id, file_name, file_contents, group_label))


def ReadMRSData(conn, file_id):
    """Reads the specified MRS data from the database.

    Args:
        conn: A database Connection object.
        file_id: Unique identifier for the file.

    Returns:
        If an entry with specified ID is found, the MRS data is returned in a
        4-tuple of the form (file_id, file_name, file_contents, group_label).
        Otherwise, the method returns None.
    """
    # Make sure the table exists.
    if not _TableExists(conn, TABLE_NAME_BRAINSCANS):
        return None
    # Query for the file.
    with conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM %s WHERE Id=\"%s\"' %
            (TABLE_NAME_BRAINSCANS, file_id))
        data = cur.fetchone()
        # If found, return the file contents.
        return data if data else None


def ListMRSData(conn):
    """Gets list of all MRS data entries stored in the database.

    Args:
        conn: A database Connection object.

    Returns:
        List of all MRS data entries in the database. Each item in the list is
        a 4-tuple of the form (ID, filename, MRS file contents, group label).
    """
    # Make sure the table exists.
    if not _TableExists(conn, TABLE_NAME_BRAINSCANS):
        return []
    # Query for files in the table.
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM %s' % TABLE_NAME_BRAINSCANS)
        return cur.fetchall()
