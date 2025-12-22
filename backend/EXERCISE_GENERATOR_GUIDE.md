# Guide du Générateur d'Exercices TEMPLATE

## 📚 Vue d'ensemble

Le générateur TEMPLATE permet de créer des exercices mathématiques de manière déterministe et reproductible, sans aucun appel IA.

**Principe clé** : Même seed + même configuration = même exercice

---

## 🔧 Configuration d'un ExerciseType

### Paramètres de random_config

Le champ `random_config` dans un ExerciseType contrôle la génération :

```json
{
  "random_config": {
    "min_value": 1,           // Valeur minimum (défaut: 1)
    "max_value": 10,          // Valeur maximum (défaut: 10)
    "operations": ["+", "-", "*"],  // Opérations disponibles
    "geometry": true,         // Activer mode géométrique
    "property_type": "egalite" // Type de propriété (pour verifier_propriete)
  }
}
```

### Types de questions (question_kinds)

```json
{
  "question_kinds": {
    "trouver_valeur": true,      // Chercher une valeur/résultat
    "verifier_propriete": false   // Vérifier une propriété (vrai/faux)
  }
}
```

---

## 📊 Types de Génération

### 1. Type : trouver_valeur

**Sans géométrie** :
```json
{
  "question_kinds": {"trouver_valeur": true},
  "random_config": {
    "min_value": 1,
    "max_value": 20
  }
}
```

**Sortie** :
```json
{
  "enonce_brut": "Calculer : 15 + 8",
  "data": {
    "type": "trouver_valeur",
    "value_a": 15,
    "value_b": 8
  },
  "solution_brut": "Résultat : 23"
}
```

**Avec géométrie** :
```json
{
  "question_kinds": {"trouver_valeur": true},
  "random_config": {
    "min_value": 1,
    "max_value": 20,
    "geometry": true
  }
}
```

**Sortie** :
```json
{
  "enonce_brut": "Soit A(5, 12) et B(8, 16). Calculer la distance AB.",
  "data": {
    "type": "trouver_valeur",
    "value_a": 10,
    "value_b": 7,
    "point_a": {"x": 5, "y": 12},
    "point_b": {"x": 8, "y": 16}
  },
  "solution_brut": "Distance AB = √((3)² + (4)²) = √(25) ≈ 5.00"
}
```

### 2. Type : verifier_propriete

```json
{
  "question_kinds": {"verifier_propriete": true},
  "random_config": {
    "min_value": 1,
    "max_value": 20,
    "property_type": "egalite"
  }
}
```

**Sortie** :
```json
{
  "enonce_brut": "Vérifier si 16 = 2 × 8. Répondre par Vrai ou Faux.",
  "data": {
    "type": "verifier_propriete",
    "value_a": 8,
    "value_b": 16,
    "expected_answer": true,
    "property_type": "egalite"
  },
  "solution_brut": "Calcul : 2 × 8 = 16\nComparaison : 16 = 16\nRéponse : Vrai"
}
```

---

## 🎲 Reproductibilité avec Seed

### Principe

```python
rng = random.Random(seed)  # Initialisation isolée
value_a = rng.randint(min_value, max_value)  # Génération déterministe
```

### Exemple

```bash
# Appel 1 avec seed=42
POST /api/mathalea/generate-exercise
{"seed": 42, "nb_questions": 3, ...}

# Résultat :
Q1: value_a=11, value_b=2
Q2: value_a=12, value_b=5
Q3: value_a=4, value_b=3

# Appel 2 avec seed=42 (même résultat)
Q1: value_a=11, value_b=2  ✅
Q2: value_a=12, value_b=5  ✅
Q3: value_a=4, value_b=3   ✅

# Appel 3 avec seed=123 (résultat différent)
Q1: value_a=1, value_b=5   ✅ Différent
Q2: value_a=13, value_b=7  ✅ Différent
Q3: value_a=2, value_b=14  ✅ Différent
```

---

## 📈 Influence de la Difficulté

### Multiplicateur

```python
difficulty_multiplier = {
    "facile": 1.0,
    "moyen": 1.5,
    "difficile": 2.0
}

adjusted_max = max_value * multiplier
```

### Exemple

**ExerciseType avec max_value=10** :

| Difficulté | Max ajusté | Exemple valeurs |
|------------|------------|-----------------|
| facile     | 10         | 3, 7, 9         |
| moyen      | 15         | 11, 14, 8       |
| difficile  | 20         | 18, 19, 16      |

```bash
# Facile : valeurs dans [1, 10]
{"seed": 42, "difficulty": "facile"}
→ avg = 6.5

# Difficile : valeurs dans [1, 20]
{"seed": 42, "difficulty": "difficile"}
→ avg = 12.8
```

---

## 🔨 Créer un ExerciseType Personnalisé

### Étape 1 : Définir le type

```bash
POST /api/mathalea/exercise-types
{
  "code_ref": "PYTHAGORE_SIMPLE",
  "titre": "Théorème de Pythagore - Calcul simple",
  "niveau": "4e",
  "domaine": "Géométrie",
  "min_questions": 1,
  "max_questions": 20,
  "default_questions": 5,
  "difficulty_levels": ["facile", "moyen", "difficile"],
  "question_kinds": {
    "trouver_valeur": true
  },
  "random_config": {
    "min_value": 3,
    "max_value": 15,
    "geometry": true
  },
  "generator_kind": "template",
  "supports_seed": true
}
```

### Étape 2 : Générer des exercices

