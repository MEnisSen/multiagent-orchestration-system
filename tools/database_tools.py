"""
Database tools for the Neo4j GraphRAG system.
Handles knowledge graph updates and retrieval operations.
"""

import json
import os
from typing import Annotated, Optional, List, Dict, Any
from pathlib import Path
import asyncio

# Neo4j imports
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j package not installed. Install with: pip install neo4j")

# Neo4j GraphRAG imports
try:
    from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
    from neo4j_graphrag.experimental.components.entity_relation_extractor import LLMEntityRelationExtractor
    from neo4j_graphrag.experimental.components.embedder import TextChunkEmbedder
    from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
    from neo4j_graphrag.experimental.components.schema import SchemaBuilder, NodeType, RelationshipType, PropertyType
    from neo4j_graphrag.experimental.components.types import TextChunks, TextChunk
    from neo4j_graphrag.llm import OpenAILLM
    from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
    from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
    GRAPHRAG_AVAILABLE = True
except ImportError:
    GRAPHRAG_AVAILABLE = False
    print("Warning: neo4j-graphrag package not installed. Install with: pip install neo4j-graphrag")


def get_neo4j_connection():
    """Get Neo4j connection from environment variables."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    if not NEO4J_AVAILABLE:
        raise ImportError("neo4j package not installed")
    
    return GraphDatabase.driver(uri, auth=(username, password))


def kg_updater(
    text_content: Annotated[str, "The text content to process and add to the knowledge graph"],
    source_info: Annotated[str, "Information about the source (e.g., document name, URL, timestamp)"],
    schema_config: Annotated[Optional[str], "Optional JSON string defining custom node types, relationship types, and patterns"] = None,
    chunk_size: Annotated[int, "Size of text chunks for processing"] = 4000,
    chunk_overlap: Annotated[int, "Overlap between consecutive chunks"] = 200
) -> str:
    """
    Transform retrieved information into knowledge graph format and store in Neo4j.
    
    This tool implements the complete GraphRAG pipeline:
    1. Text Splitting: Breaks text into manageable chunks
    2. Chunk Embedding: Generates vector embeddings for semantic search
    3. Entity & Relation Extraction: Uses LLM to identify entities and relationships
    4. Schema Building: Applies graph schema constraints
    5. Knowledge Graph Writing: Stores structured data in Neo4j
    
    The pipeline follows the Neo4j GraphRAG architecture:
    Document → Text Splitter → Chunk Embedder → Entity & Relation Extractor → KG Writer → Neo4j
    """
    try:
        if not GRAPHRAG_AVAILABLE:
            return json.dumps({
                "status": "error",
                "message": "neo4j-graphrag package not installed. Install with: pip install neo4j-graphrag"
            })
        
        # Initialize Neo4j connection
        driver = get_neo4j_connection()
        
        # Parse schema config if provided
        node_types = []
        relationship_types = []
        patterns = []
        
        if schema_config:
            try:
                schema_dict = json.loads(schema_config)
                node_types = schema_dict.get("node_types", [])
                relationship_types = schema_dict.get("relationship_types", [])
                patterns = schema_dict.get("patterns", [])
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "message": "Invalid schema_config JSON format"
                })
        
        # Initialize OpenAI LLM for entity extraction
        llm = OpenAILLM(
            model_name="gpt-4o-mini",
            model_params={
                "max_tokens": 2000,
                "response_format": {"type": "json_object"},
                "temperature": 0
            }
        )
        
        # Initialize embedder for chunk embeddings
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Step 1: Text Splitter
        splitter = FixedSizeSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Split text into chunks
        async def process_pipeline():
            chunks_result = await splitter.run(text=text_content)
            
            # Step 2: Chunk Embedder
            chunk_embedder = TextChunkEmbedder(embedder=embedder)
            embedded_chunks = await chunk_embedder.run(text_chunks=chunks_result)
            
            # Step 3: Schema Builder (if schema provided)
            schema = None
            if node_types or relationship_types:
                schema_builder = SchemaBuilder()
                
                # Convert to proper types
                node_type_objects = []
                for nt in node_types:
                    if isinstance(nt, str):
                        node_type_objects.append(NodeType(label=nt))
                    elif isinstance(nt, dict):
                        props = [PropertyType(**p) for p in nt.get("properties", [])]
                        node_type_objects.append(
                            NodeType(
                                label=nt["label"],
                                description=nt.get("description"),
                                properties=props
                            )
                        )
                
                rel_type_objects = []
                for rt in relationship_types:
                    if isinstance(rt, str):
                        rel_type_objects.append(RelationshipType(label=rt))
                    elif isinstance(rt, dict):
                        props = [PropertyType(**p) for p in rt.get("properties", [])]
                        rel_type_objects.append(
                            RelationshipType(
                                label=rt["label"],
                                description=rt.get("description"),
                                properties=props
                            )
                        )
                
                schema_result = await schema_builder.run(
                    node_types=node_type_objects,
                    relationship_types=rel_type_objects,
                    patterns=patterns if patterns else None
                )
                schema = schema_result.schema
            
            # Step 4: Entity & Relation Extractor
            extractor = LLMEntityRelationExtractor(
                llm=llm,
                create_lexical_graph=True  # Creates Document and Chunk nodes
            )
            
            # Extract entities and relationships
            if schema:
                graph = await extractor.run(chunks=embedded_chunks, schema=schema)
            else:
                graph = await extractor.run(chunks=embedded_chunks)
            
            # Step 5: Knowledge Graph Writer
            writer = Neo4jWriter(driver)
            write_result = await writer.run(graph)
            
            return write_result, len(embedded_chunks.chunks)
        
        # Run the async pipeline
        result, num_chunks = asyncio.run(process_pipeline())
        
        driver.close()
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully processed and stored knowledge graph",
            "details": {
                "source": source_info,
                "chunks_processed": num_chunks,
                "entities_extracted": "Stored in Neo4j",
                "write_status": result.status
            }
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error in knowledge graph update pipeline: {str(e)}",
            "error_type": type(e).__name__
        })


def kg_retriever(
    query: Annotated[str, "The natural language query to search the knowledge graph"],
    retrieval_type: Annotated[str, "Type of retrieval: 'vector' for semantic search, 'vector_cypher' for hybrid vector+graph traversal, 'cypher' for custom Cypher query"] = "vector",
    top_k: Annotated[int, "Number of top results to return"] = 5,
    custom_cypher: Annotated[Optional[str], "Custom Cypher query (only used when retrieval_type='cypher')"] = None
) -> str:
    """
    Retrieve relevant knowledge from the Neo4j graph database.
    
    This tool understands natural language queries and retrieves contextual information
    from the knowledge graph using various strategies:
    
    1. Vector Search: Semantic similarity search using embeddings
    2. Vector + Cypher: Combines semantic search with graph traversal
    3. Custom Cypher: Execute custom graph queries for complex retrieval
    
    The retrieved information includes entities, relationships, and contextual data
    that can be used to answer questions or provide insights.
    """
    try:
        if not GRAPHRAG_AVAILABLE:
            return json.dumps({
                "status": "error",
                "message": "neo4j-graphrag package not installed. Install with: pip install neo4j-graphrag"
            })
        
        # Initialize Neo4j connection
        driver = get_neo4j_connection()
        
        # Initialize embedder for query embedding
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        
        async def retrieve_knowledge():
            results = []
            
            if retrieval_type == "vector":
                # Simple vector similarity search
                retriever = VectorRetriever(
                    driver=driver,
                    index_name="chunk_index",  # Default index name
                    embedder=embedder
                )
                search_results = await retriever.search(
                    query_text=query,
                    top_k=top_k
                )
                results = [
                    {
                        "content": item.content,
                        "score": item.score,
                        "metadata": item.metadata
                    }
                    for item in search_results.items
                ]
                
            elif retrieval_type == "vector_cypher":
                # Hybrid: Vector search + Graph traversal
                # Custom retrieval query that combines embeddings with graph structure
                retrieval_query = """
                MATCH (node)-[:PART_OF_CHUNK]->(chunk:Chunk)
                MATCH (chunk)-[:PART_OF_DOCUMENT]->(doc:Document)
                RETURN node.id AS entity_id, 
                       labels(node) AS entity_labels,
                       node AS entity_properties,
                       chunk.text AS context,
                       doc.path AS source,
                       score
                ORDER BY score DESC
                LIMIT $top_k
                """
                
                retriever = VectorCypherRetriever(
                    driver=driver,
                    index_name="chunk_index",
                    embedder=embedder,
                    retrieval_query=retrieval_query
                )
                search_results = await retriever.search(
                    query_text=query,
                    top_k=top_k
                )
                results = [
                    {
                        "entity_id": item.get("entity_id"),
                        "entity_labels": item.get("entity_labels"),
                        "entity_properties": dict(item.get("entity_properties", {})),
                        "context": item.get("context"),
                        "source": item.get("source"),
                        "score": item.get("score")
                    }
                    for item in search_results.items
                ]
                
            elif retrieval_type == "cypher":
                # Custom Cypher query execution
                if not custom_cypher:
                    return {
                        "status": "error",
                        "message": "custom_cypher parameter required when retrieval_type='cypher'"
                    }
                
                with driver.session() as session:
                    result = session.run(custom_cypher, {"query": query, "top_k": top_k})
                    results = [dict(record) for record in result]
            
            else:
                return {
                    "status": "error",
                    "message": f"Invalid retrieval_type: {retrieval_type}. Must be 'vector', 'vector_cypher', or 'cypher'"
                }
            
            return results
        
        # Run async retrieval
        retrieved_data = asyncio.run(retrieve_knowledge())
        
        driver.close()
        
        if isinstance(retrieved_data, dict) and retrieved_data.get("status") == "error":
            return json.dumps(retrieved_data)
        
        return json.dumps({
            "status": "success",
            "message": f"Retrieved {len(retrieved_data)} results from knowledge graph",
            "query": query,
            "retrieval_type": retrieval_type,
            "results": retrieved_data
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving from knowledge graph: {str(e)}",
            "error_type": type(e).__name__
        })