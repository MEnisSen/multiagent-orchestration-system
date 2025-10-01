"""
Tester Agent for the coding assistant system.
Writes and runs unit tests for functions.
"""

from .base_agent import BaseAgent, create_handoff_function
from tools import write_unit_tests, run_unit_tests, setup_test_environment


class TesterAgent(BaseAgent):
    """
    Tester agent that writes and runs unit tests.
    
    Responsibilities:
    - Write comprehensive unit tests for functions
    - Run tests and report results
    - Provide detailed error information for failed tests
    - Suggest what needs to be fixed
    """
    
    def get_handoff_functions(self):
        return [
            create_handoff_function(
                "Orchestrator Agent",
                "Transfer back to Orchestrator with test results"
            ),
        ]
    
    def __init__(self, **kwargs):
        kwargs.setdefault("name", "Tester Agent")
        kwargs.setdefault("model", "gpt-4o-mini")
        kwargs.setdefault("instructions", (
            "You are the Tester Agent, an expert in software testing. "
            "Your responsibilities:\n"
            "1. Analyze the function to be tested and identify any external dependencies\n"
            "2. If the function requires external libraries, use setup_test_environment to:\n"
            "   - Create/activate a virtual environment in .agent_workspace\n"
            "   - Install required packages for testing\n"
            "3. Write comprehensive unit tests that cover:\n"
            "   - Normal/happy path cases\n"
            "   - Edge cases\n"
            "   - Error conditions\n"
            "   - Boundary values\n"
            "4. Use unittest framework for writing tests\n"
            "5. First use write_unit_tests to create the test file\n"
            "6. Then use run_unit_tests to execute them (will use venv if available)\n"
            "7. Analyze test results:\n"
            "   - If passed: Report success to Orchestrator\n"
            "   - If failed: Provide detailed error analysis\n"
            "8. Always transfer back to Orchestrator with results\n\n"
            "Be thorough in testing and clear in reporting issues. "
            "Consider dependencies like numpy, pandas, requests, etc. when testing functions."
        ))
        super().__init__(**kwargs)
        
        # Add testing tools
        self.add_tool(setup_test_environment)
        self.add_tool(write_unit_tests)
        self.add_tool(run_unit_tests)
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)
