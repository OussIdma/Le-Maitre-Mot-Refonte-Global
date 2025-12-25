# P4.D — HOTFIX CRITIQUE: Coercition de difficulté dans la validation admin

## Contexte

### Problème identifié

L'interface admin utilise les difficultés canoniques (`facile`, `moyen`, `difficile`), mais certains générateurs n'acceptent que des difficultés spécifiques :

- **CALCUL_NOMBRES_V1** : accepte uniquement `facile` et `standard`
- D'autres générateurs peuvent avoir des restrictions similaires

Avant P4.D, la validation admin des templates (`/api/v1/admin/generator-templates/validate`) renvoyait :
1. `INVALID_DIFFICULTY` (422) si la difficulté n'était pas supportée
2. Puis `ADMIN_TEMPLATE_MISMATCH` (422) car la génération échouait et les placeholders semblaient "manquants"

### Impact

- **Zéro 422 lié aux difficultés** : L'admin ne doit jamais voir d'erreur 422 pour une difficulté canonique
- **Distinction claire** : Les erreurs `ADMIN_TEMPLATE_MISMATCH` ne doivent apparaître QUE si le générateur réussit mais ne fournit vraiment pas les variables
- **Cohérence avec `/generate`** : La validation admin doit appliquer la même logique de coercition que l'endpoint de génération

## Solution implémentée

### 1. Normalisation et coercition dans `generator_template_service.py`

La méthode `validate_template()` applique maintenant :

```python
# 1. Normaliser la difficulté
normalized_difficulty = normalize_difficulty(request.difficulty)  # "standard" → "moyen"

# 2. Coercte selon les difficultés supportées
coerced_difficulty = coerce_to_supported_difficulty(
    normalized_difficulty,
    supported_difficulties,
    ctx,
    obs_logger
)

# 3. Générer avec la difficulté coercée
GeneratorFactory.generate(
    key=request.generator_key,
    overrides={"difficulty": coerced_difficulty, ...}
)
```

### 2. Distinction des erreurs

**Avant P4.D** :
- Toute erreur de génération → `ADMIN_TEMPLATE_MISMATCH`

**Après P4.D** :
- Erreur de difficulté invalide → `GENERATOR_INVALID_DIFFICULTY`
- Génération OK mais placeholders manquants → `ADMIN_TEMPLATE_MISMATCH` (vrai cas)

### 3. Réponse enrichie

La réponse de `/validate` inclut maintenant :

```json
{
  "valid": true,
  "difficulty_requested": "moyen",
  "difficulty_used": "standard",
  "used_placeholders": [...],
  "preview": {...}
}
```

## Endpoints modifiés

### `/api/v1/admin/generator-templates/validate` (POST)

**Fichier** : `backend/routes/admin_template_routes.py`

**Changements** :
- Applique `normalize_difficulty()` puis `coerce_to_supported_difficulty()` avant génération
- Retourne `difficulty_requested` et `difficulty_used` dans la réponse
- Distingue `GENERATOR_INVALID_DIFFICULTY` de `ADMIN_TEMPLATE_MISMATCH`

**Service** : `backend/services/generator_template_service.py`
- Méthode `validate_template()` modifiée

## Tests

### Fichier de test

`backend/tests/test_admin_template_difficulty_coercion.py`

### Scénarios testés

1. **Coercition "moyen" → "standard"** : Pour CALCUL_NOMBRES_V1 qui n'accepte que `facile`/`standard`
2. **Coercition "difficile" → "standard"** : Fallback chain pour difficultés non supportées
3. **Erreur INVALID_DIFFICULTY** : Distinction avec ADMIN_TEMPLATE_MISMATCH
4. **Vrai template mismatch** : Génération OK mais placeholders manquants
5. **Normalisation "standard" → "moyen"** : Avant coercition

### Exécution

```bash
pytest backend/tests/test_admin_template_difficulty_coercion.py -v
```

## Exemples d'utilisation

### Exemple 1 : Validation avec difficulté coercée

