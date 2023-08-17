import argparse
from typing import Any
import numpy as np
from tabulate import tabulate
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

import os, sys
import pickle
import logging

from io_functions import *
from fitter import Fitter, FitQualityError
from burst_function import BurstFunction
from plotting import plot_graphs_together
from constants import *
from logger import add_handlers, stream_h


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
add_handlers(logger)


class NoT0Val:
    """
    Sentenal value for when no t0 value is passed from the command line.
    """
    num_instances = 0
    def __init__(self) -> None:
        self.num_instances += 1
        if (self.num_instances > 1):
            raise RuntimeError("Do not instantiate this class more than once.")


def fit_trace(filepath: str, t0_value: float, n_pulses: int, ptype: TraceType,
              show_fig=False, verbose_output=False):

    data_trc = LeCroyLoader.load_trace(filepath)
    bfunc = BurstFunction(t0_value, n_pulses, ptype)
    res_data_trc = data_trc.make_restricted(bfunc.t_start, bfunc.t_end)

    fname = os.path.splitext(os.path.split(filepath)[-1])[0]
    fitter = Fitter(name=fname)

    fit_error = None
    try:
        fit = fitter.linear_regress_burst(res_data_trc, bfunc)

    except FitQualityError as err:
        # If a fit quality error is raised, display the plot of the
        # fit before throwing the exception.
        fit_error = err
        show_fig = True

    # `uval` is taken as the uncertainty estimate for the scope trace values,
    # and it is the maximum voltage value read by the scope before the first
    # pulse in "C1trc00000.csv" from June 14, 2023.
    uval = 0.001167
    chi2_res, p_val = fitter.get_chi2_stats(
        np.ones(res_data_trc.trace_len) * uval
    )

    if verbose_output:
        print("\n\n")
        print(fit.summary())
        print("\n\n")
        print(tabulate([["Red. chi2", chi2_res], ["p-value", p_val]],
                       headers=["Chi-Squared Stats"], floatfmt='.2e'))
        print("\n")

    if show_fig:
        fig, _, _, _ = plot_graphs_together(data_trc, fit, bfunc)

        fig.suptitle(fname)
        fig.tight_layout()
        plt.show()

    if not fit_error is None:
        logger.error(fit_error, exc_info=True)
        raise FitQualityError(fit_error)

    logger.info("Trace %s fit with R^2=%.2f." % (fname, fit.rsquared))
    return {'fit_results': fit, 'data_trc': data_trc, 'burst_model': bfunc}


