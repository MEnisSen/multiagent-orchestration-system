"""
Testing tools for the coding assistant system.
Contains functions for writing and running unit tests.
"""

import json
import subprocess
import sys
import os
from typing import Annotated, List
from pathlib import Path


def setup_test_environment(
    required_packages: Annotated[List[str], "List of Python packages needed for testing (e.g., ['numpy', 'requests==2.28.0'])"] = None
) -> str:
    """Set up or activate a virtual environment for testing with required packages."""
    try:
        workspace_path = Path(".agent_workspace")
        workspace_path.mkdir(exist_ok=True)
        
        venv_path = workspace_path / "test_venv"
        
        # Check if virtual environment already exists
        if venv_path.exists():
            # Virtual environment exists, get its info
            if sys.platform == "win32":
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"
            
            if python_exe.exists():
                venv_info = {
                    "status": "existing",
                    "message": f"Using existing virtual environment at {venv_path}",
                    "venv_path": str(venv_path),
                    "python_exe": str(python_exe),
                    "pip_exe": str(pip_exe)
                }
            else:
                # Corrupted venv, recreate
                import shutil
                shutil.rmtree(venv_path)
                return setup_test_environment(required_packages)
        else:
            # Create new virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to create virtual environment: {result.stderr}"
                })
            
            if sys.platform == "win32":
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"
            
            venv_info = {
                "status": "created",
                "message": f"Created new virtual environment at {venv_path}",
                "venv_path": str(venv_path),
                "python_exe": str(python_exe),
                "pip_exe": str(pip_exe)
            }
        
        # Install required packages if specified
        if required_packages:
            for package in required_packages:
                install_result = subprocess.run(
                    [str(pip_exe), "install", package],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if install_result.returncode != 0:
                    venv_info["warning"] = f"Failed to install {package}: {install_result.stderr}"
                    break
            else:
                venv_info["packages_installed"] = required_packages
        
        return json.dumps(venv_info)
        
    except subprocess.TimeoutExpired:
        return json.dumps({
            "status": "error",
            "message": "Virtual environment setup timed out"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error setting up test environment: {str(e)}"
        })


def write_unit_tests(
    function_name: Annotated[str, "Name of the function being tested"],
    test_code: Annotated[str, "Complete unittest code including test class and test methods"],
    function_file: Annotated[str, "Path to the file containing the function to test"]
) -> str:
    """Write unit tests for a function."""
    try:
        # Validate test code
        compile(test_code, '<string>', 'exec')
        
        temp_storage_path = Path(".agent_workspace")
        test_file = temp_storage_path / f"test_{function_name}.py"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        return json.dumps({
            "status": "success",
            "message": f"Unit tests for '{function_name}' created successfully",
            "test_file": str(test_file),
            "function_file": function_file
        })
    except SyntaxError as e:
        return json.dumps({
            "status": "error",
            "message": f"Syntax error in test code: {str(e)}",
            "error_line": e.lineno
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error creating unit tests: {str(e)}"
        })


def run_unit_tests(
    test_file: Annotated[str, "Path to the test file to run"],
    function_file: Annotated[str, "Path to the file containing the function being tested"],
    use_venv: Annotated[bool, "Whether to use the test virtual environment"] = True
) -> str:
    """Run unit tests and return the results."""
    try:
        # Determine which Python executable to use
        python_exe = sys.executable
        
        if use_venv:
            workspace_path = Path(".agent_workspace")
            venv_path = workspace_path / "test_venv"
            
            if venv_path.exists():
                if sys.platform == "win32":
                    venv_python = venv_path / "Scripts" / "python.exe"
                else:
                    venv_python = venv_path / "bin" / "python"
                
                if venv_python.exists():
                    python_exe = str(venv_python)
        
        # Run pytest or unittest
        result = subprocess.run(
            [python_exe, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # If pytest is not available, fall back to unittest
        if result.returncode == 1 and "No module named pytest" in result.stderr:
            result = subprocess.run(
                [python_exe, "-m", "unittest", test_file],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        output = result.stdout + result.stderr
        
        test_result = {
            "test_file": test_file,
            "python_exe": python_exe,
            "output": output
        }
        
        if result.returncode == 0:
            test_result.update({
                "status": "passed",
                "message": "All tests passed successfully"
            })
        else:
            test_result.update({
                "status": "failed",
                "message": "Some tests failed",
                "needs_fix": True
            })
        
        return json.dumps(test_result)
        
    except subprocess.TimeoutExpired:
        return json.dumps({
            "status": "error",
            "message": "Tests timed out after 30 seconds",
            "needs_fix": True
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error running tests: {str(e)}",
            "needs_fix": True
        })
