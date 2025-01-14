"""Tool Utilities
==============

Common utilities and base classes for SmolAgents tools.

Public Components:
- BaseToolResponse: Base response class for all tools
- BaseTool: Abstract base class for all tools
- ToolResponseStatus: Enum for tool response statuses
- ArtifactHandler: Helper class for handling tool artifacts

Design Decisions:
- Uses dataclasses for consistent response handling
- Implements common logging and error handling
- Provides base functionality for all tools
- Standardizes response serialization
- Centralizes artifact handling logic
"""

import json
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from smolagents import Tool
from app.models.artifact import Artifact
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ToolResponseStatus(Enum):
    """Enum for tool response statuses."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"

@dataclass
class BaseToolResponse:
    """Base response class for all tools."""
    status: ToolResponseStatus
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_string(self) -> str:
        """Convert response to JSON string."""
        return json.dumps({
            "status": self.status.value,
            "message": self.message,
            "error": self.error,
            "data": self.data
        })

class ArtifactHandler:
    """Helper class for handling tool artifacts."""
    
    def __init__(self, session_id: Optional[str] = None, artifacts: Optional[List[Artifact]] = None):
        """Initialize the artifact handler."""
        self.session_id = session_id
        self.artifacts = artifacts if artifacts is not None else []
        
    def add_artifact(self, content: Any, artifact_type: str) -> None:
        """Add a new artifact to the list."""
        if self.artifacts is not None:
            self.artifacts.append(Artifact(
                is_new=True,
                content=content,
                type=artifact_type
            ))
            logger.debug(f"Added new {artifact_type} artifact")

class BaseTool(Tool):
    """Abstract base class for all tools.

    This class provides core functionality for tools including artifact handling and logging.
    All tool implementations should inherit from this class.

    Tools serve two key purposes:
    1. Return a string response that the calling agent can use in its response to the user
    2. Generate artifacts (images, audio, etc) that are displayed to the user in the UI

    The artifact_handler manages generated content during tool execution:

    Usage:
        class MyTool(BaseTool):
            def forward(self, prompt: str) -> str:
                # Generate some content
                result = self.generate_content(prompt)
                
                # Store non-verbal content as an artifact for UI display
                self.artifact_handler.add_artifact(
                    content=result["image"],
                    artifact_type=ArtifactType.IMAGE.value  # or AUDIO, TEXT etc
                )

                # Return string response for the agent to use
                return self._create_success_response(
                    message="Generated an image of a sunset over mountains",
                    data={"description": "The image shows a vibrant sunset..."}
                )

    The artifact_handler requires a session_id to track artifacts across requests.
    Artifacts are stored in self.artifact_handler.artifacts and displayed in the UI.
    The string response from forward() is passed to the calling agent to incorporate
    into its response to the user.
    """
    
    def __init__(self, session_id: Optional[str] = None, artifacts: Optional[List] = None):
        """Initialize the base tool."""
        super().__init__()
        self.artifact_handler = ArtifactHandler(session_id, artifacts)
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Set up logging for the tool."""
        self.logger = get_logger(self.__class__.__name__)
        
    def _create_success_response(self, message: str, data: Optional[Dict[str, Any]] = None) -> str:
        """Create a success response."""
        return BaseToolResponse(
            status=ToolResponseStatus.SUCCESS,
            message=message,
            data=data
        ).to_string()
        
    def _create_error_response(self, error: str) -> str:
        """Create an error response."""
        self.logger.error(error)
        return BaseToolResponse(
            status=ToolResponseStatus.ERROR,
            error=error
        ).to_string()

def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ('true', 't', 'yes', 'y', '1', 'on')

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists at {path}") 