"""
Utility functions for data processing

Main features:
- Saving and loading JSON data
- Data hash calculation
- Enhanced cryptographic functions
"""

import os
import hashlib
from pathlib import Path
import orjson
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


def calculate_hash(data, algorithm='sha256'):
    """
    Calculate the hash value of the data.
    
    Args:
        data: Data to be hashed (string or bytes)
        algorithm (str): Name of the hash algorithm
    
    Returns:
        str: Hexadecimal representation of the hash value
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data)
    return hash_obj.hexdigest()


def save_json(file_path, data, indent=2):
    """
    Save JSON data to a file using orjson for better performance.
    
    Args:
        file_path (str or Path): Path to the file to save
        data: JSON data to save (dict or list)
        indent (int): Indentation width for JSON
    
    Returns:
        str: Absolute path of the saved file
    """
    file_path = Path(file_path)
    
    # orjson doesn't support indentation directly as an option like standard json
    # we'll use orjson.OPT_INDENT_2 if indent is 2, otherwise serialize with standard options
    options = orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
    if indent == 2:
        options |= orjson.OPT_INDENT_2
    
    json_bytes = orjson.dumps(data, option=options)
    
    with open(file_path, 'wb') as f:
        f.write(json_bytes)
    
    return str(file_path.absolute())


def load_json(file_path):
    """
    Load data from a JSON file using orjson for better performance.
    
    Args:
        file_path (str or Path): Path to the JSON file to load
    
    Returns:
        dict or list: Loaded JSON data
        Returns None if the file does not exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'rb') as f:
        return orjson.loads(f.read())


def generate_key(password, salt=None):
    """
    Generate a cryptographic key from a password using PBKDF2.
    
    Args:
        password (str): Password to derive the key from
        salt (bytes, optional): Salt for key derivation. If None, a new one is generated.
    
    Returns:
        tuple: (key, salt) where key is the derived key and salt is the salt used
    """
    if isinstance(password, str):
        password = password.encode()
    
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key, salt


def encrypt_data(data, password):
    """
    Encrypt data using a password.
    
    Args:
        data (str or bytes): Data to encrypt
        password (str): Password for encryption
    
    Returns:
        dict: {'encrypted': encrypted_data_base64, 'salt': salt_base64}
    """
    if isinstance(data, str):
        data = data.encode()
    
    key, salt = generate_key(password)
    f = Fernet(key)
    encrypted_data = f.encrypt(data)
    
    return {
        'encrypted': base64.b64encode(encrypted_data).decode('ascii'),
        'salt': base64.b64encode(salt).decode('ascii')
    }


def decrypt_data(encrypted_dict, password):
    """
    Decrypt data that was encrypted with encrypt_data.
    
    Args:
        encrypted_dict (dict): Dictionary with 'encrypted' and 'salt' keys
        password (str): Password for decryption
    
    Returns:
        bytes: Decrypted data
    """
    encrypted_data = base64.b64decode(encrypted_dict['encrypted'])
    salt = base64.b64decode(encrypted_dict['salt'])
    
    key, _ = generate_key(password, salt)
    f = Fernet(key)
    
    return f.decrypt(encrypted_data)