"""Unit tests for the data storage module."""

import datastorage as ds
import unittest


class TestDataStorage(unittest.TestCase):
    """Tests the data storage module."""
    # pylint:disable=protected-access

    def setUp(self):
        """Create a new in-memory database for each test case."""
        self.conn = ds.create_sqlite_connection(':memory:')

    def test_create_sqlite_connection(self):
        """A SQLite Connection object is created."""
        conn = ds.create_sqlite_connection(':memory:')
        # Make sure a Connection object is returned.
        self.assertIsNotNone(conn)

    def test_table_exists(self):
        """Method returns true IFF the specified table exists."""
        # Method under test returns false if table does not exist.
        table_name_dne = 'DoesNotExist'
        self.assertFalse(ds._table_exists(self.conn, table_name_dne))

        # Method under test returns true if table exists.
        table_name_exists = 'NewTable'
        ds._create_table(self.conn, table_name_exists, '(Id TEXT)')
        self.assertTrue(ds._table_exists(self.conn, table_name_exists))

    def test_create_table(self):
        """Method creates database table with specified columns."""
        # Table name and column description.
        table_name = 'NewTable'
        table_column_dsc = '(Id Text)'  # one column

        # The table does not already exist in the database.
        self.assertFalse(ds._table_exists(self.conn, table_name))
        # Call method under test: create database.
        ds._create_table(self.conn, table_name, table_column_dsc)
        # The table now exists in the database.
        self.assertTrue(ds._table_exists(self.conn, table_name))

    def test_fetch_entry_from_table(self):
        """Method fetches entry from table, if it exists."""
        # The table does not exist in the database.
        table_name_dne = 'TableDoesNotExist'
        self.assertFalse(ds._table_exists(self.conn, table_name_dne))
        # Method returns None because table does not exist.
        db_entry = ds._fetch_entry_from_table(self.conn, table_name_dne, '')
        self.assertIsNone(db_entry)

        # The table exists in the database, but the entry does not exist.
        table_name = 'TableExists'
        table_desc = '(Id TEXT)'
        ds._create_table(self.conn, table_name, table_desc)
        self.assertTrue(ds._table_exists(self.conn, table_name))
        # Method returns None because the entry does not exist.
        entry_id_dne = '1'
        db_entry = ds._fetch_entry_from_table(self.conn, table_name, entry_id_dne)
        self.assertIsNone(db_entry)

        # The table exists, and the entry also exists.
        new_table_entry = ('1',)
        ds._store_entry_in_table(self.conn, table_name, new_table_entry)
        # Method retrieves stored entry from database.
        entry_id = new_table_entry[0]
        db_entry = ds._fetch_entry_from_table(self.conn, table_name, entry_id)
        self.assertEqual(new_table_entry, db_entry)

    def test_fetch_all_from_table(self):
        """Method fetches all entries from the specified table."""
        # The table does not exist in the database.
        table_name_dne = 'TableDoesNotExist'
        self.assertFalse(ds._table_exists(self.conn, table_name_dne))
        # Method returns empty list because table does not exist.
        db_entries = ds._fetch_all_from_table(self.conn, table_name_dne)
        expected_entries = []
        self.assertEqual(expected_entries, db_entries)

        # The table exists in the database, but no entries exist.
        table_name = 'TableExists'
        table_desc = '(Id TEXT)'
        ds._create_table(self.conn, table_name, table_desc)
        self.assertTrue(ds._table_exists(self.conn, table_name))
        # Method returns empty list because no entries exist.
        db_entries = ds._fetch_all_from_table(self.conn, table_name)
        expected_entries = []
        self.assertEqual(expected_entries, db_entries)

        # The table contains one entry.
        table_entry_1 = ('1',)
        ds._store_entry_in_table(self.conn, table_name, table_entry_1)
        # Method returns list containing the one entry.
        db_entries = ds._fetch_all_from_table(self.conn, table_name)
        expected_entries = [table_entry_1]
        self.assertEqual(expected_entries, db_entries)

        # The table contains multiple (two) entries.
        table_entry_2 = ('2',)
        ds._store_entry_in_table(self.conn, table_name, table_entry_2)
        # Method returns list containing the entries.
        db_entries = ds._fetch_all_from_table(self.conn, table_name)
        # Note: order not specified, so we test for set equality.
        expected_entries = [table_entry_1, table_entry_2]
        self.assertEqual(set(expected_entries), set(db_entries))

    def test_store_entry_in_table(self):
        """Method stores new entry in the specified table."""
        # This entry should be stored in the table.
        table_entry = ('1',)

        # The table does not exist in the database.
        table_name_dne = 'TableDoesNotExist'
        self.assertFalse(ds._table_exists(self.conn, table_name_dne))
        # Method raises exception because table does not exist.
        with self.assertRaises(Exception):
            ds._store_entry_in_table(self.conn, table_name_dne, table_entry)

        # The table exists.
        table_name = 'TableExists'
        table_desc = '(Id TEXT)'
        ds._create_table(self.conn, table_name, table_desc)
        self.assertTrue(ds._table_exists(self.conn, table_name))
        # Call method under test.
        ds._store_entry_in_table(self.conn, table_name, table_entry)
        # The entry has been stored in the database.
        db_entries = ds._fetch_all_from_table(self.conn, table_name)
        expected_entries = [table_entry]
        self.assertEqual(expected_entries, db_entries)


if __name__ == '__main__':
    unittest.main()
