# P1-PHASE2: Plan d'ajout de 20 générateurs Gold

**Date**: 2025-12-28
**Statut**: Planifié
**Dépendance**: P1-INFRA (commit 7a92bb6)

## 1. Audit - État actuel

### 1.1 Générateurs existants (6)

| Key | Version | Niveaux | Type | Gold |
|-----|---------|---------|------|------|
| CALCUL_NOMBRES_V1 | 1.0.0 | 6e, 5e | CALCUL_NOMBRES | ✅ |
| SIMPLIFICATION_FRACTIONS_V2 | 2.0.0 | CM2, 6e, 5e | FRACTIONS | ✅ |
| SIMPLIFICATION_FRACTIONS_V1 | 1.0.0 | CM2, 6e, 5e | FRACTIONS | - |
| RAISONNEMENT_MULTIPLICATIF_V1 | 1.0.0 | 6e, 5e | RAISONNEMENT_MULTIPLICATIF | - |
| SYMETRIE_AXIALE_V2 | 2.0.0 | 6e, 5e | SYMETRIE_AXIALE | - |
| THALES_V2 | 2.0.0 | 6e, 5e | THALES | - |

### 1.2 Structure Curriculum

- **Fichiers**: `backend/curriculum/curriculum_6e.json`, `backend/curriculum/curriculum_5e.json`
- **Mapping**: Chaque chapitre a un `code_officiel` (ex: `6e_N04`) et un champ `exercise_types[]`
- Les exercise_types listés dans le curriculum mais sans générateur fonctionnel = **gap à combler**

### 1.3 Gaps identifiés (exercise_types sans générateur)

| Catégorie | Exercise Types manquants |
|-----------|-------------------------|
| Aires/Périmètres | PERIMETRE_AIRE, AIRE_TRIANGLE, AIRE_FIGURES_COMPOSEES, PERIMETRE |
| Conversions | CONVERSIONS_UNITES, CONVERSION_DUREES, CONVERSION_LONGUEURS |
| Problèmes | PROBLEME_2_ETAPES, PROBLEME_1_ETAPE, PROBLEME_DUREES, PROBLEME_LONGUEURS |
| Fractions | CALCUL_FRACTIONS, FRACTIONS_EGALES, FRACTION_COMPARAISON, FRACTION_REPRESENTATION |
| Géométrie | TRIANGLE_CONSTRUCTION, QUADRILATERES, CERCLE |
| Nombres | NOMBRES_LECTURE, NOMBRES_COMPARAISON, DROITE_GRADUEE_ENTIERS, DROITE_GRADUEE_DECIMAUX |
| Critères | CRITERES_DIVISIBILITE, MULTIPLES |
| Statistiques | TABLEAU_LECTURE, DIAGRAMME_BARRES, STATISTIQUES |

---

## 2. Liste priorisée des 20 générateurs

### Priorité 1: Arithmétique & Nombres (6e core)

| # | Key | Chapitre cible | Type | Params principaux |
|---|-----|----------------|------|-------------------|
| 1 | NOMBRES_ENTIERS_V1 | 6e_N01, 6e_N02 | NOMBRES | max_value, format (lettres/chiffres), operation (lire/comparer) |
| 2 | DROITE_GRADUEE_V1 | 6e_N03 | NOMBRES | min_val, max_val, step, type (entiers/decimaux) |
| 3 | CRITERES_DIVISIBILITE_V1 | 6e_N07 | DIVISIBILITE | diviseur (2,3,5,9,10), max_number |
| 4 | MULTIPLES_DIVISEURS_V1 | 6e_N07 | DIVISIBILITE | range_min, range_max, operation (multiples/diviseurs) |

### Priorité 2: Fractions (6e N08-N09)

| # | Key | Chapitre cible | Type | Params principaux |
|---|-----|----------------|------|-------------------|
| 5 | FRACTION_REPRESENTATION_V1 | 6e_N08 | FRACTIONS | max_denominator, type (partage/quotient) |
| 6 | FRACTIONS_EGALES_V1 | 6e_N09 | FRACTIONS | max_denominator, operation (simplifier/amplifier) |
| 7 | FRACTION_COMPARAISON_V1 | 6e_N09 | FRACTIONS | same_denominator, max_denominator |

### Priorité 3: Grandeurs & Mesures (6e GM)

