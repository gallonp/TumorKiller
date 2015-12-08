"""FFT methods."""

import numpy as np
from scipy.fftpack import fft


def get_fft(time_domain_mrs):
    """Applies FFT to given MRS data.

    Args:
        time_domain_mrs: Time-domain MRS data.

    Returns:
        Frequency-domain MRS data.
    """
    # pylint:disable=invalid-name, no-member

    # As recommeded by Professor Bluml, zero-fill the data up to ~8000
    # points to preserve all signal-to-noise.
    N = len(time_domain_mrs)*4
    y = np.array(time_domain_mrs)
    y = np.lib.pad(y, (0, len(time_domain_mrs)*3), 'constant', constant_values=0)
    # Sample spacing.
    #T = 1.0 / 800.0
    #x = np.linspace(0.0, N*T, N)
    yf = fft(y)
    #xf = np.linspace(0.0, 1.0/(2.0*T), 21)
    return 2.0/N * np.abs(yf[0:N/2:N/40])
