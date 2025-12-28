"""
Tests d'invariants pour générateurs Gold
=========================================

Ces tests vérifient des propriétés stables qui ne doivent JAMAIS être violées:
- Cohérence mathématique (résultats corrects)
- Reproductibilité (même seed = mêmes résultats)
- Sécurité (pas de placeholders, pas de XSS)

Ces tests sont plus stables que des snapshots car ils vérifient
des invariants métier plutôt que des outputs exacts.
"""
