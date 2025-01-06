"""Research Agent Integration
=======================

Provides an AI research assistant capable of performing internet research and generating comprehensive reports.

Public Components:
- ResearchAgent: Main class for conducting internet research and report generation
- generate_research(): Primary method for conducting research and generating reports
- configure_research(): Setup function for API configuration

Design Decisions:
- Uses SmolAgents ToolCallingAgent for structured research interactions
- Implements systematic research methodology:
  1. Query Understanding
  2. Information Gathering
  3. Source Validation
  4. Information Synthesis
  5. Report Generation
- Supports structured report formats with citations
- Implements cost tracking for API usage
- Instance-based design: Each ResearchAgent instance represents a unique session
- Uses Google Custom Search API for web search capabilities
- Implements source validation and credibility checking

Integration Notes:
- Requires GEMINI_API_KEY and GOOGLE_API_KEY in environment variables
- Configurable via logging config
- Uses CostTracker for budget management
- Uses Google Custom Search for web research
- Each instance should be created with a unique session ID
"""

import os
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from smolagents.agents import ToolCallingAgent
from smolagents.prompts import TOOL_CALLING_SYSTEM_PROMPT
from smolagents import tool, LiteLLMModel
from app.models.artifact import Artifact
from utils.logging_config import get_logger
from app.cost_tracker.cost_tracker import CostTracker
from app.agent_framework.tools.google_search import GoogleSearchTool

# Get logger instance
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

Your output should be well-structured, factual, and comprehensive while remaining accessible to the target audience.
"""

class ResearchAgent:
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize Research Agent wrapper.
        
        Args:
            session_id: Unique identifier for the session. If None, a temporary ID will be used.
        """
        load_dotenv()
        self.session_id = session_id
        if session_id is None:
            self.session_id = "temp_session_123"  # TODO: Replace with proper session management
            logger.warning("Using temporary session ID. This should be replaced with proper session management.")
            
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        if not self.google_api_key or not self.google_cse_id:
            logger.error("GOOGLE_API_KEY or GOOGLE_CSE_ID not found in environment variables")
            raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID are required")
        
        self.configure()
        self.cost_tracker = CostTracker("research", self._calculate_request_cost)
        logger.info(f"ResearchAgent initialized successfully for session {self.session_id}")

    def configure(self) -> None:
        """Configure Research Agent with credentials."""
        try:
            # Initialize with LiteLLMModel using Gemini
            self.model = LiteLLMModel(
                model_id="gemini/gemini-2.0-flash-exp",
                api_key=self.api_key
            )
            
            # Initialize Google Search tool
            self.search_tool = GoogleSearchTool(
                api_key=self.google_api_key,
                cse_id=self.google_cse_id
            )
            
            logger.debug("Research Agent configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Research Agent: {str(e)}")
            raise

    def _create_agent(self) -> ToolCallingAgent:
        """Create a new agent instance for research."""
        return ToolCallingAgent(
            tools=[self.search_tool],  # Add Google Search tool to the agent
            model=self.model,
            system_prompt=TOOL_CALLING_SYSTEM_PROMPT + RESEARCH_AGENT_PROMPT
        )

    def _calculate_request_cost(self, request_data: Dict[str, Any]) -> float:
        """
        Calculate cost for a Research Agent request.
        
        Args:
            request_data: Dictionary containing input_tokens and output_tokens
            
        Returns:
            Calculated cost in dollars
            
        Note:
            Current pricing:
            - Input tokens: $0.01 per token
            - Output tokens: $0.02 per token
        """
        input_tokens = request_data.get("input_tokens", 0)
        output_tokens = request_data.get("output_tokens", 0)
        
        input_cost = input_tokens * 0.01  # $0.01 per input token
        output_cost = output_tokens * 0.02  # $0.02 per output token
        
        total_cost = input_cost + output_cost
        logger.debug(
            f"Calculated cost: ${total_cost:.6f} "
            f"(Input: {input_tokens} tokens = ${input_cost:.6f}, "
            f"Output: {output_tokens} tokens = ${output_cost:.6f})"
        )
        
        return total_cost

    def generate_research(self, research_query: str) -> str:
        """
        Conduct research and generate a report using the Research Agent.
        
        Args:
            research_query: The research topic or question
            
        Returns:
            Generated research report
            
        Raises:
            Exception: If API call fails or budget exceeded
        """
        try:
            logger.debug(f"Starting research for query: {research_query[:50]}... (session: {self.session_id})")
            agent = self._create_agent()
            
            # Calculate request cost before making API call
            request_data = {
                "input_tokens": len(research_query.split()),  # Simple approximation
                "output_tokens": 0  # Will be updated after response
            }
            
            # Get response from agent
            response = agent.run(research_query)
            
            # Extract final report
            final_report = str(response)
            
            # Update cost with actual output tokens
            request_data["output_tokens"] = len(final_report.split())
            
            # Track cost after successful API call
            self.cost_tracker.calculate_cost(request_data, self.session_id)
            
            logger.info(f"Research completed successfully for session {self.session_id}")
            return final_report
        except ValueError as e:
            # Re-raise budget exceeded error
            logger.error(f"Budget exceeded for session {self.session_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Research generation failed for session {self.session_id}: {str(e)}")
            raise
