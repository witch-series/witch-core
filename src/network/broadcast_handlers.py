#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Message handlers for broadcast communication

This module provides handler functions for different types of broadcast messages:
- Node discovery message handling
- Ledger synchronization message handling
"""

import logging
from datetime import datetime
from typing import Dict, Any, Tuple

from ..protocol.ledger import register_node, merge_ledgers

# Logger configuration
logger = logging.getLogger("WitchBroadcast")

def _handle_discovery_message(self, message: Dict[str, Any], addr: Tuple[str, int]):
    """
    Process node discovery message
    
    Args:
        message: Received message data
        addr: Sender's address and port
    """
    node_id = message.get('node_id')
    node_hash = message.get('hash')
    node_ip = message.get('ip', addr[0])  # Use sender's IP if not specified
    node_port = message.get('port')
    node_name = message.get('name')
    node_protocols = message.get('protocols', [])
    
    # Verify hash value
    if node_hash != self.src_hash:
        logger.warning(f"Ignoring message from incompatible node: {node_id} ({node_hash[:8]})")
        return
    
    # Cache node information
    self.discovered_nodes[node_id] = {
        'id': node_id,
        'ip': node_ip,
        'port': node_port,
        'hash': node_hash,
        'name': node_name,
        'protocols': node_protocols,
        'last_seen': datetime.now().isoformat()
    }
    
    # Register node in ledger
    register_node(
        ip=node_ip,
        port=node_port,
        protocols=node_protocols,
        name=node_name,
        node_id=node_id
    )
    
    logger.info(f"Discovered new node: {node_name or node_id} ({node_ip}:{node_port})")
    
    # Call callback function
    if self.on_node_discovered:
        try:
            self.on_node_discovered(self.discovered_nodes[node_id])
        except Exception as e:
            logger.error(f"Error in node discovery callback: {e}")

def _handle_ledger_sync(self, message: Dict[str, Any], addr: Tuple[str, int]):
    """
    Process ledger synchronization message
    
    Args:
        message: Received message data
        addr: Sender's address and port
    """
    node_hash = message.get('hash')
    
    # Verify hash value
    if node_hash != self.src_hash:
        logger.warning(f"Ignoring ledger sync from incompatible node: {addr}")
        return
    
    # Get ledger data
    ledger_data = message.get('ledger')
    if not ledger_data:
        logger.warning(f"Received message without ledger data: {addr}")
        return
    
    # Merge ledger
    try:
        merged_ledger = merge_ledgers(ledger_data)
        logger.info(f"Merged remote ledger: {len(merged_ledger.get('nodes', []))} nodes, " +
                     f"{len(merged_ledger.get('protocols', []))} protocols")
        
        # Call callback function
        if self.on_ledger_received:
            try:
                self.on_ledger_received(merged_ledger)
            except Exception as e:
                logger.error(f"Error in ledger received callback: {e}")
                
    except Exception as e:
        logger.error(f"Error merging ledger: {e}")