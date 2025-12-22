# Générateur RAISONNEMENT_MULTIPLICATIF_V1

## Vue d'ensemble

Le générateur `RAISONNEMENT_MULTIPLICATIF_V1` est un générateur **PREMIUM** pour le raisonnement multiplicatif en 6e et 5e. Il couvre la proportionnalité, les pourcentages, la vitesse et l'échelle.

**Version** : 1.0.0  
**Niveaux** : 6e, 5e  
**Type d'exercice** : RAISONNEMENT_MULTIPLICATIF  
**Statut** : PREMIUM

## Objectifs pédagogiques

- **6e** : Comprendre et utiliser la proportionnalité dans des tableaux
- **6e** : Calculer des pourcentages simples (10%, 25%, 50%, 75%)
- **5e** : Maîtriser la proportionnalité avec décimaux
- **5e** : Calculer des pourcentages variés
- **5e** : Utiliser la formule vitesse = distance ÷ temps
- **5e** : Comprendre et utiliser les échelles sur les cartes

## Types d'exercices

### 1. proportionnalite_tableau

**Description** : Compléter un tableau de proportionnalité

**6e** :
- Facile : Coefficients entiers simples (2-5), 3 valeurs
- Moyen : Coefficients variés (2-10), 4 valeurs

**5e** :
- Moyen : Coefficients entiers ou décimaux, 4 valeurs
- Difficile : Coefficients variés avec décimaux, 5 valeurs

**Variables générées** :
- `enonce` : Tableau avec valeur manquante
- `solution` : Explication de la méthode
- `calculs_intermediaires` : Calculs étape par étape (coefficient + calcul)
- `reponse_finale` : Valeur manquante
- `donnees` : Dict avec tableau, coefficient, index manquant
- `methode` : "coefficient_de_proportionnalite"

### 2. pourcentage

**Description** : Exercices sur les pourcentages

**Sous-types** :
- **calcul_pourcentage** : Calculer X% de Y
- **trouver_pourcentage** : Quel pourcentage représente X par rapport à Y ?
- **trouver_valeur** : Si X% = Y, quelle est la valeur totale ?

**6e** :
- Facile : Pourcentages simples (10%, 25%, 50%, 75%)

**5e** :
- Moyen : Pourcentages variés avec décimaux
- Difficile : Pourcentages complexes (1-200%)

**Variables générées** :
- `enonce` : Énoncé selon le sous-type
- `solution` : Explication de la méthode
- `calculs_intermediaires` : Calculs étape par étape
- `reponse_finale` : Résultat (nombre ou pourcentage)
- `donnees` : Dict avec type, pourcentage, valeurs
- `methode` : "regle_de_trois_pourcentage"

### 3. vitesse

**Description** : Calculs de vitesse moyenne

**Sous-types** :
- **calcul_vitesse** : v = d/t
- **calcul_distance** : d = v × t
- **calcul_temps** : t = d/v

**5e uniquement** (peut fonctionner en 6e mais moins courant)

**Variables générées** :
- `enonce` : Énoncé avec distance/temps/vitesse
- `solution` : Explication de la formule
- `calculs_intermediaires` : Calculs étape par étape
- `reponse_finale` : Résultat avec unité (km/h, km, h)
- `donnees` : Dict avec type, distance, vitesse, temps
- `methode` : "formule_vitesse"

### 4. echelle

**Description** : Calculs d'échelle sur les cartes

**Sous-types** :
- **calcul_distance_reelle** : Distance réelle = distance carte × échelle
- **calcul_distance_carte** : Distance carte = distance réelle ÷ échelle
- **calcul_echelle** : Échelle = distance réelle ÷ distance carte (5e uniquement)

**5e uniquement** (peut fonctionner en 6e mais moins courant)

**Variables générées** :
- `enonce` : Énoncé avec échelle et distances
- `solution` : Explication de la méthode
- `calculs_intermediaires` : Calculs étape par étape avec conversions
- `reponse_finale` : Résultat (distance en km/cm ou échelle)
- `donnees` : Dict avec type, échelle, distances
- `methode` : "calcul_echelle"

## Paramètres

### Paramètres obligatoires

- `seed` (int, obligatoire) : Seed pour reproductibilité

### Paramètres optionnels

- `exercise_type` (enum) : Type d'exercice
  - Valeurs : `"proportionnalite_tableau"`, `"pourcentage"`, `"vitesse"`, `"echelle"`
  - Défaut : `"proportionnalite_tableau"`

- `difficulty` (enum) : Niveau de difficulté
  - Valeurs : `"facile"`, `"moyen"`, `"difficile"`
  - Défaut : `"moyen"`

- `grade` (enum) : Niveau scolaire
  - Valeurs : `"6e"`, `"5e"`
  - Défaut : `"6e"`

- `preset` (enum) : Preset pédagogique
  - Valeurs : `"simple"`, `"standard"`
  - Défaut : `"standard"`

## Presets pédagogiques

### 6e

- **6e_proportionnalite_facile** : Tableaux de proportionnalité simples
- **6e_proportionnalite_moyen** : Tableaux avec coefficients variés
- **6e_pourcentage_facile** : Pourcentages simples (10%, 25%, 50%, 75%)

### 5e

