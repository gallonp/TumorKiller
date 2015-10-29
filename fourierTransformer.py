import pandas as pd
import matplotlib
import math
import numpy as np
from scipy.fftpack import fft
import matplotlib.pyplot as plt

def getFFT(p):
        N = len(p)*4
        T = 1.0 / 800.0
        x = np.linspace(0.0, N*T, N)
        y = np.array(p)
        y = np.lib.pad(y, (0,len(p)*3), 'constant', constant_values=0)
        yf = fft(y)
        xf = np.linspace(0.0, 1.0/(2.0*T) , 21)
        # plt.plot(xf, 2.0/N * np.abs(yf[0:N/2:N/40]))
        # plt.grid()
        # plt.show()
        return 2.0/N * np.abs(yf[0:N/2:N/40])