from abc import ABC, abstractmethod

from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult


class AbstractExecutor(ABC):
    @abstractmethod
    def execute_script(self, function_name: str, output_count: int, *args) -> MatlabExecutionResult:
        pass

    @abstractmethod
    def __init__(
        self,
        matlab_project,
        auto_convert,
        verbose,
        input_file,
        function_json,
        return_inputs,
    ):
        pass
