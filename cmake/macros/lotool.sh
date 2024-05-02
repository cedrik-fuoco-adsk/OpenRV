#!/bin/bash

# Define the base directories for comparison
dir1="/Users/cfuoco/rv/OpenRV_main/_install/RV.app/Contents"
dir2="/Users/cfuoco/Downloads/MACOS_TEST/main/RV/RV.app/Contents"

# Function to compare libraries and executables using otool
compare_files() {
    local file1="$1"
    local file2="$2"

    if [[ ! -f "$file1" ]] || [[ ! -f "$file2" ]]; then
        echo "One of the files does not exist: $file1 or $file2"
        return
    fi

    otool -L "$file1" | awk 'NR>1 {print $1}' > /tmp/file1_otool_output.txt
    otool -L "$file2" | awk 'NR>1 {print $1}' > /tmp/file2_otool_output.txt

    diff /tmp/file1_otool_output.txt /tmp/file2_otool_output.txt | colordiff > /tmp/diff_output
    error=$?

    if [[ $error -eq 0 ]]; then
        FILENAME="/tmp/diff_output"
        if [ -s "$FILENAME" ]; then
            printf "\nDifference found: \n $file1 $file2\n"
            echo "`cat /tmp/diff_output`"
            printf "\n"
        fi
    fi

    rm /tmp/file1_otool_output.txt /tmp/file2_otool_output.txt /tmp/diff_output
}

# Recursively find all .dylib files and executables in dir1 and dir2
for dir in "Frameworks" "lib" "MacOS"; do
    find "$dir1/$dir" -type f \( -name "*.dylib" -o -perm +111 \) -print0 | while IFS= read -r -d '' file1; do
        # Construct the corresponding path in dir2
        file2="${file1/$dir1/$dir2}"

        # Ensure the file exists in dir2
        if [[ -f "$file2" ]]; then
            compare_files "$file1" "$file2"
        else
            echo "No corresponding file found in dir2 for $file1"
        fi
    done
done
