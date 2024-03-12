"""
This module defines the MatlabProject class, which represents a MATLAB project and provides 
various properties and methods for managing and interacting with the project.

The MatlabProject class provides access to the project's binary file, name, base MATLAB directory, 
functions, compiled directory, code directory, test case directory, function JSON, test case files, and executor. 

It also includes methods for initializing functions, printing functions, and finding 
available functions within the project.
"""
from __future__ import annotations

import json
import os
from glob import glob
import re
from types import NoneType
from typing import TYPE_CHECKING, OrderedDict

if TYPE_CHECKING:
    from visp_matlab_loader.execute.compiled_project_executor import MatlabExecutor
    from visp_matlab_loader.project.matlab_function import MatlabFunction


class MatlabProject:
    """
    Represents a MATLAB project with various properties and methods to manage and interact with the project.

    The class provides properties to access the binary file, project name, base MATLAB directory,
    functions, compiled directory, code directory, test case directory, function JSON, test case files,
    and executor of the MATLAB project. It also provides methods to initialize functions, print functions,
    and find available functions within the project.

    Attributes:
        wrapper_file (str): The absolute path of the project wrapper file.
        _executioner (MatlabExecutor | None): The executor for the MATLAB project.
        _functions (dict): A dictionary of functions within the MATLAB project, accessed using the functions property
    """

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
    def required_matlab_version(self) -> str | None:
        # Return cached result if it exists
        if self._required_matlab_version is not None:
            return self._required_matlab_version

        # This should be in the same directory as the binary file
        file = os.path.join(self.compiled_directory, "readme.txt")
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as file:
                content = file.read()
                match = re.search(r"MATLAB Runtime\(R(\d{4}[ab])\)", content)
                if match:
                    # Cache the result
                    self._required_matlab_version = match.group(1)
                else:
                    self._required_matlab_version = None
        else:
            self._required_matlab_version = None
        return self._required_matlab_version

    @property
    def functions(self) -> dict[str, MatlabFunction]:
        if not self._functions:
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
    def test_case_files(self) -> list[str]:
        # Get all json files in the 'test_cases' directory:
        if self.test_case_directory is not None:
            return glob(os.path.join(self.test_case_directory, "*.json"))
        return []

    def _get_executioner(
        self,
        verbose: bool = False,
        auto_convert: bool = True,
    ) -> MatlabExecutor:
        if self._executioner is None:
            from visp_matlab_loader.execute.compiled_project_executor import (
                MatlabExecutor,
            )

            self._executioner = MatlabExecutor(
                self,
                auto_convert=auto_convert,
                function_json=self.function_json,
                return_inputs=True,
            )
        return self._executioner

    @property
    def can_execute(self):
        if self.required_matlab_version is None:
            return False
        return self.executor.supports_matlab_version(self.required_matlab_version)

    @property
    def executor(self) -> MatlabExecutor:
        if self._executioner is None:
            self._executioner = self._get_executioner()
        return self._executioner

    def __init__(self, project_wrapper_file: str) -> None:
        self.wrapper_file = os.path.abspath(project_wrapper_file)
        self._executioner: MatlabExecutor | None = None
        self._functions = {}
        self._required_matlab_version = None

    def __str__(self):
        message = (
            f"Compiled files for project '{self.name}:' \n\tLocated at '{self.compiled_directory}'.\n "
            f"\tWrapper file is '{self.wrapper_file}', \n\tBinary file is '{self.binary_file}'.\n "
            f"\tCode found at '{self.code_directory}'.\n"
            f"\tTest cases are located at '{self.test_case_directory}'.\n"
            f"\tRequired MATLAB version: {str(self.required_matlab_version)}\n"
            f"\tCan execute: {str(self.can_execute)}\n"
        )
        return message

    def __repr__(self):
        return f"MatlabProjectFiles('{self.wrapper_file}')"

    def initialize_functions(self) -> dict:
        try:
            with open(self.function_json, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return {}

        functions = {}
        # We do this here, as it cannot be loaded at the start for now.
        from visp_matlab_loader.project.matlab_function import MatlabFunction

        for function_name, info in data.items():
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
        possible_functions = [f for f in self._functions if search in f]
        return possible_functions
