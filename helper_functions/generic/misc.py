# Zuyang Liu (2023)
import os
import json
import numpy as np

class ComplexEncoder(json.JSONEncoder):
    r""" written by OpenAI GPT4
    """
    def default(self, obj):
        if isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

def convert_for_json(obj):
    r""" written by OpenAI GPT4
    Recursively convert objects for JSON serialization.
    Converts numpy arrays to lists and applies the conversion to items in lists and values in dictionaries.
    """
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(item) for item in obj]
    return obj

def write_to_json(dict_name, json_name):
    r"""  written by OpenAI GPT4
    Save a Python dictionary to a JSON file. 
    Handles nested dictionaries, numpy arrays, and complex numbers.
    """
    converted_dict = convert_for_json(dict_name)
    
    os.makedirs(os.path.dirname(json_name), exist_ok=True)  # Create directories if not exist
    with open(json_name, 'w') as f:
        json.dump(converted_dict, f, cls=ComplexEncoder)
        
def read_from_json(file_name):
    r""" read a json file to a python dictionary
    """
    with open(file_name, 'r') as file:
        your_dict = json.load(file) 
    
    return your_dict

def find_closest(lst, target):
    """
    Finds the value and index of the number in a list that is closest to a given target value.
    Written by openai chatgpt 4.0

    Parameters:
    lst (list): A list of numbers.
    target (float or int): The target value.

    Returns:
    tuple: A tuple containing the closest value and its index in the list.
    """
    lst = list(lst)

    closest_value = min(lst, key=lambda x: abs(x - target))
    closest_index = lst.index(closest_value)
    
    return closest_value, closest_index