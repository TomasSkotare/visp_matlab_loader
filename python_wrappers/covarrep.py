#!/usr/bin/env python3

import argparse
from fileinput import filename
import numpy as np
import os
import sys
import importlib.util
import ast


def ensure_column_vector(array):
    # Convert the input to a numpy array if it's not already
    if not isinstance(array, np.ndarray):
        array = np.array(array)
    
    # Convert the array to float type
    array = array.astype(float)
    
    # If the array is a 1D array, reshape it to a column vector
    if len(array.shape) == 1:
        array = array.reshape((-1, 1))
    
    return array

def find_matlab_compiled(directory='.', verbose=False):
    while directory != '/':
        if 'matlab' in os.listdir(directory):
            if 'compiled' in os.listdir(os.path.join(directory, 'matlab')):
                if verbose:
                    print('Found compiled folder')
                return os.path.join(directory, 'matlab', 'compiled')
        directory = os.path.abspath(os.path.join(directory, os.pardir))
    return None

def find_and_import_package(package_name):
    current_dir = os.getcwd()
    while True:
        items_in_dir = os.listdir(current_dir)
        for item in items_in_dir:
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path) and item == package_name:
                sys.path.insert(0, current_dir)  # Add parent directory to sys.path
                package = importlib.import_module(package_name)
                return package
        parent_dir = os.path.dirname(current_dir)
        if current_dir == parent_dir:  # We've reached the root directory
            break
        current_dir = parent_dir
    return None  # Package not found

   
# Create the parser
parser = argparse.ArgumentParser(description="Process some inputs.")


# Create the parser
parser = argparse.ArgumentParser(description="Process some inputs.")

# Add a single argument that takes multiple values
parser.add_argument('inputs', nargs='*', help='Input values in the format key:type:value')

# Create the first parser
parser1 = argparse.ArgumentParser(add_help=False)
print(1)
# Add the arguments you want to handle early
parser1.add_argument('function_name', type=str, help='Covarep function name')
parser1.add_argument('--output', help='Output argument')
parser1.add_argument('--output_count', type=int, help='Output count argument')
parser1.add_argument('--verbose', default=False, type=bool, help='Verbosity level')

# Parse the early arguments
args1, remaining_args = parser1.parse_known_args()

# Store the early arguments
function_name = args1.function_name 
output = args1.output
output_count = args1.output_count
verbose = args1.verbose

# Create the second parser
parser2 = argparse.ArgumentParser(description="Process some inputs.")
print(2)
# Add a single argument that takes multiple values
parser2.add_argument('inputs', nargs='*', help='Input values in the format key:type:value')

# Parse the rest of the arguments
args2 = parser2.parse_args(remaining_args)
print(args2)

# Initialize an empty dictionary to store the inputs
inputs = {}


# Process each input
for input_str in args2.inputs:
    # Split the input string into key, type, and value
    key, type_str, value_str = input_str.split(':', 2)

    # Parse the value based on the type
    if type_str == 'int':
        value = int(value_str)
    elif type_str == 'float':
        value = float(value_str)
    elif type_str == 'str':
        value = value_str
    elif type_str == 'bool':
        value = value_str.lower() in ['true', '1']
    elif type_str == 'int_list':
        value = ast.literal_eval(value_str)
    elif type_str == 'float_list':
        value = [float(i) for i in ast.literal_eval(value_str)]
    elif type_str == 'str_list':
        value = ast.literal_eval(value_str)
    elif type_str == 'np_array':
        value = np.array(ast.literal_eval(value_str))
    else:
        raise ValueError(f'Unknown type: {type_str}')

    # Add the value to the dictionary
    inputs[key] = value
print(inputs)


# Usage
visp_matlab_loader = find_and_import_package('visp_matlab_loader')
if visp_matlab_loader:
    if verbose:
        print(f'Package found and imported')
else:
    print('Package not found')
    
from visp_matlab_loader.execute.compiled_project_executor import ExecuteCompiledProject
from visp_matlab_loader.find_compiled_projects import MatlabProject, CompiledProjectFinder   

# Consider to make this an argument
compiled_projects = CompiledProjectFinder(find_matlab_compiled(directory='.'))
if verbose:
    print('Found compiled projects:')
    for project in compiled_projects._compiled_projects:
        print(project.name)
covarep = compiled_projects.get_project('covarep')
if covarep is None:
    print('Project not found in the specified folder, aborting')
    sys.exit(-1)
    
# Execute the project
executor = ExecuteCompiledProject(covarep,return_inputs=True, verbose=verbose)

pass_args = vars(args2)
matlab_format = dict()

print(f'Attempting to execute {function_name} with {output_count} outputs and {len(inputs)} inputs')
print('Inputs:')
for arg, value in inputs.items():
    print(f"Argument: {arg}, Value: {value} Type: {type(value)}")
result = executor.execute_script(function_name, output_count, [x for x in inputs.values()])

# Save json to output file
result.to_json(output)

if result.return_code == 0:
    print(f"Execution successful, result saved to {output}")
else:
    print(f"Execution failed, return code {result.return_code}\nSee {output} for details.")





