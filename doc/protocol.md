# Protocol Module Documentation

## Overview

The protocol module defines the communication protocols and data exchange formats used in witch-core. It establishes a structured approach for message passing, version compatibility, and protocol evolution.

## Components

### Protocol Core

The `protocol_core` module provides the foundation for protocol definition and usage across the witch-core ecosystem.

#### Key Features

- Protocol versioning
- Protocol registration and discovery
- Protocol compatibility checking
- Message format validation

#### Basic Usage

```python
from src.protocol.protocol_core import register_protocol, get_protocol

# Register a protocol
register_protocol("my_protocol", version="1.0", handlers={
    "get_status": lambda data: {"status": "ok"},
    "ping": lambda data: {"pong": True}
})

# Get a registered protocol
protocol = get_protocol("my_protocol", version="1.0")
if protocol:
    result = protocol.handle_message("ping", {})
    print(result)  # {"pong": True}
```

### Protocol Manager

The `protocol_manager` module provides tools for managing multiple protocols and protocol versions.

#### Key Features

- Protocol life cycle management
- Default protocol selection
- Cross-version compatibility
- Protocol migration

#### Basic Usage

```python
from src.protocol.protocol_manager import ProtocolManager

# Create a protocol manager
manager = ProtocolManager()

# Register protocols
manager.register_protocol("data_sync", version="1.0", handlers={
    "sync": lambda data: {"status": "synced"}
})

manager.register_protocol("data_sync", version="2.0", handlers={
    "sync": lambda data: {"status": "synced", "timestamp": time.time()}
})

# Use a protocol
result = manager.handle_message("data_sync", "2.0", "sync", {})
```

### Protocol Data

The `protocol_data` module handles data serialization, validation, and transformation for protocol messages.

#### Key Features

- JSON schema validation
- Type conversion
- Default values
- Binary data handling
- Compression

#### Basic Usage

```python
from src.protocol.protocol_data import validate_data, compress_data

# Validate data against a schema
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name"]
}

data = {"name": "John", "age": 30}
is_valid, errors = validate_data(data, schema)

# Compress data for transmission
compressed = compress_data(data)
```

### Protocol File

The `protocol_file` module handles file transfer operations using the witch-core protocol.

#### Key Features

- Chunked file transfers
- Progress tracking
- Resume capability
- Transfer validation
- File integrity checking

#### Basic Usage

```python
from src.protocol.protocol_file import FileTransferProtocol

# Create a file transfer protocol handler
file_transfer = FileTransferProtocol()

# Register with a server
server.register_endpoint("file_upload", file_transfer.handle_upload)
server.register_endpoint("file_download", file_transfer.handle_download)

# Client usage
client.send_and_receive({
    "endpoint": "file_upload",
    "file_path": "/path/to/file.txt",
    "chunk_size": 8192
})
```

### Protocol Iteration

The `protocol_iteration` module handles protocol iteration and evolution over time.

#### Key Features

- Protocol versioning
- Backward compatibility
- Feature detection
- Migration paths

#### Basic Usage

```python
from src.protocol.protocol_iteration import ProtocolVersion, check_compatibility

# Define protocol versions
v1 = ProtocolVersion("1.0", features=["basic_chat"])
v2 = ProtocolVersion("2.0", features=["basic_chat", "encryption"])

# Check compatibility
is_compatible = check_compatibility(v1, v2)
missing_features = v2.get_missing_features(v1)
```

### Ledger

The `ledger` module provides distributed ledger functionality for tracking nodes and their states.

#### Key Features

- Node registration
- Status tracking
- Distributed consensus
- Ledger synchronization
- Conflict resolution

#### Basic Usage

```python
from src.protocol.ledger import Ledger

# Create a ledger
ledger = Ledger()

# Register a node
ledger.register_node("server1", {"ip": "192.168.1.100", "port": 8888})

# Update node status
ledger.update_node_status("server1", "active")

# Get all active nodes
active_nodes = ledger.get_nodes_by_status("active")

# Synchronize with another ledger
ledger.sync_with(remote_ledger)
```

## Advanced Topics

### Creating Custom Protocols

```python
from src.protocol.protocol_core import Protocol

class CustomProtocol(Protocol):
    def __init__(self):
        super().__init__(name="custom", version="1.0")
        self.register_handler("process", self.handle_process)
        
    def handle_process(self, data):
        # Process data
        result = self._process_data(data)
        return {"status": "success", "result": result}
        
    def _process_data(self, data):
        # Private processing logic
        return data.upper() if isinstance(data, str) else data
```

### Protocol Compatibility

When evolving protocols, follow these guidelines to ensure compatibility:

1. **Backward Compatibility**: New versions should handle messages from older versions
2. **Forward Compatibility**: Design protocols to gracefully handle unknown fields
3. **Feature Detection**: Implement mechanisms to detect available features
4. **Fallback Mechanisms**: Provide fallback behavior for unsupported operations

### Protocol Security Considerations

1. **Authentication**: Validate the source of protocol messages
2. **Authorization**: Ensure clients have permission to use requested endpoints
3. **Validation**: Always validate input data against schemas
4. **Encryption**: Consider encrypting sensitive data
5. **Rate Limiting**: Implement rate limiting to prevent abuse

## Best Practices

1. **Documentation**: Document protocols thoroughly, including all message formats
2. **Versioning**: Use semantic versioning for protocol versions
3. **Deprecation**: Clearly mark deprecated features and provide migration paths
4. **Extensibility**: Design protocols to be extensible from the beginning
5. **Testing**: Test protocol compatibility across different versions