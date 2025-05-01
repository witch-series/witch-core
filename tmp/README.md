# tmp Directory

This directory is used to store user-specific settings and temporary files.

## Purpose

- User-specific configuration files
- Temporary data storage
- Protocol definitions
- Server information registry
- Port information registry

## Notes

The contents of this directory are added to `.gitignore` and excluded from version control. This allows each user to work with their own configurations.

## Directory Structure

By default, the following subdirectories are automatically created:

- `tmp/protocols/` - Protocol definition files
- `tmp/logs/` - Log files (to be used in the future)

## Usage

Files and data in this directory are automatically managed by various framework functions:

```python
# Example: Save a file to the tmp directory
from src.utils import file_utils

# Save data as a temporary file
file_utils.save_to_tmp("my_settings.json", json_data)

# Load from a temporary file
data = file_utils.load_from_tmp("my_settings.json")
```

It is recommended to store application-specific settings and data files in this directory.