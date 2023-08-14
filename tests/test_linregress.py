import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import os, sys, inspect
this_dir = os.path.abspath(inspect.getfile(inspect.currentframe()))
parent_dir = os.path.dirname(os.path.dirname(this_dir))
src_dir = os.path.join(parent_dir, "src")
sys.path.insert(0, src_dir)

from constants import *
from burst_function import BurstFunction
from data_trace import DataTrace
from plotter import plot_fit
from fitter import Fitter
from pulse_profiles import GaussianExp

from itertools import product


class MockBurst:

    def __init__(self, first_pulse : float, t_start : float = -1e-8, 
                 t_end : float = 2e-7, shape_params=None) -> None:
        """
        Create mock trace by defining a known analytic burst of pulses from our
        fitting function, and sample it at the scope sampling rate.
        """
        self.start_time = first_pulse
        self.mock_ampls = np.loadtxt("tests/test_data/mock_amplitudes.csv",
                                          delimiter=",", encoding="utf-8")
        SAMPLING_RATE = 4e9 # samples/second
        SAMPLING_INTERVAL = 1 / SAMPLING_RATE

        self.mock_model = BurstFunction(first_pulse, self.mock_ampls.size, 
                                        TraceType.PUMP)
        
        if not shape_params is None:
            self.mock_model.set_pulse_params(shape_params)

        self.t_start, self.t_end = (t_start, t_end)
        sampling_times = np.arange(self.t_start, self.t_end, 
                                        SAMPLING_INTERVAL)
        mock_data = self.mock_model.burst_function(sampling_times,
                                                   self.mock_ampls)
        
        self.mock_trc = DataTrace(sampling_times, mock_data)


def test_lin_regress(tshift=0, plot_results=False, **kwargs):
    
    if 'params' in kwargs.keys():
        params = kwargs['params']
    else:
        params = None

    t0 = 0
    mb = MockBurst(t0 + tshift, shape_params=params)
    bfunc = BurstFunction(t0, mb.mock_ampls.size, TraceType.PUMP)
    
    fitter = Fitter()
    fit = fitter.linear_regress_burst(mb.mock_trc, bfunc)

    pdiff = np.mean(100 * np.abs(fit.fit_ampls - mb.mock_ampls)
                    / mb.mock_ampls)

    if plot_results:
        plot_fit(mb.mock_trc, fit, bfunc)

    return pdiff, fit.r2_val


def test_t0_variation():

    time_shift_values = np.linspace(0, 0.1 * PULSE_WIDTH, 10)
    pdiffs, r2s = [], []
    for tval in time_shift_values:
        new_pdiff, new_r2 = test_lin_regress(tshift=tval, plot_results=False)
        pdiffs += [new_pdiff]
        r2s += [new_r2]
    
    fig, (ax1, ax2) = plt.subplots(2)

    ax1.plot(time_shift_values, pdiffs, color='black')
    ax2.plot(time_shift_values, r2s, color='black')

    ax1.set_xlabel("Time Shift (s)")
    ax2.set_xlabel("Time Shift (s)")

    ax1.set_ylabel("Avs. Abs. % Diff")
    ax2.set_ylabel("$R^2$ Value")

    ax1.grid(), ax2.grid()

    fig.tight_layout()
    plt.show()


def test_param_variation():

    sig0, lam0 = GaussianExp(PUMP_PARAM_PATH).parameters

    N_VALUES = 10
    n_range = np.linspace(0, 1, N_VALUES)

    percent = 0.1
    sigs = sig0 * (1 - percent * n_range)
    lams = lam0 * (1 - percent * n_range)

    sigs, lams = np.meshgrid(sigs, lams)
    pdiffs, r2s = np.empty((N_VALUES, N_VALUES)), np.empty((N_VALUES, N_VALUES))
    for i, j in product(range(N_VALUES), range(N_VALUES)):
        shape_params = (sigs[i,j], lams[i,j])
        pdiffs[i,j], r2s[i,j] = test_lin_regress(params=shape_params)
        
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, 
                                   subplot_kw={'projection': '3d'})

    surf1 = ax1.plot_surface(sigs, lams, pdiffs, cmap=cm.plasma,
                             lw=0, antialiased=False)
    surf2 = ax2.plot_surface(sigs, lams, r2s, cmap=cm.viridis,
                             lw=0, antialiased=False)

    """
    The offset text is broken for some reason, so I make it invisible and
    set it manually.
    """
    for ax in [ax1, ax2]:
        ax.xaxis.get_offset_text().set_visible(False)
        ax.yaxis.get_offset_text().set_visible(False)
        ax.zaxis.get_offset_text().set_visible(False)

    def get_exp_text(arr):
        exponent = int('{:.2e}'.format(np.min(arr)).split('e')[1]) 
        return '$\\times\\mathdefault{10^{%d}}\\mathdefault{}$' % exponent

    fig.colorbar(surf1, shrink=0.5, aspect=10)
    fig.colorbar(surf2, shrink=0.5, aspect=10)

    ax1.set_xlabel(f"$\sigma$ ({get_exp_text(sigs)}$s^{{-1}}$)")
    ax1.set_ylabel(f"$\lambda$ ({get_exp_text(lams)}$s^{{-1}}$)")
    ax1.set_zlabel(f"Avg. Abs. % Difference")

    ax2.set_xlabel(f"$\sigma$ ({get_exp_text(sigs)}$s^{{-1}}$)")
    ax2.set_ylabel(f"$\lambda$ ({get_exp_text(lams)}$s^{{-1}}$)")
    ax2.set_zlabel(f"$R^2$ value")

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":

    # pdiff_val, r2 = test_lin_regress(plot_results=True)
    # print(f"Avg. Abs. % Diff = {pdiff_val:.2e}, R^2 = {r2:.2e}")
    
    # test_t0_variation()
    test_param_variation()
