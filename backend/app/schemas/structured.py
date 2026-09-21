from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class StructuredIntent(BaseModel):
    """
    Structured representation of user intent extracted by the LLM (Function Calling / Structured Output).
    """
    agent: Literal["financial", "secretary", "general"] = Field(
        ...,
        description="Target agent responsible for handling the request ('financial', 'secretary', or 'general')"
    )
    tool: Optional[str] = Field(
        None,
        description="Canonical name of the tool to be executed, or None if pure conversational interaction"
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the tool function"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Brief internal explanation from the LLM on why this tool or agent was selected"
    )
