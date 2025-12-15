"""
Utility helpers for the interaction application.
"""

import hashlib
from typing import Tuple
from urllib.parse import urljoin

from django.http import HttpRequest

SESSION_KEY_NAME = 'interaction_session_key'


def ensure_session_key(request: HttpRequest) -> str:
    """
    Ensure the Django session has a key and return it.
    """

    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    request.session.setdefault(SESSION_KEY_NAME, session_key)
    return session_key


def build_fingerprint(request: HttpRequest) -> str:
    """
    Build a stable fingerprint for anonymous visitors. We rely on a subset of
    request meta fields to avoid storing PII.
    """

    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept = request.META.get('HTTP_ACCEPT', '')
    accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    ip = request.META.get('REMOTE_ADDR', '')
    raw = '|'.join([user_agent, accept, accept_lang, ip])
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def identity_from_request(request: HttpRequest) -> Tuple[str, str]:
    """
    Return (anonymous_key, fingerprint) for the incoming request.
    """

    return ensure_session_key(request), build_fingerprint(request)


def build_share_url(request: HttpRequest, token: str) -> str:
    """
    Build absolute share URL for a favorite folder.
    """

    return urljoin(request.build_absolute_uri('/'), f'interaction/share/{token}/')


def format_like_count(count: int) -> str:
    """
    Format like count for display (e.g., 1234 -> "1.2K", 1234567 -> "1.2M").
    """
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1000000:.1f}M"


def validate_share_token(token: str) -> bool:
    """
    Validate that a share token has the expected format (alphanumeric, 16-32 chars).
    """
    import re
    pattern = r'^[A-Za-z0-9]{16,32}$'
    return bool(re.match(pattern, token))


def get_user_like_history(actor, limit: int = 20):
    """
    Get recent like history for an actor (user or anonymous).
    Returns a queryset of Like objects ordered by creation time.
    """
    from .models import Like
    return Like.objects.filter(actor=actor).select_related('article').order_by('-created_time')[:limit]


def get_user_favorite_count(actor) -> int:
    """
    Get total number of favorite items across all folders for an actor.
    """
    from .models import FavoriteItem
    return FavoriteItem.objects.filter(folder__owner=actor).count()


def can_user_access_folder(actor, folder) -> bool:
    """
    Check if an actor can access a folder (owner or public folder).
    """
    return folder.owner == actor or folder.is_public


def generate_qr_code_data(share_url: str) -> str:
    """
    Generate QR code data URL for a share URL.
    This is a placeholder - in production you'd use a library like qrcode.
    """
    # For now, return a data URL placeholder
    # In production: import qrcode; img = qrcode.make(share_url); return img.get_data_url()
    return f"data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y4ZjlmYSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2NjYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5RUiBDb2RlPC90ZXh0Pjwvc3ZnPg=="

