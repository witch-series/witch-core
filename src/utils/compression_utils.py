#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Compression Utility Module

This module provides various compression techniques:
- Standard compression (gzip, zlib, bz2, lzma)
- High-performance compression (zstandard, lz4)
- Bit compression
- Huffman coding
"""

import gzip
import zlib
import bz2
import lzma
import pickle
import heapq
from collections import Counter
from typing import Dict, Tuple, List, Any, Union, Optional
import zstandard as zstd
import lz4.frame
import lz4.block
import orjson


def compress_data(data: bytes, method: str = 'gzip', compression_level: int = 6) -> bytes:
    """
    Compresses data using the specified method

    Args:
        data: Byte data to compress
        method: Compression method ('gzip', 'zlib', 'bz2', 'lzma', 'zstd', 'lz4', 'bit', 'huffman')
        compression_level: Compression level (used with standard compression methods)

    Returns:
        Compressed byte data
    """
    if method == 'gzip':
        return gzip.compress(data, compression_level)
    elif method == 'zlib':
        return zlib.compress(data, compression_level)
    elif method == 'bz2':
        return bz2.compress(data, compression_level)
    elif method == 'lzma':
        return lzma.compress(data)
    elif method == 'zstd':
        return zstd.compress(data, compression_level)
    elif method == 'lz4':
        return lz4.frame.compress(data, compression_level=compression_level)
    elif method == 'lz4-block':
        return lz4.block.compress(data, compression=compression_level)
    elif method == 'bit':
        return bit_compress(data)
    elif method == 'huffman':
        return huffman_compress(data)
    else:
        raise ValueError(f"Unknown compression method: {method}")


def decompress_data(data: bytes, method: str = 'gzip') -> bytes:
    """
    Decompresses compressed data

    Args:
        data: Byte data to decompress
        method: Compression method used ('gzip', 'zlib', 'bz2', 'lzma', 'zstd', 'lz4', 'bit', 'huffman')

    Returns:
        Decompressed byte data
    """
    if method == 'gzip':
        return gzip.decompress(data)
    elif method == 'zlib':
        return zlib.decompress(data)
    elif method == 'bz2':
        return bz2.decompress(data)
    elif method == 'lzma':
        return lzma.decompress(data)
    elif method == 'zstd':
        return zstd.decompress(data)
    elif method == 'lz4':
        return lz4.frame.decompress(data)
    elif method == 'lz4-block':
        return lz4.block.decompress(data)
    elif method == 'bit':
        return bit_decompress(data)
    elif method == 'huffman':
        return huffman_decompress(data)
    else:
        raise ValueError(f"Unknown decompression method: {method}")


# Bit compression implementation
def bit_compress(data: bytes) -> bytes:
    """
    Performs bit compression.
    Compresses consecutive byte patterns.
    
    Args:
        data: Byte data to compress
        
    Returns:
        Compressed byte data
    """
    if not data:
        return b''
    
    result = bytearray()
    count = 1
    current = data[0]
    
    # Run-length encoding algorithm
    for i in range(1, len(data)):
        if data[i] == current and count < 255:
            count += 1
        else:
            # Store in the format: flag, count, value
            result.extend([count, current])
            current = data[i]
            count = 1
    
    # Add the last element
    result.extend([count, current])
    
    # Add format identifier at the beginning (used during decompression)
    return bytes([0x42, 0x43]) + bytes(result)  # BC = Bit Compression


def bit_decompress(data: bytes) -> bytes:
    """
    Decompresses bit-compressed data
    
    Args:
        data: Byte data to decompress
        
    Returns:
        Decompressed byte data
    """
    if not data or len(data) < 2 or data[0] != 0x42 or data[1] != 0x43:
        raise ValueError("Invalid bit-compressed data")
    
    # Skip format identifier
    data = data[2:]
    
    if len(data) % 2 != 0:
        raise ValueError("Invalid bit-compressed data format")
    
    result = bytearray()
    
    # Decompress run-length encoding
    for i in range(0, len(data), 2):
        count = data[i]
        value = data[i + 1]
        result.extend([value] * count)
    
    return bytes(result)


# Huffman coding implementation
class HuffmanNode:
    def __init__(self, char: Optional[int] = None, freq: int = 0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
        
    def __lt__(self, other):
        return self.freq < other.freq


def _build_huffman_tree(data: bytes) -> Tuple[HuffmanNode, Dict[int, str]]:
    """Builds a Huffman tree and creates a coding table"""
    # Frequency count
    freq = Counter(data)
    
    # Use priority queue
    heap = [HuffmanNode(char, freq) for char, freq in freq.items()]
    heapq.heapify(heap)
    
    # Merge the two smallest nodes until a single tree remains
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        
        heapq.heappush(heap, merged)
    
    # Create coding table
    codes = {}
    
    def _generate_codes(node, code=""):
        if node is not None:
            if node.char is not None:
                codes[node.char] = code
            _generate_codes(node.left, code + "0")
            _generate_codes(node.right, code + "1")
    
    if heap:
        root = heap[0]
        _generate_codes(root)
    
    return (root, codes) if heap else (None, {})


def huffman_compress(data: bytes) -> bytes:
    """
    Compresses data using Huffman coding
    
    Args:
        data: Byte data to compress
        
    Returns:
        Compressed byte data (header + compressed data)
    """
    if not data:
        return b''
    
    # Build Huffman tree and coding table
    root, codes = _build_huffman_tree(data)
    
    if not root:
        return bytes([0x48, 0x43]) + data  # HC = Huffman Compression
    
    # Convert to bit string
    encoded = ''.join(codes[byte] for byte in data)
    
    # Convert bit string to byte array
    padded_length = ((len(encoded) + 7) // 8) * 8
    padded = encoded.ljust(padded_length, '0')
    
    byte_array = bytearray()
    for i in range(0, len(padded), 8):
        byte = int(padded[i:i+8], 2)
        byte_array.append(byte)
    
    # Use orjson for faster serialization
    metadata = orjson.dumps((len(encoded), codes)).decode('utf-8')
    
    # Format identifier + metadata length + metadata + compressed data
    metadata_bytes = metadata.encode('utf-8')
    metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')
    return bytes([0x48, 0x43]) + metadata_length + metadata_bytes + bytes(byte_array)


def huffman_decompress(data: bytes) -> bytes:
    """
    Decompresses Huffman-coded data
    
    Args:
        data: Byte data to decompress
        
    Returns:
        Decompressed byte data
    """
    if not data or len(data) < 6 or data[0] != 0x48 or data[1] != 0x43:
        raise ValueError("Invalid Huffman-coded data")
    
    # Skip format identifier
    data = data[2:]
    
    # Get metadata length
    metadata_length = int.from_bytes(data[:4], byteorder='big')
    
    # Separate metadata and encoded data
    metadata_bytes = data[4:4+metadata_length]
    encoded_data = data[4+metadata_length:]
    
    # Deserialize metadata using orjson for better performance
    metadata_str = metadata_bytes.decode('utf-8')
    bit_length, codes = orjson.loads(metadata_str)
    
    # Convert codes to bit string
    bit_string = ''.join(bin(byte)[2:].zfill(8) for byte in encoded_data)
    bit_string = bit_string[:bit_length]  # Remove extra padding
    
    # Create reverse lookup dictionary
    reverse_codes = {code: char for char, code in codes.items()}
    
    # Decode bit string
    result = bytearray()
    code = ""
    for bit in bit_string:
        code += bit
        if code in reverse_codes:
            result.append(reverse_codes[code])
            code = ""
    
    return bytes(result)


# Function to get the list of compression methods
def get_compression_methods() -> List[str]:
    """
    Returns a list of available compression methods
    
    Returns:
        List of compression methods
    """
    return ['None', 'gzip', 'zlib', 'bz2', 'lzma', 'zstd', 'lz4', 'lz4-block', 'bit', 'huffman']


# Function to get the description of a compression method
def get_compression_description(method: str) -> str:
    """
    Returns the description of the specified compression method
    
    Args:
        method: Name of the compression method
        
    Returns:
        Description of the compression method
    """
    descriptions = {
        'None': 'No compression',
        'gzip': 'General compression method, balanced compression ratio and speed',
        'zlib': 'Similar algorithm to gzip but with different headers',
        'bz2': 'Higher compression ratio but slower processing',
        'lzma': 'Highest compression ratio but slowest processing',
        'zstd': 'Facebook Zstandard - excellent compression ratio and speed',
        'lz4': 'Very fast compression algorithm with good compression ratio (frame format)',
        'lz4-block': 'Raw LZ4 block format, even faster but less compression',
        'bit': 'Simple bit compression (run-length encoding), effective for repetitive patterns',
        'huffman': 'Huffman coding, variable-length coding based on frequency'
    }
    return descriptions.get(method, 'No description')


def compress_file(file_path: str, output_path: str = None, method: str = 'zstd', compression_level: int = 6) -> str:
    """
    Compresses a file using the specified method
    
    Args:
        file_path: Path to the file to compress
        output_path: Path where the compressed file will be saved (adds extension if None)
        method: Compression method to use
        compression_level: Compression level
        
    Returns:
        Path to the compressed file
    """
    if output_path is None:
        output_path = f"{file_path}.{method}"
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    compressed = compress_data(data, method, compression_level)
    
    with open(output_path, 'wb') as f:
        f.write(compressed)
    
    return output_path


def decompress_file(file_path: str, output_path: str, method: str = 'zstd') -> str:
    """
    Decompresses a file using the specified method
    
    Args:
        file_path: Path to the compressed file
        output_path: Path where the decompressed file will be saved
        method: Compression method used
        
    Returns:
        Path to the decompressed file
    """
    with open(file_path, 'rb') as f:
        data = f.read()
    
    decompressed = decompress_data(data, method)
    
    with open(output_path, 'wb') as f:
        f.write(decompressed)
    
    return output_path