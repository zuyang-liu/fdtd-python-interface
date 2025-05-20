import os
import json
import numpy as np

class ComplexEncoder(json.JSONEncoder):
    r""" 
    """
    def default(self, obj):
        if isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

def convert_for_json(obj):
    r""" 
    Recursively convert objects for JSON serialization.
    
    Converts:
        - NumPy arrays → lists
        - Items inside dicts and lists → recursively converted
    """
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(item) for item in obj]
    return obj

def write_to_json(dict_name, json_name):
    r"""  
    Save a dictionary to a JSON file.
    
    Handles:
        - Nested dictionaries
        - NumPy arrays
        - Complex numbers
    """
    converted_dict = convert_for_json(dict_name)
    
    os.makedirs(os.path.dirname(json_name), exist_ok=True)  # Create directories if they do not exist
    with open(json_name, 'w') as f:
        json.dump(converted_dict, f, cls=ComplexEncoder)

def find_closest(lst, target):
    r"""
    Find the value and index of the item in a list closest to a given target.

    Args:
        lst (list): List of numeric values.
        target (float or int): Target value.

    Returns:
        tuple: (closest_value, index_of_closest_value)
    """
    lst = list(lst)
    closest_value = min(lst, key=lambda x: abs(x - target))
    closest_index = lst.index(closest_value)
    return closest_value, closest_index