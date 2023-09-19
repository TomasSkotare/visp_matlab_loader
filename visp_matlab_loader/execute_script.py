# Note that we must have input.mat in some directory.
# This is a workaround to avoid passing values as text in the console.

from typing import Iterable
import numpy as np
from scipy.io import savemat, loadmat
import os
import subprocess
from subprocess import PIPE
import numbers
from pprint import pprint
from . import create_script
from . import matlab_path_setter

class ScriptExecutor:
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
    vo: str = None
    auto_convert: bool
    verbose: bool
    input_file: str
    LD_LIBRARY_PATH: str
    available_functions: dict

    def __init__(
        self,
        matlab_executable_script: str,
        auto_convert=True,
        verbose=False,
        input_file=f"{os.getcwd()}/input.mat",
        function_dict_location=None
    ) -> None:
        self.matlab_executable_script = matlab_executable_script
        self.auto_convert = auto_convert
        self.verbose = (verbose,)
        self.input_file = input_file
        self.path_setter = matlab_path_setter.MatlabPathSetter()
        self.path_setter.verify_paths()
        
        
        if function_dict_location:
            self.available_functions = create_script.json_to_dict(function_dict_location)

    def __printout(self, string: str):
        if self.verbose:
            print(string)

    @staticmethod
    def to_list(obj):
        """
        Convert a numpy array or a native Python data type to a list.
        Raise a ValueError if obj is a nested numpy array.
        """
        # If obj is a numpy array, check for nested numpy arrays
        if isinstance(obj, np.ndarray):
            if obj.dtype == object and any(isinstance(x, np.ndarray) for x in obj):
                raise ValueError("Nested numpy arrays are not supported.")
            return obj.tolist()
        # If obj is a list, check for nested numpy arrays
        elif isinstance(obj, list):
            if any(isinstance(x, np.ndarray) for x in obj):
                raise ValueError("Nested numpy arrays are not supported.")
            return obj
        # If obj is a non-list iterable (e.g., a tuple or set), convert it to a list
        elif isinstance(obj, Iterable):
            return list(obj)
        # If obj is a non-iterable object, return a single-item list
        else:
            return [obj]        
            

    def execute_script(self, function_name: str, output_count: int, *args):
        """Executes the specific script name witht he specified arguments.

        Requires the user to know how many outputs to extract.

        Args:
            function_name (str): The script name to run
            output_count (int): The number of outputs to request

        Returns:
            A tuple consisting of three values:
                - MATLAB return value
                - Full MATLAB return string
                - The result, as a key-value dictionary.
        """

        if type(args) is not list:
            print("Converting to list...")
            args = list(args)

        print(args)
        input = dict()
        input["function_name"] = function_name
        input["output_count"] = output_count

        varargin = np.empty((len(args),), dtype=object)

        for i, arg in enumerate(args):
            if self.auto_convert:
                if isinstance(arg, numbers.Number):
                    conversion_message = f'Input argument {i}: Converting argument to float, was {type(arg).__name__}'
                    arg = float(arg)
                elif isinstance(arg, list):
                    conversion_message = f'Input argument {i}: Found list, attempting conversion if number'
                    arg = [float(entry) if isinstance(entry, numbers.Number) else entry for entry in arg]
                else:
                    conversion_message = f'Input argument {i}: No conversion, type is {type(arg).__name__}'
        
                self.__printout(conversion_message)
            
            varargin[i] = arg

        input["varargin"] = varargin
        savemat("input.mat", input)
        self.__printout(input)
        custom_environment = os.environ.copy()

        stream = subprocess.Popen(
            [self.matlab_executable_script, self.input_file],
            env=custom_environment,
            stdout=PIPE,
        )
        exit_code = stream.wait()
        self.__printout(f"MATLAB exited with code: {exit_code}")
        matlab_output = stream.communicate()[0]
        if exit_code != 0:
            print('Error: Nonzero MATLAB exit code, no results returned!')
            return exit_code, matlab_output, None
        res = loadmat("results.mat", squeeze_me=True, simplify_cells=True)
        names, outputs = res["results"]
        # Due to how we squeeze and simplify the cells, the output array can be a numpy array in an odd way;
        # This is our best attempt at fixing the issue for now. 
        # If the return values are odd, this is likely the reason!
        print("Outputs are:")
        print('Type:', type(outputs))
        print('Complete value:', outputs)
        
        # if outputs.dtype == np.object_ and len(outputs) == len(names):
        #     outputs = [outputs[x] for x in range(len(outputs))]
        outputs = self.__class__.to_list(outputs)
            
        names = names.replace(",", " ").split()
        
        return exit_code, matlab_output, {x: y for x, y in zip(names, outputs)}
    
    def print_available_functions(self):
        for f in list(self.available_functions.keys()):
            print(f)
            print('Inputs:')
            for i in self.available_functions[f]['input']:
                print(f'  {i}')
            print('Outputs')
            for i in self.available_functions[f]['output']:
                print(f'  {i}')        
                    


if __name__ == "__main__":
    from pprint import pprint

    matlab_function = ScriptExecutor("./for_redistribution_files_only/covarep_function")
    pprint(matlab_function.execute_script("lpcrf2is", 1, 10))