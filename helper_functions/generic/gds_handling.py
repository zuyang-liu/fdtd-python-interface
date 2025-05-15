# Zuyang Liu (2023)
import gdsfactory as gf 

def get_layer_name_by_tuple(layer_tuple):

    pdk = gf.get_active_pdk()
    layers = pdk.get_layer_views().layer_map
    
    r""" get layer name in custom pdk from tuple
    This function is helped by OpenAI GPT4

    Args:
        layer_tuple: e.g. (1, 0)

    Returns:
        name: str, layer name in pdk
    """
    # Iterate over all attributes of the LAYER instance
    for name in layers:  
        # Ignore special and private attributes
        if not name.startswith('__'):
            # Get the attribute
            attr = layers[name]
            # Check if the attribute is an instance of Layer and matches the layer_tuple
            if attr == layer_tuple:
                return name
    return "Unknown Layer"

def extend_from_ports(device, offset: float=10.0):
    r""" add straight sections to all ports of a device in order to extend through boundaries in simulations.
    This function is partly written by OpenAI GPT4

    Args:
        device: a gdsfactory component with ports
        offset (float, optional): length of straight section. Defaults to 10.0.

    Returns:
        c: new gdsfactory component with extensions
        ports: ports information of the original device
    """
    
    c = gf.Component('extended_cell')
    device = c << device

    # add straight extensions to each port
    for port_name in device.ports:
        port = device.ports[port_name]
        
        # if the port has cross_section property, use it
        if port.cross_section:
            xs = gf.get_cross_section(port.cross_section)
        # if the port does not have cross_section property, create a single-layer cross-section
        else:
            xs = gf.cross_section.cross_section(width=port.width, layer=port.layer)
        
        ### Note ###
        # Cross-section property cannot be written to metadata in gdsfactory.
        # If the device is read from GDS file and metadata, there would not be cross-section information in any ports.
        # Ports contain layer and width, using which a new cross-section is defined.
        # Each port can only have one layer and one width.
        # If the device cross-section is multi-layered, make sure to create a port for each layer when exporting the GDS.
        # Otherwise the extension would only be on one layer, physically incorrect.
        ############
        
        # create straight section using the layer
        extension = c << gf.components.straight(length=offset, cross_section=xs)
        extension.connect('o2', port)
        
        # add new ports
        c.add_port(name=port_name, port=extension.ports['o1'])
        
        # absorbs from ComponentReference into Component
        c.absorb(extension)
    
    # record the original ports before extension for simulation needs
    original_ports = device.ports
    # absorbs from ComponentReference into Component
    c.absorb(device)
    
    return c, original_ports