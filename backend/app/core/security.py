import secrets
from typing import Optional
from fastapi import HTTPException, Security, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# HTTPBearer scheme with auto_error=False to allow flexible header inspection and permissive dev mode
_bearer_scheme = HTTPBearer(auto_error=False)


def mask_secret(value: Optional[str], keep_start: int = 4, keep_end: int = 4) -> str:
    """Masks a secret string for safe log presentation without leaking credentials."""
    if not value:
        return "<unset>"
    if len(value) <= (keep_start + keep_end):
        return "***"
    return f"{value[:keep_start]}...{value[-keep_end:]}"


async def verify_api_bearer_token(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> bool:
    """
    Validates API authorization against settings.API_BEARER_TOKEN.
    
    Accepts:
      - 'Authorization: Bearer <token>'
      - 'X-API-Key: <token>'
    
    Security Behavior:
      - If API_BEARER_TOKEN is configured: requires valid token verified via constant-time comparison.
        Returns 401 Unauthorized if missing or invalid.
      - If API_BEARER_TOKEN is empty/unset: permits requests in development with a security audit notice.
    """
    expected_token = (settings.API_BEARER_TOKEN or "").strip()
    
    # If no token is configured in the environment, run in permissive development mode
    if not expected_token:
        return True

    provided_token: Optional[str] = None
    if auth_credentials and auth_credentials.credentials:
        provided_token = auth_credentials.credentials.strip()
    elif x_api_key and x_api_key.strip():
        provided_token = x_api_key.strip()

    if not provided_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización inválido o no suministrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to protect against timing attacks
    if not secrets.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


async def verify_bank_webhook_secret(
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
) -> bool:
    """
    Validates the bank notification webhook secret against settings.BANK_WEBHOOK_SECRET.
    
    Security Behavior:
      - If BANK_WEBHOOK_SECRET is configured: requires matching X-Webhook-Secret header.
        Uses constant-time comparison. Returns 401 Unauthorized if invalid or missing.
      - If BANK_WEBHOOK_SECRET is empty/unset: permits requests in development.
    """
    expected_secret = (settings.BANK_WEBHOOK_SECRET or "").strip()
    
    if not expected_secret:
        return True

    if not x_webhook_secret or not x_webhook_secret.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header 'X-Webhook-Secret' es obligatorio cuando la seguridad de webhook está activada."
        )

    if not secrets.compare_digest(x_webhook_secret.strip(), expected_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook secret inválido."
        )

    return True
