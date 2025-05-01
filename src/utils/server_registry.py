"""
Server Information Management Utility Module

Main features:
- Server registration and management
- Port information recording
- Retrieving server lists

Enhanced with:
- pydantic for data validation
- pendulum for better date/time handling
- orjson for faster JSON processing
"""

import os
import socket
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Set, Any
from datetime import datetime
import pendulum
import orjson
from pydantic import BaseModel, Field, validator

# Import file_utils module
from . import file_utils


# Logger configuration
logger = logging.getLogger("WitchRegistry")


# Pydantic models for data validation
class ServerInfo(BaseModel):
    """Server information model with validation"""
    server_id: str
    port: int
    host: str = "0.0.0.0"
    local_ip: Optional[str] = None
    protocols: List[str] = Field(default_factory=list)
    description: str = ""
    registered_at: datetime
    last_updated: datetime
    
    @validator('port')
    def port_must_be_valid(cls, v):
        if not 0 <= v <= 65535:
            raise ValueError(f'Port must be between 0 and 65535, got {v}')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


def _get_server_registry_file() -> Path:
    """
    Get the path to the server registry file
    
    Returns:
        Path: Path to the registry file
    """
    return Path(file_utils._get_tmp_directory()) / "server_registry.json"


def register_server(server_id: str, port: int, host: str = '0.0.0.0', 
                   protocol_names: Optional[List[str]] = None, 
                   description: Optional[str] = None) -> bool:
    """
    Register server information in the registry
    
    Args:
        server_id: Server identifier
        port: Server port number
        host: Server hostname or IP address
        protocol_names: List of protocol names supported by the server
        description: Server description
    
    Returns:
        bool: Whether registration was successful
    """
    try:
        # Load existing registry
        registry = get_server_registry() or {}
        
        # Get local IP address
        local_ip = get_local_ip()
        
        now = pendulum.now()
        
        # Create and validate server information using pydantic
        server_info = ServerInfo(
            server_id=server_id,
            port=port,
            host=host,
            local_ip=local_ip,
            protocols=protocol_names or [],
            description=description or '',
            registered_at=now.datetime,
            last_updated=now.datetime
        )
        
        # Convert to dict for storage
        server_data = server_info.dict()
        
        # Add to registry (overwrite existing entry)
        registry[server_id] = server_data
        
        # Save registry with atomic write
        registry_file = _get_server_registry_file()
        _save_registry_atomic(registry_file, registry)
        
        return True
        
    except Exception as e:
        logger.error(f"Server registration error: {e}")
        return False


def _save_registry_atomic(file_path: Path, data: Dict) -> bool:
    """
    Save registry data with atomic write operation
    
    Args:
        file_path: Path to save the registry
        data: Registry data to save
    
    Returns:
        bool: Whether save was successful
    """
    try:
        # Create temp file
        temp_path = f"{file_path}.tmp"
        
        # Write to temp file
        with open(temp_path, 'wb') as f:
            f.write(orjson.dumps(
                data,
                option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
            ))
        
        # Atomic replace
        os.replace(temp_path, file_path)
        return True
    except Exception as e:
        logger.error(f"Error saving registry: {e}")
        return False


def get_server_registry() -> Dict[str, Dict[str, Any]]:
    """
    Get the server registry
    
    Returns:
        dict: Server registry (server ID -> server information)
    """
    registry_file = _get_server_registry_file()
    
    if not registry_file.exists():
        return {}
    
    try:
        with open(registry_file, 'rb') as f:
            return orjson.loads(f.read())
    except Exception as e:
        logger.error(f"Error loading server registry: {e}")
        return {}


def get_server_by_id(server_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information for a specific server
    
    Args:
        server_id: Server identifier
    
    Returns:
        dict: Server information, or None if not found
    """
    registry = get_server_registry()
    return registry.get(server_id)


def get_servers_by_protocol(protocol_name: str) -> List[Dict[str, Any]]:
    """
    Get a list of servers that support a specific protocol
    
    Args:
        protocol_name: Protocol name
    
    Returns:
        list: List of server information
    """
    registry = get_server_registry()
    matching_servers = []
    
    for server_id, server_info in registry.items():
        if protocol_name in server_info.get('protocols', []):
            matching_servers.append(server_info)
    
    return matching_servers


def get_servers_by_port(port: int) -> List[Dict[str, Any]]:
    """
    Get a list of servers using a specific port
    
    Args:
        port: Port number
    
    Returns:
        list: List of server information
    """
    registry = get_server_registry()
    matching_servers = []
    
    for server_id, server_info in registry.items():
        if server_info.get('port') == port:
            matching_servers.append(server_info)
    
    return matching_servers


def remove_server(server_id: str) -> bool:
    """
    Remove a server from the registry
    
    Args:
        server_id: Identifier of the server to remove
    
    Returns:
        bool: Whether removal was successful
    """
    try:
        registry = get_server_registry()
        
        if server_id in registry:
            del registry[server_id]
            
            registry_file = _get_server_registry_file()
            return _save_registry_atomic(registry_file, registry)
        
        return False
        
    except Exception as e:
        logger.error(f"Server removal error: {e}")
        return False


def update_server_last_seen(server_id: str) -> bool:
    """
    Update the last_updated timestamp for a server
    
    Args:
        server_id: Identifier of the server
    
    Returns:
        bool: Whether update was successful
    """
    try:
        registry = get_server_registry()
        
        if server_id in registry:
            server_info = registry[server_id]
            server_info['last_updated'] = pendulum.now().isoformat()
            
            registry_file = _get_server_registry_file()
            return _save_registry_atomic(registry_file, registry)
        
        return False
        
    except Exception as e:
        logger.error(f"Server update error: {e}")
        return False


def get_local_ip() -> str:
    """
    Get the local IP address
    
    Returns:
        str: Local IP address
    """
    try:
        # Attempt to connect externally to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.warning(f"Error getting local IP: {e}")
        # Return loopback address if connection fails
        return "127.0.0.1"


def remove_stale_servers(max_age_hours: int = 24) -> int:
    """
    Remove servers that haven't been updated in a while
    
    Args:
        max_age_hours: Maximum age in hours before a server is considered stale
    
    Returns:
        int: Number of servers removed
    """
    try:
        registry = get_server_registry()
        now = pendulum.now()
        removed_count = 0
        
        for server_id in list(registry.keys()):
            server_info = registry[server_id]
            last_updated = pendulum.parse(server_info['last_updated'])
            
            if now.diff(last_updated).in_hours() > max_age_hours:
                del registry[server_id]
                removed_count += 1
        
        if removed_count > 0:
            registry_file = _get_server_registry_file()
            _save_registry_atomic(registry_file, registry)
        
        return removed_count
        
    except Exception as e:
        logger.error(f"Error removing stale servers: {e}")
        return 0