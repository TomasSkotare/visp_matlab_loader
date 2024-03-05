# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
from visp_matlab_loader.compile.matlab_compiler import MATLABProjectCompiler
import os

MATLAB_LIBRARY_PATH = os.path.join(os.getcwd(), 'matlab', 'libraries')
MATLAB_COMPILED_PATH = os.path.join(os.getcwd(), 'matlab', 'compiled')

# Verify path exists
if not os.path.exists(MATLAB_LIBRARY_PATH):
    raise Exception('Matlab library path does not exist: {}'.format(MATLAB_LIBRARY_PATH))

if not os.path.exists(MATLAB_COMPILED_PATH):    
    os.makedirs(MATLAB_COMPILED_PATH)

for name in os.listdir(MATLAB_LIBRARY_PATH):
    if os.path.isdir(os.path.join(MATLAB_LIBRARY_PATH, name)):
        print('Compiling {}'.format(name))
        compiler = MATLABProjectCompiler(project_path=os.path.join(MATLAB_LIBRARY_PATH, name), 
                                         output_path=os.path.join(MATLAB_COMPILED_PATH, name)) # Here we would add a MatlabPathSetter if we want to specify which compiler to use!
        compiler_code, compiler_message = compiler.compile_project(verbose=False, force_output=True)
        if compiler_code != 0:
            if compiler_code == 2:
                print(f'Project: {name} was already compiled')
            else:
                print(f'Error compiling project: {name}, compiler message was: {compiler_message}')
        else:
            print(f'Successfully compiled project: {name}')

# %%
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder

projects = CompiledProjectFinder('./matlab/compiled')

vat = projects.get_project('get_next_thousand')

print(vat)

f = vat.functions['getnextthousand']
print(f)

result = f.execute(float(1000))

print(result)
if result is not None:
    print(result.outputs)

result.verify_serialization()


# %% [markdown]
#

# %%
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
import numpy as np
projects = CompiledProjectFinder('./matlab/compiled')

vat = projects.get_project('covarep')

print(vat)

f = vat.functions['sin_analysis']
print(f)
# f.override_output_count(2)

wav = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

# Set the sampling frequency as a single number
fs = 44100  # 44.1 kHz is a common sampling frequency in audio processing

# Create a 2D numpy array for f0s
# The first column is time instants and the second column is the corresponding f0 values
f0s = np.array([[0.0, 440], [0.01, 440], [0.02, 440], [0.03, 440], [0.04, 440]])


result = f.execute(wav, fs, f0s)

print(result)


# %%
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
import numpy as np
projects = CompiledProjectFinder('./matlab/compiled')

vat = projects.get_project('voice_analysis_toolbox')

print(vat)

f = vat.functions['voice_analysis_modified']
print(f)
# f.override_output_count(2)

result = f.execute('/home/tomas/Projects/visp_matlab_loader/reference/audio_reference/test_tone.wav', 
                          {'start_time':1.5, 
                            'dfa_scaling':np.array([10,70,90,110,130,150,170,190],dtype=np.float64).reshape((-1, 1))
                           })


print(result)
result.verify_serialization()
print('Finished without errors!')

# %%
import numpy as np 

import matlab.wrappers.covarrep

cov = matlab.wrappers.covarrep.covarep('./matlab/compiled/covarep')

funcs = cov.populate_functions()
# print(funcs['sin_analysis'])
# callable, signature = funcs['sin_analysis']
# callable(requested_outputs = 3, 
cov.sin_analysis(requested_outputs=2, 
                        wav = np.array([0.1, 0.2, 0.3, 0.4, 0.5]), 
                      fs = 44100, 
                      f0s = np.array([[0.0, 440], [0.01, 440], [0.02, 440], [0.03, 440], [0.04, 440]]))






        


    

# %%
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder

projects = CompiledProjectFinder('./matlab/compiled')

vat = projects.get_project('get_next_thousand')

print(vat)

f = vat.functions['getnextthousand']
print(f)

result = f.execute(float(1000))

print(result)
if result is not None:
    print(result.outputs)

result.verify_serialization()


# %%
import numpy as np 

import matlab.wrappers.get_next_thousand

gnt = matlab.wrappers.get_next_thousand.get_next_thousand('./matlab/compiled/get_next_thousand')

result = gnt.getnextthousand(1000)
print(result)
# result = gnt.getnexttwothousand(1000)
# print(result)
# print('Finished!')

# %%
import os
result.execution_message = 'Test message, ignore actual message'
# list diretory:
print(os.listdir('/home/tomas/Projects/visp_matlab_loader/matlab/tests/get_next_thousand'))

result.to_json(file=R'/home/tomas/Projects/visp_matlab_loader/matlab/tests/get_next_thousand/get_next_thousand_test.json')


# %%
from matlab.wrappers import voice_analysis_toolbox

vat = voice_analysis_toolbox.voice_analysis_toolbox('./matlab/compiled/voice_analysis_toolbox')

vat.voice_analysis_modified('/home/tomas/Projects/visp_matlab_loader/reference/audio_reference/Lx_ch1.wav',
                                                    start_time=20,
                                                    end_time=30)
# vat.voice_analysis_modified('/home/tomas/Projects/visp_matlab_loader/reference/audio_reference/test_tone.wav', 
#                           start_time=1.5, 
#                           dfa_scaling=[10,70,90,110,130,150,170,190])
