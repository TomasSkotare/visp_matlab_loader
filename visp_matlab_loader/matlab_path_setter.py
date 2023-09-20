import os
import glob


class MatlabPathSetter:
    def __init__(self, version=None):
        self.matlab_root = self.find_latest_matlab_or_runtime(version)
        self.set_ld_library_path()

    def find_latest_matlab_or_runtime(self, version):
        # Get a list of all MATLAB installations
        matlab_dirs = glob.glob("/usr/local/MATLAB/R20*")
        matlab_dirs.sort(
            reverse=True
        )  # Sort in reverse order to get the latest version first
        print("Available MATLAB installations:")
        for dir in matlab_dirs:
            print(dir)

        # Get a list of all MATLAB Runtime environments
        runtime_dirs = glob.glob("/usr/local/MATLAB/MATLAB_Runtime/R20*")
        runtime_dirs.sort(
            reverse=True
        )  # Sort in reverse order to get the latest version first
        print("Available MATLAB Runtime environments:")
        for dir in runtime_dirs:
            print(dir)

        # If a specific version was requested, try to use it
        if version is not None:
            version_dir = "/usr/local/MATLAB/" + version
            if version_dir in matlab_dirs or version_dir in runtime_dirs:
                return version_dir
            else:
                print(f"Error: Requested version {version} not found.")
                return None

        # If no specific version was requested, use the latest MATLAB installation or MATLAB Runtime environment
        if matlab_dirs:
            return matlab_dirs[0]
        if runtime_dirs:
            return runtime_dirs[0]
        else:
            return None

    def set_ld_library_path(self):
        if self.matlab_root is None:
            print("MATLAB installation or MATLAB Runtime environment not found.")
            return

        # Define the directories to add to LD_LIBRARY_PATH
        dirs_to_add = [
            os.path.join(self.matlab_root, "runtime/glnxa64"),
            os.path.join(self.matlab_root, "bin/glnxa64"),
            os.path.join(self.matlab_root, "sys/os/glnxa64"),
        ]

        # Get the current LD_LIBRARY_PATH
        ld_library_path = os.getenv("LD_LIBRARY_PATH", "")

        # Check if MATLAB path is already in LD_LIBRARY_PATH
        if any(dir_to_add in ld_library_path for dir_to_add in dirs_to_add):
            print("MATLAB path is already in LD_LIBRARY_PATH. no need to set it again.")
            return

        # Add the MATLAB directories to LD_LIBRARY_PATH
        for dir_to_add in dirs_to_add:
            if dir_to_add not in ld_library_path:
                ld_library_path = dir_to_add + ":" + ld_library_path

        # Set LD_LIBRARY_PATH
        os.environ["LD_LIBRARY_PATH"] = ld_library_path

        print(f"LD_LIBRARY_PATH set to: {ld_library_path}")

    def verify_paths(self):
        if self.matlab_root is None:
            print('Error: MATLAB installation or MATLAB Runtime environment not found!')
            return False
        
        # Get the current LD_LIBRARY_PATH
        ld_library_path = os.getenv("LD_LIBRARY_PATH", "")

        # Define the directories to check in LD_LIBRARY_PATH
        dirs_to_check = [
            os.path.join(self.matlab_root, "runtime/glnxa64"),
            os.path.join(self.matlab_root, "bin/glnxa64"),
            os.path.join(self.matlab_root, "sys/os/glnxa64"),
        ]

        # Check if the MATLAB directories are in LD_LIBRARY_PATH and exist
        for dir_to_check in dirs_to_check:
            if dir_to_check not in ld_library_path:
                print(f"Error: {dir_to_check} not found in LD_LIBRARY_PATH.")
                return False
            elif not os.path.isdir(dir_to_check):
                print(f"Error: {dir_to_check} does not exist.")
                return False

        print("All MATLAB paths found in LD_LIBRARY_PATH and exist.")
        return True


def main():
    # Create an instance of the class, which will find the latest MATLAB installation or MATLAB Runtime environment and set LD_LIBRARY_PATH
    # If you want to use a specific version, you can pass it as an argument, like this:
    # matlab_path_setter = MatlabPathSetter('R2023A')
    matlab_path_setter = MatlabPathSetter()

    # Verify that the MATLAB paths have been added to LD_LIBRARY_PATH
    matlab_path_setter.verify_paths()


if __name__ == "__main__":
    main()
