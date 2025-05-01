# Protocol Module

## Quick Reference

This module provides the protocol framework for witch-core, defining and managing the communication formats used between servers and clients.

For full documentation, see [Protocol Module Documentation](../../doc/protocol.md).

## Component Overview

```
Protocol Core (protocol_core.py) - Basic protocol creation & validation
    ↓
Protocol File (protocol_file.py)     Protocol Data (protocol_data.py)
    ↓                                     ↓
Protocol Manager (protocol_manager.py) ← Protocol Iteration (protocol_iteration.py)
    ↓
Ledger (ledger.py) - Distributed protocol registry
```

## Main Functions

- `create_protocol()`: Create a new protocol definition
- `validate_protocol()`: Validate a protocol structure
- `save_protocol()`: Save a protocol to disk
- `load_protocol()`: Load a protocol from disk
- `parse_data_with_protocol()`: Parse received data using a protocol

## Usage Example

```python
from src.protocol import create_protocol, save_protocol, load_protocol

# Create protocol
my_protocol = create_protocol(
    number="001",
    name="example_protocol",
    data_names=["message", "timestamp"]
)

# Save & load
save_protocol(my_protocol)
loaded = load_protocol("example_protocol")
```

See the [examples directory](../../examples/) for more comprehensive examples.