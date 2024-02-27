from abc import ABC, abstractmethod
from glob import glob
import json
import os
from types import NoneType
from typing import Any, Dict, List, Optional

from visp_matlab_loader.execute.executor import Executor
from visp_matlab_loader.project.abstract_function import AbstractFunction


class MatlabProject:
    # Property for binary file for the matlab project
    @property
    def binary_file(self):
        # Get name without the '_wrapper.m' ending:
        binary_name = self.wrapper_file.replace("_wrapper.m", "")

        # Verify that it exists...
        if not os.path.exists(binary_name):
            raise FileNotFoundError(f"No such file: '{binary_name}'")

        return binary_name

    @property
    def name(self):
        return os.path.basename(self.compiled_directory)

    @property
    def base_matlab_directory(self):
        return os.path.abspath(os.path.join(self.wrapper_file, "..", "..", ".."))

    # @property
    # def matlab_function(self):
    #     # Saves a cached local copy, but loads if it doesn't exist
    #     if not hasattr(self, '_matlab_function'):
    #         self._matlab_function = MatlabFunctions(self)
    #     return self._matlab_function

    @property
    def functions(self) -> Dict[str,AbstractFunction]:
        if self._functions == {}:
            self._functions = self.initialize_functions()
        return self._functions

    @property
    def compiled_directory(self):
        """
        The directory for the compiled project,
        where the binary and wrapper file resides
        """
        return os.path.abspath(os.path.dirname(self.wrapper_file))

    @property
    def code_directory(self):
        path = os.path.abspath(
            os.path.join(self.base_matlab_directory, "libraries", self.name)
        )
        if os.path.exists(path):
            return path
        print("could not find code directory at", path)
        return None

    @property
    def test_case_directory(self):
        # This should be two directories up from the wrapper directory,
        # under tests/project_name/test_cases
        test_case_dir = os.path.abspath(
            os.path.join(self.base_matlab_directory, "tests", self.name)
        )
        if os.path.exists(test_case_dir):
            return test_case_dir
        return None

    @property
    def function_json(self):
        # function.json should be in the same directory as the binary file
        return os.path.join(self.compiled_directory, "functions.json")

    @property
    def test_case_files(self):
        # Get all json files in the 'test_cases' directory:
        if self.test_case_directory is not None:
            return glob(os.path.join(self.test_case_directory, "*.json"))
        else:
            # Handle the case where test_case_directory is None
            return []

    @property
    def executioner(self, 
                    verbose:bool = True, 
                    auto_convert:bool = True, 
                    input_file:str=f"{os.getcwd()}/input.mat"
                    ) -> Executor:
        from ..execute.compiled_project_executor import ExecuteCompiledProject

        if self._executioner is None:
            self._executioner = ExecuteCompiledProject(
                self,
                auto_convert=True,
                verbose=verbose,
                input_file=input_file,
                function_json=self.function_json,
                return_inputs=True,
            )
        return self._executioner

    def __init__(self, project_wrapper_file) -> None:
        self.wrapper_file = os.path.abspath(project_wrapper_file)
        self._executioner: Optional[Executor] = None
        self._functions = {}
        

    def __str__(self):
        message = (
            f"Compiled files for project '{self.name}:' \n\tLocated at '{self.compiled_directory}'.\n "
            f"\tWrapper file is '{self.wrapper_file}', \n\tBinary file is '{self.binary_file}'.\n "
            f"\tCode found at '{self.code_directory}'.\n"
            f"\tTest cases are located at '{self.test_case_directory}'."
        )
        return message

    def __repr__(self):
        return f"MatlabProjectFiles('{self.wrapper_file}')"

    def initialize_functions(self) -> dict:
        try:
            with open(self.function_json, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return {}

        functions = {}
        for function_name, info in data.items():
            functions[function_name] = MatlabFunction(
                self,
                function_name=function_name,
                inputs={x: NoneType for x in info["input"]},
                output_names=info["output"],
            )

        return functions

    def print_functions(self):
        for function in self._functions:
            print(function)

    def find_available_function(self, search: str):
        # Search for the function name in the available functions
        possible_functions = [f for f in self._functions.keys() if search in f]
        return possible_functions
    




class MatlabFunction(AbstractFunction):
    """This represents a MATLAB function that has been compiled and can be executed.

    Raises:
        ValueError: If there is a missing input when executing
        TypeError: If the input doesn't match the expected type when executing

    Returns:
        _type_: _description_
    """

    @property
    def output_count(self) -> int:
        return len(self.output_names)
    
    def override_output_count(self, count: int):
        self._override_output_count = count

    def __init__(
        self,
        matlab_project: MatlabProject,
        function_name: str,
        inputs: Dict[str, type],
        output_names: List[str],
    ) -> None:
        self.matlab_project = matlab_project
        self.function_name = function_name
        self.output_names = output_names
        self.inputs = inputs
        self._override_output_count = -1
        self._override_input_count = -1

    def execute(self, **kwargs):
        if self._override_output_count >= 0:
            outputs = self._override_output_count
        else:
            outputs = self.output_count
        # Check that all required inputs are present
        used_inputs = self.inputs.copy()
        for name in self.inputs.keys():
            if name not in kwargs:
                print(f"Missing expected input: {name}, removing from list of used inputs.")
                del used_inputs[name]
                

        # Check that the types of the inputs are correct
        for name, expected_type in used_inputs.items():
            # Skip if we do not know the expected type
            print(expected_type, type(kwargs[name]))
            if expected_type is type(None):
                print('Skipping check', name, expected_type)
                continue
            if not isinstance(kwargs[name], expected_type):
                print(
                    f"Input {name} should be of type {expected_type.__name__}, but got {type(kwargs[name]).__name__}"
                )

        return self.matlab_project.executioner.execute_script(
            self.function_name, outputs, *kwargs.values()
        )
        
    def execute_noname(self, *args):
        # merge args with known names to call execute with
        input_names = list(self.inputs.keys())
        if len(args) != len(input_names):
            print(f"Expected {len(input_names)} inputs, but got {len(args)}")
            print('Assuming remaining are optional inputs...')
            input_names = input_names[:len(args)]
        return self.execute(**{name: arg for name, arg in zip(input_names, args)})
        

    # Allow for this class to be printed in a reasonable way:
    def __str__(self):
        return (
            f"MatlabFunction '{self.function_name}' from project "
            f"'{self.matlab_project.name}', with {len(self.inputs)} input(s) "
            f"({','.join(self.inputs)}) and {self.output_count} output(s) "
            f"({','.join(self.output_names)})."
)
