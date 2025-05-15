# Zuyang Liu (2023)
from helper_functions.generic.materials import read_nk
import numpy as np

c = 299792458 # speed of light, m/s

def add_material_sampled3d_old(project, file, material, display_name, color: list = [0, 0, 1, 0]):
    
    r""" add a new material to database
    
    Args:
        project: simulation project.
        file: json file containing n, k vs. wvls.
        material: name in json file, e.g. SiN, SiO2, Si.
        display_name: material name in database.
        color: material color.
    
    Returns nothing.
    """
    
    temp = read_nk(filename=file, material=material)
    
    new_mat = project.addmaterial('Sampled 3D data')
    f = c/np.array(temp['wvls'])
    eps = np.array(temp['n'])**2
    
    data = np.column_stack((f, eps))
    
    project.setmaterial(new_mat, 'Name', display_name)
    project.setmaterial(display_name, 'sampled data', data)
    project.setmaterial(display_name, 'color', np.array(color))
    project.setmaterial(display_name, 'tolerance', 0.001)

def add_material_sampled3d(
        project, 
        file, 
        display_name, 
        color: list = [0, 0, 1, 0]
        ):

    temp = read_nk(filename=file, material='', wvl_key='wavelength(m)', n_prefix='Re(index)', k_prefix='Im(index)')

    new_mat = project.addmaterial('Sampled 3D data')
    f = c/np.array(temp['wvls'])
    eps = np.array(temp['n'])**2
    
    data = np.column_stack((f, eps))
    
    project.setmaterial(new_mat, 'Name', display_name)
    project.setmaterial(display_name, 'sampled data', data)
    project.setmaterial(display_name, 'color', np.array(color))
    project.setmaterial(display_name, 'tolerance', 0.001)