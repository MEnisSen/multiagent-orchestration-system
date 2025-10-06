"""
Task management tools for the orchestrator.
Contains functions for creating and managing task lists.
"""

import json
from typing import Annotated, List
from pathlib import Path


def create_task_list(
    tasks: Annotated[str, "JSON array string of task objects with 'description' field, e.g. '[{\"description\": \"Implement calculator\"}, {\"description\": \"Write tests\"}]'"]
) -> str:
    """
    Create a task list for the current workflow.
    Use this when breaking down a complex request into step-by-step tasks.
    Each task will be displayed in the UI task panel and marked as completed as work progresses.
    
    Returns a confirmation with the number of tasks created.
    """
    try:
        # Parse the tasks JSON string
        task_list = json.loads(tasks)
        
        if not isinstance(task_list, list):
            return json.dumps({
                "status": "error",
                "message": "Tasks must be a JSON array of task objects"
            })
        
        # Validate and format tasks
        formatted_tasks = []
        for i, task in enumerate(task_list):
            if isinstance(task, dict) and "description" in task:
                formatted_tasks.append({
                    "description": task["description"],
                    "status": "pending"
                })
            elif isinstance(task, str):
                # Allow simple string tasks
                formatted_tasks.append({
                    "description": task,
                    "status": "pending"
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Task {i} must have a 'description' field or be a string"
                })
        
        if not formatted_tasks:
            return json.dumps({
                "status": "error",
                "message": "Task list cannot be empty"
            })
        
        # Store tasks in a temporary location for the backend to pick up
        workspace = Path(".agent_workspace")
        workspace.mkdir(exist_ok=True)
        
        tasks_file = workspace / "_active_tasks.json"
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_tasks, f, indent=2)
        
        return json.dumps({
            "status": "success",
            "message": f"Created task list with {len(formatted_tasks)} tasks",
            "tasks": formatted_tasks,
            "task_count": len(formatted_tasks)
        })
        
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "message": f"Invalid JSON format for tasks: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error creating task list: {str(e)}"
        })


def update_task_status(
    task_index: Annotated[int, "Index of the task to update (0-based)"],
    status: Annotated[str, "New status: 'pending', 'in_progress', or 'completed'"]
) -> str:
    """
    Update the status of a specific task in the task list.
    Use this to mark tasks as in-progress or completed as work progresses.
    """
    try:
        workspace = Path(".agent_workspace")
        tasks_file = workspace / "_active_tasks.json"
        
        if not tasks_file.exists():
            return json.dumps({
                "status": "error",
                "message": "No active task list found. Create one first with create_task_list."
            })
        
        # Read current tasks
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        if task_index < 0 or task_index >= len(tasks):
            return json.dumps({
                "status": "error",
                "message": f"Task index {task_index} out of range (0-{len(tasks)-1})"
            })
        
        if status not in ["pending", "in_progress", "completed"]:
            return json.dumps({
                "status": "error",
                "message": "Status must be 'pending', 'in_progress', or 'completed'"
            })
        
        # Update task status
        tasks[task_index]["status"] = status
        
        # Save updated tasks
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)
        
        return json.dumps({
            "status": "success",
            "message": f"Updated task {task_index} to '{status}'",
            "task": tasks[task_index]
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error updating task status: {str(e)}"
        })

