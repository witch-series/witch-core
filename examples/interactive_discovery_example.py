#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example showing how to use the interactive "Continue to iterate?" 
functionality in the BroadcastDiscovery system
"""

import sys
import time
import logging
from pathlib import Path

# Add parent directory to path so we can import our module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.network.broadcast_discovery import BroadcastDiscovery

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def iteration_callback(prompt_message):
    """
    Callback function for the BroadcastDiscovery interactive mode.
    This is called whenever the auto-discovery system is about to
    start another iteration.
    
    Args:
        prompt_message (str): The message to prompt the user with
            
    Returns:
        bool: True if iterations should continue, False to stop
    """
    print(f"\n{prompt_message} (y/n): ", end="")
    response = input().strip().lower()
    
    return response in ['y', 'yes', 'true']

def main():
    """Main example function"""
    print("Starting interactive broadcast discovery example")
    
    # Create a discovery instance with interactive mode enabled
    discovery = BroadcastDiscovery(
        broadcast_port=45678,
        node_name="InteractiveExample",
        auto_discovery_interval=10,  # Short interval for demonstration purposes
        interactive=True,  # Enable interactive mode
        iteration_callback=iteration_callback  # Use our callback function
    )
    
    # Start discovery
    if discovery.start(listen=True):
        print("Discovery started. Will ask to continue every 10 seconds.")
        
        # For the example, initiate the first discovery broadcast
        discovery.send_discovery_broadcast('127.0.0.1', 8000)
        
        try:
            # Keep the main thread running until Ctrl+C
            while discovery.running:
                time.sleep(1)
                
                # Periodically show discovered nodes
                if discovery.discovered_nodes:
                    print(f"\nDiscovered {len(discovery.discovered_nodes)} nodes:")
                    for node_id, info in discovery.discovered_nodes.items():
                        print(f"  - {info.get('node_name', 'Unknown')} ({info.get('source_ip', 'Unknown')})")
        
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        print("Failed to start discovery")

if __name__ == "__main__":
    main()