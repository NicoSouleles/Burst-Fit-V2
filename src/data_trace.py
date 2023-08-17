import numpy as np


class DataTrace:
    """
    Class representing a time series. Contains two numpy arrays, one list of 
    time values, and one list of data values. Also contanis auxiliary info
    like units.
    """
    def __init__(self, time_values: np.ndarray, data_values: np.ndarray, 
                 time_units: str = "s", data_units: str = "V") -> None:
        
        self.trace_len = time_values.size
        if self.trace_len != data_values.size:
            raise ValueError("`time_values` and `data_values` must be the same "
                             "size.")

        self._data_values: np.ndarray = None 
        self._time_values: np.ndarray = None
        self.set_time_values(time_values)
        self.set_data_values(data_values)

        self.time_units = time_units
        self.data_units = data_units

        self._current_idx = 0

    def __iter__(self):
        return self
    
    def __next__(self) -> tuple[np.ndarray, np.ndarray]:
        if self._current_idx == self.trace_len:
            raise StopIteration
        
        rval = (self._time_values[self._current_idx], 
                self._data_values[self._current_idx])
        self._current_idx += 1
        
        return rval
    
    def _set_arr(self, attrname: str, arr: np.ndarray) -> None:
        if np.ndim(arr) != 1:
            raise ValueError("Input must be a 1D array.")
        setattr(self, attrname, arr)

    def make_restricted(self, t_start, t_end):
        """
        Returns a data trace with time and data values restricted between to lie
        `t_start` and `t_end`.
        """
        idx = np.vectorize(lambda t: t_start <= t <= t_end)(self._time_values)
        new_times = self._time_values[idx]
        new_data = self._data_values[idx]
        return DataTrace(new_times, new_data, self.time_units, self.data_units)

    def get_data_values(self) -> np.ndarray:
        return self._data_values
    
    def get_time_values(self) -> np.ndarray:
        return self._time_values

    def set_data_values(self, values: np.ndarray) -> None:
        self._set_arr('_data_values', values)

    def set_time_values(self, values: np.ndarray) -> None:
        self._set_arr('_time_values', values)
