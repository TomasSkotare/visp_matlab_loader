from abc import ABC, abstractmethod
from typing import Any, List, OrderedDict

from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult


class AbstractFunction(ABC):
    """This represents a function that has been compiled and can be executed.

    Raises:
        ValueError: If there is a missing input when executing
        TypeError: If the input doesn't match the expected type when executing
    """

    @property
    @abstractmethod
    def output_count(self) -> int:
        pass

    @abstractmethod
    def override_output_count(self, count: int):
        pass

    @abstractmethod
    def __init__(
        self,
        project: Any,
        function_name: str,
        # inputs should be in order of the function signature
        inputs: OrderedDict[str, type],
        output_names: List[str],
    ) -> None:
        pass

    @abstractmethod
    def execute(self, outputs=None, *args, **kwargs) -> MatlabExecutionResult:
        pass

    @abstractmethod
    def __str__(self):
        pass
