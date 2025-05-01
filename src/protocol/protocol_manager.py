"""
Communication Protocol Definition and Management Module

Main functions:
- Protocol definition and creation
- Protocol loading and saving
- Protocol validation
- Protocol version management
- Detailed configuration of data formats and options
- Text format output of protocol information
"""

# Imports from core module
from .protocol_core import (
    create_protocol,
    validate_protocol,
    get_protocol_version,
    update_protocol_version,
    _get_protocols_directory
)

# Imports from file operation module
from .protocol_file import (
    save_protocol,
    load_protocol,
    list_available_protocols,
    protocol_to_text,
    export_protocol_to_text_file
)

# Imports from data processing module
from .protocol_data import (
    parse_data_with_protocol,
    format_data_for_protocol,
    serialize_data_with_protocol,
    deserialize_data_with_protocol,
    convert_received_data_to_json,
    create_protocol_from_data_sample,
    find_protocol_by_data
)

# Imports from iteration functionality module
from .protocol_iteration import (
    create_iteration_protocol,
    is_continue_requested
)

# Export all public functions of the module
__all__ = [
    # Protocol definition creation and validation
    'create_protocol',
    'validate_protocol',
    'get_protocol_version',
    'update_protocol_version',
    
    # File operations
    'save_protocol',
    'load_protocol',
    'list_available_protocols',
    'protocol_to_text',
    'export_protocol_to_text_file',
    
    # Data processing
    'parse_data_with_protocol',
    'format_data_for_protocol',
    'serialize_data_with_protocol',
    'deserialize_data_with_protocol',
    'convert_received_data_to_json',
    'create_protocol_from_data_sample',
    'find_protocol_by_data',
    
    # Iteration functionality
    'create_iteration_protocol',
    'is_continue_requested'
]