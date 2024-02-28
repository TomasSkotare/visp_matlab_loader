import json
import os
from glob import glob
from types import NoneType
from typing import Dict, LiteralString, OrderedDict


from visp_matlab_loader.execute.abstract_executor import AbstractExecutor
from visp_matlab_loader.project.abstract_function import AbstractFunction
from visp_matlab_loader.project.abstract_project import AbstractProject


class MatlabProject(AbstractProject):
    # Property for binary file for the matlab project
    @property
    def binary_file(self) -> str:
        # Get name without the '_wrapper.m' ending:
        binary_name = self.wrapper_file.replace("_wrapper.m", "")

        # Verify that it exists...
        if not os.path.exists(binary_name):
            raise FileNotFoundError(f"No such file: '{binary_name}'")

        return binary_name

    @property
    def name(self) -> str:
        return os.path.basename(self.compiled_directory)

    @property
    def base_matlab_directory(self) -> str:
        return os.path.abspath(os.path.join(self.wrapper_file, "..", "..", ".."))

    @property
    def functions(self) -> Dict[str, AbstractFunction]:
        if self._functions == {}:
            self._functions = self.initialize_functions()
        return self._functions

    @property
    def compiled_directory(self) -> str:
        """
        The directory for the compiled project,
        where the binary and wrapper file resides
        """
        return os.path.abspath(os.path.dirname(self.wrapper_file))

    @property
    def code_directory(self) -> str | None:
        path = os.path.abspath(os.path.join(self.base_matlab_directory, "libraries", self.name))
        if os.path.exists(path):
            return path
        return None

    @property
    def test_case_directory(self) -> str | None:
        # This should be two directories up from the wrapper directory,
        # under tests/project_name/test_cases
        test_case_dir = os.path.abspath(os.path.join(self.base_matlab_directory, "tests", self.name))
        if os.path.exists(test_case_dir):
            return test_case_dir
        return None

    @property
    def function_json(self) -> str:
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

    def get_executioner(
        self,
        verbose: bool = True,
        auto_convert: bool = True,
    ) -> AbstractExecutor:
        from ..execute.compiled_project_executor import ExecuteCompiledProject

        if self._executioner is None:
            self._executioner = ExecuteCompiledProject(
                self,
                auto_convert=auto_convert,
                verbose=verbose,
                function_json=self.function_json,
                return_inputs=True,
            )
        return self._executioner

    @property
    def executor(self) -> AbstractExecutor:
        if self._executioner is None:
            self._executioner = self.get_executioner()
        return self._executioner

    def __init__(self, project_wrapper_file) -> None:
        self.wrapper_file = os.path.abspath(project_wrapper_file)
        self._executioner: AbstractExecutor | None = None
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
            from .matlab_function import MatlabFunction

            functions[function_name] = MatlabFunction(
                self,
                function_name=function_name,
                inputs=OrderedDict({x: NoneType for x in info["input"]}),
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
