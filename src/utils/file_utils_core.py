"""
Core utilities providing basic file operation functionality with enhanced pathlib usage

Main features:
- Getting the execution directory
- Getting the project root
- Managing the tmp directory
- Advanced path operations
"""

import os
import shutil
from pathlib import Path
from typing import Union, List, Iterable, Optional


def get_execution_directory() -> Path:
    """
    Get the current execution directory.
    
    Returns:
        Path: Path of the execution directory
    """
    return Path(__file__).parent.absolute()


def get_project_root() -> Path:
    """
    Get the root directory of the project.
    
    Returns:
        Path: Path to the project root
    """
    # Project root is 2 levels up from utils/file_utils_core.py
    # (utils -> src -> project_root)
    return Path(__file__).parent.parent.parent


def get_tmp_directory() -> Path:
    """
    Get the path to the tmp directory.
    Creates it if it doesn't exist.
    
    Returns:
        Path: Path to the tmp directory
    """
    tmp_dir = get_project_root() / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def ensure_directory(directory: Union[str, Path]) -> Path:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
    
    Returns:
        Path: Path to the directory
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
    """
    List files in a directory matching a pattern.
    
    Args:
        directory: Path to the directory
        pattern: Glob pattern for matching files
        recursive: Whether to search recursively
    
    Returns:
        List[Path]: List of matching file paths
    """
    path = Path(directory)
    
    if recursive:
        return list(path.glob(f"**/{pattern}"))
    else:
        return list(path.glob(pattern))


def remove_directory(directory: Union[str, Path], ignore_errors: bool = False) -> None:
    """
    Remove a directory and all its contents.
    
    Args:
        directory: Path to the directory
        ignore_errors: Whether to ignore errors
    """
    path = Path(directory)
    if path.exists():
        shutil.rmtree(path, ignore_errors=ignore_errors)


def copy_files(files: Iterable[Union[str, Path]], destination: Union[str, Path]) -> List[Path]:
    """
    Copy multiple files to a destination directory.
    
    Args:
        files: Iterable of file paths
        destination: Destination directory
    
    Returns:
        List[Path]: Paths to the copied files
    """
    dest_dir = Path(destination)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    copied_files = []
    for file in files:
        src_path = Path(file)
        if src_path.exists():
            dest_file = dest_dir / src_path.name
            shutil.copy2(src_path, dest_file)
            copied_files.append(dest_file)
    
    return copied_files


def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Optional[int]: Size of the file in bytes, or None if the file does not exist
    """
    path = Path(file_path)
    if path.exists() and path.is_file():
        return path.stat().st_size
    return None