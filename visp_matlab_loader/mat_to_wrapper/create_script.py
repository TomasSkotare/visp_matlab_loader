import glob
import json
import re
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup


def extract_covarep_expected_functions(url: str):
    """This gets the expected public functions for the covarep library.

    Args:
        url (str): The location of the added funcitons

    Returns:
        matlab_links: A list of tuples containing the link text (function name) and the link itself, which explains the function.
    """
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, "html.parser")
    matlab_links = []
    for link in soup.find_all("a", href=True):
        if re.search(r"\.m$", link["href"]):
            matlab_links.append((link.text, link["href"]))
    return matlab_links


def contains_line_breaks(s):
    """Return True if the string contains any kind of line break, False otherwise."""
    return bool(re.search(r"\n|\r\n|\r", s))


def directory_to_script(
    directory_path: str,
    verbose: bool = False,
    excluded_files: List[str] | None = None,
    save_function_location=None,
):
    """Create a MATLAB function wrapper for a given directory.

    The intent is to scan through all .m files in the given directory (and its subdirectories),
    and add each function into a new MATLAB function.

    This new MATLAB function will take, as input, an input file.

    This file is a MATLAB .mat file, which contains several variables:
    - function_name: The function name which should be invoked
    - output_count: The number of outputs to expect. Note that MATLAB code can
                    perform different calculations depending on the number of
                    specified output variables, so we must specify this.
    - varargin: A cell list of inputs for the function, in the order they should
                according to the function signature.


    Args:
        directory_path (str): The directory to start parsing from
        verbose (bool, optional): Whether to give additional status prints or not
        excluded_files (list, optional): A list of files which should be excluded, perhaps
                as they are oddly shaped. Defaults to ['startup.m'].

    Returns:
        tuple: A tuple with two variables, the script text itself and the list of
            functions which was found.
    """
    if excluded_files is None:
        excluded_files = ["startup.m"]
    vprint = lambda x: print(x) if verbose else None

    # Get a list of all files in the directory
    files = glob.glob(f"{directory_path}/**/*.m", recursive=True)
    vprint(f"Number of files found: {len(files)}")

    # Filter the list to only include MATLAB .m files
    matlab_files = [f for f in files if f.endswith(".m")]

    # Create a string to hold the MATLAB function
    matlab_function = "function results = call_matlab_function(input_file)\n\n"
    matlab_function += "disp(input_file)\n"
    matlab_function += "inp = load(input_file);\n"
    matlab_function += "function_name = inp.function_name;\n"
    matlab_function += "varargin = inp.varargin;\n"
    matlab_function += "for i = 1:length(inp.varargin)\n"
    matlab_function += "    sprintf('Index %i, class: %s',i,class(inp.varargin{i}))\n"
    matlab_function += "end\n"
    matlab_function += "output = cell(1,inp.output_count);\n"

    found_functions = set()

    # Loop through the MATLAB files and add a call to each function
    for file in matlab_files:
        if Path(file).name in excluded_files:
            continue
        # Open the file and read its contents
        try:
            with open(file, "r", encoding="ISO-8859-1") as f:
                contents = f.read()
        except Exception as e:
            print(f"Reading {file}")
            print(" ---- FAILED ----")
            print(e)
            return
        vprint(f"Reading {file}")

        contents = re.sub(r"\s[.]{3}\s*\\n", " ", contents)

        # This is an attempt for a regex to match all different types of MATLAB function signatures.
        # MATLAB functions may not take any input, and may not return anything.
        match = re.findall(
            r"(?:\r\n|\r|\n)?\s*function\s+((\[?[0-9a-zA-z\s,]*\]?)\s*=)?\s*([0-9a-zA-z\s]*)\((.*)\)",
            contents,
        )

        # Loop through the function names and add a call to each one to the MATLAB function string

        for _, output, function, arguments in match:
            # print(output)
            current_function = ""
            output = output.strip()
            function = function.strip()

            if len(function) < 1:
                vprint("Function name shorter than expected, skipping...")
                continue

            if function in found_functions:
                vprint(f"Already found {function}, which is odd. Skipping...")
                continue

            if "=" in output or "=" in function:
                vprint('Function name contained "=" character. Skipping.')
                continue

            if function.startswith("{"):
                vprint("Function name started with {, which is likely incorrect. Skipping.")
                continue

            if verbose:
                vprint(f"Found function: {function} (output {output})")

            stem = Path(file).stem
            if stem != function:
                vprint(f"Mismatch between file name ({stem}) and function ({function})")
                function = stem
            if "%" in function:
                if verbose:
                    vprint(" ---- SKIPPED AS IT CONTAINS COMMENTS ------")
                continue
            if "\n" in function:
                if verbose:
                    vprint(" ---- SKIPPED AS IT CONTAINS MULTIPLE LINES ------")
                continue
            current_function += f"if strcmp(function_name, '{function}')\n"
            if len(output) > 0:
                current_function += "    [output{:}] = " + f"{function}" + "(varargin{:});"
            else:
                current_function += f"    {function}" + "(varargin{:});"
            if len(arguments) > 0:
                current_function += f"%{arguments}"
            current_function += "\n"
            if output.startswith("["):
                # output = '{' + output[1:-1] + '}'
                output = output[1:-1]
            if len(output) > 0:
                if contains_line_breaks(output):
                    vprint(f" ---- UNEXPECTED LINE BREAK IN OUTPUT FOUND IN FUNCTION {function} ------")
                    continue
                current_function += f"    results = " + "{" + f'"{output}", ' "output};\n"
            else:
                current_function += "    results = 0;\n"
            # matlab_function += (f'    return\n')
            current_function += "end\n"

            # If everything passed through, we actually add the function to the MATLAB function string
            matlab_function += current_function
            found_functions.add((output, function, arguments))
            break  # We break here, as we otherwise start including location functions.

    matlab_function += "% Ensure that strings are in a format readable by e.g. python\n"
    matlab_function += "results{1} = cellstr(results{1});\n"

    matlab_function += "save('results.mat','results')\n"
    # Close the function definition
    matlab_function += "\nend"

    # Create a dictionary of available functions
    function_dict = {}
    for output, function_name, function_input in found_functions:
        output_list = output.translate(str.maketrans(",[]", "   ")).split()
        input_list = function_input.translate(str.maketrans(",[]", "   ")).split()

        function_dict[function_name] = {"output": output_list, "input": input_list}

    # Return the MATLAB function string and the found functions
    if save_function_location:
        dict_to_json(function_dict, output_file=save_function_location)

    return matlab_function, function_dict


def dict_to_json(function_dict: dict, output_file: str):
    with open(output_file, "w") as f:
        json.dump(function_dict, f)


def json_to_dict(json_file: str):
    with open(json_file, "r") as f:
        return json.load(f)


# relevant_functions = extract_covarep_expected_functions(
#     "http://covarep.github.io/covarep/contributions.html"
# )