- **5e_proportionnalite_moyen** : Tableaux avec décimaux
- **5e_pourcentage_moyen** : Pourcentages variés avec décimaux
- **5e_vitesse_moyen** : Calculs de vitesse moyenne
- **5e_echelle_moyen** : Calculs d'échelle et de distances

## Variables de sortie (toujours présentes)

Toutes ces variables sont **toujours** présentes dans le résultat :

```python
{
    "enonce": str,                    # Énoncé de l'exercice
    "consigne": str,                  # Consigne pour l'élève
    "solution": str,                   # Solution détaillée (PREMIUM)
    "calculs_intermediaires": str,    # Calculs étape par étape numérotés
    "reponse_finale": str,            # Réponse finale
    "donnees": dict,                  # Données structurées (tableau, valeurs, etc.)
    "methode": str,                   # Méthode utilisée
    "niveau": "6e" | "5e",           # Niveau scolaire
    "type_exercice": str              # Type d'exercice
}
```

**Garantie** : Aucun placeholder non résolu. Toutes les variables sont toujours fournies.

**Solutions PREMIUM** : Les solutions sont détaillées avec :
- Étapes numérotées
- Justifications courtes
- Calculs intermédiaires explicites

## Gestion des erreurs

Le générateur lève des `HTTPException` 422 structurées avec :

- `error_code` : Code d'erreur standardisé
- `error` : Identifiant de l'erreur
- `message` : Message d'erreur lisible
- `hint` : Indication pour résoudre l'erreur
- `context` : Contexte supplémentaire

### Codes d'erreur

- `INVALID_EXERCISE_TYPE` : Type d'exercice invalide
- `INVALID_GRADE` : Niveau scolaire invalide
- `INVALID_DIFFICULTY` : Difficulté invalide
- `GENERATION_FAILED` : Erreur lors de la génération (seed manquant, etc.)

### Robustesse

Le générateur interdit :
- Division par 0 (vérifications explicites)
- Pourcentages > 200% si non voulu (limitation)
- Unités invalides (conversions correctes)
- Incohérences dans les données

## Exemples d'utilisation

### Exemple 1 : Proportionnalité 6e

```python
from backend.generators.factory import GeneratorFactory

result = GeneratorFactory.generate(
    key="RAISONNEMENT_MULTIPLICATIF_V1",
    exercise_params={
        "exercise_type": "proportionnalite_tableau",
        "difficulty": "facile",
        "grade": "6e",
        "seed": 42
    }
)

variables = result["variables"]
print(variables["enonce"])  # Tableau avec valeur manquante
print(variables["reponse_finale"])  # Valeur calculée
```

### Exemple 2 : Pourcentage 5e

```python
result = GeneratorFactory.generate(
    key="RAISONNEMENT_MULTIPLICATIF_V1",
    exercise_params={
        "exercise_type": "pourcentage",
        "difficulty": "moyen",
        "grade": "5e",
        "seed": 123
    }
)

variables = result["variables"]
print(variables["enonce"])  # "Calcule 35% de 150."
print(variables["calculs_intermediaires"])  # Étapes numérotées
```

### Exemple 3 : Vitesse 5e

```python
result = GeneratorFactory.generate(
    key="RAISONNEMENT_MULTIPLICATIF_V1",
    exercise_params={
        "exercise_type": "vitesse",
        "difficulty": "moyen",
        "grade": "5e",
        "seed": 456
    }
)

variables = result["variables"]
print(variables["enonce"])  # "Un véhicule parcourt 120 km en 2 heures..."
print(variables["reponse_finale"])  # "60 km/h"
```

## Chapitres couverts

### 6e

- Proportionnalité (tableaux)
- Pourcentages simples

### 5e

- Proportionnalité (tableaux avec décimaux)
- Pourcentages variés
- Vitesse moyenne
- Échelles et plans

**Note** : Le mapping dans le curriculum sera ajouté ultérieurement.

## Déterminisme

Le générateur est **déterministe** : un même seed produit toujours le même résultat.

```python
# Même seed → même résultat
result1 = GeneratorFactory.generate("RAISONNEMENT_MULTIPLICATIF_V1", {"seed": 42, ...})
result2 = GeneratorFactory.generate("RAISONNEMENT_MULTIPLICATIF_V1", {"seed": 42, ...})
assert result1["variables"] == result2["variables"]
```

## Batch-compatible

Le générateur est compatible avec la génération en lot :

```python
# Générer un lot de 5 exercices
for i in range(5):
    result = GeneratorFactory.generate(
        "RAISONNEMENT_MULTIPLICATIF_V1",
        {"seed": 100 + i, ...}
    )
    # Chaque exercice est unique grâce au seed différent
```

## Notes techniques

- **SVG** : Aucun (svg_mode="NONE")
- **Géométrie** : Aucune (geo_data=None)
- **Dépendances** : Aucune dépendance externe
- **Performance** : Génération rapide (< 10ms)
- **Premium** : Solutions détaillées avec étapes numérotées

## Tests

Voir `backend/tests/test_raisonnement_multiplicatif_v1.py` pour les tests unitaires complets.

**Commandes de test** :
```bash
pytest backend/tests/test_raisonnement_multiplicatif_v1.py -v
```

