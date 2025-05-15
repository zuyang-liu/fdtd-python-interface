# Zuyang Liu (2023)
from datetime import datetime
import os
import sys
import numpy as np
import gdsfactory as gf

from helper_functions.generic.misc import write_to_json
from helper_functions.lumerical.materials import add_material_sampled3d
from helper_functions.lumerical.initiate_fdtd import fdtd_from_gds
from helper_functions.lumerical.initiate_eme import eme_from_gds


def get_modes_lumerical(parameters):
    r""" calculate mode in MODE solutions

    Args:
        parameters (dict): input parameters
    
    Return:
        results (dict)
    """
    # default settings
    um = 1e-6
    
    p = dict(
        WG_type = 'ridge', # 'ridge' or 'strip'
        T_WG = 0.25,
        T_BOX = 3.0,
        T_TOX = 3.0,
        # strip waveguide
        wg_width = 0.8,
        # ridge waveguide
        ridge_width = 0.12,
        base_width = 3.0,
        T_WG_partial = 0.1,
        # generic simulation parameters
        sim_temperature = 300,
        solver_size_x = 5.0,
        solver_size_y = 5.0,
        wavelength = 0.85,
        resolution = 6,
        mode_num = 5,
        material_type = "universal",
        guiding_material = 'SiN', # Si or SiN
        lumapi_path = r"C:\Program Files\Lumerical\v232\api\python",
        mat_WG_name = 'user guiding',
        mat_OX_name = 'user oxide',
        file_name = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S')),
        save_Efields = 0,
    )
    
    # update default setting with input
    p.update(parameters)
    
    # convert settings to local variables
    for key, value in p.items():
        globals()[key] = value
    
    # save parameters to a json file
    write_to_json(dict_name=p, json_name=file_name+'.json')
    
    ##### start Lumerical MODE solutions #####
    sys.path.append(lumapi_path)
    sys.path.append(os.path.dirname(__file__))
    import lumapi
    project = lumapi.MODE()
    project.clear()
    project.deleteall()
    project.switchtolayout()
    
    # import material to database
    mat_wg = 'user SiN'
    if guiding_material == 'SiN':
        add_material_sampled3d(project=project, 
                            file=r'materials_library\\'+material_type+'_SiN', 
                            display_name=mat_wg, 
                            color=[0, 0, 1, 1])
    if guiding_material == 'Si':
        add_material_sampled3d(project=project, 
                            file=r'materials_library\\'+material_type+'_Si', 
                            display_name=mat_wg, 
                            color=[1, 0, 0, 1])

    mat_ox = 'user SiO2' # as background material
    add_material_sampled3d(project=project, 
                           file=r'materials_library\\'+material_type+'_SiO2', 
                           display_name=mat_ox,
                           color=[0, 1, 0, 0.3])
    
    ##### add buried oxide #####
    project.addrect()
    project.set('x', 0)
    project.set('x span', (solver_size_x+3.0)*um)
    project.set('y max', 0)
    project.set('y min', -T_BOX*um)
    project.set('z', 0)
    project.set('z span', 1*um)
    project.set('name', 'Buried oxide')
    project.set('material', mat_ox)
    
    ##### add strip waveguide #####
    if WG_type == 'strip':
        project.addrect()
        project.set('name', 'Strip WG')
        project.set('material', mat_wg)
        project.set('x', 0)
        project.set('x span', wg_width*um)
        project.set('y min', 0)
        project.set('y max', T_WG*um)
        project.set('z', 0)
        project.set('z span', 1*um)
    
    ##### add ridge waveguide #####
    if WG_type == 'ridge':
        project.addrect()
        project.set('name', 'base')
        project.set('material', mat_wg)
        project.set('x', 0)
        project.set('x span', base_width*um)
        project.set('y min', 0)
        project.set('y max', T_WG_partial*um)
        project.set('z', 0)
        project.set('z span', 1*um)

        project.addrect()
        project.set('name', 'ridge')
        project.set('material', mat_wg)
        project.set('x', 0)
        project.set('x span', ridge_width*um)
        project.set('y min', 0)
        project.set('y max', T_WG*um)
        project.set('z', 0)
        project.set('z span', 1*um)
    
    ##### add FDE solver #####
    project.addfde()
    project.set('x', 0)
    project.set('x span', solver_size_x*um)
    project.set('y', 0)
    project.set('y span', solver_size_y*um)
    project.set('z', 0)
    project.set('wavelength', wavelength*um)
    project.set('background material', mat_ox)
    project.set('simulation temperature', sim_temperature)
    mode_num = p['mode_num'] # if commented, will return an error: local variable 'mode_num' referenced before assignment. I don't know why.
    project.set('number of trial modes', mode_num)

    project.set('x min bc', 'PML')
    project.set('x max bc', 'PML')
    project.set('y min bc', 'PML')
    project.set('y max bc', 'PML')
    
    mesh_x = wavelength/resolution/2.0
    mesh_y = mesh_x

    project.set('define x mesh by', 'maximum mesh step')
    project.set('dx', mesh_x*um)
    project.set('define y mesh by', 'maximum mesh step')
    project.set('dy', mesh_y*um)
    
    simRun = 1
    if simRun:
        start_time = datetime.now()
        print('Simulation starts at '+str(start_time.strftime('%H:%M:%S')))  
        project.findmodes()
        end_time = datetime.now()
        print('Simulation finishes at '+str(end_time.strftime('%H:%M:%S')))
        dur = end_time - start_time
        print('Duration '+str(dur.seconds)+' seconds')

    project.save(file_name+'.lms')
    
    ##### get simulation results #####
    results = {}
    results['mesh_x'] = mesh_x
    results['mesh_y'] = mesh_y
    
    # return number of modes found
    N = project.nummodes()
    if N < mode_num:
        mode_num = N
    
    results['mode_num'] = mode_num
        
    # record the effective index and TE polarization fraction
    
    results['neff'] = np.zeros(int(mode_num))
    results['TEfraction'] = np.zeros(int(mode_num))
    results['ngroup'] = np.zeros(int(mode_num))
    results['loss'] = np.zeros(int(mode_num))
    results['aeff'] = np.zeros(int(mode_num))
    
    E_fields = {}
    E_fields['x'] = project.getresult('mode1', 'x')/um
    E_fields['y'] = project.getresult('mode1', 'y')/um
    
    
    for ii in range(int(mode_num)):
        
        neff_complex = project.getresult('mode'+str(ii+1),'neff')
        results['neff'][ii] = abs(neff_complex)
        results['TEfraction'][ii] = project.getresult('mode'+str(ii+1),'TE polarization fraction')
        results['ngroup'][ii] = abs(project.getresult('mode'+str(ii+1),'ng'))
        results['loss'][ii] = project.getresult('mode'+str(ii+1),'loss')
        results['aeff'][ii] = project.getresult('mode'+str(ii+1),'mode effective area')
        
        E_fields['E2_'+str(ii)] = project.getelectric('mode'+str(ii+1)) # shape (y, x, 1, 1) from lumerical
    
    # save results to json file
    write_to_json(dict_name=results, json_name=file_name+'_results.json')
    if save_Efields:
        write_to_json(dict_name=E_fields, json_name=file_name+'_Efields.json')
    

    return results


