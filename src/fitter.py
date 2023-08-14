import numpy as np

import statsmodels.api as sm
from scipy.stats import chi2

from dataclasses import dataclass

from burst_function import BurstFunction
from data_trace import DataTrace
from constants import *


class FitQualityWarning(Warning):
    pass

class FitQualityError(RuntimeError):
    pass

@dataclass(slots=True)
class FitData:
    fit_ampls: np.ndarray
    r2_val: float

    def from_results(self, res: sm.regression.linear_model.RegressionResults):
        self.fit_ampls = res.params
        self. r2_val = res.rsquared


class Fitter:

    def __init__(self, name: str) -> None:
        """
        Class containing fitting methods logic. `name` input parameter is for
        the purposes of error traceback, and is what should display for the name
        of a problematic fit if an fitting error is raiesd.
        """
        
        self.results = None
        self.name = name

    def linear_regress_burst(self, dtrace: DataTrace, 
                             bfunc: BurstFunction) -> sm.regression.linear_model.RegressionResults:
        
        time_vals, data_vals = dtrace.get_time_values(), \
                                   dtrace.get_data_values()
        regressors = bfunc.get_pulse_matrix(time_vals)
        
        # Perform a linear regression
        sm.add_constant(regressors)
        results = sm.OLS(data_vals, regressors).fit()
        self.results = results

        return results

    def get_chi2_stats(self, errs: np.ndarray):
        if self.results is None:
            raise AttributeError("`self.results` is None. Must perform fit "
                                 "before calculating test statistics.")
        
        chi2_val = np.sum(self.results.resid ** 2 / (errs ** 2))
        red_chi2_val = chi2_val / self.results.df_resid

        p_val = 1 - chi2.cdf(chi2_val, df=self.results.df_resid)
        return red_chi2_val, p_val

    @DeprecationWarning
    def _linear_regress_burst(self, dtrace: DataTrace, 
                             bfunc: BurstFunction) -> FitData:

        time_vals, data_vals = dtrace.get_time_values(), \
                                   dtrace.get_data_values()
        
        regressors = bfunc.get_pulse_matrix(time_vals)

        # The ordinary least squares estimator is given by multiplying the matrix
        # (X^T X)^-1 X^T by the observations vector y. This is just the 
        # Moore-Penrose pseudo-inverse of X, which is given by `np.linalg.pinv` 
        fit_ampls = np.linalg.pinv(regressors).dot(data_vals)

        # Compute the R^2 value associated with the fit
        fvals = bfunc.burst_function(time_vals, fit_ampls)
        r2_val = self.get_r2(data_vals, fvals)

        return FitData(fit_ampls, r2_val)

    def evaluate_fit_quality(self, results):
        """
        Performs an automated test to evaluate fit quality. This test is
        rudimentary and will only raise errors in an extreme case. Discression
        should be used when evaluating the quality of fit, and no substitute
        can be made for manually looking at the quality of fit statistics and
        associated plots.
        """
        if results.rsquared < 0.95:
            raise FitQualityWarning(f"{self.name} R^2={results.rsquared:.3f} < "
                                    "0.95. Please evaluate the quality of fit "
                                    "more thoroughly by calling the script "
                                    "with verbose output.")
        if results.rsquared < 0.5:
            raise FitQualityError(f"R^2={results.rsquared:.3f} < 0.50. "
                                  "This fit is very poor and should not be "
                                  "used.")

    @staticmethod
    def get_r2(data_values : np.ndarray, function_values : np.ndarray) -> float:
        """
        Returns the coefficient of determination, or R^2 value,
        of a curve fit.
        """
        sum_sq_res = np.sum((data_values - function_values)**2)
        sum_sq_tot = np.sum((data_values - np.mean(data_values))**2)

        return 1 - (sum_sq_res / sum_sq_tot)

    def get_adj_r2(self, data_values : np.ndarray, function_values : np.ndarray, 
                   pulse_num : int) -> float:
        r2_val = self.get_r2(data_values, function_values)
        return 1 - (1 - r2_val) * (len(data_values) - 1) / (len(data_values) -
                                                            pulse_num + 1)
