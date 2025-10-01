"""
File operation tools for the coding assistant system.
Contains functions for reading, writing, and listing files/directories.
"""

import os
from typing import Annotated
from pathlib import Path


def read_file(file_path: Annotated[str, "Path to the file to read"]) -> str:
    """Read the contents of a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"Content of {file_path}:\n```\n{content}\n```"
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"


def list_directory(dir_path: Annotated[str, "Path to the directory to list"] = ".") -> str:
    """List all files and directories in the specified path."""
    try:
        path = Path(dir_path)
        if not path.exists():
            return f"Error: Directory '{dir_path}' does not exist."
        
        items = []
        for item in path.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"  [{item_type}] {item.name}")
        
        return f"Contents of {dir_path}:\n" + "\n".join(sorted(items))
    except Exception as e:
        return f"Error listing directory '{dir_path}': {str(e)}"


def write_file(
    file_path: Annotated[str, "Path to the file to write"],
    content: Annotated[str, "Content to write to the file"]
) -> str:
    """Write content to a file. Creates the file if it doesn't exist."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file '{file_path}': {str(e)}"
