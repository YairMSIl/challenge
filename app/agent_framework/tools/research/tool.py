"""Research Tool Implementation
=========================

Main implementation of the Research Tool.

Public Components:
- ResearchTool: Tool class for conducting research

Design Decisions:
- Uses ResearchAgent for core functionality
- Implements proper error handling
- Provides rich research reports
- Follows tool interface pattern
"""

from typing import Optional, List
from app.agent_framework.agents.research_agent import ResearchAgent
from app.models.artifact import ArtifactType
from ..tools_utils import BaseTool, ToolResponseStatus
from ..tool_constants import ToolName, RESEARCH_TOOL_INPUTS
from .research_response import ResearchResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ResearchTool(BaseTool):
    """Tool for conducting internet research and generating reports."""
    
    name = ToolName.RESEARCH.value
    description = """
    This tool conducts internet research on a given topic and generates comprehensive reports.
    It returns a JSON string containing either the research report or an error message.
    The report includes citations and follows a structured format.
    """
    inputs = RESEARCH_TOOL_INPUTS
    output_type = "string"  # Returns JSON string
    
    def __init__(self, session_id: Optional[str] = None, artifacts: Optional[List] = None):
        """
        Initialize the Research Tool.
        
        Args:
            session_id: Optional session identifier for tracking
            artifacts: Optional list to store research results as artifacts
        """
        super().__init__(session_id, artifacts)
        logger.info(f"ResearchTool initialized for session {session_id}")
    
    def forward(self, query: str) -> str:
        """
        Conduct research and generate a report based on the query.
        
        Args:
            query: Research topic or question to investigate
            
        Returns:
            JSON string containing:
                status: Status of the research (success/error)
                report: Generated research report if successful
                error: Optional error message if research failed
        """
        try:
            logger.info(f"Starting research for query: {query[:50]}...")
            
            # Create a new research agent instance for this request
            research_agent = ResearchAgent(session_id=self.artifact_handler.session_id)
            
            # Get the research report and sanitize it
            report = research_agent.generate_research(query)
            
            # Normalize newlines and remove any escaped characters
            report = report.replace('\\n', '\n')  # Convert escaped newlines to actual newlines
            report = report.replace('\\t', '\t')  # Convert escaped tabs to actual tabs
            report = report.replace('\\"', '"')   # Convert escaped quotes to actual quotes
            report = report.strip()               # Remove any leading/trailing whitespace
            
            # Store research result as an artifact
            self.artifact_handler.add_artifact(report, ArtifactType.RESEARCH.value)
            
            return ResearchResponse(
                status=ToolResponseStatus.SUCCESS,
                message=f"Research completed successfully. See the report for details in the artifact section.\n\n{report}",
                report=report
            ).to_string()
            
        except ValueError as e:
            # Handle budget exceeded errors
            error_msg = f"Research budget exceeded: {str(e)}"
            logger.error(error_msg)
            return ResearchResponse(
                status=ToolResponseStatus.ERROR,
                error=error_msg
            ).to_string()
            
        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            logger.error(error_msg)
            return ResearchResponse(
                status=ToolResponseStatus.ERROR,
                error=error_msg
            ).to_string() 