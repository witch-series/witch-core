# witch-core Documentation

## Introduction

Welcome to the witch-core documentation. This library provides a robust framework for creating distributed server-client applications with peer-to-peer communication capabilities.

## Core Modules

witch-core consists of three primary modules:

1. [Network Module](./network.md): Implements server and client communication
2. [Protocol Module](./protocol.md): Defines message formats and communication protocols
3. [Utils Module](./utils.md): Provides utility functions for various operations

## Getting Started

### Installation

To include witch-core in your project:

```bash
# Clone the repository
git clone https://github.com/your-username/witch-core.git

# Or add as a submodule to your project
git submodule add https://github.com/your-username/witch-core.git
git submodule update --init --recursive
```

### Basic Usage Example

Here's a simple example to get you started:

```python
from src.network.server import Server
from src.network.client import Client

# Create a server
server = Server(port=8888, server_name="ExampleServer")

# Register an endpoint
def handle_message(data, client_id):
    print(f"Received from {client_id}: {data}")
    return {"status": "ok", "message": "Message received"}

server.register_endpoint("message", handle_message)
server.start()

# Create a client and connect to the server
client = Client(host="127.0.0.1", port=8888)
client.connect()

# Send a message to the server
response = client.send_and_receive({"endpoint": "message", "data": "Hello, server!"})
print(f"Response: {response}")
```

## Architecture Overview

witch-core uses a layered architecture:

1. **Foundation Layer**: Core networking functionality
2. **Protocol Layer**: Message formatting and validation
3. **Peer Layer**: Server-to-server communication
4. **Discovery Layer**: Node discovery and ledger maintenance

## Advanced Topics

- [Server Peer Communication](./network.md#serverpeer)
- [Protocol Definition and Management](./protocol.md#defining-protocols)
- [Hash-based Compatibility](./utils.md#hash-utilities)
- [Ledger Synchronization](./protocol.md#ledger)

## Contributing

Contributions to witch-core are welcome. Please ensure that your code follows the existing style conventions and includes appropriate documentation.