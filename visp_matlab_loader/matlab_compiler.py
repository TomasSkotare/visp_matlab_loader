"""
This module contains functions for compiling MATLAB projects.


"""
import json
import os
import shlex
import shutil
import sys
# import numpy as np
import subprocess
import traceback

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TODO: Why does this import fail if I don't do it this way?
from visp_matlab_loader import create_script, matlab_path_setter


class MATLABProjectCompiler:
    project_path: str = None
    output_directory: str = None   
    path_setter: matlab_path_setter.MatlabPathSetter = None
    
    def ensure_directories_exist(self, directories):
        """Creates the given directories if they do not exist. Raises an exception if the parent directory does not exist or if the directory cannot be created."""
        for directory in directories:
            parent_dir = os.path.dirname(directory)
            if not os.path.exists(parent_dir):
                raise FileNotFoundError(f"The parent directory {parent_dir} does not exist.")
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception as e:
                    raise Exception(f"Could not create directory {directory}. Error: {str(e)}")
    
    # Property of project name, which is the final directory in the project_path:
    @property
    def project_name(self):
        return os.path.basename(self.project_path)
    
    def __init__(self, project_path, output_path, path_setter=None) -> None:
        project_path = os.path.abspath(project_path)
        output_path = os.path.abspath(output_path)
        
        self.project_path = project_path
        self.output_directory = output_path
        
        self.ensure_directories_exist([project_path, output_path])
        
        self.path_setter = path_setter or matlab_path_setter.MatlabPathSetter()
        self.path_setter.verify_paths()
        
        
    @staticmethod
    def get_all_subdirectories(dirs):
        """
        Gets all subdirectories of the given directories.
        
        However, it will not include any directories named '.git'.
        
        Args:
            dirs: A list of directories to get subdirectories of.
        """
        all_dirs = set()

        for directory in dirs:
            normalized_dir = os.path.normpath(directory)
            for root, _, _ in os.walk(normalized_dir):
                if ".git" not in root:
                    quoted_root = shlex.quote(root)
                    all_dirs.add(quoted_root)

        return list(all_dirs)
    
    @staticmethod
    def write_text_to_file(file_path, text):
        try:
            # Open the file for writing
            with open(file_path, "w") as file:
                # Write the text to the file
                file.write(text)
        except IOError as e:
            # Print an error message if the file could not be opened
            print(f"Unable to open file {file_path}. Error: {str(e)}")
        except Exception as e:
            # Print an error message for any other exceptions
            print(f"An error occurred: {str(e)}")
            
    @staticmethod
    def create_directory(directory_path):
        # Check if the directory does not exist
        if not os.path.exists(directory_path):
            # Create the directory
            os.makedirs(directory_path)            
            
    @staticmethod            
    def load_functions(target_dir):
        """Load functions from a JSON file.
        This functions file is generated when using the MATLAB compiler function
        to compile a MATLAB script, and includes all available functions.        
        """
        json_path = os.path.join(target_dir, "functions.json")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"No such file: '{json_path}'")
        return create_script.json_to_dict(json_path)            
    
    @staticmethod
    def _convert_to_relative_paths(absolute_paths):
        current_path = os.getcwd()
        relative_paths = [os.path.relpath(path, current_path) for path in absolute_paths]
        return relative_paths    
    
    def compile_project(self, verbose=False):
        
        # Create the target directory if it does not exist
        self.create_directory(self.output_directory)
        
        vprint = print if verbose else lambda *args, **kwargs: None        
        
        # Convert the project directory to a MATLAB script.
        # This will create a "wrapper" script which enables the calling of any
        # function found in the directory or subdirectory.
        # This file can then be compiled into a standalone executable, which will
        # contain all the functions in the directory.
        #
        # Additionally, the script will create a JSON file which contains a dictionary
        # of the functions found in the directory, along with their input and output
        matlab_script, _ = create_script.directory_to_script(self.project_path, 
            verbose=verbose,
            save_function_location=os.path.join(self.output_directory, "functions.json"),
        )
        # Use the project name for the output wrapper file and write it
        project_output_file = os.path.join(self.output_directory, f"{self.project_name}_wrapper.m")
        self.write_text_to_file(project_output_file, matlab_script)
        
        # Get all subdirectories of the project directory
        if isinstance(self.project_path, list):
            project_dir = [os.path.abspath(x) for x in project_dir if os.path.isdir(x)]
        else:
            project_dir = [os.path.abspath(self.project_path)]
        project_dir = self.get_all_subdirectories(project_dir)
        
        vprint("project_output_file:", project_output_file)
        vprint("target_dir:", self.output_directory)
        vprint("project_name:", self.project_name)
        vprint("additional_dirs:")
        for _dir in self._convert_to_relative_paths(project_dir):
            vprint("  ", _dir)

        # Compile the script
        compiler_code, compiler_message = MatlabCompiler(self.path_setter).compile(
            project_output_file, self.output_directory, 
            self.project_name, 
            additional_dirs=project_dir, 
            create_output_directory=True
        )
        vprint("Compiled with code:", compiler_code)
        vprint("Message:", compiler_message)
        return compiler_code, compiler_message


