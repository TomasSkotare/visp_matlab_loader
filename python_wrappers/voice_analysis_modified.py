#!/usr/bin/env python3

import argparse
import importlib.util
import os
import sys
from fileinput import filename

import numpy as np


def find_matlab_compiled(
    directory=os.path.dirname(os.path.realpath(__file__)), verbose=False
):
    while directory != "/":
        if "matlab" in os.listdir(directory):
            if "compiled" in os.listdir(os.path.join(directory, "matlab")):
                if verbose:
                    print("Found compiled folder")
                return os.path.join(directory, "matlab", "compiled")
        directory = os.path.abspath(os.path.join(directory, os.pardir))
    return None


def find_and_import_package(
    package_name, directory=os.path.dirname(os.path.realpath(__file__))
):
    current_dir = directory
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
parser = argparse.ArgumentParser(
    description="Voice analysis toolbox, with default values available for settings."
)


def int_list(string):
    try:
        return [float(i) for i in string.split(",")]
    except Exception as e:
        print(f"Error parsing string {string}: {e}")
        return string


# Add arguments
parser.add_argument("--f0_alg", default="SWIPE", type=str, help="Algorithm for f0")
parser.add_argument(
    "--start_time", default=np.double(0), type=np.double, help="Start time"
)
parser.add_argument("--end_time", default=np.inf, type=np.double, help="End time")
parser.add_argument("--Tmax", default=1000, type=int, help="Maximum time")
parser.add_argument("--d", default=np.double(4), type=int, help="d value")
parser.add_argument("--tau", default=50, type=int, help="tau value")
parser.add_argument("--eta", default=0.2, type=float, help="eta value")
parser.add_argument(
    "--dfa_scaling",
    default=[float(x) for x in range(50, 210, 20)],
    type=int_list,
    help="DFA scaling values",
)
parser.add_argument("--f0min", default=50, type=int, help="Minimum f0")
parser.add_argument("--f0max", default=500, type=int, help="Maximum f0")
parser.add_argument("--flag", default=1, type=int, help="Flag value")
parser.add_argument("--verbose", default=False, type=bool, help="Verbose mode")
parser.add_argument(
    "filename", type=str, help="Input filename"
)  # New filename argument
parser.add_argument("output", type=str, help="Output filename")  # New filename argument

# Parse the arguments
args = parser.parse_args()

verbose = args.verbose

# Usage
visp_matlab_loader = find_and_import_package("visp_matlab_loader")
if visp_matlab_loader:
    if verbose:
        print(f"Package found and imported")
else:
    print("Package not found")

if verbose:
    # Print the values
    for arg, value in args.__dict__.items():
        print(f"Argument: {arg}, Value: {value} Type: {type(value)}")
if os.path.isfile(args.filename):
    if verbose:
        print("File exists")
else:
    print(f"File {args.filename} does not exist, aborting")
    sys.exit(-1)

from visp_matlab_loader.execute.compiled_project_executor import MatlabExecutor
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
from visp_matlab_loader.wrappers.matlab_wrapper_helper import ensure_vector

# Consider to make this an argument
compiled_projects = CompiledProjectFinder(find_matlab_compiled())
print(compiled_projects)
if verbose:
    print("Found compiled projects:")
    for project in compiled_projects._compiled_projects:
        print(project)
        print(project.name)
va_toolbox = compiled_projects.get_project("voice_analysis_toolbox")
if va_toolbox is None:
    print("Project not found in the specified folder, aborting")
    sys.exit(-1)

# Execute the project
executor = MatlabExecutor(va_toolbox, return_inputs=True)

pass_args = vars(args)
filename = pass_args.pop("filename")
output = pass_args.pop("output")
matlab_format = dict()


for arg, value in pass_args.items():
    if verbose:
        print(f"Argument: {arg}, Value: {value} Type: {type(value)}")
    matlab_format[arg] = value

# This is necessary to ensure it is of length [x,1] rather than [x,]
matlab_format["dfa_scaling"] = ensure_vector(
    matlab_format["dfa_scaling"], vector_type="column"
)

result = executor.execute_script("voice_analysis_modified", 3, filename, matlab_format)

# Save json to output file
result.to_json(output)

if result.return_code == 0:
    print(f"Execution successful, result saved to {output}")
else:
    print(
        f"Execution failed, return code {result.return_code}\nSee {output} for details."
    )
