import argparse
import numpy as np
from tabulate import tabulate
import matplotlib.pyplot as plt

import os
import pickle
import datetime
import sys
import logging

from io_functions import LeCroyLoader, output_pickler, test_filepath_overwrite
from fitter import Fitter, FitQualityError
from burst_function import BurstFunction
from plotter import plot_graphs_together
from constants import *
from logger import add_handlers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
add_handlers(logger)


class NoT0Val:
    """Sentenal value for when no t0 value is passed from the command line."""
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



def single_fit(args: argparse.Namespace):
    """
    Fits a single trace specified by a filename, and saves a file containing
    the amplitude values for the pulses in that trace, according to the values
    specified. Optially show figures, produce verbose output, or pickle the
    object containing the fit and all of its auxiliary statistical data (see
    command line flags).
    """
    
    logger.info("Initiating singe fit from '%s'" % args.filepath)
    ttype = getattr(TraceType, args.trace_type)
    fit_dict = fit_trace(args.filepath, args.t0_value, args.n_pulses, ttype, 
                         show_fig=args.plot, verbose_output=args.verbose)
    fit_results = fit_dict['fit_results']

    if args.pickle:
        out_fpath = os.path.join(args.output_path, "fit-objects.pickle")
        output_pickler(out_fpath, fit_dict, args.force)

    preamb = f"""\
Output generated at {datetime.datetime.now()}

Amplitudes (V)"""
    input_fname = os.path.splitext(os.path.split(args.filepath)[-1])[0]
    out_data_path = os.path.join(args.output_path, 
                                 f"{input_fname}-amplitudes.csv")
    test_filepath_overwrite(out_data_path, args.force)
    np.savetxt(out_data_path, fit_results.params, header=preamb, delimiter=',')
    logger.info(f"Burst amplitudes saved to '{out_data_path}'")


def batch_fit(args: argparse.Namespace):
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

    if args.pickle:
        out_fpath = os.path.join(args.output_path, "fit-objects-dict.pickle")
        output_pickler(out_fpath, fits, args.force)

    preamb = f"""\
Output generated at {datetime.datetime.now()}

""" + ", ".join([f"# {fname}" for fname in fnames])
    ampl_arr = np.column_stack(amplitdes)
    out_data_path = os.path.join(args.output_path, "trace-amplitudes.csv")

    test_filepath_overwrite(out_data_path, args.force)
    np.savetxt(out_data_path, ampl_arr, header=preamb, delimiter=',')
    logger.info(f"Burst amplitudes saved to '{out_data_path}'")


def loader(args: argparse.Namespace):
    """
    Load pickled fit results data, and optionally display plots or summary.

    WARNING: Only use this method on pickle files that are known to be 
    generated by this program; pickle is vulnerable to arbitrary code execution.
    """

    with open(args.filename, 'rb') as file:
        results = pickle.load(file)
        if args.trace:
            results = results[args.trace]

    fit, data_trc, bfunc = results.values()
    logger.info(f"Fit results loaded from {args.filename}")
    if args.verbose:
        print("\n", fit.summary())

    if args.plot:
        fig, _, _, _ = plot_graphs_together(data_trc, fit, bfunc)

        if args.trace:
            fig.suptitle(args.trace)
        fig.tight_layout()
        plt.show()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="Burst Fit",
                                     description="")

    parser.add_argument('-p', '--plot', action='store_true', 
                        help="plot fit and statistics graphs")
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help="verbose output")
    parser.add_argument('-f', '--force', action='store_true', 
                        help="enable overwritting of output files into the "
                        "same directory")
    parser.add_argument('-o', type=str, default="",
                        help="output directory path, relative to the ./output/ "
                        "directory. Only specifies a directory, not a file "
                        "name")
    parser.add_argument('--pickle', action='store_true',
                        help="pickles a copy of the fit results object(s). If "
                        "called with 'single', this pickles the fit result "
                        "object. If called with 'batch', pickles a dictionary "
                        "of fit results objects indexed by the filenames "
                        "associated with them")
    subparser = parser.add_subparsers(title="subcommands", required=True)

    # Fit the amplitudes for a single file
    single_parser = subparser.add_parser(name="single",
                                         description=single_fit.__doc__,
                                         help="fit a single trace file to "
                                         "generate amplitude fit")

    single_parser.add_argument('filepath', type=str, 
                               help="filepath to .csv to read data from")
    single_parser.add_argument('t0_value', type=float, 
                               help="time value to start fit from")
    single_parser.add_argument('n_pulses', type=int, 
                               help="number of pulses to fit")
    single_parser.add_argument('trace_type',
                               choices=[m.name for m in TraceType],
                               help="type of trace that is to be fit")
    single_parser.set_defaults(func=single_fit)

    # Fit amplitudes for a batch of files defined by a 'manifest file'
    batch_parser = subparser.add_parser(name="batch",
                                        description=batch_fit.__doc__,
                                        help="parse a batch of files, defined "
                                        "in an external manifest file")
    batch_parser.add_argument('file_manifest', type=str, 
                              help="filepath to the manifest file, which "
                              "defines which files to fit")
    batch_parser.add_argument('data_path', type=str, 
                              help="path to the folder containing the file "
                              "names specified in the manifest file")
    batch_parser.add_argument('n_pulses', type=int, 
                              help="number of pulses to fit, for each of the "
                              "files in the manifest")

    batch_parser.add_argument('-t', '--t0_value', type=float, default=NoT0Val(), 
                              help="common t0 value to start at for all files "
                              "in the manifest")
    batch_parser.add_argument('-m', '--get_t0_from_meta', action='store_true',
                              help="flag to get the t0 values from the manifest "
                              "file")
    batch_parser.set_defaults(func=batch_fit)

    # Load pickled fit results, and show the data associated with them
    results_parser = subparser.add_parser(name="load_pickle",
                                          description=loader.__doc__,
                                          help="load a previously generated "
                                          "pickle file")
    results_parser.add_argument('filename', type=str, help="file to load")
    results_parser.add_argument('-t', '--trace', type=str, default=None,
                                help="name of a trace to access if the " 
                                "pickle file has many results objects saved")

    results_parser.set_defaults(func=loader)

    # Run command
    args = parser.parse_args()

    OUT_PATH = os.path.relpath("output", start=os.getcwd())
    out_path = os.path.join(OUT_PATH, args.o)
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    args.output_path = out_path

    if args.force:
        ans = input("You have passed the `-f` flag, indicating that you want "
                    "to overwrite any previously saved data residing in the "
                    "output directory you have chosen. Are you sure that you "
                    "want to do this? [y/n]")
        match ans:
            case "y" | "Y":
                logger.warn("Output overwriting enabled, data in selected " 
                            "output directory will be overwritten.")
                args.func(args)
            case "n" | "N":
                logger.info("Fit aborted")
                sys.exit(0)
    else:
        args.func(args)