| # | Key | Chapitre cible | Type | Params principaux |
|---|-----|----------------|------|-------------------|
| 8 | CONVERSION_LONGUEURS_V1 | 6e_GM01, 6e_GM08 | CONVERSIONS | unit_from, unit_to, max_value |
| 9 | CONVERSION_MASSES_V1 | 6e_GM06 | CONVERSIONS | unit_from, unit_to, max_value |
| 10 | CONVERSION_DUREES_V1 | 6e_GM05 | CONVERSIONS | format (h:min/min:s), operation |
| 11 | PERIMETRE_V1 | 6e_GM02, 6e_GM08 | GEOMETRIE | figure (carre/rectangle/triangle), max_side |
| 12 | AIRE_RECTANGLE_V1 | 6e_GM03 | GEOMETRIE | max_side, include_carre |
| 13 | AIRE_TRIANGLE_V1 | 6e_GM04 | GEOMETRIE | max_base, max_height, type (rectangle/quelconque) |

### Priorité 4: Problèmes (6e N10)

| # | Key | Chapitre cible | Type | Params principaux |
|---|-----|----------------|------|-------------------|
| 14 | PROBLEME_1_ETAPE_V1 | 6e_N10 | PROBLEMES | operation (+,-,*,/), contexte (achat/distance/temps) |
| 15 | PROBLEME_2_ETAPES_V1 | 6e_N10 | PROBLEMES | operations, contexte, difficulte |

### Priorité 5: Statistiques & Proportionnalité (6e SP)

| # | Key | Chapitre cible | Type | Params principaux |
|---|-----|----------------|------|-------------------|
| 16 | TABLEAU_LECTURE_V1 | 6e_SP01 | STATISTIQUES | rows, cols, question_type |
| 17 | PROPORTIONNALITE_V1 | 6e_SP03 | PROPORTIONNALITE | coefficient, nb_colonnes, type (tableau/graphique) |
| 18 | MOYENNE_V1 | 6e_SP04 | STATISTIQUES | nb_valeurs, max_value, with_decimals |

### Priorité 6: Géométrie (6e G)

| # | Key | Chapitre cible | Type | Params principaux |
|---|-----|----------------|------|-------------------|
| 19 | TRIANGLE_CONSTRUCTION_V1 | 6e_G04 | GEOMETRIE | type (equilateral/isocele/scalene), with_svg |
| 20 | CERCLE_V1 | 6e_G06 | GEOMETRIE | operation (rayon/diametre/perimetre), max_rayon |

---

## 3. Roadmap par Batches

### Batch 1: Nombres & Arithmétique (4 générateurs)
- NOMBRES_ENTIERS_V1
- DROITE_GRADUEE_V1
- CRITERES_DIVISIBILITE_V1
- MULTIPLES_DIVISEURS_V1

**Commit**: `feat(gen): batch1 - nombres & arithmétique (4 générateurs)`

### Batch 2: Fractions (3 générateurs)
- FRACTION_REPRESENTATION_V1
- FRACTIONS_EGALES_V1
- FRACTION_COMPARAISON_V1

**Commit**: `feat(gen): batch2 - fractions (3 générateurs)`

### Batch 3: Conversions (3 générateurs)
- CONVERSION_LONGUEURS_V1
- CONVERSION_MASSES_V1
- CONVERSION_DUREES_V1

**Commit**: `feat(gen): batch3 - conversions (3 générateurs)`

### Batch 4: Aires & Périmètres (3 générateurs)
- PERIMETRE_V1
- AIRE_RECTANGLE_V1
- AIRE_TRIANGLE_V1

**Commit**: `feat(gen): batch4 - aires & périmètres (3 générateurs)`

### Batch 5: Problèmes & Stats (5 générateurs)
- PROBLEME_1_ETAPE_V1
- PROBLEME_2_ETAPES_V1
- TABLEAU_LECTURE_V1
- PROPORTIONNALITE_V1
- MOYENNE_V1

**Commit**: `feat(gen): batch5 - problèmes & stats (5 générateurs)`

### Batch 6: Géométrie (2 générateurs)
- TRIANGLE_CONSTRUCTION_V1
- CERCLE_V1

**Commit**: `feat(gen): batch6 - géométrie (2 générateurs)`

---

## 4. Definition of Done (DoD) par générateur

Chaque générateur doit:

- [ ] Fichier `backend/generators/{key_lower}.py` créé
- [ ] Décorateur `@GeneratorFactory.register`
- [ ] `get_meta()` avec GoldGeneratorMeta ou GeneratorMeta
- [ ] `get_schema()` avec ParamSchema pour chaque param
- [ ] `get_presets()` avec au moins 2 presets (facile + standard)
- [ ] `generate(params)` retourne `{"variables": {...}, ...}`
- [ ] Import ajouté dans `factory.py:_register_all_generators()`
- [ ] Test no-crash 100 seeds passe
- [ ] Test invariants minimal créé (si Gold)
- [ ] Ajouté à GOLD_GENERATORS si éligible

### DoD par batch

