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
            "You are the Orchestrator Agent for a coding assistant system. "
            "Your responsibilities:\n"
            "1. Parse user requests and create detailed task lists with:\n"
            "   - Function name and purpose\n"
            "   - Target file path\n"
            "   - Implementation requirements\n"
            "2. Use read_file and list_directory to understand existing code structure\n"
            "3. Coordinate the workflow:\n"
            "   a. Send coding tasks to Coder Agent\n"
            "   b. Once code is created, send to Tester Agent for unit tests\n"
            "   c. If tests pass, use finalize_function to add code to target file\n"
            "   d. If tests fail, send back to Coder Agent with error details\n"
            "4. Manage Knowledge Graph Operations:\n"
            "   a. Transfer to Database Agent to store documentation, code context, or retrieved information\n"
            "   b. Transfer to Database Agent to query the knowledge graph for relevant context\n"
            "   c. Use knowledge graph for code reuse, pattern matching, and best practices\n"
            "5. Decision Making for Database Agent:\n"
            "   - Store: When you have documentation, code examples, or context to preserve\n"
            "   - Retrieve: When you need context, similar code patterns, or historical information\n"
            "   - Consider using the knowledge graph for complex projects or when building on existing work\n"
            "6. Track progress and ensure all tasks are completed\n"
            "7. Provide clear status updates to the user\n\n"
            "Always maintain a systematic approach and verify tests pass before finalizing. "
            "Leverage the knowledge graph for intelligent code assistance and context-aware development."
        ))
        super().__init__(**kwargs)
        
        # Add orchestrator tools
        self.add_tool(read_file)
        self.add_tool(list_directory)
        self.add_tool(finalize_function)
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)
