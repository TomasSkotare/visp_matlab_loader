import importlib.util
import inspect
import os
from abc import ABC
from functools import wraps
from inspect import Signature, signature
from typing import Callable, Dict, List, Tuple, Type

from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder


def default_args(local_vars, exclude=None):
    if exclude is None:
        exclude = ["self"]
    # Create a copy of the local_vars dictionary
    local_vars_copy = local_vars.copy()

    # Remove excluded keys from the dictionary
    for key in exclude:
        local_vars_copy.pop(key, None)

    # Separate positional and keyword arguments
    # args = tuple(local_vars_copy.values())
    kwargs = local_vars_copy

    return (), kwargs


class MatlabProjectWrapper(ABC):
    def __init__(self, name: str, compiled_directory: str):
        self._name = name
        self._compiled_directory = compiled_directory

        found_projects = CompiledProjectFinder(self._compiled_directory)
        if not found_projects.has_project(self._name):
            raise ValueError(f"Could not find project with name '{self._name}'")
        self.matlab_project = found_projects.get_project(self._name)
        self._matlab_functions = None

    @property
    def name(self):
        return self._name

    @property
    def compiled_directory(self):
        return self._compiled_directory

    # @property
    # def functions(self) -> Dict[str, Callable]:
    #     if not hasattr(self, '_functions'):
    #         self._functions = self.populate_functions()
    #     return self._functions

    def populate_functions(self) -> Dict[str, Tuple[Callable, Signature]]:
        """
        This method populates a dictionary with the callable methods of the instance that are marked
        as MATLAB functions. The dictionary keys are the method names, and the values are tuples containing
        the method itself and its signature. The method checks for specific conditions:
        each method must have at least one parameter named 'requested_outputs', and the return type
        must be 'MatlabExecutionResult'.

        If these conditions are not met, the method raises a ValueError or TypeError as appropriate.
        """
        methods = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if not attr_name.startswith("_") and callable(attr) and getattr(attr, "matlab_function", False):
                sig = signature(attr)
                print("found signature", sig, "for function", attr_name)
                parameters = list(sig.parameters.values())
                print("All parameter names:")
                for param in parameters:
                    print("\t", param.name)
                if len(parameters) == 0:
                    raise ValueError(
                        f"Method {attr_name} has no parameters. The first parameter should be 'requested_outputs'."
                    )

                if parameters[0].name != "requested_outputs":
                    raise ValueError(
                        f"Method {attr_name}'s first parameter is not 'requested_outputs',",
                        "instead it is {parameters[0].name}.",
                    )

                if sig.return_annotation.__name__ != "MatlabExecutionResult":
                    raise TypeError(
                        f"Method {attr_name} does not return a MatlabExecutionResult.",
                        ", instead it returns {sig.return_annotation}",
                    )
                methods[attr_name] = (attr, sig)
        return methods

    @staticmethod
    def from_directory(directory: str) -> List[Type["MatlabProjectWrapper"]]:
        wrappers = []

        # Iterate over all files in the directory
        for filename in os.listdir(directory):
            # Check if the file is a Python file
            if filename.endswith(".py"):
                # Create the full file path
                file_path = os.path.join(directory, filename)

                # Create a module spec from the file path
                spec = importlib.util.spec_from_file_location(filename[:-3], file_path)

                if spec is None:
                    continue

                # Create a module from the spec
                module = importlib.util.module_from_spec(spec)

                if module is None or spec.loader is None:
                    continue
                spec.loader.exec_module(module)

                # Iterate over all objects in the module
                for _, obj in inspect.getmembers(module):
                    # Check if the object is a class and a subclass of MatlabProjectWrapper
                    if inspect.isclass(obj) and issubclass(obj, MatlabProjectWrapper):
                        # Add the class to the list of wrappers
                        wrappers.append(obj)

        return wrappers


def matlab_function(func):
    """
    A decorator for MATLAB project functions. It modifies arguments, checks for 'requested_outputs' keyword,
    overrides output count, executes the MATLAB function, and validates the return type.

    Parameters:
    func: The function to be decorated, expected to return modified arguments for the MATLAB function.

    Returns:
    wrapper: The decorated function.
    """

    @wraps(func)
    def wrapper(self: MatlabProjectWrapper, *args, **kwargs):
        # Allow the calling function to perform changes (i.e. fix column/row vectors, etc.)
        modified_args, modified_kwargs = func(self, *args, **kwargs)

        # Get the current function's name
        func_name = func.__name__

        # Check if 'requested_outputs' is in the keyword arguments
        if "requested_outputs" not in modified_kwargs:
            raise ValueError("The argument 'requested_outputs' must be defined")

        # Remove 'self' and 'requested_outputs' from the arguments
        kwargs_without_self_and_requested_outputs = {
            k: v for k, v in modified_kwargs.items() if k not in ["self", "requested_outputs"]
        }

        # Override the number of outputs, according to the requested_outputs argument
        matlab_func = self.matlab_project.functions[func_name]
        matlab_func.override_output_count(modified_kwargs["requested_outputs"])

        # Execute the function with the remaining arguments
        result = matlab_func.execute(*modified_args, **kwargs_without_self_and_requested_outputs)

        # Check if the return type is MatlabExecutionResult
        if not isinstance(result, MatlabExecutionResult):
            raise TypeError("Return type must be MatlabExecutionResult")
        return result

    return wrapper
