# Rapport d'Audit — SIMPLIFICATION_FRACTIONS_V1
**Date** : 2025-01-XX  
**Auditeur** : Expert Python / Ingénierie pédagogique  
**Objet** : Analyse critique du générateur V1 et vérification des points d'audit

---

## 📋 RÉSUMÉ EXÉCUTIF

L'audit critique a identifié **3 problèmes réels** dans `simplification_fractions_v1.py` :
1. ✅ **CONFIRMÉ** : Risque de crash `randrange` avec `max_denominator` petit + `difficulty="difficile"`
2. ✅ **CONFIRMÉ** : Imports manquants (`time`, `safe_random_choice`, `safe_randrange`)
3. ⚠️ **CLARIFICATION** : V2 existe déjà séparément (normal, V1 doit rester V1 pour compatibilité)

---

## 🔍 ANALYSE DÉTAILLÉE

### 1. RISQUE DE CRASH `randrange` (BLOQUANT)

**Problème identifié** : Ligne 323-352

```python
# Ligne 323 : difficulté "difficile"
pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]

# Ligne 349-352
denom_max = max_denom_base // pgcd  # Si pgcd=12 et max_denom_base=6 → denom_max=0
if denom_max < 2:
    continue  # Skip, mais le PGCD reste dans pgcd_options
denom_base = safe_randrange(2, denom_max + 1, ...)  # Si denom_max=0 → safe_randrange(2, 1) → ERREUR
```

**Scénario de crash** :
- `difficulty="difficile"` → `pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]`
- `max_denominator=6` → `max_denom_base = min(40, 6) = 6`
- Si `pgcd=12` ou `pgcd=15` est choisi :
  - `denom_max = 6 // 12 = 0` ou `6 // 15 = 0`
  - `if denom_max < 2: continue` → skip, mais le PGCD reste dans la pool
  - Boucle infinie possible si tous les PGCD sont trop grands
  - Si un PGCD valide est choisi mais `denom_max=0`, `safe_randrange(2, 1)` échoue

**Solution** : Filtrer `pgcd_options` AVANT de choisir un PGCD :
```python
# Filtrer pgcd_options selon max_denominator
pgcd_options = [pgcd for pgcd in pgcd_options if pgcd <= max_denom_base]
```

**Impact** : 🔴 **BLOQUANT** — Peut causer une exception ou une boucle infinie

---

### 2. IMPORTS MANQUANTS (BLOQUANT)

**Problème identifié** : Lignes 11-24

**Imports manquants** :
- `time` (utilisé ligne 196 : `gen_start = time.time()`)
- `safe_random_choice` (utilisé ligne 346)
- `safe_randrange` (utilisé lignes 352, 363)

**Code actuel** :
```python
from backend.observability import (
    get_request_context,
)
# ❌ Manque : safe_random_choice, safe_randrange
# ❌ Manque : import time
```

**Impact** : 🔴 **BLOQUANT** — `NameError` à l'exécution

---

### 3. CLARIFICATION : V2 vs V1

**Point d'audit** : "V2 non implémentée (bloquant) : le fichier simplification_fractions_v1.py est inchangé en V1"

**Analyse** :
- ✅ `simplification_fractions_v2.py` **existe déjà** (828 lignes)
- ✅ V2 est un générateur **séparé** avec sa propre clé `SIMPLIFICATION_FRACTIONS_V2`
- ✅ V1 doit **rester V1** pour compatibilité rétroactive (principe de non-régression)

**Conclusion** : L'audit semble confondre deux choses :
1. **V1 doit rester V1** (pas de migration V1→V2 dans le même fichier)
2. **V2 existe déjà** comme générateur séparé

**Recommandation** : Si l'intention est d'ajouter des fonctionnalités V2 à V1, cela violerait le principe de non-régression. V1 doit rester stable.

---

## ✅ POINTS POSITIFS

1. **Observabilité** : Utilisation de `safe_random_choice` et `safe_randrange` (même si imports manquants)
2. **Logging structuré** : `_obs_logger` correctement utilisé
3. **Tests complets** : 17 tests unitaires couvrent les cas principaux
4. **Architecture** : Respecte `BaseGenerator` et `GeneratorFactory`

---

## 🎯 PLAN D'ACTION RECOMMANDÉ

### Phase 1 : Corrections critiques (P0)

1. **Ajouter les imports manquants** :
   ```python
   import time
   from backend.observability import (
       get_request_context,
       safe_random_choice,
       safe_randrange,
   )
   ```

2. **Filtrer `pgcd_options` selon `max_denominator`** :
   ```python
   # Dans _pick_fraction, après avoir défini pgcd_options
   # Filtrer les PGCD qui ne peuvent pas fonctionner
   pgcd_options = [pgcd for pgcd in pgcd_options if pgcd <= max_denom_base]
   ```

