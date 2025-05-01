"""
Utility functions for file operations and data processing

Main features:
- Getting the execution directory
- Saving and loading files to/from tmp folder
- Calculating data hash
- Reading and writing JSON data
- File encryption and decryption
- Secure temporary file handling
"""

# Import from enhanced modules
from .file_utils_core import (
    get_execution_directory,
    get_project_root as _get_project_root,
    get_tmp_directory as _get_tmp_directory,
    ensure_directory,
    list_files,
    remove_directory,
    copy_files,
    get_file_size
)

from .file_utils_tmp import (
    save_to_tmp,
    load_from_tmp,
    create_secure_tmp_file,
    create_secure_tmp_directory,
    copy_to_tmp
)

from .file_utils_data import (
    calculate_hash,
    save_json,
    load_json,
    encrypt_data,
    decrypt_data,
    generate_key
)

# Provide aliases for code compatibility
_get_project_root = _get_project_root
_get_tmp_directory = _get_tmp_directory

# List of exported functions
__all__ = [
    # Core file utilities
    'get_execution_directory',
    '_get_project_root',
    '_get_tmp_directory',
    'ensure_directory',
    'list_files',
    'remove_directory',
    'copy_files',
    'get_file_size',
    
    # Temporary file utilities
    'save_to_tmp',
    'load_from_tmp',
    'create_secure_tmp_file',
    'create_secure_tmp_directory',
    'copy_to_tmp',
    
    # Data utilities
    'calculate_hash',
    'save_json',
    'load_json',
    'encrypt_data',
    'decrypt_data',
    'generate_key'
]