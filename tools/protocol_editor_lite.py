#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Protocol Editor Lite

A simplified version of the protocol editor tool focusing on:
- Creating and editing protocols
- Managing data fields
- Protocol preview and testing
"""

import sys
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime

# Add the project root directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import witch-core modules
try:
    from src.protocol import protocol_manager
except ImportError as e:
    print(f"Error importing witch-core modules: {e}")
    sys.exit(1)


class ProtocolEditorLite:
    def __init__(self, root):
        self.root = root
        self.root.title("Protocol Editor Lite")
        self.root.geometry("800x600")
        self.root.minsize(640, 480)
        
        # Variables
        self.protocol_data = None
        self.is_modified = False
        self.current_file = None
        
        # Protocol variables
        self.protocol_id = tk.StringVar()
        self.protocol_name = tk.StringVar()
        self.protocol_version = tk.StringVar(value="1.0.0")
        self.protocol_desc = tk.StringVar()
        
        # Field variables
        self.field_name = tk.StringVar()
        self.field_type = tk.StringVar(value="string")
        self.field_required = tk.BooleanVar(value=True)
        self.field_desc = tk.StringVar()
        
        # Create menu
        self.create_menu()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.basic_info_tab = ttk.Frame(self.notebook)
        self.fields_tab = ttk.Frame(self.notebook)
        self.preview_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.basic_info_tab, text="Basic Info")
        self.notebook.add(self.fields_tab, text="Data Fields")
        self.notebook.add(self.preview_tab, text="Preview")
        
        # Set up tabs
        self.setup_basic_info_tab()
        self.setup_fields_tab()
        self.setup_preview_tab()
        
        # Create button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Create save button
        save_button = ttk.Button(button_frame, text="Save Protocol", command=self.save_protocol)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Create new button
        new_button = ttk.Button(button_frame, text="New Protocol", command=self.create_new_protocol)
        new_button.pack(side=tk.RIGHT, padx=5)
        
        # Initialize with a new protocol
        self.create_new_protocol()
    
    def create_menu(self):
        """Create the application menu"""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Protocol", command=self.create_new_protocol)
        file_menu.add_command(label="Open Protocol...", command=self.open_protocol)
        file_menu.add_command(label="Save", command=self.save_protocol)
        file_menu.add_command(label="Save As...", command=self.save_protocol_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="List Available Protocols", command=self.list_protocols)
        tools_menu.add_command(label="Export as JSON", command=self.export_protocol)
        
        # Add menus to menu bar
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        
        self.root.config(menu=menu_bar)
    
    def setup_basic_info_tab(self):
        """Set up the basic info tab"""
        frame = self.basic_info_tab
        
        # Protocol ID
        ttk.Label(frame, text="Protocol ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.protocol_id, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(frame, text="(e.g. 001, 002, etc.)").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Protocol Name
        ttk.Label(frame, text="Protocol Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.protocol_name, width=30).grid(row=1, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Protocol Version
        ttk.Label(frame, text="Version:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.protocol_version, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Protocol Description
        ttk.Label(frame, text="Description:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.protocol_desc, width=50).grid(row=3, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Add trace to variables for detecting changes
        self.protocol_id.trace_add("write", self.mark_modified)
        self.protocol_name.trace_add("write", self.mark_modified)
        self.protocol_version.trace_add("write", self.mark_modified)
        self.protocol_desc.trace_add("write", self.mark_modified)
    
    def setup_fields_tab(self):
        """Set up the fields tab"""
        frame = self.fields_tab
        
        # Field edit frame
        field_edit_frame = ttk.LabelFrame(frame, text="Add/Edit Field")
        field_edit_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Field Name
        ttk.Label(field_edit_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(field_edit_frame, textvariable=self.field_name, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Field Type
        ttk.Label(field_edit_frame, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        field_types = ["string", "int", "float", "bool", "list", "dict", "binary"]
        ttk.Combobox(field_edit_frame, textvariable=self.field_type, values=field_types, width=10).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Field Required
        ttk.Checkbutton(field_edit_frame, text="Required", variable=self.field_required).grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        # Field Description
        ttk.Label(field_edit_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(field_edit_frame, textvariable=self.field_desc, width=50).grid(row=1, column=1, columnspan=4, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Field buttons
        button_frame = ttk.Frame(field_edit_frame)
        button_frame.grid(row=2, column=0, columnspan=5, pady=5)
        
        add_button = ttk.Button(button_frame, text="Add Field", command=self.add_field)
        add_button.pack(side=tk.LEFT, padx=5)
        
        update_button = ttk.Button(button_frame, text="Update Field", command=self.update_field)
        update_button.pack(side=tk.LEFT, padx=5)
        
        # Field list
        fields_frame = ttk.LabelFrame(frame, text="Fields")
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for fields
        self.fields_tree = ttk.Treeview(fields_frame, columns=("name", "type", "required", "description"), show="headings")
        self.fields_tree.heading("name", text="Field Name")
        self.fields_tree.heading("type", text="Type")
        self.fields_tree.heading("required", text="Required")
        self.fields_tree.heading("description", text="Description")
        
        self.fields_tree.column("name", width=100)
        self.fields_tree.column("type", width=50)
        self.fields_tree.column("required", width=60)
        self.fields_tree.column("description", width=300)
        
        self.fields_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar for fields tree
        scrollbar = ttk.Scrollbar(fields_frame, orient="vertical", command=self.fields_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.fields_tree.configure(yscrollcommand=scrollbar.set)
        
        # Field selection event
        self.fields_tree.bind("<<TreeviewSelect>>", self.on_field_select)
        
        # Button frame below tree
        tree_button_frame = ttk.Frame(frame)
        tree_button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        delete_button = ttk.Button(tree_button_frame, text="Delete Field", command=self.delete_field)
        delete_button.pack(side=tk.LEFT, padx=5)
    
    def setup_preview_tab(self):
        """Set up the preview tab"""
        frame = self.preview_tab
        
        # Preview frame
        preview_frame = ttk.LabelFrame(frame, text="Protocol Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Preview text
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Update preview button
        update_button = ttk.Button(frame, text="Update Preview", command=self.update_preview)
        update_button.pack(pady=10)
    
    def create_new_protocol(self):
        """Create a new protocol"""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "There are unsaved changes. Discard and create new?"):
                return
        
        # Initialize protocol data
        self.protocol_data = {
            "id": "",
            "name": "",
            "version": "1.0.0",
            "description": "",
            "fields": [],
            "options": {
                "compress": False,
                "encrypt": False
            }
        }
        
        # Clear form fields
        self.protocol_id.set("")
        self.protocol_name.set("")
        self.protocol_version.set("1.0.0")
        self.protocol_desc.set("")
        
        # Clear fields tree
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)
        
        # Clear field form
        self.field_name.set("")
        self.field_type.set("string")
        self.field_required.set(True)
        self.field_desc.set("")
        
        # Update preview
        self.update_preview()
        
        # Reset modified flag
        self.is_modified = False
        self.current_file = None
        self.update_title()
    
    def open_protocol(self):
        """Open a protocol file"""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "There are unsaved changes. Discard and open?"):
                return
        
        # Get file path
        file_path = filedialog.askopenfilename(
            title="Open Protocol File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Load protocol file
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Set protocol data
            self.protocol_data = data
            
            # Update form fields
            self.protocol_id.set(data.get("id", ""))
            self.protocol_name.set(data.get("name", ""))
            self.protocol_version.set(data.get("version", "1.0.0"))
            self.protocol_desc.set(data.get("description", ""))
            
            # Update fields tree
            self.update_fields_tree()
            
            # Update preview
            self.update_preview()
            
            # Set current file and modified flag
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            
            messagebox.showinfo("Success", f"Protocol loaded: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open protocol file: {str(e)}")
    
    def save_protocol(self):
        """Save the protocol to a file"""
        if self.current_file:
            return self.save_protocol_to_file(self.current_file)
        else:
            return self.save_protocol_as()
    
    def save_protocol_as(self):
        """Save the protocol to a new file"""
        # Validate protocol data
        if not self.validate_protocol():
            return False
        
        # Get file path
        file_path = filedialog.asksaveasfilename(
            title="Save Protocol File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            defaultextension=".json"
        )
        
        if not file_path:
            return False
        
        return self.save_protocol_to_file(file_path)
    
    def save_protocol_to_file(self, file_path):
        """Save the protocol to the specified file"""
        try:
            # Update protocol data from form
            self.update_protocol_data()
            
            # Write to file
            with open(file_path, "w") as f:
                json.dump(self.protocol_data, f, indent=2)
            
            # Update state
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            
            messagebox.showinfo("Success", f"Protocol saved: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save protocol file: {str(e)}")
            return False
    
    def update_protocol_data(self):
        """Update protocol data from form fields"""
        self.protocol_data["id"] = self.protocol_id.get()
        self.protocol_data["name"] = self.protocol_name.get()
        self.protocol_data["version"] = self.protocol_version.get()
        self.protocol_data["description"] = self.protocol_desc.get()
    
    def validate_protocol(self):
        """Validate protocol data"""
        if not self.protocol_id.get():
            messagebox.showerror("Validation Error", "Protocol ID is required")
            return False
        
        if not self.protocol_name.get():
            messagebox.showerror("Validation Error", "Protocol Name is required")
            return False
        
        return True
    
    def update_title(self):
        """Update window title with file name and modified status"""
        title = "Protocol Editor Lite"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.is_modified:
            title += " *"
        self.root.title(title)
    
    def mark_modified(self, *args):
        """Mark the protocol as modified"""
        self.is_modified = True
        self.update_title()
    
    def update_fields_tree(self):
        """Update the fields tree with current protocol data"""
        # Clear tree
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)
        
        # Add fields
        fields = self.protocol_data.get("fields", [])
        for field in fields:
            self.fields_tree.insert(
                "", "end",
                values=(
                    field.get("name", ""),
                    field.get("type", ""),
                    "Yes" if field.get("required", False) else "No",
                    field.get("description", "")
                )
            )
    
    def add_field(self):
        """Add a new field to the protocol"""
        name = self.field_name.get()
        if not name:
            messagebox.showerror("Error", "Field name is required")
            return
        
        # Check if field name already exists
        for field in self.protocol_data.get("fields", []):
            if field.get("name") == name:
                messagebox.showerror("Error", f"Field name '{name}' already exists")
                return
        
        # Create field data
        field_data = {
            "name": name,
            "type": self.field_type.get(),
            "required": self.field_required.get(),
            "description": self.field_desc.get()
        }
        
        # Add to protocol data
        if "fields" not in self.protocol_data:
            self.protocol_data["fields"] = []
        
        self.protocol_data["fields"].append(field_data)
        
        # Add to tree
        self.fields_tree.insert(
            "", "end",
            values=(
                field_data["name"],
                field_data["type"],
                "Yes" if field_data["required"] else "No",
                field_data["description"]
            )
        )
        
        # Clear form
        self.field_name.set("")
        self.field_type.set("string")
        self.field_required.set(True)
        self.field_desc.set("")
        
        # Mark modified
        self.mark_modified()
    
    def update_field(self):
        """Update the selected field"""
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Please select a field to update")
            return
        
        name = self.field_name.get()
        if not name:
            messagebox.showerror("Error", "Field name is required")
            return
        
        # Get selected field index
        selected_item = selection[0]
        selected_index = self.fields_tree.index(selected_item)
        
        # Check if name changed and conflicts with another field
        old_name = self.protocol_data["fields"][selected_index]["name"]
        if name != old_name:
            for i, field in enumerate(self.protocol_data["fields"]):
                if i != selected_index and field["name"] == name:
                    messagebox.showerror("Error", f"Field name '{name}' already exists")
                    return
        
        # Update field data
        field_data = {
            "name": name,
            "type": self.field_type.get(),
            "required": self.field_required.get(),
            "description": self.field_desc.get()
        }
        
        # Update protocol data
        self.protocol_data["fields"][selected_index] = field_data
        
        # Update tree
        self.fields_tree.item(
            selected_item,
            values=(
                field_data["name"],
                field_data["type"],
                "Yes" if field_data["required"] else "No",
                field_data["description"]
            )
        )
        
        # Mark modified
        self.mark_modified()
    
    def delete_field(self):
        """Delete the selected field"""
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Please select a field to delete")
            return
        
        # Get selected field index
        selected_item = selection[0]
        selected_index = self.fields_tree.index(selected_item)
        
        # Remove from protocol data
        del self.protocol_data["fields"][selected_index]
        
        # Remove from tree
        self.fields_tree.delete(selected_item)
        
        # Mark modified
        self.mark_modified()
    
    def on_field_select(self, event):
        """Handle field selection"""
        selection = self.fields_tree.selection()
        if not selection:
            return
        
        # Get selected field index
        selected_item = selection[0]
        selected_index = self.fields_tree.index(selected_item)
        
        # Get field data
        field_data = self.protocol_data["fields"][selected_index]
        
        # Update form
        self.field_name.set(field_data.get("name", ""))
        self.field_type.set(field_data.get("type", "string"))
        self.field_required.set(field_data.get("required", False))
        self.field_desc.set(field_data.get("description", ""))
    
    def update_preview(self):
        """Update the protocol preview"""
        # Update protocol data from form
        self.update_protocol_data()
        
        # Format preview
        preview = json.dumps(self.protocol_data, indent=2)
        
        # Update preview text
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, preview)
    
    def list_protocols(self):
        """List all available protocols"""
        try:
            protocols = protocol_manager.list_available_protocols()
            
            if not protocols:
                messagebox.showinfo("Protocols", "No protocols available")
                return
            
            # Create dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Available Protocols")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Create listbox
            protocols_list = tk.Listbox(dialog, width=40, height=10)
            protocols_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add protocols to listbox
            for protocol in protocols:
                protocols_list.insert(tk.END, protocol)
            
            # Close button
            close_button = ttk.Button(dialog, text="Close", command=dialog.destroy)
            close_button.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list protocols: {str(e)}")
    
    def export_protocol(self):
        """Export protocol to JSON file"""
        # Validate protocol data
        if not self.validate_protocol():
            return
        
        # Update protocol data from form
        self.update_protocol_data()
        
        # Get file path
        file_path = filedialog.asksaveasfilename(
            title="Export Protocol",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            defaultextension=".json"
        )
        
        if not file_path:
            return
        
        try:
            # Write to file
            with open(file_path, "w") as f:
                json.dump(self.protocol_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Protocol exported to: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export protocol: {str(e)}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_modified:
            if not messagebox.askyesnocancel("Unsaved Changes", "Save changes before closing?"):
                return
            elif not self.save_protocol():
                return
        
        self.root.destroy()


def main():
    """Main function"""
    try:
        root = tk.Tk()
        app = ProtocolEditorLite(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()