# Network Module

## Quick Reference

This module implements the networking layer of witch-core, providing server-client communications and peer-to-peer capabilities.

For full documentation, see [Network Module Documentation](../../doc/network.md).

## Architecture Overview

```
ClientBase (client_base.py)
    ↓
ClientMessage (client_message.py)
    ↓
ClientMedia (client_media.py)
    ↓
Client (client.py) - Main entry point

ServerBase (server_base.py)
    ↓
ServerHandlers (server_handlers.py)
    ↓
ServerPeer (server_peer.py)
    ↓
Server (server.py) - Main entry point
```

## Main Components

- **client.py**: High-level client interface (use this as your entry point)
- **server.py**: High-level server interface (use this as your entry point)
- **discovery.py**: Node discovery functionality
- **broadcast.py**: Broadcast messaging system

## Usage Example

```python
from src.network import Server, Client

# Create server
server = Server(port=8000)
server.register_endpoint("echo", lambda data, client_id: {"echo": data})
server.start()

# Create client
client = Client(host="localhost", port=8000)
client.connect()
response = client.send_message({"endpoint": "echo", "data": "test"})
```

See the [examples directory](../../examples/) for more comprehensive examples.