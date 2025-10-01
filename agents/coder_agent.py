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
            "Your responsibilities:\n"
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
            "Focus on correctness, readability, and maintainability."
        ))
        super().__init__(**kwargs)
        
        # Add coding tools
        self.add_tool(create_function)
        self.add_tool(fix_function)
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)
