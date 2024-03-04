# Create a class called CovarrepWrapper

import os
import sys
import importlib

def find_and_import_package(package_name):
    # set current_dir to path of currently executing file:
    current_dir = os.path.dirname(os.path.realpath(__file__))
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


try:
    import visp_matlab_loader
except ModuleNotFoundError:
    print("Could not import visp_matlab_loader, attempting to import it from the local directory")
    visp_matlab_loader = find_and_import_package("visp_matlab_loader")
    if visp_matlab_loader is None:
        raise ImportError("Could not import visp_matlab_loader from the local directory")

from visp_matlab_loader.wrappers.matlab_wrapper import MatlabProjectWrapper, matlab_function, placeholder_result
from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult


class get_next_thousand(MatlabProjectWrapper):

    def __init__(self, directory):
        super().__init__(self.__class__.__name__.lower(), directory)
        
    @matlab_function
    def getnextthousand(self, requested_outputs: int, starting_number: int) -> MatlabExecutionResult:
        return placeholder_result()
    
    @matlab_function
    def getnexttwothousand(self, requested_outputs: int, starting_number: int) -> MatlabExecutionResult:
        return placeholder_result()
    



