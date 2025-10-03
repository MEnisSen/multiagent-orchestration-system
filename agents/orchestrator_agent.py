"""
Orchestrator Agent for the coding assistant system.
Manages the entire coding workflow and coordinates between other agents.
"""

from .base_agent import BaseAgent, create_handoff_function
from tools import read_file, list_directory, finalize_function


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator agent that manages the entire coding workflow.
    
    Responsibilities:
    - Parse user requests and create detailed task lists
    - Read existing files and explore directory structure
    - Coordinate between Coder, Tester, and Database agents
    - Validate that functions pass tests before finalization
    - Finalize approved functions to target files
    - Manage knowledge graph operations for documentation and retrieval
    """
    
    def get_handoff_functions(self):
        return [
            create_handoff_function(
                "Coder Agent", 
                "Transfer to Coder Agent for implementing functions or fixing code"
            ),
            create_handoff_function(
                "Tester Agent",
                "Transfer to Tester Agent for writing and running unit tests"
            ),
            create_handoff_function(
                "Database Agent",
                "Transfer to Database Agent for storing/retrieving information in Neo4j knowledge graph"
            ),
        ]
    
    def __init__(self, **kwargs):
        kwargs.setdefault("name", "Orchestrator Agent")
        kwargs.setdefault("model", "gpt-4o-mini")
        kwargs.setdefault("instructions", (
            "You are the Orchestrator Agent for a multi-agent, multi-purpose assistant system. "
            "Your primary directive is to handle ANY user task by first assessing whether the existing agents/tools can fulfill it, and otherwise responding directly as a capable general assistant.\n"
            "Your responsibilities:\n"
            "1. Classify and plan for any request:\n"
            "   - Identify the task domain (e.g., coding, testing, data/knowledge operations, research, writing, analysis, planning, Q&A).\n"
            "   - Decide if existing agents/tools are applicable; if yes, orchestrate them. If not, proceed directly with a helpful answer without unnecessary tool calls.\n"
            "2. Coding-related tasks (retain existing capabilities):\n"
            "   - Parse requests and create detailed task lists with:\n"
            "     • Function name and purpose (when applicable)\n"
            "     • Target file path (when applicable)\n"
            "     • Implementation requirements (when applicable)\n"
            "   - Use read_file and list_directory to understand existing code structure.\n"
            "   - Coordinate the workflow:\n"
            "     a. Send coding tasks to Coder Agent\n"
            "     b. Once code is created, send to Tester Agent for unit tests\n"
            "     c. If tests pass, use finalize_function to add code to target file\n"
            "     d. If tests fail, send back to Coder Agent with error details\n"
            "3. Knowledge Graph operations (retain existing capabilities):\n"
            "   - Transfer to Database Agent to store documentation, code context, or retrieved information.\n"
            "   - Transfer to Database Agent to query the knowledge graph for relevant context.\n"
            "   - Use the knowledge graph for code reuse, pattern matching, and best practices.\n"
            "   - Decision points:\n"
            "     • Store when you have documentation, code examples, or context to preserve.\n"
            "     • Retrieve when you need context, similar code patterns, or historical information.\n"
            "     • Prefer the knowledge graph for complex projects or when building on existing work.\n"
            "4. Non-coding tasks (multipurpose behavior):\n"
            "   - If no specialized agent/tool is needed, answer directly with clear, high-quality responses.\n"
            "   - Ask concise clarifying questions only when essential.\n"
            "   - For planning/analysis/writing/research, produce structured, actionable outputs.\n"
            "5. General orchestration standards:\n"
            "   - Track progress and ensure all tasks are completed.\n"
            "   - Provide clear status updates to the user.\n"
            "   - Prefer minimal, relevant tool usage; avoid invoking irrelevant tools.\n"
            "   - Confirm feasibility, note limitations, and propose next steps when blocked.\n\n"
            "Always maintain a systematic approach. For coding tasks, verify tests pass before finalizing. "
            "Leverage the knowledge graph when helpful. For all other tasks, act as a competent, general-purpose assistant."
        ))
        super().__init__(**kwargs)
        
        # Add orchestrator tools
        self.add_tool(read_file)
        self.add_tool(list_directory)
        self.add_tool(finalize_function)
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)
