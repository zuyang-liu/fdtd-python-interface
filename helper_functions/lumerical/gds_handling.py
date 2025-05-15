# Zuyang Liu (2023)

from helper_functions.generic.gds_handling import get_layer_name_by_tuple
import gdsfactory as gf
import pya



um = 1e-6

def import_gds_to_lumerical(project, gds_file, material, cell_name: str | None=None, flag_boolean = 0):
    r""" import each layer of gds and return ports information.
    All layers use the same material.

    Args:
        project (_type_): lumerical project.
        gds_file (_type_): gds file path.
        material (_type_): material name in database.

    Returns:
        nothing
    """
    pdk = gf.get_active_pdk()
    layers = pdk.get_layer_views().layer_map
    layer_stack = pdk.get_layer_stack()

    # if a cell name is given, find the required cell
    if cell_name:
        top_cell = gf.import_gds(gdspath=gds_file, cellname=cell_name, read_metadata=True)
    # if a cell name is not given, return the top cell
    else:
        top_cell = gf.import_gds(gds_file, read_metadata=True)
        cell_name = top_cell.name

    cell_layers = top_cell.layers

    # boolean operation of partial etch layer
    if flag_boolean:
        if layers['SiN1'] in cell_layers and layers['SiN1p'] in cell_layers:
            # Initialize the main layout and read the input GDS file
            layout = pya.Layout()
            layout.read(gds_file)

            # Access the top cell
            top_cell = layout.top_cell()
            
            # Define the layer information for the operation
            layer1_info = pya.LayerInfo(layers['SiN1'][0], layers['SiN1'][1])
            layer2_info = pya.LayerInfo(layers['SiN1p'][0], layers['SiN1p'][1])
            result_layer_info = pya.LayerInfo(layers['SiN1'][0], layers['SiN1'][1])

            layer1 = layout.layer(layer1_info)
            layer2 = layout.layer(layer2_info)

            # Create pya.Region objects for each layer
            layer1 = pya.Region()
            layer2 = pya.Region()

            # Fill the regions with shapes from the corresponding layers
            for shape in top_cell.shapes(layout.layer(layer1_info)):
                if shape.is_polygon() or shape.is_box() or shape.is_path():
                    layer1.insert(shape.polygon)

            for shape in top_cell.shapes(layout.layer(layer2_info)):
                if shape.is_polygon() or shape.is_box() or shape.is_path():
                    layer2.insert(shape.polygon)

            # Perform a boolean operation (e.g., XOR) between the two regions
            result_region = layer1 - layer2  # Change ^ to & for AND, | for OR, - for NOT

            # Clear the existing shapes in the result layer and insert the result of the boolean operation
            result_layer_index = layout.layer(result_layer_info)
            top_cell.shapes(result_layer_index).clear()
            top_cell.shapes(result_layer_index).insert(result_region)

            # Save the modified layout to GDS file
            layout.write(gds_file)
    
    for layer in cell_layers:
        layer_name = get_layer_name_by_tuple(layer) # find layer name (e.g. SiN1) from the tuple (e.g.(1,0)) in PDK
        zmin = layer_stack.layers[layer_name].zmin # find zmin of the corresponding layer in PDK
        thickness = layer_stack.layers[layer_name].thickness
        zmax = zmin + thickness
        
        # import cell layer by layer
        project.gdsimport(gds_file, cell_name, str(layer[0])+':'+str(layer[1]), material, zmin*um, zmax*um)
        project.set('name', layer_name)