# 📚 RÈGLES PÉDAGOGIQUES UNIVERSELLES - Le Maître Mot

Ce document décrit les règles pédagogiques fondamentales qui s'appliquent à **TOUTES** les matières et **TOUS** les chapitres du projet Le Maître Mot.

---

## 🎯 Règle Fondamentale

### SUJET = Données connues uniquement

Le SUJET contient uniquement ce que l'élève reçoit pour résoudre l'exercice.
- ❌ Jamais la réponse
- ❌ Jamais un indice visuel qui révèle la réponse
- ✅ Uniquement les données de départ

### CORRIGÉ = Données connues + Réponses + Raisonnement

Le CORRIGÉ contient tout ce qu'un professeur montrerait sur un corrigé officiel.
- ✅ Les données de départ
- ✅ La réponse complète
- ✅ Le raisonnement / la construction
- ✅ Les justifications

---

## 📋 Classification Universelle des Types d'Exercices

Chaque exercice doit être classé dans l'une de ces 4 catégories :

### 1️⃣ `trouver_valeur`

**Description** : L'élève doit trouver quelque chose.

**Exemples** :
- Mathématiques : "Trouve le point M' symétrique de M"
- Mathématiques : "Calcule la longueur BC"
- Français : "Trouve le mot qui convient"
- Physique : "Calcule la vitesse"

**Règle** :
- **SUJET** : Ne contient JAMAIS l'objet à trouver
- **CORRIGÉ** : Montre l'objet trouvé + construction + justification

**Exemples concrets** :

```
Exercice : "Trouve le point E symétrique de D par rapport à l'axe x = 5"

SUJET :
  - Point D visible
  - Axe x = 5 visible
  - Grille visible
  - Point E ABSENT ❌
  - Segment DE ABSENT ❌
  - Point milieu ABSENT ❌

CORRIGÉ :
  - Point D visible
  - Axe x = 5 visible
  - Grille visible
  - Point E visible ✅
  - Segment DE visible ✅
  - Point milieu visible ✅
```

---

### 2️⃣ `verifier_propriete`

**Description** : L'élève doit vérifier si une propriété est vraie.

**Exemples** :
- Mathématiques : "Les points A et B sont-ils symétriques ?"
- Mathématiques : "Les droites (AB) et (CD) sont-elles parallèles ?"
- Français : "Le mot 'mangé' est-il correctement orthographié ?"

