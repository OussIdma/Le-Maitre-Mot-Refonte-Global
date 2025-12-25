"""
P0 - HTML Sanitizer (fonction pure, sans dépendances externes)

Sanitise le HTML pour prévenir les attaques XSS tout en préservant
les éléments nécessaires (SVG, table, etc.).
"""
import re
from typing import Dict, List, Any, Optional


def sanitize_html(input_html: str, *, max_len: int = 300_000) -> Dict[str, Any]:
    """
    Sanitise le HTML pour prévenir les attaques XSS.
    
    Args:
        input_html: HTML à sanitizer
        max_len: Longueur maximale acceptée (défaut: 300_000)
    
    Returns:
        {
            "html": <html_sanitized>,
            "changed": <bool>,
            "reasons": <list[str]>,
            "rejected": <bool>,
            "reject_reason": <str|None>
        }
    """
    reasons: List[str] = []
    changed = False
    rejected = False
    reject_reason = None
    
    # Vérifier la longueur
    if len(input_html) > max_len:
        return {
            "html": "",
            "changed": False,
            "reasons": [],
            "rejected": True,
            "reject_reason": "HTML_TOO_LARGE"
        }
    
    sanitized = input_html
    
    # 1. Supprimer les blocs <script ...>...</script> (case-insensitive, multi-line)
    # Pattern non-greedy pour éviter les catastrophes
    script_pattern = re.compile(
        r'<script[^>]*>.*?</script>',
        re.IGNORECASE | re.DOTALL
    )
    if script_pattern.search(sanitized):
        sanitized = script_pattern.sub('', sanitized)
        changed = True
        reasons.append("Removed <script> tags")
    
    # 2. Supprimer les tags iframe/object/embed (leurs blocs complets)
    dangerous_tags = ['iframe', 'object', 'embed']
    for tag in dangerous_tags:
        # Pattern pour capturer le tag et son contenu jusqu'à la fermeture
        tag_pattern = re.compile(
            rf'<{tag}[^>]*>.*?</{tag}>',
            re.IGNORECASE | re.DOTALL
        )
        if tag_pattern.search(sanitized):
            sanitized = tag_pattern.sub('', sanitized)
            changed = True
            reasons.append(f"Removed <{tag}> tags")
    
    # 3. Supprimer les attributs on[a-z]+= (onclick, onerror, onload, etc.)
    # Pattern pour trouver les attributs événementiels
    event_attr_pattern = re.compile(
        r'\s+on[a-z]+\s*=\s*["\'][^"\']*["\']',
        re.IGNORECASE
    )
    if event_attr_pattern.search(sanitized):
        sanitized = event_attr_pattern.sub('', sanitized)
        changed = True
        reasons.append("Removed event handler attributes (onclick, onerror, etc.)")
    
    # 4. Neutraliser javascript: dans href/src/xlink:href (remplacer par "#")
    # Pattern pour href="javascript:..." ou href='javascript:...'
    js_href_pattern = re.compile(
        r'(href|src|xlink:href)\s*=\s*["\']javascript:[^"\']*["\']',
        re.IGNORECASE
    )
    if js_href_pattern.search(sanitized):
        sanitized = js_href_pattern.sub(r'\1="#"', sanitized)
        changed = True
        reasons.append("Neutralized javascript: URLs in href/src")
    
    # 5. Vérification finale : si on détecte encore du contenu dangereux après sanitization
    # Vérifier la présence de <script (même sans balise fermante complète)
    if re.search(r'<script', sanitized, re.IGNORECASE):
        rejected = True
        reject_reason = "HTML_UNSAFE_AFTER_SANITIZE"
        reasons.append("Detected <script after sanitization")
    
    # Vérifier la présence d'attributs événementiels restants
    if re.search(r'\son[a-z]+\s*=', sanitized, re.IGNORECASE):
        rejected = True
        reject_reason = "HTML_UNSAFE_AFTER_SANITIZE"
        reasons.append("Detected event handlers after sanitization")
    
    return {
        "html": sanitized,
        "changed": changed,
        "reasons": reasons,
        "rejected": rejected,
        "reject_reason": reject_reason
    }

