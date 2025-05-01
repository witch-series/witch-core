#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for network broadcasting in Witch Core.
"""

import socket
import logging
import netifaces
import time
from typing import List, Dict, Any, Optional

from .broadcast_manager import BroadcastManager

logger = logging.getLogger("WitchBroadcast")

def get_local_ip_addresses() -> List[str]:
    """
    Get all local IP addresses using netifaces package
    
    Returns:
        List[str]: List of local IP addresses
    """
    addresses = []
    
    try:
        # Get all interfaces except loopback
        for interface in netifaces.interfaces():
            iface_data = netifaces.ifaddresses(interface)
            # Get IPv4 addresses (AF_INET)
            if netifaces.AF_INET in iface_data:
                for addr_info in iface_data[netifaces.AF_INET]:
                    if 'addr' in addr_info:
                        ip = addr_info['addr']
                        if ip != '127.0.0.1' and ip.count('.') == 3:  # Basic IPv4 validation
                            addresses.append(ip)
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
        # Fallback to socket-based discovery
        fallback_ip = socket_get_local_ip()
        if fallback_ip:
            addresses.append(fallback_ip)
    
    # If no IPs found, try fallback method
    if not addresses:
        fallback_ip = socket_get_local_ip()
        if fallback_ip:
            addresses.append(fallback_ip)
    
    return addresses

def socket_get_local_ip() -> Optional[str]:
    """
    Fallback method to get local IP using socket
    
    Returns:
        Optional[str]: Local IP address if found, None otherwise
    """
    try:
        # Create a socket to determine outgoing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Doesn't actually connect but sets up socket for outgoing connection
        s.connect(('8.8.8.8', 53))  # Google's DNS
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Fallback IP detection failed: {e}")
        return None

def get_broadcast_addresses() -> List[str]:
    """
    Get broadcast addresses for all network interfaces
    
    Returns:
        List[str]: List of broadcast addresses
    """
    broadcast_addresses = []
    
    try:
        for interface in netifaces.interfaces():
            iface_data = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in iface_data:
                for addr_info in iface_data[netifaces.AF_INET]:
                    if 'broadcast' in addr_info:
                        broadcast_addresses.append(addr_info['broadcast'])
    except Exception as e:
        logger.error(f"Error getting broadcast addresses: {e}")
        # Default to standard broadcast address
        broadcast_addresses.append('255.255.255.255')
        
    # If no broadcast addresses found, add default
    if not broadcast_addresses:
        broadcast_addresses.append('255.255.255.255')
        
    return broadcast_addresses

def rapid_node_discovery(
    ip: str, 
    port: int, 
    broadcast_port: int = 8890,
    protocols: List[str] = None,
    count: int = 10,
    interval: float = 0.2,
    wait_time: float = 3.0,
    node_name: str = None
) -> Dict[str, Dict[str, Any]]:
    """
    Perform rapid node discovery and return the list of discovered nodes
    
    Args:
        ip (str): IP address of this node
        port (int): Port where this node is listening
        broadcast_port (int): Port used for broadcasting
        protocols (List[str]): List of supported protocols
        count (int): Number of broadcasts
        interval (float): Interval between broadcasts (seconds)
        wait_time (float): Time to wait for discovery (seconds)
        node_name (str): Name of this node
        
    Returns:
        Dict[str, Dict[str, Any]]: Information of discovered nodes
    """
    manager = BroadcastManager(port=broadcast_port, node_name=node_name)
    
    # Start broadcast functionality
    if not manager.start():
        logger.error("Failed to start broadcast functionality")
        return {}
    
    try:
        # Send discovery broadcast
        manager.send_discovery_broadcast(ip, port, protocols, count, interval)
        
        # Wait for responses from other nodes
        logger.info(f"Waiting for responses for {wait_time} seconds...")
        time.sleep(wait_time)
        
        # Get discovered nodes
        return manager.get_discovered_nodes()
        
    finally:
        # Stop broadcast functionality
        manager.stop()