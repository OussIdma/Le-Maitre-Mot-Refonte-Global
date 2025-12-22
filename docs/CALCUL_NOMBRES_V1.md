# Générateur CALCUL_NOMBRES_V1

## Vue d'ensemble

Le générateur `CALCUL_NOMBRES_V1` est un générateur robuste et déterministe pour les calculs numériques en 6e et 5e. Il couvre les opérations simples, les priorités opératoires et les décimaux.

**Version** : 1.0.0  
**Niveaux** : 6e, 5e  
**Type d'exercice** : CALCUL_NOMBRES

## Objectifs pédagogiques

- **6e** : Maîtriser les opérations de base (addition, soustraction, multiplication, division) avec les entiers naturels
- **6e** : Comprendre et appliquer les priorités opératoires dans des expressions simples
- **5e** : Étendre les calculs aux nombres décimaux
- **5e** : Renforcer les priorités opératoires avec des expressions plus complexes
- **5e** : Comparer, calculer et arrondir des nombres décimaux

## Types d'exercices

### 1. operations_simples

**Description** : Opérations de base (addition, soustraction, multiplication, division)

**6e** :
- Facile : Additions et soustractions avec entiers (1-50)
- Standard : Toutes opérations avec entiers (1-100)

**5e** :
- Facile : Additions et soustractions avec entiers ou décimaux simples
- Standard : Toutes opérations avec entiers et décimaux (1-50)

**Variables générées** :
- `enonce` : "Calculer : a op b"
- `solution` : Explication de la méthode
- `calculs_intermediaires` : Calcul étape par étape
- `reponse_finale` : Résultat numérique
- `consigne` : Instructions pour l'élève

### 2. priorites_operatoires

**Description** : Expressions à plusieurs opérations avec respect des priorités

**6e** :
- Facile : Expressions à 2 opérations sans parenthèses
- Standard : Expressions à 2-3 opérations avec parenthèses possibles

**5e** :
- Facile : Expressions à 2 opérations (entiers ou décimaux)
- Standard : Expressions complexes avec décimaux et parenthèses

**Variables générées** :
- `enonce` : "Calculer : expression"
- `solution` : Explication des priorités
- `calculs_intermediaires` : Calculs étape par étape avec justification
- `reponse_finale` : Résultat numérique
- `consigne` : "Effectue le calcul en respectant les priorités opératoires."

### 3. decimaux

**Description** : Exercices sur les nombres décimaux (5e uniquement)

**Sous-types** :
- **Comparaison** : Comparer deux nombres décimaux
- **Calcul** : Opérations avec décimaux
- **Arrondi** : Arrondir à l'unité ou au dixième

**Variables générées** :
- `enonce` : Énoncé selon le sous-type
- `solution` : Explication de la méthode
- `calculs_intermediaires` : Calculs ou justification
- `reponse_finale` : Résultat ou comparaison
- `consigne` : Instructions spécifiques

## Paramètres

### Paramètres obligatoires

- `seed` (int, obligatoire) : Seed pour reproductibilité

### Paramètres optionnels

- `exercise_type` (enum) : Type d'exercice
  - Valeurs : `"operations_simples"`, `"priorites_operatoires"`, `"decimaux"`
  - Défaut : `"operations_simples"`

- `difficulty` (enum) : Niveau de difficulté
  - Valeurs : `"facile"`, `"standard"`
  - Défaut : `"standard"`

- `grade` (enum) : Niveau scolaire
  - Valeurs : `"6e"`, `"5e"`
  - Défaut : `"6e"`

- `preset` (enum) : Preset pédagogique
  - Valeurs : `"simple"`, `"standard"`
  - Défaut : `"standard"`

## Presets pédagogiques

### 6e

- **6e_operations_facile** : Additions et soustractions avec entiers naturels
- **6e_operations_standard** : Toutes opérations avec entiers naturels
- **6e_priorites_facile** : Expressions à 2 opérations sans parenthèses
- **6e_priorites_standard** : Expressions à 2-3 opérations avec parenthèses possibles

### 5e

- **5e_operations_standard** : Opérations avec entiers et décimaux simples
- **5e_priorites_standard** : Expressions complexes avec décimaux
- **5e_decimaux_standard** : Comparaison, calculs et arrondis avec décimaux

