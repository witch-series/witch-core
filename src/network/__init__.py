"""
Communication Processing Module for witch-series Project

This module includes the following features:
- Communication establishment using TCP/IP sockets
- Node discovery using broadcast at startup
- Data sending/receiving and protocol-based processing
"""

from .server import Server
from .client import Client
from .discovery import discover_nodes, broadcast_presence

__all__ = [
    'Server',
    'Client',
    'discover_nodes',
    'broadcast_presence'
]