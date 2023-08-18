import os, sys, inspect
this_dir = os.path.abspath(inspect.getfile(inspect.currentframe()))
parent_dir = os.path.dirname(os.path.dirname(this_dir))
sys.path.insert(0, os.path.join(parent_dir, "src"))

from main_funcs import fit_trace
from constants import *


def test_example():
    pass

if __name__ == "__main__":

    test_example()
