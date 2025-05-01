#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module providing server functionality using TCP/IP sockets

This module includes the following features:
- TCP server implementation
- Client connection management
- Protocol-based data processing
- Integration with distributed ledger and consistency verification
- Server-to-server communication support
"""

import socket
import threading
import logging
import os
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime

from .server_base import ServerBase
from .server_handlers import DefaultHandler
from .server_peer import ServerPeer
from ..utils import port_utils, server_registry
from ..utils.hash_utils import calculate_src_directory_hash, get_src_hash_info
from ..protocol.ledger import register_node, load_ledger, get_compatible_nodes
from .broadcast import BroadcastManager

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WitchServer")


class Server(ServerBase):
    """
    TCP/IP socket server implementation
    """
    
    def __init__(
        self,
        port: int = 0,
        host: str = "0.0.0.0",
        max_connections: int = 10,
        handler = None,
        server_id: str = None,
        server_name: str = None,
        protocols: List[str] = None,
        broadcast_enabled: bool = True,
        broadcast_port: int = 8890,
        verify_hash: bool = True,
        project_id: str = None,
        enable_peer: bool = False
    ):
        """
        Server initialization
        
        Args:
            port (int): Port number for the server to listen on
            host (str): Hostname or IP address for the server to bind to
            max_connections (int): Maximum number of simultaneous connections
            handler: Handler class for processing client connections
            server_id (str): Unique server identifier (auto-generated if not specified)
            server_name (str): Display name for the server
            protocols (List[str]): List of supported protocols
            broadcast_enabled (bool): Whether to enable node discovery via UDP broadcast
            broadcast_port (int): Port number for broadcast functionality
            verify_hash (bool): Whether to enable src directory hash verification
            project_id (str): Project identifier to which this server belongs
            enable_peer (bool): Whether to enable server-to-server peer communication
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.server_socket = None
        self.running = False
        self.clients = {}  # {client_id: (socket, address, thread)}
        self.handler = handler or DefaultHandler()
        self.listen_thread = None
        
        # Generate server ID if not provided
        self.server_id = server_id or str(uuid.uuid4())
        self.server_name = server_name or f"server-{self.server_id[:8]}"
        
        # Protocol list
        self.protocols = protocols or ["DEFAULT"]
        
        # Source hash
        self.src_hash, _ = calculate_src_directory_hash()
        self.hash_verified = False
        self.verify_hash = verify_hash
        
        # Broadcast functionality
        self.broadcast_enabled = broadcast_enabled
        self.broadcast_port = broadcast_port
        self.broadcast_manager = None
        
        # Server peer functionality
        self.project_id = project_id or "default"
        self.enable_peer = enable_peer
        self.server_peer = None
        
        # Endpoint configuration
        self.endpoints = {}  # {endpoint_name: handler_func}
    
    def start(self):
        """
        Start the server and listen for connections
        
        Returns:
            bool: Whether the server started successfully
        """
        # Do nothing if already running
        if self.running:
            logger.warning("Server is already running")
            return False
        
        # Verify src directory hash if enabled
        if self.verify_hash:
            self._verify_src_hash()
        
        # Assign an available port if none specified
        if self.port == 0:
            self.port = port_utils.get_random_available_port()
        
        try:
            # Create TCP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to host and port
            self.server_socket.bind((self.host, self.port))
            
            # Set to listening state
            self.server_socket.listen(self.max_connections)
            self.running = True
            
            # Get actual bound port number
            _, self.port = self.server_socket.getsockname()
            
            logger.info(f"Server {self.server_name} (ID: {self.server_id}) started on {self.host}:{self.port}")
            
            # Register server information
            self._register_server()
            
            # Start broadcast functionality (if enabled)
            if self.broadcast_enabled:
                self._start_broadcast()
            
            # Start server peer functionality (if enabled)
            if self.enable_peer:
                self._start_peer()
            
            # Start connection listener thread
            self.listen_thread = threading.Thread(target=self._listen_for_connections)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Server startup error: {e}")
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            self.running = False
            return False
    
    def stop(self):
        """
        Stop the server
        """
        if not self.running:
            logger.warning("Server is not running")
            return
        
        self.running = False
        
        # Disconnect all connected clients
        client_ids = list(self.clients.keys())
        for client_id in client_ids:
            self._disconnect_client(client_id)
        
        # Stop server peer functionality
        if self.server_peer:
            self.server_peer.stop()
            self.server_peer = None
        
        # Stop broadcast functionality
        if self.broadcast_manager:
            self.broadcast_manager.stop()
            self.broadcast_manager = None
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")
            self.server_socket = None
        
        # Unregister server information
        server_registry.remove_server(self.server_id)
        port_utils.unregister_port(self.port)
        
        logger.info(f"Server {self.server_name} stopped")
    
    def _listen_for_connections(self):
        """
        Thread function for listening for client connections
        """
        logger.info(f"Started listening for connections (max {self.max_connections} connections)")
        
        self.server_socket.settimeout(1.0)  # Set 1-second timeout
        
        while self.running:
            try:
                # Accept connection
                client_socket, address = self.server_socket.accept()
                
                # Assign unique ID to client
                client_id = str(uuid.uuid4())
                
                # Create and start client thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address, client_id)
                )
                client_thread.daemon = True
                client_thread.start()
                
                # Store client information
                self.clients[client_id] = (client_socket, address, client_thread)
                
                logger.info(f"Client connected: {address[0]}:{address[1]} (ID: {client_id})")
                
            except socket.timeout:
                # Timeout is normal, continue loop
                pass
            except OSError:
                # In case server shuts down, etc.
                if self.running:  # Only show error if still running
                    logger.error("Connection accept error (server socket closed)")
                break
            except Exception as e:
                logger.error(f"Unexpected error during connection accept: {e}")
                # Stop server in case of serious error
                if self.running:
                    logger.critical("Stopping server due to error")
                    self.running = False
                break
    
    def _handle_client(self, client_socket, address, client_id):
        """
        Thread for handling individual client connection
        
        Args:
            client_socket: Client socket
            address: Client address (IP and port)
            client_id: Unique client ID
        """
        try:
            # Call client handler
            self.handler.handle_client(client_socket, address, client_id, self)
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            # Clean up connection
            self._disconnect_client(client_id)
    
    def _disconnect_client(self, client_id):
        """
        Disconnect a client
        
        Args:
            client_id: ID of the client to disconnect
        """
        if client_id in self.clients:
            client_socket, address, _ = self.clients[client_id]
            
            # Close socket
            try:
                client_socket.close()
            except:
                pass
            
            # Remove from client list
            del self.clients[client_id]
            
            logger.info(f"Client disconnected: {address[0]}:{address[1]} (ID: {client_id})")
    
    def _register_server(self):
        """
        Register server information
        """
        # Register port
        port_utils.register_port(self.port, self.server_id, self.server_name)
        
        # Register server information
        server_info = {
            "id": self.server_id,
            "name": self.server_name,
            "host": self.host,
            "port": self.port,
            "protocols": self.protocols,
            "src_hash": self.src_hash,
            "project_id": self.project_id,
            "started_at": datetime.now().isoformat()
        }
        server_registry.register_server(self.server_id, server_info)
        
        # Register node in ledger
        register_node(
            ip=self._get_local_ip(),
            port=self.port,
            protocols=self.protocols,
            name=self.server_name,
            node_id=self.server_id
        )
        
        logger.info(f"Server information registered (ID: {self.server_id})")
    
    def _start_broadcast(self):
        """
        Start broadcast functionality
        """
        # Create BroadcastManager instance
        self.broadcast_manager = BroadcastManager(
            port=self.broadcast_port,
            node_id=self.server_id,
            node_name=self.server_name
        )
        
        # Start broadcast functionality
        if not self.broadcast_manager.start():
            logger.error("Failed to start broadcast functionality")
            self.broadcast_manager = None
            return
        
        # Set node discovery event callbacks
        self.broadcast_manager.on_node_discovered = self._on_node_discovered
        self.broadcast_manager.on_ledger_received = self._on_ledger_received
        
        # Send discovery broadcast
        self.broadcast_manager.send_discovery_broadcast(
            ip=self._get_local_ip(),
            port=self.port,
            protocols=self.protocols,
            count=10,  # Send 10 times
            interval=0.2  # 0.2-second interval
        )
        
        logger.info("Broadcast functionality started")
    
    def _start_peer(self):
        """
        Start server peer functionality
        """
        # Create ServerPeer instance
        self.server_peer = ServerPeer(
            server=self,
            project_id=self.project_id
        )
        
        # Register project ID as protocol
        self.server_peer.register_with_project_id()
        
        # Start peer discovery and connection
        if not self.server_peer.start():
            logger.error("Failed to start server peer functionality")
            self.server_peer = None
            return
        
        logger.info(f"Server peer functionality started (Project: {self.project_id})")
    
    def _on_node_discovered(self, node_info):
        """
        Callback for when a new node is discovered
        
        Args:
            node_info: Information about the discovered node
        """
        logger.info(f"Node discovered: {node_info.get('name')} ({node_info.get('ip')}:{node_info.get('port')})")
        
        # Additional processing for compatible nodes can be implemented here
    
    def _on_ledger_received(self, ledger_data):
        """
        Callback for when remote ledger is received
        
        Args:
            ledger_data: Received ledger data
        """
        logger.info(f"Received ledger data: {len(ledger_data.get('nodes', []))} nodes")
        
        # Additional processing for ledger data can be implemented here
    
    def _verify_src_hash(self):
        """
        Verify src directory hash
        """
        # Get src hash information
        hash_info = get_src_hash_info()
        
        # Get compatible nodes registered in the ledger
        compatible_nodes = get_compatible_nodes()
        
        if compatible_nodes:
            # If compatible nodes exist
            logger.info(f"Found {len(compatible_nodes)} compatible nodes")
            self.hash_verified = True
        else:
            # First startup or no nodes with this hash exist
            logger.info(f"No nodes found with this SRC hash: {hash_info['total_hash'][:16]}")
            logger.info(f"File count: {hash_info['file_count']}, Subdirectories: {', '.join(hash_info['subdirs'])}")
            self.hash_verified = True  # Consider verified for first run
    
    def _get_local_ip(self):
        """
        Get local IP address
        
        Returns:
            str: Local IP address
        """
        try:
            # Use dummy connection to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            # Return loopback address if failed
            return "127.0.0.1"
    
    def register_endpoint(self, endpoint_name: str, handler_func: Callable):
        """
        Register protocol-based endpoint
        
        Args:
            endpoint_name (str): Endpoint name
            handler_func (Callable): Endpoint handler function (data, client_id) -> response_data
        """
        self.endpoints[endpoint_name] = handler_func
        logger.info(f"Endpoint '{endpoint_name}' registered")
    
    def register_handler(self, protocol_name: str, handler_func: Callable) -> None:
        """
        Register protocol handler (alias for register_endpoint)
        
        Args:
            protocol_name (str): Protocol name
            handler_func (Callable): Handler function (client_address, data) -> response_data
        """
        # Call register_endpoint method
        self.register_endpoint(protocol_name, lambda data, client_id: handler_func(data.get('client_address', 'unknown'), data))
        logger.info(f"Protocol handler for '{protocol_name}' registered")
    
    def get_compatible_peers(self) -> List[Dict[str, Any]]:
        """
        Get list of compatible peers
        
        Returns:
            List[Dict[str, Any]]: List of compatible peer information
        """
        if self.server_peer:
            return self.server_peer.get_connected_peers()
        
        # Get directly from ledger if peer functionality is disabled
        compatible_nodes = get_compatible_nodes(self.src_hash)
        
        # Exclude self
        result = [
            node for node in compatible_nodes 
            if node.get("id") != self.server_id
        ]
        
        return result
    
    def broadcast_to_peers(self, message: Any) -> int:
        """
        Broadcast message to all compatible peers
        
        Args:
            message: Message to send (converted to JSON if not a string)
            
        Returns:
            int: Number of peers the message was sent to
        """
        if not self.server_peer:
            logger.warning("Server peer functionality is not enabled")
            return 0
        
        # Convert message to string if it's not already
        if not isinstance(message, str):
            try:
                message = json.dumps(message)
            except Exception as e:
                logger.error(f"Error converting message to JSON: {e}")
                return 0
        
        return self.server_peer.broadcast_to_peers(message)
    
    def send_to_peer(self, peer_id: str, message: Any) -> bool:
        """
        Send message to a specific peer
        
        Args:
            peer_id: Target peer ID
            message: Message to send (converted to JSON if not a string)
            
        Returns:
            bool: Whether the send was successful
        """
        if not self.server_peer:
            logger.warning("Server peer functionality is not enabled")
            return False
        
        # Convert message to string if it's not already
        if not isinstance(message, str):
            try:
                message = json.dumps(message)
            except Exception as e:
                logger.error(f"Error converting message to JSON: {e}")
                return False
        
        return self.server_peer.send_to_peer(peer_id, message)


if __name__ == "__main__":
    # Test operation when this script is run directly
    server = Server(
        port=8888,
        server_name="TestServer",
        project_id="test-project",
        enable_peer=True
    )
    
    # Register test endpoint
    def hello_endpoint(data, client_id):
        return {"message": f"Hello, {data.get('name', 'Anonymous')}!"}
    
    server.register_endpoint("hello", hello_endpoint)
    
    if server.start():
        try:
            print(f"Server started on port {server.port}")
            print(f"Project ID: {server.project_id}")
            print("Press Ctrl+C to exit...")
            
            # Keep main thread running
            while server.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping server...")
        finally:
            server.stop()