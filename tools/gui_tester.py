#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Tester for witch-core

This is the main entry point for the GUI Tester application.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import socket

# Add the project root directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the GUI application class
from tools.gui_tester_app import WitchCoreGUI


def get_hostname():
    """Get the hostname of the machine"""
    try:
        return socket.gethostname()
    except:
        return "unknown-host"


if __name__ == "__main__":
    # Create the root window
    root = tk.Tk()
    
    # Set default server name to hostname
    server_name = get_hostname()
    
    try:
        # Create the GUI application
        app = WitchCoreGUI(root, server_name=server_name)
        
        # Set up closing handler
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Start the application
        print(f"Starting Witch-Core GUI Tester for {server_name}...")
        print("Application ready.")
        root.mainloop()
    
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")
        root.destroy()