# Source Code Directory

## Purpose

This directory contains the core implementation code for the witch-core library. It provides the foundation for networking, protocol management, and utility functions.

## Contents

- **network/**: Network communication components including server, client, and peer discovery
  - Server implementation
  - Client implementation 
  - Broadcast discovery
  - Peer communication

- **protocol/**: Protocol definition and management
  - Protocol creation and validation
  - Data handling
  - Ledger functionality
  - File transfer protocols

- **utils/**: Utility functions
  - File operations
  - Hash calculations
  - Compression utilities
  - Port management
  - Server registry

## Usage Notes

All core functionality should be imported from these modules. For example:

```python
from src.network import Server, Client
from src.protocol import create_protocol, load_protocol
from src.utils import save_json, calculate_hash
```

For detailed documentation on each module, please refer to:
- [Network Module README](./network/README.md)
- [Protocol Module README](./protocol/README.md)
- [Utils Module README](./utils/README.md)