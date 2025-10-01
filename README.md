# AI Coding Assistant System

A multi-agent system for automated code generation, testing, and finalization with interactive web visualization.

## 🎯 System Overview

This system uses three specialized agents that work together to handle coding requests:

- **🎯 Orchestrator Agent**: Manages workflow, coordinates tasks, and finalizes functions
- **💻 Coder Agent**: Implements functions and fixes code issues  
- **🧪 Tester Agent**: Writes comprehensive tests, sets up environments, and validates code

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key (for full functionality)

### Installation
```bash
# Clone and navigate to the project
cd multiagent-orch-system

# Install Python dependencies
pip install fastapi uvicorn openai

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running the System

#### Option 1: Use the startup script
```bash
python start_system.py
```

#### Option 2: Manual startup
```bash
# Terminal 1: Start backend
python real_agent_bridge.py

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### Set OpenAI API Key (Required for full functionality)
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## 🌐 Web Interface

Once running, open your browser to:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎮 How to Use

1. **Enter a Request**: Type your coding request (e.g., "Create a function to calculate fibonacci numbers")
2. **Start Workflow**: Click "Start Agent Workflow" 
3. **Watch Agents Work**: See the network diagram show agent coordination
4. **Monitor Progress**: Track tasks and view message history
5. **Review Results**: Check generated files and test results

## 🔧 Features

### Agent Network Visualization
- **Interactive Diagram**: See agents and their tools in real-time
- **Tool Indicators**: Small circles around agents show available tools
- **Communication Flow**: Arrows show message flow between agents
- **Step-by-Step Navigation**: Navigate through the conversation history

### Real-time Monitoring
- **Task Progress**: Visual progress bar and task status
- **Message Log**: Detailed communication history
- **File Generation**: View created files and test results
- **Tool Usage**: See which tools each agent uses

### Agent Tools

#### Orchestrator Agent Tools:
- `read_file` - Read existing files
- `list_directory` - Explore directory structure  
- `finalize_function` - Add approved code to target files
- `transfer_to_coder_agent` - Hand off to Coder
- `transfer_to_tester_agent` - Hand off to Tester

#### Coder Agent Tools:
- `create_function` - Implement new functions
- `fix_function` - Fix problematic code
- `transfer_to_orchestrator_agent` - Return to Orchestrator

#### Tester Agent Tools:
- `setup_test_environment` - Create virtual environment with dependencies
- `write_unit_tests` - Write comprehensive test suites
- `run_unit_tests` - Execute tests and report results
- `transfer_to_orchestrator_agent` - Return to Orchestrator

## 📁 Project Structure

```
multiagent-orch-system/
├── agents/                     # Agent definitions
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── orchestrator_agent.py  # Orchestrator implementation
│   ├── coder_agent.py         # Coder implementation
│   └── tester_agent.py        # Tester implementation
├── tools/                     # Tool functions
│   ├── __init__.py
│   ├── file_operations.py     # File I/O tools
│   ├── coding_tools.py        # Code generation tools
│   └── testing_tools.py       # Testing and validation tools
├── frontend/                  # React web interface
│   ├── src/
│   │   ├── components/        # React components
│   │   └── App.jsx           # Main application
│   └── package.json
├── .agent_workspace/          # Generated files and temp storage
├── real_agent_bridge.py       # Backend API server
├── programmatic_agent_runner.py # Agent workflow runner
├── start_system.py           # Startup script
└── main.py                   # CLI interface
```

## 🔄 Workflow Example

1. **User Request**: "Create a function to validate email addresses"
2. **Orchestrator**: Analyzes request, creates task plan
3. **Coder**: Implements `validate_email()` function with regex
4. **Tester**: Sets up test environment, writes unit tests, runs validation
5. **Orchestrator**: Reviews test results, finalizes function to target file

## 🛠️ Development

### Backend Development
```bash
# Run backend with auto-reload
uvicorn real_agent_bridge:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development  
```bash
cd frontend
npm run dev    # Development server
npm run build  # Production build
```

### Adding New Tools
1. Create tool function in appropriate `tools/` file
2. Add to `tools/__init__.py` exports
3. Import and add to relevant agent in `agents/`

### Adding New Agents
1. Create agent class extending `BaseAgent`
2. Define tools and handoff functions
3. Add to `agents/__init__.py` and `create_coding_agents()`

## 🐛 Troubleshooting

### Common Issues

**"Agents not available" error**
- Set OPENAI_API_KEY environment variable
- Check API key is valid and has credits

**Frontend won't connect to backend**
- Ensure backend is running on port 8000
- Check CORS settings in `real_agent_bridge.py`

**Workflow gets stuck**
- Check backend logs for errors
- Verify all agent tools are properly imported
- Try resetting the system

**Tests fail to run**
- Check virtual environment setup in `.agent_workspace/test_venv`
- Verify required packages are installed

### Debug Mode
Add `verbose=True` when creating agents for detailed logging:
```python
agents = create_coding_agents()
for agent in agents.values():
    agent.verbose = True
```

## 📝 API Endpoints

- `GET /agents` - List available agents and their tools
- `GET /messages` - Get conversation history
- `GET /tasks` - Get current task list and progress
- `GET /files` - Get generated files
- `GET /status` - Get system status
- `POST /submit-prompt` - Start new workflow
- `POST /reset` - Reset system state

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both CLI and web interface
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with OpenAI GPT models
- Frontend powered by React and Vite
- Backend using FastAPI
- Agent coordination inspired by multi-agent system patterns
