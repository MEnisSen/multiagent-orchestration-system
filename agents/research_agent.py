"""
Research Agent for web search and information gathering.
Uses SerperDev API for web searches.
"""

from .base_agent import BaseAgent, create_handoff_function


class ResearchAgent(BaseAgent):
    """
    Research agent that can search the web and gather information.
    
    Responsibilities:
    - Search the web for current information
    - Gather data from multiple sources
    - Synthesize research findings
    - Provide cited, accurate information
    """
    
    def get_handoff_functions(self):
        return [
            create_handoff_function(
                "Orchestrator Agent",
                "Transfer back to Orchestrator Agent with research findings"
            ),
        ]
    
    def __init__(self, **kwargs):
        kwargs.setdefault("name", "Research Agent")
        kwargs.setdefault("model", "gpt-4o-mini")
        kwargs.setdefault("instructions", (
            "You are the Research Agent specialized in web search and information gathering.\n"
            "Your responsibilities:\n"
            "1. Search the web for current, accurate information using the web_search tool.\n"
            "2. Perform multiple searches to cover different aspects of a question.\n"
            "3. Synthesize information from multiple sources.\n"
            "4. Provide well-cited responses with sources.\n"
            "5. Distinguish between facts and opinions.\n"
            "6. Note when information is outdated or conflicting.\n\n"
            "Best practices:\n"
            "- Use specific search queries for better results\n"
            "- Search multiple times with different keywords if needed\n"
            "- Always cite your sources\n"
            "- Be clear about the recency of information\n"
            "- Transfer back to Orchestrator when research is complete\n\n"
            "You have access to web_search tool for searching the internet."
        ))
        super().__init__(**kwargs)
        
        # Add web search tool
        try:
            from tools.research_tools import web_search
            self.add_tool(web_search)
        except ImportError:
            print("Warning: Web search tool not available. Install serper-dev-haystack or configure web search.")
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)

