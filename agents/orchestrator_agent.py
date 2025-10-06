"""
Orchestrator Agent for the coding assistant system.
Manages the entire coding workflow and coordinates between other agents.
"""

from .base_agent import BaseAgent, create_handoff_function
from tools import read_file, list_directory, finalize_function
from tools.task_tools import create_task_list, update_task_status


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
            create_handoff_function(
                "Research Agent",
                "Transfer to Research Agent for web searches and gathering current information"
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
            "2. Task List Execution Protocol (CRITICAL):\n"
            "   - For complex, multi-step requests, FIRST use create_task_list to break down the work into clear tasks.\n"
            "   - Each task should be a specific, actionable step (e.g., 'Conduct web search', 'Organize data', 'Add to database').\n"
            "   - AFTER creating the task list, YOU MUST EXECUTE EACH TASK IN SEQUENCE:\n"
            "     a. Mark task as 'in_progress' using update_task_status(task_index, 'in_progress')\n"
            "     b. Execute the task by calling the appropriate agent/tool:\n"
            "        • Research tasks → transfer_to_research_agent\n"
            "        • Database tasks → transfer_to_database_agent (for kg_updater or hs_neo4j_upsert_documents)\n"
            "        • Coding tasks → transfer_to_coder_agent\n"
            "        • Testing tasks → transfer_to_tester_agent\n"
            "     c. Wait for the agent to complete and return results\n"
            "     d. Mark task as 'completed' using update_task_status(task_index, 'completed')\n"
            "     e. Move to the next task and repeat\n"
            "   - DO NOT stop after creating the task list. You must complete ALL tasks.\n"
            "   - DO NOT just describe what needs to be done. Actually execute each task.\n"
            "   - Track progress continuously and provide status updates.\n"
            "3. Coding-related tasks (retain existing capabilities):\n"
            "   - Use read_file and list_directory to understand existing code structure.\n"
            "   - CRITICAL WORKFLOW - YOU MUST FOLLOW THIS SEQUENCE:\n"
            "     a. Code Implementation → transfer_to_coder_agent (ONLY for writing production code)\n"
            "     b. Testing → transfer_to_tester_agent (ONLY Tester writes and runs tests)\n"
            "     c. Test Results → If PASS: use finalize_function; If FAIL: back to Coder with errors\n"
            "   - NEVER write tests yourself or ask Coder to write tests\n"
            "   - NEVER skip the Tester Agent - all code MUST be tested by Tester\n"
            "   - The Tester Agent will:\n"
            "     • Write comprehensive unit tests (write_unit_tests)\n"
            "     • Set up test environment if needed (setup_test_environment)\n"
            "     • Run tests and report results (run_unit_tests)\n"
            "   - Only finalize code after Tester confirms tests pass\n"
            "4. Knowledge Graph operations (retain existing capabilities):\n"
            "   - When storing information to database, transfer to Database Agent with the data to store.\n"
            "   - The Database Agent has two storage methods:\n"
            "     • kg_updater: For text content that needs entity/relationship extraction\n"
            "     • hs_neo4j_upsert_documents: For structured documents (simpler, faster)\n"
            "   - When retrieving from database, transfer to Database Agent with the query.\n"
            "   - Use the knowledge graph for code reuse, pattern matching, and best practices.\n"
            "5. Non-coding tasks (multipurpose behavior):\n"
            "   - If no specialized agent/tool is needed, answer directly with clear, high-quality responses.\n"
            "   - Ask concise clarifying questions only when essential.\n"
            "   - For planning/analysis/writing/research, produce structured, actionable outputs.\n"
            "6. General orchestration standards:\n"
            "   - ENSURE ALL TASKS ARE COMPLETED before finishing.\n"
            "   - Provide clear status updates to the user after each task.\n"
            "   - Prefer minimal, relevant tool usage; avoid invoking irrelevant tools.\n"
            "   - Confirm feasibility, note limitations, and propose next steps when blocked.\n\n"
            "CRITICAL REMINDER: When you create a task list, you MUST execute every task on that list. "
            "Do not stop after planning. Execute, hand off to agents, wait for results, and mark tasks complete. "
            "Always maintain a systematic approach. For coding tasks, verify tests pass before finalizing. "
            "Leverage the knowledge graph when helpful. For all other tasks, act as a competent, general-purpose assistant."
        ))
        super().__init__(**kwargs)
        
        # Add orchestrator tools
        self.add_tool(read_file)
        self.add_tool(list_directory)
        self.add_tool(finalize_function)
        self.add_tool(create_task_list)
        self.add_tool(update_task_status)
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)
