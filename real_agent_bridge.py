"""
Real integration bridge between the frontend and the actual agent system.
This connects to your actual Orchestrator, Coder, and Tester agents.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
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
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import your actual agent system
from agents import create_coding_agents
from programmatic_agent_runner import run_agent_workflow_programmatic, extract_agent_communications, extract_tasks_from_messages
from document_processor_v2 import process_uploaded_documents_v2, combine_prompt_with_documents_v2

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
    documents: Optional[List[str]] = None  # List of document filenames

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
    """Run the actual agent workflow in a separate thread, streaming updates."""
    global workflow_status, current_conversation, messages_store, tasks_store, workflow_running, current_task_index
    
    try:
        workflow_running = True
        workflow_status = "planning"
        current_task_index = 0
        tasks_extracted = False  # Flag to extract tasks only once from initial plan
        
        # Clear previous state
        current_conversation = []
        messages_store = []
        tasks_store = []
        
        print(f"🚀 Starting agent workflow with prompt: {prompt}")
        
        if not agents_dict:
            print("❌ No agents available")
            workflow_status = "error"
            return
        
        # Initialize conversation with the user's prompt and stream immediately
        messages = [{"role": "user", "content": prompt}]
        current_conversation.extend(messages)
        messages_store.extend(extract_agent_communications(messages))
        
        # Begin workflow
        workflow_status = "coding"
        current_agent_name = "Orchestrator Agent"
        iterations = 0
        max_iterations = 30
        no_handoff_count = 0
        
        while iterations < max_iterations:
            agent = agents_dict.get(current_agent_name)
            if not agent:
                print(f"❌ Agent not found: {current_agent_name}")
                break
            
            # Run agent step
            next_agent_name, new_messages = agent.run(messages)
            
            # Update buffers
            messages.extend(new_messages)
            current_conversation.extend(new_messages)
            
            # Stream new messages to frontend immediately
            for msg in new_messages:
                msgs = extract_agent_communications([msg])
                messages_store.extend(msgs)
                
                # Check for task list created by the Orchestrator using create_task_list tool
                tasks_file = Path(".agent_workspace") / "_active_tasks.json"
                if tasks_file.exists() and not tasks_extracted:
                    try:
                        with open(tasks_file, 'r', encoding='utf-8') as f:
                            loaded_tasks = json.load(f)
                            if loaded_tasks:
                                tasks_store = loaded_tasks
                                tasks_extracted = True
                                print(f"📋 Loaded {len(tasks_store)} tasks from task list")
                    except Exception as e:
                        print(f"Warning: Could not load tasks from file: {e}")
            
            iterations += 1
            # Track whether we're handing off; if not, allow a few self-steps before stopping
            if next_agent_name == current_agent_name:
                no_handoff_count += 1
            else:
                no_handoff_count = 0
            current_agent_name = next_agent_name
            
            # Small sleep to avoid tight loop (and allow UI to poll)
            import time
            time.sleep(0.05)
            
            # Stop if no handoff occurs repeatedly (prevents getting stuck after tool results)
            if no_handoff_count >= 3:
                break
        
        workflow_status = "completed"
        print("✓ Agent workflow completed")
        
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
                    "tools": ["read_file", "list_directory", "finalize_function", "transfer_to_coder_agent", "transfer_to_tester_agent", "transfer_to_database_agent"],
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
                },
                {
                    "id": "database",
                    "name": "Database Agent",
                    "capabilities": ["update_knowledge_graph", "retrieve_from_graph"],
                    "model": {"provider": "openai", "id": "gpt-4o-mini"},
                    "tools": ["kg_updater", "kg_retriever", "transfer_to_orchestrator_agent"],
                    "description": "Manages Neo4j knowledge graph updates and retrievals (API key required for actual use)"
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
    # Check if there's a task file created by the Orchestrator
    tasks_file = Path(".agent_workspace") / "_active_tasks.json"
    current_tasks = tasks_store
    
    if tasks_file.exists():
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                current_tasks = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load tasks from file: {e}")
    
    return {
        "status": "success",
        "tasks": current_tasks,
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

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents, returning processed markdown content."""
    try:
        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp(prefix="agent_docs_")
        file_paths = []
        filenames = []
        
        for file in files:
            # Save uploaded file to temporary location
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_paths.append(file_path)
            filenames.append(file.filename)
        
        # Process documents with vllm-based Granite model
        document_markdowns = await process_uploaded_documents_v2(file_paths, filenames)
        
        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return {
            "status": "success",
            "documents": document_markdowns,
            "filenames": filenames
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing documents: {str(e)}"
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
    
    # Process documents if provided
    final_prompt = request.prompt
    if request.documents:
        # Documents are already processed markdown content
        document_markdowns = request.documents
        final_prompt = combine_prompt_with_documents_v2(request.prompt, document_markdowns)
    
    # Start the workflow in background
    background_tasks.add_task(run_agent_workflow, final_prompt)
    
    return {
        "status": "success",
        "message": "Workflow started"
    }

@app.post("/reset")
async def reset_system():
    """Reset the system state and clear workspace."""
    global workflow_status, current_task_index, messages_store, tasks_store, files_store, current_conversation, workflow_running
    
    workflow_running = False
    messages_store.clear()
    tasks_store.clear()
    files_store.clear()
    current_conversation.clear()
    current_task_index = 0
    workflow_status = "idle"
    
    # Clear .agent_workspace directory
    workspace_path = Path(".agent_workspace")
    if workspace_path.exists():
        try:
            for item in workspace_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        except Exception as e:
            print(f"Warning: Could not fully clear workspace: {e}")
    
    return {
        "status": "success",
        "message": "System reset successfully - workspace cleared"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Real Agent Communication Bridge...")
    print("📡 Frontend can connect to: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
