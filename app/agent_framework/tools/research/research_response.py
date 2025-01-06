"""Research Tool Response
====================

Response classes for the Research Tool.

Public Components:
- ResearchResponse: Response class for research results

Design Decisions:
- Uses dataclasses for clean serialization
- Implements proper type hints
- Follows response pattern
"""

from dataclasses import dataclass
from typing import Optional
from ..tools_utils import BaseToolResponse, ToolResponseStatus

@dataclass
class ResearchResponse(BaseToolResponse):
    """Response class for research results."""
    report: Optional[str] = None
    
    def to_string(self) -> str:
        """Convert response to JSON string."""
        response_dict = {
            "status": self.status.value,
            "message": self.message,
            "error": self.error,
            "report": self.report
        }
        return super().to_string() 