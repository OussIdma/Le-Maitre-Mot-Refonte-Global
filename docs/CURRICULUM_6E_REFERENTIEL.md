# 📚 Référentiel Curriculum 6e - Documentation

> **Version** : 1.0  
> **Date** : Décembre 2024  
> **Fichiers** : 
> - `docs/CURRICULUM_OFFICIEL.csv`
> - `backend/curriculum/curriculum_6e.json`
> - `backend/curriculum/loader.py`

---

## 📋 Vue d'ensemble

Le référentiel curriculum 6e permet d'appeler l'API de génération d'exercices
par **code officiel** au lieu du couple niveau/chapitre.

### Avantages

1. **Standardisation** : Codes uniques et stables (ex: `6e_N08`)
2. **Référentiel pédagogique** : Aligné sur le programme officiel de mathématiques
3. **Flexibilité** : Mapping vers différents générateurs
4. **Évolutivité** : Support futur des contextes (DBZ, foot, etc.)

---

## 📂 Structure des fichiers

```
/app/
├── docs/
│   ├── CURRICULUM_OFFICIEL.csv      # Programme officiel (source)
│   └── CURRICULUM_6E_REFERENTIEL.md # Cette documentation
│
└── backend/
    └── curriculum/
        ├── __init__.py              # Exports du module
        ├── curriculum_6e.json       # Référentiel JSON avec mapping
        └── loader.py                # Chargeur et index
```

---

## 📊 Structure du JSON

### Fichier `curriculum_6e.json`

```json
{
  "version": 1,
  "niveau": "6e",
  "description": "Référentiel pédagogique officiel 6e",
  "chapitres": [
    {
      "niveau": "6e",
      "code_officiel": "6e_N08",
      "domaine": "Nombres et calculs",
      "libelle": "Fractions comme partage et quotient",
      "chapitre_backend": "Fractions",
      "exercise_types": ["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"],
      "schema_requis": true,
      "difficulte_min": 1,
      "difficulte_max": 3,
      "statut": "prod",
      "tags": ["fractions", "partage", "quotient"],
      "contexts": []
    }
  ]
}
```

### Champs

| Champ | Type | Description |
|-------|------|-------------|
| `niveau` | string | Niveau scolaire (ex: "6e") |
| `code_officiel` | string | Code unique (ex: "6e_N08") |
| `domaine` | string | Domaine mathématique |
| `libelle` | string | Intitulé officiel du chapitre |
| `chapitre_backend` | string | Nom du chapitre dans le backend |
| `exercise_types` | string[] | Liste des MathExerciseType |
| `schema_requis` | bool | Si un schéma/figure est nécessaire |
| `difficulte_min` | int | Difficulté minimum (1-3) |
| `difficulte_max` | int | Difficulté maximum (1-3) |
| `statut` | string | "prod", "beta", ou "hidden" |
| `tags` | string[] | Tags pour la recherche |
| `contexts` | string[] | Contextes disponibles (futur) |

---

## 🔌 Utilisation de l'API

### Mode code_officiel (nouveau)

```http
POST /api/v1/exercises/generate
Content-Type: application/json

{
  "code_officiel": "6e_N08",
  "difficulte": "moyen"
}
```

**Réponse :**
```json
{
  "niveau": "6e",
  "chapitre": "Fractions",
  "enonce_html": "...",
  "metadata": {
    "generator_code": "6e_FRACTION_REPRESENTATION",
    "is_fallback": false
  }
}
```

### Mode legacy (inchangé)

```http
POST /api/v1/exercises/generate
Content-Type: application/json

{
  "niveau": "6e",
  "chapitre": "Fractions",
  "difficulte": "moyen"
}
```

---

## 📋 Codes officiels disponibles

### Nombres et calculs (10 chapitres)

| Code | Libellé | Générateurs |
|------|---------|-------------|
| `6e_N01` | Lire et écrire les nombres entiers | NOMBRES_LECTURE, CALCUL_DECIMAUX |
| `6e_N02` | Comparer et ranger des nombres entiers | NOMBRES_COMPARAISON, CALCUL_DECIMAUX |
| `6e_N03` | Droite numérique et repérage | DROITE_GRADUEE_ENTIERS, DROITE_GRADUEE_DECIMAUX |
| `6e_N04` | Addition et soustraction de nombres entiers | CALCUL_POSE_DEDIE, CALCUL_DECIMAUX, CALCUL_MENTAL_DEDIE |
| `6e_N05` | Multiplication de nombres entiers | CALCUL_POSE_DEDIE, CALCUL_DECIMAUX, PRIORITES_OPERATIONS |
| `6e_N06` | Division euclidienne | CALCUL_DECIMAUX, CRITERES_DIVISIBILITE |
| `6e_N07` | Multiples et diviseurs, critères de divisibilité | CRITERES_DIVISIBILITE, MULTIPLES |
| `6e_N08` | Fractions comme partage et quotient | CALCUL_FRACTIONS, FRACTION_REPRESENTATION |
| `6e_N09` | Fractions simples de l'unité | CALCUL_FRACTIONS, FRACTIONS_EGALES, FRACTION_COMPARAISON |
| `6e_N10` | Problèmes à étapes avec les quatre opérations | PROBLEME_2_ETAPES, PROBLEME_1_ETAPE |

