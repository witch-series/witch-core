#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module providing node discovery and communication functionality using UDP broadcasts

This is the main entry point for broadcast functionality. It imports and re-exports
the components from the modular broadcast-related modules.

This module includes the following features:
- Fast broadcast transmission
- Broadcast listener
- Node information exchange
- Distributed ledger synchronization
"""

# Export the main BroadcastManager class
from .broadcast_manager import BroadcastManager

# Export the utility functions
from .broadcast_utils import rapid_node_discovery

# For backward compatibility, import specific functionality
from .broadcast_handlers import _handle_discovery_message, _handle_ledger_sync
from .broadcast_discovery import (
    send_discovery_broadcast, 
    _send_discovery_broadcast_thread,
    send_ledger_broadcast,
    get_discovered_nodes
)

__all__ = [
    'BroadcastManager',
    'rapid_node_discovery',
]


if __name__ == "__main__":
    # Test behavior when this script is executed directly
    import socket
    
    # Get local IP address
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    
    print(f"Local IP address: {ip_address}")
    print("Performing rapid node discovery...")
    
    discovered = rapid_node_discovery(
        ip=ip_address,
        port=8888,
        node_name="TestNode"
    )
    
    print(f"Number of discovered nodes: {len(discovered)}")
    for node_id, info in discovered.items():
        print(f"- {info.get('name')} ({info.get('ip')}:{info.get('port')})")