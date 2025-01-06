"""Research Agent Integration
=======================

Provides an AI research assistant capable of performing internet research and generating comprehensive reports.

Public Components:
- ResearchAgent: Main class for conducting internet research and report generation
- generate_research(): Primary method for conducting research and generating reports

Design Decisions:
- Inherits from BaseAgent for standardized agent interface
- Uses SmolAgents ToolCallingAgent for structured research interactions
- Implements systematic research methodology:
  1. Query Understanding
  2. Information Gathering
  3. Source Validation
  4. Information Synthesis
  5. Report Generation
- Supports structured report formats with citations
- Implements cost tracking per session

Integration Notes:
- Requires GEMINI_API_KEY and GOOGLE_API_KEY in environment variables
- Uses CostTracker for budget management
- Uses Google Custom Search for web research
- Each instance should be created with a unique session ID
"""

import os
from typing import Optional
from smolagents.agents import ToolCallingAgent
from smolagents.prompts import TOOL_CALLING_SYSTEM_PROMPT

from app.agent_framework.agents.base_agent import BaseAgent, AgentConfig, AgentType
from app.agent_framework.agents.agent_utils import (
    calculate_tokens,
    extract_final_answer,
    format_agent_flow
)
from app.agent_framework.tools.google_search.tool import GoogleSearchTool
from utils.logging_config import get_logger

logger = get_logger(__name__)

# System prompt for the research agent
RESEARCH_AGENT_PROMPT = """You are an advanced AI research assistant designed to conduct thorough internet research and produce comprehensive reports. Your primary responsibilities include:

1. Research Planning:
   - Analyze research queries to identify key topics and subtopics
   - Develop a structured research plan
   - Identify relevant search terms and strategies

2. Information Gathering:
   - Conduct systematic web searches
   - Extract relevant information from various sources
   - Track and validate source credibility

3. Information Analysis:
   - Evaluate source reliability and credibility
   - Cross-reference information across multiple sources
   - Identify consensus and conflicting viewpoints

4. Report Generation:
   - Synthesize findings into coherent narratives
   - Structure information logically and clearly
   - Include proper citations and references
   - Highlight key insights and conclusions

5. Quality Control:
   - Ensure factual accuracy
   - Maintain objectivity
   - Provide balanced perspectives
   - Flag potential biases or limitations

Guidelines:
- Always cite sources for key information
- Maintain a clear research methodology
- Present balanced viewpoints
- Highlight areas of uncertainty
- Structure reports with clear sections
- Use appropriate formatting for readability
- Put the research results, in md format. 

Your output should be well-structured, factual, and comprehensive while remaining accessible to the target audience.
"""

class ResearchAgent(BaseAgent):
    """Agent implementation for conducting internet research."""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize Research Agent.
        
        Args:
            session_id: Unique identifier for the session
            
        Raises:
            ValueError: If session_id format is invalid
        """
        if session_id and not self._is_valid_session_id(session_id):
            raise ValueError("Invalid session ID format")
            
        config = AgentConfig(
            agent_type=AgentType.RESEARCH,
            required_env_vars=[
                'GEMINI_API_KEY',
                'GOOGLE_API_KEY',
                'GOOGLE_CSE_ID'
            ]
        )
        super().__init__(session_id, config)
        
        # Get required environment variables
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        if not self.google_api_key or not self.google_cse_id:
            raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID are required")
            
        self.search_tool = None
        self.configure()

    @staticmethod
    def _is_valid_session_id(session_id: str) -> bool:
        """
        Validate session ID format.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Add your session ID validation logic here
        # For example: must be alphanumeric and between 8-32 chars
        return (
            isinstance(session_id, str) and
            session_id.isalnum() and
            8 <= len(session_id) <= 32
        )

    def configure(self) -> None:
        """Configure agent with Google Search tool."""
        try:
            self.search_tool = GoogleSearchTool(
                api_key=self.google_api_key,
                cse_id=self.google_cse_id
            )
            logger.debug("Research Agent configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Research Agent: {str(e)}")
            raise

    def _create_agent(self) -> ToolCallingAgent:
        """Create a new agent instance with Google Search tool."""
        if not self.search_tool:
            raise RuntimeError("Search tool not initialized. Call configure() first.")
            
        return ToolCallingAgent(
            tools=[self.search_tool],
            model=self.model,
            system_prompt=TOOL_CALLING_SYSTEM_PROMPT + RESEARCH_AGENT_PROMPT
        )

    def generate_research(self, research_query: str) -> str:
        """
        Conduct research and generate a report.
        
        Args:
            research_query: The research topic or question
            
        Returns:
            Generated research report
            
        Raises:
            Exception: If API call fails or budget exceeded
        """
        try:
            logger.debug(f"Starting research for query: {research_query[:50]}...")
            agent = self._create_agent()
            
            # Calculate request cost
            request_data = {
                "input_tokens": calculate_tokens(research_query),
                "output_tokens": 0
            }
            
            # Get response from agent
            response = agent.run(research_query)
            final_report = extract_final_answer(response)
            
            # Update cost with actual output tokens
            request_data["output_tokens"] = calculate_tokens(final_report)
            self.cost_tracker.calculate_cost(request_data, self.session_id)
            
            logger.info(f"Research completed successfully for session {self.session_id}")
            return final_report
        except ValueError as e:
            logger.error(f"Budget exceeded for session {self.session_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Research generation failed for session {self.session_id}: {str(e)}")
            raise
