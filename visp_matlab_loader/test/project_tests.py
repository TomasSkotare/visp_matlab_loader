from contextlib import contextmanager
from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult
from visp_matlab_loader.project.matlab_project import MatlabProject

import logging

logger = logging.getLogger(__name__)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class TestMatlabProject:
    @property
    def test_case_files(self) -> list[str]:
        return self.project.test_case_files

    def __init__(self, project: MatlabProject) -> None:
        self.project = project

    def test_project(
        self,
    ) -> list[tuple[str, MatlabExecutionResult, MatlabExecutionResult]]:
        project = self.project

        if not project.test_case_files:
            logger.warning(f"Project {project.name} has no test data, skipping...")
            return []
        logger.info(f"Project {project.name}, test directory: {project.test_case_directory}")
        logger.debug(f"Available functions: {project.functions.keys()}")

        logger.info("Project has test data\nTest case files:")
        test_results = []
        for test_case in project.test_case_files:
            test_case_execution = MatlabExecutionResult.from_json(file=test_case)
            logger.info(f"\t{test_case}\nExecution result of function: {test_case_execution.function_name}")

            matlab_function = project.functions.get(test_case_execution.function_name)
            if not matlab_function:
                logger.warning(
                    f"Function {test_case_execution.function_name} not found in the project {project.name}! Skipping..."
                )
                continue

            matlab_function.override_output_count(len(test_case_execution.outputs))
            logger.info(f"Found function: {matlab_function}\nExecuting...")
            new_result = matlab_function.execute(*test_case_execution.inputs)

            if not new_result.compare_results(test_case_execution):
                logger.warning("Results do not match")
            else:
                logger.info("Results match!")
            test_results.append((test_case, test_case_execution, new_result))

        return test_results

    @contextmanager
    def temporary_log_level(self, level):
        old_level = logger.level
        logger.setLevel(level)
        try:
            yield
        finally:
            logger.setLevel(old_level)