- [ ] Tous les générateurs du batch passent tests locaux
- [ ] Commit unique avec message standardisé
- [ ] CI GitHub passe (si configurée)
- [ ] Pas de régression sur tests existants

---

## 5. Commandes de test

### Tests locaux (Docker)

```bash
# Tous les tests générateurs
docker exec le-maitre-mot-backend python -m pytest backend/tests/test_generators_gold.py backend/tests/test_generators_no_crash.py backend/tests/invariants/ -v

# Test no-crash uniquement
docker exec le-maitre-mot-backend python -m pytest backend/tests/test_generators_no_crash.py -v

# Test Gold uniquement
docker exec le-maitre-mot-backend python -m pytest backend/tests/test_generators_gold.py -v

# Test invariants uniquement
docker exec le-maitre-mot-backend python -m pytest backend/tests/invariants/ -v

# Test un générateur spécifique (100 seeds)
docker exec le-maitre-mot-backend python -c "
from backend.generators.factory import GeneratorFactory
for seed in range(100):
    try:
        result = GeneratorFactory.generate(key='NOMBRES_ENTIERS_V1', seed=seed)
        print(f'seed={seed}: OK')
    except Exception as e:
        print(f'seed={seed}: FAIL - {e}')
"
```

### Vérification import

```bash
# Vérifier que le générateur est bien enregistré
docker exec le-maitre-mot-backend python -c "
from backend.generators.factory import GeneratorFactory
gen = GeneratorFactory.get('NOMBRES_ENTIERS_V1')
print(f'Trouvé: {gen is not None}')
if gen:
    print(f'Meta: {gen.get_meta().key}')
    print(f'Schema: {len(gen.get_schema())} params')
    print(f'Presets: {len(gen.get_presets())}')
"
```

### CI GitHub (après push)

```bash
# Voir le statut
gh run list --limit 5

# Voir les détails d'un run
gh run view <run_id>

# Voir les logs en cas d'échec
gh run view <run_id> --log-failed
```

---

## 6. Fichiers à modifier/créer par batch

### Par générateur

1. **Créer**: `backend/generators/{key_lower}.py`
2. **Modifier**: `backend/generators/factory.py` (import dans `_register_all_generators`)
3. **Créer** (si Gold): `backend/tests/invariants/test_{key_lower}_invariants.py`
4. **Modifier** (si Gold): `backend/tests/test_generators_gold.py` (ajouter à GOLD_GENERATORS_DEFAULT)

### Par batch (optionnel)

5. **Modifier**: `backend/curriculum/curriculum_6e.json` (vérifier exercise_types)
6. **Modifier**: `backend/curriculum/curriculum_5e.json` (si applicable)

---

## 7. Risques et mitigations

| Risque | Mitigation |
|--------|-----------|
| Régression tests existants | Lancer tous les tests avant chaque commit |
| Import circulaire | Importer dans `_register_all_generators` seulement |
| Performance > 100ms | Tester avec 50 seeds avant certification Gold |
| Placeholders non résolus | Utiliser `_check_no_placeholders` de BaseGoldGenerator |
| Seed non déterministe | Utiliser `self.rng_*` au lieu de `random.*` |

---

## 8. Timeline estimée

| Batch | Générateurs | Effort estimé |
|-------|-------------|---------------|
| Batch 1 | 4 | ~2h |
| Batch 2 | 3 | ~1.5h |
| Batch 3 | 3 | ~1.5h |
| Batch 4 | 3 | ~2h (SVG) |
| Batch 5 | 5 | ~3h |
| Batch 6 | 2 | ~2h (SVG) |

**Total**: ~12h de développement

---

## Annexe: Template générateur minimal

```python
"""
Générateur {KEY} - {Description}
"""
from typing import Dict, Any, List
from backend.generators.base_generator import (
    BaseGenerator, GeneratorMeta, ParamSchema, Preset, ParamType
)
from backend.generators.factory import GeneratorFactory


@GeneratorFactory.register
class {ClassName}(BaseGenerator):

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="{KEY}",
            label="{Label}",
            description="{Description}",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="{TYPE}",
            svg_mode="NONE",
            supports_double_svg=False,
            is_dynamic=True,
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Difficulté",
                default="standard",
                options=["facile", "standard"]
            ),
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(key="6e_facile", label="6e Facile", description="...",
                   niveau="6e", params={"difficulty": "facile", "seed": 42}),
            Preset(key="6e_standard", label="6e Standard", description="...",
                   niveau="6e", params={"difficulty": "standard", "seed": 42}),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        difficulty = params.get("difficulty", "standard")

        # TODO: Logique de génération
        variables = {
            "enonce": "TODO",
            "reponse_finale": "TODO",
        }

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {"generator_key": "{KEY}"},
        }
```
