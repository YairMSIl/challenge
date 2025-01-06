"""Google Search Tool Implementation
==============================

Main implementation of the Google Search tool.

Public Components:
- GoogleSearchTool: Tool class for performing Google searches

Design Decisions:
- Uses dependency injection for API credentials
- Implements proper error handling
- Provides rich search results
- Follows tool interface pattern
"""

import os
from typing import Optional, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from ..tools_utils import BaseTool
from ..tool_constants import ToolConfig, ToolName, SEARCH_TOOL_INPUTS
from .mock_handler import MockHandler
from .response_formatter import ResponseFormatter
from utils.logging_config import get_logger

logger = get_logger(__name__)

class GoogleSearchTool(BaseTool):
    """Tool for performing Google searches using the Custom Search API."""
    
    name = ToolName.GOOGLE_SEARCH.value
    description = """
    This tool performs web searches using Google Custom Search API.
    It returns a JSON string containing search results or an error message.
    """
    inputs = SEARCH_TOOL_INPUTS
    output_type = "string"  # Returns JSON string
    
    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        """
        Initialize the Google Search tool.
        
        Args:
            api_key: Optional Google API key
            cse_id: Optional Custom Search Engine ID
        """
        super().__init__()
        load_dotenv()
        
        self.api_key = api_key or os.getenv(ToolConfig.GOOGLE_API_KEY)
        self.cse_id = cse_id or os.getenv(ToolConfig.GOOGLE_CSE_ID)
        
        if not self.api_key or not self.cse_id:
            raise ValueError(
                "Google API key and Custom Search Engine ID are required. "
                f"Set {ToolConfig.GOOGLE_API_KEY} and {ToolConfig.GOOGLE_CSE_ID} environment variables."
            )
        
        self.mock_handler = MockHandler()
        self.service = build('customsearch', 'v1', developerKey=self.api_key)
        logger.info("GoogleSearchTool initialized successfully")
        
    def _execute_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """
        Execute the search query.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            Raw API response
        """
        return self.service.cse().list(
            q=query,
            cx=self.cse_id,
            num=num_results,
            fields="items(title,link,snippet,pagemap(articleBody,metatags,videoObject,article,breadcrumb,person,organization,website,review,product,offer,cse_thumbnail,cse_image),displayLink,htmlSnippet,htmlTitle,kind,labels,cacheId,fileFormat,formattedUrl,htmlFormattedUrl,mime),searchInformation(searchTime,totalResults,formattedSearchTime,formattedTotalResults),queries,context"
        ).execute()
    
    def forward(self, query: str, num_results: int = ToolConfig.DEFAULT_SEARCH_RESULTS) -> str:
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
        try:
            # Validate input
            if not ToolConfig.MIN_SEARCH_RESULTS <= num_results <= ToolConfig.MAX_SEARCH_RESULTS:
                return self._create_error_response(
                    f"num_results must be between {ToolConfig.MIN_SEARCH_RESULTS} and {ToolConfig.MAX_SEARCH_RESULTS}"
                )
            
            logger.info(f"Performing Google search for query: {query}")
            
            # Try to get mock response first
            response = self.mock_handler.get_latest_response()
            
            if response is None:
                logger.debug("No mock response available, making API call")
                response = self._execute_search(query, num_results)
                self.mock_handler.save_response(response)
            
            # Format the response
            formatted_response = ResponseFormatter.format_search_response(response)
            
            return self._create_success_response(
                message="Search completed successfully",
                data=formatted_response
            )
            
        except HttpError as e:
            error_msg = f"Google API error: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg)
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg) 