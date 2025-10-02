# Multi-Agent Orchestration System

A multi-agent system that coordinates specialized AI agents to handle coding tasks, with real-time web visualization of agent interactions and tool usage.

![Agent Network Visualization](docs/agent_network_visualization.png)

## What This Does

This system uses multiple AI agents that work together to:
- **Orchestrator**: Plans and coordinates the workflow
- **Coder**: Implements functions and fixes code
- **Tester**: Writes tests and validates functionality  
- **Database**: Manages knowledge graph operations

Each agent has specialized tools and can hand off tasks to other agents, creating a collaborative workflow that you can watch in real-time through the web interface.

## Quick Setup

### Prerequisites
- Python 3.8+ (3.12 was used for demo)
- Node.js 16+
- OpenAI API key (Can be switched with Ollama easily within the haystack-ai definitions)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### System Dependencies (if needed)

```bash
# For PDF processing (if using document upload)
sudo apt-get install poppler-utils

# For Docker/Ollama (if using local models)
sudo apt-get install docker.io
```

### Set API Key

```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Running the Demo

### Option 1: Automated startup
```bash
python start_system.py
```

### Option 2: Manual startup
```bash
# Terminal 1: Start backend
python real_agent_bridge.py

# Terminal 2: Start frontend  
cd frontend
npm run dev
```

### Access the Interface
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

## How to Use

1. Enter a coding request (e.g., "Create a fibonacci calculator")
2. Click "Start Agent Workflow"
3. Watch agents coordinate in the network diagram
4. Monitor progress in real-time
5. Review generated files and test results

## Features

- **Real-time Visualization**: See agent interactions and tool usage
- **Document Upload**: Process PDFs and other documents with AI
- **Task Tracking**: Monitor workflow progress
- **Tool Highlighting**: See which tools are being used when
- **Step-by-step Navigation**: Browse through the conversation history