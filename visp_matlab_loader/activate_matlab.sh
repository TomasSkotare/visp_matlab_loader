#!/bin/bash

# Find all installed MATLAB versions
versions=$(ls /usr/local/MATLAB)

# Check if any versions were found
if [ -z "$versions" ]; then
    echo "No MATLAB versions found."
    exit 1
fi

# Convert the versions to an array
versions_array=($versions)

# If a version was specified, use it
if [ ! -z "$1" ]; then
    version=$1
else
    # Otherwise, use the latest version
    version=${versions_array[-1]}
fi

# Change to the MATLAB bin directory
cd /usr/local/MATLAB/$version/bin

# Execute MATLAB activation script
echo "Starting MATLAB activation script for $version..."
source ./activate_matlab.sh

exit 0