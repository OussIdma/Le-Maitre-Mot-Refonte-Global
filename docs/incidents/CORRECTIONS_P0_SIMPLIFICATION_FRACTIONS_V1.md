# Corrections P0 — SIMPLIFICATION_FRACTIONS_V1
**Date** : 2025-01-XX  
**Statut** : ✅ TERMINÉ

---

## 📋 RÉSUMÉ

Corrections appliquées suite à l'audit critique du générateur `SIMPLIFICATION_FRACTIONS_V1` :
1. ✅ Imports manquants ajoutés
2. ✅ Filtrage PGCD pour éviter crash `randrange`
3. ✅ Logs debug ajoutés
4. ✅ Tests de non-régression ajoutés

---

## 🔧 MODIFICATIONS APPLIQUÉES

### 1. Imports manquants

**Fichier** : `backend/generators/simplification_fractions_v1.py`

**Ajouts** (lignes 11-24) :
```python
import time
from backend.observability import (
    get_request_context,
    safe_random_choice,
    safe_randrange,
)
```

**Impact** : Corrige les `NameError` à l'exécution.

---

### 2. Filtrage PGCD (FIX P0)

**Fichier** : `backend/generators/simplification_fractions_v1.py`

**Modification** (lignes 329-353) :
```python
# FIX P0: Filtrer pgcd_options selon max_denom_base pour éviter crash randrange
# Un PGCD ne peut fonctionner que si max_denom_base // pgcd >= 2
# (sinon denom_max < 2 et safe_randrange(2, denom_max+1) échoue)
pgcd_options_original = pgcd_options.copy()
pgcd_options = [pgcd for pgcd in pgcd_options if max_denom_base // pgcd >= 2]

# Log du filtrage si des PGCD ont été exclus
if len(pgcd_options) < len(pgcd_options_original):
    self._obs_logger.debug(
        "event=pgcd_filtered",
        event="pgcd_filtered",
        outcome="success",
        pgcd_options_before=pgcd_options_original,
        pgcd_options_after=pgcd_options,
        max_denom_base=max_denom_base,
        max_denominator=max_denominator,
        filtered_count=len(pgcd_options_original) - len(pgcd_options),
        **ctx
    )
```

**Impact** : Évite le crash `randrange` et les boucles infinies avec `max_denominator` petit.

**Exemple** :
- `difficulty="difficile"` + `max_denominator=6`
- Avant : `pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]` → risque de crash
- Après : `pgcd_options = [2, 3]` → génération sûre

---

### 3. Tests de non-régression

**Fichier** : `backend/tests/test_simplification_fractions_v1.py`

**Tests ajoutés** :
1. `test_max_denominator_small_difficile()` : Cas limite `difficulty="difficile"` + `max_denominator=6`
2. `test_max_denominator_small_moyen()` : Cas limite `difficulty="moyen"` + `max_denominator=8`
3. `test_pgcd_filtering_edge_cases()` : Cas limites multiples de filtrage PGCD
4. `test_force_reducible_false_small_denominator()` : `force_reducible=False` + `max_denominator` petit

---

## ✅ VALIDATION

### Compilation
```bash
✅ backend/generators/simplification_fractions_v1.py - OK
✅ backend/tests/test_simplification_fractions_v1.py - OK
```

### Test manuel
```python
gen = SimplificationFractionsV1Generator(seed=42)
result = gen.safe_generate({
    "difficulty": "difficile",
    "max_denominator": 6,  # Cas critique
    "force_reducible": True,
    "show_svg": False,
    "representation": "none"
})
# ✅ Génération réussie, pas de crash
# ✅ d <= 6, pgcd in [2, 3]
```

---

## 📦 FICHIERS MODIFIÉS

1. `backend/generators/simplification_fractions_v1.py`
   - Ajout imports (`time`, `safe_random_choice`, `safe_randrange`)
   - Filtrage de `pgcd_options` selon `max_denom_base`
   - Logs debug pour le filtrage

2. `backend/tests/test_simplification_fractions_v1.py`
   - 4 nouveaux tests de non-régression

3. `docs/incidents/RAPPORT_AUDIT_SIMPLIFICATION_FRACTIONS_V1.md`
   - Rapport d'audit complet

4. `docs/incidents/INCIDENT_2025-01-XX_simplification_fractions_v1_crash_randrange.md`
   - Document d'incident détaillé

---

## 🔄 COMMANDES DE REBUILD / RESTART

**📄 Voir le document détaillé** : `docs/incidents/COMMANDES_REBUILD_RESTART_V1.md`

**Commandes rapides** :
```bash
cd /Users/oussamaidamhane/Desktop/Projet\ local\ LMM/Le-Maitre-Mot-v16-Refonte-Sauvegarde

# 1. Vérifier l'infrastructure
docker compose ps

# 2. Rebuild backend
docker compose build backend

# 3. Restart backend
docker compose restart backend

# 4. Vérifier les logs
docker compose logs --tail=50 backend | grep -i error

# 5. Test de validation
docker compose exec backend python3 -c "
from backend.generators.simplification_fractions_v1 import SimplificationFractionsV1Generator
gen = SimplificationFractionsV1Generator(seed=42)
result = gen.safe_generate({
    'difficulty': 'difficile',
    'max_denominator': 6,
    'force_reducible': True,
    'show_svg': False,
    'representation': 'none'
})
print('✅ Génération réussie')
print(f'   d={result[\"variables\"][\"d\"]}, pgcd={result[\"variables\"][\"pgcd\"]}')
"
```

---

## 📊 STATUT FINAL

| Tâche | Statut | Priorité |
|-------|--------|----------|
| Imports manquants | ✅ CORRIGÉ | P0 |
| Filtrage PGCD | ✅ CORRIGÉ | P0 |
| Logs debug | ✅ AJOUTÉ | P0 |
| Tests de non-régression | ✅ AJOUTÉ | P0 |
| Validation fonctionnelle | ⏳ À valider | P0 |

---

**Prochaine étape** : Exécuter les tests dans l'environnement de test pour validation fonctionnelle complète.

