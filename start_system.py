#!/usr/bin/env python3
"""
Startup script for the AI Coding Assistant System.
This script provides clear instructions and starts the system components.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking system requirements...")
    
    # Check if we're in the right directory
    if not Path("agents").exists() or not Path("tools").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   Expected structure: agents/, tools/, frontend/")
        return False
    
    # Check Python packages
    try:
        import fastapi
        import uvicorn
        print("✓ FastAPI and uvicorn are installed")
    except ImportError:
        print("❌ Error: FastAPI or uvicorn not installed")
        print("   Run: pip install fastapi uvicorn")
        return False
    
    # Check if frontend dependencies are installed
    frontend_path = Path("frontend")
    if frontend_path.exists():
        node_modules = frontend_path / "node_modules"
        if not node_modules.exists():
            print("❌ Error: Frontend dependencies not installed")
            print("   Run: cd frontend && npm install")
            return False
        print("✓ Frontend dependencies are installed")
    
    return True

def check_api_key():
    """Check if OpenAI API key is set."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set")
        print("   The system will run in demo mode with limited functionality")
        print("   To use real agents, set your API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False
    else:
        print("✓ OpenAI API key is configured")
        return True

def start_backend():
    """Start the backend server."""
    print("\n🚀 Starting backend server...")
    print("   Backend will be available at: http://localhost:8000")
    print("   API documentation at: http://localhost:8000/docs")
    
    try:
        # Start the real agent bridge
        subprocess.run([
            sys.executable, "real_agent_bridge.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n⚠️  Backend server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting backend: {e}")

def start_frontend():
    """Start the frontend development server."""
    print("\n🎨 Starting frontend development server...")
    print("   Frontend will be available at: http://localhost:5173")
    
    try:
        os.chdir("frontend")
        subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("\n⚠️  Frontend server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting frontend: {e}")
    except FileNotFoundError:
        print("❌ Error: npm not found. Please install Node.js")

def show_usage_instructions():
    """Show instructions for using the system."""
    print("\n" + "="*60)
    print("🎯 AI CODING ASSISTANT SYSTEM")
    print("="*60)
    print("\n📋 How to use:")
    print("1. Open your browser to: http://localhost:5173")
    print("2. Enter a coding request (e.g., 'Create a fibonacci function')")
    print("3. Click 'Start Agent Workflow'")
    print("4. Watch the agents coordinate in the network diagram")
    print("5. Monitor progress in the task list and message log")
    
    print("\n🔧 Features:")
    print("• Agent Network: See Orchestrator, Coder, and Tester agents")
    print("• Tool Visualization: Tools are shown around each agent")
    print("• Real-time Communication: Step through agent interactions")
    print("• Task Progress: Monitor workflow completion")
    print("• Message History: View detailed communication logs")
    
    print("\n⚙️  System Status:")
    api_key_status = "✓ Ready" if os.getenv("OPENAI_API_KEY") else "⚠️  Demo Mode (API key needed for full functionality)"
    print(f"• OpenAI API Key: {api_key_status}")
    print("• Backend: Starting on http://localhost:8000")
    print("• Frontend: Starting on http://localhost:5173")
    
    print("\n" + "="*60)

def main():
    """Main startup function."""
    print("🚀 AI Coding Assistant System Startup")
    print("="*50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check API key (warning only)
    check_api_key()
    
    # Show usage instructions
    show_usage_instructions()
    
    # Ask user what to start
    print("\n🎮 What would you like to start?")
    print("1. Backend only (API server)")
    print("2. Frontend only (Web interface)")
    print("3. Both (recommended)")
    print("4. Show instructions only")
    
    try:
        choice = input("\nEnter your choice (1-4) [3]: ").strip() or "3"
        
        if choice == "1":
            start_backend()
        elif choice == "2":
            start_frontend()
        elif choice == "3":
            print("\n📝 To start both servers:")
            print("   Terminal 1: python real_agent_bridge.py")
            print("   Terminal 2: cd frontend && npm run dev")
            print("\n   Or use the provided scripts in separate terminals")
        elif choice == "4":
            print("\n✓ Instructions shown above")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

if __name__ == "__main__":
    main()
