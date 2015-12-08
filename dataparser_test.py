"""Unit tests for the data parser module."""

import dataparser
import unittest


class TestDataParser(unittest.TestCase):
    """Tests the data parser module."""

    @classmethod
    def setUpClass(cls):
        """Get string contents of a MRS data file."""
        cls.mrs_data = str(open('data/05_E2', 'r').read())

    def test_get_header_data(self):
        """Method parses header from MRS data file."""
        header_data = dataparser.get_header_data(self.mrs_data)
        # Make sure a non-empty dictionary is returned.
        self.assertIs(dict, type(header_data))
        self.assertTrue(len(header_data) > 0)

    def test_get_xy_data(self):
        """Method parses header from MRS data file."""
        xy_data = dataparser.get_xy_data(self.mrs_data)
        # Make sure a non-empty list of complex numbers is returned.
        self.assertIs(list, type(xy_data))
        self.assertTrue(len(xy_data) > 0)
        self.assertIs(complex, type(xy_data[0]))


if __name__ == '__main__':
    unittest.main()
