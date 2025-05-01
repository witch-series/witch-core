#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hash utilities for file verification and message signing.
Enhanced with high-performance hash algorithms and simplified APIs.
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any, Union, Callable
from functools import lru_cache
import xxhash
import blake3
from tqdm import tqdm
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ed25519
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption
)

# Logger configuration
logger = logging.getLogger("WitchHash")

# Hash algorithm mapping
HASH_ALGORITHMS = {
    'sha256': lambda: hashlib.sha256(),
    'sha512': lambda: hashlib.sha512(),
    'blake3': lambda: blake3.blake3(),
    'xxh64': lambda: xxhash.xxh64(),
    'xxh3_64': lambda: xxhash.xxh3_64(),
    'xxh3_128': lambda: xxhash.xxh3_128(),
}

def generate_file_hash(file_path: Union[str, Path]) -> str:
    """
    Generate a hash for a file using Blake3 (faster than SHA-256)
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Hash of the file
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        return ""
    
    try:
        return blake3.blake3(file_path.read_bytes()).hexdigest()
    except Exception as e:
        logger.error(f"Error generating file hash: {e}")
        return ""

def generate_key_pair(key_type: str = 'rsa') -> Dict[str, bytes]:
    """
    Generate key pair for signing and verification
    
    Args:
        key_type: Type of key ('rsa' or 'ed25519')
    
    Returns:
        Dict[str, bytes]: Dictionary with 'private_key' and 'public_key' in PEM format
    """
    if key_type == 'ed25519':
        # Ed25519 keys (faster, smaller, more secure for most uses)
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )
    else:
        # Default to RSA
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )
    
    return {
        'private_key': private_pem,
        'public_key': public_pem
    }

def sign_data(data: Union[str, bytes], private_key_pem: bytes) -> bytes:
    """
    Sign data with a private key (auto-detects key type)
    
    Args:
        data: Data to sign
        private_key_pem: PEM-encoded private key
        
    Returns:
        bytes: Signature
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    private_key = load_pem_private_key(private_key_pem, password=None)
    
    if isinstance(private_key, ed25519.Ed25519PrivateKey):
        # Ed25519 signing
        return private_key.sign(data)
    else:
        # RSA signing
        return private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