3. **Ajouter des logs de debug** :
   ```python
   self._obs_logger.debug(
       "event=pgcd_filtered",
       pgcd_options_before=len(pgcd_options_original),
       pgcd_options_after=len(pgcd_options),
       max_denom_base=max_denom_base,
       **ctx
   )
   ```

### Phase 2 : Tests de non-régression (P0)

1. **Test cas limite** : `difficulty="difficile"` + `max_denominator=6`
2. **Test cas limite** : `difficulty="difficile"` + `max_denominator=10`
3. **Test cas limite** : `force_reducible=False` + `max_denominator` très petit

### Phase 3 : Documentation (P1)

1. Documenter le comportement de filtrage des PGCD
2. Ajouter des exemples de cas limites dans les docstrings

---

## 📊 STATUT DES POINTS D'AUDIT

| Point d'audit | Statut | Priorité | Action |
|---------------|--------|----------|--------|
| V2 non implémentée dans V1 | ⚠️ Clarification nécessaire | P2 | V1 doit rester V1 |
| Risque crash `randrange` | ✅ **CONFIRMÉ** | 🔴 P0 | Filtrer `pgcd_options` |
| Imports manquants | ✅ **CONFIRMÉ** | 🔴 P0 | Ajouter imports |
| Pas de couche pédagogique avancée | ℹ️ Normal (V1) | - | V2 existe déjà |
| Pipeline MIXED/TEMPLATE plante | ❓ À investiguer séparément | P1 | Hors scope V1 |

---

## 🔧 FICHIERS À MODIFIER

1. `backend/generators/simplification_fractions_v1.py`
   - Ajouter imports (lignes 11-24)
   - Filtrer `pgcd_options` (ligne ~323)
   - Ajouter logs debug

2. `backend/tests/test_simplification_fractions_v1.py`
   - Ajouter test `test_max_denominator_small_difficile`
   - Ajouter test `test_pgcd_filtering`

---

## ✅ VALIDATION

- [x] Analyse du code V1 complétée
- [x] Vérification des imports
- [x] Identification du bug `randrange`
- [x] Vérification de l'existence de V2
- [x] Corrections appliquées
- [x] Tests de non-régression ajoutés
- [ ] Validation fonctionnelle (tests à exécuter)

---

## 🔧 CORRECTIONS APPLIQUÉES

### 1. Imports manquants (✅ CORRIGÉ)

**Fichier** : `backend/generators/simplification_fractions_v1.py` (lignes 11-24)

**Ajouts** :
```python
import time
from backend.observability import (
    get_request_context,
    safe_random_choice,
    safe_randrange,
)
```

### 2. Filtrage PGCD (✅ CORRIGÉ)

**Fichier** : `backend/generators/simplification_fractions_v1.py` (lignes ~325-350)

**Modification** :
- Ajout du filtrage de `pgcd_options` selon `max_denom_base` avant le choix du PGCD
- Filtre : `pgcd_options = [pgcd for pgcd in pgcd_options if max_denom_base // pgcd >= 2]`
- Log debug ajouté pour tracer le filtrage

**Code ajouté** :
```python
# FIX P0: Filtrer pgcd_options selon max_denom_base pour éviter crash randrange
pgcd_options_original = pgcd_options.copy()
pgcd_options = [pgcd for pgcd in pgcd_options if max_denom_base // pgcd >= 2]

# Log du filtrage si des PGCD ont été exclus
if len(pgcd_options) < len(pgcd_options_original):
    self._obs_logger.debug(
        "event=pgcd_filtered",
        pgcd_options_before=pgcd_options_original,
        pgcd_options_after=pgcd_options,
        max_denom_base=max_denom_base,
        max_denominator=max_denominator,
        filtered_count=len(pgcd_options_original) - len(pgcd_options),
        **ctx
    )
```

### 3. Tests de non-régression (✅ AJOUTÉS)

**Fichier** : `backend/tests/test_simplification_fractions_v1.py`

**Tests ajoutés** :
1. `test_max_denominator_small_difficile()` : Cas limite `difficulty="difficile"` + `max_denominator=6`
2. `test_max_denominator_small_moyen()` : Cas limite `difficulty="moyen"` + `max_denominator=8`
3. `test_pgcd_filtering_edge_cases()` : Cas limites multiples de filtrage PGCD
4. `test_force_reducible_false_small_denominator()` : `force_reducible=False` + `max_denominator` petit

---

## 📝 COMMANDES DE VALIDATION

```bash
# Compilation
python3 -m py_compile backend/generators/simplification_fractions_v1.py
python3 -m py_compile backend/tests/test_simplification_fractions_v1.py

# Tests (à exécuter dans l'environnement de test)
pytest backend/tests/test_simplification_fractions_v1.py::test_max_denominator_small_difficile -v
pytest backend/tests/test_simplification_fractions_v1.py::test_pgcd_filtering_edge_cases -v
```

---

**Statut** : ✅ Corrections P0 appliquées et prêtes pour validation fonctionnelle