### Géométrie (7 chapitres)

| Code | Libellé | Générateurs |
|------|---------|-------------|
| `6e_G01` | Points, segments, droites, demi-droites | TRIANGLE_QUELCONQUE, RECTANGLE |
| `6e_G02` | Alignement, milieu d'un segment | TRIANGLE_QUELCONQUE, RECTANGLE |
| `6e_G03` | Perpendiculaires et parallèles | TRIANGLE_QUELCONQUE, RECTANGLE, QUADRILATERES |
| `6e_G04` | Triangles (construction et classification) | TRIANGLE_QUELCONQUE, TRIANGLE_CONSTRUCTION, AIRE_TRIANGLE |
| `6e_G05` | Quadrilatères usuels | RECTANGLE, QUADRILATERES, PERIMETRE_AIRE |
| `6e_G06` | Cercle et disque | CERCLE, PERIMETRE_AIRE |
| `6e_G07` | Symétrie axiale | SYMETRIE_AXIALE, SYMETRIE_PROPRIETES |

### Grandeurs et mesures (6 chapitres)

| Code | Libellé | Générateurs |
|------|---------|-------------|
| `6e_GM01` | Mesurer et comparer des longueurs | GRANDEURS_MESURES_DEDIE, CONVERSIONS_UNITES |
| `6e_GM02` | Périmètre de figures usuelles | PERIMETRE_AIRE, RECTANGLE, CERCLE |
| `6e_GM03` | Aire du rectangle et du carré | PERIMETRE_AIRE, RECTANGLE, AIRE_FIGURES_COMPOSEES |
| `6e_GM04` | Aire du triangle rectangle | AIRE_TRIANGLE, PERIMETRE_AIRE |
| `6e_GM05` | Durées et lecture de l'heure | GRANDEURS_MESURES_DEDIE, CONVERSIONS_UNITES |
| `6e_GM06` | Masses, contenances et conversions | GRANDEURS_MESURES_DEDIE, CONVERSIONS_UNITES |

### Organisation et gestion de données (4 chapitres)

| Code | Libellé | Générateurs |
|------|---------|-------------|
| `6e_SP01` | Lire et compléter des tableaux | TABLEAU_LECTURE, TABLEAU_COMPLETER |
| `6e_SP02` | Diagrammes en barres et pictogrammes | DIAGRAMME_BARRES, STATISTIQUES |
| `6e_SP03` | Proportionnalité simple dans des tableaux | PROPORTIONNALITE, PROP_TABLEAU, PROP_ACHAT |
| `6e_SP04` | Moyenne arithmétique simple | STATISTIQUES |

---

## 🔧 Utilisation du loader Python

```python
from curriculum.loader import (
    get_chapter_by_official_code,
    get_chapters_by_backend_name,
    get_all_official_codes,
    validate_curriculum
)

# Récupérer un chapitre par code
chapter = get_chapter_by_official_code("6e_N08")
print(chapter.libelle)  # "Fractions comme partage et quotient"
print(chapter.exercise_types)  # ["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"]

# Récupérer tous les chapitres d'un chapitre backend
chapters = get_chapters_by_backend_name("Fractions")
for ch in chapters:
    print(f"{ch.code_officiel}: {ch.libelle}")

# Liste de tous les codes
codes = get_all_official_codes()

# Rapport de validation
report = validate_curriculum()
print(report["total_chapters"])  # 27
```

---

## ➕ Ajouter un nouveau chapitre

### 1. Ajouter au CSV (optionnel)

```csv
6e;Nouveau domaine;6e_XX01;Mon nouveau chapitre
```

### 2. Ajouter au JSON

```json
{
  "niveau": "6e",
  "code_officiel": "6e_XX01",
  "domaine": "Nouveau domaine",
  "libelle": "Mon nouveau chapitre",
  "chapitre_backend": "Chapitre existant",
  "exercise_types": ["TYPE1", "TYPE2"],
  "schema_requis": false,
  "difficulte_min": 1,
  "difficulte_max": 3,
  "statut": "beta",
  "tags": ["tag1", "tag2"],
  "contexts": []
}
```

### 3. Valider

```bash
cd /app/backend
python3 -c "from curriculum.loader import validate_curriculum; print(validate_curriculum())"
```

---

## 🔮 Évolutions futures

### Contextes thématiques

Les `contexts` permettront de générer des exercices avec des thèmes :

```json
{
  "code_officiel": "6e_N08",
  "contexts": ["DBZ", "foot", "cuisine"]
}
```

### Page admin

Une interface d'administration permettra de :
- Modifier le mapping code → générateurs
- Activer/désactiver des chapitres
- Ajouter des contextes

### Support multi-niveaux

Le système est conçu pour supporter 5e, 4e, 3e :
- `backend/curriculum/curriculum_5e.json`
- `backend/curriculum/curriculum_4e.json`
- etc.

---

*Documentation créée le 11 décembre 2024*
