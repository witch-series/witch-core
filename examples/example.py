#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basic usage example of the witch-series framework

This script demonstrates the following basic features:
1. Starting and running a server
2. Sending messages from a client
3. Creating and using protocols
4. Node discovery functionality
5. Server information management
6. Protocol definition file management
"""

import sys
import os
import time
import json
import threading
import argparse
from datetime import datetime

# Add the project root directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import witch-series modules
from src.network.server import Server
from src.network.client import Client
from src.network.discovery import discover_nodes, broadcast_presence
from src.protocol import protocol_manager
from src.utils import file_utils, register_server, get_server_registry, get_servers_by_port


def run_server(host='0.0.0.0', port=8888, server_id=None, description=None):
    """
    Start and run a server
    
    Args:
        host (str): Hostname or IP address to bind to
        port (int): Port number to listen on
        server_id (str): Server identifier (auto-generated if not specified)
        description (str): Server description
    """
    # Auto-generate server ID if not specified
    if server_id is None:
        server_id = f"server-{port}-{int(time.time())}"
    
    print(f"Starting server ({host}:{port}, ID: {server_id})...")
    
    # Initialize server
    server = Server(host=host, port=port)
    
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
            'timestamp': datetime.now().isoformat()
        }
        
        return response
    
    # Register handler
    server.register_handler('example_protocol', example_handler)
    
    # Start server
    if server.start():
        # Supported protocols
        supported_protocols = ['example_protocol']
        
        # Register server information in the registry
        register_server(
            server_id=server_id,
            port=port,
            host=host,
            protocol_names=supported_protocols,
            description=description or f"witch-series server running on port {port}"
        )
        
        # Check server registry
        registry = get_server_registry()
        print(f"Current number of registered servers: {len(registry)}")
        
        # Service information for node discovery
        service_info = {
            'type': 'witch-series-server',
            'port': port,
            'protocols': supported_protocols
        }
        
        # Broadcast presence
        broadcast_presence(node_id=server_id, service_info=service_info)
        
        print("Server started and waiting for client connections...")
        print("Press Ctrl+C to exit")
        
        try:
            # Keep the main thread running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
            server.stop()
            print("Server stopped")
    else:
        print("Failed to start server")


def run_client(host='127.0.0.1', port=8888, discover=False, protocol_name='example_protocol'):
    """
    Send messages from a client
    
    Args:
        host (str): Hostname or IP address of the target server
        port (int): Port number of the target server
        discover (bool): Whether to use node discovery
        protocol_name (str): Name of the protocol to use
    """
    print("Starting client...")
    
    # Get information about servers running on the specified port
    servers_on_port = get_servers_by_port(port)
    if servers_on_port:
        server_info = servers_on_port[0]
        print(f"The following server is running on port {port}:")
        print(f"  ID: {server_info['server_id']}")
        print(f"  Host: {server_info.get('host', 'unknown')}")
        print(f"  Local IP: {server_info.get('local_ip', 'unknown')}")
        print(f"  Supported protocols: {', '.join(server_info.get('protocols', []))}")
        print(f"  Description: {server_info.get('description', 'none')}")
        print(f"  Registration time: {server_info.get('registered_at', 'unknown')}")
    
    # Initialize client
    client = Client()
    
    # Use node discovery if enabled
    if discover:
        print("Detecting nodes on the network...")
        nodes = discover_nodes(wait_time=3)
        
        if not nodes:
            print("No nodes found")
            return
        
        print(f"Discovered {len(nodes)} nodes:")
        
        # Look for server nodes
        servers = []
        for node_id, info in nodes.items():
            print(f"  - {node_id}: {info}")
            
            if info.get('type') == 'witch-series-server':
                servers.append((node_id, info))
        
        if not servers:
            print("No witch-series servers found")
            return
        
        # Connect to the first server
        server_node_id, server_info = servers[0]
        print(f"Connecting to server {server_node_id}...")
        
        # Update host information
        host = server_info.get('local_ip', '127.0.0.1')
        port = server_info.get('port', 8888)
    
    # Try to load protocol
    protocol = protocol_manager.load_protocol(protocol_name)
    
    # Create new protocol if it doesn't exist
    if protocol is None:
        print(f"Protocol '{protocol_name}' not found. Creating a new one.")
        protocol = protocol_manager.create_protocol(
            number="001",
            name=protocol_name,
            data_names=["temperature", "humidity"],
            options={"compress": False}
        )
        
        # Save protocol
        protocol_path = protocol_manager.save_protocol(protocol)
        print(f"Protocol saved to: {protocol_path}")
    else:
        print(f"Loaded protocol '{protocol_name}'")
        print(f"  Version: {protocol.get('version', 'unknown')}")
        print(f"  Data names: {', '.join(protocol.get('data_names', []))}")
        print(f"  Options: {protocol.get('options', {})}")
    
    # Prepare data to send
    data = {
        'temperature': 22.5,
        'humidity': 45.3,
        'timestamp': datetime.now().isoformat(),
        'device_id': 'sensor-001'
    }
    
    # Send message
    print(f"Sending message to server {host}:{port}...")
    response = client.send_protocol_message(
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


def list_servers():
    """
    Display registered server information
    """
    registry = get_server_registry()
    
    if not registry:
        print("No registered servers")
        return
    
    print(f"List of registered servers ({len(registry)} entries):")
    for server_id, info in registry.items():
        print(f"\n[Server ID: {server_id}]")
        print(f"  Port: {info.get('port', 'unknown')}")
        print(f"  Host: {info.get('host', 'unknown')}")
        print(f"  Local IP: {info.get('local_ip', 'unknown')}")
        print(f"  Description: {info.get('description', 'none')}")
        print(f"  Protocols: {', '.join(info.get('protocols', []))}")
        print(f"  Registration time: {info.get('registered_at', 'unknown')}")


def list_protocols():
    """
    Display available protocols
    """
    protocols = protocol_manager.list_available_protocols()
    
    if not protocols:
        print("No available protocols")
        return
    
    print(f"List of available protocols ({len(protocols)} entries):")
    
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


def main():
    parser = argparse.ArgumentParser(description='Basic usage example of the witch-series framework')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start a server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    server_parser.add_argument('--port', type=int, default=8888, help='Port to use (default: 8888)')
    server_parser.add_argument('--id', dest='server_id', help='Server ID (auto-generated if omitted)')
    server_parser.add_argument('--desc', dest='description', help='Server description')
    
    # Client command
    client_parser = subparsers.add_parser('client', help='Start a client')
    client_parser.add_argument('--host', default='127.0.0.1', help='Target host (default: 127.0.0.1)')
    client_parser.add_argument('--port', type=int, default=8888, help='Target port (default: 8888)')
    client_parser.add_argument('--discover', action='store_true', help='Use node discovery')
    client_parser.add_argument('--protocol', default='example_protocol', help='Protocol name to use (default: example_protocol)')
    
    # List servers command
    subparsers.add_parser('list-servers', help='List registered servers')
    
    # List protocols command
    subparsers.add_parser('list-protocols', help='List available protocols')
    
    args = parser.parse_args()
    
    # Process according to command
    if args.command == 'server':
        run_server(
            host=args.host, 
            port=args.port, 
            server_id=args.server_id, 
            description=args.description
        )
    elif args.command == 'client':
        run_client(
            host=args.host, 
            port=args.port, 
            discover=args.discover, 
            protocol_name=args.protocol
        )
    elif args.command == 'list-servers':
        list_servers()
    elif args.command == 'list-protocols':
        list_protocols()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()