def simulate_predefined_gds(parameters):
    r""" initialize 3D FDTD of a given GDS

    Args:
        parameters (dict): simulation parameters
    """
    # default settings
    p = dict(
        # generic settings
        wavelength = 0.85,
        wav_span = 0.02,
        wav_step = 0.01,
        # wav_start = 0.78,
        # wav_stop = 0.94,
        resolution = 6,
        temperature = 300,
        predefined_gds = 'mmi_1x2_450_VISPIC2',
        gds_file = 'mmi_1x2_450_VISPIC2', # path to GDS file
        material_type = "universal",
        guiding_material = 'SiN',
        lumapi_path = r"C:\Program Files\Lumerical\v251\api\python",
        file_name = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S')),
        mode_num = 5,
        mode_idx = 1,
        flag_extend = 1,
        extension = 10,
        flag_run_simulation = 0,
        flag_boolean = 0,
        solver_z_min = -1,
        solver_z_max = 1,
        no_cladding = False,
    )

    # update default setting with input
    p.update(parameters)
    
    p['gds_file'] = p['file_name']

    # convert settings to local variables
    for key, value in p.items():
        globals()[key] = value
        
    # save parameters to a json file
    write_to_json(dict_name=p, json_name=file_name+'.json')

    # copy the GDS to project result folder
    device = gf.import_gds(predefined_gds+'.gds', read_metadata=True)
    device.write_gds(gds_file+'.gds', with_metadata=True)

    results = fdtd_from_gds(parameters=p) 

    return results