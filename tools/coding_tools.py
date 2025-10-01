"""
Coding tools for the coding assistant system.
Contains functions for creating and fixing functions.
"""

import json
from typing import Annotated
from pathlib import Path


def create_function(
    function_name: Annotated[str, "Name of the function to create"],
    function_code: Annotated[str, "Complete Python code for the function including docstring"],
    file_path: Annotated[str, "Path to the file where this function should be written"]
) -> str:
    """Create a new function and save it to the specified file."""
    try:
        # Validate the code by trying to compile it
        compile(function_code, '<string>', 'exec')
        
        # Store the function code temporarily for orchestrator review
        temp_storage_path = Path(".agent_workspace")
        temp_storage_path.mkdir(exist_ok=True)
        
        temp_file = temp_storage_path / f"{function_name}_temp.py"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(function_code)
        
        return json.dumps({
            "status": "success",
            "message": f"Function '{function_name}' created successfully",
            "temp_file": str(temp_file),
            "target_file": file_path,
            "function_name": function_name
        })
    except SyntaxError as e:
        return json.dumps({
            "status": "error",
            "message": f"Syntax error in function code: {str(e)}",
            "error_line": e.lineno,
            "error_text": e.text
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error creating function: {str(e)}"
        })


def fix_function(
    function_name: Annotated[str, "Name of the function to fix"],
    fixed_code: Annotated[str, "Fixed Python code for the function"],
    error_details: Annotated[str, "Details about what was wrong with the original code"]
) -> str:
    """Fix a problematic function based on test results or errors."""
    try:
        # Validate the fixed code
        compile(fixed_code, '<string>', 'exec')
        
        temp_storage_path = Path(".agent_workspace")
        temp_file = temp_storage_path / f"{function_name}_temp.py"
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
        
        return json.dumps({
            "status": "success",
            "message": f"Function '{function_name}' fixed successfully",
            "temp_file": str(temp_file),
            "fix_applied": error_details
        })
    except SyntaxError as e:
        return json.dumps({
            "status": "error",
            "message": f"Syntax error in fixed code: {str(e)}",
            "error_line": e.lineno
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error fixing function: {str(e)}"
        })


def finalize_function(
    function_name: Annotated[str, "Name of the function to finalize"],
    target_file: Annotated[str, "Target file path where the function should be added"],
    temp_file: Annotated[str, "Temporary file containing the approved function code"]
) -> str:
    """Finalize a function by adding it to the target file after tests pass."""
    try:
        # Read the function from temp file
        with open(temp_file, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        target_path = Path(target_file)
        
        # If target file exists, append; otherwise create new
        if target_path.exists():
            with open(target_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Add newlines for separation
            new_content = existing_content.rstrip() + "\n\n\n" + function_code
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            new_content = function_code
        
        # Write to target file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return json.dumps({
            "status": "success",
            "message": f"Function '{function_name}' finalized and added to {target_file}",
            "file": str(target_path)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error finalizing function: {str(e)}"
        })
