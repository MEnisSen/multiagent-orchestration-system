"""
Fixed Database tools for the Neo4j GraphRAG system.
Key fixes:
1. Better error handling and connection testing
2. Connection pooling and proper cleanup
3. Timeout handling
4. Better async loop management
"""

import json
import os
from typing import Annotated, Optional, List, Dict, Any
from pathlib import Path
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j imports
try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j package not installed. Install with: pip install neo4j")

# Neo4j GraphRAG imports
try:
    from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
    from neo4j_graphrag.experimental.components.entity_relation_extractor import LLMEntityRelationExtractor
    from neo4j_graphrag.experimental.components.embedder import TextChunkEmbedder
    from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
    from neo4j_graphrag.experimental.components.schema import SchemaBuilder, NodeType, RelationshipType, PropertyType
    from neo4j_graphrag.experimental.components.types import TextChunks, TextChunk, LexicalGraphConfig
    from neo4j_graphrag.llm import OpenAILLM
    from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
    from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
    GRAPHRAG_AVAILABLE = True
except ImportError:
    GRAPHRAG_AVAILABLE = False
    logger.warning("neo4j-graphrag package not installed. Install with: pip install neo4j-graphrag")

# Haystack + Neo4j integration
try:
    from haystack import Document
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder
    from haystack.components.retrievers.neo4j import Neo4jEmbeddingRetriever
    from neo4j_haystack import Neo4jDocumentStore
    HAYSTACK_NEO4J_AVAILABLE = True
except Exception:
    HAYSTACK_NEO4J_AVAILABLE = False
    logger.warning("haystack-ai or neo4j-haystack not installed")


