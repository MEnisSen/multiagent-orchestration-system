"""
Agents package for the coding assistant system.
Contains all agent classes and helper functions.
"""

from typing import Dict
from .base_agent import BaseAgent, run_agent_loop
from .orchestrator_agent import OrchestratorAgent
from .coder_agent import CoderAgent
from .tester_agent import TesterAgent
from .database_agent import DatabaseAgent
from .research_agent import ResearchAgent


def create_coding_agents(
    orchestrator_model: str = "gpt-4o-mini",
    coder_model: str = "gpt-4o-mini",
    tester_model: str = "gpt-4o-mini",
    database_model: str = "gpt-4o-mini",
    research_model: str = "gpt-4o-mini",
    api_key: str = None,
    base_url: str = None
) -> Dict[str, BaseAgent]:
    """
    Create and return a dictionary of all coding agents.
    
    Args:
        orchestrator_model: Model to use for orchestrator
        coder_model: Model to use for coder
        tester_model: Model to use for tester
        database_model: Model to use for database
        research_model: Model to use for research
        api_key: Optional API key (uses env variable if not provided)
        base_url: Optional base URL for custom endpoints (e.g., Ollama)
    
    Returns:
        Dictionary mapping agent names to agent instances
    """
    common_kwargs = {}
    if api_key:
        common_kwargs['api_key'] = api_key
    if base_url:
        common_kwargs['base_url'] = base_url
    
    orchestrator = OrchestratorAgent(model=orchestrator_model, **common_kwargs)
    coder = CoderAgent(model=coder_model, **common_kwargs)
    tester = TesterAgent(model=tester_model, **common_kwargs)
    database = DatabaseAgent(model=database_model, **common_kwargs)
    research = ResearchAgent(model=research_model, **common_kwargs)
    
    return {
        agent.name: agent
        for agent in [orchestrator, coder, tester, database, research]
    }


__all__ = [
    'BaseAgent',
    'OrchestratorAgent', 
    'CoderAgent',
    'TesterAgent',
    'DatabaseAgent',
    'ResearchAgent',
    'create_coding_agents',
    'run_agent_loop'
]
