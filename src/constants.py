# ---------------------------------------------------
# Based on Jingsen's measurements as of May 31, 2023:
# ---------------------------------------------------

# The length of one group of pulses.
PERIOD = 18.885e-9#s

# Constants defining the time between pulses in each group (see docs).
DELTA_1 = 4.98375e-9#s
DELTA_2 = 4.73250e-9#s
DELTA_3 = 4.40375e-9#s
DELTA_4 = 4.76500e-9#s

TAU_1 = DELTA_1
TAU_2 = DELTA_1 + DELTA_2
TAU_3 = DELTA_1 + DELTA_2 + DELTA_3 

# ----------------
# Burst Parameters
# ----------------

# Path to file containing pre-determined parameters for pulse shape.
# TODO: Change this location
PARAM_PATH_LOC = "/pulse_params/"
 
PARAM_PATH = PARAM_PATH_LOC + "Gaussian parameters for DET10A pulse - Gaussian and Exponential2.txt"
PUMP_PARAM_PATH = PARAM_PATH_LOC + "Parameters for DET10A - PUMP.txt"
REFLECTED_PARAM_PATH = PARAM_PATH_LOC + "Parameters for DET10A - REFLECTED.txt"
# TODO: Calibrate parameters for transmitted traces.
TRANSMIT_PARAM_PATH = PARAM_PATH_LOC + "Parameters for DET10A - TRANSMITTED.txt"

# From my code: lambda = 501_474_709.030_812_3

# -------
# Timing:
# -------

# The approximate width of a pulse ON THE SCOPE OUTPUT
# Actual laser pulses are much shorter (300fs), but the fast pulse gets 
# streached out by the limited bandwidth of the scope, causing it to appear 
# much broader.
PULSE_WIDTH = 4.72e-9#s

# The delay between the pump signal and the reflected signal before reaching the 
# oscilloscope (due to cable length differences).
REFLECT_DELAY = 1.819e-9#s

# The delay between the pump signal and the transmitted signal (due to cable 
# length differences and inter-oscilloscope external triggering).
TRANSMIT_DELAY = -2.88e-9#s

# ---------------
# Burst Type Data
# ---------------

from enum import IntEnum

class TraceType(IntEnum):
    PUMP = 0
    REFLECTED = 1
    TRANSMITTED = 2

PULSE_PARAM_IDX = {
    TraceType.PUMP: PUMP_PARAM_PATH,
    TraceType.REFLECTED: REFLECTED_PARAM_PATH,
    TraceType.TRANSMITTED: TRANSMIT_PARAM_PATH
}

TRACE_DELAY_IDX = {
    TraceType.PUMP: 0,
    TraceType.REFLECTED: 0,
    TraceType.TRANSMITTED: 0
}
