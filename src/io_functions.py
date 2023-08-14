import numpy as np
import datetime

from data_trace import DataTrace
from constants import *


class Loader:

    def __init__(self) -> None:
        pass

    def load_trace(fpath: str):
        raise NotImplementedError


class LeCroyLoader(Loader):

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def load_trace(fpath) -> DataTrace:
        if not ".csv" in fpath:
            raise ValueError("Input file must be a .csv file.")

        time_values, data_values = np.loadtxt(fpath, delimiter=',', skiprows=5,
                                              unpack=True)
        return DataTrace(time_values, data_values, 
                         time_units="s", data_units="V")
