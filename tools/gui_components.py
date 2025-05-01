#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Components

This module contains the GUI components for the Witch-Core GUI tester.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import json
import random
import string
from datetime import datetime

# Add the project root directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


class ConsoleOutput(scrolledtext.ScrolledText):
    """
    Console output widget with redirected stdout/stderr
    """
    
    def __init__(self, parent, **kwargs):
        # Set a larger height for the console output (increased from default)
        if 'height' not in kwargs:
            kwargs['height'] = 20  # Increased from typical default of 10-15
        
        super().__init__(parent, **kwargs)
        self.configure(wrap=tk.WORD, font=('Consolas', 10))
        
        # Make the text widget read-only
        self.configure(state='disabled')
        
        # Redirect stdout and stderr
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def write(self, text):
        """Write text to the console"""
        self.configure(state='normal')
        self.insert(tk.END, text)
        self.see(tk.END)
        self.configure(state='disabled')
        
        # Also write to the original stdout
        self._stdout.write(text)
    
    def flush(self):
        """Flush the console"""
        self._stdout.flush()
        self._stderr.flush()
    
    def reset(self):
        """Clear the console"""
        self.configure(state='normal')
        self.delete('1.0', tk.END)
        self.configure(state='disabled')
    
    def restore(self):
        """Restore original stdout and stderr"""
        sys.stdout = self._stdout
        sys.stderr = self._stderr


