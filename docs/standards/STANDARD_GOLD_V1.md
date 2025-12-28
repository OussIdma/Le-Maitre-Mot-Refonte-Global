# Standard Gold V1 - Générateurs d'exercices certifiés

**Version**: 1.0
**Date**: 2025-12-28
**Statut**: Actif

## Vue d'ensemble

Le standard Gold définit les exigences de qualité pour les générateurs d'exercices certifiés. Un générateur Gold garantit:

- **Reproductibilité**: même seed = même résultat
- **Performance**: génération < 100ms
- **Sécurité**: pas de placeholders non résolus, pas de XSS
- **Invariants métier**: cohérence mathématique

## Critères d'éligibilité Gold

### 1. Seed obligatoire

Un générateur Gold DOIT être utilisé avec une seed explicite pour garantir la reproductibilité.

```python
# BON
result = GeneratorFactory.generate(key="MY_GOLD_V1", seed=42)

# MAUVAIS - seed implicite interdite pour Gold
result = GeneratorFactory.generate(key="MY_GOLD_V1")  # Erreur en prod
```

### 2. Performance < 100ms

Le temps de génération moyen doit être inférieur à 100ms.

- Testé sur 50 générations consécutives
- Le P95 est surveillé mais non bloquant
- Le max peut dépasser ponctuellement

### 3. Pas de placeholders non résolus

Les variables retournées ne doivent JAMAIS contenir de `{{ }}` non résolus.

```python
# INTERDIT dans le output
variables = {
    "enonce": "Calculer {{expression}}",  # ❌ Placeholder non résolu
}
```

### 4. Pas de HTML dangereux

Les variables string ne doivent pas contenir:
- `<script>`
- `javascript:`
- `onerror=`
- `onload=`

### 5. Invariants métier respectés

Chaque générateur Gold doit passer des tests d'invariants spécifiques:

- Pour les fractions: équivalence, irréductibilité
- Pour les calculs: résultat correct
- etc.

## Architecture

### Classes de base

```python
from backend.generators.base_gold_generator import (
    BaseGoldGenerator,
    GoldGeneratorMeta
)
```

### GoldGeneratorMeta

Étend `GeneratorMeta` avec des champs Gold-spécifiques:

```python
@dataclass
class GoldGeneratorMeta(GeneratorMeta):
    gold_version: str = "1.0"      # Version Gold
    perf_budget_ms: int = 100      # Budget de performance
    quality_tier: str = "gold"     # Niveau de qualité
```

### BaseGoldGenerator

Étend `BaseGenerator` avec des validations automatiques:

- `_check_no_placeholders(obj)`: vérifie absence de {{ }}
- `_check_no_dangerous_html(obj)`: vérifie absence XSS
- `_validate_output(output)`: validation du output
- `_check_perf_budget()`: surveillance du budget

## Création d'un nouveau générateur Gold

### 1. Créer le fichier générateur

```python
# backend/generators/mon_generateur_v1.py

from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
)
from backend.generators.factory import GeneratorFactory


@GeneratorFactory.register
class MonGenerateurV1Generator(BaseGenerator):
    """Générateur Gold pour [description]."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="MON_GENERATEUR_V1",
            label="Mon générateur",
            description="Description du générateur",
            version="1.0.0",
            niveaux=["6e", "5e"],
            exercise_type="TYPE_EXERCICE",
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
                description="Niveau de difficulté",
                default="moyen",
                options=["facile", "moyen", "difficile"]
            ),
            # Autres paramètres...
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_standard",
                label="6e Standard",
                description="Exercices niveau 6e",
                niveau="6e",
                params={"difficulty": "moyen", "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Implémenter la génération
        variables = self._generate_exercise(params)

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {
                "generator_key": "MON_GENERATEUR_V1",
            }
        }
```

### 2. Ajouter au curriculum (optionnel)

Si le générateur doit être accessible via l'UI, l'ajouter au curriculum.

### 3. Créer les tests d'invariants

```python
# backend/tests/invariants/test_mon_generateur_v1_invariants.py

import pytest
from backend.generators.factory import GeneratorFactory


class TestMonGenerateurV1Invariants:
    GENERATOR_KEY = "MON_GENERATEUR_V1"

    def test_invariant_specifique(self):
        """Décrire l'invariant testé."""
        for seed in range(30):
            result = GeneratorFactory.generate(
                key=self.GENERATOR_KEY,
                seed=seed
            )
            # Vérifier l'invariant...
```

### 4. Ajouter à la liste Gold

Dans `backend/tests/test_generators_gold.py`:

```python
GOLD_GENERATORS_DEFAULT = [
    "CALCUL_NOMBRES_V1",
    "SIMPLIFICATION_FRACTIONS_V2",
    "MON_GENERATEUR_V1",  # Ajouter ici
]
```

## Tests CI

Les tests Gold sont exécutés automatiquement en CI:

1. **standard-no-crash**: 100 seeds sans crash
2. **gold-performance**: performance < 100ms
3. **invariants**: tests d'invariants métier
4. **schema-validation**: cohérence schema/params

## Helpers disponibles

Les générateurs Gold peuvent utiliser les helpers de `backend/generators/helpers/`:

```python
from backend.generators.helpers import (
    # Nombres
    pgcd,
    simplify_fraction,
    is_prime,
    prime_factors,
    lcm,

    # Unités
    format_number_fr,

    # Formatage
    safe_html,
    round_smart,
    format_latex_fraction,
)
```

## Fallback (Production uniquement)

Le fallback est **désactivé par défaut**. En production, il peut être activé via:

```bash
GOLD_ENABLE_FALLBACK=1
```

**Important**: En dev/test, les erreurs sont TOUJOURS propagées pour ne pas masquer les bugs.

## Références

- `backend/generators/base_generator.py`: Classe de base
- `backend/generators/base_gold_generator.py`: Extensions Gold
- `backend/generators/factory.py`: Factory centrale
- `backend/tests/test_generators_gold.py`: Tests Gold
- `backend/tests/invariants/`: Tests d'invariants
