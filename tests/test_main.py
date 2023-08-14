# Add the source dir to the python path
import os, sys, inspect
this_dir = os.path.abspath(inspect.getfile(inspect.currentframe()))
parent_dir = os.path.dirname(os.path.dirname(this_dir))
sys.path.insert(0, os.path.join(parent_dir, "src"))

from main import fit_trace
from constants import *

if __name__ == "__main__":
    FPATH = "..\..\Data\\14 June 2023 reflectivity results\\14 June 2023 Reflectivity Measurements\C1trc00000.csv"
    fit_trace(FPATH, 9.4e-10, 50, TraceType.PUMP, True, True)['fit_results'] 
