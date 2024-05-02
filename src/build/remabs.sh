#!/bin/bash

# Required arguments
TARGET_PATH=""
ROOT_PATH=""

# Function to get object files
get_object_files() {
    local target=$1
    if [ -d "$target" ]; then
        find "$target" -type f -exec file -bh {} \; | grep "Mach-O" | awk -F: '{print $1}'
    else
        echo "$target"
    fi
}

# Function to get rpaths
get_rpaths() {
    local object_file_path=$1
    otool -l "$object_file_path" | grep "LC_RPATH" -A 1 | grep "path" | awk '{print $2}'
}

# Function to get shared library paths
get_shared_library_paths() {
    local object_file_path=$1
    otool -L "$object_file_path" | awk '{print $1}'
}

# Function to delete rpath
delete_rpath() {
    local object_file_path=$1
    local rpath=$2
    install_name_tool -delete_rpath "$rpath" "$object_file_path"
}

# Function to change shared library path
change_shared_library_path() {
    local object_file_path=$1
    local old_library_path=$2
    local new_library_path="@rpath/$(basename "$old_library_path")"
    install_name_tool -change "$old_library_path" "$new_library_path" "$object_file_path"
    echo "$new_library_path"
}

# Main function to fix rpaths and shared library paths
fix_rpath() {
    local target=$1
    local root=$2

    for file in $(get_object_files "$target"); do
        echo "Fixing rpaths for $file"
        for rpath in $(get_rpaths "$file"); do
            if [[ ! $rpath == @* ]] && [[ ! $rpath == .* ]]; then
                echo -e "\trpath: $rpath (Deleted)"
                delete_rpath "$file" "$rpath"
            else
                echo -e "\trpath: $rpath"
            fi
        done

        echo "Fixing shared library paths for $file"
        for library_path in $(get_shared_library_paths "$file"); do
            shared_library_name=$(basename "$library_path")
            if [[ $library_path == $root* ]] || [[ $library_path == $shared_library_name ]]; then
                new_library_path=$(change_shared_library_path "$file" "$library_path")
                echo -e "\tlibrary path: $library_path (Changed to $new_library_path)"
            else
                echo -e "\tlibrary path: $library_path"
            fi
        done
    done
}

# Argument parsing
while (( "$#" )); do
 case "$1" in
    --target)
      TARGET_PATH="$2"
      shift 2
      ;;
    --root)
      ROOT_PATH="$2"
      shift 2
      ;;
    *) # If unknown option
      echo "Unknown option: $1"
      exit 1
      ;;
 esac
done

# Validation
if [[ -z "$TARGET_PATH" ]] || [[ -z "$ROOT_PATH" ]]; then
    echo "Both --target and --root arguments are required."
    exit 1
fi

if [[ ! -e "$TARGET_PATH" ]]; then
    echo "Target path does not exist: $TARGET_PATH"
    exit 1
fi

if [[ ! -e "$ROOT_PATH" ]]; then
    echo "Root path does not exist: $ROOT_PATH"
    exit 1
fi

# Call the main function
fix_rpath "$TARGET_PATH" "$ROOT_PATH"
