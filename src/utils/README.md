# Utils Module

## Quick Reference

This module provides utility functions supporting the core functionality of the witch-core library.

For full documentation, see [Utils Module Documentation](../../doc/utils.md).

## Components

The utils module is organized into focused utility files:

- **file_utils.py**: File operations (main entry point that imports from other file util modules)
- **hash_utils.py**: Hash calculation and verification
- **compression_utils.py**: Data compression functionality
- **port_utils.py**: Network port management
- **server_registry.py**: Server information and registration

## Key Functions

### File Operations
- `save_json()`: Save data to JSON file
- `load_json()`: Load data from JSON file

### Hash Utilities
- `calculate_file_hash()`: Calculate hash of a file
- `calculate_src_directory_hash()`: Calculate hash of source directory

### Compression
- `compress_data()`: Compress data with various algorithms
- `decompress_data()`: Decompress data

### Port Management
- `is_port_in_use()`: Check if a port is in use
- `suggest_port_for_protocol()`: Get available port for a protocol

## Usage Example

```python
from src.utils.hash_utils import calculate_src_directory_hash
from src.utils.compression_utils import compress_data

# Get source code hash
src_hash, file_hashes = calculate_src_directory_hash()

# Compress data
data = b"Example data"
compressed = compress_data(data, method="gzip")
```