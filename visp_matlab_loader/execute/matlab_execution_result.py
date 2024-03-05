import os
import tempfile

import json_tricks
import numpy as np


class MatlabExecutionResult:
    """
    Represents the result of a MATLAB execution.

    Attributes:
        return_code (int): The return code of the MATLAB execution.
        execution_message (str): The execution message of the MATLAB execution.
        function_name (str): The name of the MATLAB function that was executed.
        outputs (dict): The outputs of the MATLAB execution.

    Methods:
        success: Property that checks if the MATLAB execution was successful.
        __init__(return_code, execution_message, function_name, outputs): Initializes the
            MatlabExecutionResult object.
        __str__(): Returns a string representation of the MatlabExecutionResult object.
        __eq__(other): Checks if the MatlabExecutionResult object is equal to another object.
        __ne__(other): Checks if the MatlabExecutionResult object is not equal to another
            object.
        to_json(file=None): Converts the MatlabExecutionResult object to a JSON string. If a
            file is provided, writes the JSON string to the file.
        from_json(json_string=None, file=None): Class method that converts a JSON string to a
            MatlabExecutionResult object. If a file is provided, reads the JSON string from
            the file.
        verify_serialization(): Verifies that the MatlabExecutionResult object can be
            serialized and deserialized without losing information.
    """

    @property
    def success(self):
        return self.return_code == 0

    def __init__(
        self,
        return_code: int,
        execution_message: str,
        function_name: str,
        outputs: dict,
        project_name: str,
        inputs=[],  # Optional!
    ):
        self.return_code: int = return_code
        self.execution_message: str = execution_message
        self.function_name: str = function_name
        self.outputs: dict = outputs
        self.inputs: list = inputs
        self.project_name: str = project_name

    def __str__(self):
        return f"MatlabExecutionResult(return_code={self.return_code}, error_message={self.execution_message}, project_name={self.project_name} function_name={self.function_name}, outputs={self.outputs})"

    def __eq__(self, other):
        if isinstance(other, MatlabExecutionResult):
            return (
                self.return_code == other.return_code
                and self.execution_message == other.execution_message
                and self.function_name == other.function_name
                and self.project_name == other.project_name
                and MatlabExecutionResult.__compare_outputs(self.outputs, other.outputs)
            )
        return False
    
    def compare_results(self, other: "MatlabExecutionResult", verbose: bool = False):
        if isinstance(other, MatlabExecutionResult):
            return MatlabExecutionResult.__compare_outputs(self.outputs, other.outputs, verbose=verbose)
        raise ValueError("The other object is not a MatlabExecutionResult")

    @staticmethod
    def __compare_outputs(outputs1, outputs2, verbose=False):
        if type(outputs1) != type(outputs2):
            if verbose:
                print(f"Different types: {type(outputs1)} and {type(outputs2)}")
            return False

        if isinstance(outputs1, dict):
            if set(outputs1.keys()) != set(outputs2.keys()):
                if verbose:
                    print("Different keys in dictionaries")
                return False
            for key in outputs1:
                if not MatlabExecutionResult.__compare_outputs(outputs1[key], outputs2.get(key, None), verbose):
                    if verbose:
                        print(f"Different values for key {key}: {outputs1[key]} and {outputs2.get(key, None)}")
                    return False
        elif isinstance(outputs1, list):
            if len(outputs1) != len(outputs2):
                if verbose:
                    print("Different list lengths")
                return False
            for item1, item2 in zip(outputs1, outputs2):
                if not MatlabExecutionResult.__compare_outputs(item1, item2, verbose):
                    if verbose:
                        print(f"Different list items: {item1} and {item2}")
                    return False
        elif isinstance(outputs1, np.ndarray):
            if outputs1.dtype == object and outputs2.dtype == object:
                if outputs1.shape != outputs2.shape:
                    if verbose:
                        print("Different numpy array shapes")
                    return False
                for item1, item2 in zip(outputs1.flat, outputs2.flat):
                    if not MatlabExecutionResult.__compare_outputs(item1, item2, verbose):
                        if verbose:
                            print(f"Different numpy array items: {item1} and {item2}")
                        return False
            else:
                if not np.allclose(outputs1, outputs2, equal_nan=True, atol=0, rtol=0):
                    if verbose:
                        print(f"Different numpy arrays")
                    return False
        else:
            if outputs1 != outputs2:
                if verbose:
                    print(f"Different values: {outputs1} and {outputs2}")
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_json(self, file=None):
        json_string = json_tricks.dumps(self.__dict__, allow_nan=True, indent=4, sort_keys=True)
        if file:
            with open(file, "w") as f:
                f.write(str(json_string))
        else:
            return json_string

    @classmethod
    def from_json(cls, json_string=None, file=None):
        if file:
            with open(file, "r") as f:
                json_string = f.read()
        data = json_tricks.loads(json_string)
        data["outputs"] = dict(data["outputs"])
        return cls(**data)

    def verify_serialization(self):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as temp:
            temp_file_name = temp.name

        try:
            # Write to the temporary file
            self.to_json(temp_file_name)

            # Load from the temporary file
            loaded_self = type(self).from_json(file=temp_file_name)

            # Compare the results
            assert loaded_self == self, "Loaded result does not match the original result."

        finally:
            # Delete the temporary file
            os.remove(temp_file_name)