class ServerFrame(ttk.LabelFrame):
    """
    Server configuration and control frame
    """
    
    def __init__(self, parent, server_manager, discovery_manager, **kwargs):
        super().__init__(parent, text="Server", **kwargs)
        self.server_manager = server_manager
        self.discovery_manager = discovery_manager
        
        # Server status
        self.server_running = False
        
        # Initialize the UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the server UI"""
        # Create a frame for server configuration
        config_frame = ttk.Frame(self)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Host
        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, sticky=tk.W)
        self.host_var = tk.StringVar(value="0.0.0.0")
        ttk.Entry(config_frame, textvariable=self.host_var).grid(row=0, column=1, sticky=tk.EW)
        
        # Port
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, padx=(10, 0), sticky=tk.W)
        self.port_var = tk.StringVar(value="9090")
        ttk.Entry(config_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, sticky=tk.EW)
        
        # Server ID
        ttk.Label(config_frame, text="Server ID:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.server_id_var = tk.StringVar(value=self._generate_server_id())
        ttk.Entry(config_frame, textvariable=self.server_id_var).grid(row=1, column=1, sticky=tk.EW, pady=(5, 0))
        
        # Generate button
        ttk.Button(
            config_frame, 
            text="Generate", 
            command=self._generate_new_id
        ).grid(row=1, column=2, padx=(10, 0), sticky=tk.W, pady=(5, 0))
        
        # Server Name
        ttk.Label(config_frame, text="Server Name:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.server_name_var = tk.StringVar(value="Witch Server")
        ttk.Entry(config_frame, textvariable=self.server_name_var).grid(row=2, column=1, columnspan=3, sticky=tk.EW, pady=(5, 0))
        
        # Description
        ttk.Label(config_frame, text="Description:").grid(row=3, column=0, sticky=tk.NW, pady=(5, 0))
        self.description_var = tk.StringVar(value="Witch-Core test server")
        ttk.Entry(config_frame, textvariable=self.description_var).grid(row=3, column=1, columnspan=3, sticky=tk.EW, pady=(5, 0))
        
        # Configure the grid
        config_frame.columnconfigure(1, weight=1)
        
        # Create a frame for server controls
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start button
        self.start_button = ttk.Button(
            controls_frame, 
            text="Start Server", 
            command=self._start_server
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_button = ttk.Button(
            controls_frame, 
            text="Stop Server", 
            command=self._stop_server,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Broadcast checkbox
        self.broadcast_var = tk.BooleanVar(value=True)  # Changed default to ON
        self.broadcast_checkbutton = ttk.Checkbutton(
            controls_frame,
            text="Broadcast Presence",
            variable=self.broadcast_var
        )
        self.broadcast_checkbutton.pack(side=tk.RIGHT, padx=5)
    
    def _generate_server_id(self):
        """Generate a random server ID"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    def _generate_new_id(self):
        """Generate a new server ID and update the UI"""
        self.server_id_var.set(self._generate_server_id())
    
    def _start_server(self):
        """Start the server"""
        # Get server configuration
        host = self.host_var.get()
        port = int(self.port_var.get())
        server_id = self.server_id_var.get()
        description = self.description_var.get()
        server_name = self.server_name_var.get()
        
        # Start the server
        self.server_manager.start_server(
            host, port, server_id, description, server_name,
            on_success=self._on_server_started,
            on_error=self._on_server_error
        )
    
    def _stop_server(self):
        """Stop the server"""
        # Stop the server
        self.server_manager.stop_server(
            on_success=self._on_server_stopped
        )
        
        # Stop auto broadcast if running
        self.discovery_manager.stop_auto_broadcast()
    
    def _on_server_started(self):
        """Called when the server is started"""
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.server_running = True
        
        # Start auto-broadcast if enabled
        if self.broadcast_var.get():
            host = self.host_var.get()
            port = int(self.port_var.get())
            server_id = self.server_id_var.get()
            server_name = self.server_name_var.get()
            
            self.discovery_manager.start_auto_broadcast(
                interval=5,  # Broadcast every 5 seconds
                server_id=server_id,
                port=port,
                server_name=server_name
            )
    
    def _on_server_stopped(self):
        """Called when the server is stopped"""
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.server_running = False
    
    def _on_server_error(self, error_message):
        """Called when there's an error starting the server"""
        # Show error message
        messagebox.showerror("Server Error", error_message)


class ClientFrame(ttk.LabelFrame):
    """
    Client configuration and control frame
    """
    
    def __init__(self, parent, client_manager, discovery_manager, **kwargs):
        super().__init__(parent, text="Client", **kwargs)
        self.client_manager = client_manager
        self.discovery_manager = discovery_manager
        
        # Initialize the UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the client UI"""
        # Create a frame for client configuration
        config_frame = ttk.Frame(self)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Host
        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, sticky=tk.W)
        self.host_var = tk.StringVar(value="localhost")
        self.host_entry = ttk.Entry(config_frame, textvariable=self.host_var)
        self.host_entry.grid(row=0, column=1, sticky=tk.EW)
        
        # Port
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, padx=(10, 0), sticky=tk.W)
        self.port_var = tk.StringVar(value="9090")
        self.port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=0, column=3, sticky=tk.EW)
        
        # Server Node
        ttk.Label(config_frame, text="Server:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.server_nodes = {}  # Dictionary to store discovered nodes
        self.server_var = tk.StringVar()
        self.server_dropdown = ttk.Combobox(
            config_frame, 
            textvariable=self.server_var,
            state="readonly"
        )
        self.server_dropdown.grid(row=1, column=1, columnspan=3, sticky=tk.EW, pady=(5, 0))
        self.server_dropdown.bind("<<ComboboxSelected>>", self._on_server_selected)
        
        # Configure the grid
        config_frame.columnconfigure(1, weight=1)
        
        # Create a frame for discovery controls
        discovery_frame = ttk.Frame(self)
        discovery_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Discovery button
        ttk.Button(
            discovery_frame, 
            text="Discover Nodes", 
            command=self._discover_nodes
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-discovery checkbox
        self.auto_discovery_var = tk.BooleanVar(value=True)  # Changed default to ON
        ttk.Checkbutton(
            discovery_frame,
            text="Auto Discover",
            variable=self.auto_discovery_var,
            command=self._toggle_auto_discovery
        ).pack(side=tk.RIGHT, padx=5)
        
        # Create a message frame
        message_frame = ttk.LabelFrame(self, text="Message")
        message_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        # Message type selection
        ttk.Label(message_frame, text="Message Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.message_type_var = tk.StringVar(value="protocol")
        message_types = [("Protocol", "protocol"), ("Image", "image")]
        
        type_frame = ttk.Frame(message_frame)
        type_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        for i, (text, value) in enumerate(message_types):
            ttk.Radiobutton(
                type_frame,
                text=text,
                variable=self.message_type_var,
                value=value,
                command=self._toggle_message_type
            ).pack(side=tk.LEFT, padx=(0 if i == 0 else 10))
        
        # Protocol selection (initially visible)
        self.protocol_frame = ttk.Frame(message_frame)
        self.protocol_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(self.protocol_frame, text="Protocol:").grid(row=0, column=0, sticky=tk.W)
        self.protocol_var = tk.StringVar()
        self.protocol_dropdown = ttk.Combobox(self.protocol_frame, textvariable=self.protocol_var)
        self.protocol_dropdown.grid(row=0, column=1, sticky=tk.EW)
        
        # Add some default protocols
        self.protocol_dropdown['values'] = ('echo', 'timestamp', 'ping')
        self.protocol_var.set('echo')
        
        # Data type selection (new feature)
        ttk.Label(self.protocol_frame, text="Data Type:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.data_type_var = tk.StringVar(value="text")
        self.data_type_dropdown = ttk.Combobox(
            self.protocol_frame, 
            textvariable=self.data_type_var,
            state="readonly",
            values=("text", "number", "json", "image", "file")
        )
        self.data_type_dropdown.grid(row=1, column=1, sticky=tk.EW, pady=(5, 0))
        self.data_type_dropdown.bind("<<ComboboxSelected>>", self._on_data_type_selected)
        
        # Text data (initially visible)
        self.text_data_frame = ttk.Frame(self.protocol_frame)
        self.text_data_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        ttk.Label(self.text_data_frame, text="Data:").pack(side=tk.LEFT, padx=(0, 5))
        self.message_data_var = tk.StringVar(value="Hello, Witch!")
        ttk.Entry(self.text_data_frame, textvariable=self.message_data_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Number data (initially hidden)
        self.number_data_frame = ttk.Frame(self.protocol_frame)
        
        ttk.Label(self.number_data_frame, text="Number:").pack(side=tk.LEFT, padx=(0, 5))
        self.number_data_var = tk.DoubleVar(value=0)
        ttk.Spinbox(
            self.number_data_frame, 
            textvariable=self.number_data_var,
            from_=-1000, 
            to=1000, 
            increment=1
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # JSON data (initially hidden)
        self.json_data_frame = ttk.Frame(self.protocol_frame)
        
        ttk.Label(self.json_data_frame, text="JSON:").pack(side=tk.TOP, anchor=tk.W)
        self.json_data_text = scrolledtext.ScrolledText(
            self.json_data_frame, 
            height=4, 
            width=40
        )
        self.json_data_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.json_data_text.insert(tk.END, '{"key": "value"}')
        
        # Image data (initially hidden)
        self.image_data_frame = ttk.Frame(self.protocol_frame)
        
        ttk.Label(self.image_data_frame, text="Image Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.image_path_var = tk.StringVar()
        ttk.Entry(self.image_data_frame, textvariable=self.image_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            self.image_data_frame, 
            text="Browse", 
            command=self._browse_image
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # File data (initially hidden)
        self.file_data_frame = ttk.Frame(self.protocol_frame)
        
        ttk.Label(self.file_data_frame, text="File Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_path_var = tk.StringVar()
        ttk.Entry(self.file_data_frame, textvariable=self.file_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            self.file_data_frame, 
            text="Browse", 
            command=self._browse_file
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Image selection (initially hidden)
        self.image_frame = ttk.Frame(message_frame)
        self.image_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        self.image_frame.grid_remove()  # Hide initially
        
        ttk.Label(self.image_frame, text="Image File:").grid(row=0, column=0, sticky=tk.W)
        self.image_file_var = tk.StringVar()
        ttk.Entry(self.image_frame, textvariable=self.image_file_var).grid(row=0, column=1, sticky=tk.EW, padx=(5, 5))
        ttk.Button(
            self.image_frame, 
            text="Browse", 
            command=self._browse_image_file
        ).grid(row=0, column=2)
        
        # Configure the grid
        message_frame.columnconfigure(1, weight=1)
        self.protocol_frame.columnconfigure(1, weight=1)
        
        # Send button
        send_frame = ttk.Frame(self)
        send_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            send_frame, 
            text="Send Message", 
            command=self._send_message
        ).pack(side=tk.RIGHT)
        
        # Start auto-discovery by default
        if self.auto_discovery_var.get():
            self._start_auto_discovery()
    
    def _toggle_message_type(self):
        """Toggle between protocol and image message types"""
        message_type = self.message_type_var.get()
        
        if message_type == "protocol":
            self.protocol_frame.grid()
            self.image_frame.grid_remove()
        elif message_type == "image":
            self.protocol_frame.grid_remove()
            self.image_frame.grid()
    
    def _on_data_type_selected(self, event=None):
        """Handle data type selection"""
        data_type = self.data_type_var.get()
        
        # Hide all data frames
        self.text_data_frame.grid_remove()
        self.number_data_frame.grid_remove()
        self.json_data_frame.grid_remove()
        self.image_data_frame.grid_remove()
        self.file_data_frame.grid_remove()
        
        # Show the selected data frame
        if data_type == "text":
            self.text_data_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
        elif data_type == "number":
            self.number_data_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
        elif data_type == "json":
            self.json_data_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
        elif data_type == "image":
            self.image_data_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
        elif data_type == "file":
            self.file_data_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
    
    def _browse_image(self):
        """Browse for an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_path_var.set(file_path)
    
    def _browse_file(self):
        """Browse for any file"""
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def _browse_image_file(self):
        """Browse for an image file for direct image transfer"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_file_var.set(file_path)
    
    def _discover_nodes(self):
        """Discover nodes on the network"""
        self.discovery_manager.discover_nodes(
            on_success=self._update_server_nodes
        )
    
    def _toggle_auto_discovery(self):
        """Toggle automatic node discovery"""
        if self.auto_discovery_var.get():
            self._start_auto_discovery()
        else:
            self.discovery_manager.stop_auto_discovery()
    
    def _start_auto_discovery(self):
        """Start automatic node discovery"""
        self.discovery_manager.start_auto_discovery(
            interval=10,  # Discover every 10 seconds
            update_callback=self._update_server_nodes
        )
    
    def _update_server_nodes(self, nodes):
        """Update the server nodes dropdown"""
        self.server_nodes = nodes
        
        # Update the dropdown
        node_names = []
        for node_id, info in nodes.items():
            server_name = info.get('server_name', 'anonymous')
            ip = info.get('local_ip', info.get('host', 'unknown'))
            port = info.get('port', '?')
            node_names.append(f"{server_name} ({ip}:{port})")
        
        # Update the dropdown values
        self.server_dropdown['values'] = tuple(node_names)
        
        # Select the first node if available and no node is selected
        if node_names and not self.server_var.get():
            self.server_dropdown.current(0)
            self._on_server_selected()  # Update host/port fields
    
    def _on_server_selected(self, event=None):
        """Handle server selection"""
        selected = self.server_var.get()
        if not selected:
            return
        
        # Extract the node details
        try:
            # Parse the selected node
            # Format: "server_name (ip:port)"
            import re
            match = re.match(r"(.*) \((.+):(\d+)\)$", selected)
            if not match:
                return
                
            server_name, ip, port = match.groups()
            
            # Update the host and port fields
            self.host_var.set(ip)
            self.port_var.set(port)
            
        except Exception as e:
            print(f"Error parsing server selection: {e}")
    
    def _send_message(self):
        """Send a message to the server"""
        # Get client configuration
        host = self.host_var.get()
        port = int(self.port_var.get())
        
        # Check message type
        message_type = self.message_type_var.get()
        
        if message_type == "protocol":
            # Get protocol and data
            protocol = self.protocol_var.get()
            
            # Get data based on type
            data_type = self.data_type_var.get()
            data = {}
            
            if data_type == "text":
                data = {"message": self.message_data_var.get()}
            elif data_type == "number":
                data = {"value": self.number_data_var.get()}
            elif data_type == "json":
                try:
                    json_text = self.json_data_text.get("1.0", tk.END).strip()
                    data = json.loads(json_text)
                except json.JSONDecodeError as e:
                    messagebox.showerror("JSON Error", f"Invalid JSON: {e}")
                    return
            elif data_type == "image":
                image_path = self.image_path_var.get()
                if not os.path.isfile(image_path):
                    messagebox.showerror("File Error", "Invalid image file path")
                    return
                data = {"image_path": image_path}
            elif data_type == "file":
                file_path = self.file_path_var.get()
                if not os.path.isfile(file_path):
                    messagebox.showerror("File Error", "Invalid file path")
                    return
                data = {"file_path": file_path}
            
            # Send the message
            self.client_manager.send_message(
                host, port, protocol, data,
                discover=False,  # We're connecting directly
                on_success=self._on_message_sent,
                on_error=self._on_message_error
            )
            
        elif message_type == "image":
            # Get the image file
            image_file = self.image_file_var.get()
            
            if not image_file or not os.path.isfile(image_file):
                messagebox.showerror("Image Error", "Please select a valid image file")
                return
            
            # Send the image
            self.client_manager.send_image(
                host, port, image_file,
                on_success=self._on_message_sent,
                on_error=self._on_message_error
            )
    
    def _on_message_sent(self, response):
        """Called when a message is successfully sent"""
        # Show success message
        messagebox.showinfo("Message Sent", f"Message sent successfully\nResponse: {response}")
    
    def _on_message_error(self, error_message):
        """Called when there's an error sending a message"""
        # Show error message
        messagebox.showerror("Message Error", error_message)


class ProtocolFrame(ttk.LabelFrame):
    """
    Protocol management frame
    """
    
    def __init__(self, parent, protocol_manager, **kwargs):
        super().__init__(parent, text="Protocol Management", **kwargs)
        self.protocol_manager = protocol_manager
        
        # Initialize the UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the protocol UI"""
        # Protocol list button
        ttk.Button(
            self, 
            text="List Protocols", 
            command=self._list_protocols
        ).pack(padx=5, pady=5, anchor=tk.W)
        
        # Create protocol frame
        create_frame = ttk.LabelFrame(self, text="Create Protocol")
        create_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Protocol name
        ttk.Label(create_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar(value="my_protocol")
        ttk.Entry(create_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Protocol number
        ttk.Label(create_frame, text="Number:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.number_var = tk.StringVar(value="100")
        ttk.Entry(create_frame, textvariable=self.number_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Protocol data fields
        ttk.Label(create_frame, text="Data Fields:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.data_fields_text = scrolledtext.ScrolledText(create_frame, height=5, width=30)
        self.data_fields_text.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.data_fields_text.insert(tk.END, "message\nvalue\ntimestamp")
        
        # Create button
        ttk.Button(
            create_frame, 
            text="Create Protocol", 
            command=self._create_protocol
        ).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Configure the grid
        create_frame.columnconfigure(1, weight=1)
    
    def _list_protocols(self):
        """List available protocols"""
        self.protocol_manager.list_protocols()
    
    def _create_protocol(self):
        """Create a new protocol"""
        # Get protocol configuration
        name = self.name_var.get()
        number = self.number_var.get()
        
        # Parse data fields
        data_fields_text = self.data_fields_text.get("1.0", tk.END).strip()
        data_fields = data_fields_text.split("\n")
        data_fields = [field.strip() for field in data_fields if field.strip()]
        
        # Create the protocol
        self.protocol_manager.create_protocol(
            name, number, data_fields,
            on_success=self._on_protocol_created,
            on_error=self._on_protocol_error
        )
    
    def _on_protocol_created(self, message):
        """Called when a protocol is successfully created"""
        # Show success message
        messagebox.showinfo("Protocol Created", message)
    
    def _on_protocol_error(self, error_message):
        """Called when there's an error creating a protocol"""
        # Show error message
        messagebox.showerror("Protocol Error", error_message)


class RegistryFrame(ttk.LabelFrame):
    """
    Server registry frame
    """
    
    def __init__(self, parent, registry_manager, **kwargs):
        super().__init__(parent, text="Server Registry", **kwargs)
        self.registry_manager = registry_manager
        
        # Initialize the UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the registry UI"""
        # List servers button
        ttk.Button(
            self, 
            text="List Registered Servers", 
            command=self._list_servers
        ).pack(padx=5, pady=5)
    
    def _list_servers(self):
        """List registered servers"""
        self.registry_manager.list_servers()