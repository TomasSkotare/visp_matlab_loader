from abc import ABC
from functools import wraps
import importlib.util
from inspect import Parameter, Signature, signature
import inspect
import os
from typing import Dict, Callable, List, Tuple, Type
from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult

from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
from visp_matlab_loader.project.matlab_project import MatlabProject

def matlab_function(func):
    @wraps(func)
    def wrapper(self: MatlabProjectWrapper, *args, **kwargs):
        """
        This decorator is used for MATLAB functions. It performs the following:

        1. Validates that the first keyword argument is 'requested_outputs'.
        2. Binds the function's arguments and applies defaults.
        3. Ensures all arguments after 'requested_outputs' are named.
        4. Removes 'self' and 'requested_outputs' from the arguments.
        5. Overrides the MATLAB function's output count based on 'requested_outputs'.
        6. Executes the MATLAB function with the remaining arguments.
        7. Validates that the return type is MatlabExecutionResult.

        The original function's return value is ignored, and the result of this decorator is returned instead.
        """
        # Get the current function's name
        func_name = func.__name__
        # Check if the first keyword argument is 'requested_outputs'
        if list(kwargs.keys())[0] != 'requested_outputs':
            raise ValueError("The first argument must be 'requested_outputs'")

        # Get the current function's arguments
        bound_args = inspect.signature(func).bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        # Check if the rest of the arguments are named
        if args:
            raise ValueError("All arguments after 'requested_outputs' must be named")


        # Remove 'self' and 'requested_outputs' from the arguments
        args_without_requested_outputs = [v for k, v in bound_args.arguments.items() if k not in ['self', 'requested_outputs']]
              
        # Override the number of outputs, according to the requested_outputs argument
        this_matlab_function = self.matlab_project.functions[func_name]
        this_matlab_function.override_output_count(bound_args.arguments['requested_outputs'])
        
        result = this_matlab_function.execute(*args_without_requested_outputs)

        # Check if the return type is MatlabExecutionResult
        if not isinstance(result, MatlabExecutionResult):
            raise TypeError("Return type must be MatlabExecutionResult")
        return result

    wrapper.matlab_function = True # type: ignore
    return wrapper

def placeholder_result() -> MatlabExecutionResult:
    """
    Returns a dummy MatlabExecutionResult object with default values.

    Returns:
        MatlabExecutionResult: A dummy MatlabExecutionResult object.
    """
    return MatlabExecutionResult(
        return_code=0,
        execution_message="",
        function_name="",
        outputs={},
        project_name="",
        inputs=[]
    )

class MatlabProjectWrapper(ABC):
    
    def __init__(self, name: str, compiled_directory:str):
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
        methods = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if not attr_name.startswith('_') and callable(attr) and getattr(attr, 'matlab_function', False):
                sig = signature(attr)
                print('found signature', sig, 'for function', attr_name)
                parameters = list(sig.parameters.values())
                print('All parameter names:')
                for param in parameters:
                    print('\t', param.name)
                if len(parameters) == 0:
                    raise ValueError(f"Method {attr_name} has no parameters. The first parameter should be 'requested_outputs'.")

                if parameters[0].name != 'requested_outputs':
                    raise ValueError(f"Method {attr_name}'s first parameter is not 'requested_outputs', instead it is {parameters[0].name}.") 

                if sig.return_annotation.__name__ != 'MatlabExecutionResult':
                    raise TypeError(f"Method {attr_name} does not return a MatlabExecutionResult., instead it returns {sig.return_annotation}")
                methods[attr_name] = (attr, sig)
        return methods
    
    @staticmethod
    def from_directory(directory: str) -> List[Type['MatlabProjectWrapper']]:
        wrappers = []

        # Iterate over all files in the directory
        for filename in os.listdir(directory):
            # Check if the file is a Python file
            if filename.endswith('.py'):
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
    
 