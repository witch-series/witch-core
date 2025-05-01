"""
Client message module providing protocol message handling functionality

Main features:
- Protocol-based message sending
- Efficient data serialization
- Iteration protocol support
"""

import socket
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union, Tuple, Callable

from .client_base import ClientBase
from ..protocol.protocol_data import (
    serialize_data_efficiently, 
    deserialize_data_efficiently
)
from ..protocol.protocol_file import load_protocol

# Logger configuration
logger = logging.getLogger("WitchClientMessage")


class ClientMessage(ClientBase):
    """
    Client class with message handling functionality
    """
    
    def send_message(self, host, port, message, wait_for_response=True):
        """
        Send a message to the server and optionally wait for a response
        
        Args:
            host (str): Hostname or IP address of the target server
            port (int): Port number of the target server
            message (dict): Message to send (data that can be converted to JSON format)
            wait_for_response (bool): Whether to wait for a response
            
        Returns:
            dict or None: Server response, or None if error/no response requested
        """
        try:
            # Create socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.timeout)
            
            # Connect to server
            logger.info(f"Connecting to server {host}:{port}...")
            client_socket.connect((host, port))
            logger.info(f"Connected to server {host}:{port}")
            
            # Convert message to JSON format
            if isinstance(message, dict):
                message = json.dumps(message)
            
            # Send message
            client_socket.sendall(message.encode('utf-8') + b'\n')
            logger.info(f"Message sent: {message[:100]}...")
            
            if wait_for_response:
                # Receive response
                data = b""
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    
                    # Detect end of reception (ends with newline)
                    if data.endswith(b'\n'):
                        break
                
                if data:
                    # Parse JSON response
                    try:
                        response = json.loads(data.decode('utf-8').strip())
                        logger.info("Response received")
                        client_socket.close()
                        return response
                    except json.JSONDecodeError:
                        logger.warning("Received response is not in JSON format")
                        client_socket.close()
                        return data.decode('utf-8').strip()
                else:
                    logger.warning("No response received")
            
            # Close socket
            client_socket.close()
            return None
            
        except socket.timeout:
            logger.error(f"Connection timeout: {host}:{port}")
            return None
        
        except ConnectionRefusedError:
            logger.error(f"Connection refused: {host}:{port}")
            return None
        
        except Exception as e:
            logger.error(f"Communication error: {e}")
            return None
    
    def send_protocol_message(self, host, port, protocol_name, data, wait_for_response=True):
        """
        Send a message following a specific protocol
        
        Args:
            host (str): Hostname or IP address of the target server
            port (int): Port number of the target server
            protocol_name (str): Name of the protocol to use
            data (dict): Data to send
            wait_for_response (bool): Whether to wait for a response
            
        Returns:
            dict or None: Server response, or None if error/no response requested
        """
        # Create protocol message
        message = {
            'protocol_name': protocol_name,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send message
        return self.send_message(host, port, message, wait_for_response)

    def send_iteration_protocol(self, host, port, protocol_name, data, max_iterations=None, 
                               callback=None, timeout_override=None):
        """
        Perform continuous message exchange using an iteration protocol.
        
        Args:
            host (str): Hostname or IP address of the target server
            port (int): Port number of the target server
            protocol_name (str): Name of the protocol to use (iteration-compatible)
            data (dict): Initial data to send
            max_iterations (int, optional): Maximum number of iterations. None follows protocol settings
            callback (function, optional): Callback function to call on each response 
                                         callback(response, iteration_count) -> continue_flag
            timeout_override (float, optional): Override timeout duration
            
        Returns:
            dict: Final response data
            int: Number of completed iterations
            str: Termination status ('complete', 'max_reached', 'callback_terminated', 'error')
        """
        # Initial settings
        iteration_count = 0
        current_data = data.copy()
        original_timeout = self.timeout
        status = 'error'  # Default status
        final_response = None
        
        try:
            # Temporarily change timeout (if needed)
            if timeout_override is not None:
                self.timeout = timeout_override
            
            # Loop until continue flag is false
            continue_flag = True
            
            while continue_flag:
                # Update and add iteration count
                iteration_count += 1
                current_data['iteration_count'] = iteration_count
                
                # Send message and receive response
                logger.info(f"Sending iteration {iteration_count}...")
                response = self.send_protocol_message(host, port, protocol_name, current_data)
                
                # Error check
                if response is None:
                    status = 'error'
                    break
                
                # Save response
                final_response = response
                
                # Call callback if available
                if callback is not None:
                    callback_result = callback(response, iteration_count)
                    if not callback_result:
                        status = 'callback_terminated'
                        continue_flag = False
                        continue
                
                # Get continue flag from protocol manager
                # (Local import for this purpose)
                from ..protocol.protocol_manager import is_continue_requested
                continue_flag = is_continue_requested(response.get('data', {}))
                
                # Check maximum iterations
                if max_iterations is not None and iteration_count >= max_iterations:
                    status = 'max_reached'
                    break
                
                # Update data for next iteration
                current_data = response.get('data', {})
            
            # Normal termination
            if status == 'error' and final_response is not None:
                status = 'complete'
            
            return final_response, iteration_count, status
            
        except Exception as e:
            logger.error(f"Iteration protocol error: {e}")
            return final_response, iteration_count, 'error'
            
        finally:
            # Restore timeout setting
            if timeout_override is not None:
                self.timeout = original_timeout
    
    def send_efficient_message(self, message: Dict[str, Any], protocol_name: str = None,
                             wait_for_response: bool = True) -> Optional[Dict[str, Any]]:
        """
        Send a message efficiently using protocol definitions.
        
        Args:
            message: Message to send
            protocol_name: Protocol name (None uses JSON conversion)
            wait_for_response: Whether to wait for a response
            
        Returns:
            Server response, None on error
        """
        # Connection check
        if not self.is_connected():
            if not self._try_reconnect():
                logger.error("Send error: Not connected")
                return None
        
        try:
            # Load protocol
            protocol = None
            if protocol_name:
                protocol = load_protocol(protocol_name)
                
            # Serialize data
            if protocol:
                # Efficient serialization based on protocol
                serialized = serialize_data_efficiently(message, protocol)
            else:
                # Normal JSON conversion
                serialized = json.dumps(message).encode('utf-8')
            
            # Add newline at the end
            if not serialized.endswith(b'\n'):
                serialized += b'\n'
            
            # Send data
            self.socket.sendall(serialized)
            logger.info(f"Efficient message sent (size: {len(serialized)} bytes)")
            
            if not wait_for_response:
                return None
            
            # Receive response
            data = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Reception complete if ending with newline
                if data.endswith(b'\n'):
                    break
            
            # Deserialize response
            if not data:
                logger.warning("No response received")
                return None
            
            data = data.rstrip(b'\n')  # Remove trailing newline
            
            if protocol:
                # Efficient deserialization based on protocol
                response = deserialize_data_efficiently(data, protocol)
                logger.info("Efficiently deserialized response")
                return response
            else:
                # Normal JSON parsing
                try:
                    response = json.loads(data.decode('utf-8'))
                    logger.info("Response received")
                    return response
                except json.JSONDecodeError:
                    logger.warning("Received response is not in JSON format")
                    return {"data": data.decode('utf-8', errors='replace'), "_parse_error": True}
                
        except Exception as e:
            logger.error(f"Efficient message send error: {e}")
            
            # Attempt reconnect if connection was lost
            if self.auto_reconnect and "Broken pipe" in str(e):
                if self._try_reconnect():
                    # Retry sending
                    return self.send_efficient_message(message, protocol_name, wait_for_response)
            
            return None