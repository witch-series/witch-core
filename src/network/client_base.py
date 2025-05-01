"""
Base client module providing core connection functionality

Main features:
- Server connection
- Basic message sending
- Response receiving
- Connection management
"""

import socket
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Union, Optional

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WitchClientBase")


class ClientBase:
    """
    Base client class for handling connection and basic communications
    """
    
    def __init__(self, host=None, port=None, timeout=5.0, 
                auto_reconnect=False, max_reconnect_attempts=3, reconnect_delay=1.0):
        """
        Initialize the client base
        
        Args:
            host (str): Server hostname or IP address
            port (int): Server port number
            timeout (float): Connection timeout in seconds
            auto_reconnect (bool): Whether to automatically reconnect when connection is lost
            max_reconnect_attempts (int): Maximum number of reconnection attempts
            reconnect_delay (float): Delay between reconnection attempts in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        # Connection state
        self.socket = None
        self.connected = False
        self.client_id = str(uuid.uuid4())
        
        # If host and port are provided, connect immediately
        if host and port:
            self.connect()
    
    def connect(self) -> bool:
        """
        Connect to the server
        
        Returns:
            bool: Whether the connection was successful
        """
        if self.connected:
            logger.info("Already connected")
            return True
            
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            # Connect to server
            logger.info(f"Connecting to server {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to server {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.socket = None
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from the server
        """
        if not self.connected:
            return
            
        # Close the socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            
        self.socket = None
        self.connected = False
        logger.info("Disconnected from the server")
    
    def is_connected(self) -> bool:
        """
        Check the connection status
        
        Returns:
            bool: Whether the client is connected
        """
        return self.connected and self.socket is not None
    
    def _try_reconnect(self) -> bool:
        """
        Attempt to reconnect
        
        Returns:
            bool: Whether the reconnection was successful
        """
        if not self.auto_reconnect:
            return False
            
        # Disconnect
        self.disconnect()
        
        # Attempt to reconnect
        for attempt in range(self.max_reconnect_attempts):
            logger.info(f"Attempting to reconnect ({attempt+1}/{self.max_reconnect_attempts})...")
            if self.connect():
                return True
                
            # Add delay
            time.sleep(self.reconnect_delay)
            
        logger.error("Failed to reconnect")
        return False
    
    def send(self, data: Union[str, Dict[str, Any], bytes]) -> bool:
        """
        Send data
        
        Args:
            data: Data to send (string, dictionary, or bytes)
            
        Returns:
            bool: Whether the send was successful
        """
        # Connection check
        if not self.is_connected():
            if not self._try_reconnect():
                logger.error("Send error: Not connected")
                return False
        
        try:
            # Process based on data format
            if isinstance(data, dict):
                # Convert dictionary to JSON
                data_bytes = json.dumps(data).encode('utf-8') + b'\n'
            elif isinstance(data, str):
                # Encode string
                data_bytes = data.encode('utf-8') + b'\n'
            elif isinstance(data, bytes):
                # Use bytes as is
                data_bytes = data if data.endswith(b'\n') else data + b'\n'
            else:
                # Convert other types to string
                data_bytes = str(data).encode('utf-8') + b'\n'
            
            # Send data
            self.socket.sendall(data_bytes)
            return True
            
        except Exception as e:
            logger.error(f"Send error: {e}")
            
            # Try to reconnect if connection was lost
            if self.auto_reconnect:
                if self._try_reconnect():
                    # Try to resend
                    return self.send(data)
            
            return False
    
    def receive(self, buffer_size=4096) -> Optional[str]:
        """
        Receive data
        
        Args:
            buffer_size: Size of the receive buffer
            
        Returns:
            str: Received data, None on error
        """
        # Connection check
        if not self.is_connected():
            if not self._try_reconnect():
                logger.error("Receive error: Not connected")
                return None
        
        try:
            # Receive data
            data = b""
            while True:
                chunk = self.socket.recv(buffer_size)
                if not chunk:
                    break
                    
                data += chunk
                
                # Reception complete if ending with newline
                if data.endswith(b'\n'):
                    break
            
            # Convert received data to string
            return data.decode('utf-8').strip() if data else None
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            
            # Try to reconnect if connection was lost
            if self.auto_reconnect:
                if self._try_reconnect():
                    # Try to receive again
                    return self.receive(buffer_size)
            
            return None