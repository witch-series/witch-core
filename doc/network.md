# Network Module Documentation

## Overview

The network module provides the core networking functionality for server-client communication in witch-core. It includes server implementation, client connection handling, discovery mechanisms, and peer-to-peer communication.

## Components

### Server

The `Server` class implements a TCP/IP server that handles client connections and requests.

#### Key Features

- Multi-threaded client handling
- Protocol-based endpoint registration and dispatching
- Automatic client disconnect detection
- Peer server discovery and communication
- Source hash-based compatibility verification

#### Basic Usage

```python
from src.network.server import Server

# Create a server on port 8888
server = Server(port=8888, server_name="MyServer")

# Register an endpoint
def handle_echo(data, client_id):
    return {"echo": data}

server.register_endpoint("echo", handle_echo)

# Start the server
server.start()
```

### Client

The `Client` class implements a TCP/IP client for connecting to a witch-core server.

#### Key Features

- Automatic reconnection
- Timeout handling
- JSON message serialization and deserialization
- Connection status tracking
- Synchronous and asynchronous request modes

#### Basic Usage

```python
from src.network.client import Client

# Create a client
client = Client(host="127.0.0.1", port=8888)

# Connect to the server
if client.connect():
    # Send a request and wait for response
    response = client.send_and_receive({"endpoint": "echo", "data": "Hello"})
    print(f"Response: {response}")
    
    # Disconnect
    client.disconnect()
```

### Discovery

The `Discovery` module provides mechanisms for server discovery on local networks.

#### Key Features

- UDP broadcast-based discovery
- Automatic server registration
- Server status verification
- Multi-network interface support

#### Basic Usage

```python
from src.network.discovery import broadcast_server_info, listen_for_server_broadcasts

# Broadcast server info
broadcast_server_info(server_name="MyServer", port=8888, protocols=["v1"])

# Listen for server broadcasts
def server_found(server_info):
    print(f"Found server: {server_info['name']} at {server_info['ip']}:{server_info['port']}")

listen_for_server_broadcasts(callback=server_found)
```

### ServerPeer

The `ServerPeer` class manages server-to-server communication for distributed operations.

#### Key Features

- Automatic peer discovery
- Peer status monitoring
- Project-based peer isolation
- Message broadcasting to all peers
- Targeted peer messaging

#### Basic Usage

```python
# Server with peer support
server = Server(port=8888, server_name="PeerServer", enable_peer=True, project_id="my_project")

# Send a message to all peers
server.peer.broadcast_to_peers(json.dumps({
    "type": "status_update",
    "status": "active"
}))
```

## Server Handlers

The `server_handlers` module provides predefined request handlers for common server operations.

#### Available Handlers

- `handle_status_request`: Server status information
- `handle_info_request`: Server metadata
- `handle_peer_list_request`: List of connected peers
- `handle_echo_request`: Simple echo response
- `handle_ping_request`: Connectivity testing

## Client Connection

The `client_connection` module manages individual client connections within the server.

#### Key Features

- Connection lifecycle management
- Request parsing and validation
- Response formatting
- Client identification and tracking

## Advanced Configuration

### Server Configuration

```python
server = Server(
    port=8888,                   # Server port
    server_name="MyServer",      # Server name
    max_clients=10,              # Maximum connected clients
    enable_discovery=True,       # Enable UDP discovery
    protocols=["v1", "v2"],      # Supported protocols
    enable_peer=True,            # Enable peer connections
    project_id="my_project"      # Project identifier
)
```

### Client Configuration

```python
client = Client(
    host="127.0.0.1",           # Server host
    port=8888,                  # Server port
    timeout=5.0,                # Connection timeout
    auto_reconnect=True,        # Auto-reconnect on disconnect
    max_reconnect_attempts=3,   # Maximum reconnection attempts
    reconnect_delay=1.0         # Delay between reconnection attempts
)
```

## Error Handling

The network module includes comprehensive error handling:

- Connection errors
- Timeout errors
- Protocol errors
- JSON parsing errors
- Authentication errors

## Best Practices

1. **Security**: Always validate client input before processing
2. **Resource Management**: Properly close connections when they are no longer needed
3. **Error Handling**: Implement robust error handling in endpoint functions
4. **Timeouts**: Configure appropriate timeouts for your application's needs
5. **Reconnection**: Use auto-reconnect carefully to prevent reconnection storms