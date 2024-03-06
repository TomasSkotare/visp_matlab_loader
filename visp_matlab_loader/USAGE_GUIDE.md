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

results = MATLABProjectCompiler.compile_projects(MATLAB_LIBRARY_PATH, MATLAB_COMPILED_PATH, force_output=False)
for project_path, exit_status, message in results:
    project_name = os.path.basename(project_path)
    if exit_status != 0:
        print(f'Error compiling {project_name} with message:\n\t{message}')
    else:
        print(f'Compiled {project_name} successfully')
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

### WARNING: Deletion of output.mat
In the current version, outputs are always saved in the current directory as output.mat.
This file is then automatically deleted after having been read. If you already have a file named this,
it will either be deleted or cause an error.

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
The advantage of the first approach is that the input can be defined only once.


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

A more complex example is the following, where the input signature of the MATLAB file does not match the Python input:
```
@matlab_function
def voice_analysis_modified(
    self, filename: str, f0_alg="SWIPE", start_time=0, end_time=np.inf, Tmax=1000, d=4, tau=50,
    eta=0.2, dfa_scaling=np.arange(50, 201, 20), f0min=50, f0max=500, flag=1, requested_outputs=3
) -> MatlabExecutionResult:
    
    if not filename: 
        raise ValueError("Filename must be provided")
    
    dfa_scaling = ensure_vector(dfa_scaling, "column")
    start_time, end_time = float(start_time), float(end_time)
    
    params = {
        k: v for k, v in locals().items() 
        if k not in ["self", "filename", "requested_outputs"]
    }
    
    return (filename,), {"requested_outputs": requested_outputs, "params": params}  # type: ignore
```
Here we verify the input, and ensure tha tone variable is in a column vector format using the `ensure_vector` 
helper functionfrom `visp_matlab_loader.wrappers.matlab_wrapper_helper`. The options are then put into a dictionary,
as the Matlab function expects a struct with these variables.  We then create the args and kwargs separately and 
return them instead of using the default with locals.





# References:

The Visible Speech project (VISP): for more information, please visit the [VISP website](https://visp.humlab.umu.se).
