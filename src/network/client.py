#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client module for network communication with Witch Core servers.
"""

import socket
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from ..protocol.protocol_core import Protocol
from ..protocol.protocol_data import ProtocolData
from . import client_message
from . import client_media

# Logger configuration
logger = logging.getLogger("WitchClient")

class Client:
    """
    Client class for communication with Witch Core servers
    """
    
    def __init__(self, server_ip: str = "127.0.0.1", server_port: int = 8000, 
                 timeout: float = 5.0, max_retries: int = 3):
        """
        Initialize a client
        
        Args:
            server_ip (str): Server IP address
            server_port (int): Server port
            timeout (float): Connection timeout in seconds
            max_retries (int): Maximum number of connection retry attempts
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_address = (server_ip, server_port)
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'WitchCore-Client'
        })
        self.base_url = f"http://{server_ip}:{server_port}"
        
        # Message client component
        self.message = client_message.MessageClient(self)
        
        # Media client component
        self.media = client_media.MediaClient(self)
    
    def send_request(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> Tuple[bool, Dict[str, Any]]:
        """
        Send a request to the server
        
        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any]): Data to send
            method (str): HTTP method (POST, GET, etc.)
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and response data
        """
        url = f"{self.base_url}/{endpoint}"
        response_data = {"success": False, "message": "Unknown error"}
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, params=data, timeout=self.timeout)
                else:  # Default to POST
                    response = self.session.post(url, json=data, timeout=self.timeout)
                
                response.raise_for_status()
                return True, response.json()
                
            except Timeout:
                logger.warning(f"Request timed out (attempt {attempt+1}/{self.max_retries})")
                response_data = {"success": False, "message": "Request timed out"}
                
            except ConnectionError:
                logger.warning(f"Connection error (attempt {attempt+1}/{self.max_retries})")
                response_data = {"success": False, "message": "Connection error"}
                
            except RequestException as e:
                logger.warning(f"Request failed: {e} (attempt {attempt+1}/{self.max_retries})")
                response_data = {"success": False, "message": f"Request failed: {str(e)}"}
                
            # Wait before retrying
            if attempt < self.max_retries - 1:
                time.sleep(min(2 ** attempt, 10))  # Exponential backoff
                
        return False, response_data
