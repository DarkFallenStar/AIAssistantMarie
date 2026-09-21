from typing import Optional
from app.core.config import settings
from app.services.email.base import BaseEmailClient, EmailMessage
from app.services.email.imap_client import IMAPEmailClient
from app.services.email.mock_client import MockEmailClient

__all__ = [
    "BaseEmailClient",
    "EmailMessage",
    "IMAPEmailClient",
    "MockEmailClient",
    "get_email_client",
    "set_email_client",
]

_email_client_instance: Optional[BaseEmailClient] = None

def get_email_client(provider: Optional[str] = None) -> BaseEmailClient:
    """
    Factory function returning the active BaseEmailClient instance.
    - If set_email_client() was called with an override, that instance is returned.
    - If explicit provider 'imap' is requested and configured, returns IMAPEmailClient.
    - If explicit provider 'mock' is requested, returns MockEmailClient.
    - Otherwise, auto-detects: if IMAP_HOST and IMAP_USER are set in settings, uses IMAPEmailClient,
      else falls back to MockEmailClient with Supabase / In-memory sync.
    """
    global _email_client_instance
    if _email_client_instance is not None:
        return _email_client_instance

    p_lower = (provider or "").lower().strip()
    if p_lower == "imap":
        return IMAPEmailClient(
            host=settings.IMAP_HOST,
            port=settings.IMAP_PORT,
            username=settings.IMAP_USER,
            password=settings.IMAP_PASSWORD,
            use_ssl=settings.IMAP_USE_SSL
        )
    elif p_lower == "mock":
        return MockEmailClient()

    # Auto-detection from environment configuration
    if settings.IMAP_HOST and settings.IMAP_USER and settings.IMAP_PASSWORD:
        try:
            return IMAPEmailClient(
                host=settings.IMAP_HOST,
                port=settings.IMAP_PORT,
                username=settings.IMAP_USER,
                password=settings.IMAP_PASSWORD,
                use_ssl=settings.IMAP_USE_SSL
            )
        except Exception as exc:
            print(f"[EMAIL] Failed initializing IMAP client ({exc}), falling back to MockEmailClient")
            return MockEmailClient()

    return MockEmailClient()

def set_email_client(client: Optional[BaseEmailClient]):
    """Sets a global override for the email client (useful for unit testing)."""
    global _email_client_instance
    _email_client_instance = client
