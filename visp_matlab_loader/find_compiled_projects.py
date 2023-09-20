import fnmatch
import os


def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

for filename in find_files('/path/to/directory', '*_wrapper.m'):
    print(filename)
    
    
class WrapperFile:
    # Property for binary file for the wrapper file
    @property
    def binary_file(self):
        # Get name without the '_wrapper.m' ending:
        binary_name = self.wrapper_file.replace('_wrapper.m', '')
        
        # Verify that it exists... 
        if not os.path.exists(binary_name):
            raise FileNotFoundError(f"No such file: '{binary_name}'")
        
        return binary_name
    
    @property
    def wrapper_directory(self):
        return os.path.dirname(self.wrapper_file)
    
    @property
    def function_json(self):
        # function.json should be in the same directory as the wrapper file
        return os.path.join(self.wrapper_directory, 'function.json')
        
    
    
    def __init__(self, wrapper_file) -> None:
        self.wrapper_file = wrapper_file
        
    
class CompiledProjectFinder:
    directory: str = None
    
    def __init__(self, directory) -> None:
        
        self.directory = directory
        # Check if the directory exists
        if not os.path.exists(self.directory):
            raise FileNotFoundError(f"No such directory: '{self.directory}'")
        
        self.wrapper_files = [WrapperFile(x) for x in find_files(self.directory, '*_wrapper.m')]
        
        print('Found the following wrapper files:')
        for wrapper_file in self.wrapper_files:
            print(wrapper_file.binary_file)
            
    
        
# Test main function
def main():
    # Get the directory of the current module
    current_module_path = os.path.dirname(os.path.realpath(__file__))
    # Get the parent directory of the current module path:
    parent_directory = os.path.dirname(current_module_path)
    # Assume files are in parent / tests / output:
    library_directory = os.path.join(parent_directory, 'tests', 'output')
    
    compiled_project_finder = CompiledProjectFinder(library_directory)
    
    

if __name__ == "__main__":
    main()
        
        
    