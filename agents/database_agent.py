"""
Database Agent for the Neo4j GraphRAG system.
Handles knowledge graph updates and retrieval operations.
"""

from .base_agent import BaseAgent, create_handoff_function
from tools import kg_updater, kg_retriever


class DatabaseAgent(BaseAgent):
    """
    Database agent that manages Neo4j GraphRAG operations.
    
    Responsibilities:
    - Transform retrieved information into knowledge graph format
    - Extract entities and relationships from unstructured text
    - Store knowledge in Neo4j graph database
    - Retrieve relevant knowledge based on queries
    - Maintain graph schema consistency
    """
    
    def get_handoff_functions(self):
        return [
            create_handoff_function(
                "Orchestrator Agent",
                "Transfer back to Orchestrator after completing database operations"
            ),
        ]
    
    def __init__(self, **kwargs):
        kwargs.setdefault("name", "Database Agent")
        kwargs.setdefault("model", "gpt-4o-mini")
        kwargs.setdefault("instructions", (
            "You are the Database Agent, an expert in Neo4j GraphRAG operations. "
            "Your responsibilities:\n"
            "1. Knowledge Graph Updates:\n"
            "   - Transform retrieved information into graph-structured data\n"
            "   - Extract entities, relationships, and properties from text\n"
            "   - Maintain consistent graph schema\n"
            "   - Generate embeddings for semantic search\n"
            "   - Store processed data in Neo4j database\n"
            "2. Knowledge Retrieval:\n"
            "   - Understand natural language queries\n"
            "   - Retrieve relevant entities and relationships from the graph\n"
            "   - Perform semantic search using embeddings\n"
            "   - Return contextual information for answering questions\n"
            "3. Best Practices:\n"
            "   - Always use kg_updater when storing new information\n"
            "   - Always use kg_retriever when querying the knowledge base\n"
            "   - Ensure data quality and consistency\n"
            "   - Handle errors gracefully\n"
            "4. After completing database operations, transfer back to Orchestrator\n\n"
            "Focus on accuracy, consistency, and efficient graph operations."
        ))
        super().__init__(**kwargs)
        
        # Add database tools
        self.add_tool(kg_updater)
        self.add_tool(kg_retriever)
        
        # Add handoff functions
        for handoff_func in self.get_handoff_functions():
            self.add_tool(handoff_func)