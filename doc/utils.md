# Utilities Module Documentation

## Overview

The utils module provides a collection of utility functions and classes that support the core functionality of the witch-core library. These utilities handle common operations like file management, hashing, compression, and server registration.

## Key Components

### Hash Utilities

The `hash_utils` module provides functions for calculating and verifying hashes:

- Source directory hash calculation
- File integrity verification
- Hash comparison and validation
- Compatibility checking

#### Key Functions:

- `calculate_src_directory_hash()`: Calculates a hash of the source directory
- `get_src_hash_info()`: Retrieves detailed information about the source hash
- `verify_hash_compatibility()`: Checks if hashes are compatible

### File Utilities

The file utilities modules provide functions for file operations:

- File reading and writing
- Directory traversal
- Temporary file management
- Data serialization and deserialization

#### Core File Utilities:

- `read_file()`: Reads content from a file
- `write_file()`: Writes content to a file
- `list_directory()`: Lists directory contents
- `ensure_directory()`: Creates directories if they don't exist

#### Data File Utilities:

- `load_json()`: Loads JSON data from a file
- `save_json()`: Saves JSON data to a file
- `load_binary()`: Loads binary data from a file
- `save_binary()`: Saves binary data to a file

#### Temporary File Utilities:

- `create_temp_file()`: Creates a temporary file
- `create_temp_directory()`: Creates a temporary directory
- `cleanup_temp_files()`: Removes temporary files

### Compression Utilities

The `compression_utils` module provides functions for data compression and decompression:

- Data compression
- Data decompression
- Compressed file handling
- Compression format selection

### Port Utilities

The `port_utils` module provides functions for managing network ports:

- Available port detection
- Port registration and unregistration
- Port conflict resolution
- Port status checking

### Server Registry

The `server_registry` module maintains a registry of active servers:

- Server registration and unregistration
- Server status tracking
- Server lookup
- Server metadata management

## Usage Examples

### Calculating Source Hash

```python
from src.utils.hash_utils import calculate_src_directory_hash

# Calculate hash of the source directory
hash_value, hash_info = calculate_src_directory_hash()
print(f"Source hash: {hash_value}")
print(f"Files counted: {hash_info['file_count']}")
```

### Working with Files

```python
from src.utils.file_utils import read_file, write_file

# Write data to a file
write_file("data.json", '{"key": "value"}')

# Read data from a file
content = read_file("data.json")
```

### Managing Ports

```python
from src.utils.port_utils import get_random_available_port, register_port

# Get an available port
port = get_random_available_port()

# Register the port
register_port(port, "server-123", "My Server")
```