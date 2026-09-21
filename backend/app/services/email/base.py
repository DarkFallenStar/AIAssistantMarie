from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class EmailMessage(BaseModel):
    """
    Standardized email message model across all email providers (IMAP, Gmail, Graph, Mock).
    """
    id: str = Field(..., description="Unique identifier for the email")
    sender: str = Field(..., description="Sender name and email address")
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Subject line of the email")
    body: str = Field(..., description="Plain-text body content")
    snippet: str = Field(default="", description="Short preview of the email content")
    status: Literal["unread", "read", "draft", "sent"] = Field(default="unread")
    category: str = Field(default="general")
    received_at: str = Field(..., description="Timestamp or human-readable date of receipt")
    is_important: bool = Field(default=False)
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="MEDIUM")

class BaseEmailClient(ABC):
    """
    Abstract interface for email service providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'imap', 'mock', 'gmail', 'graph')."""
        pass

    @abstractmethod
    async def list_unread(self, limit: int = 10) -> List[EmailMessage]:
        """Lists unread emails from the inbox."""
        pass

    @abstractmethod
    async def list_all(self, status: Optional[str] = None, limit: int = 10) -> List[EmailMessage]:
        """Lists emails optionally filtered by status."""
        pass

    @abstractmethod
    async def get_by_id(self, email_id: str) -> Optional[EmailMessage]:
        """Retrieves a single email by ID."""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[EmailMessage]:
        """Searches emails by text query in sender, subject, or body."""
        pass

    @abstractmethod
    async def create_draft(self, recipient: str, subject: str, body: str) -> EmailMessage:
        """Saves an email draft without sending."""
        pass

    @abstractmethod
    async def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Dispatches an email (only called after explicit user confirmation)."""
        pass
