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


def check_environment():
    """Check required environment variables."""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for LLM operations",
        "NEO4J_URI": "Neo4j database URI (default: bolt://localhost:7687)",
        "NEO4J_USERNAME": "Neo4j username (default: neo4j)",
        "NEO4J_PASSWORD": "Neo4j password"
    }
    
    missing_vars = []
    warnings = []
    
    # Check critical variables
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    
    # Check Neo4j variables (warnings only)
    if not os.getenv("NEO4J_URI"):
        warnings.append("NEO4J_URI (will use default: bolt://localhost:7687)")
    if not os.getenv("NEO4J_USERNAME"):
        warnings.append("NEO4J_USERNAME (will use default: neo4j)")
    if not os.getenv("NEO4J_PASSWORD"):
        warnings.append("NEO4J_PASSWORD")
    
    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  • {var}: {required_vars[var]}")
        print("\nPlease set them using:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    if warnings:
        print("⚠️  Warning: Optional environment variables not set:")
        for var in warnings:
            print(f"  • {var}")
        print("\nDatabase Agent features will be limited without Neo4j configuration.")
        print("To enable full functionality, set:")
        print("  export NEO4J_URI='bolt://localhost:7687'")
        print("  export NEO4J_USERNAME='neo4j'")
        print("  export NEO4J_PASSWORD='your-password'")
        print()
    
    return True

def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          🤖 AI CODING ASSISTANT SYSTEM 🤖                 ║
║                                                           ║
║  Multi-Agent System for Code Generation and Testing       ║
║         with Neo4j Knowledge Graph Integration            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Available Agents:
  🎯 Orchestrator Agent - Manages workflow and coordinates tasks
  💻 Coder Agent        - Implements and fixes functions  
  🧪 Tester Agent       - Writes and runs unit tests
  💾 Database Agent     - Manages Neo4j knowledge graph operations

How it works:
  1. Describe what you need (new function or modify existing)
  2. Orchestrator will analyze and create a task plan
  3. Optionally queries knowledge graph for similar patterns
  4. Coder implements the function
  5. Tester writes and runs unit tests
  6. If tests pass, code is finalized to target file
  7. If tests fail, Coder fixes the issues
  8. Documentation and context stored in knowledge graph

Example requests:
  • "Create a function to calculate fibonacci numbers in utils.py"
  • "Add a function to validate email addresses in validators.py"
  • "Store information about authentication best practices in the knowledge graph"
  • "Search the knowledge graph for examples of data validation functions"
  • "Create multiple helper functions for string manipulation"

Knowledge Graph Features:
  • Store code documentation and patterns
  • Retrieve similar code examples
  • Build context-aware coding assistance
  • Track project knowledge over time
"""
    print(banner)


def main():
    """Main entry point for the coding assistant."""
    
    # Check environment variables
    if not check_environment():
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
        orchestrator_model="gpt-4o-mini",
        coder_model="gpt-4o-mini",
        tester_model="gpt-4o-mini",
        database_model="gpt-4o-mini"
    )
    
    # For using Ollama for specific agents (uncomment and adjust):
    # agents = create_coding_agents(
    #     orchestrator_model="gpt-4o-mini",
    #     coder_model="gpt-4o-mini",
    #     tester_model="llama3.2:3b",  # Use local model for testing
    #     database_model="gpt-4o-mini",
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
    print("\n🔍 Knowledge Graph Tips:")
    print("  - Ask to store documentation for future reference")
    print("  - Request similar code patterns from the knowledge graph")
    print("  - Build context over multiple sessions")
    print("\n" + "="*60 + "\n")
    
    # Check Neo4j connection
    neo4j_configured = all([
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_PASSWORD")
    ])
    
    if neo4j_configured:
        print("✅ Neo4j configuration detected - Knowledge graph features enabled")
    else:
        print("⚠️  Neo4j not configured - Database Agent features limited")
    print()
    
    # Run the agent loop starting with Orchestrator
    try:
        conversation = run_agent_loop(
            agents=agents,
            starting_agent_name="Orchestrator Agent",
            max_iterations=150  # Increased for database operations
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