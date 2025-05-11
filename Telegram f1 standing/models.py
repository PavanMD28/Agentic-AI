from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ModelType(str, Enum):
    """
    Enumeration of supported model types for LLM processing.
    """
    GEMINI = "gemini"
    GPT = "gpt"
    CUSTOM = "custom"

class FastMCPBase(BaseModel):
    """
    Base class for FastMCP protocol implementation.
    Provides common attributes for all MCP messages.
    """
    mcp_version: str = Field(default="1.0", description="MCP protocol version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    trace_id: str = Field(..., description="Unique trace identifier")

class Driver(FastMCPBase):
    """
    Represents a Formula 1 driver's standing information.
    """
    position: str = Field(..., description="Current position in standings")
    driver_name: str = Field(..., description="Driver's full name")
    points: str = Field(..., description="Current points")

class F1Standings(FastMCPBase):
    """
    Represents the complete Formula 1 standings data.
    Inherits from FastMCPBase for MCP protocol compliance.
    """
    standings: List[Driver] = Field(..., description="List of driver standings")
    season: str = Field(default="2024", description="Current F1 season")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional standings metadata")

class MessageContext(FastMCPBase):
    """
    Main message context for the F1 standings system.
    Implements FastMCP protocol for standardized message handling.
    
    Attributes:
        message_id (str): Unique identifier for the message
        message_type (str): Type of message being transmitted
        content (F1Standings): The F1 standings data
        source (str): Source of the message
        metadata (Dict): Additional message metadata
    """
    message_id: str = Field(..., description="Unique message identifier")
    message_type: str = Field(..., description="Type of message")
    content: F1Standings = Field(..., description="F1 standings content")
    source: str = Field(default="F1_API", description="Message source")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional message metadata"
    )

    class Config:
        """
        Pydantic model configuration.
        """
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_trace_context(self) -> Dict[str, Any]:
        """
        Returns the trace context for message tracking.
        
        Returns:
            Dict[str, Any]: Trace context information
        """
        return {
            "trace_id": self.trace_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "source": self.source
        }

    def validate_mcp_compliance(self) -> bool:
        """
        Validates if the message follows MCP protocol standards.
        
        Returns:
            bool: True if message is MCP compliant
        """
        return all([
            self.trace_id,
            self.message_id,
            isinstance(self.content, F1Standings),
            self.mcp_version
        ])