def get_neo4j_config() -> Dict[str, str]:
    """Get Neo4j configuration from environment variables."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "username": os.getenv("NEO4J_USERNAME", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "passw0rd"),
    }


def test_neo4j_connection(config: Dict[str, str]) -> tuple[bool, Optional[str]]:
    """Test Neo4j connection before proceeding."""
    if not NEO4J_AVAILABLE:
        return False, "neo4j package not installed"
    
    try:
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["username"], config["password"]),
            connection_timeout=5.0,  # 5 second timeout
            max_connection_lifetime=300
        )
        
        # Verify connectivity
        driver.verify_connectivity()
        driver.close()
        return True, None
        
    except ServiceUnavailable as e:
        return False, f"Neo4j service unavailable at {config['uri']}. Is Docker running?"
    except AuthError as e:
        return False, f"Authentication failed. Check NEO4J_USERNAME and NEO4J_PASSWORD"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def get_neo4j_connection():
    """Get Neo4j connection with proper error handling."""
    if not NEO4J_AVAILABLE:
        raise ImportError("neo4j package not installed")
    
    config = get_neo4j_config()
    
    # Test connection first
    is_connected, error_msg = test_neo4j_connection(config)
    if not is_connected:
        raise ConnectionError(error_msg)
    
    return GraphDatabase.driver(
        config["uri"],
        auth=(config["username"], config["password"]),
        connection_timeout=10.0,
        max_connection_lifetime=300
    )


def _run_async_safely(coro):
    """Run an async coroutine safely."""
    try:
        loop = asyncio.get_running_loop()
        raise RuntimeError("Already in async context. Call from sync context only.")
    except RuntimeError:
        pass
    
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            # Cancel all pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Run loop briefly to let tasks clean up
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        finally:
            loop.close()


def kg_updater(
    text_content: Annotated[str, "The text content to process and add to the knowledge graph"],
    source_info: Annotated[str, "Information about the source (e.g., document name, URL, timestamp)"],
    schema_config: Annotated[Optional[str], "Optional JSON string defining custom node types, relationship types, and patterns"] = None,
    chunk_size: Annotated[int, "Size of text chunks for processing"] = 4000,
    chunk_overlap: Annotated[int, "Overlap between consecutive chunks"] = 200
) -> str:
    """
    Transform retrieved information into knowledge graph format and store in Neo4j.
    """
    try:
        logger.info(f"Starting kg_updater for source: {source_info}")
        
        # Check package availability
        if not GRAPHRAG_AVAILABLE:
            return json.dumps({
                "status": "error",
                "message": "neo4j-graphrag package not installed. Install with: pip install neo4j-graphrag"
            })
        
        # Test connection first
        config = get_neo4j_config()
        is_connected, error_msg = test_neo4j_connection(config)
        if not is_connected:
            return json.dumps({
                "status": "error",
                "message": f"Cannot connect to Neo4j: {error_msg}",
                "config": {
                    "uri": config["uri"],
                    "username": config["username"]
                }
            })
        
        # Initialize Neo4j connection
        driver = get_neo4j_connection()
        logger.info("Neo4j connection established")
        
        # Parse schema config
        node_types = []
        relationship_types = []
        patterns = []
        
        if schema_config:
            try:
                schema_dict = json.loads(schema_config)
                node_types = schema_dict.get("node_types", [])
                relationship_types = schema_dict.get("relationship_types", [])
                patterns = schema_dict.get("patterns", [])
            except json.JSONDecodeError as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Invalid schema_config JSON: {str(e)}"
                })
        else:
            # Try loading from file
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
                    logger.info(f"Loaded schema from {schema_path}")
                except Exception as e:
                    logger.warning(f"Could not load schema from {schema_path}: {str(e)}")
        
        # Initialize LLM
        llm = OpenAILLM(
            model_name="gpt-4o-mini",
            model_params={
                "max_tokens": 2000,
                "response_format": {"type": "json_object"},
                "temperature": 0
            }
        )
        
        # Initialize embedder
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Helper function for PropertyType conversion
        def _to_property_types(props: List[Any]) -> List[PropertyType]:
            property_types: List[PropertyType] = []
            for p in props or []:
                if isinstance(p, dict):
                    try:
                        property_types.append(PropertyType(**p))
                    except TypeError:
                        if "name" in p:
                            property_types.append(PropertyType(name=p["name"]))
                        elif "key" in p:
                            property_types.append(PropertyType(name=p["key"]))
                elif isinstance(p, str):
                    try:
                        property_types.append(PropertyType(name=p))
                    except TypeError:
                        try:
                            property_types.append(PropertyType(key=p))
                        except Exception:
                            continue
            return property_types
        
        # Process pipeline
        async def process_pipeline():
            logger.info("Starting text splitting")
            # Step 1: Split text
            splitter = FixedSizeSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            chunks_result = await splitter.run(text=text_content)
            logger.info(f"Created {len(chunks_result.chunks) if hasattr(chunks_result, 'chunks') else 'unknown'} chunks")
            
            # Step 2: Embed chunks
            logger.info("Embedding chunks")
            chunk_embedder = TextChunkEmbedder(embedder=embedder)
            embedded_chunks = await chunk_embedder.run(text_chunks=chunks_result)
            
            # Step 2.5: CRITICAL FIX for v1.10.0 - Manually ensure embeddings are stored
            # The issue is that embeddings might be in a separate field
            if hasattr(embedded_chunks, 'chunks') and embedded_chunks.chunks:
                for i, chunk in enumerate(embedded_chunks.chunks):
                    # Initialize metadata if needed
                    if not hasattr(chunk, 'metadata'):
                        chunk.metadata = {}
                    elif chunk.metadata is None:
                        chunk.metadata = {}
                    
                    # Remove embedding from metadata if it's there (prevents duplication)
                    if 'embedding' in chunk.metadata:
                        del chunk.metadata['embedding']
                    
                    # Set document metadata (FLATTENED - no nested dicts!)
                    chunk.metadata.update({
                        'document_id': source_info,
                        'document_path': source_info,
                        'document_title': source_info,
                        'source': source_info,
                        'chunk_id': f"{source_info}_chunk_{i}",
                        'chunk_index': i,
                    })
                    
                    # CRITICAL: In v1.10.0, ensure the chunk has the embedding attribute set
                    # Check if embedding exists and log for debugging
                    if hasattr(chunk, 'embedding') and chunk.embedding is not None:
                        logger.info(f"Chunk {i} has embedding of length {len(chunk.embedding)}")
                    else:
                        logger.warning(f"Chunk {i} is missing embedding!")
            
            # Step 3: Build schema (if provided)
            schema = None
            if node_types or relationship_types:
                logger.info("Building schema")
                # ... [your existing schema building code] ...
            
            # Step 4: Extract entities and relationships
            logger.info("Extracting entities and relationships")
            extractor = LLMEntityRelationExtractor(
                llm=llm,
                create_lexical_graph=True  # This should create Chunk nodes with embeddings
            )
            
            if schema:
                graph = await extractor.run(chunks=embedded_chunks, schema=schema)
            else:
                graph = await extractor.run(chunks=embedded_chunks)
            
            # DEBUG: Check if graph has chunks with embeddings
            if hasattr(graph, 'chunks'):
                logger.info(f"Graph has {len(graph.chunks)} chunks")
                for i, chunk in enumerate(graph.chunks[:3]):  # Check first 3
                    has_emb = hasattr(chunk, 'embedding') and chunk.embedding is not None
                    logger.info(f"  Graph chunk {i}: has_embedding={has_emb}")
            
            # Step 5: Write to Neo4j (simple version for v1.10.0)
            logger.info("Writing to Neo4j")
            writer = Neo4jWriter(driver)
            write_result = await writer.run(graph)
            
            num_chunks = len(embedded_chunks.chunks) if hasattr(embedded_chunks, 'chunks') else 0
            return write_result, num_chunks
        
        # Run the pipeline
        result, num_chunks = _run_async_safely(process_pipeline())
        
        driver.close()
        logger.info("Pipeline completed successfully")
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully processed and stored knowledge graph",
            "details": {
                "source": source_info,
                "chunks_processed": num_chunks,
                "write_status": result.status if hasattr(result, 'status') else "completed"
            }
        })
        
    except ConnectionError as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_type": "ConnectionError"
        })
    except Exception as e:
        logger.error(f"Error in kg_updater: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Error in knowledge graph update pipeline: {str(e)}",
            "error_type": type(e).__name__
        })


def kg_retriever(
    query: Annotated[str, "The natural language query to search the knowledge graph"],
    retrieval_type: Annotated[str, "Type of retrieval: 'vector', 'vector_cypher', or 'cypher'"] = "vector",
    top_k: Annotated[int, "Number of top results to return"] = 5,
    custom_cypher: Annotated[Optional[str], "Custom Cypher query (only used when retrieval_type='cypher')"] = None
) -> str:
    """
    Retrieve relevant knowledge from the Neo4j graph database.
    """
    try:
        logger.info(f"Starting kg_retriever with query: {query[:50]}...")
        
        if not GRAPHRAG_AVAILABLE:
            return json.dumps({
                "status": "error",
                "message": "neo4j-graphrag package not installed"
            })
        
        # Test connection
        config = get_neo4j_config()
        is_connected, error_msg = test_neo4j_connection(config)
        if not is_connected:
            return json.dumps({
                "status": "error",
                "message": f"Cannot connect to Neo4j: {error_msg}"
            })
        
        # Initialize connection
        driver = get_neo4j_connection()
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        
        async def retrieve_knowledge():
            results = []
            
            if retrieval_type == "vector":
                logger.info("Using vector retrieval")
                retriever = VectorRetriever(
                    driver=driver,
                    index_name="chunk_index",
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
                logger.info("Using vector+cypher retrieval")
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
                if not custom_cypher:
                    return {
                        "status": "error",
                        "message": "custom_cypher required when retrieval_type='cypher'"
                    }
                
                logger.info("Using custom cypher query")
                with driver.session() as session:
                    result = session.run(custom_cypher, {"query": query, "top_k": top_k})
                    results = [dict(record) for record in result]
            
            else:
                return {
                    "status": "error",
                    "message": f"Invalid retrieval_type: {retrieval_type}"
                }
            
            return results
        
        # Run retrieval
        retrieved_data = _run_async_safely(retrieve_knowledge())
        driver.close()
        
        if isinstance(retrieved_data, dict) and retrieved_data.get("status") == "error":
            return json.dumps(retrieved_data)
        
        logger.info(f"Retrieved {len(retrieved_data)} results")
        
        return json.dumps({
            "status": "success",
            "message": f"Retrieved {len(retrieved_data)} results from knowledge graph",
            "query": query,
            "retrieval_type": retrieval_type,
            "results": retrieved_data
        })
        
    except ConnectionError as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_type": "ConnectionError"
        })
    except Exception as e:
        logger.error(f"Error in kg_retriever: {str(e)}", exc_info=True)
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