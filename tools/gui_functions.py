#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Functions for witch-core

This module contains the core functions needed by the GUI Tester.
It handles server and client operations, discovery, and protocol management.
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
import traceback

# Add the project root directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import witch-core modules
try:
    from src.network.server import Server
    from src.network.client import Client
    from src.network.discovery import discover_nodes, broadcast_presence
    from src.protocol import protocol_manager
    from src.utils import file_utils, register_server, get_server_registry, get_servers_by_port
except ImportError as e:
    print(f"Error importing witch-core modules: {e}")
    sys.exit(1)


class ServerManager:
    """Manages server operations"""
    
    def __init__(self):
        self.server = None
        self.server_running = False
        
    def start_server(self, host, port, server_id, description, server_name="anonymous"):
        """Start a server with the given parameters"""
        try:
            print(f"Starting server '{server_name}' ({host}:{port}, ID: {server_id})...")
            
            # Initialize server
            self.server = Server(host=host, port=port)
            
            # Register test protocol handler
            def example_handler(client_address, data):
                print(f"Received data from client {client_address}: {data}")
                
                # Save received data to tmp directory
                if 'data' in data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"received_{timestamp}.json"
                    file_utils.save_to_tmp(filename, json.dumps(data['data'], indent=2))
                    print(f"Data saved to {filename}")
                
                # Create response
                response = {
                    'status': 'success',
                    'message': 'Data received',
                    'timestamp': datetime.now().isoformat(),
                    'server_name': server_name
                }
                
                return response
            
            # Register handler for various data types
            self.server.register_handler('example_protocol', example_handler)
            self.server.register_handler('text_data', example_handler)
            self.server.register_handler('json_data', example_handler)
            self.server.register_handler('image_data', example_handler)
            self.server.register_handler('file_data', example_handler)
            
            # Start server
            if self.server.start():
                self.server_running = True
                
                # Supported protocols
                supported_protocols = [
                    'example_protocol', 
                    'text_data', 
                    'json_data', 
                    'image_data', 
                    'file_data'
                ]
                
                # Register server information in the registry
                register_server(
                    server_id=server_id,
                    port=port,
                    host=host,
                    protocol_names=supported_protocols,
                    description=description
                )
                
                # Service information for node discovery
                service_info = {
                    'type': 'witch-series-server',
                    'port': port,
                    'protocols': supported_protocols,
                    'server_name': server_name
                }
                
                # Broadcast presence
                broadcast_presence(node_id=server_id, service_info=service_info)
                
                print(f"Server '{server_name}' started and waiting for client connections...")
                return True
            else:
                print("Failed to start server")
                return False
        except Exception as e:
            print(f"Error starting server: {e}")
            traceback.print_exc()
            return False
    
    def stop_server(self):
        """Stop the running server"""
        if self.server and self.server_running:
            print("Stopping server...")
            self.server.stop()
            self.server_running = False
            print("Server stopped")
            return True
        return False


class ClientManager:
    """Manages client operations"""
    
    def __init__(self):
        self.client = Client()
    
    def send_message(self, host, port, protocol_name, data, use_discovery=False):
        """Send a message from the client to a server"""
        try:
            print(f"Sending message to server {host}:{port}...")
            
            # Use node discovery if enabled
            if use_discovery:
                print("Detecting nodes on the network...")
                nodes = discover_nodes(wait_time=3)
                
                if not nodes:
                    print("No nodes found")
                    return None
                
                print(f"Discovered {len(nodes)} nodes:")
                
                # Look for server nodes
                servers = []
                for node_id, info in nodes.items():
                    print(f"  - {node_id}: {info}")
                    
                    if info.get('type') == 'witch-series-server':
                        servers.append((node_id, info))
                
                if not servers:
                    print("No witch-series servers found")
                    return None
                
                # Connect to the first server
                server_node_id, server_info = servers[0]
                print(f"Connecting to server {server_node_id}...")
                
                # Update host information
                host = server_info.get('local_ip', '127.0.0.1')
                port = server_info.get('port', 8888)
            
            # Send message
            response = self.client.send_protocol_message(
                host=host,
                port=port,
                protocol_name=protocol_name,
                data=data
            )
            
            # Display response
            if response:
                print(f"Response from server: {response}")
            else:
                print("No response received")
            
            return response
        
        except Exception as e:
            print(f"Error sending message: {e}")
            traceback.print_exc()
            return None
    
    def send_file(self, host, port, protocol_name, file_path):
        """Send a file to a server"""
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Create data object
            file_name = os.path.basename(file_path)
            data = {
                'file_name': file_name,
                'content': file_content,
                'size': len(file_content),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"Sending file '{file_name}' ({len(file_content)} bytes) to server {host}:{port}...")
            
            # Send message
            response = self.client.send_protocol_message(
                host=host,
                port=port,
                protocol_name=protocol_name,
                data=data
            )
            
            # Display response
            if response:
                print(f"Response from server: {response}")
            else:
                print("No response received")
            
            return response
        
        except Exception as e:
            print(f"Error sending file: {e}")
            traceback.print_exc()
            return None


