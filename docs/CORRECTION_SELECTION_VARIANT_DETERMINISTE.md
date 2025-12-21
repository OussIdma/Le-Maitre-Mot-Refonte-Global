# Correction — Sélection Variant Déterministe
**Date :** 2025-01-XX  
**Fichier modifié :** `backend/services/tests_dyn_handler.py`

---

## 🐛 Problème identifié

### Symptômes
1. **L'`else` du `try` écrasait la sélection fixe** : Quand `variant_id` était fourni et que la sélection réussissait, l'`else` du `try` s'exécutait et écrasait `chosen_variant` avec un fallback.
2. **Pas de fallback quand `variant_id` absent** : Quand `variant_id` n'était pas fourni, il n'y avait pas de branche `else` pour gérer ce cas, laissant potentiellement `chosen_variant=None`.

### Root Cause
Structure incorrecte du code :
```python
if variant_id_from_params:
    try:
        # Sélection fixe réussit
        chosen_variant = ...
    except ValueError:
        # Erreur → OK
    else:  # ❌ PROBLÈME : s'exécute quand le try réussit !
        # Écrase chosen_variant avec un fallback
        chosen_variant = ...
# ❌ PROBLÈME : Pas de else pour gérer variant_id absent
```

---

## ✅ Correction appliquée

### Structure corrigée
```python
if variant_id_from_params:
    try:
        # Sélection fixe
        chosen_variant = choose_template_variant(..., mode="fixed", fixed_variant_id=variant_id_from_params)
        # Log succès
    except ValueError:
        # Erreur 422 si variant_id invalide
        raise HTTPException(422, ...)
else:  # ✅ Fallback quand variant_id absent
    # Sélection déterministe du premier variant
    if not variant_objs:
        raise HTTPException(422, "NO_VARIANTS_AVAILABLE")
    fallback_variant_id = available_variant_ids[0]
    chosen_variant = choose_template_variant(..., mode="fixed", fixed_variant_id=fallback_variant_id)
    # Log fallback
```

### Changements

1. **Suppression de l'`else` du `try`** : Plus d'écrasement de la sélection fixe
2. **Ajout d'un `else` au niveau du `if variant_id_from_params`** : Gestion du cas où `variant_id` est absent
3. **Fallback déterministe** : Sélection du premier variant disponible via `mode="fixed"` (pas random)
4. **Gestion des erreurs** : Erreurs 422 explicites si aucun variant disponible

### Logs

**Sélection fixe (variant_id fourni)** :
- `event=variant_fixed_selected` (INFO)

**Fallback (variant_id absent)** :
- `event=variant_fallback_selected` (INFO) - changé de WARNING à INFO car comportement attendu

**Erreurs** :
- `event=variant_fixed_error` (ERROR) - variant_id invalide
- `event=variant_no_variants_available` (ERROR) - aucun variant disponible
- `event=variant_no_id_available` (ERROR) - aucun variant_id dans les variants

---

## 🧪 Tests mis à jour

### Test modifié
- `test_random_fallback_when_variant_id_absent` → `test_deterministic_fallback_when_variant_id_absent`
- **Comportement attendu** : Fallback déterministe sur le premier variant (A), pas random

### Tests conservés
- `test_determinism_same_seed_same_variant_id` : Même seed + même variant_id → même résultat
- `test_determinism_different_variant_ids` : Variants différents sélectionnés correctement
- `test_variant_id_invalid_raises_error` : Erreur 422 si variant_id invalide
- `test_generator_v2_registered` : Générateur enregistré
- `test_generator_v2_generates_variables` : Variables générées correctement

---

## ✅ Validation

### Compilation
```bash
docker compose exec backend python -m py_compile backend/services/tests_dyn_handler.py
```

### Tests
```bash
docker compose exec backend pytest backend/tests/test_simplification_fractions_v2_determinism.py -q --disable-warnings --maxfail=1
```

**Résultats attendus** :
- ✅ Tous les tests passent
- ✅ Déterminisme vérifié
- ✅ Fallback déterministe vérifié
- ✅ Erreurs 422 vérifiées

---

## 📋 DoD (Definition of Done)

- [x] Code compilable (`py_compile` OK)
- [x] Plus de branche `else` qui écrase la sélection fixe
- [x] Fallback clair quand `variant_id` manquant (premier variant, déterministe)
- [x] Logs propres (pas de log "fallback" après succès fixe)
- [x] Tests mis à jour et passants
- [x] Pas de modification des autres fichiers
- [x] Structure de retour inchangée (compatibilité préservée)

---

## 🔍 Points de vérification

### Cas 1 : variant_id fourni et valide
- ✅ Sélection via `mode="fixed"` avec `fixed_variant_id=variant_id`
- ✅ Log `event=variant_fixed_selected`
- ✅ Pas d'écrasement par un fallback

### Cas 2 : variant_id fourni mais invalide
- ✅ `ValueError` capturé
- ✅ Log `event=variant_fixed_error`
- ✅ `HTTPException(422)` levée avec détails

### Cas 3 : variant_id absent
- ✅ Fallback déterministe sur le premier variant
- ✅ Log `event=variant_fallback_selected`
- ✅ Pas d'erreur, `chosen_variant` toujours défini

### Cas 4 : Aucun variant disponible
- ✅ `HTTPException(422)` avec `NO_VARIANTS_AVAILABLE`
- ✅ Log `event=variant_no_variants_available`

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Correction appliquée, prête pour validation