class CommandHandler(object):

    # Make this class a singleton
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(CommandHandler, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.file_handler = None

    @staticmethod
    def _check_handler(func):
        def checked_method(self, *args, **kwargs):
            if self.file_handler is None:
                raise RuntimeError("File handler must be created before "
                                   f"{func} can be called.")
            return func(self, *args, **kwargs)
        return checked_method
    
    def create_file_handler(self, outpath, force):
        self.file_handler = OutputHandler(outpath, force_overwrites=force)

    @_check_handler
    def single_fit(self, args: argparse.Namespace):
        """
        Fits a single trace specified by a filename, and saves a file containing
        the amplitude values for the pulses in that trace, according to the values
        specified. Optially show figures, produce verbose output, or pickle the
        object containing the fit and all of its auxiliary statistical data (see
        command line flags).
        """
        
        logger.info("Initiating singe fit from '%s'" % args.filepath)
        ttype = getattr(TraceType, args.trace_type)
        fit_dict = fit_trace(args.filepath, args.t0_value, 
                             args.n_pulses, ttype, show_fig=args.plot,
                             verbose_output=args.verbose)
        fit_results = fit_dict['fit_results']
        print(f"Fit produced with R^2={fit_results.rsquared}")

        if args.pickle:
            self.file_handler.pickle_obj("fit-objects.pickle", fit_dict)

        fname = os.path.splitext(os.path.split(args.filepath)[-1])[0]
        fname = f"{fname}-amplitudes.csv"
        self.file_handler.save_csv(fit_results.params, fname, 
                                   col_headers=["Amplitudes (V)"], 
                                   encoding="utf-8")

    @_check_handler
    def batch_fit(self, args: argparse.Namespace):
        """
        Fit a batch of files all at once. Files to fit are specified by a 'manifest'
        file, which is a .csv file containnig in the first column a list of
        filenames to fit, in the second column the type of trace of each file (one
        of the strings 'PUMP', 'REFLECTED', 'TRANSMITTED'), and optionally in
        the third column a list of t0 values (floats) to start at for each file.
        This last option needs to be enabled with a flag in the command.
        
        If t0 values are not specified in the manifest file, it is expected that
        the t0 value will be specified in the command line argument. If the t0
        value is specified both in the manifest file and the command line, an
        error will be raised; similarly if neither are specified.
        """

        metadata = np.loadtxt(args.file_manifest, delimiter=',', unpack=True,
                            dtype=str, encoding='utf-8')
        if args.get_t0_from_meta:
            fnames, ttypes, t0_vals = metadata
            if not isinstance(args.t0_value, NoT0Val):
                raise ValueError("Cannot specify t0 values in the manifest file "
                                "and the command line at the same time.")
        else:
            fnames, ttypes = metadata
            if isinstance(args.t0_value, NoT0Val):
                raise ValueError("Must either pass t0 values from the manifest "
                                "file, or from the command line.")

        logger.info(f"Fitting batch from {args.data_path}")
        
        fits = {}
        amplitdes = []
        for idx, (filename, ttype) in enumerate(zip(fnames, ttypes)):

            t0_val = args.t0_value
            if args.get_t0_from_meta:
                t0_val = float(t0_vals[idx])

            ttype_enum = getattr(TraceType, ttype)
            fpath = os.path.join(args.data_path, str(filename))

            trace_fit = fit_trace(fpath, t0_val, args.n_pulses, ttype_enum, 
                                args.plot, args.verbose)
            fits[filename] = trace_fit
            trace_fit = trace_fit['fit_results']

            amplitdes.append(trace_fit.params)

            sys.stdout.write(f"\rFit {idx + 1} / {len(fnames)} completed.")
            sys.stdout.flush()

        print("\n")

        if args.pickle:
            self.file_handler.pickle_obj("fit-objects-dict.pickle", fits)

        ampl_arr = np.column_stack(amplitdes)
        self.file_handler.save_csv(ampl_arr, "trace-amplitudes.csv",
                                   col_headers=fnames, encoding="utf-8")

    @staticmethod
    def loader(args: argparse.Namespace):
        """
        Load pickled fit results data, and optionally display plots or summary.

        WARNING: Only use this method on pickle files that are known to be
        generated by this program; pickle is vulnerable to arbitrary code execution.
        """

        with open(args.filename, 'rb') as file:
            results = pickle.load(file)
        
        print(results)
        if args.trace:
            results = results[args.trace]

        try:
            fit, data_trc, bfunc = results.values()
        except AttributeError as err:
            if isinstance(results, RegressionResultsWrapper):
                fit = results
                data_trc = None
                bfunc = None
            else:
                raise err

        except ValueError as err:
            logger.error("Pickle load failed. Maybe you forgot to pass the "
                        "trace you were looking for with -t")
            raise err

        logger.info(f"Fit results loaded from {args.filename}")
        if args.verbose:
            print("\n", fit.summary())

        if bfunc is None or data_trc is None:
            logger.error("Cannot plot fit since some data was not saved with "
                         "the pickle object.")
            return

        if args.plot:
            fig, _, _, _ = plot_graphs_together(data_trc, fit, bfunc)

            if args.trace:
                fig.suptitle(args.trace)
            fig.tight_layout()
            plt.show()
