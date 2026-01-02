#!/bin/bash

# Stop on errors and print commands
set -Eeuox pipefail

# Remove current directory of dist/ and build/
rm -rf dist/
rm -rf build/

# Compile using PyInstaller
executableName='petdance'
py -m PyInstaller main.py --windowed --noconfirm --icon=assets/icon.ico --name="$executableName"

# Run TCLChanger to fix tcl version 
# python TCLChanger/TCLChanger.py

# Copy assets over to dist/ folder
distAssets="dist/$executableName/assets"
mkdir $distAssets
for dir in assets/*; do
	if [ -d $dir ]; then
        cp -r $dir $distAssets
    fi
done

# compress solution to zip file
if [ -f petdance.zip ]; then
    rm petdance.zip
fi
find dist/petdance -printf "%P\n" | tar.exe -acf petdance.zip --no-recursion -C dist/petdance -T -