## Variables de sortie (toujours présentes)

Toutes ces variables sont **toujours** présentes dans le résultat :

```python
{
    "enonce": str,                    # Énoncé de l'exercice
    "solution": str,                  # Solution détaillée
    "calculs_intermediaires": str,    # Calculs étape par étape
    "reponse_finale": str,            # Réponse finale (nombre)
    "niveau": "6e" | "5e",           # Niveau scolaire
    "type_exercice": str,             # Type d'exercice
    "consigne": str                   # Consigne pour l'élève
}
```

**Garantie** : Aucun placeholder non résolu. Toutes les variables sont toujours fournies.

## Gestion des erreurs

Le générateur lève des `HTTPException` 422 structurées avec :

- `error_code` : Code d'erreur standardisé
- `error` : Identifiant de l'erreur
- `message` : Message d'erreur lisible
- `hint` : Indication pour résoudre l'erreur
- `context` : Contexte supplémentaire

### Codes d'erreur

- `INVALID_EXERCISE_TYPE` : Type d'exercice invalide
- `INVALID_GRADE` : Niveau scolaire invalide (ex: décimaux en 6e)
- `INVALID_DIFFICULTY` : Difficulté invalide
- `GENERATION_FAILED` : Erreur lors de la génération (seed manquant, etc.)

## Exemples d'utilisation

### Exemple 1 : Opérations simples 6e

```python
from backend.generators.factory import GeneratorFactory

result = GeneratorFactory.generate(
    key="CALCUL_NOMBRES_V1",
    exercise_params={
        "exercise_type": "operations_simples",
        "difficulty": "facile",
        "grade": "6e",
        "seed": 42
    }
)

variables = result["variables"]
print(variables["enonce"])  # "Calculer : 15 + 23"
print(variables["reponse_finale"])  # "38"
```

### Exemple 2 : Priorités opératoires 5e

```python
result = GeneratorFactory.generate(
    key="CALCUL_NOMBRES_V1",
    exercise_params={
        "exercise_type": "priorites_operatoires",
        "difficulty": "standard",
        "grade": "5e",
        "seed": 123
    }
)

variables = result["variables"]
print(variables["enonce"])  # "Calculer : (12.5 + 8.3) × 2"
```

### Exemple 3 : Décimaux 5e

```python
result = GeneratorFactory.generate(
    key="CALCUL_NOMBRES_V1",
    exercise_params={
        "exercise_type": "decimaux",
        "difficulty": "standard",
        "grade": "5e",
        "seed": 456
    }
)

variables = result["variables"]
print(variables["enonce"])  # "Comparer : 12.5 et 12.3"
```

## Chapitres couverts

### 6e

- **6e_N04** : Addition et soustraction de nombres entiers
- **6e_N05** : Multiplication de nombres entiers
- **6e_N06** : Division euclidienne

### 5e

- Calculs sur les nombres (opérations avec décimaux)
- Priorités opératoires (expressions complexes)
- Calculs avec décimaux (comparaison, arrondis)

## Déterminisme

Le générateur est **déterministe** : un même seed produit toujours le même résultat.

```python
# Même seed → même résultat
result1 = GeneratorFactory.generate("CALCUL_NOMBRES_V1", {"seed": 42, ...})
result2 = GeneratorFactory.generate("CALCUL_NOMBRES_V1", {"seed": 42, ...})
assert result1["variables"] == result2["variables"]
```

## Batch-compatible

Le générateur est compatible avec la génération en lot :

```python
# Générer un lot de 5 exercices
for i in range(5):
    result = GeneratorFactory.generate(
        "CALCUL_NOMBRES_V1",
        {"seed": 100 + i, ...}
    )
    # Chaque exercice est unique grâce au seed différent
```

## Notes techniques

- **SVG** : Aucun (svg_mode="NONE")
- **Géométrie** : Aucune (geo_data=None)
- **Dépendances** : Aucune dépendance externe
- **Performance** : Génération rapide (< 10ms)

## Tests

Voir `backend/tests/test_calcul_nombres_v1.py` pour les tests unitaires complets.

**Commandes de test** :
```bash
pytest backend/tests/test_calcul_nombres_v1.py -v
```

