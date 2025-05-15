# Zuyang Liu (2023)
from datetime import datetime
import tidy3d as td
from tidy3d.plugins.mode import ModeSolver
from tidy3d.plugins.mode.web import run as run_mode_solver
import gdsfactory as gf

from helper_functions.generic.misc import write_to_json
from helper_functions.tidy3d.materials import load_pole_material
from helper_functions.tidy3d.initiate_fdtd import fdtd_from_gds

# from gds_library import custom_pdk

def get_modes_tidy3d_server(parameters):
    r""" calculate modes on server, cost credits

    Args:
        parameters (dict): input parameters
    
    Return:
        results (dict): with neff, ng, TE polarization fraction
    """
    
    ##### default settings #####
    p = {}
    um = 1
    
    # waveguide geometry
    p['WG_type'] = 'ridge' # 'ridge' or 'strip'
    p['T_WG'] = 0.25
    p['T_BOX'] = 3.0
    p['T_TOX'] = 3.0
    
    # strip wg
    p['wg_width'] = 0.8
    
    # ridge wg
    p['ridge_width'] = 0.12
    p['base_width'] = 3.0
    p['T_WG_partial'] = 0.1
    
    # simulation settings
    p['sim_temperature'] = 300
    p['solver_size_y'] = 5.0
    p['solver_size_z'] = 5.0
    p['wavelength'] = 0.85
    
    p['resolution'] = 6
    
    p['mode_num'] = 5
    p['material_file'] = r'materials_library\VisPDK_materials_mid'
    p['mat_WG_name'] = 'SiN'
    p['mat_OX_name'] = 'SiO2'
    
    p['file_name'] = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S'))
    
    # update default setting with input
    p.update(parameters)
    
    # convert settings to local variables
    for key, value in p.items():
        globals()[key] = value
    
    # save parameters to a json file
    write_to_json(dict_name=p, json_name=file_name+'.json')
    
    # import material to tidy3d
    mat_WG = load_pole_material(filename=material_file+'_SiN_pole.json')
    mat_OX = load_pole_material(filename=material_file+'_SiO2_pole.json')
    
    # add bottom and top cladding
    BOX = td.Structure(geometry = td.Box(center=(0.0, 
                                                 0.0,
                                                 -0.5*T_BOX*um),
                                         size=(10.0*um,
                                               solver_size_y*um+2*3.0*um,
                                               T_BOX*um),),
                       medium = mat_OX,
                       name = 'BOX',)
    
    TOX = td.Structure(geometry = td.Box(center=(0.0, 
                                                 0.0,
                                                 0.5*T_TOX*um),
                                         size=(10.0*um,
                                               solver_size_y*um+2*3.0*um,
                                               T_TOX*um),),
                       medium = mat_OX,
                       name = 'TOX',)
    
    ##### add waveguide #####
    if WG_type == 'ridge':
        partial = td.Structure(geometry = td.Box(center=(0.0, 
                                                         0.0,
                                                         0.5*T_WG_partial*um),
                                                 size=(10.0*um,
                                                       base_width*um,
                                                       T_WG_partial*um),),
                               medium = mat_WG,
                               name = 'base',)
        
        full = td.Structure(geometry = td.Box(center=(0.0, 
                                                      0.0,
                                                      0.5*T_WG*um),
                                              size=(10.0*um,
                                                    ridge_width*um,
                                                    T_WG*um),),
                            medium = mat_WG,
                            name = 'ridge',)
        
        structures = [TOX, BOX, partial, full]
    
    if WG_type == 'strip':
        wg = td.Structure(geometry = td.Box(center=(0.0, 
                                                 0.0,
                                                 0.5*T_WG*um),
                                            size=(10.0*um,
                                                  WG_width*um,
                                                  T_WG*um),),
                          medium = mat_WG,
                          name = 'strip',)
        structures = [TOX, BOX, wg]
        
    ##### add mode source #####
    freq0 = td.C_0/wavelength
    
    src_plane = td.Box(center=[0.0, 0.0, 0.0],
                       size=[0.0, solver_size_y*um, solver_size_z*um])
    
    src_time = td.GaussianPulse(freq0=freq0, fwidth=freq0/10)
    
    mode_spec = td.ModeSpec(num_modes = mode_num, 
                            target_neff = 1.9)
    
    mode_source = td.ModeSource(
        center = src_plane.center,
        size = src_plane.size,
        source_time = src_time,
        direction = "+",
        mode_spec = mode_spec,
        mode_index = 0,
        num_freqs = 1,)
    
    run_time = 1e-12
    grid_spec=td.GridSpec.auto(min_steps_per_wvl=resolution)
    
    sim = td.Simulation(
        size = (1.0*um, solver_size_y, solver_size_z),
        grid_spec=grid_spec,
        structures = structures,
        sources = [mode_source],
        run_time = run_time,
        boundary_spec = td.BoundarySpec.all_sides(boundary=td.PML()),
    )
    
    
    mode_solver = ModeSolver(simulation = sim,
                             plane = src_plane,
                             mode_spec = mode_spec,
                             freqs = freq0,
                             )
    
    mode_data = run_mode_solver(mode_solver, task_name='mode_solver', results_file=file_name+'_results.hdf5')
    
    results = {}
    results['neff'] = mode_data.n_eff.values
    results['TE_frac'] = mode_data.pol_fraction.te.values
    results['group_index'] = mode_data.n_group
    results['eff_area'] = mode_data.mode_area.data
    
    # save results to json file
    write_to_json(dict_name=results, json_name=file_name+'_results.json')
    
    return results

def simulate_predefined_gds(parameters):
    # default settings
    p = dict(
        # generic settings
        wavelength = 0.85,
        wav_span = 0.05,
        # wav_start = 0.78,
        # wav_stop = 0.94,
        resolution = 6,
        temperature = 300,
        predefined_gds = 'mmi_1x2_450_VISPIC2',
        gds_file = 'mmi_1x2_450_VISPIC2',
        material_type = "universal",
        guiding_material = 'SiN',
        file_name = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S')),
        task_name = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S')),
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

    device = gf.import_gds(predefined_gds+'.gds', read_metadata=True)
    device.write_gds(gds_file+'.gds', with_metadata=True)

    results = fdtd_from_gds(parameters=p) 