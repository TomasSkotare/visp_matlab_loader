#!/bin/bash

# Define the directories to be zipped
# Separate multiple directories with spaces
DIRS_TO_ZIP="./visp_matlab_loader ./python_wrappers ./matlab/compiled ./matlab/wrappers ./matlab/tests"

# Get the current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Define the name of the zip file
ZIP_FILE_NAME="runtime_files_${CURRENT_DATE}.zip"

# Define the files and directories to be excluded
EXCLUDE="*.pyc *__pycache__*"

# Create the zip file
zip -r $ZIP_FILE_NAME $DIRS_TO_ZIP -x $EXCLUDE

echo "Zip file $ZIP_FILE_NAME created."
