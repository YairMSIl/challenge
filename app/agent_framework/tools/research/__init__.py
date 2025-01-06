"""Research Tool Package
===================

Tool for conducting internet research and generating comprehensive reports.

Public Components:
- ResearchTool: Main tool class for conducting research
- ResearchResponse: Response class for research results

Design Decisions:
- Splits functionality into focused modules
- Uses proper dependency injection
- Implements clean separation of concerns
"""

from .tool import ResearchTool
from .research_response import ResearchResponse

__all__ = ['ResearchTool', 'ResearchResponse'] 