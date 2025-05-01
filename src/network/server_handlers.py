"""
Module providing handler functions for server client requests

This module includes the following features:
- Default handler class
- Standard request processing functions
- Media data processing and streaming functionality
- Stream manager
"""

import json
import logging
import socket
import time
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Callable, BinaryIO, Union

from ..protocol.protocol_data import (
    deserialize_data_efficiently,
    serialize_data_efficiently,
    decode_media_data,
    encode_media_data,
    chunk_media_data,
    create_media_stream_chunk
)
from ..protocol.protocol_file import load_protocol, save_protocol

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WitchServerHandlers")


class MediaStreamManager:
    """
    Server-side media stream management class
    """
    
    def __init__(self):
        """
        Initialize stream manager
        """
        self.active_streams = {}  # stream_id -> stream_info
        self.stream_callbacks = {}  # stream_id -> {event_type: callback}
        self.stream_buffers = {}  # stream_id -> [chunks]
    
    def register_stream(self, stream_id: str, media_type: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Register a new media stream
        
        Args:
            stream_id: Stream ID
            media_type: Media type
            metadata: Stream metadata
            
        Returns:
            Registered stream information
        """
        stream_info = {
            "id": stream_id,
            "type": media_type,
            "started_at": datetime.now().isoformat(),
            "chunk_count": 0,
            "total_bytes": 0,
            "metadata": metadata or {},
            "status": "active",
            "client_id": None  # Set later
        }
        
        self.active_streams[stream_id] = stream_info
        self.stream_buffers[stream_id] = []
        
        logger.info(f"New media stream ({media_type}) registered (Stream ID: {stream_id})")
        return stream_info
    
    def process_stream_chunk(self, chunk_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Process received stream chunk
        
        Args:
            chunk_data: Stream chunk information
            
        Returns:
            (success flag, response data)
        """
        stream_id = chunk_data.get("stream_id")
        if not stream_id or stream_id not in self.active_streams:
            # Register new stream if not registered
            if chunk_data.get("action") == "start_stream":
                stream_info = self.register_stream(
                    stream_id=stream_id or str(uuid.uuid4()),
                    media_type=chunk_data.get("media_type", "unknown"),
                    metadata=chunk_data.get("metadata")
                )
                return True, {"status": "stream_started", "stream_id": stream_info["id"]}
            
            return False, {"error": "unknown_stream", "message": f"Stream {stream_id} is not registered"}
        
        # Get stream information
        stream_info = self.active_streams[stream_id]
        
        # Check if this is the last chunk
        is_last = chunk_data.get("is_last", False)
        
        # Process media content
        if "content" in chunk_data and chunk_data["content"]:
            # Decode encoded media data
            try:
                binary_data, _ = decode_media_data(chunk_data)
                
                # Update chunk information
                stream_info["chunk_count"] += 1
                stream_info["total_bytes"] += len(binary_data)
                
                # Add to buffer
                self.stream_buffers[stream_id].append(binary_data)
                
                # Call chunk received callback
                if stream_id in self.stream_callbacks and "on_chunk" in self.stream_callbacks[stream_id]:
                    try:
                        self.stream_callbacks[stream_id]["on_chunk"](stream_id, binary_data, chunk_data)
                    except Exception as e:
                        logger.error(f"Stream chunk callback error: {e}")
            
            except Exception as e:
                logger.error(f"Stream chunk processing error: {e}")
                return False, {"error": "chunk_processing_error", "message": str(e)}
        
        # Process final chunk
        if is_last:
            try:
                # Update metadata
                if "metadata" in chunk_data and chunk_data["metadata"]:
                    if isinstance(chunk_data["metadata"], dict):
                        stream_info["metadata"].update(chunk_data["metadata"])
                    elif isinstance(chunk_data["metadata"], str):
                        try:
                            metadata = json.loads(chunk_data["metadata"])
                            stream_info["metadata"].update(metadata)
                        except:
                            pass
                
                # Complete stream processing
                stream_info["status"] = "completed"
                stream_info["ended_at"] = datetime.now().isoformat()
                
                # Call completion callback
                if stream_id in self.stream_callbacks and "on_complete" in self.stream_callbacks[stream_id]:
                    try:
                        self.stream_callbacks[stream_id]["on_complete"](
                            stream_id, 
                            self.get_complete_stream_data(stream_id), 
                            stream_info
                        )
                    except Exception as e:
                        logger.error(f"Stream completion callback error: {e}")
                
                logger.info(f"Stream {stream_id} completed (total {stream_info['chunk_count']} chunks, {stream_info['total_bytes']/1024:.1f} KB)")
                
                # Create final response
                response = {
                    "status": "stream_completed",
                    "stream_id": stream_id,
                    "total_chunks": stream_info["chunk_count"],
                    "total_bytes": stream_info["total_bytes"],
                    "duration": self._calculate_stream_duration(stream_info)
                }
                
                return True, response
            
            except Exception as e:
                logger.error(f"Stream completion processing error: {e}")
                return False, {"error": "stream_completion_error", "message": str(e)}
        
        # Normal in-progress response
        return True, {
            "status": "chunk_received",
            "stream_id": stream_id,
            "chunk_index": chunk_data.get("chunk_index"),
            "received_chunks": stream_info["chunk_count"]
        }
    
    def register_stream_callback(self, stream_id: str, event_type: str, callback: Callable) -> bool:
        """
        Register callback for stream events
        
        Args:
            stream_id: Stream ID
            event_type: Event type ("on_chunk", "on_complete", "on_error")
            callback: Callback function
            
        Returns:
            Whether the registration was successful
        """
        if stream_id not in self.active_streams:
            logger.warning(f"Stream {stream_id} is not registered")
            return False
        
        if stream_id not in self.stream_callbacks:
            self.stream_callbacks[stream_id] = {}
        
        self.stream_callbacks[stream_id][event_type] = callback
        return True
    
    def get_complete_stream_data(self, stream_id: str) -> bytes:
        """
        Get complete data for a stream
        
        Args:
            stream_id: Stream ID
            
        Returns:
            Combined binary data
        """
        if stream_id not in self.stream_buffers:
            return b""
        
        # Join all chunks
        return b"".join(self.stream_buffers[stream_id])
    
    def clean_up_stream(self, stream_id: str) -> bool:
        """
        Clean up a stream
        
        Args:
            stream_id: Stream ID
            
        Returns:
            Whether the cleanup was successful
        """
        if stream_id not in self.active_streams:
            return False
        
        # Remove stream buffer
        if stream_id in self.stream_buffers:
            del self.stream_buffers[stream_id]
        
        # Remove callbacks
        if stream_id in self.stream_callbacks:
            del self.stream_callbacks[stream_id]
        
        # Remove from active streams list
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
        
        logger.info(f"Stream {stream_id} cleanup completed")
        return True
    
    def _calculate_stream_duration(self, stream_info: Dict[str, Any]) -> float:
        """
        Calculate stream duration
        
        Args:
            stream_info: Stream information
            
        Returns:
            Duration (seconds)
        """
        try:
            start_time = datetime.fromisoformat(stream_info["started_at"])
            end_time = datetime.fromisoformat(stream_info.get("ended_at", datetime.now().isoformat()))
            return (end_time - start_time).total_seconds()
        except:
            return 0.0


class DefaultHandler:
    """
    Server default handler class
    """
    
    def __init__(self):
        """
        Initialize default handler
        """
        # Create media stream manager
        self.stream_manager = MediaStreamManager()
    
    def handle_client(self, client_socket, address, client_id, server):
        """
        Handle client connection
        
        Args:
            client_socket: Client socket
            address: Client address (ip, port)
            client_id: Client ID
            server: Server instance
        """
        logger.info(f"Started client handling: {address[0]}:{address[1]} (ID: {client_id})")
        
        try:
            client_socket.settimeout(None)  # Disable timeout (blocking mode)
            
            # Client message receiving loop
            while True:
                try:
                    # Receive data
                    data = b""
                    while True:
                        chunk = client_socket.recv(4096)
                        if not chunk:
                            return  # Client closed connection
                            
                        data += chunk
                        
                        # Receipt complete if ends with newline
                        if data.endswith(b'\n'):
                            break
                    
                    # Remove trailing newline
                    data = data.rstrip(b'\n')
                    
                    # Process message
                    response = self._process_message(data, client_id, server)
                    
                    # Send response
                    if response is not None:
                        # Encode if string
                        if isinstance(response, str):
                            response_data = response.encode('utf-8') + b'\n'
                        # Byte sequence
                        elif isinstance(response, bytes):
                            response_data = response if response.endswith(b'\n') else response + b'\n'
                        # Otherwise convert to JSON
                        else:
                            response_data = json.dumps(response).encode('utf-8') + b'\n'
                        
                        client_socket.sendall(response_data)
                
                except ConnectionResetError:
                    logger.info(f"Client reset connection: {client_id}")
                    break
                    
                except ConnectionAbortedError:
                    logger.info(f"Connection aborted: {client_id}")
                    break
                    
                except socket.timeout:
                    logger.warning(f"Client connection timed out: {client_id}")
                    break
                
                except Exception as e:
                    logger.error(f"Error during client processing: {e}")
                    traceback.print_exc()
                    break
                
        finally:
            logger.info(f"Ending client connection: {client_id}")
            try:
                client_socket.close()
            except:
                pass
    
    def _process_message(self, data, client_id, server):
        """
        Process received message
        
        Args:
            data: Received data (bytes)
            client_id: Client ID
            server: Server instance
        
        Returns:
            Response data
        """
        try:
            # Protocol detection and deserialization
            try:
                # Check protocol header
                if data.startswith(b'{"protocol_name":'):
                    # Protocol-specified message
                    message = json.loads(data.decode('utf-8'))
                    protocol_name = message.get('protocol_name')
                    message_data = message.get('data', {})
                    
                    if protocol_name:
                        # If protocol_name is specified, look for corresponding endpoint/handler
                        if protocol_name in server.endpoints:
                            # Call registered endpoint/handler
                            try:
                                # Add client address information
                                if client_id in server.clients:
                                    _, address, _ = server.clients[client_id]
                                    message_data['client_address'] = f"{address[0]}:{address[1]}"
                                
                                # Call handler function
                                handler_func = server.endpoints[protocol_name]
                                response_data = handler_func(message_data, client_id)
                                
                                # Create response
                                return {
                                    'status': 'success',
                                    'data': response_data,
                                    'timestamp': datetime.now().isoformat()
                                }
                            except Exception as e:
                                logger.error(f"Protocol processing error ({protocol_name}): {e}")
                                return {
                                    'status': 'error',
                                    'message': f'Error during protocol processing: {str(e)}',
                                    'timestamp': datetime.now().isoformat()
                                }
                        else:
                            # Try loading from file if protocol handler not registered
                            protocol = load_protocol(protocol_name)
                            if protocol:
                                # Protocol exists but handler not registered
                                logger.warning(f"Protocol '{protocol_name}' exists but no handler is registered")
                                return {
                                    'status': 'error',
                                    'message': f'No handler registered for protocol {protocol_name}',
                                    'timestamp': datetime.now().isoformat()
                                }
                            else:
                                # Protocol not found
                                return {
                                    'status': 'error',
                                    'message': f'Unknown protocol: {protocol_name}',
                                    'timestamp': datetime.now().isoformat()
                                }
                else:
                    # Regular JSON message
                    message = json.loads(data.decode('utf-8'))
                    protocol_name = None
                    message_data = message
                    
            except json.JSONDecodeError:
                # Process binary data, such as media data
                protocol_name = self._detect_protocol_from_binary(data)
                if protocol_name:
                    protocol = load_protocol(protocol_name)
                    if protocol:
                        # Efficient deserialization based on protocol
                        message_data = deserialize_data_efficiently(data, protocol)
                    else:
                        message_data = {'_binary_data': True, 'size': len(data)}
                else:
                    # Unknown binary data
                    return {
                        'status': 'error',
                        'message': 'Unknown data format',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Detect media-related messages
            if self._is_media_message(message_data, protocol_name):
                return self._handle_media_message(message_data, client_id, server)
            
            # Process message by endpoint
            if "endpoint" in message_data:
                endpoint = message_data["endpoint"]
                
                # Check registered endpoints in server
                if endpoint in server.endpoints:
                    endpoint_func = server.endpoints[endpoint]
                    
                    # Execute endpoint function
                    try:
                        response_data = endpoint_func(message_data, client_id)
                        return {
                            'status': 'success',
                            'data': response_data,
                            'timestamp': datetime.now().isoformat()
                        }
                    except Exception as e:
                        logger.error(f"Endpoint processing error ({endpoint}): {e}")
                        return {
                            'status': 'error',
                            'message': f'Error processing endpoint: {str(e)}',
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    # Unregistered endpoint
                    logger.warning(f"Unknown endpoint requested: {endpoint}")
                    return {
                        'status': 'error',
                        'message': f'Unknown endpoint: {endpoint}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Basic request processing
            if "request" in message_data:
                request_type = message_data["request"]
                
                # Process built-in request types
                if request_type == "ping":
                    return handle_ping_request(message_data, client_id, server)
                    
                elif request_type == "status":
                    return handle_status_request(message_data, client_id, server)
                    
                elif request_type == "info":
                    return handle_info_request(message_data, client_id, server)
                    
                elif request_type == "echo":
                    return handle_echo_request(message_data, client_id, server)
                    
                else:
                    # Unknown request type
                    logger.warning(f"Unknown request type: {request_type}")
                    return {
                        'status': 'error',
                        'message': f'Unknown request type: {request_type}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Default response if no specific handler found
            return {
                'status': 'received',
                'message': 'Message received but no specific handler found',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during message processing: {e}")
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Internal server error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _detect_protocol_from_binary(self, data: bytes) -> Optional[str]:
        """
        Detect protocol from binary data
        
        Args:
            data: Binary data
            
        Returns:
            Detected protocol name, None if not found
        """
        # TODO: Implement more advanced protocol detection algorithm
        # Currently only assuming media protocols
        
        # Get list of media transfer protocols
        from ..protocol.protocol_file import list_available_protocols
        for protocol_name in list_available_protocols():
            if protocol_name.startswith("media_"):
                protocol = load_protocol(protocol_name)
                if protocol:
                    # Simple logic to detect compressed data
                    if protocol.get("options", {}).get("compression") in ["gzip", "zlib"] and data.startswith(b'\x1f\x8b'):
                        return protocol_name
                    elif protocol.get("options", {}).get("compression") == "bz2" and data.startswith(b'BZh'):
                        return protocol_name
        
        return None
    
    def _is_media_message(self, message_data: Dict[str, Any], protocol_name: Optional[str]) -> bool:
        """
        Determine if a message is media-related
        
        Args:
            message_data: Message data
            protocol_name: Protocol name (may be None)
            
        Returns:
            Whether the message is media-related
        """
        # Check by protocol name
        if protocol_name and ("media" in protocol_name or "stream" in protocol_name):
            return True
        
        # Check by message content
        if isinstance(message_data, dict):
            # If stream ID exists
            if "stream_id" in message_data:
                return True
            
            # If media type and content exist
            if "media_type" in message_data and "content" in message_data:
                return True
            
            # If action attribute is media-related
            if message_data.get("action", "").startswith("stream_") or message_data.get("action") == "start_stream":
                return True
        
        return False
    
    def _handle_media_message(self, message_data: Dict[str, Any], client_id: str, server) -> Dict[str, Any]:
        """
        Process media message
        
        Args:
            message_data: Message data
            client_id: Client ID
            server: Server instance
            
        Returns:
            Response data
        """
        try:
            # Stream-related message
            if "stream_id" in message_data:
                # Process stream chunk
                success, response = self.stream_manager.process_stream_chunk(message_data)
                
                if success:
                    return {
                        "status": "success",
                        "data": response,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "error": response.get("error", "unknown_error"),
                        "message": response.get("message", "Stream processing error"),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Single media data processing
            elif "media_type" in message_data and "content" in message_data:
                # Get media type
                media_type = message_data.get("media_type")
                
                # Decode media data
                binary_data, _ = decode_media_data(message_data)
                
                # Call registered media handler if available
                media_handler = self._get_media_handler(media_type, server)
                if media_handler:
                    result = media_handler(binary_data, message_data, client_id)
                    
                    # Return result based on response
                    if isinstance(result, dict):
                        result.setdefault("timestamp", datetime.now().isoformat())
                        return result
                    else:
                        return {
                            "status": "success",
                            "message": f"Received {len(binary_data)} bytes of media data ({media_type})",
                            "size": len(binary_data),
                            "timestamp": datetime.now().isoformat()
                        }
                
                # Default response
                return {
                    "status": "success",
                    "message": f"Received {len(binary_data)} bytes of media data ({media_type})",
                    "size": len(binary_data),
                    "media_type": media_type,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Other media commands
            else:
                return {
                    "status": "error",
                    "message": "Unknown media message format",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Media message processing error: {e}")
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error during media message processing: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_media_handler(self, media_type: str, server) -> Optional[Callable]:
        """
        Get handler function for a media type
        
        Args:
            media_type: Media type
            server: Server instance
            
        Returns:
            Handler function, None if not found
        """
        # Look for registered endpoint in server
        endpoint_name = f"media_{media_type}"
        if endpoint_name in server.endpoints:
            return server.endpoints[endpoint_name]
        
        # Look for generic media handler
        if "media_handler" in server.endpoints:
            return server.endpoints["media_handler"]
        
        return None


# Built-in request handler functions

def handle_ping_request(data, client_id, server):
    """
    Process ping request
    
    Args:
        data: Request data
        client_id: Client ID
        server: Server instance
    
    Returns:
        Response data
    """
    return {
        'status': 'success',
        'pong': True,
        'server_time': datetime.now().isoformat(),
        'timestamp': datetime.now().isoformat()
    }


def handle_status_request(data, client_id, server):
    """
    Process status request
    
    Args:
        data: Request data
        client_id: Client ID
        server: Server instance
    
    Returns:
        Status information
    """
    # Client connection count
    client_count = len(server.clients)
    
    # Server information
    status_info = {
        'status': 'running',
        'server_id': server.server_id,
        'server_name': server.server_name,
        'uptime': _calculate_uptime(server),
        'client_count': client_count,
        'max_connections': server.max_connections,
        'port': server.port,
        'timestamp': datetime.now().isoformat()
    }
    
    return {
        'status': 'success',
        'data': status_info
    }


def handle_info_request(data, client_id, server):
    """
    Process server information request
    
    Args:
        data: Request data
        client_id: Client ID
        server: Server instance
    
    Returns:
        Server information
    """
    # Detailed server information
    info = {
        'server_id': server.server_id,
        'server_name': server.server_name,
        'protocols': server.protocols,
        'hash': server.src_hash[:16],  # Only show part of the hash
        'endpoints': list(server.endpoints.keys()),
        'client_count': len(server.clients),
        'max_connections': server.max_connections,
        'port': server.port,
        'host': server.host,
        'project_id': server.project_id if hasattr(server, 'project_id') else None
    }
    
    # Add peer information if available
    if hasattr(server, 'server_peer') and server.server_peer:
        peers = server.server_peer.get_connected_peers()
        info['peers'] = [{'id': p.get('id'), 'name': p.get('name')} for p in peers]
    
    return {
        'status': 'success',
        'data': info,
        'timestamp': datetime.now().isoformat()
    }


def handle_echo_request(data, client_id, server):
    """
    Process echo request
    
    Args:
        data: Request data
        client_id: Client ID
        server: Server instance
    
    Returns:
        Echo response
    """
    echo_data = data.get('data', {})
    return {
        'status': 'success',
        'echo': echo_data,
        'timestamp': datetime.now().isoformat()
    }


def _calculate_uptime(server):
    """
    Calculate server uptime
    
    Args:
        server: Server instance
    
    Returns:
        Uptime (seconds)
    """
    if hasattr(server, 'start_time'):
        return (datetime.now() - server.start_time).total_seconds()
    return 0