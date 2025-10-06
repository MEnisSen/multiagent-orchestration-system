"""
Coder Agent for the coding assistant system.
Implements functions and fixes code issues.
"""

from .base_agent import BaseAgent, create_handoff_function
from tools import create_function, fix_function


class CoderAgent(BaseAgent):
    """
    Coder agent that implements functions and fixes code issues.
    
    Responsibilities:
    - Create new functions based on specifications
    - Fix functions that fail tests
    - Write clean, well-documented code
    - Follow best practices and coding standards
    """
    
    def get_handoff_functions(self):
        return [
            create_handoff_function(
                "Orchestrator Agent",
                "Transfer back to Orchestrator after creating or fixing code"
            ),
        ]
    
    def __init__(self, **kwargs):
        kwargs.setdefault("name", "Coder Agent")
        kwargs.setdefault("model", "gpt-4o-mini")
        kwargs.setdefault("instructions", (
            "You are the Coder Agent, an expert Python programmer. "
            "Your SOLE responsibility is writing PRODUCTION CODE ONLY.\n\n"
            "What you DO:\n"
            "1. Implement functions according to specifications from Orchestrator\n"
            "2. Write clean, well-documented code with:\n"
            "   - Clear docstrings\n"
            "   - Type hints\n"
            "   - Proper error handling\n"
            "   - Following PEP 8 style guidelines\n"
            "3. When fixing code, carefully analyze error messages and test failures\n"
            "4. Always use create_function for new implementations\n"
            "5. Always use fix_function when fixing issues\n"
            "6. After creating or fixing code, transfer back to Orchestrator\n\n"
            "What you NEVER DO:\n"
            "- NEVER write unit tests or test code\n"
            "- NEVER write test files or test functions\n"
            "- NEVER include test code in your implementations\n"
            "- Testing is the EXCLUSIVE job of the Tester Agent\n\n"
            "If asked to write tests, remind the requester that Tester Agent handles all testing. "
            "Focus exclusively on correctness, readability, and maintainability of PRODUCTION CODE."
        ))
        super().__init__(**kwargs)
        
        # Add coding tools
        self.add_tool(create_function)
        self.add_tool(fix_function)
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)
