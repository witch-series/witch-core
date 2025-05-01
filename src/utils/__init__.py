"""
Common utility modules for the witch-series project

This module includes the following common utility functions:
- File operations (including temporary directory management)
- Hash calculation
- JSON data processing
- Server registry management
- Port management
"""

from .file_utils import (
    get_execution_directory,
    save_to_tmp,
    load_from_tmp,
    calculate_hash,
    save_json,
    load_json
)

from .server_registry import (
    register_server,
    get_server_registry,
    get_server_by_id,
    get_servers_by_protocol,
    get_servers_by_port,
    remove_server
)

from .port_utils import (
    is_port_in_use,
    is_port_registered,
    register_port,
    unregister_port,
    get_registered_server_info,
    list_registered_ports,
    suggest_port_for_protocol,
    get_random_available_port
)

__all__ = [
    'get_execution_directory',
    'save_to_tmp',
    'load_from_tmp',
    'calculate_hash',
    'save_json',
    'load_json',
    'register_server',
    'get_server_registry',
    'get_server_by_id',
    'get_servers_by_protocol', 
    'get_servers_by_port',
    'remove_server',
    'is_port_in_use',
    'is_port_registered',
    'register_port',
    'unregister_port',
    'get_registered_server_info',
    'list_registered_ports',
    'suggest_port_for_protocol',
    'get_random_available_port'
]