"""
Système de logging professionnel pour Le Maître Mot
===================================================

Fonctionnalités:
- Contexte partagé (request_id, correlation_id, chapter_code, pipeline, etc.)
- Tags/prefixes par module ([PIPELINE], [TESTS_DYN], [GENERATOR], etc.)
- Configuration via ENV (LOG_LEVEL, LOG_VERBOSE, LOG_MODULES, LOG_AUDIT)
- Duration_ms et outcome sur événements clés
- Prévention des doublons ERROR
- Format key=value, 1 ligne, pas de PII, truncate listes >20
"""

import logging
import json
import os
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional, List, Set
from datetime import datetime
from functools import wraps
import re

# Context variables pour le contexte partagé (thread-safe pour async)
_request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})

# Configuration ENV
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_VERBOSE = os.getenv('LOG_VERBOSE', '0') == '1'
LOG_MODULES = set(os.getenv('LOG_MODULES', '').split(',')) if os.getenv('LOG_MODULES') else None
LOG_AUDIT = os.getenv('LOG_AUDIT', '0') == '1'

# Mapping des modules aux tags
MODULE_TAGS = {
    'PIPELINE': '[PIPELINE]',
    'TESTS_DYN': '[TESTS_DYN]',
    'GENERATOR': '[GENERATOR]',
    'CACHE': '[CACHE]',
    'PERSIST': '[PERSIST]',
    'HTTP': '[HTTP]',
}


class ObservabilityFormatter(logging.Formatter):
    """Formatter structuré key=value, 1 ligne, pas de PII"""
    
    def _truncate_list(self, value: Any, max_items: int = 20) -> Any:
        """Tronque les listes > max_items"""
        if isinstance(value, list) and len(value) > max_items:
            return value[:max_items] + [f"... ({len(value) - max_items} more)"]
        return value
    
    def _format_value(self, value: Any) -> str:
        """Formate une valeur de manière safe (pas de PII, truncate)"""
        if isinstance(value, list):
            value = self._truncate_list(value)
        if isinstance(value, dict):
            # Ne pas dumper les dicts énormes
            if len(str(value)) > 200:
                return f"<dict with {len(value)} keys>"
        return str(value)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format: [LEVEL][TAG] key=value key=value ... message"""
        parts = []
        
        # Level
        parts.append(f"[{record.levelname}]")
        
        # Tag (si présent)
        tag = getattr(record, 'log_tag', None)
        if tag:
            parts.append(tag)
        
        # Contexte partagé
        ctx = _request_context.get({})
        context_keys = [
            'request_id', 'correlation_id', 'chapter_code', 'code_officiel',
            'pipeline', 'difficulty', 'offer', 'seed', 'generator_key',
            'template_id', 'variant_id', 'exercise_type', 'exercise_id',
            'admin_exercise_id', 'chapter_backend'
        ]
        for key in context_keys:
            if key in ctx:
                value = self._format_value(ctx[key])
                parts.append(f"{key}={value}")
        
        # Champs custom du record
        custom_keys = [
            'event', 'outcome', 'reason', 'duration_ms', 'pool_size',
            'missing_placeholders', 'available_keys_count', 'template_id',
            'generator_key', 'variant_id', 'pedagogy_mode', 'hint_level',
            'chapter_code', 'code_officiel', 'pipeline', 'difficulty', 'offer',
            'seed', 'exercise_id', 'admin_exercise_id', 'chapter_backend',
            'exercise_type', 'cache_hit', 'cache_miss', 'db_count'
        ]
        for key in custom_keys:
            if hasattr(record, key):
                value = getattr(record, key)
                if value is not None:
                    value = self._format_value(value)
                    parts.append(f"{key}={value}")
        
        # Message
        message = record.getMessage()
        parts.append(message)
        
        # Exception (seulement au point de capture)
        if record.exc_info and getattr(record, 'log_exception', True):
            parts.append(f"exception={self.formatException(record.exc_info)}")
        
        return " ".join(parts)


def configure_logging():
    """Configure le système de logging selon ENV"""
    logger = logging.getLogger('lemaitremot')
    logger.handlers.clear()
    
    # Niveau selon ENV
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
    }
    logger.setLevel(level_map.get(LOG_LEVEL, logging.INFO))
    
    # Formatter
    formatter = ObservabilityFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Pas de propagation pour éviter doublons
    logger.propagate = False
    
    return logger


# Logger global
_logger = configure_logging()


class ObservabilityLogger:
    """Logger avec contexte partagé et tags"""
    
    def __init__(self, module: Optional[str] = None):
        self.module = module
        self.tag = MODULE_TAGS.get(module, '') if module else ''
        self.logger = _logger
    
    def _should_log(self, level: str, module: Optional[str] = None) -> bool:
        """Vérifie si on doit logger selon LOG_VERBOSE et LOG_MODULES"""
        # Si LOG_MODULES est défini, ne logger que ces modules
        if LOG_MODULES and module and module not in LOG_MODULES:
            return False
        
        # DEBUG uniquement si LOG_VERBOSE=1
        if level == 'DEBUG' and not LOG_VERBOSE:
            return False
        
        # LOG_AUDIT: uniquement INFO/WARNING/ERROR (pas DEBUG)
        if LOG_AUDIT and level == 'DEBUG':
            return False
        
        return True
    
    def _create_record(self, level: str, message: str, **kwargs) -> None:
        """Crée un record de log avec contexte"""
        if not self._should_log(level, self.module):
            return
        
        # Extra fields
        extra = {
            'log_tag': self.tag,
            **kwargs
        }
        # Nettoyage des clés réservées pour éviter les collisions
        extra.pop('exc_info', None)
        extra.pop('stack_info', None)
        
        # Exception handling (éviter doublons)
        exc_info = kwargs.pop('exc_info', False)
        if exc_info:
            extra['log_exception'] = True
        
        # Log
        getattr(self.logger, level.lower())(message, extra=extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        """DEBUG: détails (pools, listes, keys manquantes) uniquement si LOG_VERBOSE=1"""
        self._create_record('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """INFO: flux normal, décisions clés, variant"""
        self._create_record('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """WARNING: fallback, incohérence, pool vide évité"""
        self._create_record('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """ERROR: exceptions/422 avec contexte complet"""
        self._create_record('ERROR', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """CRITICAL: erreurs système"""
        self._create_record('CRITICAL', message, **kwargs)


def get_logger(module: Optional[str] = None) -> ObservabilityLogger:
    """Obtient un logger pour un module"""
    return ObservabilityLogger(module)


# ============================================================================
# Contexte partagé (request_id, correlation_id, etc.)
# ============================================================================

def set_request_context(**kwargs):
    """Définit le contexte partagé pour cette requête"""
    ctx = _request_context.get({}).copy()
    ctx.update(kwargs)
    _request_context.set(ctx)


def get_request_context() -> Dict[str, Any]:
    """Obtient le contexte partagé actuel"""
    return _request_context.get({}).copy()


def clear_request_context():
    """Efface le contexte partagé"""
    _request_context.set({})


def ensure_request_id() -> str:
    """Assure qu'un request_id existe, le crée si absent"""
    ctx = _request_context.get({})
    if 'request_id' not in ctx:
        ctx['request_id'] = str(uuid.uuid4())[:8]
        _request_context.set(ctx)
    return ctx['request_id']


