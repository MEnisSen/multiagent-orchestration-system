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


# Haystack + Neo4j integration (optional, separate from GraphRAG)
try:
    from haystack import Document
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder
    from haystack.components.retrievers.neo4j import Neo4jEmbeddingRetriever
    from neo4j_haystack import Neo4jDocumentStore
    HAYSTACK_NEO4J_AVAILABLE = True
except Exception:
    HAYSTACK_NEO4J_AVAILABLE = False
    print("Warning: haystack-ai or neo4j-haystack not installed. Install with: pip install 'haystack-ai>=2.0.0' neo4j-haystack")


def get_neo4j_connection():
    """Get Neo4j connection from environment variables."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "passw0rd")
    
    if not NEO4J_AVAILABLE:
        raise ImportError("neo4j package not installed")
    
    return GraphDatabase.driver(uri, auth=(username, password))


def _run_async_safely(coro):
    """Run an async coroutine in a way that avoids event loop shutdown issues.
    - If no loop is running, create one and do not aggressively close it.
    - If a loop is running (unlikely in our sync tool context), raise a clear error.
    """
    try:
        running_loop = asyncio.get_running_loop()
        # Avoid deadlocks by not trying to nest
        raise RuntimeError("Async loop already running; call this tool from a sync context.")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            # Intentionally do not close the loop immediately to allow background cleanup tasks to finish
            pass


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
        else:
            # Fallback: allow prebuilt schema via env var or default path
            schema_path = os.getenv("NEO4J_SCHEMA_PATH")
            if not schema_path:
                default_path = Path("configs/neo4j_schema.json")
                if default_path.exists():
                    schema_path = str(default_path)
            if schema_path:
                try:
                    with open(schema_path, "r", encoding="utf-8") as f:
                        schema_dict = json.load(f)
                    node_types = schema_dict.get("node_types", [])
                    relationship_types = schema_dict.get("relationship_types", [])
                    patterns = schema_dict.get("patterns", [])
                except Exception as e:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to read schema file at {schema_path}: {str(e)}"
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
        
        # Helper: convert a list of property specs (str or dict) to PropertyType instances
        def _to_property_types(props: List[Any]) -> List[PropertyType]:
            property_types: List[PropertyType] = []
            for p in props or []:
                if isinstance(p, dict):
                    try:
                        property_types.append(PropertyType(**p))
                    except TypeError:
                        # Try common alternate key names
                        if "name" in p:
                            property_types.append(PropertyType(name=p["name"], **{k: v for k, v in p.items() if k != "name"}))
                        elif "key" in p:
                            property_types.append(PropertyType(name=p["key"], **{k: v for k, v in p.items() if k != "key"}))
                        else:
                            # Skip invalid shapes gracefully
                            continue
                elif isinstance(p, str):
                    # Best-effort: set name only; library may default type
                    try:
                        property_types.append(PropertyType(name=p))
                    except TypeError:
                        # Older versions may use 'key' instead of 'name'
                        try:
                            property_types.append(PropertyType(key=p))
                        except Exception:
                            continue
            return property_types

        # Step 1: Text Splitter
        splitter = FixedSizeSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Split text into chunks
        async def process_pipeline():
            # Step 1: Split text into chunks
            chunks_result = await splitter.run(text=text_content)
            
            # Step 2: Chunk Embedder
            chunk_embedder = TextChunkEmbedder(embedder=embedder)
            embedded_chunks = await chunk_embedder.run(text_chunks=chunks_result)
            
            # CRITICAL FIX: Set metadata in the exact format the lexical graph expects
            if hasattr(embedded_chunks, 'chunks') and embedded_chunks.chunks:
                for i, chunk in enumerate(embedded_chunks.chunks):
                    if not hasattr(chunk, 'metadata'):
                        chunk.metadata = {}
                    elif chunk.metadata is None:
                        chunk.metadata = {}
                    
                    # Remove embedding from metadata if present (it bloats the metadata)
                    if 'embedding' in chunk.metadata:
                        del chunk.metadata['embedding']
                    
                    # Set the document metadata structure the lexical graph expects
                    # The key issue: it needs BOTH 'document' dict AND 'document_id' at root level
                    chunk.metadata.update({
                        'document_id': source_info,
                        'document': {
                            'id': source_info,
                            'path': source_info,
                            'title': source_info,
                        },
                        'source': source_info,
                        'chunk_id': f"{source_info}_chunk_{i}",
                        'chunk_index': i,
                    })
            
            # Also try setting metadata at the container level
            if hasattr(embedded_chunks, 'metadata'):
                if not embedded_chunks.metadata:
                    embedded_chunks.metadata = {}
                embedded_chunks.metadata.update({
                    'document_id': source_info,
                    'document': {
                        'id': source_info,
                        'path': source_info,
                        'title': source_info,
                    }
                })
            
            # Step 3: Schema Builder (if schema provided)
            schema = None
            if node_types or relationship_types:
                schema_builder = SchemaBuilder()
                
                node_type_objects = []
                for nt in node_types:
                    if isinstance(nt, str):
                        node_type_objects.append(NodeType(label=nt))
                    elif isinstance(nt, dict):
                        props = _to_property_types(nt.get("properties", []))
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
                        props = _to_property_types(rt.get("properties", []))
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
                schema_candidate = getattr(schema_result, "graph_schema", None)
                if schema_candidate is None:
                    attr = getattr(schema_result, "schema", None)
                    schema_candidate = attr if (attr is not None and not callable(attr)) else None
                schema = schema_candidate or schema_result
            
            # Step 4: Entity & Relation Extractor
            # Try with create_lexical_graph=False first to see if that's causing issues
            extractor = LLMEntityRelationExtractor(
                llm=llm,
                create_lexical_graph=True
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
        result, num_chunks = _run_async_safely(process_pipeline())
        
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
        retrieved_data = _run_async_safely(retrieve_knowledge())
        
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


def hs_neo4j_upsert_documents(
    documents: Annotated[str, "JSON array of Haystack Document dicts or plain texts"],
    embedding_model: Annotated[str, "SentenceTransformers model name" ] = "sentence-transformers/all-MiniLM-L6-v2",
    index: Annotated[Optional[str], "Neo4j vector index name"] = None,
    node_label: Annotated[str, "Neo4j node label for documents"] = "Document",
    embedding_field: Annotated[str, "Property name for embeddings"] = "embedding",
    database: Annotated[str, "Neo4j database name"] = "neo4j"
) -> str:
    """
    Upsert documents into Neo4j via Haystack's Neo4jDocumentStore.
    Accepts a JSON string that is either:
      - an array of strings (treated as content), or
      - an array of Haystack Document-like dicts: {content, id?, meta?, embedding?}
    """
    try:
        if not HAYSTACK_NEO4J_AVAILABLE:
            return json.dumps({
                "status": "error",
                "message": "Haystack Neo4j integration not available. Install haystack-ai and neo4j-haystack."
            })

        data = json.loads(documents)
        if not isinstance(data, list):
            return json.dumps({"status": "error", "message": "documents must be a JSON array"})

        # Prepare Haystack Documents
        hs_docs: List[Document] = []
        for item in data:
            if isinstance(item, str):
                hs_docs.append(Document(content=item))
            elif isinstance(item, dict):
                content = item.get("content")
                if not isinstance(content, str):
                    return json.dumps({"status": "error", "message": "Each dict doc must include string 'content'"})
                hs_docs.append(Document(
                    id=item.get("id"),
                    content=content,
                    meta=item.get("meta") or {},
                    embedding=item.get("embedding")
                ))
            else:
                return json.dumps({"status": "error", "message": "Unsupported document item type"})

        # Embed if no embeddings provided
        need_embedding = any(d.embedding is None for d in hs_docs)
        if need_embedding:
            embedder = SentenceTransformersDocumentEmbedder(model=embedding_model)
            embedder.warm_up()
            result = embedder.run(documents=hs_docs)
            hs_docs = result["documents"]  # enriched with embeddings

        # Connect to Neo4j and write
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "passw0rd")

        # Infer embedding dim from first document
        first_emb = next((d.embedding for d in hs_docs if d.embedding is not None), None)
        if first_emb is None:
            return json.dumps({"status": "error", "message": "No embeddings available after embedding step"})
        embedding_dim = len(first_emb)

        doc_store = Neo4jDocumentStore(
            url=uri,
            username=username,
            password=password,
            database=database,
            embedding_dim=embedding_dim,
            embedding_field=embedding_field,
            index=index or "document_embeddings",
            node_label=node_label,
        )

        doc_store.write_documents(hs_docs)

        return json.dumps({
            "status": "success",
            "message": f"Upserted {len(hs_docs)} documents into Neo4j via Haystack",
            "details": {"index": index or "document_embeddings", "node_label": node_label}
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Haystack Neo4j upsert failed: {str(e)}",
            "error_type": type(e).__name__
        })


def hs_neo4j_retrieve(
    query: Annotated[str, "Natural language query"],
    embedding_model: Annotated[str, "SentenceTransformers model name"] = "sentence-transformers/all-MiniLM-L6-v2",
    top_k: Annotated[int, "Number of results"] = 5,
    index: Annotated[Optional[str], "Neo4j vector index name"] = None,
    node_label: Annotated[str, "Neo4j node label for documents"] = "Document",
    embedding_field: Annotated[str, "Property name for embeddings"] = "embedding",
    database: Annotated[str, "Neo4j database name"] = "neo4j"
) -> str:
    """
    Retrieve documents from Neo4j via Haystack's Neo4jEmbeddingRetriever.
    """
    try:
        if not HAYSTACK_NEO4J_AVAILABLE:
            return json.dumps({
                "status": "error",
                "message": "Haystack Neo4j integration not available. Install haystack-ai and neo4j-haystack."
            })

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "passw0rd")

        # Build a document store aligned with how data was inserted
        # We need embedding dim to init the store; use the embedder to get it
        embedder = SentenceTransformersDocumentEmbedder(model=embedding_model)
        embedder.warm_up()
        emb_dim = embedder.embedding_dimension if hasattr(embedder, "embedding_dimension") else 384

        document_store = Neo4jDocumentStore(
            url=uri,
            username=username,
            password=password,
            database=database,
            embedding_dim=emb_dim,
            embedding_field=embedding_field,
            index=index or "document_embeddings",
            node_label=node_label,
        )

        retriever = Neo4jEmbeddingRetriever(document_store=document_store, top_k=top_k)
        result = retriever.run(query=query)
        docs: List[Document] = result.get("documents", [])

        return json.dumps({
            "status": "success",
            "message": f"Retrieved {len(docs)} documents via Haystack Neo4j",
            "results": [
                {
                    "id": d.id,
                    "content": d.content,
                    "meta": d.meta,
                    "score": getattr(d, "score", None)
                }
                for d in docs
            ]
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Haystack Neo4j retrieval failed: {str(e)}",
            "error_type": type(e).__name__
        })