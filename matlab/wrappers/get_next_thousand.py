

import importlib
import os
import sys


def find_and_import_package(package_name, additional_dirs=None):
    # set current_dir to path of currently executing file:
    current_dir = os.path.dirname(os.path.realpath(__file__))
    dirs_to_check = [current_dir]

    # Add parent directories to dirs_to_check
    while True:
        parent_dir = os.path.dirname(current_dir)
        if current_dir == parent_dir:  # We've reached the root directory
            break
        dirs_to_check.append(parent_dir)
        current_dir = parent_dir

    # Add additional directories to dirs_to_check
    if additional_dirs is not None:
        dirs_to_check.extend(additional_dirs)

    # Check all directories in dirs_to_check
    for dir in dirs_to_check:
        items_in_dir = os.listdir(dir)
        for item in items_in_dir:
            item_path = os.path.join(dir, item)
            if os.path.isdir(item_path) and item == package_name:
                sys.path.insert(0, dir)  # Add directory to sys.path
                package = importlib.import_module(package_name)
                return package

    return None  # Package not found


try:
    import visp_matlab_loader
except ModuleNotFoundError:
    print(
        "Could not import visp_matlab_loader, attempting to import it from the local directory"
    )
    visp_matlab_loader = find_and_import_package("visp_matlab_loader")
    if visp_matlab_loader is None:
        raise ImportError(
            "Could not import visp_matlab_loader from the local directory"
        )

from visp_matlab_loader.execute.matlab_execution_result import \
    MatlabExecutionResult
from visp_matlab_loader.wrappers.matlab_wrapper import (MatlabProjectWrapper,
                                                        default_args,
                                                        matlab_function)


class get_next_thousand(MatlabProjectWrapper):
    """
    A wrapper class for the 'get_next_thousand' MATLAB project.

    Args:
        directory (str): The directory path of the MATLAB project.

    Attributes:
        directory (str): The directory path of the MATLAB project.

    Methods:
        getnextthousand: A MATLAB function that returns the next thousand numbers.
        getnexttwothousand: A MATLAB function that returns the next two thousand numbers.
    """

    def __init__(self, directory):
        super().__init__(self.__class__.__name__.lower(), directory)

    @matlab_function
    def getnextthousand(
        self, inputNumber: int, requested_outputs=1
    ) -> MatlabExecutionResult:
        """
        Call the 'getnextthousand' MATLAB function.

        Args:
            inputNumber (int): The input number.
            requested_outputs (int, optional): The number of requested outputs. Defaults to 1.

        Returns:
            MatlabExecutionResult: The result of the MATLAB function execution.
        """
        return default_args(locals())  # type: ignore

    @matlab_function
    def getnexttwothousand(
        self, inputNumber: int, requested_outputs=1
    ) -> MatlabExecutionResult:
        """
        Call the 'getnexttwothousand' MATLAB function.

        Args:
            inputNumber (int): The input number.
            requested_outputs (int, optional): The number of requested outputs. Defaults to 1.

        Returns:
            MatlabExecutionResult: The result of the MATLAB function execution.
        """
        return default_args(locals())  # type: ignore
