from datetime import datetime
import sys
import os
import numpy as np
import gdsfactory as gf
import re

from helper_functions.generic.misc import write_to_json
from helper_functions.lumerical.materials import add_material_sampled3d
from helper_functions.lumerical.gds_handling import import_gds_to_lumerical
from helper_functions.generic.gds_handling import extend_from_ports

def fdtd_from_gds(parameters):
    r""" run 3D FDTD simulation of a device defined in a GDS.
    Uses layer stack information from the PDK.

    Args:
        parameters (dict): simulation parameters

    Returns:
        results (dict): only if flag_run_simulation
    """
    
    # unit conversion
    um = 1e-6
    
    # default parameters
    p = dict(
        wavelength = 0.85,
        wav_span = 0.04,
        wav_step = 0.01,
        
        resolution = 6,
        
        temperature = 300,
        
        gds_file = 'mmi_1x2_450_VISPIC2.gds',
        material_type = "universal",
        guiding_material = 'SiN',
        
        lumapi_path = r"C:\Program Files\Lumerical\v232\api\python",
        file_name = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S')),
        
        mode_num = 5,
        mode_idx = 1,
        
        flag_extend = 1,
        extension = 10,
        
        flag_run_simulation = 0,
        
        solver_z_min = -0.5,
        solver_z_max = 0.7,
        
        flag_boolean = 0,
        
        change_cladding = False,
    )
    
    # update default setting with input
    p.update(parameters)
    
    # convert settings to local variables
    for key, value in p.items():
        globals()[key] = value             
    
    # save parameters to a JSON file
    write_to_json(dict_name=p, json_name=file_name+'_fdtd.json')

    
    # start lumerical FDTD
    sys.path.append(lumapi_path)
    sys.path.append(os.path.dirname(__file__))
    import lumapi
    project = lumapi.FDTD()
    project.clear()
    project.deleteall()
    project.switchtolayout()
    
    # import material to database
    mat_wg = 'user guiding'
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
    
    # import and optionally extend GDS
    if flag_extend:
        device = gf.import_gds(gds_file, read_metadata=True)
        device, ports = extend_from_ports(device, offset=extension)
        device.write_gds(file_name+'_extended.gds', with_metadata=True)
        import_gds_to_lumerical(project=project, gds_file=file_name+'_extended.gds', material=mat_wg, flag_boolean=flag_boolean)
        
    else:
        device = gf.import_gds(gds_file, read_metadata=True)
        ports = device.ports
        device.write_gds(file_name+'.gds', with_metadata=True)
        import_gds_to_lumerical(project=project, gds_file=file_name+'.gds', material=mat_wg, flag_boolean=flag_boolean)
    
    
    # add FDTD solver
    project.addfdtd()
    project.set('simulation temperature', temperature)
    project.set('dimension', '3D')
    
    # calculate bounds from ports
    x_min = np.inf
    x_max = -1*np.inf
    y_min = np.inf
    y_max = -1*np.inf
    
    for port_name in ports:
        if ports[port_name].center[0] < x_min:
            x_min = ports[port_name].center[0]
        if ports[port_name].center[0] > x_max:
            x_max = ports[port_name].center[0]
        if ports[port_name].center[1] - ports[port_name].width < y_min:
            y_min = ports[port_name].center[1] - ports[port_name].width
        if ports[port_name].center[1] + ports[port_name].width > y_max:
            y_max = ports[port_name].center[1] + ports[port_name].width
    
    if x_min == x_max: # like a 180-degree bend, U-shape
        x_min = ports['o1'].center[0]
        x_max = device.xmax
        y_min = device.ymin
        y_max = device.ymax
    
    solver_x_min = x_min - 1.0
    solver_x_max = x_max + 1.0
    solver_y_min = y_min - 1.0
    solver_y_max = y_max + 1.0
    
    project.set('x min', solver_x_min*um)
    project.set('x max', solver_x_max*um)
    project.set('y min', solver_y_min*um)
    project.set('y max', solver_y_max*um)
    project.set('z min', solver_z_min*um)
    project.set('z max', solver_z_max*um)
    
    project.set('background material', mat_ox)
    
    project.set('mesh type', 'custom non-uniform')
    project.set('mesh cells per wavelength', resolution)
    
    if guiding_material == 'Si':
        sim_time = 30.0*((solver_x_max-solver_x_min)*um*2.0/299792458) # c=299792458 m/s, speed of light
    if guiding_material == 'SiN':
        sim_time = 30.0*((solver_x_max-solver_x_min)*um*2.0/299792458) # c=299792458 m/s, speed of light
    project.set("simulation time", sim_time)
    
    # set boundary conditions
    for axis in ['x', 'y', 'z']:
        project.set(f'{axis} min bc', 'PML')
        project.set(f'{axis} max bc', 'PML')

    # optional: stabilized PML
    pmlDiv = 0
    if pmlDiv:
        project.set('pml profile', 4) # set PML profile to 'stabilized' to prevent diverging simulation
        project.set('pml layers',64)
        project.set('pml kappa', 5)
        project.set('pml alpha', 0.9)
    
    # optionally change top cladding to Si3N4
    if change_cladding:
        project.addrect()
        project.set('name', 'new clad')
        project.set('index', 2.0)
        project.set('alpha', 0.3)
        project.set('override mesh order from material database', 1)
        project.set('mesh order', 3)
        project.set('x min', (solver_x_min - 5.0)*um)
        project.set('x max', (solver_x_max + 5.0)*um)
        project.set('y min', (solver_y_min - 5.0)*um)
        project.set('y max', (solver_y_max + 5.0)*um)
        project.set('z min', 0*um)
        project.set('z max', (solver_z_max + 5.0)*um)
        
    
    # configure global source and monitor
    wav_start = wavelength - 0.5*wav_span
    wav_stop = wavelength + 0.5*wav_span
    project.setglobalsource('wavelength start', wav_start*um)
    project.setglobalsource('wavelength stop', wav_stop*um)
    project.setglobalmonitor('frequency points', round(wav_span/wav_step)+1)
    
    # add input port (injection)
    project.addport()
    project.set('name', 'o1')
    project.set('x', (ports['o1'].center[0])*um)
    project.set('y', ports['o1'].center[1]*um)
    project.set('y span', (ports['o1'].width+4.0)*um)
    project.set('z', 0)
    project.set('z span', 2.0*um)
    project.set('injection axis', 'x-axis')
    project.set('direction', 'Forward')
    project.set('mode selection', 'user select')
    project.set('selected mode numbers', np.linspace(1, mode_num, num=mode_num))
    project.set('number of field profile samples', round(wav_span/wav_step)+1)
    
    # add output ports
    for port_name in ports:
        # check if the port name matches "o2", other ports (e.g. "o2_1") are on same position but other layers, redundant
        if re.match(r'^o\d+$', port_name) and port_name!='o1':
            project.addport()
            project.set('name', port_name)
            orientation = ports[port_name].orientation
            if orientation in [0.0, 180.0]:
                project.set('injection axis', 'x-axis')
                project.set('x', (ports[port_name].center[0])*um)
                project.set('y', ports[port_name].center[1]*um)
                project.set('y span', (ports[port_name].width+4.0)*um)
            
            elif orientation in [90.0, 270.0]:
                project.set('injection axis', 'y-axis')
                project.set('x', (ports[port_name].center[0])*um)
                project.set('y', ports[port_name].center[1]*um)
                project.set('x span', (ports[port_name].width+4.0)*um)
            
            project.set('z', 0.0)
            project.set('z span', 2.0*um)
            project.set('direction', 'Forward')
            project.set('mode selection', 'user select')
            project.set('selected mode numbers', np.linspace(1, mode_num, num=mode_num))
            project.set('number of field profile samples', round(wav_span/wav_step)+1)

    # set input port mode
    project.select('FDTD::ports')
    project.set('source port', 'o1')
    project.set('source mode', 'mode '+str(mode_idx))
    
    # add 2D z-normal monitor
    project.adddftmonitor()
    project.set('name','z normal')
    project.set('monitor type', '2D Z-normal')
    project.set('x min', solver_x_min*um)
    project.set('x max', solver_x_max*um)
    project.set('y min', solver_y_min*um)
    project.set('y max', solver_y_max*um)
    project.set('z', 0.1*um)

    # save the project file
    project.save(file_name+'_FDTD.fsp')
    
    # run simulation and extract results if requested
    if flag_run_simulation:

        start_time = datetime.now()
        print('Simulation started at '+str(start_time.strftime('%H:%M:%S')))

        project.run()

        end_time = datetime.now()
        print('Simulation finished at '+str(end_time.strftime('%H:%M:%S')))
        dur = end_time - start_time
        print('Duration '+str(dur.seconds)+' seconds')
    
        results = {}
        results['time(s)'] = dur.seconds
        
        # extract transmission and mode expansion results
        for port_name in ports:
            if re.match(r'^o\d+$', port_name):
                # total transmission
                results[port_name+' T'] = project.getresult('FDTD::ports::'+port_name, 'T')
                # mode expansion
                temp = project.getresult('FDTD::ports::'+port_name, 'expansion for port monitor')
                results[port_name+' T_net'] = {}
                results[port_name+' T_net']['lambda'] = temp['lambda']
                results[port_name+' T_net']['T_net'] = temp['T_net']
        
        return results