**Règle** :
- **SUJET** : Montre TOUS les objets nécessaires (ils doivent être visibles pour que l'élève puisse vérifier)
- **CORRIGÉ** : Explication + éventuellement constructions intermédiaires

**Exemples concrets** :

```
Exercice : "Vérifie si les points D et E sont symétriques par rapport à x = 5"

SUJET :
  - Point D visible ✅
  - Point E visible ✅
  - Axe x = 5 visible ✅
  - Grille visible ✅

CORRIGÉ :
  - Point D visible ✅
  - Point E visible ✅
  - Axe x = 5 visible ✅
  - Grille visible ✅
  - + Constructions intermédiaires (perpendiculaires, distances)
  - + Explication détaillée
```

---

### 3️⃣ `completer_structure`

**Description** : L'élève doit compléter une figure, un texte, un tableau, une équation.

**Exemples** :
- Mathématiques : "Complète le triangle par symétrie"
- Français : "Complète la phrase avec le bon mot"
- Histoire : "Complète le tableau chronologique"

**Règle** :
- **SUJET** : Montre uniquement la partie donnée
- **CORRIGÉ** : Montre la partie donnée + la complétion + raisonnement

**Exemples concrets** :

```
Exercice : "Complète le triangle ABC par symétrie axiale"

SUJET :
  - Triangle ABC visible ✅
  - Axe de symétrie visible ✅
  - Grille visible ✅
  - Triangle A'B'C' ABSENT ❌

CORRIGÉ :
  - Triangle ABC visible ✅
  - Axe de symétrie visible ✅
  - Grille visible ✅
  - Triangle A'B'C' visible ✅
  - Segments de construction visibles ✅
```

---

### 4️⃣ `probleme_redige`

**Description** : Texte contextualisé + plusieurs questions.

**Exemples** :
- Problème de géométrie avec plusieurs étapes
- Problème de physique avec contexte
- Texte avec questions de compréhension

**Règle** :
- **SUJET** : Texte + questions
- **CORRIGÉ** : Solutions détaillées étape par étape

---

## 🎨 Règles pour les Schémas (SVG)

### Génération de 2 SVG distincts

Pour chaque exercice contenant un schéma, le backend **DOIT** générer **2 SVG** :

1. **`figure_svg_question`** : Affiché dans l'onglet SUJET
2. **`figure_svg_correction`** : Affiché dans l'onglet CORRIGÉ

Et optionnellement :
3. **`figure_svg`** : Fallback pour compatibilité avec anciens exercices

### Règles par type d'exercice

| Type d'exercice | SUJET | CORRIGÉ |
|-----------------|-------|---------|
| `trouver_valeur` | Objet initial seulement | Objet initial + objet à trouver + constructions |
| `verifier_propriete` | Tous les éléments nécessaires | + constructions / annotations |
| `completer_structure` | Figure initiale | Figure initiale + figure complétée |
| `probleme_redige` | SVG minimal | SVG annoté si nécessaire |

---

## 📐 Règles Spécifiques par Matière

### Mathématiques

#### Transformations géométriques (symétrie, rotation, translation, homothétie)

**Type `trouver_valeur`** :
```
SUJET montre seulement :
  - Point initial
  - Axe/centre/vecteur
  - Grille

CORRIGÉ montre :
  - Point initial + point transformé
  - Segment de construction
  - Point milieu
  - etc.
```

**Type `verifier_propriete`** :
```
SUJET montre tout (A, B, axe)
CORRIGÉ ajoute construction / justification
```

**Type `completer_structure`** :
```
SUJET : Triangle initial
CORRIGÉ : Triangle initial + triangle image
```

#### Pythagore, Thalès, géométrie plane

```
SUJET : N'affiche JAMAIS la longueur recherchée
CORRIGÉ : Affiche la longueur + les étapes de calcul
```

### Français

```
SUJET : Texte + trous / QCM sans réponse
CORRIGÉ : Texte complété / bonne réponse visible
```

### Histoire, Géographie

```
SUJET : Carte / texte / tableau sans réponses
CORRIGÉ : Annotations et réponses complètes
```

### Anglais

```
SUJET : Phrases à compléter
CORRIGÉ : Réponses complètes
```

---

## 🔧 Implémentation Technique

### Module Central : `pedagogie_rules.py`

Ce module contient la logique pédagogique universelle.

**Fonction principale** :
```python
from pedagogie_rules import determine_elements_to_hide_in_question

hiding_rules = determine_elements_to_hide_in_question(
    exercise_type="trouver_valeur",
    metadata={
        "points": ["M", "M'"],
        "properties": [],
        "is_geometry": True
    }
)

# Retourne :
# {
#     "elements_to_hide": ["M'"],
#     "hide_constructions": True,
#     "hide_annotations": True,
#     "exercise_type_detected": "trouver_valeur"
# }
```

### Backend : Services de génération

Chaque service de génération d'exercices doit :

1. **Définir le type d'exercice** :
```python
exercise_dict = {
    "exercise_type": "trouver_valeur",  # ⚠️ OBLIGATOIRE
    "enonce": "...",
    "spec_mathematique": {
        ...
    }
}
```

2. **Appeler la règle pédagogique** :
```python
from pedagogie_rules import determine_elements_to_hide_in_question

hiding_rules = determine_elements_to_hide_in_question(
    exercise_type=exercise_dict["exercise_type"],
    metadata={...}
)
```

3. **Générer 2 SVG** :
```python
svg_question = generate_svg(data, hide=hiding_rules["elements_to_hide"])
svg_correction = generate_svg(data, hide=[])

exercise_dict["figure_svg_question"] = svg_question
exercise_dict["figure_svg_correction"] = svg_correction
```

### Frontend : Affichage

Le frontend **DOIT** utiliser les bons champs :

**Onglet SUJET** :
```javascript
{exercise.figure_svg_question && (
  <div dangerouslySetInnerHTML={{ __html: exercise.figure_svg_question }} />
)}
```

**Onglet CORRIGÉ** :
```javascript
{exercise.figure_svg_correction && (
  <div dangerouslySetInnerHTML={{ __html: exercise.figure_svg_correction }} />
)}
```

**Fallback pour compatibilité** :
```javascript
{!exercise.figure_svg_question && exercise.figure_svg && (
  <div dangerouslySetInnerHTML={{ __html: exercise.figure_svg }} />
)}
```

---

## 🧪 Tests Automatiques

### Test Principal : `test_regle_pedagogique_universelle.py`

Ce test vérifie que :
- ✅ Pour chaque type : Le sujet ne montre jamais de réponse
- ✅ Pour chaque type : Le corrigé montre toujours la réponse
- ✅ Tous les SVG respectent la logique
- ✅ Les champs obligatoires existent
- ✅ Aucun chapitre ne brise la règle SUJET/CORRIGÉ

**Exécution** :
```bash
cd /app/backend && python tests/test_regle_pedagogique_universelle.py
```

**Résultat attendu** :
```
✅ TEST 1 RÉUSSI : Type trouver_valeur
✅ TEST 2 RÉUSSI : Type completer_structure
✅ TEST 3 RÉUSSI : Type verifier_propriete
✅ TEST 4 RÉUSSI : Pas de régression
```

---

## 📦 Créer un Nouveau Chapitre Conforme

### Checklist pour un nouveau chapitre

#### 1. Définir le type d'exercice

```python
# Dans le générateur
exercise_type = "trouver_valeur"  # ou "verifier_propriete", etc.
```

#### 2. Construire les métadonnées

```python
metadata = {
    "points": ["A", "B", "C"],  # Points de l'exercice
    "properties": ["triangle", "symetrie"],  # Propriétés
    "is_geometry": True,  # Si c'est un exercice de géométrie
    "shapes": ["triangle_ABC", "triangle_A'B'C'"]  # Formes
}
```

#### 3. Appeler la règle pédagogique

```python
from pedagogie_rules import determine_elements_to_hide_in_question

hiding_rules = determine_elements_to_hide_in_question(
    exercise_type=exercise_type,
    metadata=metadata
)
```

#### 4. Générer les 2 SVG

```python
# SVG pour le sujet (avec éléments cachés)
svg_question = render_svg(
    data,
    hide_elements=hiding_rules["elements_to_hide"],
    hide_constructions=hiding_rules["hide_constructions"]
)

# SVG pour le corrigé (complet)
svg_correction = render_svg(
    data,
    hide_elements=[],
    hide_constructions=False
)
```

#### 5. Retourner l'exercice

```python
return {
    "exercise_type": exercise_type,
    "enonce": "...",
    "figure_svg_question": svg_question,
    "figure_svg_correction": svg_correction,
    "spec_mathematique": {...}
}
```

---

## ✅ Tester la Conformité

### Test rapide d'un chapitre

```python
# 1. Générer un exercice
exercise = generate_exercise(...)

# 2. Vérifier les champs obligatoires
assert "exercise_type" in exercise
assert "figure_svg_question" in exercise
assert "figure_svg_correction" in exercise

# 3. Vérifier que les SVG sont différents
assert exercise["figure_svg_question"] != exercise["figure_svg_correction"]

# 4. Vérifier que le sujet ne contient pas la réponse
svg_q = exercise["figure_svg_question"]
assert "point-a-trouver" not in svg_q  # Adapter selon le contexte
```

### Test complet avec le test automatique

```bash
cd /app/backend
python tests/test_regle_pedagogique_universelle.py
```

---

## 📌 Résumé des Principes

1. **Règle fondamentale** : SUJET = données | CORRIGÉ = données + réponse
2. **4 types d'exercices** : trouver_valeur, verifier_propriete, completer_structure, probleme_redige
3. **2 SVG obligatoires** : figure_svg_question, figure_svg_correction
4. **Logique centralisée** : Module `pedagogie_rules.py`
5. **Tests automatiques** : Validation continue de la conformité

---

## 🚀 Contributions

Lors de l'ajout d'un nouveau chapitre ou d'une nouvelle matière :
1. Suivre cette documentation
2. Utiliser le module `pedagogie_rules.py`
3. Générer les 2 SVG
4. Exécuter les tests automatiques
5. Mettre à jour cette documentation si nécessaire

---

**Version** : 1.0  
**Dernière mise à jour** : Décembre 2024  
**Auteur** : Équipe Le Maître Mot
