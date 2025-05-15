# Zuyang Liu (2023)
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
    
    # default parameters
    um = 1e-6
    
    p = dict(
        wavelength = 0.85,
        wav_span = 0.04,
        wav_step = 0.01,
        # wav_start = 0.78,
        # wav_stop = 0.94,
        resolution = 6,
        temperature = 300,
        gds_file = 'mmi_1x2_450_VISPIC2',
        material_type = "universal",
        guiding_material = 'SiN',
        lumapi_path = r"C:\Program Files\Lumerical\v232\api\python",
        file_name = 'test_'+str(datetime.now().strftime('%Y%m%d%H%M%S')),
        mode_num = 5,
        mode_idx = 1,
        flag_extend = 1,
        extension = 10,
        flag_run_simulation = 0,
        flag_grating_coupler = 0,
        solver_z_min = -0.5,
        solver_z_max = 0.7,
        flag_boolean = 0,
        no_cladding = False,
    )
    
    # update default setting with input
    p.update(parameters)
    
    # convert settings to local variables
    for key, value in p.items():
        globals()[key] = value
    
    # save parameters to a json file
    write_to_json(dict_name=p, json_name=file_name+'_fdtd.json')
    
    # start lumerical fdtd
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
    
    # read gds, and extend from ports
    if flag_extend:
        device = gf.import_gds(gds_file+'.gds', read_metadata=True)
        device, ports = extend_from_ports(device, offset=extension)
        device.write_gds(file_name+'_extended.gds', with_metadata=True)
        # import_gds_to_lumerical(project=project, gds_file=file_name+'_extended.gds', material=mat_wg, cell_name='extended_cell')
        import_gds_to_lumerical(project=project, gds_file=file_name+'_extended.gds', material=mat_wg, flag_boolean=flag_boolean)
        
    else:
        device = gf.import_gds(gds_file+'.gds', read_metadata=True)
        ports = device.ports
        # device.write_gds(file_name+'.gds', with_metadata=True)
        import_gds_to_lumerical(project=project, gds_file=file_name+'.gds', material=mat_wg, flag_boolean=flag_boolean)
    
    
    # add FDTD solver
    project.addfdtd()
    project.set('simulation temperature', temperature)
    project.set('dimension', '3D')
    
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
  
    # solver_x_min = ports['o1'].center[0] - 1.0
    # solver_x_max = ports['o'+str(len(ports))].center[0] + 1.0 #device.xmax - 0.5*extension
    # solver_y_min = device.ymin - 1.0
    # solver_y_max = device.ymax + 1.0
    
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
    
    project.set('x min bc', 'PML')
    project.set('y min bc', 'PML')
    project.set('x max bc', 'PML')
    project.set('y max bc', 'PML')
    project.set('z min bc', 'PML')
    project.set('z max bc', 'PML')

    ##### change PML settings if simulation diverges #####
    pmlDiv = 0
    if pmlDiv:
        project.set('pml profile', 4) # set PML profile to 'stabilized' to prevent diverging simulation
        project.set('pml layers',64)
        project.set('pml kappa', 5)
        project.set('pml alpha', 0.9)
    
    ### add air cladding ###
    if no_cladding:
        project.addrect()
        project.set('name', 'air clad')
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
        
    
    ##### global source and monitor properties #####
    wav_start = wavelength - 0.5*wav_span
    wav_stop = wavelength + 0.5*wav_span
    project.setglobalsource('wavelength start', wav_start*um)
    project.setglobalsource('wavelength stop', wav_stop*um)
    project.setglobalmonitor('frequency points', round(wav_span/wav_step)+1)
    
    ##### add inject port #####
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
    
    ##### add output ports #####
    for port_name in ports:
        # check if the port name matches "o2", other ports (e.g. "o2_1") are on same position but other layers, redundant
        if re.match(r'^o\d+$', port_name) and port_name!='o1':
            project.addport()
            project.set('name', port_name)
            
            if ports[port_name].orientation == 180.0 or ports[port_name].orientation == 0.0:
                project.set('injection axis', 'x-axis')
                project.set('x', (ports[port_name].center[0])*um)
                project.set('y', ports[port_name].center[1]*um)
                project.set('y span', (ports[port_name].width+4.0)*um)
            
            if ports[port_name].orientation == 90.0 or ports[port_name].orientation == 270.0:
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
    
    # special output port setting for grating couplers
    if flag_grating_coupler:
        
        # add oxide cladding
        project.addrect()
        project.set('name', 'background oxide')
        project.set('y max', (solver_y_max+2.0)*um)
        project.set('y min', (solver_y_min-2.0)*um)
        project.set('x max', (solver_x_max+2.0)*um)
        project.set('x min', (solver_x_min-2.0)*um)
        project.set('z min', (solver_z_min-2.0)*um)
        project.set('z max', 0.5*um)
        project.set('material', mat_ox)
        project.set('override mesh order from material database', 1)
        project.set('mesh order', 3)
        project.set('alpha', 0.3)

        if guiding_material == 'Si':
            project.addrect()
            project.set('name', 'Si slab')
            project.set('y max', (solver_y_max+2.0)*um)
            project.set('y min', (solver_y_min-2.0)*um)
            project.set('x max', (solver_x_max+2.0)*um)
            project.set('x min', (solver_x_min-2.0)*um)
            project.set('z min', 0*um)
            project.set('z max', 0.15*um)
            project.set('material', mat_wg)
            project.set('override mesh order from material database', 1)
            project.set('mesh order', 2)

        # add optical fiber
        project.addstructuregroup()
        project.set('name', 'fiber')
        project.set('x', 23*um)
        project.adduserprop('core diameter', 2, 9*um)
        project.adduserprop('clad diameter', 2, 50*um)
        project.adduserprop('y span', 2, 20*um)
        project.adduserprop('theta', 0, 8)
        project.adduserprop('core index', 0, 1.44427)
        project.adduserprop('clad index', 0, 1.43482)

        myscript = """deleteall;
        core_index = %core index%;
        clad_index = %clad index%;
        addcircle();
        set('name', 'core');
        setnamed("core","index",core_index);
        addcircle();
        set('name', 'clad');
        setnamed("clad","index",clad_index);
        core_radius = %core diameter%*0.5;
        clad_radius = %clad diameter%*0.5;

        theta_rad = theta/(180/pi);
        L = %y span%/cos(theta_rad);
        setnamed("core","radius",core_radius);
        setnamed("core","x",0.0);
        setnamed("core","y",0.0);
        setnamed("core","z",0.0);
        setnamed("core","z span",L);
        setnamed("core","first axis","y");
        setnamed("core","rotation 1",theta);
        setnamed("core", "override mesh order from material database", 1);
        setnamed("core", "mesh order", 4);

        setnamed("clad","radius",clad_radius);
        setnamed("clad","x",0.0);
        setnamed("clad","y",0.0);
        setnamed("clad","z",0.0);
        setnamed("clad","z span",L);
        setnamed("clad","first axis","y");
        setnamed("clad","rotation 1",theta);
        setnamed("clad", "override mesh order from material database", 1);
        setnamed("clad", "mesh order", 5);
        setnamed("clad", "alpha", 0.3);
        """

        project.set('script', myscript)
        
        project.addindex()
        project.set('name','index')
        project.set('monitor type', '2D Y-normal')
        project.set('x min', solver_x_min*um)
        project.set('x max', solver_x_max*um)
        project.set('z min', solver_z_min*um)
        project.set('z max', solver_z_max*um)
        project.set('y', 0.0*um)

        project.addport()
        project.set('name', 'o2')
        project.set('injection axis', 'z-axis')
        project.set('x min', solver_x_min*um)
        project.set('x max', solver_x_max*um)
        project.set('y', 0)
        project.set('y span', (solver_y_max-solver_y_min)*um)
        project.set('theta', 8)
        project.set('rotation offset', 3*um)
        project.set('z', (solver_z_max-0.3)*um)
        project.set('mode selection', 'user select')
        project.set('selected mode numbers', np.linspace(1, mode_num, num=mode_num))
        project.set('number of field profile samples', round(wav_span/wav_step)+1)

        # add y-normal monitor over the entire simulation area
        project.adddftmonitor()
        project.set('name','y normal')
        project.set('monitor type', '2D Y-normal')
        project.set('x min', solver_x_min*um)
        project.set('x max', solver_x_max*um)
        project.set('z min', solver_z_min*um)
        project.set('z max', solver_z_max*um)
        project.set('y', 0*um)


    # set source mode
    project.select('FDTD::ports')
    project.set('source port', 'o1')
    project.set('source mode', 'mode '+str(mode_idx))
    
    # add z-normal monitor over the entire simulation area
    project.adddftmonitor()
    project.set('name','z normal')
    project.set('monitor type', '2D Z-normal')
    project.set('x min', solver_x_min*um)
    project.set('x max', solver_x_max*um)
    project.set('y min', solver_y_min*um)
    project.set('y max', solver_y_max*um)
    project.set('z', 0.1*um)
    
    project.save(file_name+'_FDTD.fsp')
    
    if flag_run_simulation:
        start_time = datetime.now()
        print('Simulation started at '+str(start_time.strftime('%H:%M:%S')))
        # run simulation
        project.run()
        end_time = datetime.now()
        print('Simulation finished at '+str(end_time.strftime('%H:%M:%S')))
        dur = end_time - start_time
        print('Duration '+str(dur.seconds)+' seconds')
    
        results = {}
        results['time(s)'] = dur.seconds
        
        # # get all data from each port
        # for port_name in ports:
        #     if re.match(r'^o\d+$', port_name):
        #         keys = project.getresult('FDTD::ports::'+port_name)
        #         keys = keys.split('\n') # convert a long string to a list            
        #         for key in keys:
        #             if key != 'farfield': # far field calculation requires further manual setting
        #                 temp = project.getresult('FDTD::ports::'+port_name, key)
        #                 results[port_name+' '+key] = temp

        # get results of interest from each port
        for port_name in ports:
            if re.match(r'^o\d+$', port_name):
                # # electric field distribution
                # results[port_name+' E'] = project.getresult('FDTD::ports::'+port_name, 'E')
                # total transmission
                results[port_name+' T'] = project.getresult('FDTD::ports::'+port_name, 'T')
                # mode expansion
                temp = project.getresult('FDTD::ports::'+port_name, 'expansion for port monitor')
                results[port_name+' T_net'] = {}
                results[port_name+' T_net']['lambda'] = temp['lambda']
                results[port_name+' T_net']['T_net'] = temp['T_net']
        
        # # write the results to a json file
        # write_to_json(dict_name=results, json_name=file_name+'_results.json')
        
        return results