# ============================================================================
# Helpers pour prévention pool vide
# ============================================================================

def safe_random_choice(items: List[Any], context: Dict[str, Any], logger: ObservabilityLogger) -> Any:
    """random.choice avec vérification préalable et WARNING si liste vide"""
    if not items:
        logger.warning(
            "pool_empty_prevented",
            event="pool_empty",
            outcome="error",
            reason="list_empty",
            pool_size=0,
            **context
        )
        raise ValueError(f"random.choice() called on empty list: {context}")
    
    if len(items) == 1:
        return items[0]
    
    import random
    selected = random.choice(items)
    
    if LOG_VERBOSE:
        logger.debug(
            "random_choice",
            event="random_choice",
            outcome="success",
            pool_size=len(items),
            selected_index=items.index(selected) if selected in items else None,
            **context
        )
    
    return selected


def safe_randrange(start: int, stop: Optional[int] = None, step: int = 1, context: Dict[str, Any] = None, logger: ObservabilityLogger = None) -> int:
    """random.randrange avec vérification préalable et WARNING si range vide"""
    import random
    
    if stop is None:
        stop = start
        start = 0
    
    if start >= stop:
        if logger and context:
            logger.warning(
                "randrange_empty_prevented",
                event="randrange_empty",
                outcome="error",
                reason="empty_range",
                range_start=start,
                range_stop=stop,
                **context
            )
        raise ValueError(f"random.randrange() called with empty range: start={start}, stop={stop}, context={context}")
    
    result = random.randrange(start, stop, step)
    
    if LOG_VERBOSE and logger and context:
        logger.debug(
            "randrange",
            event="randrange",
            outcome="success",
            range_start=start,
            range_stop=stop,
            result=result,
            **context
        )
    
    return result

