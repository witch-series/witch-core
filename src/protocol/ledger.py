#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module providing distributed ledger functionality

This module includes the following features:
- Registration and management of node information
- Protocol definition management
- Ledger integrity verification
- Ledger synchronization between nodes
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set

from ..utils import file_utils
from ..utils.hash_utils import calculate_src_directory_hash, verify_src_integrity


# Path to the ledger file
def _get_ledger_file_path() -> str:
    """Get the path to the ledger file"""
    return os.path.join(file_utils._get_tmp_directory(), "ledger.json")


def _create_default_ledger() -> Dict[str, Any]:
    """Create default ledger data"""
    return {
        "nodes": [],
        "protocols": [],
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


def _create_node_entry(
    node_id: str,
    ip: str,
    port: int,
    src_hash: str,
    name: Optional[str] = None,
    protocols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a node entry
    
    Args:
        node_id: Unique ID for the node
        ip: IP address of the node
        port: Port number of the node
        src_hash: Hash value of the source code
        name: Node name (uses node ID if not specified)
        protocols: List of supported protocol names
        
    Returns:
        Dict[str, Any]: Dictionary of node information
    """
    return {
        "id": node_id,
        "ip": ip,
        "port": port,
        "hash": src_hash,
        "name": name or node_id,
        "protocols": protocols or [],
        "updated": datetime.now().isoformat(),
        "status": "active"
    }


def load_ledger() -> Dict[str, Any]:
    """
    Load the ledger. Create a new one if it doesn't exist.
    
    Returns:
        Dict[str, Any]: Ledger data
    """
    ledger_path = _get_ledger_file_path()
    
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Failed to load the ledger file. Creating a new one.")
            return _create_default_ledger()
    else:
        return _create_default_ledger()


def save_ledger(ledger_data: Dict[str, Any]) -> bool:
    """
    Save the ledger to a file
    
    Args:
        ledger_data: Ledger data to save
        
    Returns:
        bool: Whether the save was successful
    """
    ledger_path = _get_ledger_file_path()
    
    # Update the modification timestamp
    ledger_data["updated_at"] = datetime.now().isoformat()
    
    try:
        with open(ledger_path, 'w', encoding='utf-8') as f:
            json.dump(ledger_data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"Error: Failed to save ledger: {e}")
        return False


def register_node(
    ip: str, 
    port: int, 
    protocols: List[str] = None, 
    name: str = None,
    node_id: str = None
) -> str:
    """
    Register a node in the ledger
    
    Args:
        ip: IP address of the node
        port: Port number of the node
        protocols: List of supported protocol names
        name: Node name (auto-generated if not specified)
        node_id: Node ID (auto-generated if not specified)
        
    Returns:
        str: ID of the registered node
    """
    # Calculate the hash of the src directory
    src_hash, _ = calculate_src_directory_hash()
    
    # Generate node ID if not provided
    if node_id is None:
        node_id = str(uuid.uuid4())
    
    # Generate node name from IP and port if not provided
    if name is None:
        name = f"node-{ip}-{port}"
    
    # Load the ledger
    ledger = load_ledger()
    
    # Check for existing node entry
    existing_node = None
    for node in ledger["nodes"]:
        if node.get("id") == node_id or (node.get("ip") == ip and node.get("port") == port):
            existing_node = node
            break
    
    if existing_node:
        # Update existing node
        existing_node["ip"] = ip
        existing_node["port"] = port
        existing_node["hash"] = src_hash
        existing_node["name"] = name
        existing_node["protocols"] = protocols or existing_node.get("protocols", [])
        existing_node["updated"] = datetime.now().isoformat()
        existing_node["status"] = "active"
    else:
        # Create new node entry
        node_entry = _create_node_entry(
            node_id=node_id,
            ip=ip,
            port=port,
            src_hash=src_hash,
            name=name,
            protocols=protocols
        )
        ledger["nodes"].append(node_entry)
    
    # Save the ledger
    save_ledger(ledger)
    
    return node_id


def get_node_by_id(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Get node information by ID
    
    Args:
        node_id: ID of the node to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: Node information, or None if not found
    """
    ledger = load_ledger()
    
    for node in ledger["nodes"]:
        if node.get("id") == node_id:
            return node
    
    return None


def get_compatible_nodes(src_hash: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get a list of compatible nodes
    
    Args:
        src_hash: Hash value of the source code (uses current hash if not specified)
        
    Returns:
        List[Dict[str, Any]]: List of compatible nodes
    """
    if src_hash is None:
        src_hash, _ = calculate_src_directory_hash()
    
    ledger = load_ledger()
    compatible_nodes = []
    
    for node in ledger["nodes"]:
        if node.get("hash") == src_hash and node.get("status") == "active":
            compatible_nodes.append(node)
    
    return compatible_nodes


def register_protocol(
    protocol_id: str,
    name: str,
    format_str: str,
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Register a protocol definition in the ledger
    
    Args:
        protocol_id: Unique ID for the protocol
        name: Protocol name
        format_str: Protocol format string
        options: Protocol options settings
        
    Returns:
        bool: Whether the registration was successful
    """
    ledger = load_ledger()
    
    # Check for existing protocol definition
    existing_protocol = None
    for protocol in ledger["protocols"]:
        if protocol.get("id") == protocol_id or protocol.get("name") == name:
            existing_protocol = protocol
            break
    
    if existing_protocol:
        # Update existing protocol definition
        existing_protocol["name"] = name
        existing_protocol["format"] = format_str
        existing_protocol["options"] = options or existing_protocol.get("options", {})
        existing_protocol["updated"] = datetime.now().isoformat()
    else:
        # Create new protocol definition
        protocol_entry = {
            "id": protocol_id,
            "name": name,
            "format": format_str,
            "options": options or {},
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        }
        ledger["protocols"].append(protocol_entry)
    
    # Save the ledger
    return save_ledger(ledger)


def merge_ledgers(remote_ledger: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge remote ledger information with the current ledger
    
    Args:
        remote_ledger: Remote ledger data to merge
        
    Returns:
        Dict[str, Any]: Merged ledger data
    """
    local_ledger = load_ledger()
    
    # Node merge
    node_map = {node.get("id"): node for node in local_ledger["nodes"]}
    
    for remote_node in remote_ledger.get("nodes", []):
        node_id = remote_node.get("id")
        if node_id:
            if node_id in node_map:
                # For existing nodes, adopt the one with the most recent update time
                local_updated = datetime.fromisoformat(node_map[node_id].get("updated", "2000-01-01T00:00:00"))
                remote_updated = datetime.fromisoformat(remote_node.get("updated", "2000-01-01T00:00:00"))
                
                if remote_updated > local_updated:
                    node_map[node_id] = remote_node
            else:
                # For new nodes, add them
                node_map[node_id] = remote_node
    
    # Protocol merge
    protocol_map = {protocol.get("id"): protocol for protocol in local_ledger["protocols"]}
    
    for remote_protocol in remote_ledger.get("protocols", []):
        protocol_id = remote_protocol.get("id")
        if protocol_id:
            if protocol_id in protocol_map:
                # For existing protocols, adopt the one with the most recent update time
                local_updated = datetime.fromisoformat(protocol_map[protocol_id].get("updated", "2000-01-01T00:00:00"))
                remote_updated = datetime.fromisoformat(remote_protocol.get("updated", "2000-01-01T00:00:00"))
                
                if remote_updated > local_updated:
                    protocol_map[protocol_id] = remote_protocol
            else:
                # For new protocols, add them
                protocol_map[protocol_id] = remote_protocol
    
    # Build the merged result as a new ledger
    merged_ledger = {
        "nodes": list(node_map.values()),
        "protocols": list(protocol_map.values()),
        "version": remote_ledger.get("version", local_ledger.get("version", "1.0.0")),
        "created_at": local_ledger.get("created_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat()
    }
    
    # Save the merged ledger
    save_ledger(merged_ledger)
    
    return merged_ledger


def verify_node_compatibility(node_info: Dict[str, Any]) -> bool:
    """
    Verify node compatibility
    
    Args:
        node_info: Node information to verify
        
    Returns:
        bool: True if compatible, False if not
    """
    src_hash, _ = calculate_src_directory_hash()
    node_hash = node_info.get("hash", "")
    
    return src_hash == node_hash


def clean_inactive_nodes(max_age_hours: int = 24) -> int:
    """
    Mark nodes that haven't been updated for a certain time as inactive
    
    Args:
        max_age_hours: Maximum allowed inactive time (in hours)
        
    Returns:
        int: Number of nodes marked as inactive
    """
    ledger = load_ledger()
    now = datetime.now()
    inactive_count = 0
    
    for node in ledger["nodes"]:
        try:
            updated = datetime.fromisoformat(node.get("updated", "2000-01-01T00:00:00"))
            age_hours = (now - updated).total_seconds() / 3600
            
            if age_hours > max_age_hours and node.get("status") == "active":
                node["status"] = "inactive"
                inactive_count += 1
        except (ValueError, TypeError):
            # Invalid date format
            node["status"] = "inactive"
            inactive_count += 1
    
    if inactive_count > 0:
        save_ledger(ledger)
    
    return inactive_count