import numpy as np
import statsmodels.api as sm
from scipy.stats import chi2

import logging
from dataclasses import dataclass

from burst_function import BurstFunction
from data_trace import DataTrace
from constants import *
from logger import add_handlers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
add_handlers(logger)


class FitQualityError(RuntimeError):
    """
    Should be raised when the fit quality dips below a certain threshold.
    """
    pass


class Fitter:
    """
    Class containing fitting methods logic. `name` input parameter is for
    the purposes of error traceback, and is what should display for the name
    of a problematic fit if an fitting error is raiesd.
    """

    def __init__(self, name: str, thresh: float=0.95) -> None:
        
        self.results = None
        self.name = name
        
        try:
            self.set_rsquared_thresh(thresh)
        except ValueError as err:
            logger.error(err, exc_info=True)
            raise err

    def set_rsquared_thresh(self, thresh: float):
        """
        Sets a trheshold for the R^2 value of any fits produced; will cause an
        error to be raised if a fit is produced with an R^2 below this treshold.
        """
        
        if not isinstance(thresh, float):
            raise ValueError("Threshold value must be a float")

        if not (0. <= thresh <= 1.):
            raise ValueError("Threshold value must be between 0 and 1")

        self._fit_qual_thresh = thresh

    def linear_regress_burst(self, dtrace: DataTrace, 
                             bfunc: BurstFunction) -> sm.regression.linear_model.RegressionResults:
        """
        Performs a linear regression on a data trace with a BurstFunction object
        as the model. Returns the `statsmodels.api.linear_model.RegressionResults` 
        objcet produced by the fit.

        Raises a `FitQualityError` if the R^2 value is less that the threshold 
        parameter in this class.
        """
        
        time_vals, data_vals = dtrace.get_time_values(), \
                                   dtrace.get_data_values()
        regressors = bfunc.get_pulse_matrix(time_vals)
        
        # Perform a linear regression
        sm.add_constant(regressors)
        results = sm.OLS(data_vals, regressors).fit()
        self.results = results

        if results.rsquared < self._fit_qual_thresh:
            raise FitQualityError(f"{self.name} R^2={results.rsquared:.3f} < "
                                    f"{self._fit_qual_thresh}. Please evaluate "
                                    "the quality of fit more thoroughly by "
                                    "calling the script with verbose output, "
                                    "or reduce the R^2 threshold value.")

        return results

    def get_chi2_stats(self, errs: np.ndarray):
        """
        Does a chi-squared test on the fit, given uncertainty values for the
        data.
        """

        if self.results is None:
            raise AttributeError("`self.results` is None. Must perform fit "
                                 "before calculating test statistics.")
        
        chi2_val = np.sum(self.results.resid ** 2 / (errs ** 2))
        red_chi2_val = chi2_val / self.results.df_resid

        p_val = 1 - chi2.cdf(chi2_val, df=self.results.df_resid)
        return red_chi2_val, p_val

    @staticmethod
    def get_r2(data_values : np.ndarray, function_values : np.ndarray) -> float:
        """
        Returns the coefficient of determination, or R^2 value, of a curve fit.
        """
        sum_sq_res = np.sum((data_values - function_values)**2)
        sum_sq_tot = np.sum((data_values - np.mean(data_values))**2)

        return 1 - (sum_sq_res / sum_sq_tot)

    def get_adj_r2(self, data_values : np.ndarray, function_values : np.ndarray, 
                   pulse_num : int) -> float:
        """
        Returns the adjusted R^2 value of a fit.
        """
        r2_val = self.get_r2(data_values, function_values)
        return 1 - (1 - r2_val) * (len(data_values) - 1) / (len(data_values) -
                                                            pulse_num + 1)
