"""
Core module providing basic protocol definition functionality

Main features:
- Protocol creation
- Protocol validation
- Protocol directory management
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

# Import utils module
from ..utils import file_utils


def _get_protocols_directory():
    """
    Get the directory for storing protocol definition files.
    Creates the directory if it doesn't exist.
    
    Returns:
        Path: Path to the protocols directory
    """
    # Use tmp/protocols directory
    protocols_dir = Path(file_utils._get_tmp_directory()) / "protocols"
    os.makedirs(protocols_dir, exist_ok=True)
    return protocols_dir


def create_protocol(number, name, data_names=None, options=None, data_types=None, 
                    default_port=None, description=None, schema=None):
    """
    Create a new protocol definition.
    
    Args:
        number (str): Protocol number (e.g. "001")
        name (str): Protocol name (e.g. "example_protocol")
        data_names (list): List of data names (e.g. ["temperature", "humidity"])
        options (dict): Dictionary of options (e.g. {"compress": "base64"})
        data_types (dict): Dictionary of data types (e.g. {"temperature": "float", "humidity": "float"})
        default_port (int): Default port number to use
        description (str): Protocol description
        schema (dict): Schema definition for data validation
    
    Returns:
        dict: Created protocol definition
    """
    if data_names is None:
        data_names = []
    
    if options is None:
        options = {}
    
    if data_types is None:
        # Default data type is string
        data_types = {name: "string" for name in data_names}
    else:
        # Add default string type for data names not specified
        for name in data_names:
            if name not in data_types:
                data_types[name] = "string"
    
    protocol = {
        "number": number,
        "name": name,
        "data_names": data_names,
        "data_types": data_types,
        "options": options,
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "id": str(uuid.uuid4())
    }
    
    if default_port:
        protocol["default_port"] = default_port
        
    if description:
        protocol["description"] = description
        
    if schema:
        protocol["schema"] = schema
    
    return protocol


def validate_protocol(protocol):
    """
    Validate if a protocol definition is valid.
    
    Args:
        protocol (dict): Protocol definition to validate
    
    Returns:
        bool: True if valid, False if invalid
    """
    # Check for required fields
    required_fields = ["number", "name", "data_names"]
    for field in required_fields:
        if field not in protocol:
            return False
    
    # number must be a string
    if not isinstance(protocol["number"], str):
        return False
    
    # name must be a string
    if not isinstance(protocol["name"], str):
        return False
    
    # data_names must be a list
    if not isinstance(protocol["data_names"], list):
        return False
    
    # data_types must be a dictionary if it exists
    if "data_types" in protocol and not isinstance(protocol["data_types"], dict):
        return False
    
    # options must be a dictionary if it exists
    if "options" in protocol and not isinstance(protocol["options"], dict):
        return False
    
    # version must be a string if it exists
    if "version" in protocol and not isinstance(protocol["version"], str):
        return False
    
    return True


def get_protocol_version(protocol):
    """
    Get the protocol version.
    
    Args:
        protocol (dict): Protocol definition
    
    Returns:
        str: Protocol version
    """
    if not validate_protocol(protocol):
        return None
    
    return protocol.get("version", "1.0.0")


def update_protocol_version(protocol, new_version):
    """
    Update the protocol version.
    
    Args:
        protocol (dict): Protocol definition
        new_version (str): New version
    
    Returns:
        dict: Updated protocol definition
    """
    if not validate_protocol(protocol):
        return protocol
    
    updated_protocol = protocol.copy()
    updated_protocol["version"] = new_version
    updated_protocol["updated_at"] = datetime.now().isoformat()
    
    return updated_protocol