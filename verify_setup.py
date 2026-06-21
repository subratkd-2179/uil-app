#!/usr/bin/env python
"""
UIL Tutor AI - Setup Verification Script
Verify that all components are properly installed and configured
"""

import os
import sys
import subprocess
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_status(status, message):
    """Print status message with color"""
    if status == 'ok':
        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
    elif status == 'error':
        print(f"{Colors.RED}✗{Colors.RESET} {message}")
    elif status == 'warning':
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
    else:
        print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_status('ok', f"Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_status('error', f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_status('ok', f"{description} found: {filepath}")
        return True
    else:
        print_status('error', f"{description} not found: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    if os.path.isdir(dirpath):
        print_status('ok', f"{description} exists: {dirpath}")
        return True
    else:
        print_status('warning', f"{description} not found: {dirpath}")
        return False

def check_python_package(package_name):
    """Check if a Python package is installed"""
    try:
        __import__(package_name)
        print_status('ok', f"Package '{package_name}' is installed")
        return True
    except ImportError:
        print_status('error', f"Package '{package_name}' is NOT installed")
        return False

def check_port_available(port=5000):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result != 0:
        print_status('ok', f"Port {port} is available")
        return True
    else:
        print_status('warning', f"Port {port} is already in use")
        return False

def verify_setup():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("UIL Tutor AI - Setup Verification")
    print("="*60 + "\n")
    
    all_ok = True
    
    # Check Python version
    print(f"{Colors.BLUE}Checking Python Environment...{Colors.RESET}")
    if not check_python_version():
        all_ok = False
    print()
    
    # Check required files
    print(f"{Colors.BLUE}Checking Required Files...{Colors.RESET}")
    files_to_check = [
        ('UI/uil-tutor-ai.html', 'HTML Interface'),
        ('UI/app.js', 'Frontend JavaScript'),
        ('API/app.py', 'Backend API Server'),
        ('API/utils.py', 'Utility Functions'),
        ('API/requirements.txt', 'Python Dependencies'),
        ('README.md', 'Main Documentation'),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_ok = False
    print()
    
    # Check directories
    print(f"{Colors.BLUE}Checking Directories...{Colors.RESET}")
    dirs_to_check = [
        ('UI', 'UI Directory'),
        ('API', 'API Directory'),
    ]
    
    for dirpath, description in dirs_to_check:
        if not check_directory_exists(dirpath, description):
            all_ok = False
    print()
    
    # Check Python packages
    print(f"{Colors.BLUE}Checking Python Packages...{Colors.RESET}")
    packages = ['flask', 'flask_cors', 'werkzeug']
    packages_ok = True
    
    for package in packages:
        if not check_python_package(package):
            packages_ok = False
    
    if not packages_ok:
        print_status('warning', "Some packages not installed. Run: pip install -r API/requirements.txt")
    print()
    
    # Check port availability
    print(f"{Colors.BLUE}Checking Port Availability...{Colors.RESET}")
    if not check_port_available(5000):
        print_status('warning', "Port 5000 might be in use. Server may fail to start.")
    print()
    
    # Final status
    print("="*60)
    if all_ok and packages_ok:
        print_status('ok', "Setup verification PASSED! ✓")
        print("\nYou can now:")
        print("1. Run: python API/app.py (to start the backend)")
        print("2. Open: UI/uil-tutor-ai.html (in your browser)")
    else:
        print_status('error', "Setup verification found issues!")
        print("\nFix the issues above, then try again.")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        # Change to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        verify_setup()
    except Exception as e:
        print_status('error', f"Verification failed: {e}")
        sys.exit(1)
