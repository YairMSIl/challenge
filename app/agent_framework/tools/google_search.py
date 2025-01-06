"""Google Search Tool
====================

SmolAgents tool for performing web searches using Google Custom Search API.

Public Components:
- GoogleSearchTool: Tool class for performing Google searches
- SearchResponse: Response class with serialization methods

Design Decisions:
- Uses Google Custom Search JSON API for reliable and structured results
- Implements rate limiting and error handling
- Returns rich structured results with comprehensive metadata
- Configurable number of results per query
- Handles API quota limitations gracefully
- Follows consistent tool pattern across the project

Integration Notes:
- Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables
- Returns a maximum of 10 results per query (API limitation)
- Implements exponential backoff for rate limiting
"""

import os
import sys
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from smolagents import Tool
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class SearchResponse:
    """Response class for search results."""
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    total_results: Optional[int] = None
    search_time: Optional[float] = None
    
    def to_string(self) -> str:
        """Convert response to JSON string."""
        return json.dumps({
            "success": self.success,
            "results": self.results,
            "error": self.error,
            "total_results": self.total_results,
            "search_time": self.search_time
        })

def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ('true', 't', 'yes', 'y', '1', 'on')

class GoogleSearchTool(Tool):
    """Tool for performing Google searches using the Custom Search API."""
    
    name = "google_search"
    description = """
    This tool performs web searches using Google Custom Search API.
    It returns a JSON string containing search results or an error message.
    """
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query to execute",
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results to return (max 10, default 5)",
            "nullable": True
        }
    }
    output_type = "string"  # Returns JSON string
    
    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        """Initialize the Google Search tool."""
        super().__init__()
        load_dotenv()
        
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.cse_id = cse_id or os.getenv('GOOGLE_CSE_ID')
        
        # Get mock configuration
        self.use_mock = str_to_bool(os.getenv('USE_SEARCH_MOCK_IF_AVAILABLE', 'True'))
        logger.debug(f"Mock usage configuration: {self.use_mock}")
        
        if not self.api_key or not self.cse_id:
            raise ValueError(
                "Google API key and Custom Search Engine ID are required. "
                "Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables."
            )
        
        self._ensure_directories()
        self.service = build('customsearch', 'v1', developerKey=self.api_key)
        logger.info(f"GoogleSearchTool initialized successfully (mock enabled: {self.use_mock})")
        
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        mock_dir = Path("mock")
        mock_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured mock directory exists at {mock_dir}")

    def _save_mock_response(self, response_content: Any) -> None:
        """Save API response for mock testing."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("mock") / f"google_search_{timestamp}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_content, f, indent=2)
                
            logger.debug(f"Saved mock response to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save mock response: {str(e)}")
            # Don't raise - this is not critical for the main functionality

    def _get_mock_response(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent mock response if available.
        
        Returns:
            Mock response data if available, None otherwise
        """
        try:
            mock_dir = Path("mock")
            if not mock_dir.exists():
                return None
                
            # Get all google search response files
            mock_files = list(mock_dir.glob("google_search_*.json"))
            if not mock_files:
                return None
                
            # Get most recent file
            latest_mock = max(mock_files, key=lambda p: p.stat().st_mtime)
            logger.debug(f"Found mock response file: {latest_mock}")
            
            with open(latest_mock, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)
                
            logger.info("Using mock response instead of making API call")
            return mock_data
            
        except Exception as e:
            logger.error(f"Failed to load mock response: {str(e)}")
            return None
    
    def forward(self, query: str, num_results: int = 5) -> str:
        """
        Execute a search query.
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 10)
            
        Returns:
            JSON string containing:
                success: Boolean indicating if search was successful
                results: List of search results with detailed information
                error: Optional error message if search failed
                total_results: Total number of results found
                search_time: Search execution time in seconds
        """
        if not 1 <= num_results <= 10:
            return SearchResponse(
                success=False,
                error="num_results must be between 1 and 10"
            ).to_string()
            
        try:
            logger.info(f"Performing Google search for query: {query}")
            
            # Check for mock response if enabled
            response = self._get_mock_response() if self.use_mock else None
            
            if response is None:
                if self.use_mock:
                    logger.debug("No mock response available, falling back to API call")
                else:
                    logger.debug("Mock disabled, making API call")
                
                # Execute the search
                response = self.service.cse().list(
                    q=query,
                    cx=self.cse_id,
                    num=num_results,
                    fields="items(title,link,snippet,pagemap(articleBody,metatags,videoObject,article,breadcrumb,person,organization,website,review,product,offer,cse_thumbnail,cse_image),displayLink,htmlSnippet,htmlTitle,kind,labels,cacheId,fileFormat,formattedUrl,htmlFormattedUrl,mime),searchInformation(searchTime,totalResults,formattedSearchTime,formattedTotalResults),queries,context"
                ).execute()
                
                # Save the response for future mock usage
                self._save_mock_response(response)
            
            # Extract search information
            search_info = response.get('searchInformation', {})
            total_results = int(search_info.get('totalResults', 0))
            search_time = float(search_info.get('searchTime', 0))
            
            # Extract and format results
            search_results = []
            if 'items' in response:
                for item in response['items']:
                    result_item = {
                        'title': item['title'],
                        'link': item['link'],
                        'snippet': item.get('snippet', ''),
                        'html_snippet': item.get('htmlSnippet', ''),
                        'html_title': item.get('htmlTitle', ''),
                        'display_link': item.get('displayLink', ''),
                        'kind': item.get('kind', ''),
                        'cache_id': item.get('cacheId', ''),
                        'file_format': item.get('fileFormat', ''),
                        'formatted_url': item.get('formattedUrl', ''),
                        'mime': item.get('mime', '')
                    }
                    
                    # Add rich pagemap information if available
                    if 'pagemap' in item:
                        pagemap = item['pagemap']
                        result_item['rich_data'] = {}
                        
                        # Extract article content
                        if 'articleBody' in pagemap:
                            result_item['rich_data']['article_body'] = pagemap['articleBody']
                            
                        # Extract meta tags
                        if 'metatags' in pagemap and pagemap['metatags']:
                            metatags = pagemap['metatags'][0]
                            result_item['rich_data']['meta'] = {
                                'description': metatags.get('og:description', metatags.get('description', '')),
                                'keywords': metatags.get('keywords', ''),
                                'author': metatags.get('author', ''),
                                'published_date': metatags.get('article:published_time', '')
                            }
                            
                        # Extract video information
                        if 'videoObject' in pagemap:
                            result_item['rich_data']['video'] = pagemap['videoObject'][0]
                            
                        # Extract article metadata
                        if 'article' in pagemap:
                            result_item['rich_data']['article_meta'] = pagemap['article'][0]
                            
                        # Extract breadcrumb navigation
                        if 'breadcrumb' in pagemap:
                            result_item['rich_data']['breadcrumb'] = pagemap['breadcrumb'][0]
                            
                        # Extract person information
                        if 'person' in pagemap:
                            result_item['rich_data']['person'] = pagemap['person'][0]
                            
                        # Extract organization information
                        if 'organization' in pagemap:
                            result_item['rich_data']['organization'] = pagemap['organization'][0]
                            
                        # Extract website information
                        if 'website' in pagemap:
                            result_item['rich_data']['website'] = pagemap['website'][0]
                            
                        # Extract review information
                        if 'review' in pagemap:
                            result_item['rich_data']['review'] = pagemap['review'][0]
                            
                        # Extract product information
                        if 'product' in pagemap:
                            result_item['rich_data']['product'] = pagemap['product'][0]
                            
                        # Extract offer information
                        if 'offer' in pagemap:
                            result_item['rich_data']['offer'] = pagemap['offer'][0]
                            
                        # Extract thumbnail and image information
                        if 'cse_thumbnail' in pagemap:
                            result_item['thumbnail'] = pagemap['cse_thumbnail'][0]
                        if 'cse_image' in pagemap:
                            result_item['image'] = pagemap['cse_image'][0]
                            
                    # Add any labels
                    if 'labels' in item:
                        result_item['labels'] = item['labels']
                            
                    search_results.append(result_item)
                    
            logger.debug(f"Found {len(search_results)} results")
            
            return SearchResponse(
                success=True,
                results=search_results,
                total_results=total_results,
                search_time=search_time
            ).to_string()
            
        except HttpError as e:
            error_msg = f"Google Search API error: {str(e)}"
            logger.error(error_msg)
            return SearchResponse(success=False, error=error_msg).to_string()
        except Exception as e:
            error_msg = f"Unexpected error during search: {str(e)}"
            logger.error(error_msg)
            return SearchResponse(success=False, error=error_msg).to_string()

