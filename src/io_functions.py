import numpy as np

import os
import pickle
import logging
import datetime

from data_trace import DataTrace
from constants import *
from logger import add_handlers, stream_h


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
add_handlers(logger)


class OutputHandler:

    def __init__(self, filepath, force_overwrites=False):
        
        self.fpath = filepath
        self.fname, self.fileext = os.path.splitext(
            os.path.split(filepath)[-1]
        )

        self.force_overwrites = force_overwrites
        self.preamble = f"Output generated at {datetime.datetime.now()}\n\n"

    def set_file_preamble(self, preamble: str):
        if not isinstance(preamble, str):
            raise ValueError("Preamble must be of type str")
        self.preamble = preamble
    
    def test_filepath_overwrite(self, filename: str):
        """
        Raises an error if filename exists and the 'force' flag is false.
        """
        
        if os.path.exists(filename) and not self.force_overwrites:
            raise RuntimeError(f"'{filename}' has already been written to. "
                               "Please choose another output destination, or " 
                               "enable file-overwritting with the -f flag.")

    def save_csv(self, arr: np.ndarray, fname: str, col_headers: list[str]=[], 
                 encoding: str=None):
        """
        Wrapper for numpy's savetxt function, to save a numpy array to a .csv
        file.

        `col_headers` is a list of names for the columns in the array to be 
        saved. Headers will be saved as comments (i.e. '# ' will be appended
        to the front of each headername). Must have the same length as the 
        number of columns in `arr`.
        """
        outfile = os.path.join(self.fpath, fname)
        self.test_filepath_overwrite(outfile)
        
        if col_headers is not []:
            self.preamble += col_headers[0] + "# ".join(col_headers[1:])

        np.savetxt(outfile, arr, header=self.preamble, delimiter=',', 
                   encoding=encoding)

        stream_h.setLevel(logging.INFO)
        logger.info(f"Burst amplitudes saved to '{outfile}'")
        stream_h.setLevel(logging.ERROR)

    def pickle_obj(self, filename, obj):
        """
        Pickles an output data object.
        """
        pickle_path = os.path.join(self.fpath, filename)
        try:
            self.test_filepath_overwrite(pickle_path)
        except RuntimeError as err:
            logger.error(err, exc_info=True)
            raise err
        
        with open(pickle_path, 'wb') as file:
            pickle.dump(obj, file)
            stream_h.setLevel(logging.INFO)
            logger.info(f"Pickle file saved to '{pickle_path}'")
            stream_h.setLevel(logging.ERROR)


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
            err =  ValueError("Input file must be a .csv file.")
            logger.error(err, exc_info=True)
            raise err

        time_values, data_values = np.loadtxt(fpath, delimiter=',', skiprows=5,
                                              unpack=True)
        logger.info("Data loaded from '%s'" % fpath)
        return DataTrace(time_values, data_values, 
                         time_units="s", data_units="V")
