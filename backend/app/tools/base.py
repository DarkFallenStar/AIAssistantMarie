from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    success: bool = Field(..., description="Whether the tool execution was successful")
    data: Any = Field(default=None, description="Structured data returned by the tool")
    message: str = Field(..., description="Human-readable execution message or summary")

class BaseTool(ABC):
    """
    Abstract base class for all operational tools executed by agents.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool accomplishes."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Executes the tool with provided arguments and returns a structured ToolResult.
        """
        pass
