"""Methods for storing and retrieving files in the database."""

import cPickle
import sqlite3


# Name of file for SQLite database.
# Note: In-memory database (":memory:") is erased after closing the connection.
SQLITE_DATABASE_FILE = 'database.db'

# Name of table containing brain scan data.
TABLE_NAME_BRAINSCANS = 'BrainScans'
# Column description for table containing brain scan data.
TABLE_COLS_BRAINSCANS = '(Id TEXT, FileName TEXT, FileContents BLOB, GroupLabel TEXT)'

# Name of table containing classifiers.
TABLE_NAME_CLASSIFIERS = 'Classifiers'
# Column description for table containing classifiers.
TABLE_COLS_CLASSIFIERS = '(Id TEXT, ClassifierName TEXT, ClassifierType TEXT, SerializedClassifier TEXT)'


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


def _FetchEntryFromTable(conn, table_name, entry_id):
    """Fetches entry with specified ID from table.
    
    Args:
        conn: A database Connection object.
        table_name: Name of the table to query.
        entry_id: ID of the entry to fetch.

    Returns:
        The entry with specified ID if found. Otherwise returns None.
    """
    # Make sure the table exists.
    if not _TableExists(conn, table_name):
        return None
    # Query for the classifier.
    with conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM %s WHERE Id=\"%s\"' % (table_name, entry_id))
        query_result = cur.fetchone()
        # If found, return the classifier.
        return query_result if query_result else None


def _FetchAllFromTable(conn, table_name):
    """Fetches all rows from the specified table.
    
    Args:
        conn: A database Connection object.
        table_name: Name of the table to query.
    
    Returns:
        A list of all entries in the specified table.
    """
    # Make sure the table exists.
    if not _TableExists(conn, table_name):
        return []
    # Query for all entries in the table.
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM %s' % table_name)
        return cur.fetchall()


def StoreMRSData(conn, file_id, file_name, file_contents, group_label):
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


def FetchMRSData(conn, file_id):
    """Fetches the specified MRS data from the database.

    Args:
        conn: A database Connection object.
        file_id: Unique identifier for the file.

    Returns:
        If an entry with specified ID is found, the MRS data is returned in a
        4-tuple of the form (file_id, file_name, file_contents, group_label).
        Otherwise, the method returns None.
    """
    # Fetch specified MRS data from the database.
    return _FetchEntryFromTable(conn, TABLE_NAME_BRAINSCANS, file_id)


def FetchAllMRSData(conn):
    """Fetches all MRS data from the database.

    Args:
        conn: A database Connection object.

    Returns:
        List of all MRS data entries in the database. Each item in the list is
        a 4-tuple of the form (ID, filename, MRS file contents, group label).
    """
    # Fetch all MRS data from the database.
    return _FetchAllFromTable(conn, TABLE_NAME_BRAINSCANS)


def StoreClassifier(conn, classifier_id, classifier_name, classifier_type, classifier):
    """Stores the given classifier in the database.

    Args:
        conn: A database Connection object.
        classifier_id: ID to associate with the saved classifier. Must be unique.
        classifier_name: String description for the classifier.
        classifier_type: The classifier type (e.g. neural network, SVM).
        classifier: The classifier that should be saved.
    """
    # Serialize the classifier.
    classifier = cPickle.dumps(classifier)
    # Create the table if it does not exist.
    _CreateTableIfNotExists(conn, TABLE_NAME_CLASSIFIERS, TABLE_COLS_CLASSIFIERS)
    # Try to insert a new row into the table.
    with conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO %s VALUES(?, ?, ?, ?)' % TABLE_NAME_CLASSIFIERS,
            (classifier_id, classifier_name, classifier_type, classifier))


def FetchClassifier(conn, classifier_id):
    """Queries the database for a classifier with specified ID.

    Args:
        conn: A database Connection object.
        classifier_id: Unique identifier for the classifier.

    Returns:
        A 4-tuple containing (classifier_id, classifier_name, classifier_type,
        classifier). This method will return None if a classifier with the
        specified ID is not found in the database.
    """
    # Fetch specified classifier from the database.
    db_entry = _FetchEntryFromTable(conn, TABLE_NAME_CLASSIFIERS, classifier_id)
    if db_entry is None:
        return None
    # Convert serialized classifier to object.
    return (db_entry[0], db_entry[1], db_entry[2], cPickle.loads(str(db_entry[3])))


def FetchAllClassifiers(conn):
    """Fetches all classifiers from the database.

    Args:
        conn: A database Connection object.

    Returns:
        List of all classifiers in the database. Each item in the list is a
        4-tuple of the form (classifier_id, classifier_name, classifier_type,
        classifier).
    """
    # Fetch all classifiers from the database.
    db_entries = _FetchAllFromTable(conn, TABLE_NAME_CLASSIFIERS)
    # Convert serialized classifiers to objects.
    converted_entries = []
    for entry in db_entries:
        converted_entries.append(
            (entry[0], entry[1], entry[2], cPickle.loads(str(entry[3]))))
    return converted_entries
