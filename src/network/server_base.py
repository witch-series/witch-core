#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module providing base class for server functionality

This module includes the following features:
- Basic TCP server functionality
- Basic client connection management
- Common server interface definition
"""

import socket
import threading
import logging
from typing import Dict, List, Any, Optional, Callable

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ServerBase")


class ServerBase:
    """
    Abstract base class providing basic server functionality
    """
    
    def __init__(self, host="0.0.0.0", port=0):
        """
        ServerBase initialization
        
        Args:
            host (str): Hostname or IP address for the server to bind to
            port (int): Port number for the server to listen on
        """
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
    
    def start(self):
        """
        Start the server
        
        Returns:
            bool: Whether the startup was successful
        """
        raise NotImplementedError("This method must be implemented by subclasses")
    
    def stop(self):
        """
        Stop the server
        """
        raise NotImplementedError("This method must be implemented by subclasses")
    
    def is_running(self):
        """
        Check if the server is running
        
        Returns:
            bool: Whether the server is running
        """
        return self.running