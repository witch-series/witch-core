# witch-core

Core networking and protocol library for distributed server-client applications.

## Overview

The witch-core library provides a complete solution for:
- Network communication between servers and clients
- Protocol-based message exchange
- Server-to-server peer communication
- Node discovery via UDP broadcast
- Source code hash verification for security and integrity

## Development Policy and Guidelines

### Development Principles

All development principles and architectural decisions for this project are documented in the `policy` folder:
- [Design Principles](./policy/DESIGN_PRINCIPLES.md): Core architectural principles and design decisions
- [Policy README](./policy/README.md): General development policies and guidelines

Please review these documents before making any significant changes to the codebase.

### Language Policy

All code, documentation, comments, and READMEs in this project **must be written in English**. This ensures:
- Consistency throughout the codebase
- Accessibility for international contributors
- Better compatibility with development tools and LLMs

Non-English text should be translated to English before being committed to the repository.

### Source Code Integrity

The witch-core library uses hash verification of the `src` directory to ensure code integrity and prevent unauthorized modifications. Because of this security feature:

1. **Be careful with source code modifications:**
   Any changes to the source code will change the hash value, potentially preventing communication with other nodes in an established network.

2. **Proper version management:**
   Always ensure all nodes in a network are updated to compatible versions.

3. **For cleaning Python cache files:**
   ```bash
   # Run the included tool to maintain a clean workspace
   python tools/clean_pycache.py
   ```

## Quick Start

### Basic Server Example

```python
from src.network import Server

# Create a server
server = Server(port=8000)

# Define a handler for incoming messages
def handle_message(data, client_id):
    print(f"Received from {client_id}: {data}")
    return {"status": "success", "message": "Received your message"}

# Register the endpoint and start the server
server.register_endpoint("message", handle_message)
server.start()
```

### Basic Client Example

```python
from src.network import Client

# Create and connect a client
client = Client(host="localhost", port=8000)
client.connect()

# Send a message and get response
response = client.send_message(
    {"endpoint": "message", "data": "Hello, server!"},
    wait_for_response=True
)

print(f"Server response: {response}")
```

## GUI Tools

The witch-core library comes with GUI tools to help with testing and development. These tools are located in the `tools` directory.

### GUI Tester

The GUI Tester provides a graphical interface for testing the witch-core library's functionality:

- Server management (start/stop)
- Client connections and message sending
- Protocol testing
- Node discovery
- Automatic node detection and broadcasting

To run the GUI Tester:

```bash
# Basic usage
python tools/gui_tester.py

# With a custom server name
python tools/gui_tester.py --name myproject
```

#### Key Features:

1. **Server Tab**:
   - Configure and start a server with custom name, port, and ID
   - Enable automatic presence broadcasting

2. **Client Tab**:
   - Select destination server from discovered nodes via dropdown
   - Create and send custom messages

3. **Discovery Tab**:
   - Discover nodes on the network with IP address display
   - Enable automatic node discovery at configurable intervals

4. **Protocol Tab**:
   - Create and manage protocols
   - List available protocols

5. **Settings Tab**:
   - Configure auto-discovery interval
   - Configure auto-broadcast interval

### Protocol Editor

A lite version of the protocol editor is available for creating and editing protocol definitions:

```bash
# Run the protocol editor
python tools/protocol_editor_lite.py
```

#### Protocol Editor Features:

- Create and edit protocol definitions
- Manage protocol fields
- Preview protocol JSON structure
- Save protocols for use with witch-core

## Documentation

For detailed documentation, please refer to the [doc](./doc/) directory:

- [Index](./doc/index.md): Main documentation index and getting started guide
- [Network](./doc/network.md): Network module documentation (servers, clients, peers)
- [Protocol](./doc/protocol.md): Protocol module documentation (messages, formats, ledger)
- [Utils](./doc/utils.md): Utilities module documentation (hashing, compression, etc.)

Each module also has its own README file with focused information:

- [Network Module README](./src/network/README.md)
- [Protocol Module README](./src/protocol/README.md)
- [Utils Module README](./src/utils/README.md)

## Project Structure

- **src/**: Source code
  - **network/**: Network communication components
  - **protocol/**: Protocol definition and management
  - **utils/**: Utility functions
- **examples/**: Usage examples with their own [README](./examples/README.md)
- **doc/**: Detailed documentation
- **tools/**: Development tools
- **policy/**: Development guidelines and architectural decisions

## Usage as a Submodule

To use witch-core as a git submodule in your project:

```bash
# Add witch-core as a submodule
git submodule add https://github.com/your-username/witch-core.git

# Initialize and update the submodule
git submodule update --init --recursive
```

## License

This project is licensed under the terms of the LICENSE file included in the repository.
