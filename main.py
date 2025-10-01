"""
Main script to run the coding assistant system.
This orchestrates multiple agents to help with code creation, testing, and finalization.
"""

import os
from pathlib import Path
from agents import create_coding_agents, run_agent_loop


def setup_workspace():
    """Create necessary workspace directories."""
    workspace = Path(".agent_workspace")
    workspace.mkdir(exist_ok=True)
    print(f"✓ Workspace created at: {workspace.absolute()}")


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          🤖 AI CODING ASSISTANT SYSTEM 🤖                 ║
║                                                           ║
║  Multi-Agent System for Code Generation and Testing       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Available Agents:
  🎯 Orchestrator Agent - Manages workflow and coordinates tasks
  💻 Coder Agent        - Implements and fixes functions  
  🧪 Tester Agent       - Writes and runs unit tests

How it works:
  1. Describe what you need (new function or modify existing)
  2. Orchestrator will analyze and create a task plan
  3. Coder implements the function
  4. Tester writes and runs unit tests
  5. If tests pass, code is finalized to target file
  6. If tests fail, Coder fixes the issues

Example requests:
  • "Create a function to calculate fibonacci numbers in utils.py"
  • "Add a function to validate email addresses in validators.py"
  • "Create multiple helper functions for string manipulation"
"""
    print(banner)


def main():
    """Main entry point for the coding assistant."""
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("\nPlease set it using:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Setup
    print_banner()
    setup_workspace()
    
    print("\n" + "="*60)
    print("Initializing agents...")
    print("="*60)
    
    # Create agents
    # You can customize models for each agent
    agents = create_coding_agents(
        orchestrator_model="gpt-4o-mini",  # Can use "gpt-4" for better planning
        coder_model="gpt-4o-mini",         # Can use "gpt-4" for better code
        tester_model="gpt-4o-mini"         # Can use "gpt-4" for better tests
    )
    
    # For using Ollama for specific agents (uncomment and adjust):
    # agents = create_coding_agents(
    #     orchestrator_model="gpt-4o-mini",
    #     coder_model="gpt-4o-mini",
    #     tester_model="llama3.2:3b",  # Use local model for testing
    #     base_url="http://localhost:11434/v1",
    #     api_key="ollama"
    # )
    
    # Print agent info
    print("\n✓ Agents initialized:\n")
    for agent_name, agent in agents.items():
        config = agent.get_config()
        print(f"  • {agent_name}")
        print(f"    Model: {config['model']}")
        print(f"    Tools: {config['num_tools']} ({', '.join(config['tool_names'][:3])}...)")
        print()
    
    print("="*60)
    print("\n💡 TIP: Be specific about:")
    print("  - Function name and purpose")
    print("  - Target file path (e.g., utils.py, helpers/validators.py)")
    print("  - Any specific requirements or edge cases")
    print("\n" + "="*60 + "\n")
    
    # Run the agent loop starting with Orchestrator
    try:
        conversation = run_agent_loop(
            agents=agents,
            starting_agent_name="Orchestrator Agent",
            max_iterations=100  # Prevent infinite loops
        )
        
        print("\n" + "="*60)
        print(f"✓ Session completed. Total messages: {len(conversation)}")
        print("="*60)
        
        # Show workspace contents
        workspace = Path(".agent_workspace")
        if workspace.exists():
            print("\n📁 Workspace contents:")
            for item in workspace.iterdir():
                print(f"  - {item.name}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()