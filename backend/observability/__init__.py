"""
Module d'observabilité pour Le Maître Mot
"""

from backend.observability.logger import (
    get_logger,
    set_request_context,
    get_request_context,
    clear_request_context,
    ensure_request_id,
    safe_random_choice,
    safe_randrange,
)

__all__ = [
    'get_logger',
    'set_request_context',
    'get_request_context',
    'clear_request_context',
    'ensure_request_id',
    'safe_random_choice',
    'safe_randrange',
]

