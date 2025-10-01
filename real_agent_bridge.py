"""
Real integration bridge between the frontend and the actual agent system.
This connects to your actual Orchestrator, Coder, and Tester agents.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import time
import asyncio
import threading
from datetime import datetime
import uuid
import os

# Import your actual agent system
from agents import create_coding_agents
from programmatic_agent_runner import run_agent_workflow_programmatic, extract_agent_communications, extract_tasks_from_messages

app = FastAPI(title="Real Agent Communication Bridge")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
messages_store = []
tasks_store = []
files_store = []
current_task_index = 0
workflow_status = "idle"
agents_dict = {}
current_conversation = []
workflow_thread = None
workflow_running = False

class PromptRequest(BaseModel):
    prompt: str

def initialize_agents():
    """Initialize the actual agent system."""
    global agents_dict
    try:
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY environment variable not set")
            print("   Please set it using: export OPENAI_API_KEY='your-api-key-here'")
            return False
        
        agents_dict = create_coding_agents()
        print(f"✓ Initialized {len(agents_dict)} agents: {list(agents_dict.keys())}")
        return True
    except Exception as e:
        print(f"❌ Error initializing agents: {e}")
        if "api_key" in str(e).lower():
            print("   Make sure OPENAI_API_KEY environment variable is set")
        return False

# Message conversion functions are now in programmatic_agent_runner.py

def run_agent_workflow(prompt: str):
    """Run the actual agent workflow in a separate thread."""
    global workflow_status, current_conversation, messages_store, tasks_store, workflow_running, current_task_index
    
    try:
        workflow_running = True
        workflow_status = "planning"
        current_task_index = 0
        
        # Clear previous state
        current_conversation = []
        messages_store = []
        tasks_store = []
        
        print(f"🚀 Starting agent workflow with prompt: {prompt}")
        
        # Run the actual agent workflow programmatically
        if agents_dict:
            workflow_status = "coding"
            
            # Use the programmatic runner
            conversation_history = run_agent_workflow_programmatic(
                agents=agents_dict,
                initial_prompt=prompt,
                starting_agent_name="Orchestrator Agent",
                max_iterations=15
            )
            
            # Store the raw conversation
            current_conversation = conversation_history
            
            # Convert to frontend format
            frontend_messages = extract_agent_communications(conversation_history)
            messages_store.extend(frontend_messages)
            
            # Extract tasks from conversation
            extracted_tasks = extract_tasks_from_messages(conversation_history)
            tasks_store.extend(extracted_tasks)
            
            # Update task progress based on workflow
            if len(tasks_store) > 0:
                # Mark first task as completed (planning)
                tasks_store[0]["status"] = "completed"
                current_task_index = 1
                
                # If we have evidence of coding activity, mark coding tasks as completed
                if any("create_function" in str(msg) or "fix_function" in str(msg) for msg in conversation_history):
                    if len(tasks_store) > 1:
                        tasks_store[1]["status"] = "completed"
                        current_task_index = 2
                
                # If we have evidence of testing activity, mark testing tasks as completed
                if any("test" in str(msg).lower() or "unit_test" in str(msg) for msg in conversation_history):
                    if len(tasks_store) > 2:
                        tasks_store[2]["status"] = "completed"
                        current_task_index = 3
                
                # If workflow seems complete
                if any("finalize" in str(msg).lower() or "completed" in str(msg).lower() for msg in conversation_history):
                    for task in tasks_store:
                        task["status"] = "completed"
                    current_task_index = len(tasks_store)
            
            workflow_status = "completed"
            print("✓ Agent workflow completed")
        else:
            print("❌ No agents available")
            workflow_status = "error"
            
    except Exception as e:
        print(f"❌ Error in agent workflow: {e}")
        import traceback
        traceback.print_exc()
        workflow_status = "error"
    finally:
        workflow_running = False

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup."""
    print("🚀 Starting Real Agent Bridge...")
    success = initialize_agents()
    if success:
        print("✓ Agent system ready")
    else:
        print("❌ Agent system failed to initialize")

