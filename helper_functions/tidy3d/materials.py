import os
import sys
import numpy as np
import tidy3d as td
from tidy3d.plugins.dispersion import FastDispersionFitter, AdvancedFastFitterParam
import matplotlib.pyplot as plt

from tidy3d.plugins.dispersion import AdvancedFitterParam
from tidy3d.plugins.dispersion.web import run as run_fitter

def fit_pole_residue_material(filename,
                              output_file,
                              n_name,
                              k_name,
                              material_name,
                              wav_range: tuple = (0.4, 2.0),
                              web_serive = False):
    
    r""" perform dispersion fitter on n, k data.
    save fitting result to a json file.
    """
    
    # read n, k data from file
    mat = read_from_json(filename)
    wvl_um = np.array(mat['wavelength(m)'])*1e6
    n_data = np.array(mat[n_name])
    k_data = np.array(mat[k_name])
    
    # pole residue fitting
    fitter = FastDispersionFitter(wvl_um=wvl_um,
                                  n_data=n_data,
                                  k_data=k_data,
                                  wvl_range=wav_range,)
    
    if web_serive:
        print('start web service fitting')
        medium, rms_error = run_fitter(
            fitter,
            num_poles=6, tolerance_rms=1e-5, num_tries=50, 
            advanced_param = AdvancedFitterParam(nlopt_maxeval=5000),
        )
    else:
        advanced_param = AdvancedFastFitterParam(weights=(1,1))
        print('start local fitting')
        medium, rms_error = fitter.fit(max_num_poles=6, 
                                       advanced_param=advanced_param, 
                                       tolerance_rms=1e-5)

    print("rms error "+str(rms_error))    

    fitter.plot(medium)
    # plt.xlim(0.8, 1.1)
    # plt.ylim(1.879, 1.888)
    plt.xlabel('wavelength (um)')
    plt.show()
    
    medium.to_file(output_file)
    
def load_pole_material(filename):
    r""" load pole residue data to tidy3d as a new medium
    """
    medium = td.PoleResidue.from_file(filename+'.json')
    return medium

if __name__ == "__main__":
    
    current_directory = os.getcwd()
    sys.path.append(current_directory)
    
    from helper_functions.generic.misc import read_from_json
    
    filename = r'materials_library\universal_Si.json'
    n_name = 'Re(index)'
    k_name = 'Im(index)'
    material_name = 'Si'
    output_file = r'materials_library\universal_Si_pole.json'
    
    fit_pole_residue_material(
        filename=filename, 
        n_name=n_name, k_name=k_name, 
        material_name=material_name, 
        output_file=output_file,
        wav_range=(1.2, 2.0),
        web_serive=False
        )