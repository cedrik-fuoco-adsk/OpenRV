#!/bin/bash

# Check if a binary file was provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <binary_file> <CMAKE_SOURCE_DIR>"
    exit 1
fi

# The binary file to process
binary_file=$1

if [[ "${binary_file}" == *.a ]]; then
  exit 0;
fi

# Use otool to list dynamic libraries and parse for those starting with /Users/cfuoco
otool_output=$(otool -L "$binary_file")

# Loop through each line of the otool output
while IFS= read -r line; do
    original_path=$(echo "$line" | awk '{print $1}')
    echo $original_path

    if [[ $original_path == *"$2"* ]] || ([[ ! $original_path == /* ]] && [[ ! $original_path == @* ]]); then
        # Extract the library name
        library_name=$(basename "$original_path")
        # Extract the original path
        original_path=$(echo "$original_path" | awk '{print $1}')
        # Construct the new path
        new_path="@rpath/$library_name"
        # Use install_name_tool to change the install name
        install_name_tool -change "$original_path" "$new_path" "$binary_file"
    fi
done <<< "$otool_output"

# Automatically remove all RPATHs
rpaths=$(otool -l "$binary_file" | awk '/LC_RPATH/{getline; getline; print $2}')
for rpath in $rpaths; do
    install_name_tool -delete_rpath "$rpath" "$binary_file"
done

echo "Processed install names for $binary_file"
