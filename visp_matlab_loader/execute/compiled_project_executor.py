from __future__ import annotations

import numbers
import os
import subprocess
import tempfile
import logging
from subprocess import PIPE
from typing import Iterable

import numpy as np
import scipy
from scipy.io import loadmat, savemat

from visp_matlab_loader.project.matlab_project import MatlabProject

from .. import matlab_path_setter
from ..mat_to_wrapper import create_script
from .matlab_execution_result import MatlabExecutionResult


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


# Note that we must have input.mat in some directory.
# This is a workaround to avoid passing values as text in the console.
class MatlabExecutor:
    """Create a script executor.

    The script executor is intended to execute scripts compiled with MATLAB compiler.
    The compiled scripts should be the ones generated from the create_script function.

    In the current implementation, arguments are passed to and from matlab using saved
    MATLAB files ('input.mat' and 'output.mat').

    To make this work, the LD_LIBRARY_PATH must be set, usually to the installation directory
    of the MATLAB runtime; see the default LD_LIBRARY_PATH for reference.

    auto_convert automatically converts inputs to floating point, according to MATLAB default handling.
    This can be avoided by setting the flag to False, but then the user must instead ensure the types are
    correct. Only simple numbers are converted - numpy arrays are not.



    Returns:
        ScriptExecutor: An instance of the class
    """

    def __init__(
        self,
        matlab_project: MatlabProject,
        auto_convert=True,
        function_json=None,
        return_inputs=False,
    ) -> None:
        self.matlab_project: MatlabProject = matlab_project
        self.auto_convert: bool = auto_convert
        self.path_setter: matlab_path_setter.MatlabPathSetter = matlab_path_setter.MatlabPathSetter()
        self.path_setter.verify_paths()
        self.return_inputs: bool = return_inputs
        self.function_json = function_json

    @property
    def available_functions(self):
        if not self._available_functions and self.function_json:
            self._available_functions = create_script.json_to_dict(self.function_json)
        return self._available_functions

    def supports_matlab_version(self, version: str) -> bool:
        return self.path_setter.can_support_version(version)

    @staticmethod
    def iterate_or_return_single(obj, expected_outputs: int | None = None):
        """
        If obj is an iterable (but not a numpy array), iterate over its elements.
        If obj is a single numpy array or a non-iterable object, return it as is.
        """
        if isinstance(obj, np.ndarray):
            if expected_outputs is not None and len(obj) != expected_outputs:
                logger.debug("Assuming numpy array is a single output, as size did not match expected outputs.")
                yield obj
            logger.debug("Numpy list is type object and length matches. Assuming value is a list of return values.")

        elif obj is not isinstance(obj, Iterable):
            logger.debug("Assuming single output, as object is not iterable.")
            yield obj
        logger.debug("Iterating over outputs.")
        for item in obj:
            yield item
            
    @staticmethod
    def mat_struct_to_dict(obj):
        """
        A function to convert MATLAB structs into Python dictionaries.
        """
        if isinstance(obj, scipy.io.matlab.mat_struct):
            # If the input object is a MATLAB struct, convert it to a dictionary
            dict = {str(field): MatlabExecutor.mat_struct_to_dict(getattr(obj, field)) for field in obj._fieldnames}
            logger.debug("Converted MATLAB struct to dictionary.")
        elif isinstance(obj, np.ndarray) and obj.dtype.names is not None:
            # If the input object is a structured NumPy array, convert it to a dictionary
            dict = {name: MatlabExecutor.mat_struct_to_dict(obj[name]) for name in obj.dtype.names}
            logger.debug("Converted structured NumPy array to dictionary.")
        elif isinstance(obj, (list, np.ndarray)):
            # If the input object is a list or an unstructured NumPy array, apply the function to each element
            dict = [MatlabExecutor.mat_struct_to_dict(element) for element in obj]
            logger.debug("Applied function to each element of list or unstructured NumPy array.")
        else:
            # If the input object is not a MATLAB struct or a NumPy array, return it as is
            dict = obj
            # Omitted this even in logging, as it is the most common case and not very interesting.
            # logger.debug("Input object is not a MATLAB struct or a NumPy array.")
        return dict

    def execute_script(self, function_name: str, output_count: int, *args):
        """Executes the specific script name witht he specified arguments.

        Requires the user to know how many outputs to extract.

        Args:
            function_name (str): The script name to run
            output_count (int): The number of outputs to request

        Returns:
            A MATLAB execution result object (MatlabExecutionResult)
        """

        logger.info("Executing script %s with %d outputs", function_name, output_count)
        logger.info("Number of inputs: %d", len(args))
        logger.info("Inputs:")
        for i, arg in enumerate(args):
            logger.info("  %d: %s of type %s", i, arg, type(arg).__name__)

        if not isinstance(args, list):
            logger.info("Converting to list for enumeration.")
            args = list(args)

        script_input = {}
        script_input["function_name"] = function_name
        script_input["output_count"] = output_count

        varargin = np.empty((len(args),), dtype=object)

        for i, arg in enumerate(args):
            if self.auto_convert:
                original_type = type(arg).__name__
                if isinstance(arg, numbers.Real):
                    arg = float(arg)
                    conversion_message = f"Input argument {i}: Converting argument to float, was {original_type}"
                elif isinstance(arg, list):
                    conversion_message = f"Input argument {i}: Found list, attempting conversion if number"
                    # We must verify if this actually works with complex file types.

                    arg = [
                        float(entry)
                        if isinstance(entry, numbers.Real)
                        else entry
                        if isinstance(entry, numbers.Complex)
                        else entry
                        for entry in arg
                    ]
                else:
                    conversion_message = f"Input argument {i}: No conversion, type is {original_type}"

                final_type = type(arg).__name__
                conversion_message += f", now {final_type}"

                logger.debug(conversion_message)

            varargin[i] = arg

        script_input["varargin"] = varargin

        # Verify that results.mat does not exist before running the script, as it will be overwritten:
        if os.path.exists("results.mat"):
            raise FileExistsError("results.mat already exists, please remove before running!")

        with tempfile.NamedTemporaryFile(suffix=".mat", delete=True) as temp_file:
            input_file = temp_file.name

            # Save input to the file
            savemat(input_file, script_input)
            logger.debug("Sending the following to the script:", script_input)

            custom_environment = os.environ.copy()

            try:
                completed_process = subprocess.run(
                    [self.matlab_project.binary_file, input_file],
                    env=custom_environment,
                    stdout=subprocess.PIPE,
                    text=True,
                )
            except (
                subprocess.TimeoutExpired,
                subprocess.CalledProcessError,
                FileNotFoundError,
                PermissionError,
                OSError,
                ValueError,
                subprocess.SubprocessError,
            ) as e:
                logger.error("%s: %s", type(e).__name__, e)

            exit_code = completed_process.returncode
            logger.info("MATLAB exited with code: %d", exit_code)
            matlab_output = completed_process.stdout
            if exit_code != 0:
                logger.error("Error: Nonzero MATLAB exit code, no results returned!")
                return MatlabExecutionResult(
                    exit_code,
                    matlab_output,
                    function_name,
                    {},
                    self.matlab_project.name,
                )

            # Load results from "results.mat" and then delete the file
            res = loadmat("results.mat", squeeze_me=True, simplify_cells=True, struct_as_record=True)
            os.remove("results.mat")
        output_names, outputs = res["results"]

        # Due to how we squeeze and simplify the cells, the output array can be a numpy
        # array shaped in unexpected ways.
        # This is our best attempt at fixing the issue for now.
        # If the return values are odd, this is likely the reason!
        logger.info("Outputs are:")
        logger.info("Type: %s", type(outputs))
        if isinstance(outputs, np.ndarray):
            logger.info("Shape: %s", outputs.shape)
        if isinstance(outputs, list):
            logger.info("Length: %d", len(outputs))
        # logger.info("Complete value: %s", outputs)

        # if outputs.dtype == np.object_ and len(outputs) == len(names):
        #     outputs = [outputs[x] for x in range(len(outputs))]
        outputs_iter = MatlabExecutor.iterate_or_return_single(outputs, expected_outputs=output_count)

        output_names = output_names.replace(",", " ").split()

        logger.info("Output names are:")
        logger.info(output_names)
        if isinstance(outputs, Iterable):
            if len(output_names) != 1 and len(output_names) != len(outputs):
                logger.warning(
                    f"Output names and outputs do not match in length!\n(Outputs: {len(outputs)}, Names: {len(output_names)})"
                )
        else:
            if len(output_names) != 1:
                logger.warning(
                    f"Output is not iterable, but there are {len(output_names)} output names Assuming only first is requested."
                )
                output_names = [output_names[0]]
        if self.return_inputs:
            return_inputs = list(varargin)
        else:
            return_inputs = []

        outputs_dict = dict(zip(output_names, outputs_iter))
        
        # Convert any matlab structs to python dictionaries
        outputs_dict = {n:MatlabExecutor.mat_struct_to_dict(v) for n,v in outputs_dict.items()}

        debug_output_lines = [f"{key}: {str(value)[:100]}" for key, value in outputs_dict.items()]
        debug_output_str = "\n\t".join(debug_output_lines)
        logger.debug("Outputs: %s", debug_output_str)

        return MatlabExecutionResult(
            exit_code,
            matlab_output,
            function_name,
            outputs_dict,
            self.matlab_project.name,
            return_inputs,
        )

    # exit_code, matlab_output, {x: y for x, y in zip(names, outputs_iter)}

    def print_available_functions(self):
        for f in list(self.available_functions.keys()):
            print(f)
            print("Inputs:")
            for i in self.available_functions[f]["input"]:
                print(f"  {i}")
            print("Outputs")
            for i in self.available_functions[f]["output"]:
                print(f"  {i}")


if __name__ == "__main__":
    print("This is a library, not a standalone script.")
