"""
A class to run test cases on compiled projects.

Attributes:
    test_directory (str): Directory for the test cases.
    compiled_directory (str): Directory for the compiled projects.
    base_directory (str): Base directory.
    project_finder (CompiledProjectFinder): Finder for compiled projects.
"""

import os
import sys
from typing import List

# This allows the file to be run directory without installing the package
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

from .execute import compiled_project_executor
from .find_compiled_projects import CompiledProjectFinder, MatlabProject


class TestCase:
    """
    Create a test case file for a single test case in a project.

    This includes the function name, input and output values.
    """

    function_name: str = ""
    input_list: list = ""
    output_list: list = ""

    def __init__(self, function_name, input_list, output_list) -> None:
        self.function_name = function_name
        self.input_list = input_list
        self.output_list = output_list

    def __str__(self) -> str:
        input_str = "\n".join([f"{type(val).__name__}: {val}" for val in self.input_list])
        output_str = "\n".join([f"{type(val).__name__}: {val}" for val in self.output_list])
        return f"TestCase(function_name={self.function_name},\ninput_list=\n{input_str},\noutput_list=\n{output_str})"


class TestCaseRunner:
    """
    A class to run test cases on compiled projects.
    """

    project: MatlabProject
    project_finder: CompiledProjectFinder
    # Declare test cases as a list of TestCase objects
    test_cases: List[TestCase] = []

    def check_dirs_exists(self, directories):
        """Checks if the given directories exist."""
        return all([os.path.exists(x) for x in directories])

    def __init__(self, project: MatlabProject, verbose=True) -> None:
        """Initializes TestCaseRunner with directories and a project finder."""

        self.project = project
        self.verbose = verbose

        if not self.check_dirs_exists([self.project.test_case_directory, self.project.compiled_directory]):
            print("Error: one or more directories do not exist!")

        # Load all test cases, if any:
        self.test_cases = []
        for test in self.project.test_case_files:
            test_json = json_numpy.JsonNumpy(test)
            (
                function_name,
                input_list,
                output_list,
            ) = TestCaseRunner.convert_from_test_dict(test_json.read())
            self.test_cases.append(TestCase(function_name, input_list, output_list))

    @staticmethod
    def convert_from_test_dict(data):
        """Converts test data from a dictionary to a tuple."""
        function_name = data["function_name"]
        input_keys = sorted([k for k in data.keys() if "input" in k], key=lambda x: int(x.split("_")[1]))
        output_keys = sorted(
            [k for k in data.keys() if "output" in k],
            key=lambda x: int(x.split("_")[1]),
        )

        input_list = [data[k] for k in input_keys]
        output_list = [data[k] for k in output_keys]

        return function_name, input_list, output_list

    @staticmethod
    def convert_to_test_dict(function_name, input_list, output_list):
        """Converts test data from a tuple to a dictionary."""
        data = {}
        data["function_name"] = function_name

        for i, val in enumerate(input_list, start=1):
            data[f"input_{i}"] = val

        for i, val in enumerate(output_list, start=1):
            data[f"output_{i}"] = val

        return data

    def create_test_data(self, function_name, input_list, output_count):
        """Creates test data for a specific project and function."""

        script_executer = compiled_project_executor.ExecuteCompiledProject(self.project.binary_file)
        exit_code, matlab_output, return_value = script_executer.execute_script(
            function_name, output_count, *input_list
        )
        return (
            exit_code,
            matlab_output,
            self.__class__.convert_to_test_dict(function_name, input_list, return_value.values()),
        )


def main():
    """Main function to run test cases on compiled projects."""
    tcr = TestCaseRunner(base_directory=os.getcwd())
    print("\n")
    for project in tcr.project_finder.compiled_projects:
        print("Project name:", project.name)
        print("Project directory:", project.compiled_directory)
        for test_case in project.test_case_files:
            print("Test case:", test_case)
            data = json_numpy.load(test_case)
            (
                function_name,
                input_list,
                output_list,
            ) = TestCaseRunner.convert_from_test_dict(data)
            print("Executing function:", function_name)
            script_executer = compiled_project_executor.ExecuteCompiledProject(project.binary_file)
            exit_code, matlab_output, return_value = script_executer.execute_script(
                function_name, len(output_list), *input_list
            )
            print("Exit code:", exit_code)
            print("Matlab output:", matlab_output)
            print("Return value keys:", return_value.keys)

    exit_code, matlab_output, complete_test_dictionary = tcr.create_test_data(
        "get_next_thousand", "getnextthousand", [1], 1
    )
    print("This was the result:")
    print(complete_test_dictionary)


if __name__ == "__main__":
    main()
