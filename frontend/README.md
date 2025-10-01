# AI Coding Assistant Frontend

Interactive visualization for the multi-agent coding assistant system.

## Features

- **Agent Network Visualization**: See Orchestrator, Coder, and Tester agents with their tools
- **Tool Visualization**: Each agent shows its available tools around it in the network diagram
- **Real-time Communication**: Step-by-step visualization of agent interactions
- **Task Progress Tracking**: Monitor task completion and workflow status
- **Message History**: View detailed communication logs between agents

## Agent Structure

### 🎯 Orchestrator Agent
- **Role**: Manages workflow and coordinates tasks
- **Tools**: `read_file`, `list_directory`, `finalize_function`, handoff functions
- **Color**: Blue

### 💻 Coder Agent  
- **Role**: Implements and fixes functions
- **Tools**: `create_function`, `fix_function`, handoff functions
- **Color**: Green

### 🧪 Tester Agent
- **Role**: Writes and runs comprehensive tests
- **Tools**: `setup_test_environment`, `write_unit_tests`, `run_unit_tests`, handoff functions
- **Color**: Orange

## Quick Start

### 1. Start the Backend Bridge
```bash
# From the project root
python frontend_bridge.py
```
This starts a FastAPI server on `http://localhost:8000` that provides the API endpoints the frontend expects.

### 2. Start the Frontend
```bash
# In a new terminal
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173` (or `http://localhost:3000` depending on your setup).

### 3. Use the Interface
1. Enter a coding request (e.g., "Create a function to calculate fibonacci numbers")
2. Click "Start Agent Workflow"
3. Watch the agents coordinate in the network diagram
4. See tools being used around each agent
5. Monitor task progress and message flow

## Network Diagram Features

- **Tool Indicators**: Small circles around each agent show available tools
- **Tool Count**: Blue number badge shows how many tools each agent has
- **Active Status**: Green dot indicates agent is active
- **Message Flow**: Arrows show communication between agents
- **Interactive**: Hover over agents, tools, and messages for details
- **Navigation**: Step through message history with navigation controls

## Integration with Your Backend

To integrate with your actual agent system, modify `frontend_bridge.py` to:

1. Import your agent classes from `agents`
2. Replace the mock message creation with actual agent communication
3. Connect the `/submit-prompt` endpoint to your `run_agent_loop` function
4. Stream real-time updates from your agent system

Example integration:
```python
from agents import create_coding_agents, run_agent_loop

# In your endpoint
agents = create_coding_agents()
conversation = run_agent_loop(agents, starting_agent_name="Orchestrator Agent")
```

## Customization

- **Agent Colors**: Modify colors in `AgentDiagram.jsx` `agentPositions`
- **Tool Icons**: Update tool icons in the tool rendering section
- **Message Types**: Add new message types in `MessageLog.jsx`
- **Layout**: Adjust agent positions in the network diagram

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## API Endpoints

The frontend expects these endpoints from the backend:

- `GET /agents` - List of available agents
- `GET /messages` - Recent agent communications  
- `GET /tasks` - Current task list and progress
- `GET /files` - Generated files
- `GET /status` - System status
- `POST /submit-prompt` - Submit user request
- `POST /reset` - Reset system state