class DiscoveryManager:
    """Manages node discovery and broadcasting"""
    
    def __init__(self):
        self.discovered_nodes = {}
        self.auto_discovery_thread = None
        self.auto_broadcast_thread = None
        self.stop_discovery_thread = threading.Event()
        self.stop_broadcast_thread = threading.Event()
    
    def discover_nodes(self):
        """Discover nodes on the network"""
        try:
            print("Discovering nodes on the network...")
            # 待機時間を3秒から10秒に延長して、より多くのノードを発見する
            nodes = discover_nodes(wait_time=10)
            
            # Store discovered nodes
            self.discovered_nodes = nodes or {}
            
            if not nodes:
                print("No nodes found. Please check network configuration and firewall settings.")
                print("- Make sure UDP port 8889 is not blocked by the firewall")
                print("- Ensure both machines are on the same network/subnet")
                print("- Try disabling firewall temporarily to test")
            else:
                print(f"Discovered {len(nodes)} nodes:")
                
                for node_id, info in nodes.items():
                    print(f"  - {node_id}: {info}")
                    if 'local_ip' in info:
                        print(f"    IP: {info['local_ip']}")
                    if 'port' in info:
                        print(f"    Port: {info['port']}")
                    if 'server_name' in info:
                        print(f"    Name: {info['server_name']}")
            
            return self.discovered_nodes
        except Exception as e:
            print(f"Error discovering nodes: {e}")
            traceback.print_exc()
            print("Try checking your network configuration:")
            print("- UDP broadcasts may be blocked by routers/firewalls")
            print("- Make sure port 8889 is open for UDP traffic")
            print("- Check your system's network permissions")
            return {}
    
    def broadcast_presence(self, server_id, port, server_name="anonymous"):
        """Broadcast presence on the network"""
        try:
            # Service information for node discovery
            service_info = {
                'type': 'witch-series-server',
                'port': port,
                'protocols': ['example_protocol', 'text_data', 'json_data', 'image_data', 'file_data'],
                'server_name': server_name
            }
            
            print(f"Broadcasting presence with node ID: {server_id} (Server Name: {server_name})")
            success = broadcast_presence(node_id=server_id, service_info=service_info)
            if success:
                print("Broadcast sent successfully")
            else:
                print("Broadcast may not have been sent - check network configuration")
                print("- UDP broadcast traffic may be blocked by your network")
                print("- Check firewall settings to allow UDP port 8889")
            return success
        except Exception as e:
            print(f"Error broadcasting presence: {e}")
            traceback.print_exc()
            print("Network troubleshooting tips:")
            print("- Check Windows Defender Firewall settings")
            print("- Ensure UDP broadcast traffic is allowed")
            print("- Try running the application as administrator")
            return False
    
    def start_auto_discovery(self, interval, callback=None):
        """Start automatic node discovery thread"""
        if self.auto_discovery_thread is not None and self.auto_discovery_thread.is_alive():
            print("Auto-discovery is already running")
            return False  # Thread already running
        
        self.stop_discovery_thread.clear()
        self.auto_discovery_thread = threading.Thread(
            target=self.auto_discovery_worker,
            args=(interval, callback)
        )
        self.auto_discovery_thread.daemon = True
        self.auto_discovery_thread.start()
        print(f"Auto-discovery started (interval: {interval}s)")
        
        # Also start broadcasting own presence
        self.start_auto_broadcast("auto_server", 8888, "Auto-Discovery Server")
        
        return True
    
    def stop_auto_discovery(self):
        """Stop automatic node discovery thread"""
        if self.auto_discovery_thread is None or not self.auto_discovery_thread.is_alive():
            print("Auto-discovery is not running")
            return False  # No thread running
        
        self.stop_discovery_thread.set()
        self.auto_discovery_thread.join(1.0)  # Wait for thread to finish
        
        # Also stop broadcasting
        self.stop_auto_broadcast()
        
        print("Auto-discovery stopped")
        return True
    
    def auto_discovery_worker(self, interval, callback=None):
        """Worker function for auto-discovery thread"""
        while not self.stop_discovery_thread.is_set():
            try:
                nodes = self.discover_nodes()
                if callback:
                    callback(nodes)
            except Exception as e:
                print(f"Error in auto-discovery worker: {e}")
                traceback.print_exc()
            
            # Wait for the next discovery cycle
            remaining = interval
            while remaining > 0 and not self.stop_discovery_thread.is_set():
                time.sleep(1)
                remaining -= 1
    
    def start_auto_broadcast(self, server_id, port, server_name="anonymous"):
        """Start automatic broadcasting thread"""
        if self.auto_broadcast_thread is not None and self.auto_broadcast_thread.is_alive():
            print("Auto-broadcast is already running")
            return False  # Thread already running
        
        self.stop_broadcast_thread.clear()
        self.auto_broadcast_thread = threading.Thread(
            target=self.auto_broadcast_worker,
            args=(server_id, port, server_name)
        )
        self.auto_broadcast_thread.daemon = True
        self.auto_broadcast_thread.start()
        print(f"Auto-broadcast started for server '{server_name}'")
        return True
    
    def stop_auto_broadcast(self):
        """Stop automatic broadcasting thread"""
        if self.auto_broadcast_thread is None or not self.auto_broadcast_thread.is_alive():
            print("Auto-broadcast is not running")
            return False  # No thread running
        
        self.stop_broadcast_thread.set()
        self.auto_broadcast_thread.join(1.0)  # Wait for thread to finish
        print("Auto-broadcast stopped")
        return True
    
    def auto_broadcast_worker(self, server_id, port, server_name):
        """Worker function for auto-broadcast thread"""
        while not self.stop_broadcast_thread.is_set():
            try:
                self.broadcast_presence(server_id, port, server_name)
            except Exception as e:
                print(f"Error in auto-broadcast worker: {e}")
                traceback.print_exc()
            
            # Wait for the next broadcast cycle (every 5 seconds)
            remaining = 5
            while remaining > 0 and not self.stop_broadcast_thread.is_set():
                time.sleep(1)
                remaining -= 1


