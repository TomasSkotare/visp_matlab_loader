import os
import subprocess
import os
import re

import shutil
import json
import traceback


class MatlabVersionFinder:
    def __init__(self):
        self.matlab_dir = '/usr/local/MATLAB'
        versions = self.find_versions(self.matlab_dir)
        self.latest_matlab_version = self.select_version(versions)

    def find_versions(self, directory):
        versions = [d for d in os.listdir(directory) if re.match(r'^R\d{4}[ab]$', d)]
        versions.sort(reverse=True)
        return versions

    def select_version(self, versions, version=None):
        if version and version in versions:
            return version
        else:
            return versions[0]
        
    @property
    def latest_version_path(self):
        return os.path.join(self.matlab_dir, self.latest_matlab_version)        




class MatlabCompiler:
    def __init__(self, matlab_version_finder=None):
        if not matlab_version_finder:
            matlab_version_finder = MatlabVersionFinder()
        self.finder = matlab_version_finder

    @staticmethod        
    def file_exists(path, filename):
        full_path = os.path.join(path, filename)
        return os.path.isfile(full_path)        

    def compile(self, script_path, output_dir=None, output_file=None, additional_dirs=None, create_output_directory=False, force_output=False):
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
                print('Creating output directory')
                os.makedirs(output_dir)
            else:
                return 1, f"Output directory {output_dir} does not exist."

        matlab_dir = self.finder.latest_version_path
        matlab_bin = os.path.join(matlab_dir, 'bin', 'mcc')

        command = [matlab_bin, '-m', '-v', '-o', output_file, '-d', output_dir, script_path]

        if additional_dirs:
            for dir in additional_dirs:
                command.extend(['-I', dir])

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
                print(f"Error occurred: {str(e)}")
            print('Successful...')

            return 0, "Compilation successful.\nOutput result:\n" + output_result + "\nOutput error:\n" + output_error
        except subprocess.CalledProcessError as e:
            error_message = f"mcc command FAILED with message: {str(e)}"
            error_traceback = traceback.format_exc()
            return 1, f"Return code: {e.returncode}\nError message: {error_message}\nTraceback: {error_traceback}\nOutput:\n{e.output}\n\nStderr:\n{e.stderr}"

def main(script='../matlab/libraries/voice_analysis_toolbox/voice_analysis_directory.m', output_dir='./voice_analysis/', output_file='voice_analysis_output', additional_dirs=None):
    finder = MatlabVersionFinder()
    versions = finder.find_versions(finder.matlab_dir)
    selected_version = finder.select_version(versions)
    finder.matlab_dir = os.path.join(finder.matlab_dir, selected_version)

    compiler = MatlabCompiler(finder)
    status, message = compiler.compile(script, output_dir, output_file, additional_dirs)
    print(f"Status: {status}, Message: {message}")

if __name__ == "__main__":
    main()