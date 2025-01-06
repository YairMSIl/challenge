"""Research Tool Integration
======================

SmolAgents tool for conducting internet research and generating comprehensive reports.

Public Components:
- ResearchTool: Tool class for conducting research using Google Search and LLM
- ResearchResponse: Response class with serialization methods

Design Decisions:
- Creates new ResearchAgent instance per request with session tracking
- Uses structured research methodology with source validation
- Implements cost tracking for API usage
- Returns formatted research reports with citations
- Maintains session-aware operation per research query
- Integrates with logging system for debugging
- Uses proper response serialization
- Stores research results as artifacts for UI display

Integration Notes:
- Requires GEMINI_API_KEY and GOOGLE_API_KEY in environment variables
- Configurable via logging config
- Uses CostTracker for budget management
- Creates new ResearchAgent instance for each request
- Integrates with UI artifact system for displaying research results
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from smolagents import Tool
from app.agent_framework.agents.research_agent import ResearchAgent
from app.models.artifact import Artifact, ArtifactType
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)

@dataclass
class ResearchResponse:
    """Response class for research results."""
    success: bool
    report: Optional[str] = None
    error: Optional[str] = None

    def to_string(self) -> str:
        """Convert response to JSON string."""
        return json.dumps({
            "success": self.success,
            "report": self.report,
            "error": self.error
        })

class ResearchTool(Tool):
    """Tool for conducting internet research and generating reports."""
    
    name = "research"
    description = """
    This tool conducts internet research on a given topic and generates comprehensive reports.
    It returns a JSON string containing either the research report or an error message.
    The report includes citations and follows a structured format.
    """
    inputs = {
        "query": {
            "type": "string",
            "description": "Research topic or question to investigate",
        }
    }
    output_type = "string"  # Returns JSON string
    
    def __init__(self, session_id: Optional[str] = None, artifacts: Optional[List] = None):
        """
        Initialize the Research Tool with optional session ID and artifacts list.
        
        Args:
            session_id: Optional session identifier for tracking
            artifacts: Optional list to store research results as artifacts
        """
        super().__init__()
        self.session_id = session_id
        self.artifacts = artifacts if artifacts is not None else []
        logger.info(f"ResearchTool initialized for session {session_id}")
    
    def forward(self, query: str) -> str:
        """
        Conduct research and generate a report based on the query.
        
        Args:
            query: Research topic or question to investigate
            
        Returns:
            JSON string containing:
                success: Boolean indicating if research was successful
                report: Generated research report if successful
                error: Optional error message if research failed
        """
        try:
            logger.info(f"Starting research for query: {query[:50]}...")
            
            # Create a new research agent instance for this request
            research_agent = ResearchAgent(session_id=self.session_id)
            
            # Get the research report
            report = research_agent.generate_research(query)
            
            # Store research result as an artifact
            self.artifacts.append(Artifact(
                is_new=True,
                content=report,
                type=ArtifactType.RESEARCH
            ))
            
            return ResearchResponse(
                success=True,
                report=report,
                error=None
            ).to_string()
            
        except ValueError as e:
            # Handle budget exceeded errors
            error_msg = f"Research budget exceeded: {str(e)}"
            logger.error(error_msg)
            return ResearchResponse(
                success=False,
                error=error_msg
            ).to_string()
            
        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            logger.error(error_msg)
            return ResearchResponse(
                success=False,
                error=error_msg
            ).to_string()
