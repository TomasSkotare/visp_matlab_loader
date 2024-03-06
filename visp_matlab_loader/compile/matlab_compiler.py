"""
This module contains functions for compiling MATLAB projects.

"""
import json
import os
import shlex
import shutil
# import numpy as np
import subprocess
import sys
import traceback

from visp_matlab_loader.mat_to_wrapper import create_script

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TODO: Why does this import fail if I don't do it this way?
from visp_matlab_loader.matlab_path_setter import MatlabPathSetter


class MATLABProjectCompiler:
    """
    Compiles a MATLAB project into a standalone executable.

    This class provides methods to ensure directories exist, get all subdirectories,
    write text to a file, create a directory, load functions from a JSON file,
    convert absolute paths to relative paths, and compile the project.

    Args:
        project_path (str): The path to the MATLAB project directory.
        output_path (str): The path to the output directory.
        path_setter (object, optional): An object that sets the MATLAB path. Defaults to None.
    """

    def ensure_directories_exist(self, directories):
        """
        Creates the given directories if they do not exist. 

        Raises a FileNotFoundError if the parent directory does not exist. Raises an OSError if the 
        directory cannot be created.

        Args:
            directories (list): List of directory paths to be created.

        Raises:
            FileNotFoundError: If the parent directory does not exist.
            OSError: If the directory cannot be created.
        """
        for directory in directories:
            parent_dir = os.path.dirname(directory)
            if not os.path.exists(parent_dir):
                raise FileNotFoundError(f"The parent directory {parent_dir} does not exist.")
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except OSError as e:
                    raise OSError(f"Could not create directory {directory}. Error: {str(e)}") from e

    # Property of project name, which is the final directory in the project_path:
    @property
    def project_name(self):
        return os.path.basename(self.project_path)

    def __init__(self, project_path: str, output_path: str, path_setter: MatlabPathSetter | None = None) -> None:
        project_path = os.path.abspath(project_path)
        output_path = os.path.abspath(output_path)

        self.project_path = project_path
        self.output_directory = output_path

        self.ensure_directories_exist([project_path, output_path])

        self.path_setter = path_setter or MatlabPathSetter()
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
            with open(file_path, "w", encoding="utf-8") as file:
                # Write the text to the file
                file.write(text)
        except (IOError, OSError, PermissionError) as e:
            # Print an error message if the file could not be opened or written to
            print(f"Unable to open or write to file {file_path}. Error: {str(e)}")

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

    def compile_project(self, verbose=False, force_output=False):
        """Compiles the project to a standalone executable.
        This function will create a wrapper script for the given project directory,
        and then compile it into a standalone executable.

        Args:
            verbose: bool - Whether to print additional status messages or not
            force_output: bool - Whether to overwrite the output file if it already exists
        """
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
        created_script = create_script.directory_to_script(
            self.project_path,
            verbose=verbose,
            save_function_location=os.path.join(self.output_directory, "functions.json"),
        )
        if created_script is None:
            return 1, "Error creating script"
        matlab_script, _ = created_script

        # Use the project name for the output wrapper file and write it
        project_output_file = os.path.join(self.output_directory, f"{self.project_name}_wrapper.m")
        self.write_text_to_file(project_output_file, matlab_script)

        # Get all subdirectories of the project directory
        if isinstance(self.project_path, list):
            project_dir = [os.path.abspath(x) for x in self.project_path if os.path.isdir(x)]
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
            project_output_file,
            self.output_directory,
            self.project_name,
            additional_dirs=project_dir,
            create_output_directory=True,
            force_output=force_output,
        )
        vprint("Compiled with code:", compiler_code)
        vprint("Message:", compiler_message)
        return compiler_code, compiler_message
    
    
    @staticmethod
    def compile_projects(source_path: str, 
                         output_path: str, 
                         force_output: bool = False,
                         path_setter: MatlabPathSetter| None = None) -> list[tuple[str, int, str]]:
        """Compile all projects in the source directory.
        
        Each project will be compiled into a separate directory in the output directory, with the same 
        name as the project.

        Args:
            source_path (str): The source path, containing separate subdirectories for each project.
            output_path (str): The output path, with one subdirectory created for each project.
            path_setter (MatlabPathSetter, optional): A path setter object. Defaults to None. Can be used if a specific
                MATLAB version is required.

        Returns:
            list[tuple[str, int, str]]: A tuple containing the project name, 
            the return code, and the compilation result.
        """
        print('Compiling project with source path:', source_path)
        print('Output path:', output_path)
        print('Force output:', force_output)
        print('Path setter:', path_setter)
        
        # Create a list to store the results
        results = []

        # Get all subdirectories of the project directory
        project_dirs = [
            os.path.abspath(os.path.join(source_path, x))
            for x in os.listdir(source_path)
            if os.path.isdir(os.path.join(source_path, x))
        ]
        
        # Loop through the directories and compile the projects
        for project_path in project_dirs:
            project_name = os.path.basename(project_path)
            print('Project is:', project_name)
            current_project_output = os.path.join(output_path, project_name)
            print('Creating output path: ', current_project_output)
            os.makedirs(current_project_output, exist_ok=True)
            
            compiler = MATLABProjectCompiler(
                project_path=os.path.join(source_path, project_name), 
                output_path=current_project_output,
                path_setter=path_setter
            )
            compiler_code, compiler_message = compiler.compile_project(force_output=force_output)
            results.append((project_name, compiler_code, compiler_message))

        return results