class ProtocolManager:
    """Manages protocol operations"""
    
    def __init__(self):
        pass
    
    def list_protocols(self):
        """List available protocols"""
        protocols = protocol_manager.list_available_protocols()
        
        if not protocols:
            print("No available protocols")
            return []
        
        print(f"List of available protocols ({len(protocols)} entries):")
        
        protocol_info = []
        for name in protocols:
            protocol = protocol_manager.load_protocol(name)
            if protocol:
                print(f"\n[Protocol name: {name}]")
                print(f"  Number: {protocol.get('number', 'unknown')}")
                print(f"  Version: {protocol.get('version', 'unknown')}")
                print(f"  Data names: {', '.join(protocol.get('data_names', []))}")
                
                options = protocol.get('options', {})
                if options:
                    print("  Options:")
                    for key, value in options.items():
                        print(f"    {key}: {value}")
                
                protocol_info.append({
                    'name': name,
                    'number': protocol.get('number', 'unknown'),
                    'version': protocol.get('version', 'unknown'),
                    'data_names': protocol.get('data_names', []),
                    'options': protocol.get('options', {})
                })
        
        return protocol_info
    
    def create_protocol(self, name, number, data_names):
        """Create a new protocol"""
        try:
            print(f"Creating new protocol '{name}'...")
            
            # Create protocol
            protocol = protocol_manager.create_protocol(
                number=number,
                name=name,
                data_names=data_names,
                options={"compress": False}
            )
            
            # Save protocol
            protocol_path = protocol_manager.save_protocol(protocol)
            print(f"Protocol saved to: {protocol_path}")
            return True
        except Exception as e:
            print(f"Error creating protocol: {e}")
            traceback.print_exc()
            return False


def get_server_registry_info():
    """Get information about registered servers"""
    registry = get_server_registry()
    
    if not registry:
        print("No registered servers")
        return []
    
    print(f"List of registered servers ({len(registry)} entries):")
    
    servers_info = []
    for server_id, info in registry.items():
        print(f"\n[Server ID: {server_id}]")
        print(f"  Port: {info.get('port', 'unknown')}")
        print(f"  Host: {info.get('host', 'unknown')}")
        print(f"  Local IP: {info.get('local_ip', 'unknown')}")
        print(f"  Description: {info.get('description', 'none')}")
        print(f"  Protocols: {', '.join(info.get('protocols', []))}")
        print(f"  Registration time: {info.get('registered_at', 'unknown')}")
        print(f"  Server Name: {info.get('server_name', 'anonymous')}")
        
        servers_info.append({
            'id': server_id,
            'port': info.get('port', 'unknown'),
            'host': info.get('host', 'unknown'),
            'local_ip': info.get('local_ip', 'unknown'),
            'description': info.get('description', 'none'),
            'protocols': info.get('protocols', []),
            'registered_at': info.get('registered_at', 'unknown'),
            'server_name': info.get('server_name', 'anonymous')
        })
    
    return servers_info