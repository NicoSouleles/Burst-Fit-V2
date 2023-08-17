import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.graphics.gofplots import qqplot

from data_trace import DataTrace
from burst_function import BurstFunction
 

def plot_stats_graphs(results: sm.regression.linear_model.RegressionResults,
                      fig=None, ax1=None, ax2=None, plot_res_lbf=True):
    """
    Plots a "Residuals vs Fitted" plot, and a normal Q-Q plot of the residuals.
    """
    
    if not (fig and ax1 and ax2):
        fig, (ax1, ax2) = plt.subplots(1, 2)

    ax1.plot(results.fittedvalues, results.resid, lw=0, marker='.', 
             label='Residuals')

    if plot_res_lbf:
        line_best_fit = sm.OLS(results.fittedvalues, results.resid).fit()
        ax1.plot(results.fittedvalues, line_best_fit.fittedvalues, color='red',
                 label="Line of best fit")
    ax1.legend()

    ax1.set_xlabel("Fitted Values")
    ax1.set_ylabel("Residual Values")
    ax1.set_title("Residuals vs Fitted")

    ax1.grid()
    
    plt_kwargs = {'lw': 0, 'marker': '.'}
    qqplot(results.resid,
           xlabel="Theoretical Quartiles",
           ylabel="Quartiles of Residuals",
           line='q',
           ax=ax2,
           **plt_kwargs)
    
    dots, qline = ax2.get_lines()
    dots.set_label("Residual quartiles")
    qline.set_label("Line through quartiles")
    ax2.legend()

    ax2.set_title("Normal Q-Q Plot")
    ax2.grid()
    return fig, ax1, ax2


def plot_burst_model_trace(ax, times, fit_ampls, bf, **fit_kwargs):

    n_points = 10_000
    t_start, t_end = np.min(times), np.max(times)
    plot_times = np.linspace(t_start, t_end, n_points)
    func_vals = bf.burst_function(plot_times, fit_ampls)
    ax.plot(plot_times, func_vals, **fit_kwargs)


def plot_fit(data_trc: DataTrace, fit_ampls: np.ndarray, r2_val: float, 
             bf: BurstFunction, data_kwargs: dict = {}, 
             fit_kwargs: dict = {}, fig=None, ax=None) -> None:

    if not (fig and ax):
        fig, ax = plt.subplots()

    times = data_trc.get_time_values()
    ax.plot(times, data_trc.get_data_values(),
            color='black', lw=0, marker='.', label='Data Trace', 
            **data_kwargs)

    plot_burst_model_trace(ax, times, fit_ampls, bf, 
                           color='blue', label='Burst Fit', **fit_kwargs)

    ax.text(0.01, 0.99, f"$R^2={r2_val:.2f}$", fontsize=12,
            transform=ax.transAxes, ha='left', va='top')

    ax.set_xlabel(f"Time ({data_trc.time_units})")
    ax.set_ylabel(f"Voltage ({data_trc.data_units})")

    ax.grid()
    ax.legend()
    return fig, ax


def plot_graphs_together(data_trc, fit, bfunc, plot_res_lbf=True):
    
    fig = plt.figure(figsize=(10, 6))
    gs = fig.add_gridspec(2, 2)

    ax = fig.add_subplot(gs[0, :])
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[1, 1])

    fig, ax1, ax2 = plot_stats_graphs(fit, fig=fig, ax1=ax1, ax2=ax2, 
                                      plot_res_lbf=plot_res_lbf)
    fig, ax = plot_fit(data_trc, fit.params, fit.rsquared, bfunc, 
                           fig=fig, ax=ax)

    return fig, ax1, ax2, ax
