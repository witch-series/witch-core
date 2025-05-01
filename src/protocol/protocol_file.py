"""
Module providing functions for protocol definition file operations

Main features:
- Loading and saving protocols
- Output of protocols in text format
- Retrieving list of available protocols
"""

import os
import json
from .protocol_core import _get_protocols_directory, validate_protocol

# Import utils module
from ..utils import file_utils


def save_protocol(protocol, filename=None, as_text=False):
    """
    Save protocol definition to a file.
    
    Args:
        protocol (dict): Protocol definition to save
        filename (str): Filename to save as (auto-generated from protocol name if None)
        as_text (bool): Whether to also save in text format
    
    Returns:
        str: Path of the saved file
    """
    if filename is None:
        filename = f"{protocol['name']}.json"
    
    protocols_dir = _get_protocols_directory()
    file_path = protocols_dir / filename
    file_utils.save_json(str(file_path), protocol)
    
    # If saving in text format as well
    if as_text:
        text_filename = f"{os.path.splitext(filename)[0]}.txt"
        text_file_path = protocols_dir / text_filename
        
        with open(text_file_path, 'w', encoding='utf-8') as f:
            f.write(protocol_to_text(protocol))
    
    return str(file_path)


def load_protocol(name_or_path):
    """
    Load a protocol definition.
    
    Args:
        name_or_path (str): Protocol name or file path
        
    Returns:
        dict: Loaded protocol definition, None if not found
    """
    # If a file path is directly specified
    if os.path.exists(name_or_path):
        return file_utils.load_json(name_or_path)
    
    # Search by protocol name
    protocols_dir = _get_protocols_directory()
    
    # Add .json extension if not included
    if not name_or_path.endswith('.json'):
        name_or_path = f"{name_or_path}.json"
    
    file_path = protocols_dir / name_or_path
    
    if not file_path.exists():
        return None
    
    return file_utils.load_json(str(file_path))


def list_available_protocols():
    """
    Get a list of all available protocols.
    
    Returns:
        list: List of protocol names
    """
    protocols_dir = _get_protocols_directory()
    protocol_files = [f.name for f in protocols_dir.glob("*.json")]
    
    # Remove .json extension
    protocol_names = [os.path.splitext(name)[0] for name in protocol_files]
    
    return protocol_names


def protocol_to_text(protocol):
    """
    Convert protocol definition to text format.
    
    Args:
        protocol (dict): Protocol definition
        
    Returns:
        str: Text format of protocol definition
    """
    if not validate_protocol(protocol):
        return "Invalid protocol"
    
    lines = []
    lines.append(f"Protocol: {protocol['name']} (#{protocol['number']})")
    lines.append(f"Version: {protocol.get('version', '1.0.0')}")
    
    if "description" in protocol:
        lines.append("\nDescription:")
        lines.append(protocol["description"])
    
    lines.append("\nData Fields:")
    data_names = protocol["data_names"]
    data_types = protocol.get("data_types", {})
    
    for i, name in enumerate(data_names):
        data_type = data_types.get(name, "string")
        lines.append(f"  {i+1}. {name} ({data_type})")
    
    options = protocol.get("options", {})
    if options:
        lines.append("\nOptions:")
        for key, value in options.items():
            lines.append(f"  {key}: {value}")
    
    if "default_port" in protocol:
        lines.append(f"\nDefault Port: {protocol['default_port']}")
    
    if "created_at" in protocol:
        lines.append(f"\nCreated: {protocol['created_at']}")
    
    if "updated_at" in protocol:
        lines.append(f"Updated: {protocol['updated_at']}")
    
    return "\n".join(lines)


def export_protocol_to_text_file(protocol_name, output_path=None):
    """
    Export protocol to a text file.
    
    Args:
        protocol_name (str): Name of the protocol to export
        output_path (str): Path for output file (tmp/protocols directory if None)
        
    Returns:
        str: Path of exported file, None if failed
    """
    protocol = load_protocol(protocol_name)
    if not protocol:
        return None
    
    if output_path is None:
        protocols_dir = _get_protocols_directory()
        output_path = str(protocols_dir / f"{protocol_name}.txt")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(protocol_to_text(protocol))
        return output_path
    except Exception as e:
        print(f"Export error: {e}")
        return None