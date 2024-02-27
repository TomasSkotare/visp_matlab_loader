from abc import ABC, abstractmethod
from typing import Any, Dict, List


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
        inputs: Dict[str, type],
        output_names: List[str],
    ) -> None:
        pass

    @abstractmethod
    def execute(self, outputs=None, **kwargs):
        pass

    @abstractmethod
    def execute_noname(self, outputs=None, *args):
        pass

    @abstractmethod
    def __str__(self):
        pass