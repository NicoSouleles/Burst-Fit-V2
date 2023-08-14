import numpy as np

from constants import *
from pulse_profiles import GaussianExp


class BurstFunction:

    def __init__(self, t_0: float, n_pulses: int, 
                 pulse_type: TraceType) -> None:
        self._t0 = t_0
        self._n_pulses = n_pulses
        
        self.ptype = pulse_type
        self.pulse_shape = GaussianExp(PULSE_PARAM_IDX[pulse_type])

        self.t_start = self.get_t0() - PULSE_WIDTH / 2
        self.t_end = self.t_start + \
                        self.get_time_from_pulses(self.get_n_pulses())

    def get_t0(self) -> float:
        return self._t0
    
    def get_n_pulses(self) -> int:
        return self._n_pulses

    def set_t0(self, value: float) -> None:
        if not isinstance(value, float):
            raise ValueError("`value` must be a float.")
        self._t0 = value

    def set_n_pulses(self, value: float) -> None:
        if not isinstance(value, int):
            raise ValueError("`value` must be an integer.")
        self._n_pulses = value

    def set_pulse_params(self, params):
        if len(params) != self.pulse_shape.param_num:
            raise ValueError(f"Must pass {self.pulse_shape.param_num} "
                             "parameters.")
        self.pulse_shape.parameters = np.array(params)

    @staticmethod
    def tau_function(n : np.ndarray) -> np.ndarray:
        """
        Returns the timing value for each pulse within a burst of four. See diagram
        in README for how constants TAU_1, TAU_2 and TAU_3 relate to the overall 
        timing.
        """

        # Returns 1 if 'value' is congruent to 'n' mod 4, else returns 0.
        compare_func = lambda value : np.vectorize(lambda x : x == value)
        compare_func = compare_func(np.mod(n, 4))

        return compare_func(1) * TAU_1 + compare_func(2) * TAU_2 + \
                compare_func(3) * TAU_3

    def get_time_from_pulses(self, n_vals):
        return PERIOD * np.floor_divide(n_vals, 4) + self.tau_function(n_vals)

    def get_pulse_matrix(self, time_vals) -> np.ndarray:
            """
            Return a matrix of pulse values, where each column corresponds to a 
            series of times (axis 0), and each row corresponds to a different 
            value of n (axis 1).

            This is also a matrix of regressors for the burst function if doing linear 
            regression.
            """

            n_values = np.arange(0, self._n_pulses, 1, dtype=int)

            total_tshift = self._t0 - TRACE_DELAY_IDX[self.ptype]
            time_values = time_vals[:, None] - total_tshift - \
                            self.get_time_from_pulses(n_values[None, :])

            pulse_shape_func = self.pulse_shape.norm_pulse_shape
            return pulse_shape_func(time_values, *self.pulse_shape.parameters)

    def burst_function(self, time_values, amplitudes) -> np.ndarray:

            if len(amplitudes) != self._n_pulses:
                raise ValueError("Number of amplitudes must equal number of "
                                "pulses.")
            amplitudes = np.array(amplitudes)

            pulse_val_matrix = self.get_pulse_matrix(time_values)
            return pulse_val_matrix.dot(amplitudes)
