"""
Module providing the `MatlabFunction` class for executing compiled MATLAB functions. 
Handles missing inputs and type mismatches during execution. 
Depends on numpy and visp_matlab_loader.
"""
from __future__ import annotations

from typing import List, OrderedDict

import numpy as np
from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult

from visp_matlab_loader.project.matlab_project import MatlabProject


class MatlabFunction:
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

    def override_output_count(self, count: int) -> None:
        assert count >= 0
        self._override_output_count = count

    def __init__(
        self,
        matlab_project: MatlabProject,
        function_name: str,
        inputs: OrderedDict[str, type],
        output_names: List[str],
    ) -> None:
        self.matlab_project = matlab_project
        self.function_name = function_name
        self.output_names = output_names
        self.inputs = inputs
        self._override_output_count = -1
        self._override_input_count = -1

    def execute(self, *args, **kwargs) -> MatlabExecutionResult:
        """
        Executes a MATLAB function with provided arguments and keyword arguments.

        This method validates the inputs, checks for missing values, verifies the types,
        and handles the execution of the MATLAB script.

        Parameters
        ----------
        *args : tuple
            Unnamed arguments for the function.
        **kwargs : dict
            Named arguments for the function.

        Returns
        -------
        The result of the MATLAB script execution as a MatlabExecutionResult.

        Raises
        ------
        ValueError
            If an unknown input is provided, if there are too many inputs,
            or if there are missing inputs in the input chain.
        """
        # Create ordered dict from inputs
        used_inputs = OrderedDict({k: None for k in self.inputs.keys()})

        # We allow them in order to be able to call the function without specifying the names
        for name, value in kwargs.items():
            if not name in used_inputs:
                raise ValueError(
                    f"Unknown input {name} for function {self.function_name},",
                    "expected {','.join(list(used_inputs.keys()))}",
                )
            used_inputs[name] = kwargs[name]

        # Fill in any missing inputs with unnamed args, in order:
        was_used = False
        for arg in args:
            for name, value in used_inputs.items():
                if value is None:
                    used_inputs[name] = arg
                    was_used = True
                    break
            if not was_used:
                raise ValueError(f"Too many inputs for function {self.function_name}")
            was_used = False

        # Check if there are "holes" in the inputs, where the value is none but followed by a real value:
        has_inputs = np.array([x is not None for x in used_inputs.values()])
        missing_inputs = [k for k, v in used_inputs.items() if v is None]

        if np.any(has_inputs[1:] & ~has_inputs[:-1]):
            raise ValueError(f"Missing in input chain (some inputs are missing): {missing_inputs}")

        # Remove any unused inputs
        used_inputs = OrderedDict({k: v for k, v in used_inputs.items() if v is not None})

        # Check that the types of the inputs are correct
        for name, expected_type in self.inputs.items():
            # Skip if we do not know the expected type
            if expected_type is type(None):
                # print("Skipping check", name, expected_type)
                continue
            if not isinstance(used_inputs[name], expected_type):
                print(f"Warning: Input {name} should be of type {expected_type.__name__}, but got ",
                      f"{type(kwargs[name]).__name__}")

        if self._override_output_count >= 0:
            requested_output_count = self._override_output_count
        else:
            requested_output_count = self.output_count

        return self.matlab_project.executor.execute_script(
            self.function_name, requested_output_count, *used_inputs.values()
        )

    # Allow for this class to be printed in a reasonable way:
    def __str__(self):
        return (
            f"MatlabFunction '{self.function_name}' from project "
            f"'{self.matlab_project.name}', with {len(self.inputs)} input(s) "
            f"({','.join(self.inputs)}) and {self.output_count} output(s) "
            f"({','.join(self.output_names)})."
        )