**Requête** :
```json
{
  "generator_key": "CALCUL_NOMBRES_V1",
  "difficulty": "moyen",
  "grade": "6e",
  "seed": 42,
  "enonce_template_html": "<p>{{enonce}}</p>",
  "solution_template_html": "<p>{{solution}}</p>"
}
```

**Réponse** :
```json
{
  "valid": true,
  "difficulty_requested": "moyen",
  "difficulty_used": "standard",
  "used_placeholders": ["enonce", "solution"],
  "preview": {
    "enonce_html": "<p>Calculer : 15 + 23</p>",
    "solution_html": "<p>15 + 23 = 38</p>",
    "variables": {...}
  }
}
```

### Exemple 2 : Erreur de difficulté invalide

**Requête** : Même que ci-dessus, mais générateur qui refuse même après coercition

**Réponse** :
```json
{
  "valid": false,
  "error_code": "GENERATOR_INVALID_DIFFICULTY",
  "message": "Le générateur 'CALCUL_NOMBRES_V1' ne peut pas générer avec la difficulté 'standard'...",
  "difficulty_requested": "moyen",
  "difficulty_used": "standard"
}
```

### Exemple 3 : Vrai template mismatch

**Requête** :
```json
{
  "generator_key": "CALCUL_NOMBRES_V1",
  "difficulty": "facile",
  "enonce_template_html": "<p>{{enonce}}</p>",
  "solution_template_html": "<p>{{variable_inexistante}}</p>"
}
```

**Réponse** :
```json
{
  "valid": false,
  "error_code": "ADMIN_TEMPLATE_MISMATCH",
  "message": "Placeholders manquants: variable_inexistante...",
  "missing_placeholders": ["variable_inexistante"],
  "difficulty_requested": "facile",
  "difficulty_used": "facile"
}
```

## Logs et observabilité

### Tags de log

- `[DIFFICULTY_COERCED]` : Lorsqu'une difficulté est coercée
- `[GENERATOR_INVALID_DIFFICULTY]` : Lorsqu'une erreur de difficulté invalide est détectée

### Exemple de log

```
[DIFFICULTY_COERCED] Validation template: requested=moyen coerced=standard generator=CALCUL_NOMBRES_V1
```

## Vérification de non-régression

### Endpoints non modifiés

Les endpoints suivants n'appellent pas `GeneratorFactory.generate()` dans un contexte admin et n'ont donc pas besoin de modification :

- `/api/v1/admin/chapters/{code}/generators` (GET, PUT)
- `/api/v1/admin/chapters/{code}/generators/auto-fill` (POST)
- `/api/v1/admin/chapters/{code}/generators/normalize` (POST)

### Endpoint `/generate` (non modifié)

L'endpoint `/api/v1/exercises/generate` applique déjà la coercition de difficulté (P4.C) et n'a pas été modifié dans P4.D.

## Migration

Aucune migration de base de données nécessaire. Les templates existants continuent de fonctionner, mais bénéficient maintenant de la coercition automatique.

## Notes techniques

### Ordre d'exécution

1. **Normalisation** : `normalize_difficulty()` convertit `standard` → `moyen`, `hard` → `difficile`, etc.
2. **Coercition** : `coerce_to_supported_difficulty()` applique la fallback chain :
   - `difficile` → `moyen` → `facile` → `standard` (si supporté)
3. **Génération** : `GeneratorFactory.generate()` avec la difficulté coercée
4. **Validation** : Vérification des placeholders et sécurité HTML

### Fallback chain

La fonction `coerce_to_supported_difficulty()` implémente une hiérarchie de fallback :

```
difficile → moyen → facile → standard (si supporté)
```

Si aucune difficulté n'est supportée, une erreur est levée.

## Références

- **P4.C** : Standardisation des difficultés (`docs/P4C_DIFFICULTY_STANDARDIZATION.md`)
- **P4.B** : Gestion des générateurs activés dans les chapitres
- **Utilitaires** : `backend/utils/difficulty_utils.py`
- **Service** : `backend/services/generator_template_service.py`

## Auteur

P4.D — Hotfix critique pour la validation admin
Date : 2024