```bash
POST /api/mathalea/generate-exercise
{
  "exercise_type_id": "uuid-from-step-1",
  "nb_questions": 5,
  "seed": 12345,
  "difficulty": "moyen"
}
```

---

## 📐 Workflow Complet

### Cas d'usage : Feuille de révisions

```bash
# 1. Créer des compétences
POST /api/mathalea/competences
{
  "code": "6G1",
  "intitule": "Symétrie axiale",
  "niveau": "6e",
  "domaine": "Géométrie"
}
# → comp_id

# 2. Créer un ExerciseType
POST /api/mathalea/exercise-types
{
  "code_ref": "SYM_AX_DISTANCE",
  "titre": "Symétrie - Calcul de distance",
  "niveau": "6e",
  "domaine": "Géométrie",
  "competences_ids": [comp_id],
  "question_kinds": {"trouver_valeur": true},
  "random_config": {
    "min_value": 1,
    "max_value": 20,
    "geometry": true
  },
  "generator_kind": "template"
}
# → exercise_type_id

# 3. Créer une feuille
POST /api/mathalea/sheets
{
  "titre": "Révisions Symétrie",
  "niveau": "6e",
  "owner_id": "prof_123"
}
# → sheet_id

# 4. Ajouter l'exercice à la feuille
POST /api/mathalea/sheet-items
{
  "sheet_id": sheet_id,
  "exercise_type_id": exercise_type_id,
  "nb_questions": 5,
  "difficulty": "moyen",
  "seed": 42
}

# 5. Générer l'exercice
POST /api/mathalea/generate-exercise
{
  "exercise_type_id": exercise_type_id,
  "nb_questions": 5,
  "seed": 42,
  "difficulty": "moyen"
}
# → JSON avec 5 questions
```

---

## 🧪 Tests de Reproductibilité

### Script de test

```python
import asyncio
from httpx import AsyncClient

async def test_reproducibility():
    async with AsyncClient(base_url="http://localhost:8001") as client:
        # Premier appel
        response1 = await client.post("/api/mathalea/generate-exercise", json={
            "exercise_type_id": "uuid",
            "nb_questions": 10,
            "seed": 42
        })
        data1 = response1.json()
        
        # Deuxième appel (même seed)
        response2 = await client.post("/api/mathalea/generate-exercise", json={
            "exercise_type_id": "uuid",
            "nb_questions": 10,
            "seed": 42
        })
        data2 = response2.json()
        
        # Vérifier égalité
        assert data1 == data2
        print("✅ Reproductibilité validée")

asyncio.run(test_reproducibility())
```

---

## 🎯 Bonnes Pratiques

### 1. Choix de la seed
- **Fixe** : Pour exercices reproductibles (contrôles, corrections)
- **Aléatoire** : Pour entraînement varié

```python
import time
seed_fixe = 42  # Toujours le même exercice
seed_aleatoire = int(time.time())  # Exercice différent à chaque fois
```

### 2. Configuration random_config
- Adapter les plages selon le niveau
- Tester avec différentes seeds
- Valider que les valeurs générées sont pédagogiquement pertinentes

### 3. Difficulté
- Créer plusieurs ExerciseTypes avec des configs différentes
- OU utiliser le paramètre difficulty pour adapter dynamiquement

### 4. Types de questions
- Commencer simple (trouver_valeur)
- Ajouter progressivement des types plus complexes
- Tester chaque type indépendamment

---

## 🔍 Débogage

### Problème : Valeurs toujours identiques

**Cause** : Seed fixe

**Solution** :
```python
import random
seed = random.randint(1, 1000000)  # Seed aléatoire
```

### Problème : Valeurs hors plage

**Cause** : difficulty_multiplier trop élevé

**Solution** :
- Réduire max_value dans random_config
- OU ajuster le multiplicateur de difficulté

### Problème : Exercices trop faciles/difficiles

**Cause** : random_config mal configuré

**Solution** :
```json
{
  "difficulty_levels": ["facile", "moyen", "difficile"],
  "random_config": {
    "min_value": 1,
    "max_value": 10  // Ajuster selon niveau
  }
}
```

---

## 📚 Exemples de Configurations

### Configuration 1 : Additions simples (CP-CE1)
```json
{
  "question_kinds": {"trouver_valeur": true},
  "random_config": {
    "min_value": 1,
    "max_value": 10,
    "operations": ["+"]
  }
}
```

### Configuration 2 : Calculs variés (CE2-CM1)
```json
{
  "question_kinds": {"trouver_valeur": true},
  "random_config": {
    "min_value": 1,
    "max_value": 50,
    "operations": ["+", "-", "*"]
  }
}
```

### Configuration 3 : Géométrie 6e
```json
{
  "question_kinds": {"trouver_valeur": true},
  "random_config": {
    "min_value": 1,
    "max_value": 20,
    "geometry": true
  }
}
```

### Configuration 4 : Vérification de propriétés
```json
{
  "question_kinds": {"verifier_propriete": true},
  "random_config": {
    "min_value": 1,
    "max_value": 30,
    "property_type": "egalite"
  }
}
```

---

## 🚀 Prochaines Évolutions

### À venir dans les prochains sprints :
- Support de templates Pythagore, Thalès
- Génération de figures SVG
- Mode hybrid (TEMPLATE + IA)
- Templates avancés avec LaTeX
- Export PDF avec mise en page

---

## 📞 Support

Pour toute question sur le générateur :
- Documentation API : `/app/backend/MATHALEA_API_GUIDE.md`
- Tests : `/app/backend/tests/test_exercise_template_generation.py`
- Code source : `/app/backend/services/exercise_template_service.py`
