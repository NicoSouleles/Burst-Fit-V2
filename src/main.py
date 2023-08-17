import argparse

import os
import sys
import logging

from main_funcs import CommandHandler, NoT0Val
from constants import *
from logger import add_handlers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
add_handlers(logger)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="Burst Fit",
                                     description="")
    command_handler = CommandHandler()

    parser.add_argument('-p', '--plot', action='store_true', 
                        help="plot fit and statistics graphs")
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help="verbose output")
    parser.add_argument('-f', '--force', action='store_true', 
                        help="enable overwritting of output files into the "
                        "same directory")
    parser.add_argument('-o', type=str, default="",
                        help="relative output directory path, defaults to "
                        "./output/")
    parser.add_argument('--pickle', action='store_true',
                        help="pickles a copy of the fit results object(s). If "
                        "called with 'single', this pickles the fit result "
                        "object. If called with 'batch', pickles a dictionary "
                        "of fit results objects indexed by the filenames "
                        "associated with them")
    subparser = parser.add_subparsers(title="subcommands", required=True)

    # Fit the amplitudes for a single file
    single_parser = subparser.add_parser(name="single",
                                         description=command_handler.single_fit.__doc__,
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
    single_parser.set_defaults(func=command_handler.single_fit)

    # Fit amplitudes for a batch of files defined by a 'manifest file'
    batch_parser = subparser.add_parser(name="batch",
                                        description=command_handler.batch_fit.__doc__,
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
    batch_parser.set_defaults(func=command_handler.batch_fit)

    # Load pickled fit results, and show the data associated with them
    results_parser = subparser.add_parser(name="load_pickle",
                                          description=command_handler.loader.__doc__,
                                          help="load a previously generated "
                                          "pickle file")
    results_parser.add_argument('filename', type=str, help="file to load")
    results_parser.add_argument('-t', '--trace', type=str, default=None,
                                help="name of a trace to access if the " 
                                "pickle file has many results objects saved")

    results_parser.set_defaults(func=command_handler.loader)

    # Run command
    args = parser.parse_args()
    out_path = args.o if args.o else 'output'
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    command_handler.create_file_handler(out_path, args.force)

    if args.force:
        ans = input("You have passed the `-f` flag, indicating that you want "
                    "to overwrite any previously saved data residing in the "
                    "output directory you have chosen. Are you sure that you "
                    "want to do this? [y/n]")
        if ans == "y":
            logger.warning("Output overwriting enabled, data in selected " 
                        "output directory will be overwritten.")
            args.func(args)
        else:
            print("Fit aborted")
            sys.exit(0)
    else:
        args.func(args)
