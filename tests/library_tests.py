import os
import shlex
import sys
import numpy as np

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from visp_matlab_loader import (
    create_script,
    matlab_compiler,
    execute_script,
    matlab_path_setter,
)

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


def get_all_subdirectories(dirs):
    all_dirs = set()

    for dir in dirs:
        normalized_dir = os.path.normpath(dir)
        for root, subdirs, files in os.walk(normalized_dir):
            if '.git' not in root:
                quoted_root = shlex.quote(root)
                all_dirs.add(quoted_root)

    return list(all_dirs)

def create_directory(directory_path):
    # Check if the directory does not exist
    if not os.path.exists(directory_path):
        # Create the directory
        os.makedirs(directory_path)
        
def load_functions(target_dir):
    """Load functions from a JSON file."""
    json_path = os.path.join(target_dir, "functions.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"No such file: '{json_path}'")
    return create_script.json_to_dict(json_path)

def select_random_function(functions):
    """Select a random function from the dictionary."""
    function_names = list(functions.keys())
    if not function_names:
        raise ValueError("No function names found.")
    return function_names[np.random.randint(0, len(function_names))]

def randomize_inputs(input_count):
    """Generate a list of random integers."""
    return [np.random.randint(0, 100) for _ in range(input_count)]

def execute_random_function(target_dir, project_name):
    """Execute a random function from a JSON file."""
    functions = load_functions(target_dir)
    random_function_name = select_random_function(functions)
    print("Random function:", random_function_name)

    input_count = len(functions[random_function_name]["input"])
    output_count = len(functions[random_function_name]["output"])
    print(
        "Function has inputs with name: ",
        functions[random_function_name]["input"],
        "And outputs with name: ",
        functions[random_function_name]["output"],
    )

    input_args = randomize_inputs(input_count)
    print("Randomized input arguments:", input_args)

    executable_path = os.path.join(target_dir, project_name)
    execute_script.ScriptExecutor(
        executable_path, function_dict_location=os.path.join(target_dir, "functions.json")
    ).execute_script(
        random_function_name, output_count, *input_args
    )        
        


def test_project(project_dir: str, target_dir: str):
    create_directory(target_dir)
    matlab_path_setter.MatlabPathSetter().verify_paths()
    matlab_script, functions = create_script.directory_to_script(
        project_dir,
        verbose=True,
        save_function_location=os.path.join(target_dir, "functions.json"),
    )

    # print(matlab_script)
    
    # Get the project name from the final directory in the path
    project_name = os.path.basename(os.path.normpath(project_dir))

    # Use the project name for the output file
    project_output_file = os.path.join(target_dir, f"{project_name}_wrapper.m")
    write_text_to_file(project_output_file, matlab_script)
    if isinstance(project_dir, list):
        project_dir = [os.path.abspath(x) for x in project_dir if os.path.isdir(x)]
    else:
        project_dir = [os.path.abspath(project_dir)]
    project_dir = get_all_subdirectories(project_dir)

    print("project_output_file:", project_output_file)
    print("target_dir:", target_dir)
    print("project_name:", project_name)
    print("additional_dirs:", project_dir)

    # Compile the script
    compiler_code, compiler_message = matlab_compiler.MatlabCompiler().compile(
        project_output_file, target_dir, project_name, additional_dirs=project_dir
    )
    print("Compiled with code:", compiler_code)
    print("Message:", compiler_message)

    print("Testing execution...")

    try:
        execute_random_function(target_dir, project_name)
    except Exception as e:
        print('Failed to execute function... This could mean nothing!\nMessage:', e)
        
    print("Done testing execution.")

def main():
    base_dir = "../matlab/libraries/"
    for name in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, name)):
            print(f"Testing {name}")
            test_project(os.path.join(base_dir, name), f"./{name}/")

if __name__ == "__main__":
    main()
