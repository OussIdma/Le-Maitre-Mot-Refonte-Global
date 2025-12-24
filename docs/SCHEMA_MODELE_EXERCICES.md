# SCHÉMA VISUEL — MODÈLE EXERCICES

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE PROF                           │
│  (ExerciseGeneratorPage.js)                                 │
│                                                              │
│  Catalogue → Sélection → Générer → Exercice unique          │
│                                                              │
│  ❌ Ne voit PAS : type, source, pipeline, variables          │
│  ✅ Voit UNIQUEMENT : énoncé + solution + PDF               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              API : POST /exercises/generate                 │
│                                                              │
│  Pipeline décision :                                         │
│  ├─ DYNAMIC → Cherche is_dynamic=true                      │
│  ├─ STATIC → Cherche is_dynamic=false                      │
│  └─ AUTO → Essaie DYNAMIC, fallback STATIC                 │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                     ▼
┌───────────────────┐              ┌───────────────────┐
│  TYPE 1           │              │  TYPE 2           │
│  DYNAMIQUE        │              │  STATIQUE         │
│  (Principal)      │              │  (Fallback)       │
└───────────────────┘              └───────────────────┘
        │                                     │
        ▼                                     ▼
┌───────────────────┐              ┌───────────────────┐
│ MongoDB           │              │ MongoDB           │
│ admin_exercises   │              │ admin_exercises   │
│                   │              │                   │
│ is_dynamic=true   │              │ is_dynamic=false  │
│ generator_key     │              │ generator_key=null │
│ templates + vars  │              │ HTML figé         │
└───────────────────┘              └───────────────────┘
        │                                     │
        ▼                                     ▼
┌─────────────────────────────────────────────────────────────┐
│              INTERFACE ADMIN                                │
│  (ChapterExercisesAdminPage.js)                            │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ 🧩 Générateurs    │  │ 📄 Statiques       │            │
│  │ (is_dynamic=true)  │  │ (is_dynamic=false) │            │
│  │                    │  │                    │            │
│  │ - Templates        │  │ - HTML figé        │            │
│  │ - Variables        │  │ - Pas de template  │            │
│  │ - generator_key    │  │ - Pas de variables │            │
│  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Flux de génération (détaillé)

```
PROF demande exercice
    │
    ▼
POST /exercises/generate
    │
    ├─ Pipeline = DYNAMIC ?
    │   │
    │   ├─ Cherche exercices dynamiques DB
    │   │   (is_dynamic=true, generator_key présent)
    │   │
    │   ├─ Trouvé ?
    │   │   │
    │   │   ├─ OUI → Génère avec Factory
    │   │   │         (variables aléatoires, templates)
    │   │   │
    │   │   └─ NON → Erreur 422
    │   │
    │   └─ Retourne exercice généré
    │
    ├─ Pipeline = STATIC ?
    │   │
    │   ├─ Cherche exercices statiques DB
    │   │   (is_dynamic=false)
    │   │
    │   ├─ Trouvé ?
    │   │   │
    │   │   ├─ OUI → Retourne exercice figé
    │   │   │
    │   │   └─ NON → Erreur 422
    │   │
    │   └─ Retourne exercice statique
    │
    └─ Pipeline = AUTO (par défaut) ?
        │
        ├─ Essaie DYNAMIC
        │   │
        │   ├─ Succès → Retourne exercice dynamique
        │   │
        │   └─ Échec → Essaie STATIC
        │       │
        │       ├─ Succès → Retourne exercice statique
        │       │
        │       └─ Échec → Erreur 422
        │
        └─ Retourne exercice (dynamique ou statique)
```

## Structure des données

### Exercice DYNAMIQUE

```json
{
  "id": 1,
  "chapter_code": "6E_GM07",
  "is_dynamic": true,
  "generator_key": "THALES_V1",
  "enonce_template_html": "<p>Calculer {{variable_a}} + {{variable_b}}</p>",
  "solution_template_html": "<p>Solution : {{variable_a}} + {{variable_b}} = {{resultat}}</p>",
  "variables": {
    "variable_a": {"type": "int", "min": 1, "max": 10},
    "variable_b": {"type": "int", "min": 1, "max": 10}
  },
  "difficulty": "moyen",
  "offer": "free"
}
```

### Exercice STATIQUE

```json
{
  "id": 2,
  "chapter_code": "6E_GM07",
  "is_dynamic": false,
  "generator_key": null,
  "enonce_html": "<p>Calculer 5 + 3</p>",
  "solution_html": "<p>Solution : 5 + 3 = 8</p>",
  "difficulty": "facile",
  "offer": "free",
  "locked": false
}
```

## Règles de validation

### Règle 1 : "Sujet ≠ Corrigé"

```
❌ INTERDIT :
enonce_template_html == solution_template_html

✅ AUTORISÉ :
enonce_template_html = "<p>Calculer {{a}} + {{b}}</p>"
solution_template_html = "<p>{{a}} + {{b}} = {{resultat}}</p>"
```

### Règle 2 : Séparation stricte ADMIN

```
Onglet Générateurs :
  ✅ is_dynamic === true && generator_key
  ❌ is_dynamic === false

Onglet Statiques :
  ✅ is_dynamic === false && !isLegacySource()
  ❌ is_dynamic === true
```

### Règle 3 : Pas de legacy Python

```
❌ Chargement depuis fichiers Python (désactivé)
✅ Uniquement MongoDB admin_exercises
```

## Migration legacy → DB

```
AVANT (Legacy)
┌─────────────────────┐
│ gm07_exercises.py   │ → Handler hardcodé → Exercice
│ gm08_exercises.py   │ → Handler hardcodé → Exercice
└─────────────────────┘

APRÈS (Migration P3.2)
┌─────────────────────┐
│ MongoDB             │ → Service DB → Exercice
│ admin_exercises     │
│ source="legacy_     │
│   migration"        │
└─────────────────────┘
```

## Comparaison Avant / Après

### AVANT (Complexe)

```
4 sources :
- Dynamiques DB
- Statiques DB  
- Legacy Python
- Génération pure

3 pipelines :
- TEMPLATE
- SPEC
- MIXED

3 onglets ADMIN :
- Dynamiques (mélange)
- Statiques (mélange)
- Catalogue (unifié)
```

### APRÈS (Simple)

```
2 types :
- Dynamique (principal)
- Statique (fallback)

2 pipelines :
- DYNAMIC
- STATIC
(+ AUTO = DYNAMIC → STATIC)

2 onglets ADMIN :
- Générateurs (dynamiques uniquement)
- Statiques (statiques uniquement)
```

## Métriques de simplification

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Sources d'exercices | 4 | 2 | -50% |
| Pipelines | 3 | 2 (+ auto) | -33% |
| Onglets ADMIN | 3 | 2 | -33% |
| Fallbacks possibles | 5+ | 1 | -80% |
| Complexité cognitive | Élevée | Faible | ✅ |

