#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Media Data Transfer and Streaming Implementation Example

This sample demonstrates how to efficiently transfer media data such as images and audio,
and how to implement real-time streaming.

Usage examples:
- Server mode: python media_transfer_example.py server
- Client mode (image transfer): python media_transfer_example.py client_image <image_file_path>
- Client mode (audio transfer): python media_transfer_example.py client_audio <audio_file_path>
- Client mode (webcam stream): python media_transfer_example.py stream_webcam
"""

import os
import sys
import time
import argparse
from datetime import datetime
import json
import io
import uuid
from pathlib import Path
from threading import Thread
import logging

# Add witch-core path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import witch-core modules
from src.network.server import Server
from src.network.client import Client
from src.protocol.protocol_data import (
    encode_media_data, 
    decode_media_data, 
    create_media_protocol, 
    create_media_stream_chunk
)
from src.protocol.protocol_file import save_protocol, load_protocol

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MediaTransferExample")

# Server port
SERVER_PORT = 8888

# Save directory
SAVE_DIR = os.path.join(current_dir, "media_received")
os.makedirs(SAVE_DIR, exist_ok=True)


def handle_media_image(data, metadata, client_id):
    """
    Server endpoint to process image media
    
    Args:
        data: Image binary data
        metadata: Metadata
        client_id: Client ID
    
    Returns:
        Response data
    """
    logger.info(f"Received image data ({len(data)/1024:.1f} KB)")
    
    # Display image information
    width = metadata.get("width", "Unknown")
    height = metadata.get("height", "Unknown")
    format_type = metadata.get("format", "jpg")
    logger.info(f"Image info: {width}x{height}, Format: {format_type}")
    
    # Save to file
    filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
    filepath = os.path.join(SAVE_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(data)
    
    logger.info(f"Image saved: {filepath}")
    
    # Response data
    return {
        "status": "success",
        "message": "Image received and saved",
        "saved_path": filename,
        "size": len(data)
    }


def handle_media_audio(data, metadata, client_id):
    """
    Server endpoint to process audio media
    
    Args:
        data: Audio binary data
        metadata: Metadata
        client_id: Client ID
    
    Returns:
        Response data
    """
    logger.info(f"Received audio data ({len(data)/1024:.1f} KB)")
    
    # Display audio information
    duration = metadata.get("duration", "Unknown")
    format_type = metadata.get("format", "wav")
    sample_rate = metadata.get("sample_rate", "Unknown")
    channels = metadata.get("channels", "Unknown")
    
    logger.info(f"Audio info: Duration {duration}s, Format: {format_type}, Sample rate: {sample_rate}, Channels: {channels}")
    
    # Save to file
    filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
    filepath = os.path.join(SAVE_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(data)
    
    logger.info(f"Audio saved: {filepath}")
    
    # Response data
    return {
        "status": "success",
        "message": "Audio received and saved",
        "saved_path": filename,
        "size": len(data),
        "duration": duration
    }


def handle_media_video(data, metadata, client_id):
    """
    Server endpoint to process video media
    
    Args:
        data: Video binary data
        metadata: Metadata
        client_id: Client ID
    
    Returns:
        Response data
    """
    logger.info(f"Received video data ({len(data)/1024:.1f} KB)")
    
    # Display video information
    duration = metadata.get("duration", "Unknown")
    format_type = metadata.get("format", "mp4")
    width = metadata.get("width", "Unknown")
    height = metadata.get("height", "Unknown")
    fps = metadata.get("fps", "Unknown")
    
    logger.info(f"Video info: {width}x{height}, {fps}fps, Duration {duration}s, Format: {format_type}")
    
    # Save to file
    filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
    filepath = os.path.join(SAVE_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(data)
    
    logger.info(f"Video saved: {filepath}")
    
    # Response data
    return {
        "status": "success",
        "message": "Video received and saved",
        "saved_path": filename,
        "size": len(data),
        "duration": duration
    }


def handle_media_stream_video(stream_id, frame_data, chunk_info):
    """
    Callback function to process video stream data
    
    Args:
        stream_id: Stream ID
        frame_data: Frame binary data
        chunk_info: Chunk information
    """
    # Frame number
    frame_number = chunk_info.get("chunk_index", 0)
    
    # Display progress every 10 frames
    if frame_number % 10 == 0:
        logger.info(f"Stream {stream_id}: Frame {frame_number} received ({len(frame_data)/1024:.1f} KB)")
    
    # Process the frame as needed
    # Example: Display or analyze the frame using OpenCV
    # Processing is omitted in this example


def handle_stream_completed(stream_id, full_data, stream_info):
    """
    Callback function called when the stream is completed
    
    Args:
        stream_id: Stream ID
        full_data: Complete stream data (all chunks combined)
        stream_info: Stream information
    """
    media_type = stream_info.get("type", "unknown")
    total_chunks = stream_info.get("chunk_count", 0)
    total_bytes = stream_info.get("total_bytes", 0)
    duration = datetime.now().timestamp() - datetime.fromisoformat(stream_info.get("started_at")).timestamp()
    
    logger.info(f"Stream {stream_id} ({media_type}) completed")
    logger.info(f"Total: {total_chunks} chunks, {total_bytes/1024:.1f} KB, Duration: {duration:.1f}s")
    
    # Save video stream if applicable
    if media_type == "video" and full_data:
        filename = f"stream_{stream_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        filepath = os.path.join(SAVE_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(full_data)
        
        logger.info(f"Stream data saved: {filepath}")


def run_server():
    """
    Start a server that supports media transfer
    """
    logger.info("Starting media transfer server...")
    
    # Create server
    server = Server(
        port=SERVER_PORT,
        server_name="MediaTransferServer",
        max_connections=10
    )
    
    # Register handlers for each media type
    server.register_endpoint("media_image", handle_media_image)
    server.register_endpoint("media_audio", handle_media_audio)
    server.register_endpoint("media_video", handle_media_video)
    
    # Set stream handler
    def stream_handler(data, client_id):
        """Handler for stream start requests"""
        stream_id = data.get("stream_id")
        media_type = data.get("media_type", "unknown")
        
        # Create new stream ID if not specified
        if not stream_id:
            stream_id = str(uuid.uuid4())
        
        logger.info(f"New stream start request: {stream_id} ({media_type})")
        
        # Register stream with stream manager
        server.handler.stream_manager.register_stream(
            stream_id=stream_id, 
            media_type=media_type, 
            metadata=data.get("metadata")
        )
        
        # Register stream callbacks
        if media_type == "video":
            server.handler.stream_manager.register_stream_callback(
                stream_id, "on_chunk", handle_media_stream_video
            )
        
        # Register completion callback
        server.handler.stream_manager.register_stream_callback(
            stream_id, "on_complete", handle_stream_completed
        )
        
        return {
            "stream_id": stream_id,
            "status": "stream_started",
            "server_time": datetime.now().isoformat()
        }
    
    # Register stream handler
    server.register_endpoint("start_stream", stream_handler)
    
    # Start server
    if server.start():
        logger.info(f"Media transfer server started (Port {SERVER_PORT})")
        logger.info(f"Received media files will be saved in {SAVE_DIR}")
        
        try:
            # Keep main thread running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nStopping server...")
        finally:
            server.stop()
    else:
        logger.error("Failed to start server")


def send_image_file(filepath):
    """
    Send an image file to the server
    
    Args:
        filepath: Path to the image file
    """
    # Check if file exists
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return
    
    try:
        # Read image file
        with open(filepath, 'rb') as f:
            image_data = f.read()
        
        logger.info(f"Image file loaded: {filepath} ({len(image_data)/1024:.1f} KB)")
        
        # Determine image format
        file_ext = os.path.splitext(filepath)[1].lower().lstrip('.')
        if not file_ext:
            file_ext = 'jpg'  # Default to JPG
        
        # Create client
        client = Client(host="localhost", port=SERVER_PORT)
        
        if not client.connect():
            logger.error("Failed to connect to server")
            return
        
        # Create image metadata
        metadata = {
            "format": file_ext,
            "filepath": os.path.basename(filepath),
            "timestamp": datetime.now().isoformat()
        }
        
        # Create media protocol
        protocol = create_media_protocol("media_transfer_image", "image", "gzip", "binary")
        save_protocol(protocol)
        
        logger.info("Sending image to server...")
        start_time = time.time()
        
        # Send image data
        response = client.send_media_data(
            media_data=image_data,
            media_type="image",
            metadata=metadata
        )
        
        elapsed = time.time() - start_time
        
        if response:
            logger.info(f"Send complete ({elapsed:.2f}s)")
            logger.info(f"Server response: {response}")
        else:
            logger.error("Failed to send")
        
        # Disconnect
        client.disconnect()
        
    except Exception as e:
        logger.error(f"Image send error: {e}")


def send_audio_file(filepath):
    """
    Send an audio file to the server
    
    Args:
        filepath: Path to the audio file
    """
    # Check if file exists
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return
    
    try:
        # Read audio file
        with open(filepath, 'rb') as f:
            audio_data = f.read()
        
        logger.info(f"Audio file loaded: {filepath} ({len(audio_data)/1024:.1f} KB)")
        
        # Determine audio format
        file_ext = os.path.splitext(filepath)[1].lower().lstrip('.')
        if not file_ext:
            file_ext = 'wav'  # Default to WAV
        
        # Create client
        client = Client(host="localhost", port=SERVER_PORT)
        
        if not client.connect():
            logger.error("Failed to connect to server")
            return
        
        # Create audio metadata
        metadata = {
            "format": file_ext,
            "filepath": os.path.basename(filepath),
            "timestamp": datetime.now().isoformat()
        }
        
        # Create media protocol
        protocol = create_media_protocol("media_transfer_audio", "audio", "gzip", "binary")
        save_protocol(protocol)
        
        logger.info("Sending audio to server...")
        start_time = time.time()
        
        # Send audio data
        response = client.send_media_data(
            media_data=audio_data,
            media_type="audio",
            metadata=metadata
        )
        
        elapsed = time.time() - start_time
        
        if response:
            logger.info(f"Send complete ({elapsed:.2f}s)")
            logger.info(f"Server response: {response}")
        else:
            logger.error("Failed to send")
        
        # Disconnect
        client.disconnect()
        
    except Exception as e:
        logger.error(f"Audio send error: {e}")


def stream_webcam():
    """
    Stream webcam video in real-time
    Note: This feature requires OpenCV (cv2)
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.error("OpenCV (cv2) is not installed. Install it using 'pip install opencv-python'")
        return
    
    logger.info("Initializing webcam streaming...")
    
    # Create client
    client = Client(host="localhost", port=SERVER_PORT)
    
    if not client.connect():
        logger.error("Failed to connect to server")
        return
    
    # Start webcam capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Failed to open webcam")
        client.disconnect()
        return
    
    # Get camera information
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    logger.info(f"Webcam: {width}x{height} @{fps}fps")
    
    # Stream start request
    start_stream_request = {
        "endpoint": "start_stream",
        "media_type": "video",
        "metadata": {
            "width": width,
            "height": height,
            "fps": fps,
            "format": "jpg"
        }
    }
    
    # Start stream
    response = client.send_efficient_message(start_stream_request)
    if not response or response.get("status") != "success":
        logger.error("Failed to start stream")
        client.disconnect()
        cap.release()
        return
    
    stream_id = response.get("data", {}).get("stream_id")
    if not stream_id:
        logger.error("Failed to get stream ID")
        client.disconnect()
        cap.release()
        return
    
    logger.info(f"Streaming started: ID {stream_id}")
    
    # Start stream
    stream_id = client.start_media_stream(
        media_type="video",
        metadata={
            "width": width,
            "height": height,
            "fps": fps,
            "format": "jpg"
        }
    )
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to capture frame")
                break
            
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_data = buffer.tobytes()
            
            # Send frame to stream
            client.stream_media_chunk(stream_id, frame_data)
            
            frame_count += 1
            
            # Display frame in window
            cv2.imshow('Streaming', frame)
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Target 30 frames per second
            time.sleep(0.033)  # Approx. 30fps
    
    except KeyboardInterrupt:
        logger.info("Stopping streaming...")
    
    except Exception as e:
        logger.error(f"Streaming error: {e}")
    
    finally:
        # Stop streaming
        elapsed = time.time() - start_time
        client.stop_media_stream(
            stream_id, 
            metadata={
                "total_frames": frame_count,
                "duration": elapsed,
                "avg_fps": frame_count / elapsed if elapsed > 0 else 0
            }
        )
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        client.disconnect()
        
        logger.info(f"Streaming ended: {frame_count} frames, {elapsed:.1f}s ({frame_count/elapsed:.1f} fps)")


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description="Sample for media data transfer and streaming")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Server command
    subparsers.add_parser("server", help="Start media transfer server")
    
    # Image transfer command
    image_parser = subparsers.add_parser("client_image", help="Send image file")
    image_parser.add_argument("filepath", help="Path to the image file to send")
    
    # Audio transfer command
    audio_parser = subparsers.add_parser("client_audio", help="Send audio file")
    audio_parser.add_argument("filepath", help="Path to the audio file to send")
    
    # Webcam streaming command
    subparsers.add_parser("stream_webcam", help="Stream webcam video")
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == "server":
        run_server()
    
    elif args.command == "client_image":
        send_image_file(args.filepath)
    
    elif args.command == "client_audio":
        send_audio_file(args.filepath)
    
    elif args.command == "stream_webcam":
        stream_webcam()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()