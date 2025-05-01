"""
Module providing protocol data processing functionality

Main features:
- Data serialization and deserialization
- Protocol-based data parsing and conversion
- Protocol detection and automatic generation
- Efficient binary and media data transfer
- Real-time data streaming support
"""

import json
import pickle
import base64
import io
from datetime import datetime
import uuid
from typing import Dict, Any, Union, Optional, Tuple, List, BinaryIO
from .protocol_core import validate_protocol, create_protocol
from .protocol_file import load_protocol, list_available_protocols
from ..utils.compression_utils import compress_data, decompress_data, get_compression_methods


def parse_data_with_protocol(data, protocol):
    """
    Parse and convert data types based on protocol.
    
    Args:
        data (dict): Data to parse
        protocol (dict): Protocol definition to use for parsing
        
    Returns:
        dict: Parsed data
    """
    if not validate_protocol(protocol) or not data:
        return data
    
    result = {}
    data_types = protocol.get("data_types", {})
    
    for field, value in data.items():
        # Process only fields defined in protocol
        if field in data_types:
            field_type = data_types[field]
            
            # Type conversion
            try:
                if field_type == "int":
                    result[field] = int(value)
                elif field_type == "float":
                    result[field] = float(value)
                elif field_type == "bool":
                    if isinstance(value, str):
                        result[field] = value.lower() in ("true", "yes", "1", "y")
                    else:
                        result[field] = bool(value)
                elif field_type == "string":
                    result[field] = str(value)
                elif field_type == "list" and isinstance(value, str):
                    # Convert comma-separated string to list
                    result[field] = [item.strip() for item in value.split(",")]
                else:
                    # Keep other types as is
                    result[field] = value
            except (ValueError, TypeError):
                # Use original value if conversion fails
                result[field] = value
        else:
            # Keep fields not defined in protocol as is
            result[field] = value
    
    return result


def format_data_for_protocol(data, protocol):
    """
    Format data according to protocol.
    Use default values for missing fields.
    
    Args:
        data (dict): Data to format
        protocol (dict): Protocol definition to use for formatting
        
    Returns:
        dict: Formatted data
    """
    if not validate_protocol(protocol):
        return data
    
    result = {}
    data_names = protocol.get("data_names", [])
    data_types = protocol.get("data_types", {})
    
    # Process data names defined in the protocol
    for name in data_names:
        # Use existing value if available
        if name in data:
            result[name] = data[name]
        # Otherwise set default value based on data type
        else:
            field_type = data_types.get(name, "string")
            if field_type == "int":
                result[name] = 0
            elif field_type == "float":
                result[name] = 0.0
            elif field_type == "bool":
                result[name] = False
            elif field_type == "list":
                result[name] = []
            else:
                result[name] = ""
    
    # Add timestamp if not present
    if "timestamp" not in result:
        result["timestamp"] = datetime.now().isoformat()
    
    return result


def serialize_data_with_protocol(data, protocol):
    """
    Serialize data according to protocol.
    
    Args:
        data (dict): Data to serialize
        protocol (dict): Protocol definition to use for serialization
    
    Returns:
        str: Serialized data (usually a JSON string)
    """
    if not validate_protocol(protocol) or not data:
        return json.dumps(data, ensure_ascii=False)
    
    # Get options
    options = protocol.get("options", {})
    
    # Format data according to protocol
    formatted_data = format_data_for_protocol(data, protocol)
    
    # Apply serialization options
    serialization_format = options.get("serialization", "json")
    
    if serialization_format == "json":
        # Serialize as JSON
        indent = 2 if options.get("pretty", False) else None
        ensure_ascii = not options.get("unicode", True)
        return json.dumps(formatted_data, ensure_ascii=ensure_ascii, indent=indent)
    elif serialization_format == "compact_json":
        # Compact JSON (no spaces)
        return json.dumps(formatted_data, ensure_ascii=False, separators=(',', ':'))
    else:
        # Default is JSON
        return json.dumps(formatted_data, ensure_ascii=False)


def deserialize_data_with_protocol(serialized_data, protocol):
    """
    Deserialize data according to protocol.
    
    Args:
        serialized_data (str): Data string to deserialize
        protocol (dict): Protocol definition to use for deserialization
    
    Returns:
        dict: Deserialized data
    """
    if not validate_protocol(protocol) or not serialized_data:
        try:
            return json.loads(serialized_data)
        except Exception:
            return {}
    
    # Get options
    options = protocol.get("options", {})
    
    # Get serialization format
    serialization_format = options.get("serialization", "json")
    
    try:
        if serialization_format in ["json", "compact_json"]:
            # Deserialize from JSON format
            data = json.loads(serialized_data)
        else:
            # Default is JSON
            data = json.loads(serialized_data)
        
        # Parse deserialized data according to protocol
        return parse_data_with_protocol(data, protocol)
    except Exception as e:
        print(f"Deserialization error: {e}")
        return {}


