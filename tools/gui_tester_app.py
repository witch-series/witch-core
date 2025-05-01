#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Tester App for witch-core

This module contains the GUI components and application logic for the Witch-Core GUI Tester.
"""

import sys
import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime

# Add the project root directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import GUI functions
from tools.gui_functions import (
    ServerManager, ClientManager, DiscoveryManager, ProtocolManager,
    get_server_registry_info
)


class RedirectText:
    """Redirect print statements to a tkinter widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
    
    def flush(self):
        pass


class WitchCoreGUI:
    def __init__(self, root, server_name="anonymous"):
        self.root = root
        self.root.title("Witch-Core GUI Tester")
        self.root.geometry("1000x800")  # Increased size for better layout
        self.root.minsize(900, 700)     # Increased minimum size
        
        # Initialize managers
        self.server_manager = ServerManager()
        self.client_manager = ClientManager()
        self.discovery_manager = DiscoveryManager()
        self.protocol_manager = ProtocolManager()
        
        # Variables
        self.server_running = False
        self.protocol_name = tk.StringVar(value="example_protocol")
        self.server_host = tk.StringVar(value="0.0.0.0")
        self.server_port = tk.IntVar(value=8888)
        self.server_name = tk.StringVar(value=server_name)
        self.client_host = tk.StringVar(value="127.0.0.1")
        self.client_port = tk.IntVar(value=8888)
        self.discover_enabled = tk.BooleanVar(value=False)
        self.server_id = tk.StringVar(value=f"{server_name}-{int(time.time())}")
        self.server_description = tk.StringVar(value=f"Witch-Core Test Server ({server_name})")
        
        # Node selection variables
        self.discovered_nodes = {}
        self.selected_node = tk.StringVar(value="")
        self.node_display_to_id = {}
        
        # Message data variables
        self.message_data_type = tk.StringVar(value="json_data")
        self.message_file_path = tk.StringVar(value="")
        
        # Auto-discovery variables (auto-discovery enabled by default)
        self.auto_discovery_enabled = tk.BooleanVar(value=True)
        self.auto_discovery_interval = tk.IntVar(value=10)
        self.auto_broadcast_enabled = tk.BooleanVar(value=False)
        self.auto_broadcast_interval = tk.IntVar(value=10)
        
        # Create tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create frames for tabs
        self.server_frame = ttk.Frame(self.notebook)
        self.client_frame = ttk.Frame(self.notebook)
        self.protocol_frame = ttk.Frame(self.notebook)
        self.discovery_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.server_frame, text="Server")
        self.notebook.add(self.client_frame, text="Client")
        self.notebook.add(self.protocol_frame, text="Protocols")
        self.notebook.add(self.discovery_frame, text="Discovery")
        self.notebook.add(self.settings_frame, text="Settings")
        
        # Create frames for console output (increased size)
        self.console_frame = ttk.Frame(root)
        self.console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Set up the tabs and console
        self.setup_server_tab()
        self.setup_client_tab()
        self.setup_protocol_tab()
        self.setup_discovery_tab()
        self.setup_settings_tab()
        self.setup_console()
        
        # Redirect standard output to the console
        self.old_stdout = sys.stdout
        sys.stdout = RedirectText(self.console)
        
        # Start auto-discovery by default
        if self.auto_discovery_enabled.get():
            self.toggle_auto_discovery()

    def setup_server_tab(self):
        """Set up the server tab components"""
        frame = self.server_frame
        
        # Server configuration
        config_frame = ttk.LabelFrame(frame, text="Server Configuration")
        config_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Server Name
        ttk.Label(config_frame, text="Server Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.server_name, width=20).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Host input
        ttk.Label(config_frame, text="Host:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.server_host, width=20).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Port input
        ttk.Label(config_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.server_port, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Generate Server ID button
        gen_id_button = ttk.Button(config_frame, text="Generate Server ID", command=self.generate_server_id)
        gen_id_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Server ID input
        ttk.Label(config_frame, text="Server ID:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.server_id, width=30).grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Description input
        ttk.Label(config_frame, text="Description:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.server_description, width=50).grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Control buttons
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Auto broadcast checkbox
        auto_broadcast_check = ttk.Checkbutton(
            control_frame, 
            text="Auto Broadcast Presence", 
            variable=self.auto_broadcast_enabled,
            command=self.toggle_auto_broadcast
        )
        auto_broadcast_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Server status
        self.server_status = ttk.Label(frame, text="Server Status: Not Running", font=("", 10, "bold"))
        self.server_status.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Registered servers list
        list_button = ttk.Button(frame, text="List Registered Servers", command=self.list_servers)
        list_button.pack(fill=tk.X, expand=False, padx=10, pady=5)
    
    def generate_server_id(self):
        """Generate a new server ID based on server name and timestamp"""
        name = self.server_name.get()
        if not name:
            name = "anonymous"
        self.server_id.set(f"{name}-{int(time.time())}")
        self.server_description.set(f"Witch-Core Test Server ({name})")
        
    def setup_client_tab(self):
        """Set up the client tab components"""
        frame = self.client_frame
        
        # Client configuration
        config_frame = ttk.LabelFrame(frame, text="Client Configuration")
        config_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Node selection dropdown
        ttk.Label(config_frame, text="Select Node:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.node_select_combobox = ttk.Combobox(config_frame, textvariable=self.selected_node, width=50)
        self.node_select_combobox.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        self.node_select_combobox.bind("<<ComboboxSelected>>", self.on_node_selected)
        
        # Host input
        ttk.Label(config_frame, text="Host:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.client_host, width=20).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Port input
        ttk.Label(config_frame, text="Port:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.client_port, width=10).grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Protocol/Data Type selection
        data_type_frame = ttk.LabelFrame(frame, text="Data Type")
        data_type_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Data type dropdown
        ttk.Label(data_type_frame, text="Data Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        data_types = ["text_data", "json_data", "image_data", "file_data"]
        self.data_type_combobox = ttk.Combobox(data_type_frame, textvariable=self.message_data_type, values=data_types, width=15)
        self.data_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.data_type_combobox.bind("<<ComboboxSelected>>", self.on_data_type_selected)
        
        # File selection (for image and file data)
        ttk.Label(data_type_frame, text="File Path:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        file_entry = ttk.Entry(data_type_frame, textvariable=self.message_file_path, width=40)
        file_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        
        browse_button = ttk.Button(data_type_frame, text="Browse...", command=self.browse_file)
        browse_button.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Message data
        message_frame = ttk.LabelFrame(frame, text="Message Data")
        message_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.message_data = scrolledtext.ScrolledText(message_frame, height=10)
        self.message_data.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Set default JSON data
        self.set_default_message_data()
        
        # Control buttons
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        send_button = ttk.Button(control_frame, text="Send Message", command=self.send_message)
        send_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        discover_button = ttk.Button(control_frame, text="Discover Nodes", command=self.discover_nodes)
        discover_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        refresh_dropdown_button = ttk.Button(control_frame, text="Refresh Node List", command=self.refresh_node_dropdown)
        refresh_dropdown_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def browse_file(self):
        """Open file browser to select a file"""
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[
                ("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.message_file_path.set(file_path)
            print(f"Selected file: {file_path}")
    
    def set_default_message_data(self):
        """Set default message data based on selected data type"""
        data_type = self.message_data_type.get()
        
        self.message_data.delete(1.0, tk.END)
        
        if data_type == "text_data":
            self.message_data.insert(tk.END, "Enter plain text message here")
        
        elif data_type == "json_data":
            default_json = {
                "temperature": 22.5,
                "humidity": 45.3,
                "timestamp": datetime.now().isoformat(),
                "device_id": "sensor-001"
            }
            self.message_data.insert(tk.END, json.dumps(default_json, indent=2))
        
        elif data_type in ["image_data", "file_data"]:
            self.message_data.insert(tk.END, "Select a file using the Browse button above.\n\nAdditional JSON metadata can be added here:")
    
    def on_data_type_selected(self, event):
        """Handle data type selection"""
        self.set_default_message_data()
    
    def on_node_selected(self, event):
        """Handle node selection from dropdown"""
        selected = self.selected_node.get()
        if not selected:
            return
        
        # Find the node ID based on selected display string
        node_id = None
        for display_str, id in self.node_display_to_id.items():
            if display_str == selected:
                node_id = id
                break
        
        if not node_id or node_id not in self.discovered_nodes:
            print("Invalid node selection")
            return
        
        # Get node information
        node_info = self.discovered_nodes[node_id]
        
        # Update host and port information for client
        if 'local_ip' in node_info:
            self.client_host.set(node_info['local_ip'])
        elif 'host' in node_info:
            self.client_host.set(node_info['host'])
        
        if 'port' in node_info:
            self.client_port.set(node_info['port'])
        
        # If node has protocols, select the first one
        if 'protocols' in node_info and node_info['protocols']:
            self.protocol_name.set(node_info['protocols'][0])
        
        print(f"Selected node: {node_id}, host: {self.client_host.get()}, port: {self.client_port.get()}")
    
    def refresh_node_dropdown(self):
        """Refresh the node selection dropdown with current discovered nodes"""
        # Clear dropdown
        self.node_select_combobox['values'] = []
        
        # If there are no discovered nodes, try to discover them
        if not self.discovery_manager.discovered_nodes:
            self.discover_nodes()
        
        # Update discovered nodes from discovery manager
        self.discovered_nodes = self.discovery_manager.discovered_nodes
        
        # Format node display strings
        node_strings = []
        self.node_display_to_id = {}
        
        for node_id, info in self.discovered_nodes.items():
            ip = info.get('local_ip', info.get('host', 'unknown'))
            port = info.get('port', '?')
            node_type = info.get('type', 'unknown')
            server_name = info.get('server_name', 'anonymous')
            
            # Create display string
            display_str = f"{server_name}: {node_id} ({ip}:{port}) - {node_type}"
            node_strings.append(display_str)
            
            # Map display string to node ID
            self.node_display_to_id[display_str] = node_id
        
        # Update dropdown
        self.node_select_combobox['values'] = node_strings
        
        print(f"Node dropdown refreshed with {len(node_strings)} nodes")

    def setup_protocol_tab(self):
        """Set up the protocol tab components"""
        frame = self.protocol_frame
        
        # Protocol management
        protocol_list_frame = ttk.LabelFrame(frame, text="Available Protocols")
        protocol_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Protocol list button
        list_protocols_button = ttk.Button(protocol_list_frame, text="List Available Protocols", command=self.list_protocols)
        list_protocols_button.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # Create protocol frame
        create_protocol_frame = ttk.LabelFrame(frame, text="Create New Protocol")
        create_protocol_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Protocol name
        ttk.Label(create_protocol_frame, text="Protocol Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.new_protocol_name = tk.StringVar(value="custom_protocol")
        ttk.Entry(create_protocol_frame, textvariable=self.new_protocol_name, width=30).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Protocol number
        ttk.Label(create_protocol_frame, text="Protocol Number:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.new_protocol_number = tk.StringVar(value="002")
        ttk.Entry(create_protocol_frame, textvariable=self.new_protocol_number, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Protocol data names
        ttk.Label(create_protocol_frame, text="Data Names (comma separated):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.new_protocol_data_names = tk.StringVar(value="field1,field2,message")
        ttk.Entry(create_protocol_frame, textvariable=self.new_protocol_data_names, width=50).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Create button
        create_button = ttk.Button(create_protocol_frame, text="Create Protocol", command=self.create_protocol)
        create_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        
    def setup_discovery_tab(self):
        """Set up the discovery tab components"""
        frame = self.discovery_frame
        
        # Discovery controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        discover_button = ttk.Button(control_frame, text="Discover Nodes", command=self.discover_nodes)
        discover_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Auto discovery checkbox (checked by default)
        auto_discovery_check = ttk.Checkbutton(
            control_frame, 
            text="Auto Discover", 
            variable=self.auto_discovery_enabled,
            command=self.toggle_auto_discovery
        )
        auto_discovery_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        broadcast_button = ttk.Button(control_frame, text="Broadcast Presence", command=self.broadcast_presence)
        broadcast_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Auto discovery status
        interval = self.auto_discovery_interval.get()
        self.discovery_status = ttk.Label(
            control_frame, 
            text=f"Auto: ON ({interval}s)" if self.auto_discovery_enabled.get() else "Auto: OFF"
        )
        self.discovery_status.pack(side=tk.LEFT, padx=20)
        
        # Discovered nodes list
        nodes_frame = ttk.LabelFrame(frame, text="Discovered Nodes")
        nodes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Updated columns to include IP
        self.nodes_tree = ttk.Treeview(nodes_frame, columns=("id", "ip", "port", "type", "protocols"), show="headings")
        self.nodes_tree.heading("id", text="Node ID")
        self.nodes_tree.heading("ip", text="IP Address")
        self.nodes_tree.heading("port", text="Port")
        self.nodes_tree.heading("type", text="Type")
        self.nodes_tree.heading("protocols", text="Protocols")
        
        self.nodes_tree.column("id", width=200)
        self.nodes_tree.column("ip", width=120)
        self.nodes_tree.column("port", width=60)
        self.nodes_tree.column("type", width=100)
        self.nodes_tree.column("protocols", width=300)
        
        self.nodes_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(nodes_frame, orient=tk.VERTICAL, command=self.nodes_tree.yview)
        self.nodes_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_settings_tab(self):
        """Set up the settings tab components"""
        frame = self.settings_frame
        
        # Auto-discovery settings
        discovery_frame = ttk.LabelFrame(frame, text="Auto-Discovery Settings")
        discovery_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        ttk.Label(discovery_frame, text="Discovery Interval (seconds):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        interval_spinner = ttk.Spinbox(
            discovery_frame, 
            from_=1, 
            to=60, 
            increment=1, 
            textvariable=self.auto_discovery_interval,
            width=5
        )
        interval_spinner.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Auto-broadcast settings
        broadcast_frame = ttk.LabelFrame(frame, text="Auto-Broadcast Settings")
        broadcast_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        ttk.Label(broadcast_frame, text="Broadcast Interval (seconds):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        broadcast_spinner = ttk.Spinbox(
            broadcast_frame, 
            from_=1, 
            to=60, 
            increment=1, 
            textvariable=self.auto_broadcast_interval,
            width=5
        )
        broadcast_spinner.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Auto-discovery apply button
        apply_frame = ttk.Frame(frame)
        apply_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        apply_button = ttk.Button(apply_frame, text="Apply Settings", command=self.apply_settings)
        apply_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Help text
        help_frame = ttk.LabelFrame(frame, text="Help")
        help_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_text = scrolledtext.ScrolledText(help_frame, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        help_text.insert(tk.END, """
Auto-Discovery: When enabled, automatically discovers nodes on the network at the specified interval.

Auto-Broadcast: When enabled, automatically broadcasts your server's presence at the specified interval.

Tips:
- Auto-Discovery is useful for continuously monitoring the network for new nodes
- Auto-Broadcast helps ensure your server is visible to other nodes
- Lower intervals provide more real-time updates but increase network traffic
- For most use cases, 5-10 second intervals are sufficient
        """)
        help_text.config(state=tk.DISABLED)
    
    def apply_settings(self):
        """Apply settings changes"""
        # If auto-discovery is running, restart it with new interval
        if self.auto_discovery_enabled.get():
            self.discovery_manager.stop_auto_discovery()
            self.discovery_manager.start_auto_discovery(
                interval=self.auto_discovery_interval.get(),
                callback=self.on_nodes_discovered
            )
            self.discovery_status.config(text=f"Auto: ON ({self.auto_discovery_interval.get()}s)")
        
        # If auto-broadcast is running, restart it with new interval
        if self.auto_broadcast_enabled.get() and self.server_manager.server_running:
            self.discovery_manager.stop_auto_broadcast()
            self.discovery_manager.start_auto_broadcast(
                interval=self.auto_broadcast_interval.get(),
                server_id=self.server_id.get(),
                port=self.server_port.get(),
                server_name=self.server_name.get()
            )
        
        print("Settings applied")
        
    def setup_console(self):
        """Set up the console output area"""
        console_label = ttk.Label(self.console_frame, text="Console Output:")
        console_label.pack(anchor=tk.W)
        
        # Create console text widget with dark background, light text, and monospace font
        # Increased height for more visibility
        self.console = scrolledtext.ScrolledText(
            self.console_frame, 
            height=15,  # Increased height
            bg="#000000", 
            fg="#FFFFFF",
            font=("Courier New", 10)  # Monospace font good for distinguishing l and 1
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.config(state=tk.DISABLED)
        
        # Clear console button
        clear_button = ttk.Button(self.console_frame, text="Clear Console", command=self.clear_console)
        clear_button.pack(anchor=tk.E, padx=5, pady=5)
    
    def clear_console(self):
        """Clear the console output"""
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)
        print("Console cleared")
    
    def toggle_auto_discovery(self):
        """Toggle automatic node discovery"""
        if self.auto_discovery_enabled.get():
            success = self.discovery_manager.start_auto_discovery(
                interval=self.auto_discovery_interval.get(),
                callback=self.on_nodes_discovered
            )
            if success:
                self.discovery_status.config(text=f"Auto: ON ({self.auto_discovery_interval.get()}s)")
        else:
            success = self.discovery_manager.stop_auto_discovery()
            if success:
                self.discovery_status.config(text="Auto: OFF")
    
    def on_nodes_discovered(self, nodes):
        """Callback when nodes are discovered"""
        # Update the discovered nodes
        self.discovered_nodes = nodes
        
        # Update the nodes treeview
        self.update_nodes_treeview(nodes)
        
        # Update the node dropdown
        self.refresh_node_dropdown()
    
    def update_nodes_treeview(self, nodes):
        """Update the nodes treeview with discovered nodes"""
        # Clear the treeview
        for item in self.nodes_tree.get_children():
            self.nodes_tree.delete(item)
        
        if not nodes:
            return
        
        # Add nodes to the treeview with IP address
        for node_id, info in nodes.items():
            node_type = info.get('type', 'unknown')
            port = info.get('port', 'N/A')
            ip_address = info.get('local_ip', info.get('host', 'unknown'))
            protocols = ', '.join(info.get('protocols', []))
            server_name = info.get('server_name', 'anonymous')
            
            # Display server name in the node ID column if available
            display_id = f"{server_name}: {node_id}" if server_name != 'anonymous' else node_id
            
            self.nodes_tree.insert('', tk.END, values=(display_id, ip_address, port, node_type, protocols))
    
    def toggle_auto_broadcast(self):
        """Toggle automatic presence broadcast"""
        if not self.server_manager.server_running:
            if self.auto_broadcast_enabled.get():
                self.auto_broadcast_enabled.set(False)
                messagebox.showinfo("Info", "Start the server first before enabling auto-broadcast")
                return
        
        if self.auto_broadcast_enabled.get():
            self.discovery_manager.start_auto_broadcast(
                interval=self.auto_broadcast_interval.get(),
                server_id=self.server_id.get(),
                port=self.server_port.get(),
                server_name=self.server_name.get()
            )
        else:
            self.discovery_manager.stop_auto_broadcast()
    
    def start_server(self):
        """Start the server with the current configuration"""
        host = self.server_host.get()
        port = self.server_port.get()
        server_id = self.server_id.get()
        description = self.server_description.get()
        server_name = self.server_name.get() or "anonymous"  # Use default if empty
        
        success = self.server_manager.start_server(
            host=host,
            port=port,
            server_id=server_id,
            description=description,
            server_name=server_name
        )
        
        if success:
            self.server_running = True
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.server_status.config(text=f"Server Status: Running '{server_name}' on {host}:{port}", foreground="green")
            
            # Start auto-broadcast if enabled
            if self.auto_broadcast_enabled.get():
                self.discovery_manager.start_auto_broadcast(
                    interval=self.auto_broadcast_interval.get(),
                    server_id=server_id,
                    port=port,
                    server_name=server_name
                )
        else:
            messagebox.showerror("Error", "Failed to start server")
    
    def stop_server(self):
        """Stop the running server"""
        success = self.server_manager.stop_server()
        
        if success:
            self.server_running = False
            
            # Update UI
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.server_status.config(text="Server Status: Not Running", foreground="black")
            
            # Stop auto-broadcast if running
            if self.auto_broadcast_enabled.get():
                self.auto_broadcast_enabled.set(False)
                self.discovery_manager.stop_auto_broadcast()
    
    def send_message(self):
        """Send a message from the client to the server"""
        host = self.client_host.get()
        port = self.client_port.get()
        data_type = self.message_data_type.get()
        file_path = self.message_file_path.get()
        
        try:
            # Handle different data types
            if data_type in ["image_data", "file_data"] and file_path:
                # Send file data
                response = self.client_manager.send_file(
                    host=host,
                    port=port,
                    protocol_name=data_type,
                    file_path=file_path
                )
            else:
                # Get message data
                if data_type == "text_data":
                    # For text data, use the raw text
                    data = self.message_data.get(1.0, tk.END)
                else:
                    # For JSON data, parse the text as JSON
                    try:
                        data = json.loads(self.message_data.get(1.0, tk.END))
                    except json.JSONDecodeError as e:
                        print(f"JSON error: {e}")
                        messagebox.showerror("JSON Error", f"Invalid JSON: {e}")
                        return
                
                # Send message data
                response = self.client_manager.send_message(
                    host=host,
                    port=port,
                    protocol_name=data_type,
                    data=data
                )
            
            if response:
                messagebox.showinfo("Response", f"Server response received:\n\n{json.dumps(response, indent=2)}")
        
        except Exception as e:
            print(f"Error sending message: {e}")
            messagebox.showerror("Error", f"Error sending message: {e}")
    
    def discover_nodes(self):
        """Discover nodes on the network"""
        nodes = self.discovery_manager.discover_nodes()
        self.discovered_nodes = nodes
        self.update_nodes_treeview(nodes)
        self.refresh_node_dropdown()
    
    def broadcast_presence(self):
        """Broadcast presence on the network"""
        success = self.discovery_manager.broadcast_presence(
            server_id=self.server_id.get(),
            port=self.server_port.get(),
            server_name=self.server_name.get()
        )
        
        if success:
            messagebox.showinfo("Success", "Broadcast sent successfully")
    
    def list_servers(self):
        """List registered servers"""
        servers_info = get_server_registry_info()
        if not servers_info:
            messagebox.showinfo("Info", "No registered servers found")
    
    def list_protocols(self):
        """List available protocols"""
        protocols_info = self.protocol_manager.list_protocols()
        if not protocols_info:
            messagebox.showinfo("Info", "No available protocols found")
    
    def create_protocol(self):
        """Create a new protocol"""
        name = self.new_protocol_name.get()
        number = self.new_protocol_number.get()
        data_names_str = self.new_protocol_data_names.get()
        data_names = [name.strip() for name in data_names_str.split(",") if name.strip()]
        
        if not name or not number or not data_names:
            messagebox.showerror("Error", "Protocol name, number, and at least one data name are required")
            return
        
        success = self.protocol_manager.create_protocol(
            name=name,
            number=number,
            data_names=data_names
        )
        
        if success:
            messagebox.showinfo("Success", f"Protocol '{name}' created successfully!")
    
    def on_closing(self):
        """Handle the window closing event"""
        if self.server_manager.server_running:
            self.server_manager.stop_server()
        
        # Stop background threads
        self.discovery_manager.stop_auto_discovery()
        self.discovery_manager.stop_auto_broadcast()
        
        # Restore stdout
        sys.stdout = self.old_stdout
        self.root.destroy()