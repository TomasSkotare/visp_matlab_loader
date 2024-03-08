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

import os
import sys

sys.path.append('..')
from visp_matlab_loader.matlab_path_setter import MatlabPathSetter

matlab_path = MatlabPathSetter()

print(matlab_path.matlab_root)
if not matlab_path.verify_paths():
    raise Exception('Matlab paths are not set correctly')

# MatlabCompiler(finder).compile()


# %%
from visp_matlab_loader.compile.matlab_compiler import MATLABProjectCompiler
import os

MATLAB_LIBRARY_PATH = os.path.join(os.getcwd(), '..', 'matlab', 'libraries')
MATLAB_COMPILED_PATH = os.path.join(os.getcwd(), '..', 'matlab', 'compiled')

results = MATLABProjectCompiler.compile_projects(MATLAB_LIBRARY_PATH, MATLAB_COMPILED_PATH, force_output=True)
for project_path, exit_status, message in results:
    project_name = os.path.basename(project_path)
    if exit_status != 0:
        print(f'Error compiling {project_name} with message:\n\t{message}')
    else:
        print(f'Compiled {project_name} successfully')

# %%



# %% [markdown]
# # Test compiled projects:

# %%

import sys
import logging

sys.path.append('..')

from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
from visp_matlab_loader.execute.matlab_execution_result import MatlabExecutionResult
from visp_matlab_loader.test.project_tests import TestMatlabProject

compiled_projects = CompiledProjectFinder(MATLAB_COMPILED_PATH, verbose=False)

for compiled_project in compiled_projects.found_projects:
    tester = TestMatlabProject(compiled_project)
    with tester.temporary_log_level('DEBUG'):  
        tester.test_project()
