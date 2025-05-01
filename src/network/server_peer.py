#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for server-to-server peer connection functionality.

This module provides:
- Server-to-server communication and data exchange
- Peer list management and peer discovery
- Source hash-based compatibility verification
- Project-based server isolation
"""

import json
import socket
import threading
import time
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime

from ..utils.hash_utils import calculate_src_directory_hash
from ..protocol.ledger import load_ledger, get_compatible_nodes, register_node
from .client import Client

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WitchServerPeer")


class ServerPeer:
    """
    Manages peer connections between servers.
    """
    
    def __init__(self, server, project_id: str = None):
        """
        Initialize a ServerPeer instance.
        
        Args:
            server: Parent server instance
            project_id: Project identifier this server belongs to
        """
        self.server = server
        self.project_id = project_id or "default"
        
        # Connected peers {node_id: peer_info}
        self.connected_peers = {}
        
        # Discovered peers {node_id: peer_info}
        self.discovered_peers = {}
        
        # Client connections {node_id: client}
        self.peer_clients = {}
        
        # Peer discovery thread
        self.discovery_thread = None
        self.discovery_running = False
        
        # Source hash
        self.src_hash, _ = calculate_src_directory_hash()
    
    def start(self):
        """
        Start peer discovery and connection.
        
        Returns:
            bool: Whether successfully started
        """
        if self.discovery_running:
            logger.warning("Peer discovery is already running")
            return False
        
        self.discovery_running = True
        
        # Start peer discovery thread
        self.discovery_thread = threading.Thread(target=self._peer_discovery_thread)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        
        logger.info(f"Started server peer discovery (project: {self.project_id})")
        return True
    
    def stop(self):
        """
        Stop peer discovery and connection.
        """
        if not self.discovery_running:
            return
        
        self.discovery_running = False
        
        # Disconnect all peer connections
        for peer_id, client in list(self.peer_clients.items()):
            self._disconnect_peer(peer_id)
        
        # Wait for thread termination
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=1.0)
        
        logger.info("Stopped server peer discovery")
    
    def _peer_discovery_thread(self):
        """
        Thread process for continuous peer discovery.
        """
        while self.discovery_running:
            try:
                # Search for compatible nodes
                self._discover_compatible_peers()
                
                # Connect to new compatible peers
                self._connect_to_new_peers()
                
                # Check connection status
                self._check_peer_connections()
                
            except Exception as e:
                logger.error(f"Error during peer discovery: {e}")
            
            # Sleep until next discovery (10 seconds)
            for _ in range(10):
                if not self.discovery_running:
                    break
                time.sleep(1)
    
    def _discover_compatible_peers(self):
        """
        Discover compatible server peers from the ledger.
        """
        # Get compatible nodes
        compatible_nodes = get_compatible_nodes(self.src_hash)
        
        # Filter nodes that belong to the same project
        project_nodes = []
        for node in compatible_nodes:
            node_protocols = node.get("protocols", [])
            
            # Check if project ID is included in protocols
            project_tag = f"PROJECT:{self.project_id}"
            if project_tag in node_protocols:
                # Exclude self
                if node.get("id") != self.server.server_id:
                    project_nodes.append(node)
        
        # Update discovered peers
        current_time = datetime.now().isoformat()
        for node in project_nodes:
            node_id = node.get("id")
            
            # Update or add peer info
            self.discovered_peers[node_id] = {
                "id": node_id,
                "ip": node.get("ip"),
                "port": node.get("port"),
                "name": node.get("name"),
                "hash": node.get("hash"),
                "last_seen": current_time,
                "connected": node_id in self.connected_peers
            }
        
        peer_count = len(self.discovered_peers)
        if peer_count > 0:
            logger.debug(f"Discovered {peer_count} compatible peers")
    
    def _connect_to_new_peers(self):
        """
        Attempt to connect to newly discovered compatible peers.
        """
        for peer_id, peer_info in list(self.discovered_peers.items()):
            # Skip already connected peers
            if peer_id in self.connected_peers:
                continue
            
            ip = peer_info.get("ip")
            port = peer_info.get("port")
            
            # Try connecting to the peer
            try:
                logger.info(f"Attempting to connect to peer {peer_info.get('name')} ({ip}:{port})...")
                
                # Create client connection
                client = Client(host=ip, port=port)
                if client.connect():
                    # Connection successful
                    self.peer_clients[peer_id] = client
                    self.connected_peers[peer_id] = peer_info.copy()
                    self.connected_peers[peer_id]["connected_at"] = datetime.now().isoformat()
                    
                    # Perform peer connection handshake
                    self._send_peer_handshake(client, peer_id)
                    
                    logger.info(f"Connected to peer {peer_info.get('name')}")
                else:
                    logger.warning(f"Failed to connect to peer {peer_info.get('name')}")
            
            except Exception as e:
                logger.error(f"Peer connection error ({ip}:{port}): {e}")
    
    def _send_peer_handshake(self, client: Client, peer_id: str):
        """
        Send peer connection handshake message.
        
        Args:
            client: Client connection to the peer
            peer_id: Peer node ID
        """
        try:
            # Create handshake message
            handshake = {
                "type": "peer_handshake",
                "node_id": self.server.server_id,
                "name": self.server.server_name,
                "project_id": self.project_id,
                "hash": self.src_hash,
                "timestamp": datetime.now().isoformat()
            }
            
            # Serialize message to JSON
            message = json.dumps(handshake)
            
            # Send message
            client.send(message)
            
            # Wait for response
            response = client.receive()
            if response:
                response_data = json.loads(response)
                
                if response_data.get("type") == "peer_handshake_ack":
                    logger.info(f"Peer handshake successful: {peer_id}")
                    return True
            
            logger.warning(f"Peer handshake failed: {peer_id}")
            return False
            
        except Exception as e:
            logger.error(f"Peer handshake error: {e}")
            return False
    
    def _check_peer_connections(self):
        """
        Check status of connected peers.
        """
        for peer_id, client in list(self.peer_clients.items()):
            if not client.is_connected():
                logger.info(f"Connection to peer {peer_id} was lost")
                self._disconnect_peer(peer_id)
    
    def _disconnect_peer(self, peer_id: str):
        """
        Disconnect a specific peer connection.
        
        Args:
            peer_id: ID of the peer to disconnect
        """
        # Disconnect client connection
        if peer_id in self.peer_clients:
            try:
                self.peer_clients[peer_id].disconnect()
            except:
                pass
            del self.peer_clients[peer_id]
        
        # Remove from connected peers
        if peer_id in self.connected_peers:
            del self.connected_peers[peer_id]
    
    def broadcast_to_peers(self, message: str) -> int:
        """
        Broadcast message to all connected peers.
        
        Args:
            message: Message to broadcast
            
        Returns:
            int: Number of peers message was sent to
        """
        sent_count = 0
        
        for peer_id, client in list(self.peer_clients.items()):
            try:
                if client.send(message):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Error sending message to peer {peer_id}: {e}")
        
        return sent_count
    
    def send_to_peer(self, peer_id: str, message: str) -> bool:
        """
        Send message to a specific peer.
        
        Args:
            peer_id: Target peer ID
            message: Message to send
            
        Returns:
            bool: Whether sending was successful
        """
        if peer_id not in self.peer_clients:
            logger.warning(f"Specified peer {peer_id} is not connected")
            return False
        
        try:
            return self.peer_clients[peer_id].send(message)
        except Exception as e:
            logger.error(f"Error sending message to peer {peer_id}: {e}")
            return False
    
    def get_connected_peers(self) -> List[Dict[str, Any]]:
        """
        Get list of connected peers.
        
        Returns:
            List[Dict[str, Any]]: List of peer information
        """
        return list(self.connected_peers.values())
    
    def get_discovered_peers(self) -> List[Dict[str, Any]]:
        """
        Get list of discovered peers.
        
        Returns:
            List[Dict[str, Any]]: List of peer information
        """
        return list(self.discovered_peers.values())
    
    def register_with_project_id(self):
        """
        Register project ID as a protocol in the ledger.
        """
        # Get current protocol list
        current_protocols = self.server.protocols.copy()
        
        # Add project ID as protocol
        project_tag = f"PROJECT:{self.project_id}"
        if project_tag not in current_protocols:
            current_protocols.append(project_tag)
            
        # Register node with updated protocols in the ledger
        register_node(
            ip=self.server._get_local_ip(),
            port=self.server.port,
            protocols=current_protocols,
            name=self.server.server_name,
            node_id=self.server.server_id
        )
        
        # Update server protocol list
        self.server.protocols = current_protocols