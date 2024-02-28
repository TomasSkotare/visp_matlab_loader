# Create a class called CovarrepWrapper

import os
import sys
import importlib


def find_and_import_package(package_name):
    # set current_dir to path of currently executing file:
    current_dir = os.path.dirname(os.path.realpath(__file__))
    while True:
        items_in_dir = os.listdir(current_dir)
        for item in items_in_dir:
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path) and item == package_name:
                sys.path.insert(0, current_dir)  # Add parent directory to sys.path
                package = importlib.import_module(package_name)
                return package
        parent_dir = os.path.dirname(current_dir)
        if current_dir == parent_dir:  # We've reached the root directory
            break
        current_dir = parent_dir
    return None  # Package not found


try:
    from visp_matlab_loader.execute.compiled_project_executor import MatlabExecutor
    from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
    from visp_matlab_loader.mat_to_wrapper.create_script import  extract_covarep_expected_functions
    from visp_matlab_loader.project.matlab_project import MatlabProject
except ModuleNotFoundError:
    print("Could not import visp_matlab_loader, attempting to import it from the local directory")
    visp_matlab_loader = find_and_import_package("visp_matlab_loader")
    if visp_matlab_loader is None:
        raise ImportError("Could not import visp_matlab_loader from the local directory")
    from visp_matlab_loader.execute.compiled_project_executor import MatlabExecutor
    from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
    from visp_matlab_loader.project.matlab_project import MatlabProject


class CovarepWrapper:
    # Add variables for each of the arguments to initialize the class
    covarrep_directory: str
    verbose: bool
    covarep_project: MatlabProject

    def __init__(self, covarep_directory, verbose=False):
        self.covarrep_directory = covarep_directory
        self.verbose = verbose
        self.expected_functions = extract_covarep_expected_functions(
            "http://covarep.github.io/covarep/contributions.html"
        )
        self._verify_correct()

    def _verify_correct(self):
        # Check that the inputs can be found

        # Check that the directory exists
        if not os.path.exists(self.covarrep_directory):
            raise ValueError(f"Directory {self.covarrep_directory} not found")

        # Check that covarrep can be loaded:
        compiled_projects = CompiledProjectFinder(directory=self.covarrep_directory)
        covarep = compiled_projects.get_project("covarep")
        if covarep is None:
            raise ValueError(f"Project not found in the specified folder, aborting")

        self.covarep_project = covarep

    def execute_function(self, function_name, output_count, inputs):
        executor = MatlabExecutor(
            self.covarep_project, return_inputs=True, verbose=self.verbose
        )
        print(
            f"Attempting to execute {function_name} with {output_count} outputs and {len(inputs)} inputs"
        )
        execution_result = executor.execute_script(function_name, output_count, *inputs)
        return execution_result


# Create default test code including main function:


def main(path="../matlab/compiled/"):
    # Create an instance of the CovarrepWrapper class
    covarrep = CovarepWrapper(covarep_directory=path, verbose=True)

    # Create a dictionary of inputs
    inputs = {
        "input1": 1,
        "input2": 2,
        "input3": 3,
    }

    # Execute the function
    result = covarrep.execute_function("covarrep_function", 1, inputs)

    # Save the result to a file
    result.to_json("output.json")

    # Print the result
    print(result)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Python script that takes a path as an input argument."
    )
    parser.add_argument("path", type=str, help="The path to the file")

    args = parser.parse_args()
    main(args.path)
