"""
Simple FastAPI bridge to connect the frontend with the current agent system.
This provides the API endpoints that the frontend expects.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime
import uuid

app = FastAPI(title="Agent Communication Bridge")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo purposes
messages_store = []
tasks_store = []
files_store = []
current_task_index = 0
workflow_status = "idle"

class PromptRequest(BaseModel):
    prompt: str

# Mock agent data matching the frontend structure
AGENTS_DATA = [
    {
        "id": "orchestrator",
        "capabilities": ["coordinate_workflow", "parse_requests", "manage_tasks", "finalize_functions"],
        "model": {
            "provider": "openai",
            "id": "gpt-4o-mini"
        },
        "tools": ["read_file", "list_directory", "finalize_function", "transfer_to_coder_agent", "transfer_to_tester_agent"],
        "description": "Manages the entire coding workflow and coordinates between other agents"
    },
    {
        "id": "coder", 
        "capabilities": ["implement_functions", "fix_code", "write_documentation"],
        "model": {
            "provider": "openai",
            "id": "gpt-4o-mini"
        },
        "tools": ["create_function", "fix_function", "transfer_to_orchestrator_agent"],
        "description": "Implements functions and fixes code issues based on specifications"
    },
    {
        "id": "tester",
        "capabilities": ["write_tests", "run_tests", "setup_environment", "analyze_failures"],
        "model": {
            "provider": "openai", 
            "id": "gpt-4o-mini"
        },
        "tools": ["setup_test_environment", "write_unit_tests", "run_unit_tests", "transfer_to_orchestrator_agent"],
        "description": "Writes comprehensive unit tests and validates code functionality"
    }
]

def create_message(from_agent: str, to_agent: str, message_type: str, content: str, tools_used: List[str] = None):
    """Create a message in the format expected by the frontend."""
    return {
        "id": str(uuid.uuid4()),
        "from": from_agent,
        "to": to_agent,
        "type": message_type,
        "content": content,
        "tools_used": tools_used or [],
        "timestamp": datetime.now().isoformat(),
        "status": "ok"
    }

@app.get("/agents")
async def get_agents():
    """Get list of available agents."""
    return {
        "status": "success",
        "agents": AGENTS_DATA
    }

@app.get("/messages")
async def get_messages(limit: int = 50):
    """Get recent messages."""
    return {
        "status": "success",
        "messages": messages_store[-limit:] if messages_store else []
    }

@app.get("/tasks")
async def get_tasks():
    """Get current tasks."""
    return {
        "status": "success",
        "tasks": tasks_store,
        "currentTaskIndex": current_task_index,
        "workflowStatus": workflow_status
    }

@app.get("/files")
async def get_files():
    """Get generated files."""
    return {
        "status": "success",
        "files": files_store
    }

@app.get("/status")
async def get_status():
    """Get system status."""
    return {
        "status": "success",
        "system_status": {
            "agents_active": len(AGENTS_DATA),
            "messages_count": len(messages_store),
            "tasks_count": len(tasks_store),
            "workflow_status": workflow_status
        }
    }

@app.post("/submit-prompt")
async def submit_prompt(request: PromptRequest):
    """Submit a user prompt to start the workflow."""
    global workflow_status, current_task_index
    
    # Reset state
    messages_store.clear()
    tasks_store.clear()
    files_store.clear()
    current_task_index = 0
    workflow_status = "planning"
    
    # Create initial user message
    user_message = create_message("user", "orchestrator", "request", request.prompt)
    messages_store.append(user_message)
    
    # Simulate orchestrator response
    orchestrator_response = create_message(
        "orchestrator", "user", "plan", 
        f"I'll help you with: {request.prompt}. Let me break this down into tasks.",
        ["read_file", "list_directory"]
    )
    messages_store.append(orchestrator_response)
    
    # Create sample tasks
    tasks_store.extend([
        {"description": f"Analyze requirements for: {request.prompt}", "status": "pending"},
        {"description": "Create function implementation", "status": "pending"},
        {"description": "Write comprehensive tests", "status": "pending"},
        {"description": "Finalize and integrate code", "status": "pending"}
    ])
    
    workflow_status = "coding"
    
    return {
        "status": "success",
        "message": "Prompt submitted successfully"
    }

@app.post("/next-task")
async def next_task():
    """Move to next task (debug function)."""
    global current_task_index, workflow_status
    
    if current_task_index < len(tasks_store) - 1:
        current_task_index += 1
        
        # Simulate agent communication
        if current_task_index == 1:  # Coder task
            coder_message = create_message(
                "orchestrator", "coder", "request",
                "Please implement the requested function",
                ["transfer_to_coder_agent"]
            )
            messages_store.append(coder_message)
            
            coder_response = create_message(
                "coder", "orchestrator", "response",
                "Function implemented successfully",
                ["create_function"]
            )
            messages_store.append(coder_response)
            
        elif current_task_index == 2:  # Tester task
            tester_message = create_message(
                "orchestrator", "tester", "request",
                "Please write and run tests for the function",
                ["transfer_to_tester_agent"]
            )
            messages_store.append(tester_message)
            
            tester_response = create_message(
                "tester", "orchestrator", "response",
                "Tests written and executed successfully",
                ["setup_test_environment", "write_unit_tests", "run_unit_tests"]
            )
            messages_store.append(tester_response)
            
        elif current_task_index == 3:  # Finalization
            final_message = create_message(
                "orchestrator", "user", "response",
                "All tasks completed successfully!",
                ["finalize_function"]
            )
            messages_store.append(final_message)
            workflow_status = "completed"
    
    return {
        "status": "success",
        "currentTaskIndex": current_task_index,
        "workflowStatus": workflow_status
    }

@app.post("/reset")
async def reset_system():
    """Reset the system state."""
    global workflow_status, current_task_index
    
    messages_store.clear()
    tasks_store.clear()
    files_store.clear()
    current_task_index = 0
    workflow_status = "idle"
    
    return {
        "status": "success",
        "message": "System reset successfully"
    }

@app.post("/demo/full-cycle")
async def demo_full_cycle():
    """Run a full demo cycle."""
    # This would integrate with your actual agent system
    # For now, just simulate the workflow
    
    await submit_prompt(PromptRequest(prompt="Create a calculator function"))
    
    # Simulate progression through tasks
    for _ in range(len(tasks_store)):
        await next_task()
        time.sleep(0.5)  # Small delay for demo effect
    
    return {
        "status": "success",
        "message": "Full demo cycle completed"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Agent Communication Bridge...")
    print("📡 Frontend can connect to: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
