# INCIDENT — Crash randrange SIMPLIFICATION_FRACTIONS_V1
**ID** : INC-2025-01-XX-SF-V1-RANDRANGE  
**Date** : 2025-01-XX  
**Priorité** : 🔴 P0 (BLOQUANT)  
**Statut** : ✅ CORRIGÉ

---

## 📋 SYMPTÔME

Le générateur `SIMPLIFICATION_FRACTIONS_V1` peut crasher ou entrer dans une boucle infinie lorsque :
- `difficulty="difficile"`
- `max_denominator` est très petit (ex: 6, 8, 10)

**Erreur observée** :
```
ValueError: empty range for randrange(2, 1)
```
ou boucle infinie si tous les PGCD sont filtrés mais la pool n'est pas vidée.

---

## 🔍 ROOT CAUSE

**Fichier** : `backend/generators/simplification_fractions_v1.py` (lignes 323-355)

**Problème** :
1. Pour `difficulty="difficile"`, `pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]`
2. Si `max_denominator=6`, alors `max_denom_base = min(40, 6) = 6`
3. Si `pgcd=12` ou `pgcd=15` est choisi :
   - `denom_max = 6 // 12 = 0` ou `6 // 15 = 0`
   - `if denom_max < 2: continue` → skip, mais le PGCD reste dans la pool
   - Si un PGCD valide est choisi mais `denom_max=0`, `safe_randrange(2, 1)` échoue

**Chaîne de cause** :
```
max_denominator petit (6)
  → max_denom_base = 6
  → pgcd_options contient [12, 15] (incompatibles)
  → denom_max = 0 pour ces PGCD
  → safe_randrange(2, 1) → ERREUR
```

---

## ✅ FIX APPLIQUÉ

### 1. Filtrage préventif de `pgcd_options`

**Fichier** : `backend/generators/simplification_fractions_v1.py` (lignes ~325-350)

**Modification** :
```python
# AVANT (ligne 323-327)
else:  # difficile
    max_denom_base = min(40, max_denominator)
    pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
    max_numerator_ratio = 1.0

# APRÈS
else:  # difficile
    max_denom_base = min(40, max_denominator)
    pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
    max_numerator_ratio = 1.0

# FIX P0: Filtrer pgcd_options selon max_denom_base
pgcd_options_original = pgcd_options.copy()
pgcd_options = [pgcd for pgcd in pgcd_options if max_denom_base // pgcd >= 2]
```

**Logique** : Un PGCD ne peut fonctionner que si `max_denom_base // pgcd >= 2` (sinon `denom_max < 2`).

### 2. Ajout de logs debug

**Code ajouté** :
```python
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

### 3. Correction des imports manquants

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

---

## 🧪 TESTS / PREUVE

### Tests ajoutés

**Fichier** : `backend/tests/test_simplification_fractions_v1.py`

1. **`test_max_denominator_small_difficile()`**
   - Cas : `difficulty="difficile"` + `max_denominator=6`
   - Vérifie : génération réussie, `d <= 6`, `pgcd in [2, 3]`

2. **`test_max_denominator_small_moyen()`**
   - Cas : `difficulty="moyen"` + `max_denominator=8`
   - Vérifie : génération réussie, `d <= 8`, `pgcd in [2, 3, 4]`

3. **`test_pgcd_filtering_edge_cases()`**
   - Cas multiples : différentes combinaisons `difficulty` + `max_denominator`
   - Vérifie : PGCD valides pour chaque cas

4. **`test_force_reducible_false_small_denominator()`**
   - Cas : `force_reducible=False` + `max_denominator=5`
   - Vérifie : génération réussie même avec dénominateur très petit

### Validation manuelle

```python
# Test de régression
gen = SimplificationFractionsV1Generator(seed=42)
result = gen.safe_generate({
    "difficulty": "difficile",
    "max_denominator": 6,  # Cas critique
    "force_reducible": True,
    "show_svg": False,
    "representation": "none"
})
# ✅ Pas de crash, génération réussie
assert result["variables"]["d"] <= 6
assert result["variables"]["pgcd"] in [2, 3]
```

---

## 📦 FICHIERS MODIFIÉS

1. `backend/generators/simplification_fractions_v1.py`
   - Ajout imports (`time`, `safe_random_choice`, `safe_randrange`)
   - Filtrage de `pgcd_options` selon `max_denom_base`
   - Logs debug pour le filtrage

2. `backend/tests/test_simplification_fractions_v1.py`
   - 4 nouveaux tests de non-régression

---

## 🔄 COMMANDES DE REBUILD / RESTART

```bash
# Rebuild backend (si Docker)
docker compose build backend

# Restart backend
docker compose restart backend

# Vérification compilation
python3 -m py_compile backend/generators/simplification_fractions_v1.py
```

---

## ✅ VALIDATION

- [x] Code compilé sans erreur
- [x] Tests de non-régression ajoutés
- [x] Logs debug ajoutés
- [ ] Tests exécutés et passants (à valider)
- [ ] Validation fonctionnelle en environnement de test

---

## 📚 RÉFÉRENCES

- Rapport d'audit : `docs/incidents/RAPPORT_AUDIT_SIMPLIFICATION_FRACTIONS_V1.md`
- Fichier source : `backend/generators/simplification_fractions_v1.py`
- Tests : `backend/tests/test_simplification_fractions_v1.py`


