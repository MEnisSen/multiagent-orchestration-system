"""
Research tools for web search and information gathering.
"""

from typing import Annotated
import os
import json


def web_search(query: Annotated[str, "The search query to look up on the web"]) -> str:
    """
    Search the web for information using SerperDev API.
    Returns search results with titles, links, and snippets.
    """
    try:
        # Check if API key is set
        api_key = os.getenv("SERPERDEV_API_KEY")
        if not api_key:
            return json.dumps({
                "status": "error",
                "message": "SERPERDEV_API_KEY not set. Please configure your SerperDev API key in .env file.",
                "suggestion": "Get a free API key at https://serper.dev and add to .env: SERPERDEV_API_KEY=your_key"
            })
        
        # Try to use SerperDev if available
        try:
            from haystack.components.websearch import SerperDevWebSearch
            
            # Create searcher (it reads API key from environment automatically)
            searcher = SerperDevWebSearch(top_k=5)
            
            # Perform search (no warm_up needed for SerperDevWebSearch)
            result = searcher.run(query=query)
            
            # Extract and format results
            documents = result.get("documents", [])
            links = result.get("links", [])
            
            if not documents:
                return json.dumps({
                    "status": "success",
                    "message": f"No results found for: {query}",
                    "results": []
                })
            
            # Format results
            formatted_results = []
            for doc in documents:
                formatted_results.append({
                    "title": doc.meta.get("title", "No title"),
                    "link": doc.meta.get("link", "No link"),
                    "snippet": doc.content[:300] if doc.content else "No content available"
                })
            
            return json.dumps({
                "status": "success",
                "query": query,
                "result_count": len(formatted_results),
                "results": formatted_results,
                "all_links": links[:10]
            }, indent=2)
            
        except ImportError:
            # Fallback: Return mock results or error
            return json.dumps({
                "status": "error",
                "message": "SerperDev integration not installed. Install with: pip install haystack-ai",
                "suggestion": "The SerperDev component is part of haystack-ai package"
            })
    
    except Exception as e:
        import traceback
        return json.dumps({
            "status": "error",
            "message": f"Error performing web search: {str(e)}",
            "traceback": traceback.format_exc()
        })


def search_wikipedia(query: Annotated[str, "The query to search on Wikipedia"]) -> str:
    """
    Search Wikipedia for information.
    Returns article summaries and links.
    """
    try:
        # Simple implementation - in production you'd use Wikipedia API
        return json.dumps({
            "status": "info",
            "message": "Wikipedia search not yet implemented. Use web_search with 'site:wikipedia.org' in your query.",
            "suggestion": f"Try: web_search('site:wikipedia.org {query}')"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error searching Wikipedia: {str(e)}"
        })

