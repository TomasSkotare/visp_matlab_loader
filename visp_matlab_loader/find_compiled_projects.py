import fnmatch
import os
from typing import List

from visp_matlab_loader.project.matlab_project import MatlabProject




def find_files(directory, pattern):
    for root, _, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


class CompiledProjectFinder:
    @property
    def found_projects(self) -> List[MatlabProject]:
        return self._compiled_projects

    def has_project(self, project_name) -> bool:
        return any([project.name == project_name for project in self._compiled_projects])

    def get_project(self, project_name) -> MatlabProject:
        for project in self._compiled_projects:
            if project.name == project_name:
                return project
        raise ValueError(f"Could not find project with name '{project_name}'")

    def __init__(self, directory, verbose=False) -> None:
        self._compiled_projects: list[MatlabProject] = []

        self.directory = directory
        # Check if the directory exists
        if not os.path.exists(self.directory):
            raise FileNotFoundError(f"No such directory: '{self.directory}'")

        self._compiled_projects = [MatlabProject(x) for x in find_files(self.directory, "*_wrapper.m")]

        if verbose:
            for wrapper_file in self._compiled_projects:
                print(wrapper_file.binary_file)


# Test main function
def main():
    # Get the directory of the current module
    current_module_path = os.path.dirname(os.path.realpath(__file__))
    # Get the parent directory of the current module path:
    parent_directory = os.path.dirname(current_module_path)
    # Assume files are in parent / tests / output:
    # library_directory = os.path.join(parent_directory, 'tests', 'output')

    # compiled_project_finder = CompiledProjectFinder(library_directory)


if __name__ == "__main__":
    main()
