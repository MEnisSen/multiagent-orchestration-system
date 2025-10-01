"""
Programmatic agent runner that can be used by the web interface.
This is a modified version of run_agent_loop that doesn't require interactive input.
"""

from typing import Dict, List
from agents.base_agent import BaseAgent


def run_agent_workflow_programmatic(
    agents: Dict[str, BaseAgent], 
    initial_prompt: str,
    starting_agent_name: str = None,
    max_iterations: int = 20
) -> List[Dict[str, str]]:
    """
    Run a multi-agent conversation loop programmatically.
    
    Args:
        agents: Dictionary mapping agent names to agent instances
        initial_prompt: The user's initial request
        starting_agent_name: Name of the first agent to run (optional)
        max_iterations: Maximum number of iterations to prevent infinite loops
        
    Returns:
        Complete conversation history as list of message dicts
    """
    if not agents:
        raise ValueError("No agents provided")
    
    current_agent_name = starting_agent_name or list(agents.keys())[0]
    messages = []
    iterations = 0
    
    # Add the initial user prompt
    messages.append({"role": "user", "content": initial_prompt})
    
    print(f"🚀 Starting workflow with: {initial_prompt}")
    print(f"📋 Available agents: {list(agents.keys())}")
    print("-" * 50)
    
    while iterations < max_iterations:
        agent = agents.get(current_agent_name)
        if not agent:
            print(f"❌ Error: Agent '{current_agent_name}' not found")
            break
        
        print(f"\n🤖 Running {current_agent_name}...")
        
        try:
            # Run the agent
            next_agent_name, new_messages = agent.run(messages)
            messages.extend(new_messages)
            
            # Check if we should continue
            if next_agent_name == current_agent_name:
                # Agent didn't hand off, check if we need more input
                last_message = messages[-1] if messages else None
                if (last_message and 
                    last_message.get("role") == "assistant" and 
                    not any("transfer" in str(msg).lower() for msg in new_messages)):
                    # Agent is waiting for input but we're in programmatic mode
                    print(f"✓ {current_agent_name} completed its task")
                    break
            
            current_agent_name = next_agent_name
            iterations += 1
            
            # Add a small delay to prevent overwhelming the system
            import time
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error running {current_agent_name}: {e}")
            break
    
    if iterations >= max_iterations:
        print(f"\n⚠️ Reached maximum iterations ({max_iterations}). Ending workflow.")
    else:
        print(f"\n✅ Workflow completed after {iterations} iterations.")
    
    print(f"📝 Generated {len(messages)} messages total")
    return messages


def extract_agent_communications(messages: List[Dict[str, str]]) -> List[Dict]:
    """
    Extract and format agent communications for the frontend.
    """
    communications = []
    
    for i, msg in enumerate(messages):
        # Determine the communication type and participants
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        # Extract tool usage
        tools_used = []
        if "tool_calls" in msg:
            for tool_call in msg.get("tool_calls", []):
                if "function" in tool_call:
                    tools_used.append(tool_call["function"]["name"])
        
        # Determine message type
        message_type = "response"
        if role == "user":
            message_type = "request"
        elif "transfer" in content.lower() or "handoff" in content.lower():
            message_type = "handoff"
        elif any(tool in content.lower() for tool in ["create_function", "fix_function"]):
            message_type = "code"
        elif any(tool in content.lower() for tool in ["test", "unit_test"]):
            message_type = "test"
        elif "finalize" in content.lower():
            message_type = "finalize"
        
        # Determine from/to agents
        from_agent = "unknown"
        to_agent = "unknown"
        
        if role == "user":
            from_agent = "user"
            to_agent = "orchestrator"
        elif role == "assistant":
            # Try to determine which agent based on content
            if "orchestrator" in content.lower() or i == 1:  # First response usually orchestrator
                from_agent = "orchestrator"
                to_agent = "user"
            elif "coder" in content.lower() or any(tool in tools_used for tool in ["create_function", "fix_function"]):
                from_agent = "coder"
                to_agent = "orchestrator"
            elif "tester" in content.lower() or any(tool in tools_used for tool in ["write_unit_tests", "run_unit_tests"]):
                from_agent = "tester"
                to_agent = "orchestrator"
            else:
                from_agent = "orchestrator"  # Default
                to_agent = "user"
        elif role == "tool":
            from_agent = "system"
            to_agent = "orchestrator"
        
        communication = {
            "id": f"msg_{i}",
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "content": content,
            "tools_used": tools_used,
            "timestamp": f"2024-01-01T{10 + i//60:02d}:{i%60:02d}:00",  # Mock timestamp
            "status": "ok",
            "raw_message": msg
        }
        
        communications.append(communication)
    
    return communications


def extract_tasks_from_messages(messages: List[Dict[str, str]]) -> List[Dict]:
    """
    Extract task information from the conversation.
    """
    tasks = []
    
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            # Look for task-related content
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                # Look for numbered lists, bullet points, or task keywords
                if (any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '- ', '* ']) or
                    any(keyword in line.lower() for keyword in ['task', 'step', 'implement', 'create', 'write', 'test'])):
                    if len(line) > 15 and not line.startswith('```'):  # Avoid code blocks and very short lines
                        # Clean up the line
                        clean_line = line.lstrip('1234567890.- *').strip()
                        if clean_line and len(clean_line) > 10:
                            tasks.append({
                                "description": clean_line,
                                "status": "pending"
                            })
    
    # Remove duplicates and limit
    seen = set()
    unique_tasks = []
    for task in tasks:
        desc = task["description"].lower()
        if desc not in seen and len(unique_tasks) < 6:
            seen.add(desc)
            unique_tasks.append(task)
    
    # If no tasks found, create default workflow tasks
    if not unique_tasks:
        unique_tasks = [
            {"description": "Parse user request and create implementation plan", "status": "pending"},
            {"description": "Implement the requested functionality", "status": "pending"},
            {"description": "Write comprehensive unit tests", "status": "pending"},
            {"description": "Run tests and validate functionality", "status": "pending"},
            {"description": "Finalize and integrate the code", "status": "pending"}
        ]
    
    return unique_tasks
