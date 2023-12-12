import fnmatch
import os
import glob


def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

# for filename in find_files('/path/to/directory', '*_wrapper.m'):
#     print(filename)
    
    
class MatlabProject:
    # Property for binary file for the matlab project
    @property
    def binary_file(self):
        # Get name without the '_wrapper.m' ending:
        binary_name = self.wrapper_file.replace('_wrapper.m', '')
        
        # Verify that it exists... 
        if not os.path.exists(binary_name):
            raise FileNotFoundError(f"No such file: '{binary_name}'")
        
        return binary_name
    
    @property
    def name(self):
        return os.path.basename(self.compiled_directory)
    
    @property
    def base_matlab_directory(self):
        return os.path.abspath(os.path.join(self.wrapper_file, '..', '..', '..'))
    
    @property
    def compiled_directory(self):
        """
        The directory for the compiled project, 
        where the binary and wrapper file resides
        """
        return os.path.abspath(os.path.dirname(self.wrapper_file))
    
    @property
    def code_directory(self):
        path = os.path.abspath(os.path.join(self.base_matlab_directory, 'libraries', self.name))
        if os.path.exists(path):
            return path
        print('could not find code directory at', path)
        return None

    
    @property
    def test_case_directory(self):
        # This should be two directories up from the wrapper directory,
        # under tests/project_name/test_cases
        test_case_dir =  os.path.abspath(os.path.join(self.base_matlab_directory, 'tests', self.name))
        if os.path.exists(test_case_dir):
            return test_case_dir
        return None
    
    @property
    def function_json(self):
        # function.json should be in the same directory as the binary file
        return os.path.join(self.compiled_directory, 'functions.json')
    
    
    @property
    def test_case_files(self):
        # Get all json files in the 'test_cases' directory:
        try:
            return glob.glob(os.path.join(self.test_case_directory, '*.json'))
        # And if no such directory exists, return an empty list
        except Exception:
            return []
    
    def __init__(self, project_wrapper_file) -> None:
        self.wrapper_file = os.path.abspath(project_wrapper_file)
        
    def __str__(self):
        message = (
                f"Compiled files for project '{self.name}:' \n\tLocated at '{self.compiled_directory}'.\n "
                f"\tWrapper file is '{self.wrapper_file}', \n\tBinary file is '{self.binary_file}'.\n "
                f"\tCode found at '{self.code_directory}'.\n"
                f"\tTest cases are located at '{self.test_case_directory}'."
                
            )
        return message

    def __repr__(self):
        return f"MatlabProjectFiles('{self.wrapper_file}')"        
        
        
    
class CompiledProjectFinder:
    directory: str = None
    compiled_projects: list[MatlabProject] = []
    
    def get_project(self, project_name):
        for project in self.compiled_projects:
            if project.name == project_name:
                return project
        return None
    
    def __init__(self, directory, verbose=False) -> None:
        
        self.directory = directory
        # Check if the directory exists
        if not os.path.exists(self.directory):
            raise FileNotFoundError(f"No such directory: '{self.directory}'")
        
        self.compiled_projects = [MatlabProject(x) for x in find_files(self.directory, '*_wrapper.m')]
        
        if verbose:
            for wrapper_file in self.compiled_projects:
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
        
        
    