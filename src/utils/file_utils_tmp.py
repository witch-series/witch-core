"""
Utility functions for temporary file operations

Main features:
- Saving files to tmp folder with atomic write operations
- Loading files from tmp folder
- Secure temporary file handling
"""

from pathlib import Path
from atomicwrites import atomic_write
import tempfile
import shutil
import os

from .file_utils_core import get_tmp_directory


def save_to_tmp(filename, data, binary=False):
    """
    Save data to the tmp directory using atomic write for safer file operations.
    
    Args:
        filename (str): Name of the file to save
        data: Data to save
        binary (bool): Whether to save in binary mode
    
    Returns:
        str: Absolute path of the saved file
    """
    file_path = get_tmp_directory() / filename
    
    # Ensure the parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    mode = 'wb' if binary else 'w'
    
    # Use atomic_write for safer file operations
    with atomic_write(file_path, mode=mode, overwrite=True) as f:
        f.write(data)
    
    return str(file_path.absolute())


def load_from_tmp(filename, binary=False):
    """
    Load data from the tmp directory.
    
    Args:
        filename (str): Name of the file to load
        binary (bool): Whether to load in binary mode
    
    Returns:
        Contents of the data, None if the file does not exist
    """
    file_path = get_tmp_directory() / filename
    
    if not file_path.exists():
        return None
    
    mode = 'rb' if binary else 'r'
    encoding = None if binary else 'utf-8'
    
    with open(file_path, mode, encoding=encoding) as f:
        return f.read()


def create_secure_tmp_file(prefix=None, suffix=None, content=None, binary=False):
    """
    Create a secure temporary file with optional content.
    
    Args:
        prefix (str, optional): Prefix for the temporary filename
        suffix (str, optional): Suffix for the temporary filename
        content (optional): Content to write to the file
        binary (bool): Whether to handle content as binary
    
    Returns:
        str: Path to the created temporary file
    """
    tmp_dir = get_tmp_directory()
    
    # Create a secure temporary file
    fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=tmp_dir)
    
    try:
        if content is not None:
            mode = 'wb' if binary else 'w'
            encoding = None if binary else 'utf-8'
            
            with open(fd, mode, encoding=encoding, closefd=True) as f:
                f.write(content)
        else:
            # Close the file if no content was provided
            os.close(fd)
    except:
        # Make sure we close the file descriptor in case of an exception
        os.close(fd)
        raise
    
    return temp_path


def create_secure_tmp_directory(prefix=None):
    """
    Create a secure temporary directory within the tmp folder.
    
    Args:
        prefix (str, optional): Prefix for the temporary directory name
    
    Returns:
        str: Path to the created temporary directory
    """
    tmp_dir = get_tmp_directory()
    return tempfile.mkdtemp(prefix=prefix, dir=tmp_dir)


def copy_to_tmp(src_path, dest_filename=None):
    """
    Copy a file to the tmp directory.
    
    Args:
        src_path (str or Path): Path to the source file
        dest_filename (str, optional): Destination filename in tmp dir.
                                     If None, uses the original filename.
    
    Returns:
        str: Path to the copied file in the tmp directory
    """
    src_path = Path(src_path)
    
    if not src_path.exists() or not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    
    if dest_filename is None:
        dest_filename = src_path.name
    
    dest_path = get_tmp_directory() / dest_filename
    
    # Use shutil for efficient file copying
    shutil.copy2(src_path, dest_path)
    
    return str(dest_path.absolute())