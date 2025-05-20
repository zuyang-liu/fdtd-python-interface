from datetime import datetime
import os
import gdsfactory as gf
import json

from helper_functions.generic.misc import write_to_json
from helper_functions.lumerical.initiate_fdtd import fdtd_from_gds

def simulate_predefined_gds(parameters):
    r""" initialize 3D FDTD of a given GDS

    Args:
        parameters (dict): simulation parameters
    """
    # default settings
    p = dict(

        wavelength = 0.85,  # center wavelength (um)
        wav_span = 0.02,    # wavelength span (um)
        wav_step = 0.01,    # wavelength step (um)

        resolution = 6,     # spatial resolution, number of cells per wavelength
        
        temperature = 300,  # simulation temperature (K)
        
        predefined_gds = 'mmi_1x2_450_VISPIC2.gds', # default GDS file path

        material_type = "universal",    # material name
        guiding_material = 'SiN',       # core material
        
        lumapi_path = r"C:\Program Files\Lumerical\v251\api\python",        # Lumerical API path
        file_name = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S')),   # output base name
        
        mode_num = 5,   # number of modes to compute
        mode_idx = 1,   # index of injected mode
        
        flag_extend = 1,    # extend waveguide?
        extension = 10,     # extension length (um)
        
        flag_run_simulation = 0,    # run simulation?
        flag_boolean = 0,           # apply boolean operation?
        
        solver_z_min = -1,          # simulation region z min (um)
        solver_z_max = 1,           # simulation region z max (um)
        
        change_cladding = False,    # True: replace top cladding with Si3N4
    )

    # load user settings from config.json
    f = open("config.json")
    config = json.load(f)
    p.update(config)

    # update default setting with input
    p.update(parameters)
    
    # define the output GDS file name
    p['gds_file'] = p['file_name']+'.gds'

    # convert parameters to local variables
    for key, value in p.items():
        globals()[key] = value
        
    # save parameters to a JSON file
    write_to_json(dict_name=p, json_name=file_name+'.json')

    # copy the predefined GDS to the output location
    device = gf.import_gds(predefined_gds, read_metadata=True)
    device.write_gds(gds_file, with_metadata=True)

    # check if the simulation file already exists
    if os.path.exists(file_name+'_FDTD.fsp') and flag_run_simulation:
        print('\033[1;91mAttention: simulation file already exists.\033[0m')
        while True:
            response = input("\033[1;91mDo you want to continue? (y/n):\033[0m").strip().lower()
            if response == 'y':
                results = fdtd_from_gds(parameters=p)
                return results
            elif response == 'n':
                print('\033[1;91mStopping...\033[0m')
                return
            else:
                print("\033[1;91mPlease enter 'y' or 'n'.\033[0m")
    else:
        results = fdtd_from_gds(parameters=p)
        return results

     

    