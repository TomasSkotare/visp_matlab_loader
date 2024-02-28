# Note that we must have input.mat in some directory.
# This is a workaround to avoid passing values as text in the console.

import numbers
import os
import subprocess
from subprocess import PIPE
import tempfile
from typing import Iterable

import numpy as np
from scipy.io import loadmat, savemat

from visp_matlab_loader.project.abstract_project import AbstractProject

from .. import matlab_path_setter
from ..mat_to_wrapper import create_script
from .abstract_executor import AbstractExecutor
from .matlab_execution_result import MatlabExecutionResult


class ExecuteCompiledProject(AbstractExecutor):
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
        matlab_project: AbstractProject,  # TODO Make sure this is a MATLAB project
        auto_convert=True,
        verbose=False,
        function_json=None,
        return_inputs=False,
    ) -> None:
        self.matlab_project = matlab_project
        self.auto_convert = auto_convert
        self.verbose = verbose
        self.path_setter = matlab_path_setter.MatlabPathSetter()
        self.path_setter.verify_paths()
        self.return_inputs = return_inputs

        if not function_json:
            function_json = matlab_project.function_json

        if function_json:
            self.available_functions = create_script.json_to_dict(function_json)

    def vprint(self, *args):
        if self.verbose:
            print(*args)

    @staticmethod
    def iterate_or_return_single(obj):
        """
        If obj is an iterable (but not a numpy array), iterate over its elements.
        If obj is a single numpy array or a non-iterable object, return it as is.
        """
        if isinstance(obj, np.ndarray) or not isinstance(obj, Iterable):
            yield obj
        else:
            for item in obj:
                yield item

    def execute_script(self, function_name: str, output_count: int, *args):
        """Executes the specific script name witht he specified arguments.

        Requires the user to know how many outputs to extract.

        Args:
            function_name (str): The script name to run
            output_count (int): The number of outputs to request

        Returns:
            A MATLAB execution result object (MatlabExecutionResult)
        """

        if self.verbose:
            print("Executing script", function_name, "with", output_count, "outputs")
            print("Number of inputs: ", len(args))
            print("Inputs:")
            for i, arg in enumerate(args):
                print(f"  {i}: {arg} of type {type(arg).__name__}")

        if type(args) is not list:
            self.vprint("Converting to list for enumeration.")
            args = list(args)

        input = dict()
        input["function_name"] = function_name
        input["output_count"] = output_count

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

                # If the message is too long, print only the first 100 characters
                if len(conversion_message) > 100:
                    conversion_message = conversion_message[:100] + "..."

                self.vprint(conversion_message)

            varargin[i] = arg

        input["varargin"] = varargin
        with tempfile.NamedTemporaryFile(suffix=".mat", delete=True) as temp_file:
            input_file = temp_file.name

            # Save input to the file
            savemat(input_file, input)
            self.vprint(input)

            custom_environment = os.environ.copy()

            stream = subprocess.Popen(
                [self.matlab_project.binary_file, input_file],
                env=custom_environment,
                stdout=PIPE,
            )
            exit_code = stream.wait()
            self.vprint(f"MATLAB exited with code: {exit_code}")
            # Ensure output is string!
            matlab_output = stream.communicate()[0]
            matlab_output = matlab_output.decode("utf-8")
            if exit_code != 0:
                self.vprint("Error: Nonzero MATLAB exit code, no results returned!")
                return MatlabExecutionResult(exit_code, matlab_output, function_name, dict())

            # Load results from "results.mat" and then delete the file
            res = loadmat("results.mat", squeeze_me=True, simplify_cells=True)
            os.remove("results.mat")
        names, outputs = res["results"]
        # Due to how we squeeze and simplify the cells, the output array can be a numpy
        # array shaped in unexpected ways.
        # This is our best attempt at fixing the issue for now.
        # If the return values are odd, this is likely the reason!
        self.vprint("Outputs are:")
        self.vprint("Type:", type(outputs))
        self.vprint("Complete value:", outputs)

        # if outputs.dtype == np.object_ and len(outputs) == len(names):
        #     outputs = [outputs[x] for x in range(len(outputs))]
        outputs_iter = self.__class__.iterate_or_return_single(outputs)

        names = names.replace(",", " ").split()
        if self.return_inputs:
            return_inputs = list(varargin)
        else:
            return_inputs = []
        return MatlabExecutionResult(
            exit_code,
            matlab_output,
            function_name,
            {x: y for x, y in zip(names, outputs_iter)},
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
    pass
