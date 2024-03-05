# Create a class called CovarrepWrapper

import importlib
import os
import sys

import numpy as np


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
    visp_matlab_loader = find_and_import_package(
        "visp_matlab_loader", "/matlab-scripts/"
    )
    if visp_matlab_loader is None:
        raise ImportError(
            "Could not import visp_matlab_loader from the local directory"
        )

from visp_matlab_loader.execute.matlab_execution_result import \
    MatlabExecutionResult
from visp_matlab_loader.wrappers.matlab_wrapper import (MatlabProjectWrapper,
                                                        matlab_function)
from visp_matlab_loader.wrappers.matlab_wrapper_helper import ensure_vector


class voice_analysis_toolbox(MatlabProjectWrapper):
    def __init__(self, directory):
        super().__init__(self.__class__.__name__.lower(), directory)

    @matlab_function
    def voice_analysis_modified(
        self,
        filename: str,
        f0_alg="SWIPE",
        start_time=0,
        end_time=np.inf,
        Tmax=1000,
        d=4,
        tau=50,
        eta=0.2,
        dfa_scaling=np.arange(50, 201, 20),
        f0min=50,
        f0max=500,
        flag=1,
        requested_outputs=3,
    ) -> MatlabExecutionResult:
        if not filename:
            raise ValueError("Filename must be provided")
        dfa_scaling = ensure_vector(dfa_scaling, "column")

        # ensure that both start time and end time are floats:
        start_time = float(start_time)
        end_time = float(end_time)
        # This function takes a struct (dictionary) as input in MATLAB, so we need to convert
        # the input parameters to a dictionary. However, filename is sent as a separate argument.
        params = {
            k: v
            for k, v in locals().items()
            if k not in ["self", "filename", "requested_outputs"]
        }
        args = (filename,)
        kwargs = {"requested_outputs": requested_outputs, "params": params}

        return args, kwargs  # type: ignore
