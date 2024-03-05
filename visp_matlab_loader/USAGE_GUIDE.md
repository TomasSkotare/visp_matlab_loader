# Introduction
This is intended to be used to enable the use of a MATLAB script in other languages.

In this case, we use the MATLAB compiler option to compile a script to a portable format.

This usually requires MATLAB to be run on the platform it intends to run on in the future, i.e. Linux if you want to run it on Linux.

To begin, the code supplied here first creates a MATLAB script that allows for calling functions you want to expose. This is the code that should be compiled using MATLAB compiler. The idea behind this is that this acts as a gateway to your other MATLAB functions. 

# Required software:

For compilation, a valid installation of MATLAB including MATLAB Compiler is required.

For running a compiled project, the corresponding version of MATLAB compiler runtime is required.

Pyton 3.11

# Usage:

## Compiling 

Compiling a set of libraries can be done using this sample code:

```
from visp_matlab_loader.compile.matlab_compiler import MATLABProjectCompiler
import os

MATLAB_LIBRARY_PATH = os.path.join(os.getcwd(), 'matlab', 'libraries')
MATLAB_COMPILED_PATH = os.path.join(os.getcwd(), 'matlab', 'compiled')

# Verify path exists
if not os.path.exists(MATLAB_LIBRARY_PATH):
    raise Exception(f'Matlab library path does not exist: {MATLAB_LIBRARY_PATH}')

if not os.path.exists(MATLAB_COMPILED_PATH):    
    os.makedirs(MATLAB_COMPILED_PATH)

for name in os.listdir(MATLAB_LIBRARY_PATH):
    if os.path.isdir(os.path.join(MATLAB_LIBRARY_PATH, name)):
        print(f'Compiling {name}')
        compiler = MATLABProjectCompiler(project_path=os.path.join(MATLAB_LIBRARY_PATH, name), 
                                         output_path=os.path.join(MATLAB_COMPILED_PATH, name)) # Here we would add a MatlabPathSetter if we want to specify which compiler to use!
        compiler_code, compiler_message = compiler.compile_project(verbose=False)
        if compiler_code != 0:
            print(f'Error compiling project: {name}, compiler message was: {compiler_message}')
        else:
            print(f'Successfully compiled project: {name}')
```        
The user will have to declare the actual path to both `MATLAB_LIBRARY_PATH` and `MATLAB_COMPILED_PATH`, which is the input and output respectively.

# Running code:
There are two options, running code that has not been wrapped, and running code that has been wrapped.

Wrapping in this case is that someone has defined the input to the function, and it can be used as a regular python function:
```
import matlab.wrappers.get_next_thousand

gnt = matlab.wrappers.get_next_thousand.get_next_thousand('./matlab/compiled/get_next_thousand')

result = gnt.getnextthousand(requested_outputs=1, starting_number=1000)
print(result)
```

## In the case where no wrapper has been defined, the user must instead call the function knowing the input themselves:
```
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder

projects = CompiledProjectFinder('./matlab/compiled')

vat = projects.get_project('get_next_thousand')

print(vat)

f = vat.functions['getnextthousand']
print(f)

result = f.execute(float(1000))

print(result)
```


The library should find the currently installed MATLAB Runtime Environment automatically, however the version be manually matched.

# The input
In general, MATLAB works with floats, even when integers might be expected.

For matrices, we use [NumPy](https://numpy.org/). Note that sometimes column vectors are expected instead of (e.g. dimensions 10,1 instead of 10,) or perhaps row vectors (1,10). The helper function `ensure_vector` was created to help with this.

Inputs will otherwise automatically be converted; verify the results you get back in this case.

# The output

The result will be a `MatlabExecutionResult`.

The `MatlabExecutionResult` object has the following properties:
1. return_code: The return code of the MATLAB execution, 0 if successful.
1. execution_message: The execution message of the MATLAB execution.
1. function_name: The name of the MATLAB function that was executed.
1. outputs: The outputs of the MATLAB execution.

The execution message is the output from running the funcwtion in matlab, and can often be very verbose and must be manually parsed if it contains information.

# Creating a new wrapper

A new wrapper for a new MATLAB project can be created using the MatlabProjectWrapper abstract base class (ABC). 

To create this, a class must extend this class, and be the exact same name as the compiled MATLAB library.

Each defined method must then use the `@matlab_function` decorator. This way, the input can be handled and type checked
in python.

As a simple example, look at the definition for the `get_next_thousand` library (and function):

```
class get_next_thousand(MatlabProjectWrapper):

    def __init__(self, directory):
        super().__init__(self.__class__.__name__.lower(), directory)

    @matlab_function
    def getnextthousand(
        self, inputNumber: int, requested_outputs=1
    ) -> MatlabExecutionResult:
        return default_args(locals())  # type: ignore
``` 

This creates the wrapper (used above) for the `get_next_thousand` library and defines the input and default types for one of the available functions.

Note that the inputs can be modified as well, before being returned, if the types must be validated somehow (for example,
if MATLAB expects a list to be a column or row vector, it can be modified).






# References:

The Visible Speech project (VISP): for more information, please visit the [VISP website](https://visp.humlab.umu.se).
