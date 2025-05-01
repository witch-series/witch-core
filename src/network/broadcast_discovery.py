#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Node discovery functionality using UDP broadcasts

This module provides functions for:
- Sending discovery broadcasts
- Broadcasting ledger data
- Managing discovered nodes
- Performing rapid node discovery
"""

import json
import time
import threading
import logging
import socket
import netifaces  # Use netifaces for better network interface handling
from datetime import datetime
from typing import Dict, List, Any, Callable

from ..protocol.ledger import register_node

# Logger configuration
logger = logging.getLogger("WitchBroadcast")


class BroadcastDiscovery:
    """
    Manages node discovery through UDP broadcasts
    """
    
    def __init__(
        self, 
        broadcast_port: int = 45678, 
        node_name: str = None, 
        node_id: str = None,
        auto_discovery_interval: int = 300,  # 5 minutes in seconds
        interactive: bool = False,
        iteration_callback: Callable = None
    ):
        """
        Initialize the broadcast discovery system
        
        Args:
            broadcast_port (int): Port to use for broadcasts
            node_name (str): Name of this node (optional)
            node_id (str): ID of this node (optional, will be generated if None)
            auto_discovery_interval (int): Interval for periodic re-discovery in seconds
            interactive (bool): Whether to prompt for confirmation before continuing iterations
            iteration_callback (Callable): Function to call for iteration confirmation
        """
        import hashlib
        
        self.broadcast_port = broadcast_port
        self.node_name = node_name
        self.node_id = node_id
        self.auto_discovery_interval = auto_discovery_interval
        
        # Interactive mode and callback for iteration control
        self.interactive = interactive
        self.iteration_callback = iteration_callback
        
        # Generate a source hash for verification
        self.src_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Non-blocking socket
        self.sock.setblocking(False)
        
        # Dictionary of discovered nodes
        self.discovered_nodes = {}
        
        # Control variables
        self.running = False
        self.receiver_thread = None
        self.sender_thread = None
        self.auto_discovery_thread = None
        
        logger.info(f"Broadcast discovery initialized on port {broadcast_port}")
    
    def start(self, listen: bool = True):
        """
        Start broadcast discovery functionality
        
        Args:
            listen (bool): Whether to start listening for broadcasts
            
        Returns:
            bool: Whether the start was successful
        """
        if self.running:
            logger.warning("Broadcast discovery is already running")
            return False
            
        try:
            # Bind to the broadcast port
            self.sock.bind(('', self.broadcast_port))
            self.running = True
            
            # Start listener thread if requested
            if listen:
                self.receiver_thread = threading.Thread(target=self._receive_broadcasts_thread)
                self.receiver_thread.daemon = True
                self.receiver_thread.start()
                logger.info(f"Started broadcast listener on port {self.broadcast_port}")
            
            # Start periodic auto-discovery if interval is set
            if self.auto_discovery_interval > 0:
                self.auto_discovery_thread = threading.Thread(target=self._auto_discovery_thread)
                self.auto_discovery_thread.daemon = True
                self.auto_discovery_thread.start()
                logger.info(f"Started periodic auto-discovery every {self.auto_discovery_interval} seconds")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to start broadcast discovery: {e}")
            logger.exception("Details:")
            return False
    
    def _auto_discovery_thread(self):
        """
        Thread that periodically initiates discovery to maintain an up-to-date node list
        """
        # Get the primary IP address of this machine using netifaces
        ip = self._get_primary_ip()
        
        # Use a default port for our node
        port = 8000
        
        while self.running:
            try:
                # Run a discovery broadcast
                self.send_discovery_broadcast(ip, port)
                logger.debug(f"Performed periodic auto-discovery")
                
                # If in interactive mode, ask for confirmation before continuing
                if self.interactive:
                    should_continue = True
                    
                    # Use the callback if provided, otherwise default to True
                    if self.iteration_callback is not None:
                        try:
                            logger.debug("Prompting user via callback: 'Continue to iterate?'")
                            should_continue = self.iteration_callback("Continue to iterate?")
                            logger.debug(f"User responded with: {should_continue}")
                        except Exception as e:
                            logger.error(f"Error in iteration callback: {e}")
                            # Add stack trace for debugging
                            logger.exception("Iteration callback exception details:")
                            # Default to stopping on error to prevent unwanted iterations
                            should_continue = False
                    
                    # If user chose not to continue, stop the auto-discovery
                    if not should_continue:
                        logger.info("Auto-discovery iterations stopped by user")
                        self.running = False
                        break
                
                # Wait for the next discovery cycle
                time.sleep(self.auto_discovery_interval)
                
            except Exception as e:
                logger.error(f"Error in auto-discovery thread: {e}")
                logger.exception("Auto-discovery error details:")
                time.sleep(60)  # Wait a minute before retrying after error

    def _get_primary_ip(self):
        """
        Get the primary IP address using netifaces
        
        Returns:
            str: IP address of the primary interface
        """
        try:
            # Get default gateway interface
            default_gateway = netifaces.gateways().get('default', {})
            if not default_gateway:
                raise ValueError("No default gateway found")
            
            # Get the interface for the default gateway
            default_interface = default_gateway.get(netifaces.AF_INET, [None])[1]
            if not default_interface:
                raise ValueError("No default interface found")
            
            # Get the IP address for the default interface
            interface_addresses = netifaces.ifaddresses(default_interface).get(netifaces.AF_INET, [])
            if not interface_addresses:
                raise ValueError(f"No IPv4 address found for interface {default_interface}")
            
            # Return the first IPv4 address
            return interface_addresses[0]['addr']
            
        except (ValueError, KeyError) as e:
            logger.warning(f"Could not determine IP address: {e}")
            # Try to get any valid IP address
            try:
                for interface in netifaces.interfaces():
                    addresses = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
                    for address in addresses:
                        ip = address.get('addr')
                        if ip and not ip.startswith('127.'):
                            return ip
            except Exception:
                pass
                
            # Fallback to loopback address
            logger.warning("Using loopback address as fallback")
            return '127.0.0.1'

    def send_discovery_broadcast(
        self, 
        source_ip: str, 
        source_port: int, 
        broadcast_addresses: list = None, 
        repeat: int = 5, 
        interval: float = 0.2,
        retry_count: int = 3,
        retry_backoff: float = 2.0
    ):
        """
        Send a broadcast to discover other nodes
        
        Args:
            source_ip (str): Source IP to include in the broadcast
            source_port (int): Source port to include in the broadcast
            broadcast_addresses (list): List of broadcast addresses to use
            repeat (int): How many times to send the broadcast
            interval (float): Interval between broadcasts in seconds
            retry_count (int): Number of retry attempts if discovery fails
            retry_backoff (float): Multiplier for backoff between retries
            
        Returns:
            bool: Whether the broadcast was sent successfully
        """
        if not self.running:
            logger.warning("Broadcast discovery is not running")
            return False
            
        # Convert node info to message
        msg_dict = {
            'type': 'discovery',
            'source_ip': source_ip,
            'source_port': source_port,
            'src_hash': self.src_hash,
            'time': time.time()
        }
        
        # Add node name and ID if available
        if self.node_name:
            msg_dict['node_name'] = self.node_name
        if self.node_id:
            msg_dict['node_id'] = self.node_id
            
        # Serialize to JSON
        msg = json.dumps(msg_dict)
        
        # Use default broadcast addresses if none provided
        if broadcast_addresses is None:
            broadcast_addresses = [
                '255.255.255.255',
                '192.168.255.255',
                '10.255.255.255',
                '172.16.255.255'
            ]
            
        # Start a thread to send the broadcasts
        self.sender_thread = threading.Thread(
            target=self._send_broadcast_with_retry,
            args=(msg, source_ip, broadcast_addresses, repeat, interval, retry_count, retry_backoff)
        )
        self.sender_thread.daemon = True
        self.sender_thread.start()
        
        return True

    def _send_broadcast_with_retry(
        self, 
        msg, 
        source_ip, 
        broadcast_addresses, 
        repeat, 
        interval,
        retry_count,
        retry_backoff
    ):
        """
        Helper method to send broadcasts with retry logic and exponential backoff
        """
        discovered_before = len(self.discovered_nodes)
        current_retry = 0
        current_interval = interval
        
        while current_retry <= retry_count:
            try:
                # Send the broadcasts
                self._send_broadcast_thread(msg, source_ip, broadcast_addresses, repeat, current_interval)
                
                # Wait for discovery to complete (give it time to process responses)
                time.sleep(2.0)
                
                # Check if we've discovered any new nodes
                discovered_after = len(self.discovered_nodes)
                if discovered_after > discovered_before:
                    logger.info(f"Discovery successful, found {discovered_after - discovered_before} new nodes")
                    return
                
                # If no new nodes were found, retry with exponential backoff
                current_retry += 1
                if current_retry <= retry_count:
                    wait_time = current_interval * retry_backoff
                    logger.debug(f"No new nodes found, retrying in {wait_time:.2f} seconds (attempt {current_retry}/{retry_count})")
                    time.sleep(wait_time)
                    current_interval *= retry_backoff
            
            except Exception as e:
                logger.error(f"Error in broadcast retry: {e}")
                current_retry += 1
                if current_retry <= retry_count:
                    wait_time = current_interval * retry_backoff
                    logger.debug(f"Error in broadcast, retrying in {wait_time:.2f} seconds (attempt {current_retry}/{retry_count})")
                    time.sleep(wait_time)
                    current_interval *= retry_backoff
                    
        if current_retry > retry_count:
            logger.warning(f"Discovery retry limit reached after {retry_count} attempts")

    def _send_broadcast_thread(self, msg, source_ip, broadcast_addresses, repeat, interval):
        """
        Thread to send broadcast messages
        """
        try:
            # Convert message to bytes
            msg_bytes = msg.encode()
            
            # Try each broadcast address
            for broadcast_addr in broadcast_addresses:
                try:
                    # Send the broadcast multiple times
                    for i in range(repeat):
                        try:
                            self.sock.sendto(msg_bytes, (broadcast_addr, self.broadcast_port))
                            logger.debug(f"Sent discovery broadcast to {broadcast_addr}:{self.broadcast_port}")
                            time.sleep(interval)
                        except Exception as e:
                            logger.error(f"Failed to send broadcast to {broadcast_addr}: {e}")
                except Exception as e:
                    logger.error(f"Error broadcasting to {broadcast_addr}: {e}")
            
        except Exception as e:
            logger.error(f"Error in broadcast thread: {e}")

    def send_ledger_broadcast(self, ledger_data: Dict[str, Any]):
        """
        Broadcast ledger data
        
        Args:
            ledger_data: Ledger data to send
            
        Returns:
            bool: Whether the sending was successful
        """
        if not self.running:
            logger.warning("Broadcast functionality is not running")
            return False
        
        try:
            # Create broadcast message
            message = {
                'type': 'ledger_sync',
                'node_id': self.node_id,
                'hash': self.src_hash,
                'ledger': ledger_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Serialize data
            data = json.dumps(message).encode('utf-8')
            
            # List of broadcast addresses to try
            broadcast_addresses = [
                '255.255.255.255',  # Global broadcast
                '192.168.255.255',  # Common class C network
                '172.16.255.255',   # Common class B network
                '10.255.255.255',   # Common class A network
                '127.0.0.1'         # Loopback (for testing on same machine)
            ]
            
            success = False
            # Try each broadcast address
            for broadcast_addr in broadcast_addresses:
                try:
                    # Send broadcast
                    self.sock.sendto(data, (broadcast_addr, self.broadcast_port))
                    logger.debug(f"Sent ledger broadcast to {broadcast_addr}")
                    success = True
                except Exception as e:
                    logger.debug(f"Failed to send ledger to {broadcast_addr}: {e}")
            
            if success:
                logger.info("Broadcasted ledger data successfully")
                return True
            else:
                logger.warning("Failed to broadcast ledger data to any address")
                return False
            
        except Exception as e:
            logger.error(f"Error broadcasting ledger: {e}")
            logger.exception("Details:")  # Log stack trace
            return False


    def get_discovered_nodes(self, max_age_minutes: int = 10) -> Dict[str, Dict[str, Any]]:
        """
        Return the list of discovered nodes
        
        Args:
            max_age_minutes (int): Remove information older than this time (minutes)
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of node information keyed by node ID
        """
        current_time = datetime.now()
        valid_nodes = {}
        
        for node_id, node_info in self.discovered_nodes.items():
            try:
                last_seen = datetime.fromisoformat(node_info.get('last_seen', '2000-01-01T00:00:00'))
                age_minutes = (current_time - last_seen).total_seconds() / 60
                
                if age_minutes <= max_age_minutes:
                    valid_nodes[node_id] = node_info
            except (ValueError, TypeError):
                # Skip if date format is invalid
                pass
        
        return valid_nodes


# Add this standalone function to bridge the gap for older imports
def send_discovery_broadcast(source_ip: str, source_port: int, broadcast_addresses: list = None, 
                           repeat: int = 5, interval: float = 0.2, node_id: str = None, 
                           node_name: str = None):
    """
    Send a broadcast to discover other nodes (standalone function)
    
    Args:
        source_ip (str): Source IP to include in the broadcast
        source_port (int): Source port to include in the broadcast
        broadcast_addresses (list): List of broadcast addresses to use
        repeat (int): How many times to send the broadcast
        interval (float): Interval between broadcasts in seconds
        node_id (str): ID of this node (optional)
        node_name (str): Name of this node (optional)
    
    Returns:
        bool: Whether the broadcast was sent successfully
    """
    try:
        # Create a temporary instance of BroadcastDiscovery
        bd = BroadcastDiscovery(node_id=node_id, node_name=node_name)
        bd.start(listen=False)
        
        # Send the discovery broadcast
        success = bd.send_discovery_broadcast(
            source_ip=source_ip,
            source_port=source_port,
            broadcast_addresses=broadcast_addresses,
            repeat=repeat,
            interval=interval
        )
        
        return success
    except Exception as e:
        logger.error(f"Error in standalone send_discovery_broadcast: {e}")
        return False

# Add this standalone function for legacy code that might be importing it directly
def _send_discovery_broadcast_thread(msg, source_ip, broadcast_addresses, repeat, interval):
    """
    Standalone function to send broadcast messages
    
    Args:
        msg (str): JSON message to send
        source_ip (str): Source IP to include in the broadcast
        broadcast_addresses (list): List of broadcast addresses to use
        repeat (int): How many times to send the broadcast
        interval (float): Interval between broadcasts in seconds
    """
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Convert message to bytes
        msg_bytes = msg.encode()
        broadcast_port = 45678  # Default port
            
        # Try each broadcast address
        for broadcast_addr in broadcast_addresses:
            try:
                # Send the broadcast multiple times
                for i in range(repeat):
                    try:
                        sock.sendto(msg_bytes, (broadcast_addr, broadcast_port))
                        logger.debug(f"Sent discovery broadcast to {broadcast_addr}:{broadcast_port}")
                        time.sleep(interval)
                    except Exception as e:
                        logger.error(f"Failed to send broadcast to {broadcast_addr}: {e}")
            except Exception as e:
                logger.error(f"Error broadcasting to {broadcast_addr}: {e}")
        
    except Exception as e:
        logger.error(f"Error in broadcast thread: {e}")
    finally:
        try:
            sock.close()
        except:
            pass

# Add this standalone function for legacy code
def send_ledger_broadcast(ledger_data, node_id=None):
    """
    Standalone function to broadcast ledger data
    
    Args:
        ledger_data: Ledger data to send
        node_id: Optional node ID to include
        
    Returns:
        bool: Whether the sending was successful
    """
    try:
        # Create a temporary instance of BroadcastDiscovery
        bd = BroadcastDiscovery(node_id=node_id)
        bd.start(listen=False)
        
        # Send the ledger broadcast
        success = bd.send_ledger_broadcast(ledger_data)
        
        return success
    except Exception as e:
        logger.error(f"Error in standalone send_ledger_broadcast: {e}")
        return False

# Add standalone function for getting discovered nodes
def get_discovered_nodes(max_age_minutes: int = 10):
    """
    Standalone function to return discovered nodes (for backward compatibility)
    
    Args:
        max_age_minutes (int): Remove information older than this time (minutes)
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of node information keyed by node ID
    """
    try:
        # Since this is a standalone function, we can't easily keep track of discovered nodes
        # Return an empty dictionary as a fallback
        logger.warning("get_discovered_nodes called outside of a BroadcastDiscovery instance")
        return {}
    except Exception as e:
        logger.error(f"Error in standalone get_discovered_nodes: {e}")
        return {}