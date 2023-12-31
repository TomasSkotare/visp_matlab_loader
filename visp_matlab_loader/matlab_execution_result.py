import numpy as np
import json_tricks


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
        __init__(return_code, execution_message, function_name, outputs): Initializes the MatlabExecutionResult object.
        __str__(): Returns a string representation of the MatlabExecutionResult object.
        __eq__(other): Checks if the MatlabExecutionResult object is equal to another object.
        __ne__(other): Checks if the MatlabExecutionResult object is not equal to another object.
        to_json(file=None): Converts the MatlabExecutionResult object to a JSON string. If a file is provided, writes the JSON string to the file.
        from_json(json_string=None, file=None): Class method that converts a JSON string to a MatlabExecutionResult object. If a file is provided, reads the JSON string from the file.
    """

    return_code: int
    execution_message: str
    function_name: str
    outputs: dict
    inputs: list

    @property
    def success(self):
        return self.return_code == 0

    def __init__(
        self,
        return_code: int,
        execution_message: str,
        function_name: str,
        outputs: dict,
        inputs = [],  # Optional!
    ):
        self.return_code = return_code
        self.execution_message = execution_message
        self.function_name = function_name
        self.outputs = outputs
        self.inputs = inputs

    def __str__(self):
        return f"MatlabExecutionResult(return_code={self.return_code}, error_message={self.execution_message}, function_name={self.function_name}, outputs={self.outputs})"

    def __eq__(self, other):
        if isinstance(other, MatlabExecutionResult):
            return (
                self.return_code == other.return_code
                and self.execution_message == other.execution_message
                and self.function_name == other.function_name
                and self.__class__.__compare_outputs(self.outputs, other.outputs)
            )
        else:
            return False

    @staticmethod
    def __compare_outputs(outputs1, outputs2, verbose=False):
        if type(outputs1) != type(outputs2):
            if verbose:
                print(f"Different types: {type(outputs1)} and {type(outputs2)}")
            return False

        if isinstance(outputs1, dict):
            if set(outputs1.keys()) != set(outputs2.keys()):
                if verbose:
                    print(f"Different keys in dictionaries")
                return False
            for key in outputs1:
                if not __class__.__compare_outputs(
                    outputs1[key], outputs2.get(key, None), verbose
                ):
                    if verbose:
                        print(
                            f"Different values for key {key}: {outputs1[key]} and {outputs2.get(key, None)}"
                        )
                    return False
        elif isinstance(outputs1, list):
            if len(outputs1) != len(outputs2):
                if verbose:
                    print(f"Different list lengths")
                return False
            for item1, item2 in zip(outputs1, outputs2):
                if not __class__.__compare_outputs(item1, item2, verbose):
                    if verbose:
                        print(f"Different list items: {item1} and {item2}")
                    return False
        elif isinstance(outputs1, np.ndarray):
            if outputs1.dtype == object and outputs2.dtype == object:
                if outputs1.shape != outputs2.shape:
                    if verbose:
                        print(f"Different numpy array shapes")
                    return False
                for item1, item2 in zip(outputs1.flat, outputs2.flat):
                    if not __class__.__compare_outputs(item1, item2, verbose):
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
        json_string = json_tricks.dumps(
            self.__dict__, allow_nan=True, indent=4, sort_keys=True
        )
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