def convert_received_data_to_json(raw_data, protocol_name=None):
    """
    Convert received data to JSON. If a protocol is specified,
    parse the data according to the protocol and convert to appropriate data types.
    
    Args:
        raw_data (str/bytes): Received data (string or bytes)
        protocol_name (str): Protocol name to use (None for processing without protocol)
    
    Returns:
        dict: Data converted to JSON format
    """
    # Convert bytes to string
    if isinstance(raw_data, bytes):
        raw_data = raw_data.decode('utf-8', errors='replace')
    
    # Load protocol if specified
    protocol = None
    if protocol_name:
        protocol = load_protocol(protocol_name)
    
    # Deserialize data according to protocol
    if protocol:
        return deserialize_data_with_protocol(raw_data, protocol)
    else:
        # Parse as simple JSON if no protocol
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError:
            # Return as text data if not JSON
            return {"data": raw_data, "format": "text", "_parse_error": True}


def create_protocol_from_data_sample(name, number, data_sample, description=None, default_port=None):
    """
    Automatically generate protocol from sample data.
    
    Args:
        name (str): Protocol name
        number (str): Protocol number
        data_sample (dict): Sample data
        description (str): Protocol description
        default_port (int): Default port number
    
    Returns:
        dict: Generated protocol definition
    """
    data_names = []
    data_types = {}
    
    # Infer data names and types from sample data
    if isinstance(data_sample, dict):
        for field, value in data_sample.items():
            data_names.append(field)
            
            # Determine value type
            if isinstance(value, bool):
                data_types[field] = "bool"
            elif isinstance(value, int):
                data_types[field] = "int"
            elif isinstance(value, float):
                data_types[field] = "float"
            elif isinstance(value, list):
                data_types[field] = "list"
            else:
                data_types[field] = "string"
    
    # Create protocol
    return create_protocol(
        number=number,
        name=name,
        data_names=data_names,
        data_types=data_types,
        description=description,
        default_port=default_port
    )


def find_protocol_by_data(data):
    """
    Infer the most appropriate protocol from received data.
    
    Args:
        data (dict): Received data
    
    Returns:
        dict: Best matching protocol definition, None if not found
    """
    if not data or not isinstance(data, dict):
        return None
    
    # Get available protocols
    protocol_names = list_available_protocols()
    
    best_protocol = None
    best_match_score = -1
    
    # Score each protocol for match with data
    for name in protocol_names:
        protocol = load_protocol(name)
        if not protocol:
            continue
        
        match_score = 0
        data_names = set(protocol.get("data_names", []))
        
        # Count matches between data keys and protocol data names
        for key in data.keys():
            if key in data_names:
                match_score += 1
        
        # Select protocol with more matching fields
        if match_score > best_match_score:
            best_match_score = match_score
            best_protocol = protocol
    
    return best_protocol if best_match_score > 0 else None