@app.get("/agents")
async def get_agents():
    """Get list of available agents."""
    if not agents_dict:
        initialize_agents()
    
    # If agents failed to initialize, return default structure for demo
    if not agents_dict:
        return {
            "status": "success",
            "agents": [
                {
                    "id": "orchestrator",
                    "name": "Orchestrator Agent",
                    "capabilities": ["coordinate_workflow", "parse_requests", "manage_tasks"],
                    "model": {"provider": "openai", "id": "gpt-4o-mini"},
                    "tools": ["read_file", "list_directory", "finalize_function", "transfer_to_coder_agent", "transfer_to_tester_agent"],
                    "description": "Manages the entire coding workflow (API key required for actual use)"
                },
                {
                    "id": "coder",
                    "name": "Coder Agent", 
                    "capabilities": ["implement_functions", "fix_code"],
                    "model": {"provider": "openai", "id": "gpt-4o-mini"},
                    "tools": ["create_function", "fix_function", "transfer_to_orchestrator_agent"],
                    "description": "Implements functions and fixes code (API key required for actual use)"
                },
                {
                    "id": "tester",
                    "name": "Tester Agent",
                    "capabilities": ["write_tests", "run_tests", "setup_environment"],
                    "model": {"provider": "openai", "id": "gpt-4o-mini"},
                    "tools": ["setup_test_environment", "write_unit_tests", "run_unit_tests", "transfer_to_orchestrator_agent"],
                    "description": "Writes and runs tests (API key required for actual use)"
                }
            ]
        }
    
    # Convert your agents to frontend format
    frontend_agents = []
    for agent_name, agent in agents_dict.items():
        config = agent.get_config()
        
        # Map agent names to frontend IDs
        agent_id = agent_name.lower().replace(" agent", "").replace(" ", "_")
        
        frontend_agent = {
            "id": agent_id,
            "name": agent_name,
            "capabilities": [],  # Would need to extract from agent
            "model": {
                "provider": "openai",
                "id": config.get("model", "gpt-4o-mini")
            },
            "tools": config.get("tool_names", []),
            "description": f"Agent: {agent_name}"
        }
        frontend_agents.append(frontend_agent)
    
    return {
        "status": "success",
        "agents": frontend_agents
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
    # Check .agent_workspace for files
    workspace_path = ".agent_workspace"
    files = []
    
    if os.path.exists(workspace_path):
        for filename in os.listdir(workspace_path):
            if filename.endswith(('.py', '.txt')):
                file_path = os.path.join(workspace_path, filename)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    files.append({
                        "name": filename,
                        "path": file_path,
                        "size": len(content),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                        "content": content[:500] + "..." if len(content) > 500 else content
                    })
                except Exception as e:
                    print(f"Error reading file {filename}: {e}")
    
    return {
        "status": "success",
        "files": files
    }

@app.get("/status")
async def get_status():
    """Get system status."""
    return {
        "status": "success",
        "system_status": {
            "agents_active": len(agents_dict),
            "messages_count": len(messages_store),
            "tasks_count": len(tasks_store),
            "workflow_status": workflow_status,
            "workflow_running": workflow_running
        }
    }

@app.post("/submit-prompt")
async def submit_prompt(request: PromptRequest, background_tasks: BackgroundTasks):
    """Submit a user prompt to start the actual agent workflow."""
    global workflow_status, current_task_index, workflow_running
    
    if workflow_running:
        return {
            "status": "error",
            "message": "Workflow already running"
        }
    
    # Check if agents are available
    if not agents_dict:
        initialize_agents()
    
    if not agents_dict:
        return {
            "status": "error",
            "message": "Agents not available. Please set OPENAI_API_KEY environment variable."
        }
    
    # Reset state
    current_task_index = 0
    workflow_status = "planning"
    
    # Start the workflow in background
    background_tasks.add_task(run_agent_workflow, request.prompt)
    
    return {
        "status": "success",
        "message": "Workflow started"
    }

@app.post("/reset")
async def reset_system():
    """Reset the system state."""
    global workflow_status, current_task_index, messages_store, tasks_store, files_store, current_conversation, workflow_running
    
    workflow_running = False
    messages_store.clear()
    tasks_store.clear()
    files_store.clear()
    current_conversation.clear()
    current_task_index = 0
    workflow_status = "idle"
    
    return {
        "status": "success",
        "message": "System reset successfully"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Real Agent Communication Bridge...")
    print("📡 Frontend can connect to: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
