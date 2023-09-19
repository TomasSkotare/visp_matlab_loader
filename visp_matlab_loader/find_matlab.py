import os
import re
import argparse

def find_matlab_versions():
    matlab_dir = '/usr/local/MATLAB'
    versions = [d for d in os.listdir(matlab_dir) if re.match(r'^R\d{4}[ab]$', d)]
    versions.sort(reverse=True)
    return versions

def select_matlab_version(versions, version=None):
    if version and version in versions:
        return version
    else:
        return versions[0]

def main():
    parser = argparse.ArgumentParser(description='Find MATLAB versions.')
    parser.add_argument('-l', '--list', action='store_true', help='List all MATLAB versions')
    parser.add_argument('-v', '--version', type=str, help='Specify a MATLAB version')
    args = parser.parse_args()

    versions = find_matlab_versions()
    if not versions:
        print("No MATLAB versions found.")
        return

    if args.list:
        print("Found MATLAB versions:")
        for version in versions:
            print(version)

    selected_version = select_matlab_version(versions, args.version)
    print(f"Selected MATLAB version: {selected_version}")
    print(f"Path to selected MATLAB version: /usr/local/MATLAB/{selected_version}")

if __name__ == "__main__":
    main()