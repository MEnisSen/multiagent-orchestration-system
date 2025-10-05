"""
Simple test to verify database tools work with your agent setup
"""

import json
import os

# Make sure environment variables are set
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "passw0rd")

# Import your tools directly
try:
    from tools.database_tools import kg_updater, kg_retriever
    print("✓ Successfully imported database tools")
except ImportError as e:
    print(f"✗ Failed to import tools: {e}")
    print("\nMake sure you're running from the correct directory")
    print("Or adjust the import path")
    exit(1)


def test_kg_updater_simple():
    """Test the kg_updater with simple text."""
    print("\n" + "="*60)
    print("TEST: kg_updater")
    print("="*60)
    
    test_text = """
    Python is a high-level programming language. 
    It was created by Guido van Rossum and first released in 1991.
    Python is known for its simple syntax and readability.
    Many developers use Python for web development, data science, and AI.
    """
    
    print("Processing text...")
    print(f"Text length: {len(test_text)} characters")
    
    try:
        result = kg_updater(
            text_content=test_text,
            source_info="test_python_intro",
            chunk_size=500,
            chunk_overlap=50
        )
        
        result_dict = json.loads(result)
        
        print(f"\nStatus: {result_dict['status']}")
        print(f"Message: {result_dict['message']}")
        
        if result_dict['status'] == 'success':
            print("\n✓ kg_updater working correctly!")
            if 'details' in result_dict:
                print(f"\nDetails:")
                for key, value in result_dict['details'].items():
                    print(f"  {key}: {value}")
            return True
        else:
            print(f"\n✗ kg_updater failed")
            print(f"Error: {result_dict.get('message', 'Unknown error')}")
            if 'error_type' in result_dict:
                print(f"Error type: {result_dict['error_type']}")
            return False
            
    except Exception as e:
        print(f"\n✗ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_kg_retriever_simple():
    """Test the kg_retriever with simple query."""
    print("\n" + "="*60)
    print("TEST: kg_retriever")
    print("="*60)
    
    queries = [
        "What is Python?",
        "Who created Python?",
        "What is Python used for?"
    ]
    
    all_success = True
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        try:
            result = kg_retriever(
                query=query,
                retrieval_type="vector",
                top_k=3
            )
            
            result_dict = json.loads(result)
            
            if result_dict['status'] == 'success':
                results = result_dict.get('results', [])
                print(f"  ✓ Found {len(results)} results")
                
                # Show first result if available
                if results:
                    first = results[0]
                    content = first.get('content', '')
                    score = first.get('score', 0)
                    print(f"  Top result (score: {score:.3f}):")
                    print(f"    {content[:100]}...")
            else:
                print(f"  ✗ Failed: {result_dict.get('message', 'Unknown error')}")
                all_success = False
                
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
            all_success = False
    
    if all_success:
        print("\n✓ kg_retriever working correctly!")
    else:
        print("\n⚠ Some queries failed")
    
    return all_success


def verify_database_changes():
    """Check if data was actually written to Neo4j."""
    print("\n" + "="*60)
    print("VERIFICATION: Database Changes")
    print("="*60)
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            
            # Get labels
            result = session.run("CALL db.labels()")
            labels = [record[0] for record in result]
            
            print(f"Nodes: {node_count}")
            print(f"Relationships: {rel_count}")
            print(f"Labels: {', '.join(labels) if labels else 'None'}")
            
            if node_count > 0:
                print("\n✓ Data successfully written to Neo4j!")
                
                # Show sample data
                print("\nSample nodes (first 3):")
                result = session.run("MATCH (n) RETURN labels(n)[0] as label, n LIMIT 3")
                for i, record in enumerate(result, 1):
                    label = record['label']
                    node = dict(record['n'])
                    print(f"\n  {i}. {label}")
                    for key, value in list(node.items())[:3]:  # Show first 3 properties
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"     {key}: {value}")
                
                return True
            else:
                print("\n⚠ No data found in database")
                return False
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Verification failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DATABASE AGENT TOOLS TEST")
    print("="*60)
    
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠ WARNING: OPENAI_API_KEY not set!")
        print("The tools use OpenAI for embeddings and entity extraction.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\nThis test will:")
    print("1. Store sample text in Neo4j using kg_updater")
    print("2. Query the data using kg_retriever")
    print("3. Verify data was written correctly")
    print("\nNote: This may take 30-60 seconds due to LLM calls\n")
    
    input("Press Enter to continue...")
    
    # Test 1: Updater
    print("\n⏳ Running kg_updater (may take 30-60 seconds)...")
    updater_success = test_kg_updater_simple()
    
    if not updater_success:
        print("\n❌ kg_updater test failed!")
        print("\nCommon issues:")
        print("  - OPENAI_API_KEY not set or invalid")
        print("  - Network connectivity issues")
        print("  - Neo4j connection issues")
        return
    
    # Test 2: Retriever
    print("\n⏳ Running kg_retriever...")
    retriever_success = test_kg_retriever_simple()
    
    # Test 3: Verification
    verify_success = verify_database_changes()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"kg_updater:  {'✓ PASS' if updater_success else '✗ FAIL'}")
    print(f"kg_retriever: {'✓ PASS' if retriever_success else '✗ FAIL'}")
    print(f"Verification: {'✓ PASS' if verify_success else '✗ FAIL'}")
    print("="*60)
    
    if updater_success and retriever_success and verify_success:
        print("\n🎉 All tests passed! Your database tools are working correctly.")
        print("\nYour DatabaseAgent should now be able to:")
        print("  - Store information in Neo4j knowledge graph")
        print("  - Retrieve relevant information using semantic search")
        print("  - Extract entities and relationships from text")
    else:
        print("\n⚠ Some tests failed. Review the output above for details.")


if __name__ == "__main__":
    main()