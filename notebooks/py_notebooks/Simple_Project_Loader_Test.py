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

# %% [markdown]
# # Check that single value is considered valid
# We check that json serialization doesn't cause a correct serialization to fail...
#
# The underlying issue is that single numpy values of a base type can be converted to a python native type (int, float)
# which will cause the comparison to fail, even though the value will be correct (although of a different base type).

# %% [markdown]
#

# %%

import sys

sys.path.append("..")
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
from visp_matlab_loader.test.temporary_log_level import TempLogLevel
import logging

projects = CompiledProjectFinder("../matlab/compiled")

vat = projects.get_project("get_next_thousand")

print(vat)

# import logging
# logging.basicConfig(level=logging.DEBUG)  # Set the root logger level to DEBUG
# logger = logging.getLogger('visp_matlab_loader.execute.compiled_project_executor')  # Get the specific logger
# logger.setLevel(logging.DEBUG)  # Set the specific logger level to DEBUG

f = vat.functions["getnextthousand"]
with TempLogLevel(
    "visp_matlab_loader.execute.compiled_project_executor", logging.DEBUG
):
    result = f.execute(float(1000))
import numpy as np

assert np.all(
    [x == y for x, y in zip(result.outputs["nextNumbers"], range(1001, 2000))]
)  # We check the values returned
print("Expected value returned")
result.verify_serialization()
print("Serialization passed!")


# %%
# The same as above but using the other method

from matlab.wrappers import get_next_thousand

gnt = get_next_thousand.get_next_thousand("../matlab/compiled/get_next_thousand")
with TempLogLevel(
    "visp_matlab_loader.execute.compiled_project_executor", logging.DEBUG
):
    result = gnt.getnextthousand(1000)
assert np.all(
    [x == y for x, y in zip(result.outputs["nextNumbers"], range(1001, 2000))]
)  # We check the values returned
print("Expected value returned")
result.verify_serialization()
print("Serialization passed!")

# %%
# Try with a single return value
gnt = get_next_thousand.get_next_thousand("../matlab/compiled/get_next_thousand")

with TempLogLevel(
    "visp_matlab_loader.execute.compiled_project_executor", logging.DEBUG
):
    result = gnt.getnextone(inputNumber=5)
result.verify_serialization()
assert result.outputs["nextNumber"] == 6

# %%
# Try with more return values
gnt = get_next_thousand.get_next_thousand("../matlab/compiled/get_next_thousand")

with TempLogLevel(
    "visp_matlab_loader.execute.compiled_project_executor", logging.DEBUG
):
    result = gnt.getnextthree(inputNumber=3)
print(result)

# %%
# NOTE: This is a test that will fail because the function seemingly broken in the original code
import numpy as np

import matlab.wrappers.covarrep

cov = matlab.wrappers.covarrep.covarep("../matlab/compiled/covarep")

cov.sin_analysis(
    requested_outputs=2,
    wav=np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
    fs=44100,
    f0s=np.array([[0.0, 440], [0.01, 440], [0.02, 440], [0.03, 440], [0.04, 440]]),
)

# %%
from visp_matlab_loader.find_compiled_projects import CompiledProjectFinder
import numpy as np

projects = CompiledProjectFinder("../matlab/compiled")

vat = projects.get_project("voice_analysis_toolbox")

print(vat)

f = vat.functions["voice_analysis_modified"]
print(f)
# f.override_output_count(2)

result = f.execute(
    "/home/tomas/Projects/visp_matlab_loader/reference/audio_reference/test_tone.wav",
    {
        "start_time": 1.5,
        "dfa_scaling": np.array(
            [10, 70, 90, 110, 130, 150, 170, 190], dtype=np.float64
        ).reshape((-1, 1)),
    },
)


result.verify_serialization()
print("Output keys: ", result.outputs.keys())
print("Finished without errors!")

# %%
import os

result.execution_message = "Test message, ignore actual message"
# list diretory:
print(
    os.listdir("/home/tomas/Projects/visp_matlab_loader/matlab/tests/get_next_thousand")
)

result.to_json(
    file=R"/home/tomas/Projects/visp_matlab_loader/matlab/tests/get_next_thousand/get_next_thousand_test.json"
)


# %%
import logging
from matlab.wrappers import voice_analysis_toolbox
from visp_matlab_loader.test.temporary_log_level import TempLogLevel


vat = voice_analysis_toolbox.voice_analysis_toolbox(
    "../matlab/compiled/voice_analysis_toolbox"
)

with TempLogLevel(
    "visp_matlab_loader.execute.compiled_project_executor", logging.DEBUG
):
    result = vat.voice_analysis_modified(
        "/home/tomas/Projects/visp_matlab_loader/reference/audio_reference/Lx_ch1.wav",
        start_time=20,
        end_time=21,
    )

result.outputs.keys()
