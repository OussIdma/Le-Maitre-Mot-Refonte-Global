# Procédure complète — Création d'un générateur dynamique
**Version :** 2.0.0  
**Date :** 2025-01-XX  
**Objectif :** Procédure exhaustive pour créer un nouveau générateur dynamique sans erreur, industrialisable.

---

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Étape 1 : Structure du fichier générateur](#étape-1--structure-du-fichier-générateur)
3. [Étape 2 : Imports obligatoires](#étape-2--imports-obligatoires)
4. [Étape 3 : Métadonnées (get_meta)](#étape-3--métadonnées-get_meta)
5. [Étape 4 : Schéma de paramètres (get_schema)](#étape-4--schéma-de-paramètres-get_schema)
6. [Étape 5 : Presets pédagogiques (get_presets)](#étape-5--presets-pédagogiques-get_presets)
7. [Étape 6 : Méthode generate()](#étape-6--méthode-generate)
8. [Étape 7 : Templates HTML de référence](#étape-7--templates-html-de-référence)
9. [Étape 8 : Enregistrement dans GeneratorFactory](#étape-8--enregistrement-dans-generatorfactory)
10. [Étape 9 : Tests unitaires](#étape-9--tests-unitaires)
11. [Étape 10 : Validation et déploiement](#étape-10--validation-et-déploiement)
12. [Checklist complète](#checklist-complète)
13. [Pièges courants et solutions](#pièges-courants-et-solutions)

---

## ✅ Prérequis

- [ ] Compréhension de l'architecture `BaseGenerator` / `GeneratorFactory`
- [ ] Accès au code backend
- [ ] Docker opérationnel pour rebuild/restart
- [ ] Accès à l'interface admin pour créer les exercices dynamiques

---

## 📁 Étape 1 : Structure du fichier générateur

### 1.1 Nom du fichier

**Règle** : `backend/generators/{generator_key_lowercase}.py`

**Exemples** :
- `SIMPLIFICATION_FRACTIONS_V1` → `backend/generators/simplification_fractions_v1.py`
- `SIMPLIFICATION_FRACTIONS_V2` → `backend/generators/simplification_fractions_v2.py`
- `THALES_V2` → `backend/generators/thales_v2.py`

### 1.2 Structure de base

```python
"""
Générateur {GENERATOR_KEY} - {Description courte}
=====================================================================

Version: {X.Y.Z}

{Description détaillée}
"""

import math
import time  # ⚠️ OBLIGATOIRE pour mesurer la durée
from typing import Dict, Any, List, Optional
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
    create_svg_wrapper,
)
from backend.generators.factory import GeneratorFactory
from backend.observability import (
    get_request_context,
    safe_random_choice,  # ⚠️ OBLIGATOIRE au lieu de random.choice
    safe_randrange,     # ⚠️ OBLIGATOIRE au lieu de random.randrange
)


# Templates HTML de référence (SOURCE DE VÉRITÉ)
ENONCE_TEMPLATE = "<p>...</p>"
SOLUTION_TEMPLATE = "<ol>...</ol>"


@GeneratorFactory.register  # ⚠️ OBLIGATOIRE pour l'enregistrement
class MonGenerator(BaseGenerator):
    """Description du générateur."""
    
    # Constantes SVG (si applicable)
    SVG_WIDTH = 520
    SVG_HEIGHT = 140
    # ...
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        # ...
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        # ...
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        # ...
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # ...
```

---

## 🔧 Étape 2 : Imports obligatoires

### 2.1 Imports système

**⚠️ OBLIGATOIRE** :
```python
import math  # Si calculs mathématiques
import time  # ⚠️ OBLIGATOIRE pour mesurer duration_ms dans les logs
```

### 2.2 Imports BaseGenerator

**⚠️ OBLIGATOIRE** :
```python
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
    create_svg_wrapper,  # Si génération SVG
)
```

### 2.3 Imports Factory

**⚠️ OBLIGATOIRE** :
```python
from backend.generators.factory import GeneratorFactory
```

### 2.4 Imports Observability

**⚠️ OBLIGATOIRE** (remplace `random.choice` et `random.randrange`) :
```python
from backend.observability import (
    get_request_context,
    safe_random_choice,  # ⚠️ Utiliser au lieu de random.choice
    safe_randrange,      # ⚠️ Utiliser au lieu de random.randrange
)
```

**❌ INTERDIT** :
```python
import random
random.choice(...)  # ❌ Utiliser safe_random_choice
random.randrange(...)  # ❌ Utiliser safe_randrange
```

---

## 📊 Étape 3 : Métadonnées (get_meta)

### 3.1 Structure obligatoire

```python
@classmethod
def get_meta(cls) -> GeneratorMeta:
    return GeneratorMeta(
        key="GENERATOR_KEY",  # ⚠️ DOIT correspondre au nom du fichier (sans .py)
        label="Label lisible",
        description="Description complète",
        version="1.0.0",  # Format X.Y.Z
        niveaux=["CM2", "6e", "5e"],  # Niveaux supportés
        exercise_type="FRACTIONS",  # Type d'exercice (ex: FRACTIONS, GEOMETRY, etc.)
        svg_mode="AUTO",  # "AUTO", "MANUAL", "NONE"
        supports_double_svg=True,  # Si SVG énoncé + solution
        pedagogical_tips="Conseils pédagogiques (optionnel)"
    )
```

### 3.2 Règles

- **`key`** : DOIT être en MAJUSCULES, format `NOM_VERSION` (ex: `SIMPLIFICATION_FRACTIONS_V1`)
- **`exercise_type`** : DOIT être cohérent avec les autres générateurs du même type
- **`version`** : Format sémantique `X.Y.Z` (ex: `1.0.0`, `2.0.0`)

---

## ⚙️ Étape 4 : Schéma de paramètres (get_schema)

### 4.1 Structure obligatoire

```python
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
        ParamSchema(
            name="max_value",
            type=ParamType.INT,
            description="Valeur maximum",
            default=100,
            min=10,
            max=1000
        ),
        # ...
    ]
```

### 4.2 Types de paramètres

- **`ParamType.ENUM`** : Liste de valeurs possibles (`options` obligatoire)
- **`ParamType.INT`** : Entier (`min`/`max` optionnels)
- **`ParamType.BOOL`** : Booléen (`default` = `True` ou `False`)
- **`ParamType.STRING`** : Chaîne de caractères

### 4.3 Paramètre `difficulty` obligatoire

**⚠️ TOUS les générateurs DOIVENT avoir un paramètre `difficulty`** :
```python
ParamSchema(
    name="difficulty",
    type=ParamType.ENUM,
    description="Niveau de difficulté",
    default="moyen",
    options=["facile", "moyen", "difficile"]
)
```

---

## 🎯 Étape 5 : Presets pédagogiques (get_presets)

### 5.1 Structure obligatoire

```python
@classmethod
def get_presets(cls) -> List[Preset]:
    return [
        Preset(
            key="CM2_facile",
            label="CM2 Facile - Description",
            description="Description détaillée",
            niveau="CM2",
            params={
                "difficulty": "facile",
                "max_value": 20,
                # ... autres paramètres
            }
        ),
        # ...
    ]
```

### 5.2 Règles

- **Au moins 1 preset** par niveau supporté (recommandé)
- **`key`** : Format `{niveau}_{difficulty}` (ex: `CM2_facile`, `6e_moyen`)
- **`params`** : DOIVENT être valides selon le schéma

---

## 🎲 Étape 6 : Méthode generate()

### 6.1 Structure obligatoire

```python
def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un exercice.
    
    Args:
        params: Paramètres validés
        
    Returns:
        Dict avec variables, geo_data, SVG, meta, results
    """
    gen_start = time.time()  # ⚠️ OBLIGATOIRE
    ctx = get_request_context()
    ctx.update({
        'generator_key': self.get_meta().key,
        'difficulty': params.get('difficulty'),
    })
    
    # Log début génération
    self._obs_logger.info(
        "event=generate_in",
        event="generate_in",
        outcome="in_progress",
        **ctx
    )
    
    # ... logique de génération ...
    
    # Log succès
    gen_duration_ms = int((time.time() - gen_start) * 1000)
    self._obs_logger.info(
        "event=generate_complete",
        event="generate_complete",
        outcome="success",
        duration_ms=gen_duration_ms,
        **ctx
    )
    
    return {
        "variables": {...},  # ⚠️ OBLIGATOIRE : tous les placeholders des templates
        "geo_data": {...},   # Optionnel : données géométriques JSON-safe
        "figure_svg_enonce": "...",  # Optionnel : SVG énoncé
        "figure_svg_solution": "...",  # Optionnel : SVG solution
        "meta": {
            "exercise_type": "...",
            "difficulty": "...",
            "question_type": "..."
        },
        "results": {...}  # Optionnel : résultats calculés
    }
```

### 6.2 Règles critiques

1. **Variables** : DOIVENT contenir **TOUS** les placeholders des templates
2. **Safe random** : Utiliser `safe_random_choice` et `safe_randrange` (pas `random.choice/randrange`)
3. **Logging** : Logs `generate_in` et `generate_complete` obligatoires
4. **Duration** : Mesurer `duration_ms` avec `time.time()`

### 6.3 Filtrage de pools (éviter crash randrange)

**⚠️ CRITIQUE** : Si vous filtrez des options selon des paramètres, filtrer AVANT de choisir :

```python
# ❌ MAUVAIS (risque de crash)
pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
pgcd = safe_random_choice(pgcd_options, ctx, self._obs_logger)
denom_max = max_denom_base // pgcd
if denom_max < 2:
    continue  # ❌ Risque de boucle infinie ou crash

# ✅ BON (filtrage préventif)
pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
# Filtrer AVANT de choisir
pgcd_options = [pgcd for pgcd in pgcd_options if max_denom_base // pgcd >= 2]
if not pgcd_options:
    raise ValueError(f"Aucun PGCD valide pour max_denom_base={max_denom_base}")
pgcd = safe_random_choice(pgcd_options, ctx, self._obs_logger)
```

---

## 📝 Étape 7 : Templates HTML de référence

### 7.1 Définir les templates

**⚠️ OBLIGATOIRE** : Définir les templates comme constantes en haut du fichier :

```python
# Templates HTML de référence (SOURCE DE VÉRITÉ)
ENONCE_TEMPLATE = "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>"

SOLUTION_TEMPLATE = """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""
```

### 7.2 Règles

- **Nommage** : `ENONCE_TEMPLATE` et `SOLUTION_TEMPLATE` (ou `ENONCE_TEMPLATE_A`, `SOLUTION_TEMPLATE_A` pour variants)
- **Placeholders** : Format `{{variable}}` (pas d'espaces : `{{ variable }}` ❌)
- **Source de vérité** : Ces templates servent de référence pour les tests et l'admin

---

## 🔗 Étape 8 : Enregistrement dans GeneratorFactory

### 8.1 Décorateur obligatoire

**⚠️ OBLIGATOIRE** : Ajouter le décorateur `@GeneratorFactory.register` :

```python
@GeneratorFactory.register  # ⚠️ OBLIGATOIRE
class MonGenerator(BaseGenerator):
    # ...
```

### 8.2 Import dans factory.py

**⚠️ OBLIGATOIRE** : Ajouter l'import dans `backend/generators/factory.py` :

```python
def _register_all_generators():
    """Importe et enregistre tous les générateurs."""
    # ... imports existants ...
    
    try:
        from backend.generators.mon_generator import MonGenerator  # noqa:F401
    except ImportError:
        pass
```

**⚠️ IMPORTANT** :
- L'import DOIT être dans un bloc `try/except ImportError`
- Le `# noqa:F401` indique à flake8 que l'import non utilisé est volontaire (déclenche l'enregistrement)

### 8.3 Ordre des imports

**Règle** : Ajouter les imports par ordre alphabétique pour faciliter la maintenance.

---

## 🧪 Étape 9 : Tests unitaires

### 9.1 Créer le fichier de test

**Fichier** : `backend/tests/test_{generator_key_lowercase}.py`

**Exemple** : `backend/tests/test_simplification_fractions_v1.py`

### 9.2 Tests obligatoires

```python
import pytest
from backend.generators.mon_generator import MonGenerator, ENONCE_TEMPLATE, SOLUTION_TEMPLATE
from backend.generators.factory import GeneratorFactory
import re

def _extract_placeholders(template_str: str) -> set:
    """Extrait tous les placeholders d'un template."""
    return set(re.findall(r'\{\{(\w+)\}\}', template_str))

@pytest.fixture(scope="module", autouse=True)
def register_generator():
    """Assure l'enregistrement du générateur pour les tests."""
    GeneratorFactory.register(MonGenerator)

def test_meta_data():
    """Test que les métadonnées sont correctes."""
    meta = MonGenerator.get_meta()
    assert meta.key == "MON_GENERATOR"
    assert meta.version == "1.0.0"
    # ...

def test_schema_definition():
    """Test que le schéma est valide."""
    schema = MonGenerator.get_schema()
    assert len(schema) > 0
    # ...

def test_validate_params():
    """Test la validation des paramètres."""
    valid, result = MonGenerator.validate_params({"difficulty": "moyen"})
    assert valid
    # ...

def test_determinism():
    """Test que le générateur est déterministe."""
    params = {"difficulty": "moyen", "seed": 42}
    result1 = MonGenerator(seed=42).generate(params)
    result2 = MonGenerator(seed=42).generate(params)
    assert result1["variables"] == result2["variables"]
    # ...

def test_factory_registration():
    """Test que le générateur est enregistré dans la Factory."""
    gen_class = GeneratorFactory.get("MON_GENERATOR")
    assert gen_class == MonGenerator

def test_all_placeholders_resolved():
    """Test que tous les placeholders sont résolus."""
    params = {"difficulty": "moyen", "seed": 1}
    generator = MonGenerator(seed=1)
    result = generator.generate(params)
    
    enonce_placeholders = _extract_placeholders(ENONCE_TEMPLATE)
    solution_placeholders = _extract_placeholders(SOLUTION_TEMPLATE)
    all_expected_placeholders = enonce_placeholders.union(solution_placeholders)
    
    for placeholder in all_expected_placeholders:
        assert placeholder in result["variables"], \
            f"Placeholder '{placeholder}' not found in variables"
```

### 9.3 Tests de non-régression (si V2)

Si vous créez une V2, ajouter des tests de non-régression :

```python
def test_v2_backward_compatibility():
    """Test que V2 avec params par défaut = V1."""
    # ...
```

---

## ✅ Étape 10 : Validation et déploiement

### 10.1 Compilation

```bash
# Vérifier la syntaxe
python3 -m py_compile backend/generators/mon_generator.py
python3 -m py_compile backend/tests/test_mon_generator.py
```

### 10.2 Vérification de l'enregistrement

```bash
# Tester l'import
python3 -c "
from backend.generators.mon_generator import MonGenerator
from backend.generators.factory import GeneratorFactory
gen_class = GeneratorFactory.get('MON_GENERATOR')
assert gen_class == MonGenerator
print('✅ Générateur enregistré correctement')
"
```

### 10.3 Rebuild Docker (OBLIGATOIRE)

**⚠️ CRITIQUE** : Après toute modification de code Python, rebuild Docker :

```bash
cd /Users/oussamaidamhane/Desktop/Projet\ local\ LMM/Le-Maitre-Mot-v16-Refonte-Sauvegarde

# 1. Vérifier l'infrastructure
docker compose ps

# 2. Rebuild backend
docker compose build backend

# 3. Restart backend
docker compose restart backend

# 4. Vérifier les logs (pas d'erreur)
docker compose logs --tail=50 backend | grep -i error
```

### 10.4 Test via API

```bash
# Lister les générateurs
curl -s http://localhost:8000/api/v1/exercises/generators | jq '.[] | select(.key == "MON_GENERATOR")'

# Récupérer le schéma
curl -s http://localhost:8000/api/v1/exercises/generators/MON_GENERATOR/full-schema | jq '.'

# Test de génération
curl -X POST http://localhost:8000/api/v1/exercises/generators/preview-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "MON_GENERATOR",
    "difficulty": "moyen",
    "seed": 42
  }' | jq '.variables | keys'
```

---

## 📋 Checklist complète

### Avant de commencer

- [ ] Compréhension de l'architecture `BaseGenerator` / `GeneratorFactory`
- [ ] Documentation du cahier des charges lue
- [ ] Exemples de générateurs existants analysés

### Création du fichier

- [ ] Fichier créé : `backend/generators/{generator_key_lowercase}.py`
- [ ] Imports obligatoires présents (`time`, `safe_random_choice`, `safe_randrange`)
- [ ] Décorateur `@GeneratorFactory.register` présent
- [ ] Classe hérite de `BaseGenerator`

### Métadonnées et schéma

- [ ] `get_meta()` implémenté avec `key`, `version`, `niveaux`, `exercise_type`
- [ ] `get_schema()` implémenté avec au moins `difficulty`
- [ ] `get_presets()` implémenté avec au moins 1 preset
- [ ] Templates HTML définis comme constantes (`ENONCE_TEMPLATE`, `SOLUTION_TEMPLATE`)

### Méthode generate()

- [ ] `generate()` implémentée
- [ ] Logs `generate_in` et `generate_complete` présents
- [ ] `duration_ms` calculé avec `time.time()`
- [ ] `safe_random_choice` / `safe_randrange` utilisés (pas `random.choice/randrange`)
- [ ] Filtrage préventif des pools (si applicable)
- [ ] Tous les placeholders des templates présents dans `variables`

### Enregistrement

- [ ] Import ajouté dans `backend/generators/factory.py` (`_register_all_generators`)
- [ ] Import dans un bloc `try/except ImportError`
- [ ] `# noqa:F401` ajouté pour éviter warning flake8

### Tests

- [ ] Fichier de test créé : `backend/tests/test_{generator_key_lowercase}.py`
- [ ] Tests `meta`, `schema`, `validate_params`, `determinism`, `factory_registration`
- [ ] Test `all_placeholders_resolved` (CRITIQUE)
- [ ] Tests de cas limites (si applicable)

### Validation

- [ ] Compilation Python OK (`python3 -m py_compile`)
- [ ] Tests unitaires passent (`pytest`)
- [ ] Générateur visible dans l'API (`/api/v1/exercises/generators`)
- [ ] Schéma accessible (`/api/v1/exercises/generators/{key}/full-schema`)
- [ ] Test de génération OK (`/api/v1/exercises/generators/preview-dynamic`)

### Déploiement

- [ ] Rebuild Docker backend effectué
- [ ] Restart backend effectué
- [ ] Logs backend sans erreur
- [ ] Générateur accessible depuis l'admin UI

---

## 🐛 Pièges courants et solutions

### Piège 1 : Import manquant dans factory.py

**Symptôme** :
```
generator_key not found: MON_GENERATOR
```

**Cause** : Import manquant dans `_register_all_generators()`

**Solution** :
1. Vérifier que l'import est présent dans `backend/generators/factory.py`
2. Vérifier que le décorateur `@GeneratorFactory.register` est présent
3. Rebuild Docker backend

---

### Piège 2 : Imports manquants (time, safe_random_choice, safe_randrange)

**Symptôme** :
```
NameError: name 'time' is not defined
NameError: name 'safe_random_choice' is not defined
```

**Cause** : Imports manquants en haut du fichier

**Solution** :
```python
import time
from backend.observability import (
    get_request_context,
    safe_random_choice,
    safe_randrange,
)
```

---

### Piège 3 : Crash randrange avec pools filtrées

**Symptôme** :
```
ValueError: empty range for randrange(2, 1)
```

**Cause** : Pool non filtrée avant `safe_randrange`

**Solution** :
```python
# Filtrer AVANT de choisir
pgcd_options = [pgcd for pgcd in pgcd_options if max_denom_base // pgcd >= 2]
if not pgcd_options:
    raise ValueError(f"Aucun PGCD valide")
pgcd = safe_random_choice(pgcd_options, ctx, self._obs_logger)
```

---

### Piège 4 : Placeholders non résolus

**Symptôme** :
```
UNRESOLVED_PLACEHOLDERS: ['variable1', 'variable2']
```

**Cause** : Variables manquantes dans `result["variables"]`

**Solution** :
1. Extraire tous les placeholders des templates : `{{variable}}`
2. Vérifier que chaque placeholder est présent dans `result["variables"]`
3. Utiliser le test `test_all_placeholders_resolved`

---

### Piège 5 : Code modifié mais Docker non rebuild

**Symptôme** :
- Générateur non visible dans l'API
- Erreurs d'import dans les logs

**Cause** : Code modifié localement mais image Docker non mise à jour

**Solution** :
```bash
docker compose build backend
docker compose restart backend
```

---

### Piège 6 : Erreur de syntaxe/indentation

**Symptôme** :
```
IndentationError: expected an indented block
SyntaxError: invalid syntax
```

**Cause** : Erreur de syntaxe Python

**Solution** :
1. Vérifier avec `python3 -m py_compile backend/generators/mon_generator.py`
2. Corriger les erreurs d'indentation
3. Rebuild Docker

---

### Piège 7 : Décorateur @GeneratorFactory.register manquant

**Symptôme** :
- Générateur non enregistré dans la Factory
- `GeneratorFactory.get("MON_GENERATOR")` retourne `None`

**Cause** : Décorateur manquant

**Solution** :
```python
@GeneratorFactory.register  # ⚠️ OBLIGATOIRE
class MonGenerator(BaseGenerator):
    # ...
```

---

### Piège 8 : Templates copiés depuis un autre générateur

**Symptôme** :
- `UNRESOLVED_PLACEHOLDERS` avec des placeholders d'un autre générateur

**Cause** : Templates copiés sans vérification

**Solution** :
1. **TOUJOURS** utiliser les templates définis dans le générateur lui-même
2. Extraire les templates depuis `ENONCE_TEMPLATE` et `SOLUTION_TEMPLATE` du fichier
3. Ne jamais copier des templates d'un autre générateur

---

## 📚 Exemples de référence

### Exemple 1 : SIMPLIFICATION_FRACTIONS_V1

**Fichier** : `backend/generators/simplification_fractions_v1.py`

**Points clés** :
- Imports corrects (`time`, `safe_random_choice`, `safe_randrange`)
- Filtrage préventif de `pgcd_options`
- Logs structurés
- Templates définis comme constantes

### Exemple 2 : SIMPLIFICATION_FRACTIONS_V2

**Fichier** : `backend/generators/simplification_fractions_v2.py`

**Points clés** :
- Variants pédagogiques (A, B, C)
- Templates multiples (`ENONCE_TEMPLATE_A`, `SOLUTION_TEMPLATE_A`, etc.)
- Non-régression V1 (params par défaut = comportement V1)

---

## 🎯 Règles d'or

1. **Toujours utiliser `safe_random_choice` / `safe_randrange`** (jamais `random.choice/randrange`)
2. **Filtrer les pools AVANT de choisir** (éviter crash randrange)
3. **Tous les placeholders des templates DOIVENT être dans `variables`**
4. **Toujours rebuild Docker après modification de code Python**
5. **Toujours tester l'enregistrement** (`GeneratorFactory.get("KEY")`)
6. **Toujours valider les placeholders** (test `all_placeholders_resolved`)
7. **Toujours utiliser les templates du générateur** (jamais copier d'un autre)

---

## 📝 Notes importantes

- **Versioning** : V1, V2, V3 sont des générateurs **séparés**, pas des migrations
- **Non-régression** : V2 doit être compatible avec V1 si params par défaut
- **Déterminisme** : Même seed + mêmes params → mêmes résultats
- **Observabilité** : Logs structurés obligatoires (`event=generate_in`, `event=generate_complete`)

---

**Document créé le :** 2025-01-XX  
**Dernière mise à jour :** 2025-01-XX  
**Statut :** ✅ Validé

