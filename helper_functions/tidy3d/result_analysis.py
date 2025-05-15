# Zuyang Liu (2023)
import tidy3d as td
import numpy as np

def read_mode_monitor_from_file(
    fname:str|None=None,
    monitor:str|None=None,
):
    sim_data = td.SimulationData.from_file(fname)
    mode_data = sim_data[monitor]
    coeffs = np.abs(mode_data.amps.sel(direction="+"))**2
    lambdas = td.C_0/mode_data.amps.f
    return lambdas, coeffs
