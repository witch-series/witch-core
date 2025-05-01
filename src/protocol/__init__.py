"""
Communication Protocol Management Module for witch-series Project

This module includes the following features:
- Protocol definition
- Protocol version management
- Protocol validation and integrity checking
"""

from .protocol_manager import (
    load_protocol,
    validate_protocol,
    create_protocol,
    save_protocol,
    get_protocol_version
)

__all__ = [
    'load_protocol',
    'validate_protocol',
    'create_protocol',
    'save_protocol',
    'get_protocol_version'
]