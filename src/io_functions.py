import numpy as np

import os
import pickle
import logging

from data_trace import DataTrace
from constants import *
from logger import add_handlers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
add_handlers(logger)


def output_pickler(pickle_path, obj, force_overwrite):
    """
    Pickles an output data object.
    """
    try:
        test_filepath_overwrite(pickle_path, force_overwrite)
    except RuntimeError as err:
        logger.error(err, exc_info=True)
        raise err
    
    with open(pickle_path, 'wb') as file:
        pickle.dump(obj, file)
        logger.info(f"Pickle file saved to '{pickle_path}'")


def test_filepath_overwrite(filename: str, overwrite: bool):
    """
    Raises an error if filename exists and the 'force' flag is false.
    """
    
    if os.path.exists(filename) and not overwrite:
        raise RuntimeError(f"'{filename}' has already been written to. Please "
                           "choose another output destination, or enable "
                           "file-overwritting with the -f flag.")


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