class MatlabCompiler:
    matlab_path: MatlabPathSetter

    def __init__(self, matlab_path=None):
        if not matlab_path:
            matlab_path = MatlabPathSetter()
        self.matlab_path = matlab_path

    @staticmethod
    def file_exists(path, filename):
        full_path = os.path.join(path, filename)
        return os.path.isfile(full_path)

    def compile(
        self,
        script_path,
        output_dir=None,
        output_file=None,
        additional_dirs=None,
        create_output_directory=False,
        force_output=False,
        verbose=False,
    ):
        """
        Compile a MATLAB script using the MATLAB Compiler (mcc).

        Args:
            script_path (str): The path to the MATLAB script to be compiled.
            output_dir (str, optional): The directory where the compiled files will be saved.
                If not provided, the current directory will be used.
            output_file (str, optional): The name of the compiled output file.
                If not provided, the name of the input script will be used.
            additional_dirs (list, optional): A list of additional directories to be included during compilation.
            create_output_directory (bool, optional): If True, the output directory will be created
                if it does not exist.
                If False and the output directory does not exist, an error will be returned. Default is False.
            force_output (bool, optional): If True, the output file will be overwritten if it already exists.
                If False and the output file already exists, an error will be returned. Default is False.
            verbose (bool, optional): If True, verbose output will be printed during compilation. Default is False.

        Returns:
            tuple: A tuple containing the return code and the compilation result.
                The return code is 0 for successful compilation and 1 for compilation failure.
                The compilation result includes the output result and error messages.

        Raises:
            subprocess.CalledProcessError: If the mcc command fails during compilation.

        """
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
            return 2, f"Output file {output_file} already exists in {output_dir}."

        if not os.path.isdir(output_dir):
            if create_output_directory:
                vprint("Creating output directory")
                os.makedirs(output_dir)
            else:
                return 1, f"Output directory {output_dir} does not exist."

        matlab_bin = self.matlab_path.mcc_binary

        command = [
            matlab_bin,
            "-m",
            "-v",
            "-o",
            output_file,
            "-d",
            output_dir,
            script_path,
        ]

        if additional_dirs:
            for directory in additional_dirs:
                command.extend(["-I", directory])

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            output_result = result.stdout
            output_error = result.stderr
            if output_error is None or len(output_error) == 0:
                output_error = "None"

            # Create a metadata file
            metadata = {
                "script_path": script_path,
                "output_dir": output_dir,
                "output_file": output_file,
                "additional_dirs": additional_dirs,
                "create_output_directory": create_output_directory,
                "command": command,
            }

            with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as file:
                json.dump(metadata, file, indent=4)

            # Copy the original input file to the output directory
            # Also catches same file error, when using the same directory for input and output
            try:
                shutil.copy(script_path, output_dir)
            except (IOError, shutil.SameFileError, PermissionError) as e:
                vprint(f"Error occurred: {str(e)}")
            vprint("Successful...")

            return (
                0,
                "Compilation successful.\nOutput result:\n" + output_result + "\nOutput error:\n" + output_error,
            )
        except subprocess.CalledProcessError as e:
            error_message = f"mcc command FAILED with message: {str(e)}"
            error_traceback = traceback.format_exc()
            return (
                1,
                (
                    f"Return code: {e.returncode}\n"
                    f"Error message: {error_message}\n"
                    f"Traceback: {error_traceback}\n"
                    f"Output:\n{e.output}\n\n"
                    f"Stderr:\n{e.stderr}"
                ),
            )