def verify_signature(data: Union[str, bytes], signature: bytes, public_key_pem: bytes) -> bool:
    """
    Verify a signature with a public key (auto-detects key type)
    
    Args:
        data: Signed data
        signature: Signature to verify
        public_key_pem: PEM-encoded public key
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    public_key = load_pem_public_key(public_key_pem)
    
    try:
        if isinstance(public_key, ed25519.Ed25519PublicKey):
            # Ed25519 verification
            public_key.verify(signature, data)
        else:
            # RSA verification
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        return True
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False

@lru_cache(maxsize=128)
def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'xxh3_64') -> str:
    """
    Calculates the hash value of a file with LRU cache to avoid recalculating
    recently accessed files.

    Args:
        file_path: Path to the file to calculate hash
        algorithm: Hash algorithm to use (xxh3_64, blake3, sha256, etc.)

    Returns:
        str: Hexadecimal representation of the hash value
    """
    file_path = Path(file_path)  # Convert to Path object
    
    # Use XXH3 by default (much faster than SHA-256)
    if algorithm not in HASH_ALGORITHMS:
        algorithm = 'xxh3_64'
        
    hash_obj = HASH_ALGORITHMS[algorithm]()
    
    try:
        # For small files, read at once
        if file_path.stat().st_size < 10 * 1024 * 1024:  # 10MB
            hash_obj.update(file_path.read_bytes())
        else:
            # For larger files, read in chunks
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
                    
        # XXHash has both hexdigest and intdigest
        if hasattr(hash_obj, 'hexdigest'):
            return hash_obj.hexdigest()
        else:
            return format(hash_obj.intdigest(), 'x')
    except (IOError, OSError):
        return ""


def calculate_src_directory_hash(
    src_path: Optional[Union[str, Path]] = None,
    algorithm: str = 'xxh3_64',
    exclude_dirs: Optional[Set[str]] = None,
    exclude_files: Optional[Set[str]] = None,
    file_extension: str = '.py',
    show_progress: bool = False
) -> Tuple[str, Dict[str, str]]:
    """
    Calculates the hash of all Python files in the src directory,
    and combines them to generate a single hash value.

    Args:
        src_path: Path to src directory (automatically detected if not specified)
        algorithm: Hash algorithm to use (xxh3_64, blake3, sha256, etc.)
        exclude_dirs: Set of directory names to exclude
        exclude_files: Set of file names to exclude
        file_extension: File extension to target
        show_progress: Whether to show a progress bar

    Returns:
        Tuple[str, Dict[str, str]]: 
            - Combined hash value of all files
            - Dictionary of file paths and their hash values
    """
    # Set default values
    if exclude_dirs is None:
        exclude_dirs = {'__pycache__', '.git', '.svn'}
    
    if exclude_files is None:
        exclude_files = {'__init__.py'}
    
    # Auto-detect src path if not specified
    if src_path is None:
        # The parent directory of the parent directory of this file (hash_utils.py) is src
        src_path = Path(__file__).parent.parent
    else:
        src_path = Path(src_path)  # Convert to Path object if it's a string
    
    # Optimize file collection with pathlib
    target_files = []
    for path in src_path.rglob(f"*{file_extension}"):
        if any(p.name in exclude_dirs for p in path.parents):
            continue
        if path.name in exclude_files:
            continue
        target_files.append(path)
    
    # Dictionary to store file hashes
    file_hashes = {}
    
    # Process files with optional progress bar
    file_iterator = tqdm(target_files, desc="Hashing files") if show_progress else target_files
    
    for file_path in file_iterator:
        relative_path = str(file_path.relative_to(src_path))
        file_hash = calculate_file_hash(file_path, algorithm)
        
        if file_hash:  # Add only if hash calculation was successful
            file_hashes[relative_path] = file_hash
    
    # Sort by file path, then concatenate hash values
    sorted_paths = sorted(file_hashes.keys())
    combined_hash = ''.join(file_hashes[path] for path in sorted_paths)
    
    # Calculate the final combined hash using the same algorithm
    if algorithm in HASH_ALGORITHMS:
        final_hash_obj = HASH_ALGORITHMS[algorithm]()
    else:
        final_hash_obj = hashlib.new(algorithm)
    
    final_hash_obj.update(combined_hash.encode('utf-8'))
    
    # Return the final hash as a hexadecimal string
    if hasattr(final_hash_obj, 'hexdigest'):
        return final_hash_obj.hexdigest(), file_hashes
    else:
        return format(final_hash_obj.intdigest(), 'x'), file_hashes


def verify_src_integrity(expected_hash: str, src_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Verifies the integrity of the src directory

    Args:
        expected_hash: Expected hash value
        src_path: Path to the src directory to verify

    Returns:
        bool: True if the hash matches, False otherwise
    """
    actual_hash, _ = calculate_src_directory_hash(src_path)
    return actual_hash == expected_hash


def get_src_hash_info(src_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Gets hash information for the src directory

    Args:
        src_path: Path to the src directory

    Returns:
        Dict[str, Any]: Dictionary containing hash information
    """
    total_hash, file_hashes = calculate_src_directory_hash(src_path)
    
    # Count total files and subdirectories
    subdirs = set()
    for file_path in file_hashes.keys():
        subdir = file_path.split(os.sep)[0] if os.sep in file_path else "root"
        subdirs.add(subdir)
    
    return {
        'total_hash': total_hash,
        'file_count': len(file_hashes),
        'subdirs': list(subdirs),
        'algorithm': 'xxh3_64',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Behavior when this script is executed directly
    src_hash, files = calculate_src_directory_hash(show_progress=True)
    print(f"Total hash value of SRC directory: {src_hash}")
    print(f"Number of files: {len(files)}")
    for path, hash_value in sorted(files.items()):
        print(f"{path}: {hash_value[:8]}...")