"""
Module providing node discovery functionality in the network

Main features:
- Node discovery using UDP broadcast
- Broadcasting own presence
- Management of discovered nodes
"""

import socket
import json
import threading
import time
import logging
import ipaddress
import netifaces
from datetime import datetime, timedelta

# Logger configuration
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG to output detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WitchDiscovery")


class NodeDiscovery:
    """
    Node discovery class using UDP broadcast
    """
    
    def __init__(self, broadcast_port=8889, node_id=None, service_info=None):
        """
        Initialize node discovery functionality
        
        Args:
            broadcast_port (int): Port number used for broadcasting
            node_id (str): Identifier for this node (auto-generated if omitted)
            service_info (dict): Information about services provided by this node
        """
        self.broadcast_port = broadcast_port
        self.node_id = node_id or f"node-{int(time.time())}"
        self.service_info = service_info or {}
        
        # Dictionary to store discovered nodes {node_id: (info, last_seen)}
        self.discovered_nodes = {}
        
        # UDP socket
        self.sock = None
        self.running = False
        
        # Thread running broadcasts
        self.broadcast_thread = None
        
        # Thread running discovery listener
        self.discovery_thread = None
        
        logger.debug(f"NodeDiscovery initialized with ID: {self.node_id}, port: {broadcast_port}")
    
    def start_discovery(self):
        """
        Start node discovery
        """
        if self.running:
            logger.warning("Node discovery is already running")
            return False
        
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Set socket buffer size larger
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.running = True
            
            # Bind listen socket
            try:
                self.sock.bind(('0.0.0.0', self.broadcast_port))
                logger.info(f"Started UDP listening - port {self.broadcast_port}")
            except OSError as e:
                logger.error(f"Cannot bind to port {self.broadcast_port}: {e}. Disabling discovery reception.")
            
            # Start discovery reception thread
            self.discovery_thread = threading.Thread(target=self._listen_for_broadcasts)
            self.discovery_thread.daemon = True
            self.discovery_thread.start()
            
            # Start broadcast thread
            self.broadcast_thread = threading.Thread(target=self._broadcast_presence)
            self.broadcast_thread.daemon = True
            self.broadcast_thread.start()
            
            logger.info("Started node discovery")
            return True
            
        except Exception as e:
            logger.error(f"Error starting node discovery: {e}")
            if self.sock:
                self.sock.close()
                self.sock = None
            self.running = False
            return False
    
    def stop_discovery(self):
        """
        Stop node discovery
        """
        if not self.running:
            logger.warning("Node discovery is not running")
            return
        
        self.running = False
        
        # Close socket
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        logger.info("Stopped node discovery")
    
    def get_network_broadcast_addresses(self):
        """
        Get broadcast addresses for all network interfaces
        
        Returns:
            list: List of broadcast addresses
        """
        broadcast_addresses = ['255.255.255.255']  # Default broadcast address
        
        try:
            # Get all network interfaces
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                try:
                    # Get address info
                    addrs = netifaces.ifaddresses(interface)
                    
                    # Check for IPv4 addresses
                    if netifaces.AF_INET in addrs:
                        for addr_info in addrs[netifaces.AF_INET]:
                            if 'broadcast' in addr_info:
                                broadcast_addr = addr_info['broadcast']
                                if broadcast_addr and broadcast_addr not in broadcast_addresses:
                                    broadcast_addresses.append(broadcast_addr)
                                    logger.debug(f"Found broadcast address {broadcast_addr} for interface {interface}")
                except Exception as e:
                    logger.debug(f"Error getting broadcast address for interface {interface}: {e}")
        except Exception as e:
            logger.warning(f"Error getting network interfaces: {e}")
        
        # Add common subnet broadcast addresses
        additional_broadcasts = [
            '192.168.255.255',
            '192.168.0.255', 
            '192.168.1.255',
            '10.255.255.255',
            '10.0.0.255',
            '10.0.1.255',
            '172.16.255.255',
            '172.31.255.255'
        ]
        
        for addr in additional_broadcasts:
            if addr not in broadcast_addresses:
                broadcast_addresses.append(addr)
        
        # Add loopback broadcast
        if '127.0.0.255' not in broadcast_addresses:
            broadcast_addresses.append('127.0.0.255')
        
        # Also add localhost for testing
        if '127.0.0.1' not in broadcast_addresses:
            broadcast_addresses.append('127.0.0.1')
        
        logger.debug(f"Using broadcast addresses: {broadcast_addresses}")
        return broadcast_addresses
    
    def broadcast_presence(self):
        """
        Broadcast the existence of this node
        """
        if not self.running:
            logger.warning("Cannot broadcast because node discovery is not running")
            return False
        
        try:
            # Create broadcast message
            message = {
                'type': 'node_discovery',
                'node_id': self.node_id,
                'service_info': self.service_info,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send broadcast to all available interfaces
            broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            data = json.dumps(message).encode('utf-8')
            
            # Get broadcast addresses
            broadcast_addresses = self.get_network_broadcast_addresses()
            
            # Send to all broadcast addresses
            success_count = 0
            for addr in broadcast_addresses:
                try:
                    broadcast_sock.sendto(data, (addr, self.broadcast_port))
                    logger.debug(f"Sent broadcast to {addr}:{self.broadcast_port}")
                    success_count += 1
                except Exception as e:
                    logger.debug(f"Failed to broadcast to {addr}: {e}")
                
            broadcast_sock.close()
            
            logger.info(f"Broadcasted presence: {self.node_id} (sent to {success_count}/{len(broadcast_addresses)} addresses)")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            return False
    
    def _broadcast_presence(self):
        """
        Thread that periodically broadcasts this node's existence
        """
        while self.running:
            self.broadcast_presence()
            time.sleep(5)  # Broadcast every 5 seconds
    
    def _listen_for_broadcasts(self):
        """
        Thread that receives broadcast messages
        """
        if not self.sock:
            logger.error("No listen socket available")
            return
        
        logger.debug("Starting broadcast listener thread")
        while self.running:
            try:
                # Wait for reception (with timeout)
                self.sock.settimeout(1.0)
                data, addr = self.sock.recvfrom(1024)
                logger.debug(f"Received data from {addr}")
                
                # Parse received data
                try:
                    message = json.loads(data.decode('utf-8'))
                    
                    # Ignore broadcasts from self
                    if message.get('node_id') == self.node_id:
                        logger.debug(f"Ignoring self-broadcast from {self.node_id}")
                        continue
                    
                    # In case of node discovery message
                    if message.get('type') == 'node_discovery':
                        node_id = message.get('node_id')
                        service_info = message.get('service_info', {})
                        
                        # Add source IP to service info
                        if service_info and isinstance(service_info, dict):
                            service_info['local_ip'] = addr[0]
                        
                        # Save discovered node information
                        self.discovered_nodes[node_id] = (service_info, datetime.now())
                        
                        logger.info(f"Discovered node: {node_id} from {addr}")
                        logger.debug(f"Node info: {service_info}")
                
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid broadcast message from {addr}")
                    continue
                
            except socket.timeout:
                # Timeout is normal, continue loop
                pass
            except Exception as e:
                if self.running:  # Only output error log if running
                    logger.error(f"Broadcast reception error: {e}")
                break
        
        logger.debug("Broadcast listener thread stopped")
    
    def get_discovered_nodes(self, max_age_minutes=15):
        """
        Get the list of discovered nodes
        
        Args:
            max_age_minutes (int): Remove information older than this time (minutes)
            
        Returns:
            dict: Node information dictionary in {node_id: service_info} format
        """
        current_time = datetime.now()
        max_age = timedelta(minutes=max_age_minutes)
        
        # Remove old entries
        nodes_to_remove = []
        for node_id, (_, last_seen) in self.discovered_nodes.items():
            if current_time - last_seen > max_age:
                nodes_to_remove.append(node_id)
        
        for node_id in nodes_to_remove:
            del self.discovered_nodes[node_id]
            logger.debug(f"Removed old node: {node_id}")
        
        # Return latest node information
        result = {
            node_id: info 
            for node_id, (info, _) in self.discovered_nodes.items()
        }
        
        logger.debug(f"Current discovered nodes: {len(result)}")
        return result


# Provide easy access as module-level functions
_discovery_instance = None


def get_discovery_instance(broadcast_port=8889, node_id=None, service_info=None):
    """
    Get the node discovery instance (singleton pattern)
    
    Returns:
        NodeDiscovery: Node discovery instance
    """
    global _discovery_instance
    
    if _discovery_instance is None:
        _discovery_instance = NodeDiscovery(
            broadcast_port=broadcast_port,
            node_id=node_id,
            service_info=service_info
        )
    elif node_id is not None or service_info is not None:
        # Update existing instance with new information if provided
        if node_id:
            _discovery_instance.node_id = node_id
        if service_info:
            _discovery_instance.service_info = service_info
    
    return _discovery_instance


def discover_nodes(broadcast_port=8889, node_id=None, service_info=None, wait_time=10):
    """
    Discover nodes on the network
    
    Args:
        broadcast_port (int): Port number used for broadcasting
        node_id (str): Identifier for this node
        service_info (dict): Information about services provided by this node
        wait_time (int): Time to wait for discovery (seconds)
    
    Returns:
        dict: Information of discovered nodes
    """
    discovery = get_discovery_instance(broadcast_port, node_id, service_info)
    
    # Start discovery
    discovery.start_discovery()
    
    # Wait for the specified time
    logger.info(f"Waiting {wait_time} seconds for node discovery...")
    time.sleep(wait_time)
    
    # Return discovered nodes
    nodes = discovery.get_discovered_nodes()
    logger.info(f"Discovery complete. Found {len(nodes)} nodes.")
    return nodes


def broadcast_presence(broadcast_port=8889, node_id=None, service_info=None):
    """
    Broadcast the existence of this node
    
    Args:
        broadcast_port (int): Port number used for broadcasting
        node_id (str): Identifier for this node
        service_info (dict): Information about services provided by this node
    
    Returns:
        bool: Whether the broadcast was successful
    """
    discovery = get_discovery_instance(broadcast_port, node_id, service_info)
    # Make sure discovery is started
    if not discovery.running:
        discovery.start_discovery()
    return discovery.broadcast_presence()