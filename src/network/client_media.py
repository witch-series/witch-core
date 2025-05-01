"""
Client media module providing media transfer and streaming functionality

Main features:
- Media data transfer
- Media streaming
- Chunk-based transfer for large files
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, BinaryIO, Callable

from .client_message import ClientMessage
from ..protocol.protocol_data import (
    encode_media_data,
    decode_media_data,
    chunk_media_data, 
    create_media_stream_chunk
)
from ..protocol.protocol_core import create_protocol
from ..protocol.protocol_file import save_protocol, load_protocol

# Logger configuration
logger = logging.getLogger("WitchClientMedia")


def create_media_protocol(protocol_name, media_type, compression="gzip", format_type="binary"):
    """
    Create a media transfer protocol
    
    Args:
        protocol_name: Name of the protocol
        media_type: Media type ("image", "audio", "video", etc.)
        compression: Compression method
        format_type: Format type
    
    Returns:
        dict: Created protocol
    """
    return create_protocol(
        number="101",
        name=protocol_name,
        data_names=["data", "media_type", "chunk_index", "total_chunks", "stream_id", "is_last", "timestamp"],
        options={
            "compression": compression,
            "format": format_type,
            "chunk_size": 64 * 1024,  # 64KB chunks by default
            "media_type": media_type
        },
        description=f"Protocol for {media_type} data transfer"
    )


class ClientMedia(ClientMessage):
    """
    Client class with media handling and streaming functionality
    """
    
    def __init__(self, host=None, port=None, timeout=5.0, 
                auto_reconnect=False, max_reconnect_attempts=3, reconnect_delay=1.0):
        """
        Initialize the client media handler
        
        Args:
            host (str): Server hostname or IP address
            port (int): Server port number
            timeout (float): Connection timeout in seconds
            auto_reconnect (bool): Whether to automatically reconnect when connection is lost
            max_reconnect_attempts (int): Maximum number of reconnection attempts
            reconnect_delay (float): Delay between reconnection attempts in seconds
        """
        super().__init__(host, port, timeout, auto_reconnect, max_reconnect_attempts, reconnect_delay)
        
        # Streaming settings
        self.active_streams = {}  # stream_id -> stream_info
        self.stream_callbacks = {}  # stream_id -> callback_function
    
    def send_media_data(self, media_data: bytes, media_type: str = "image",
                       metadata: Dict[str, Any] = None, chunk_size: int = None) -> Optional[Dict[str, Any]]:
        """
        Send media data
        
        Args:
            media_data: Binary data to send
            media_type: Media type ("image", "audio", "video", "binary")
            metadata: Media metadata
            chunk_size: Chunk size (bytes), None sends all at once
            
        Returns:
            Server response, None on error
        """
        # Create media transfer protocol
        protocol_name = f"media_transfer_{media_type}"
        protocol = load_protocol(protocol_name)
        
        if not protocol:
            # Create protocol if it doesn't exist
            protocol = create_media_protocol(protocol_name, media_type, "gzip", "binary")
            save_protocol(protocol)
        
        # Get chunk size
        if chunk_size is None:
            # Get chunk size from protocol
            chunk_size = protocol.get("options", {}).get("chunk_size", 64 * 1024)
        
        # Send all at once if media size is small
        if len(media_data) <= chunk_size:
            # Encode media data
            media_message = encode_media_data(media_data, media_type)
            
            # Add metadata if available
            if metadata:
                if isinstance(metadata, dict):
                    media_message.update(metadata)
                else:
                    media_message["metadata"] = str(metadata)
            
            # Send using efficient protocol
            return self.send_efficient_message(media_message, protocol_name)
        
        # Send large media data in chunks
        else:
            return self._send_chunked_media(media_data, media_type, metadata, chunk_size, protocol, protocol_name)
    
    def _send_chunked_media(self, media_data: bytes, media_type: str,
                          metadata: Dict[str, Any], chunk_size: int,
                          protocol: Dict[str, Any], protocol_name: str) -> Optional[Dict[str, Any]]:
        """
        Send large media data in chunks
        
        Args:
            media_data: Binary data to send
            media_type: Media type
            metadata: Media metadata
            chunk_size: Chunk size (bytes)
            protocol: Protocol definition to use
            protocol_name: Protocol name
            
        Returns:
            Server response for the last chunk, None on error
        """
        # Split media data into chunks
        chunks = chunk_media_data(media_data, chunk_size)
        total_chunks = len(chunks)
        stream_id = str(uuid.uuid4())
        
        logger.info(f"Sending media data in {total_chunks} chunks (Stream ID: {stream_id})")
        
        # Initialize response
        response = None
        
        # Send each chunk
        for i, chunk in enumerate(chunks):
            # Check if it's the last chunk
            is_last = (i == total_chunks - 1)
            
            # Create stream chunk information
            chunk_info = create_media_stream_chunk(
                chunk_data=chunk,
                chunk_index=i,
                total_chunks=total_chunks,
                stream_id=stream_id,
                media_type=media_type,
                is_last=is_last,
                metadata=metadata if is_last else None  # Metadata only included in the last chunk
            )
            
            # Send chunk
            response = self.send_efficient_message(chunk_info, protocol_name)
            
            # Error check
            if response is None:
                logger.error(f"Failed to send chunk {i+1}/{total_chunks}")
                return None
            
            # Progress report
            if (i + 1) % 10 == 0 or is_last:
                logger.info(f"Sent chunk {i+1}/{total_chunks} ({((i+1)/total_chunks*100):.1f}%)")
        
        logger.info("Media data sent successfully")
        return response
    
    def start_media_stream(self, media_type: str = "video", 
                         metadata: Dict[str, Any] = None, 
                         callback: Callable = None) -> str:
        """
        Start sending a media stream
        
        Args:
            media_type: Media type ("video", "audio", etc.)
            metadata: Stream metadata
            callback: Callback function for stream status notifications
            
        Returns:
            stream_id: Stream ID
        """
        # Generate stream ID
        stream_id = str(uuid.uuid4())
        
        # Create or get media transfer protocol
        protocol_name = f"media_stream_{media_type}"
        protocol = load_protocol(protocol_name)
        
        if not protocol:
            # Create protocol if it doesn't exist
            protocol = create_media_protocol(
                protocol_name, 
                media_type, 
                "zlib",  # Lightweight compression for streaming
                "binary"
            )
            save_protocol(protocol)
        
        # Save stream information
        self.active_streams[stream_id] = {
            "id": stream_id,
            "type": media_type,
            "protocol": protocol_name,
            "started_at": datetime.now().isoformat(),
            "chunk_count": 0,
            "total_bytes": 0,
            "metadata": metadata or {},
            "status": "active"
        }
        
        # Save callback function
        if callback:
            self.stream_callbacks[stream_id] = callback
        
        # Send stream start message
        start_message = {
            "stream_id": stream_id,
            "media_type": media_type,
            "action": "start_stream",
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        self.send_efficient_message(start_message, protocol_name, wait_for_response=False)
        logger.info(f"Started media stream ({media_type}) (Stream ID: {stream_id})")
        
        return stream_id
    
    def stream_media_chunk(self, stream_id: str, chunk_data: bytes) -> bool:
        """
        Send a media chunk to an active stream
        
        Args:
            stream_id: Stream ID
            chunk_data: Chunk data to send
            
        Returns:
            bool: Whether the send was successful
        """
        # Get stream information
        if stream_id not in self.active_streams:
            logger.error(f"Stream {stream_id} does not exist or has already ended")
            return False
        
        stream_info = self.active_streams[stream_id]
        
        # Check if stream is active
        if stream_info["status"] != "active":
            logger.error(f"Stream {stream_id} is not currently active (Status: {stream_info['status']})")
            return False
        
        # Update chunk information
        chunk_index = stream_info["chunk_count"]
        stream_info["chunk_count"] += 1
        stream_info["total_bytes"] += len(chunk_data)
        
        # Create stream chunk information
        chunk_info = create_media_stream_chunk(
            chunk_data=chunk_data,
            chunk_index=chunk_index,
            total_chunks=-1,  # Total unknown for streaming
            stream_id=stream_id,
            media_type=stream_info["type"],
            is_last=False,
            metadata=None
        )
        
        # Send chunk
        try:
            self.send_efficient_message(chunk_info, stream_info["protocol"], wait_for_response=False)
            
            # Progress report (every 10 chunks)
            if chunk_index % 10 == 0:
                logger.debug(f"Sent chunk {chunk_index} to stream {stream_id} (Total {stream_info['total_bytes']/1024:.1f} KB)")
            
            return True
                
        except Exception as e:
            logger.error(f"Stream chunk send error: {e}")
            return False
    
    def stop_media_stream(self, stream_id: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Stop sending a media stream
        
        Args:
            stream_id: Stream ID
            metadata: Additional metadata to send upon stopping
            
        Returns:
            bool: Whether the operation was successful
        """
        # Get stream information
        if stream_id not in self.active_streams:
            logger.warning(f"Stream {stream_id} has already ended or does not exist")
            return False
        
        stream_info = self.active_streams[stream_id]
        protocol_name = stream_info["protocol"]
        
        # Create stream stop message
        final_metadata = stream_info["metadata"].copy()
        if metadata:
            final_metadata.update(metadata)
        
        final_metadata.update({
            "total_chunks": stream_info["chunk_count"],
            "total_bytes": stream_info["total_bytes"],
            "duration": (datetime.now() - datetime.fromisoformat(stream_info["started_at"])).total_seconds()
        })
        
        # Create final chunk (empty data)
        final_chunk = create_media_stream_chunk(
            chunk_data=b"",
            chunk_index=stream_info["chunk_count"],
            total_chunks=stream_info["chunk_count"] + 1,
            stream_id=stream_id,
            media_type=stream_info["type"],
            is_last=True,
            metadata=final_metadata
        )
        
        # Send stop message
        try:
            self.send_efficient_message(final_chunk, protocol_name, wait_for_response=False)
            
            # Update stream status
            stream_info["status"] = "completed"
            stream_info["ended_at"] = datetime.now().isoformat()
            
            logger.info(f"Stopped stream {stream_id} (Total {stream_info['chunk_count']} chunks, {stream_info['total_bytes']/1024:.1f} KB)")
            
            # Call callback
            if stream_id in self.stream_callbacks:
                try:
                    self.stream_callbacks[stream_id](stream_info, "completed")
                    del self.stream_callbacks[stream_id]
                except Exception as e:
                    logger.error(f"Stream stop callback error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Stream stop message send error: {e}")
            stream_info["status"] = "error"
            return False