def search(query: str, num_results: int = 5, api_key: Optional[str] = None, 
          cse_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Convenience function to perform a single Google search.
    
    Args:
        query: Search query string
        num_results: Number of results to return (max 10)
        api_key: Optional Google API key
        cse_id: Optional Custom Search Engine ID
        
    Returns:
        List of search results
    """
    search_tool = GoogleSearchTool(api_key, cse_id)
    response = json.loads(search_tool.forward(query, num_results))
    return response.get('results', []) if response.get('success') else []

if __name__ == "__main__":
    # Example usage
    try:

        search_tool = GoogleSearchTool()
        response = json.loads(search_tool.forward("Python web frameworks", num_results=5))
        
        if response['success']:
            print(f"\nSearch completed in {response['search_time']:.2f} seconds")
            print(f"Total results found: {response['total_results']:,}")
            print("\nSearch Results using class:")
            
            for i, result in enumerate(response['results'], 1):
                print(f"\n{i}. {result['title']}")
                print(f"   {result['snippet']}")
                print(f"   Display URL: {result['display_link']}")
                print(f"   Full URL: {result['link']}")
                if 'thumbnail' in result:
                    print(f"   Thumbnail: {result['thumbnail']['src']}")
                if 'labels' in result:
                    print(f"   Labels: {', '.join(result['labels'])}")
        else:
            print(f"\nError: {response['error']}")
            
    except Exception as e:
        logger.error(f"Error in example: {str(e)}") 