from dataclasses import dataclass
from typing import Any

from enum import Enum, auto

class ArtifactType(Enum):
    """Enum for artifact types."""
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    RESEARCH = "research"
    SEARCH = "search"


@dataclass()
class Artifact:
    """Represents a generated artifact like an image or text response."""
    type: ArtifactType
    content: Any  # The actual artifact content
    is_new: bool  # Whether this is a newly generated artifact
    
    def __post_init__(self):
        """Validate artifact after initialization."""
        if not self.type:
            raise ValueError("Artifact type cannot be empty")
        if self.content is None:
            raise ValueError("Artifact content cannot be None")
