"""Google Search Response Formatter
============================

Formats Google Search API responses into structured data.

Public Components:
- ResponseFormatter: Class for formatting search results
- SearchResult: Data class for structured search results

Design Decisions:
- Extracts rich metadata from pagemap
- Handles missing fields gracefully
- Provides consistent result structure
- Implements proper type hints
- Makes SearchResult JSON serializable
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class SearchResult:
    """Structured search result data."""
    title: str
    link: str
    snippet: str
    html_snippet: str
    html_title: str
    display_link: str
    kind: str
    cache_id: str
    file_format: str
    formatted_url: str
    mime: str
    rich_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the search result to a dictionary."""
        return asdict(self)

class ResponseFormatter:
    """Formatter for Google Search API responses."""
    
    @staticmethod
    def extract_meta_tags(metatags: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract metadata from metatags.
        
        Args:
            metatags: Raw metatags dictionary
            
        Returns:
            Formatted metadata dictionary
        """
        return {
            'description': metatags.get('og:description', metatags.get('description', '')),
            'keywords': metatags.get('keywords', ''),
            'author': metatags.get('author', ''),
            'published_date': metatags.get('article:published_time', '')
        }
    
    @staticmethod
    def extract_rich_data(pagemap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract rich data from pagemap.
        
        Args:
            pagemap: Raw pagemap dictionary
            
        Returns:
            Formatted rich data dictionary
        """
        rich_data = {}
        
        # Extract article content
        if 'articleBody' in pagemap:
            rich_data['article_body'] = pagemap['articleBody']
            
        # Extract meta tags
        if 'metatags' in pagemap and pagemap['metatags']:
            rich_data['meta'] = ResponseFormatter.extract_meta_tags(pagemap['metatags'][0])
            
        # Extract video information
        if 'videoObject' in pagemap:
            rich_data['video'] = pagemap['videoObject']
            
        # Extract article metadata
        if 'article' in pagemap:
            rich_data['article_meta'] = pagemap['article']
            
        # Extract breadcrumbs
        if 'breadcrumb' in pagemap:
            rich_data['breadcrumbs'] = pagemap['breadcrumb']
            
        # Extract person information
        if 'person' in pagemap:
            rich_data['person'] = pagemap['person']
            
        # Extract organization information
        if 'organization' in pagemap:
            rich_data['organization'] = pagemap['organization']
            
        # Extract website information
        if 'website' in pagemap:
            rich_data['website'] = pagemap['website']
            
        # Extract review information
        if 'review' in pagemap:
            rich_data['review'] = pagemap['review']
            
        # Extract product information
        if 'product' in pagemap:
            rich_data['product'] = pagemap['product']
            
        # Extract offer information
        if 'offer' in pagemap:
            rich_data['offer'] = pagemap['offer']
            
        # Extract thumbnail information
        if 'cse_thumbnail' in pagemap:
            rich_data['thumbnail'] = pagemap['cse_thumbnail']
            
        # Extract image information
        if 'cse_image' in pagemap:
            rich_data['image'] = pagemap['cse_image']
            
        return rich_data
    
    @staticmethod
    def format_search_result(item: Dict[str, Any]) -> SearchResult:
        """
        Format a single search result.
        
        Args:
            item: Raw search result item
            
        Returns:
            Formatted SearchResult object
        """
        result = SearchResult(
            title=item['title'],
            link=item['link'],
            snippet=item.get('snippet', ''),
            html_snippet=item.get('htmlSnippet', ''),
            html_title=item.get('htmlTitle', ''),
            display_link=item.get('displayLink', ''),
            kind=item.get('kind', ''),
            cache_id=item.get('cacheId', ''),
            file_format=item.get('fileFormat', ''),
            formatted_url=item.get('formattedUrl', ''),
            mime=item.get('mime', ''),
            rich_data={}
        )
        
        # Add rich data if available
        if 'pagemap' in item:
            result.rich_data = ResponseFormatter.extract_rich_data(item['pagemap'])
            
        return result
    
    @staticmethod
    def format_search_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the complete search response.
        
        Args:
            response: Raw API response
            
        Returns:
            Formatted response dictionary
        """
        # Extract search information
        search_info = response.get('searchInformation', {})
        total_results = int(search_info.get('totalResults', 0))
        search_time = float(search_info.get('searchTime', 0))
        
        # Format results
        results = []
        if 'items' in response:
            for item in response['items']:
                try:
                    search_result = ResponseFormatter.format_search_result(item)
                    results.append(search_result.to_dict())  # Convert to dict for JSON serialization
                except Exception as e:
                    logger.error(f"Failed to format search result: {str(e)}")
                    
        return {
            'results': results,
            'total_results': total_results,
            'search_time': search_time
        } 