class MatlabCompiler:
    matlab_path: matlab_path_setter.MatlabPathSetter
    
    def __init__(self, matlab_path=None):
        if not matlab_path:
            matlab_path = matlab_path_setter.MatlabPathSetter()
        self.matlab_path = matlab_path

    @staticmethod        
    def file_exists(path, filename):
        full_path = os.path.join(path, filename)
        return os.path.isfile(full_path)        

    def compile(self, script_path, output_dir=None, output_file=None, 
                additional_dirs=None, create_output_directory=False, 
                force_output=False, verbose=False):
        
        vprint = print if verbose else lambda *args, **kwargs: None        


        if not os.path.isfile(script_path):
            return 1, f"Input file {script_path} does not exist."



        # Get the script name without the extension
        script_name = os.path.splitext(os.path.basename(script_path))[0]

        # If output directory is not provided, use the current directory
        if not output_dir:
            output_dir = os.getcwd()

        # If output file name is not provided, use the input script name
        if not output_file:
            output_file = script_name

        if not force_output and self.__class__.file_exists(output_dir, output_file):
            return 1, f"Output file {output_file} already exists in {output_dir}."
        
        if not os.path.isdir(output_dir):
            if create_output_directory:
                vprint('Creating output directory')
                os.makedirs(output_dir)
            else:
                return 1, f"Output directory {output_dir} does not exist."

        matlab_bin = self.matlab_path.mcc_binary

        command = [matlab_bin, '-m', '-v', '-o', output_file, '-d', output_dir, script_path]

        if additional_dirs:
            for directory in additional_dirs:
                command.extend(['-I', directory])

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            output_result = result.stdout
            output_error = result.stderr
            if output_error is None or len(output_error) == 0:
                output_error = 'None'
            
            # Create a metadata file
            metadata = {
                'script_path': script_path,
                'output_dir': output_dir,
                'output_file': output_file,
                'additional_dirs': additional_dirs,
                'create_output_directory': create_output_directory,
                'command': command
            }

            with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=4)

            # Copy the original input file to the output directory
            # Also catches same file error, when using the same directory for input and output
            try:
                shutil.copy(script_path, output_dir)
            except Exception as e:
                vprint(f"Error occurred: {str(e)}")
            vprint('Successful...')

            return 0, "Compilation successful.\nOutput result:\n" + output_result + "\nOutput error:\n" + output_error
        except subprocess.CalledProcessError as e:
            error_message = f"mcc command FAILED with message: {str(e)}"
            error_traceback = traceback.format_exc()
            return 1, f"Return code: {e.returncode}\nError message: {error_message}\nTraceback: {error_traceback}\nOutput:\n{e.output}\n\nStderr:\n{e.stderr}"


# def select_random_function(functions):
#     """Select a random function from the dictionary."""
#     function_names = list(functions.keys())
#     if not function_names:
#         raise ValueError("No function names found.")
#     return function_names[np.random.randint(0, len(function_names))]


# def randomize_inputs(input_count):
#     """Generate a list of random integers."""
#     return [np.random.randint(0, 100) for _ in range(input_count)]


# def execute_random_function(target_dir, project_name):
#     """Execute a random function from a JSON file."""
#     functions = load_functions(target_dir)
#     random_function_name = select_random_function(functions)
#     print("Random function:", random_function_name)

#     input_count = len(functions[random_function_name]["input"])
#     output_count = len(functions[random_function_name]["output"])
#     print(
#         "Function has inputs with name: ",
#         functions[random_function_name]["input"],
#         "And outputs with name: ",
#         functions[random_function_name]["output"],
#     )

#     input_args = randomize_inputs(input_count)
#     print("Randomized input arguments:", input_args)

#     executable_path = os.path.join(target_dir, project_name)
#     execute_script.ScriptExecutor(
#         executable_path,
#         function_dict_location=os.path.join(target_dir, "functions.json"),
#     ).execute_script(random_function_name, output_count, *input_args)



    





# def test_script(target_dir, project_name):
#     print("Testing execution...")

#     try:
#         execute_random_function(target_dir, project_name)
#     except Exception as e:
#         print("Failed to execute function... This could mean nothing!\nMessage:", e)

#     print("Done testing execution.")


# def main():
#     base_dir = "./matlab/libraries/"
#     for name in os.listdir(base_dir):
#         if os.path.isdir(os.path.join(base_dir, name)):
#             print(f"Testing {name}")
#             compile_project(os.path.join(base_dir, name), f"./tests/output/{name}/")


# if __name__ == "__main__":
#     main()
