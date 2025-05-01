#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Core broadcast manager for node discovery and communication using UDP broadcasts

This module provides the main BroadcastManager class that handles:
- Socket initialization and management
- Starting and stopping broadcast functionality
- Thread management for listeners and senders
"""

import socket
import json
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable, Union

from ..utils.hash_utils import calculate_src_directory_hash
from ..protocol.ledger import register_node, merge_ledgers, verify_node_compatibility

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WitchBroadcast")


class BroadcastManager:
    """
    Class to manage node discovery and communication using broadcasts
    """
    
    def __init__(self, port=8890, node_id=None, node_name=None):
        """
        Initialize the Broadcast Manager
        
        Args:
            port (int): Port number used for broadcasting
            node_id (str): Identifier for this node (auto-generated if omitted)
            node_name (str): Name of this node (auto-generated if omitted)
        """
        self.broadcast_port = port
        self.node_id = node_id
        self.node_name = node_name
        self.sock = None
        self.running = False
        self.sender_thread = None
        self.listener_thread = None
        self.discovered_nodes = {}  # {node_id: node_info}
        
        # Calculate hash value of src
        self.src_hash, _ = calculate_src_directory_hash()
        
        # Callback functions
        self.on_node_discovered = None  # (node_info) -> None
        self.on_ledger_received = None  # (ledger_data) -> None
        
    def start(self):
        """
        Start the broadcast functionality
        
        Returns:
            bool: Whether the start was successful
        """
        if self.running:
            logger.warning("Broadcast functionality is already running")
            return False
        
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            try:
                # Bind to a specific port for listening
                self.sock.bind(('0.0.0.0', self.broadcast_port))
                logger.info(f"Bound to UDP port {self.broadcast_port}")
            except OSError as e:
                logger.error(f"Failed to bind to port {self.broadcast_port}: {e}")
                return False
            
            self.running = True
            
            # Start listener thread
            self.listener_thread = threading.Thread(target=self._listen_for_broadcasts)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            logger.info(f"Started broadcast listener (port {self.broadcast_port})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting broadcast functionality: {e}")
            if self.sock:
                self.sock.close()
                self.sock = None
            self.running = False
            return False
    
    def stop(self):
        """
        Stop the broadcast functionality
        """
        if not self.running:
            logger.warning("Broadcast functionality is not running")
            return
        
        self.running = False
        
        # Stop threads
        if self.sender_thread and self.sender_thread.is_alive():
            self.sender_thread.join(timeout=1.0)
        
        # Close socket
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            self.sock = None
        
        logger.info("Stopped broadcast functionality")
    
    def _listen_for_broadcasts(self):
        """
        Thread process for listening to broadcast messages
        """
        if not self.sock:
            logger.error("No listening socket available")
            return
        
        while self.running:
            try:
                # Wait for reception (with timeout)
                self.sock.settimeout(1.0)
                data, addr = self.sock.recvfrom(8192)  # Receive with larger buffer size
                
                try:
                    # Parse data
                    message = json.loads(data.decode('utf-8'))
                    message_type = message.get('type')
                    
                    # Ignore messages from self
                    if message.get('node_id') == self.node_id:
                        continue
                    
                    # Process based on type
                    if message_type == 'node_discovery':
                        self._handle_discovery_message(message, addr)
                    elif message_type == 'ledger_sync':
                        self._handle_ledger_sync(message, addr)
                    else:
                        logger.debug(f"Unknown broadcast message type: {message_type}")
                
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON data: {addr}")
                except Exception as e:
                    logger.error(f"Error processing broadcast message: {e}")
            
            except socket.timeout:
                # Timeout is normal, continue loop
                pass
            except Exception as e:
                if self.running:  # Log error only if running
                    logger.error(f"Error receiving broadcast: {e}")
                break
    
    # Import handlers from broadcast_handlers.py
    from .broadcast_handlers import _handle_discovery_message, _handle_ledger_sync
    
    # Import discovery methods from broadcast_discovery.py
    from .broadcast_discovery import (
        send_discovery_broadcast,
        _send_discovery_broadcast_thread,
        send_ledger_broadcast,
        get_discovered_nodes
    )