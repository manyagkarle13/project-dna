"""
One-time auth tokens for cross-domain OAuth handoff.

After a successful OAuth callback, the backend generates a short-lived token
and passes it as a query param when redirecting to the frontend.  The frontend
then exchanges the token for a real session via POST /api/auth/token-login.
"""

import uuid
from django.core.cache import cache

TOKEN_PREFIX = "oauthtoken:"
TOKEN_TTL = 300  # 5 minutes


def generate_auth_token(user_id: int) -> str:
    """Create a one-time token that maps to *user_id*.  Expires after TOKEN_TTL seconds."""
    token = uuid.uuid4().hex
    cache.set(f"{TOKEN_PREFIX}{token}", user_id, timeout=TOKEN_TTL)
    return token


def consume_auth_token(token: str):
    """Return the user_id for *token* and delete it (one-time use).

    Returns ``None`` if the token is invalid or expired.
    """
    key = f"{TOKEN_PREFIX}{token}"
    user_id = cache.get(key)
    if user_id is not None:
        cache.delete(key)
    return user_id
