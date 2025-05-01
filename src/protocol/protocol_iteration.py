"""
Module providing iteration protocol functionality

Main features:
- Creation of protocols for iterative processing
- Handling of continuation flags
- Management of iteration state
"""

import uuid
from datetime import datetime
from .protocol_core import validate_protocol


def create_iteration_protocol(base_protocol, iteration_options=None):
    """
    Create an iteration protocol from a base protocol.
    Iteration protocols are used to manage continuous communication sessions.
    
    Args:
        base_protocol (dict): Base protocol definition
        iteration_options (dict): Iteration processing options
            e.g.: {
                'max_iterations': 10,  # Maximum iteration count
                'timeout': 30,         # Timeout (seconds)
                'auto_continue': True, # Auto-continue mode
                'termination_signals': ["STOP", "COMPLETE"]  # Termination signals
            }
    
    Returns:
        dict: Protocol definition for iteration processing
    """
    if not validate_protocol(base_protocol):
        return None
    
    # Default iteration options
    default_options = {
        'max_iterations': 100,    # Default maximum iteration count
        'timeout': 60,           # Default timeout (seconds)
        'auto_continue': True,    # Default auto-continue mode
        'termination_signals': ["STOP", "COMPLETE", "ERROR"]  # Termination signals
    }
    
    # Override defaults with provided options
    if iteration_options is None:
        iteration_options = {}
    
    iter_options = {**default_options, **iteration_options}
    
    # Create iteration protocol
    iter_protocol = base_protocol.copy()
    iter_protocol["name"] = f"{base_protocol['name']}_iteration"
    iter_protocol["id"] = str(uuid.uuid4())
    iter_protocol["base_protocol_id"] = base_protocol.get("id")
    iter_protocol["created_at"] = datetime.now().isoformat()
    iter_protocol["updated_at"] = datetime.now().isoformat()
    
    # Add iteration data fields
    if "iteration_status" not in iter_protocol["data_names"]:
        iter_protocol["data_names"].append("iteration_status")
    
    if "iteration_count" not in iter_protocol["data_names"]:
        iter_protocol["data_names"].append("iteration_count")
    
    if "continue" not in iter_protocol["data_names"]:
        iter_protocol["data_names"].append("continue")
    
    # Update data type definitions
    if "data_types" not in iter_protocol:
        iter_protocol["data_types"] = {}
    
    iter_protocol["data_types"]["iteration_status"] = "string"
    iter_protocol["data_types"]["iteration_count"] = "int"
    iter_protocol["data_types"]["continue"] = "bool"
    
    # Set iteration options
    if "options" not in iter_protocol:
        iter_protocol["options"] = {}
    
    iter_protocol["options"]["iteration"] = iter_options
    
    return iter_protocol


def is_continue_requested(data):
    """
    Check for continuation request in iteration protocol response data
    
    Args:
        data (dict): Protocol response data
        
    Returns:
        bool: True if continuation is requested, False otherwise
    """
    # Check for continuation flag (if explicit flag exists)
    if 'continue' in data:
        return bool(data['continue'])
    
    # Check for continue_iteration key
    if 'continue_iteration' in data:
        return bool(data['continue_iteration'])
    
    # Check status (continue if "continue" or "iterate")
    if 'status' in data:
        status = data['status'].lower()
        if status in ['continue', 'iterate', 'next']:
            return True
        if status in ['stop', 'complete', 'finished', 'done', 'end']:
            return False
    
    # Check iteration_status key
    if 'iteration_status' in data:
        iteration_status = data['iteration_status'].lower()
        if iteration_status in ['continue', 'iterate', 'next']:
            return True
        if iteration_status in ['stop', 'complete', 'finished', 'done', 'end']:
            return False
    
    # Check next_iteration key (continue if there's information for next iteration)
    if 'next_iteration' in data and data['next_iteration']:
        return True
    
    # Default: don't continue
    return False