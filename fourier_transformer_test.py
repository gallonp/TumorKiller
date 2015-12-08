"""Unit tests for the FFT module."""

import dataparser
import fourier_transformer
import unittest


class TestFourierTransformer(unittest.TestCase):
    """Tests the FFT module."""

    @classmethod
    def setUpClass(cls):
        """Parse data from a MRS data file."""
        mrs_data_string = str(open('data/05_E2', 'r').read())
        cls.mrs_data = dataparser.get_xy_data(mrs_data_string)

    def test_get_fft(self):
        """Method applies FFT to the given time-domain data."""
        fft_data = fourier_transformer.get_fft(self.mrs_data)
        # Make sure a non-empty list of floats is returned.
        self.assertIs(list, type(list(fft_data)))  # convert numpy array
        self.assertTrue(len(fft_data) > 0)
        self.assertIs(float, type(float(fft_data[0])))  # convert numpy float


if __name__ == '__main__':
    unittest.main()
