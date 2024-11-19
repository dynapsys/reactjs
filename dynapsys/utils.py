"""Utility functions for DynaPsys"""
import os
import sys
import logging
import subprocess
from typing import Tuple, Optional, List, Dict, Any
import json
from pathlib import Path

def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists and is writable.
    
    Args:
        path: Directory path to check/create
        
    Returns:
        bool: True if directory exists and is writable, False otherwise
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return os.access(path, os.W_OK)
    except Exception as e:
        logging.error(f"Error ensuring directory {path}: {str(e)}")
        return False

def run_command(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> Tuple[int, str, str]:
    """
    Run a shell command and return its output.
    
    Args:
        command: Command to run as list of strings
        cwd: Working directory for command
        env: Environment variables for command
        timeout: Command timeout in seconds
        
    Returns:
        Tuple[int, str, str]: Return code, stdout, and stderr
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
        
    except subprocess.TimeoutExpired:
        process.kill()
        logging.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        return -1, '', 'Command timed out'
    except Exception as e:
        logging.error(f"Error running command {' '.join(command)}: {str(e)}")
        return -1, '', str(e)

def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """
    Load and parse a JSON file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON data or None if error
    """
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file {path}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error reading file {path}: {str(e)}")
        return None

def save_json_file(path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        path: Path to save JSON file
        data: Data to save
        indent: JSON indentation level
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {path}: {str(e)}")
        return False

def is_port_in_use(port: int) -> bool:
    """
    Check if a port is in use.
    
    Args:
        port: Port number to check
        
    Returns:
        bool: True if port is in use, False otherwise
    """
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_free_port(start_port: int = 8000, max_port: int = 9000) -> Optional[int]:
    """
    Find a free port in a range.
    
    Args:
        start_port: Start of port range
        max_port: End of port range
        
    Returns:
        Optional[int]: Free port number or None if none found
    """
    for port in range(start_port, max_port + 1):
        if not is_port_in_use(port):
            return port
    return None

def get_system_info() -> Dict[str, str]:
    """
    Get system information.
    
    Returns:
        Dict[str, str]: System information
    """
    import platform
    return {
        'os': platform.system(),
        'os_release': platform.release(),
        'python_version': platform.python_version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'node': platform.node()
    }

def format_size(size: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"

def is_valid_domain(domain: str) -> bool:
    """
    Validate domain name format.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        log_file: Path to log file
        format_string: Log format string
    """
    if format_string is None:
        format_string = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=handlers
    )
