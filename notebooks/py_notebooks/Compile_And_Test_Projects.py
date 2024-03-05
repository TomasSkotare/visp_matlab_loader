# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
#  Find installed MATLAB versions

# from visp_matlab_loader.matlab_compiler import MatlabVersionFinder, MatlabCompiler
from visp_matlab_loader.matlab_path_setter import MatlabPathSetter
matlab_path = MatlabPathSetter()
print(matlab_path.matlab_root)
if not matlab_path.verify_paths():
    raise Exception('Matlab paths are not set correctly')

# MatlabCompiler(finder).compile()


# %%
from visp_matlab_loader.compile.matlab_compiler import MATLABProjectCompiler
import os

MATLAB_LIBRARY_PATH = os.path.join(os.getcwd(), 'matlab', 'libraries')
MATLAB_COMPILED_PATH = os.path.join(os.getcwd(), 'matlab', 'compiled')

results = MATLABProjectCompiler.compile_projects(MATLAB_LIBRARY_PATH, MATLAB_COMPILED_PATH, force_output=False)
for project_path, exit_status, message in results:
    project_name = os.path.basename(project_path)
    if exit_status != 0:
        print(f'Error compiling {project_name} with message:\n\t{message}')
    else:
        print(f'Compiled {project_name} successfully')

# %%
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder

compiled_projects = CompiledProjectFinder(MATLAB_COMPILED_PATH)
for project in compiled_projects.found_projects:
    print(project)



# %%
# Now we have the compiled projects, and can check if any of them have any test data

from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult

def execute_projects(compiled_projects: CompiledProjectFinder) -> None:
    for project in compiled_projects.found_projects:
        print(f'Project {project.name}, test directory: {project.test_case_directory}')

        if not project.test_case_files:
            print('\tProject has no test data, skipping...')
            continue

        print('Project has test data\nTest case files:')
        for test_case in project.test_case_files:
            execution_result = MatlabExecutionResult.from_json(file=test_case)
            print(f'\t{test_case}\nExecution result of function: {execution_result.function_name}')

            matlab_function = project.functions.get(execution_result.function_name)
            if not matlab_function:
                print('Function not found')
                continue

            matlab_function.override_output_count(len(execution_result.outputs))
            print(f'Found function: {matlab_function}\nExecuting...')
            new_result = matlab_function.execute(*execution_result.inputs)

            if not new_result.compare_results(execution_result, verbose=True):
                print('Results do not match')
            else:
                print('Results match!')

execute_projects(compiled_projects)
            
            
