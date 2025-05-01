#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Port Management Utility Functions

This module includes functions related to port management,
such as checking for ports in use, registering/unregistering ports,
and suggesting available ports for use.

Enhanced with:
- orjson for faster JSON processing
- psutil for better port usage detection
- portend for more reliable port checking
- enhanced error handling and type annotations
"""

import os
import random
import socket
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Set, Tuple, Any
import orjson
import psutil
import portend

# Logger configuration
logger = logging.getLogger("WitchPorts")

# Path to the file storing port registration information
_PORT_REGISTRY_FILE = Path(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tmp", "port_registry.json")


def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """
    Check if the specified port is currently in use.
    Uses multiple methods for more reliable detection.

    Args:
        port: Port number to check
        host: Hostname or IP address

    Returns:
        bool: True if the port is in use, False otherwise
    """
    # First check using psutil (most reliable but only checks localhost)
    if host in ('localhost', '127.0.0.1', '::1'):
        connections = psutil.net_connections()
        for conn in connections:
            if conn.laddr.port == port:
                return True
    
    # Then check using portend (reliable TCP check)
    try:
        portend.free(host, port, timeout=1.0)
        return False
    except portend.Timeout:
        return True
    except portend.PortNotFree:
        return True
    except Exception as e:
        logger.warning(f"Error checking port {port} with portend: {e}")
        # Fall back to socket method
        pass
    
    # Finally try with direct socket connection
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((host, port))
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False
    except Exception as e:
        logger.warning(f"Error checking port {port} with socket: {e}")
        return True  # Return True for safety in case of an error


def _ensure_port_registry_exists() -> None:
    """
    Ensure that the port registry file exists.
    If it does not exist, create a new empty registry file.
    """
    os.makedirs(os.path.dirname(_PORT_REGISTRY_FILE), exist_ok=True)
    
    if not _PORT_REGISTRY_FILE.exists():
        with open(_PORT_REGISTRY_FILE, 'wb') as f:
            f.write(orjson.dumps({}))


def is_port_registered(port: int) -> bool:
    """
    Check if the specified port is registered.

    Args:
        port: Port number to check

    Returns:
        bool: True if the port is registered, False otherwise
    """
    _ensure_port_registry_exists()
    
    try:
        with open(_PORT_REGISTRY_FILE, 'rb') as f:
            registry = orjson.loads(f.read())
            return str(port) in registry
    except (Exception, orjson.JSONDecodeError) as e:
        logger.error(f"Error checking port registration: {e}")
        return False


def register_port(port: int, server_id: str, protocol_names: Optional[List[str]] = None, 
                 description: Optional[str] = None) -> bool:
    """
    Register a port and associate it with a server ID.

    Args:
        port: Port number to register
        server_id: Server ID to associate
        protocol_names: List of supported protocol names
        description: Description of the port

    Returns:
        bool: True if registration is successful, False otherwise
    """
    _ensure_port_registry_exists()
    
    try:
        # Load existing registry
        with open(_PORT_REGISTRY_FILE, 'rb') as f:
            try:
                registry = orjson.loads(f.read())
            except orjson.JSONDecodeError:
                registry = {}
        
        port_str = str(port)
        registry[port_str] = {
            'server_id': server_id,
            'protocols': protocol_names or [],
            'description': description or f'Port {port} for server {server_id}'
        }
        
        # Write registry with atomic write pattern
        with open(f"{_PORT_REGISTRY_FILE}.tmp", 'wb') as f:
            f.write(orjson.dumps(registry, option=orjson.OPT_INDENT_2))
        
        os.replace(f"{_PORT_REGISTRY_FILE}.tmp", _PORT_REGISTRY_FILE)
        
        return True
    except Exception as e:
        logger.error(f"Error registering port {port}: {str(e)}")
        return False


def unregister_port(port: int) -> bool:
    """
    Unregister a registered port.

    Args:
        port: Port number to unregister

    Returns:
        bool: True if unregistration is successful, False otherwise
    """
    _ensure_port_registry_exists()
    
    try:
        with open(_PORT_REGISTRY_FILE, 'rb') as f:
            registry = orjson.loads(f.read())
        
        port_str = str(port)
        if port_str in registry:
            del registry[port_str]
            
            # Write registry with atomic write pattern
            with open(f"{_PORT_REGISTRY_FILE}.tmp", 'wb') as f:
                f.write(orjson.dumps(registry, option=orjson.OPT_INDENT_2))
            
            os.replace(f"{_PORT_REGISTRY_FILE}.tmp", _PORT_REGISTRY_FILE)
            
            return True
        return False
    except Exception as e:
        logger.error(f"Error unregistering port {port}: {str(e)}")
        return False


def get_registered_server_info(port: int) -> Optional[Dict[str, Any]]:
    """
    Get server information registered to the specified port.

    Args:
        port: Port number to retrieve information for

    Returns:
        dict: Server information associated with the port, or None if not registered
    """
    _ensure_port_registry_exists()
    
    try:
        with open(_PORT_REGISTRY_FILE, 'rb') as f:
            registry = orjson.loads(f.read())
        
        port_str = str(port)
        if port_str in registry:
            return registry[port_str]
        return None
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return None


def list_registered_ports() -> Dict[str, Any]:
    """
    Get a list of all registered ports.

    Returns:
        dict: Dictionary with port numbers as keys and server information as values
    """
    _ensure_port_registry_exists()
    
    try:
        with open(_PORT_REGISTRY_FILE, 'rb') as f:
            registry = orjson.loads(f.read())
        return registry
    except Exception as e:
        logger.error(f"Error listing ports: {e}")
        return {}


def suggest_port_for_protocol(protocol_name: str, start_port: int = 8000, 
                             end_port: int = 9000) -> Optional[int]:
    """
    Suggest a recommended port for the specified protocol.
    First checks existing ports for the protocol, then finds an available port.

    Args:
        protocol_name: Protocol name
        start_port: Starting port for search
        end_port: Ending port for search

    Returns:
        int: Recommended port number, or None if no available port is found
    """
    # First, check registered ports
    registry = list_registered_ports()
    
    # Look for ports supporting the same protocol
    for port_str, info in registry.items():
        if protocol_name in info.get('protocols', []) and not is_port_in_use(int(port_str)):
            return int(port_str)
    
    # Search for a new available port
    return get_random_available_port(start_port, end_port)


def scan_ports(start_port: int = 8000, end_port: int = 9000) -> Dict[int, bool]:
    """
    Scan a range of ports to determine which are in use.

    Args:
        start_port: Starting port for scan
        end_port: Ending port for scan

    Returns:
        Dict[int, bool]: Dictionary with port numbers as keys and usage status as values
    """
    results = {}
    
    # Use psutil to get all connections (faster than individual checks)
    in_use_ports = set()
    try:
        connections = psutil.net_connections()
        for conn in connections:
            if conn.laddr.port >= start_port and conn.laddr.port <= end_port:
                in_use_ports.add(conn.laddr.port)
    except psutil.AccessDenied:
        # Fall back to individual checks if we don't have permission to get all connections
        for port in range(start_port, end_port + 1):
            results[port] = is_port_in_use(port)
        return results
    
    # Create results dictionary
    for port in range(start_port, end_port + 1):
        results[port] = port in in_use_ports
            
    return results


def get_random_available_port(start_port: int = 8000, end_port: int = 9000, 
                             max_attempts: int = 50) -> Optional[int]:
    """
    Find a random available port within the specified range.

    Args:
        start_port: Starting port for search
        end_port: Ending port for search
        max_attempts: Maximum number of attempts

    Returns:
        int: Available port number, or None if no available port is found
    """
    # First try a quick scan to find available ports
    if end_port - start_port < 1000:  # Only scan if range is reasonably small
        port_status = scan_ports(start_port, end_port)
        available_ports = [port for port, in_use in port_status.items() 
                          if not in_use and not is_port_registered(port)]
        if available_ports:
            return random.choice(available_ports)
    
    # Fall back to random sampling
    attempts = 0
    while attempts < max_attempts:
        port = random.randint(start_port, end_port)
        if not is_port_in_use(port) and not is_port_registered(port):
            return port
        attempts += 1
    
    # Sequential search as last resort
    for port in range(start_port, end_port + 1):
        if not is_port_in_use(port) and not is_port_registered(port):
            return port
    
    return None