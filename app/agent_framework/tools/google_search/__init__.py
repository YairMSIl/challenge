"""Google Search Tool Package
=======================

Tool for performing web searches using Google Custom Search API.

Public Components:
- GoogleSearchTool: Main tool class for performing searches
- search(): Convenience function for direct API access
- SearchResult: Data class for search results

Design Decisions:
- Splits functionality into focused modules
- Uses proper dependency injection
- Implements clean separation of concerns
- Provides both class-based and functional interfaces
- Handles JSON serialization properly
"""

import json
from typing import List, Dict, Any
from .tool import GoogleSearchTool
from .response_formatter import SearchResult

__all__ = ['GoogleSearchTool', 'SearchResult', 'search']

def search(query: str, num_results: int = 5, api_key: str = None, cse_id: str = None) -> List[Dict[str, Any]]:
    """
    Convenience function to perform a Google search without instantiating the tool.
    
    Args:
        query: Search query string
        num_results: Number of results to return (max 10)
        api_key: Optional Google API key
        cse_id: Optional Custom Search Engine ID
        
    Returns:
        List of search results as dictionaries
    """
    tool = GoogleSearchTool(api_key=api_key, cse_id=cse_id)
    response = json.loads(tool.forward(query, num_results))
    return response.get('data', {}).get('results', []) 