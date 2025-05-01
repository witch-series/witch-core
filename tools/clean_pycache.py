#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to remove __pycache__ directories and bytecode (.pyc) files

This script recursively searches and removes all __pycache__ directories
and .pyc files within the project.
"""

import os
import shutil
from pathlib import Path

def remove_pycache_dirs(start_dir='.'):
    """
    Removes all __pycache__ directories and .pyc files under the specified directory.
    
    Args:
        start_dir (str): Directory path to start the search
    
    Returns:
        tuple: Tuple of (number of directories removed, number of files removed)
    """
    dirs_removed = 0
    files_removed = 0
    start_path = Path(start_dir)
    
    # Remove __pycache__ directories
    for pycache_dir in start_path.glob('**/__pycache__'):
        if pycache_dir.is_dir():
            print(f"Removing: {pycache_dir}")
            try:
                shutil.rmtree(pycache_dir)
                dirs_removed += 1
            except Exception as e:
                print(f"Error: Failed to remove {pycache_dir} - {e}")
    
    # Remove .pyc files
    for pyc_file in start_path.glob('**/*.pyc'):
        if pyc_file.is_file():
            print(f"Removing: {pyc_file}")
            try:
                os.remove(pyc_file)
                files_removed += 1
            except Exception as e:
                print(f"Error: Failed to remove {pyc_file} - {e}")
    
    return dirs_removed, files_removed

if __name__ == "__main__":
    # Path to the project root directory
    project_root = Path(__file__).parent.parent
    
    print(f"Project directory: {project_root}")
    print("Searching for and removing __pycache__ directories and .pyc files...")
    
    dirs, files = remove_pycache_dirs(project_root)
    
    print(f"\nCompleted: Removed {dirs} __pycache__ directories and {files} .pyc files.")
    print("\nTo prevent Python from generating bytecode files, use one of the following methods:")
    print("1. Set environment variable: export PYTHONDONTWRITEBYTECODE=1")
    print("2. Use the -B flag when running Python: python -B script.py")
    print("3. Set sys.dont_write_bytecode = True in your program")