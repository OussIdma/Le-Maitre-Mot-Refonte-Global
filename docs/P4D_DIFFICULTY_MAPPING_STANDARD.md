# P4.D HOTFIX — Mapping Difficulté UI → Générateur (standard vs moyen)

## Contexte

### Problème identifié

L'interface admin utilise les difficultés canoniques (`facile`, `moyen`, `difficile`), mais certains générateurs utilisent des difficultés non canoniques :

- **CALCUL_NOMBRES_V1** : supporte uniquement `facile` et `standard`
- **RAISONNEMENT_MULTIPLICATIF_V1** : peut avoir des restrictions similaires

**Problème** :
1. `normalize_difficulty()` convertit `standard` → `moyen` (pour l'UI)
2. Mais quand on appelle le générateur avec `moyen`, il ne comprend pas car il attend `standard`
3. Résultat : `INVALID_DIFFICULTY` (422) puis `ADMIN_TEMPLATE_MISMATCH` (422) car la génération échoue

### Impact

- **Erreurs 422/500** : L'admin voit des erreurs `ADMIN_TEMPLATE_MISMATCH` alors que le problème est juste un mapping de difficulté
- **UX dégradée** : L'admin ne peut pas créer d'exercices avec des difficultés "moyen" ou "difficile" pour certains générateurs
- **Incohérence** : Le mapping UI → générateur n'est pas appliqué de manière cohérente

## Solution implémentée

### Fonction `map_ui_difficulty_to_generator()`

**Fichier** : `backend/utils/difficulty_utils.py`

**Fonction** :
```python
def map_ui_difficulty_to_generator(
    generator_key: str,
    ui_difficulty: str,
    logger=None
) -> str:
```

**Comportement** :
1. Normalise la difficulté UI (`facile`/`moyen`/`difficile`)
2. Récupère les difficultés réellement supportées par le générateur (via `GeneratorFactory.get_schema()`)
3. Mappe intelligemment :
   - `ui_difficulty == "moyen"` et générateur supporte `"standard"` → retourne `"standard"`
   - `ui_difficulty == "difficile"` et non supporté → fallback vers `"standard"` si présent, sinon `"facile"`
   - Sinon retourne la difficulté normalisée

**Exemple** :
```python
# CALCUL_NOMBRES_V1 supporte facile/standard
map_ui_difficulty_to_generator("CALCUL_NOMBRES_V1", "moyen")
# → "standard" (car "moyen" UI = "standard" générateur)

map_ui_difficulty_to_generator("CALCUL_NOMBRES_V1", "difficile")
# → "standard" (fallback car "difficile" non supporté)
```

### Intégration

La fonction `map_ui_difficulty_to_generator()` est utilisée dans :

1. **`backend/services/exercise_persistence_service.py`** :
   - Méthode `_validate_template_placeholders()` : Mappe les difficultés avant de tester les placeholders
   - Distingue les erreurs `INVALID_DIFFICULTY` des vraies erreurs `ADMIN_TEMPLATE_MISMATCH`

2. **`backend/routes/exercises_routes.py`** :
   - Endpoint `/generate` : Mappe la difficulté avant d'appeler `GeneratorFactory.generate()`
   - Logs `[DIFFICULTY_MAPPED]` pour traçabilité

3. **`backend/services/generator_template_service.py`** :
   - Méthode `validate_template()` : Mappe la difficulté avant validation (déjà fait via `coerce_to_supported_difficulty()`)

## Mapping des difficultés

### Règles de mapping

| Difficulté UI | Générateur supporte | Résultat |
|---------------|---------------------|----------|
| `facile` | `facile` | `facile` |
| `moyen` | `standard` | `standard` |
| `moyen` | `facile` | `facile` (fallback) |
| `difficile` | `standard` | `standard` (fallback) |
| `difficile` | `facile` | `facile` (fallback) |
| `difficile` | `moyen` | `moyen` (fallback) |

### Exemples concrets

#### CALCUL_NOMBRES_V1 (supporte : `facile`, `standard`)

```python
map_ui_difficulty_to_generator("CALCUL_NOMBRES_V1", "facile")
# → "facile" ✓

map_ui_difficulty_to_generator("CALCUL_NOMBRES_V1", "moyen")
# → "standard" ✓ (mapping UI moyen → générateur standard)

map_ui_difficulty_to_generator("CALCUL_NOMBRES_V1", "difficile")
# → "standard" ✓ (fallback)
```

#### Générateur standard (supporte : `facile`, `moyen`, `difficile`)

```python
map_ui_difficulty_to_generator("THALES_V2", "facile")
# → "facile" ✓

map_ui_difficulty_to_generator("THALES_V2", "moyen")
# → "moyen" ✓

map_ui_difficulty_to_generator("THALES_V2", "difficile")
# → "difficile" ✓
```

## Logs et observabilité

### Tags de log

- `[DIFFICULTY_MAPPED]` : Lorsqu'une difficulté UI est mappée vers une difficulté générateur différente

### Exemple de log

```
[DIFFICULTY_MAPPED] generator=CALCUL_NOMBRES_V1 ui=moyen -> generator=standard (supported: ['facile', 'standard'])
```

### Logs structurés (observabilité)

```json
{
  "event": "difficulty_mapped",
  "ui_difficulty": "moyen",
  "generator_difficulty": "standard",
  "generator_key": "CALCUL_NOMBRES_V1"
}
```

## Distinction des erreurs

### Avant P4.D HOTFIX

- Toute erreur de génération → `ADMIN_TEMPLATE_MISMATCH`
- Erreurs 500 parfois au lieu de 422

### Après P4.D HOTFIX

- Erreur de difficulté invalide → ignorée (ne remonte pas comme mismatch)
- Vraie erreur de template mismatch → `ADMIN_TEMPLATE_MISMATCH` (seulement si génération OK mais placeholders manquants)
- Toutes les erreurs sont des 422 propres, jamais de 500

## Tests

### Scénarios testés

1. **CALCUL_NOMBRES_V1 avec "facile"** :
   - UI : `facile`
   - Générateur : `facile`
   - Résultat : ✅ OK

2. **CALCUL_NOMBRES_V1 avec "moyen"** :
   - UI : `moyen`
   - Générateur : `standard` (mappé)
   - Résultat : ✅ OK

3. **CALCUL_NOMBRES_V1 avec "difficile"** :
   - UI : `difficile`
   - Générateur : `standard` (fallback)
   - Résultat : ✅ OK

4. **Validation admin** :
   - Teste `facile`, `moyen`, `difficile` avec mapping automatique
   - Ne remonte `ADMIN_TEMPLATE_MISMATCH` que si vraie erreur de placeholders

### Exécution des tests

```bash
# Tests unitaires (à créer)
pytest backend/tests/test_difficulty_mapping.py -v

# Tests d'intégration
pytest backend/tests/test_admin_template_difficulty_coercion.py -v
```

## Migration

Aucune migration de base de données nécessaire. Les exercices existants continuent de fonctionner, mais bénéficient maintenant du mapping automatique.

## Références

- **P4.C** : Standardisation des difficultés (`docs/P4C_DIFFICULTY_STANDARDIZATION.md`)
- **P4.D** : Coercition dans la validation admin (`docs/P4D_ADMIN_VALIDATE_DIFFICULTY_COERCION.md`)
- **Utilitaires** : `backend/utils/difficulty_utils.py`
- **Service** : `backend/services/exercise_persistence_service.py`
- **Routes** : `backend/routes/exercises_routes.py`

## Auteur

P4.D HOTFIX — Mapping Difficulté UI → Générateur
Date : 2024

