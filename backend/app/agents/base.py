from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolResult

class AgentResponse(BaseModel):
    agent_name: str = Field(..., description="Name of the executing agent")
    intent: str = Field(..., description="Classified intent")
    tools_executed: List[str] = Field(default_factory=list, description="Names of tools executed by the agent")
    tool_results: List[ToolResult] = Field(default_factory=list, description="Structured results from tool executions")
    final_response: str = Field(..., description="Natural language response synthesized by LLM or fallback")
    raw_llm_response: Optional[str] = Field(default=None, description="Direct text output from LLM")
    llm_used: bool = Field(default=True, description="Whether an LLM was successfully used to generate the response")

class BaseAgent(ABC):
    """
    Abstract contract for specialized domain agents.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the specialized agent."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Persona and system instructions for the LLM."""
        pass

    @property
    @abstractmethod
    def tools(self) -> Dict[str, BaseTool]:
        """Dictionary of tools registered to this agent."""
        pass

    @abstractmethod
    async def handle(self, request: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Processes user request: determines tools, executes them, and synthesizes response with LLM.
        """
        pass
