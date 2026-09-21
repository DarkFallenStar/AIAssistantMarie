from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

class SubIntentAction(BaseModel):
    agent: Literal["financial", "secretary", "general"]
    tool: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = None

class StructuredIntent(BaseModel):
    """
    Structured representation of user intent extracted by the LLM (Function Calling / Structured Output).
    """
    agent: Literal["financial", "secretary", "general", "combined"] = Field(
        ...,
        description="Target agent responsible for handling the request ('financial', 'secretary', 'general', or 'combined')"
    )
    tool: Optional[str] = Field(
        None,
        description="Canonical name of the tool to be executed, or None if pure conversational interaction or combined"
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the tool function"
    )
    actions: Optional[List[SubIntentAction]] = Field(
        default=None,
        description="List of sub-actions to execute when combining multiple agents"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Brief internal explanation from the LLM on why this tool or agent was selected"
    )
