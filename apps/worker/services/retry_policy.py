"""
Retry & Dead-letter policy — Phase 07.
Classifies errors as transient/permanent/quota and applies retry strategy.
"""
from __future__ import annotations
from enum import Enum


class ErrorCategory(Enum):
    TRANSIENT = "transient"  # Retry with backoff
    PERMANENT = "permanent"  # Dead-letter, no retry
    QUOTA = "quota"  # Retry after cooldown


def classify_error(exception: Exception) -> ErrorCategory:
    """Classify an exception into retry category."""
    msg = str(exception).lower()

    if any(kw in msg for kw in ['timeout', 'connection', 'temporary', 'rate limit', '503']):
        return ErrorCategory.TRANSIENT

    if any(kw in msg for kw in ['quota', 'exceeded', '429']):
        return ErrorCategory.QUOTA

    if any(kw in msg for kw in ['not found', '404', 'invalid', 'permission', 'unauthorized', '403', '401']):
        return ErrorCategory.PERMANENT

    return ErrorCategory.TRANSIENT  # Default: retry


def get_retry_delay(attempt: int, category: ErrorCategory) -> int:
    """
    Calculate retry delay in seconds.

    - TRANSIENT: exponential backoff (2^attempt * 5s), max 60s
    - QUOTA: fixed 120s cooldown
    - PERMANENT: 0 (no retry)
    """
    if category == ErrorCategory.PERMANENT:
        return 0
    if category == ErrorCategory.QUOTA:
        return 120
    # Exponential backoff: 5, 10, 20, 40, 60, 60...
    delay = min(2 ** attempt * 5, 60)
    return delay


MAX_RETRIES = 3


def should_retry(attempt: int, category: ErrorCategory) -> bool:
    """Check if retry is allowed."""
    if category == ErrorCategory.PERMANENT:
        return False
    return attempt < MAX_RETRIES
