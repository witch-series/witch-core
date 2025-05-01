# Examples

This directory contains example implementations demonstrating how to use the witch-core library in real applications.

## Available Examples

### Basic Example (`example.py`)

A simple demonstration of server-client communication using witch-core:

- Creating a server with custom handlers
- Connecting clients to the server
- Sending and receiving messages using protocols
- Server-to-server peer discovery

### Media Transfer Example (`media_transfer_example.py`)

Shows how to transfer media (images, audio, video) between client and server:

- Transferring image files
- Streaming video data
- Managing media in chunks
- Using compression for efficient media transfer

## Running Examples

To run the basic example:

```bash
# Navigate to the witch-core directory
cd path/to/witch-core

# Run the server
python examples/example.py server

# In another terminal, run the client
python examples/example.py client
```

To run the media transfer example:

```bash
# Navigate to the witch-core directory
cd path/to/witch-core

# Run the server
python examples/media_transfer_example.py server

# In another terminal, run the client
python examples/media_transfer_example.py client
```

## Example Architecture

```
┌─────────────┐                    ┌─────────────┐
│             │   1. Connect       │             │
│   Client    │ ─────────────────> │   Server    │
│             │                    │             │
│             │   2. Send Protocol │             │
│             │ ─────────────────> │             │
│             │                    │             │
│             │   3. Response      │             │
│             │ <───────────────── │             │
└─────────────┘                    └─────────────┘
```

## Creating Your Own Examples

To create a new example using witch-core:

1. Import necessary modules:
   ```python
   from src.network import Server, Client
   from src.protocol import create_protocol, save_protocol
   ```

2. Define your protocol:
   ```python
   my_protocol = create_protocol(
       number="001",
       name="my_example_protocol",
       data_names=["message", "timestamp"],
       description="Example protocol for demonstration"
   )
   save_protocol(my_protocol)
   ```

3. Create a server with custom handlers:
   ```python
   def message_handler(data, client_id):
       print(f"Received from {client_id}: {data}")
       return {"status": "success", "message": "Message received"}
   
   server = Server(port=8000)
   server.register_endpoint("message", message_handler)
   server.start()
   ```

4. Create a client and communicate:
   ```python
   client = Client(host="localhost", port=8000)
   client.connect()
   
   response = client.send_protocol_message(
       "localhost", 8000, "my_example_protocol", 
       {"message": "Hello server", "timestamp": "2025-04-30T15:00:00"}
   )
   print(f"Response: {response}")
   ```

## Learning Path

1. Start with `example.py` for basic concepts
2. Progress to `media_transfer_example.py` for advanced features
3. Experiment with modifying these examples
4. Create your own implementation using the patterns shown