def serialize_data_efficiently(data: Dict[str, Any], protocol: Dict[str, Any]) -> bytes:
    """
    Efficiently serialize data based on protocol definition.
    Applies optimizations using type information and specified compression method.
    
    Args:
        data: Data to serialize
        protocol: Protocol definition
        
    Returns:
        Optimized byte data
    """
    if not validate_protocol(protocol) or not data:
        return json.dumps(data, ensure_ascii=False).encode('utf-8')
    
    # Get protocol options
    options = protocol.get("options", {})
    compression = options.get("compression", None)
    format_type = options.get("format", "json")
    compression_level = options.get("compression_level", 6)
    
    # Format data according to protocol
    formatted_data = format_data_for_protocol(data, protocol)
    
    # Serialize based on data format
    if format_type == "json":
        # Standard JSON
        serialized = json.dumps(formatted_data, ensure_ascii=False).encode('utf-8')
    elif format_type == "compact_json":
        # Compact JSON (no spaces)
        serialized = json.dumps(formatted_data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    elif format_type == "binary":
        # Binary format (pickle)
        serialized = pickle.dumps(formatted_data)
    elif format_type == "messagepack":
        # MessagePack - efficient binary serialization
        try:
            import msgpack
            serialized = msgpack.packb(formatted_data)
        except ImportError:
            # Fall back to pickle if MessagePack not installed
            serialized = pickle.dumps(formatted_data)
            print("Warning: MessagePack not installed, falling back to pickle")
    else:
        # Default is JSON
        serialized = json.dumps(formatted_data, ensure_ascii=False).encode('utf-8')
    
    # Apply compression if configured
    if compression and compression != "None":
        try:
            return compress_data(serialized, method=compression, compression_level=compression_level)
        except Exception as e:
            print(f"Compression error: {e}")
            return serialized
    
    return serialized


def deserialize_data_efficiently(serialized_data: bytes, protocol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserialize efficiently serialized data based on protocol definition.
    
    Args:
        serialized_data: Byte data to deserialize
        protocol: Protocol definition
        
    Returns:
        Deserialized data
    """
    if not validate_protocol(protocol) or not serialized_data:
        try:
            if isinstance(serialized_data, bytes):
                return json.loads(serialized_data.decode('utf-8'))
            return json.loads(serialized_data)
        except Exception:
            return {}
    
    # Get protocol options
    options = protocol.get("options", {})
    compression = options.get("compression", None)
    format_type = options.get("format", "json")
    
    # Decompress data
    if compression and compression != "None":
        try:
            decompressed = decompress_data(serialized_data, method=compression)
        except Exception as e:
            print(f"Decompression error: {e}")
            decompressed = serialized_data
    else:
        decompressed = serialized_data
    
    # Deserialize based on data format
    try:
        if format_type == "binary":
            # Binary format (pickle)
            data = pickle.loads(decompressed)
        elif format_type == "messagepack":
            # MessagePack
            try:
                import msgpack
                data = msgpack.unpackb(decompressed)
            except ImportError:
                # Fall back to pickle if MessagePack not installed
                data = pickle.loads(decompressed)
        else:
            # JSON format
            if isinstance(decompressed, bytes):
                data = json.loads(decompressed.decode('utf-8'))
            else:
                data = json.loads(decompressed)
        
        # Parse deserialized data according to protocol
        return parse_data_with_protocol(data, protocol)
    except Exception as e:
        print(f"Deserialization error: {e}")
        return {}


def encode_media_data(media_data: bytes, media_type: str = "binary") -> Dict[str, Any]:
    """
    Convert binary media data for protocol transfer
    
    Args:
        media_data: Binary data to convert
        media_type: Data type ("image", "audio", "video", "binary")
        
    Returns:
        Dictionary containing encoded data in content field
    """
    encoded = base64.b64encode(media_data).decode('ascii')
    return {
        "content": encoded,
        "media_type": media_type,
        "size": len(media_data),
        "encoding": "base64",
        "timestamp": datetime.now().isoformat()
    }


def decode_media_data(media_dict: Dict[str, Any]) -> Tuple[bytes, str]:
    """
    Convert encoded media data back to binary data
    
    Args:
        media_dict: Dictionary containing encoded media data
        
    Returns:
        Tuple of (binary data, media type)
    """
    encoded = media_dict.get("content")
    media_type = media_dict.get("media_type", "binary")
    
    if encoded:
        encoding = media_dict.get("encoding", "base64")
        if encoding == "base64":
            return base64.b64decode(encoded), media_type
    
    return b'', media_type


def create_media_protocol(name: str, media_type: str = "image",
                          compression: str = "gzip", format_type: str = "binary") -> Dict[str, Any]:
    """
    Create protocol definition for media transfer
    
    Args:
        name: Protocol name
        media_type: Media type ("image", "audio", "video", "mixed")
        compression: Compression method ("None", "gzip", "zlib", etc.)
        format_type: Format type ("binary", "json", "messagepack")
        
    Returns:
        Protocol definition for media transfer
    """
    # Define data fields
    data_names = [
        "content", "media_type", "format", "width", "height", 
        "duration", "fps", "channels", "sample_rate", "metadata"
    ]
    
    # Define data types
    data_types = {
        "content": "string",  # Base64 encoded content
        "media_type": "string",
        "format": "string",
        "width": "int",
        "height": "int",
        "duration": "float",
        "fps": "float",
        "channels": "int",
        "sample_rate": "int",
        "metadata": "string"  # Additional metadata stored as JSON
    }
    
    # Option settings
    options = {
        "compression": compression,
        "format": format_type,
        "compression_level": 6,
        "streaming": True,  # Streaming support
        "chunk_size": 64 * 1024  # Default chunk size: 64KB
    }
    
    # Generate protocol number (based on media type)
    protocol_number = f"M{str(uuid.uuid4())[:6]}"
    
    # Create protocol definition
    protocol = create_protocol(
        number=protocol_number,
        name=name,
        data_names=data_names,
        data_types=data_types,
        options=options,
        description=f"{media_type.capitalize()} media transfer protocol"
    )
    
    return protocol


def chunk_media_data(media_data: bytes, chunk_size: int = 64 * 1024) -> List[bytes]:
    """
    Split large media data into chunks
    
    Args:
        media_data: Binary data to split
        chunk_size: Chunk size (bytes)
        
    Returns:
        List of byte chunks
    """
    return [media_data[i:i + chunk_size] for i in range(0, len(media_data), chunk_size)]


def create_media_stream_chunk(
    chunk_data: bytes,
    chunk_index: int,
    total_chunks: int,
    stream_id: str,
    media_type: str = "binary",
    is_last: bool = False,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create media chunk for streaming transfer
    
    Args:
        chunk_data: Binary data for the chunk
        chunk_index: Chunk number (starting from 0)
        total_chunks: Total number of chunks (-1 if unknown)
        stream_id: Stream ID
        media_type: Media type
        is_last: Whether this is the last chunk
        metadata: Additional metadata
        
    Returns:
        Media chunk object
    """
    # Base64 encoding
    encoded = base64.b64encode(chunk_data).decode('ascii')
    
    # Chunk information
    chunk = {
        "content": encoded,
        "media_type": media_type,
        "encoding": "base64",
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "is_last": is_last,
        "stream_id": stream_id,
        "size": len(chunk_data),
        "timestamp": datetime.now().isoformat()
    }
    
    # Add metadata if available
    if metadata:
        chunk["metadata"] = json.dumps(metadata)
        
    return chunk