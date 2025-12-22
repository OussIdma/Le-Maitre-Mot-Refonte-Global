# API Exercises - Spécification Fonctionnelle

## Vue d'ensemble

L'API Exercises permet de générer des exercices mathématiques personnalisés avec leurs corrections, figures géométriques et exports PDF.

---

## Endpoint : POST /api/v1/exercises/generate

### Description

Génère un exercice mathématique complet basé sur le niveau scolaire et le chapitre spécifié.

### URL

```
POST /api/v1/exercises/generate
```

### Headers

```
Content-Type: application/json
```

### Request Body

| Champ | Type | Requis | Description | Valeurs possibles |
|-------|------|--------|-------------|-------------------|
| `niveau` | string | ✅ | Niveau scolaire | CP, CE1, CE2, CM1, CM2, 6e, 5e, 4e, 3e, 2nde, 1ère, Terminale |
| `chapitre` | string | ✅ | Chapitre du curriculum | Voir curriculum_complete.py |
| `type_exercice` | string | ❌ | Type d'exercice | "standard" (défaut), "avancé", "simplifié" |
| `difficulte` | string | ❌ | Niveau de difficulté | "facile" (défaut), "moyen", "difficile" |

#### Exemple de requête

```json
{
  "niveau": "5e",
  "chapitre": "Symétrie axiale",
  "type_exercice": "standard",
  "difficulte": "moyen"
}
```

### Response (200 OK)

| Champ | Type | Description |
|-------|------|-------------|
| `id_exercice` | string | Identifiant unique de l'exercice généré |
| `niveau` | string | Niveau scolaire de l'exercice |
| `chapitre` | string | Chapitre du curriculum |
| `enonce_html` | string | Énoncé de l'exercice au format HTML |
| `svg` | string | Figure géométrique SVG (si applicable) |
| `solution_html` | string | Solution détaillée au format HTML |
| `pdf_token` | string | Token pour télécharger le PDF de l'exercice |
| `metadata` | object | Métadonnées supplémentaires |

#### Exemple de réponse

```json
{
  "id_exercice": "ex_5e_sym_001",
  "niveau": "5e",
  "chapitre": "Symétrie axiale",
  "enonce_html": "<p>Construire le symétrique du point A(3, 4) par rapport à l'axe vertical x=5.</p>",
  "svg": "<svg width=\"400\" height=\"300\">...</svg>",
  "solution_html": "<p><strong>Solution :</strong><br>1. Le point A est à 2 unités à gauche de l'axe...",
  "pdf_token": "ex_5e_sym_001",
  "metadata": {
    "type_exercice": "standard",
    "difficulte": "moyen",
    "duree_estimee": 5,
    "points": 2.0
  }
}
```

### Codes d'erreur

#### 422 Unprocessable Entity

Retourné lorsque les paramètres de la requête sont invalides.

**Cas 1 : Niveau invalide**

```json
{
  "detail": {
    "error": "niveau_invalide",
    "message": "Le niveau '5eme' n'est pas reconnu. Niveaux disponibles : CP, CE1, CE2, CM1, CM2, 6e, 5e, 4e, 3e, 2nde, 1ère, Terminale.",
    "niveaux_disponibles": ["CP", "CE1", "CE2", "CM1", "CM2", "6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"]
  }
}
```

**Cas 2 : Chapitre invalide**

```json
{
  "detail": {
    "error": "chapitre_invalide",
    "message": "Le chapitre 'Géométrie spatiale' n'existe pas pour le niveau '5e'. Chapitres disponibles : Symétrie axiale, Symétrie centrale, Triangles, ...",
    "niveau": "5e",
    "chapitres_disponibles": ["Symétrie axiale", "Symétrie centrale", "Triangles", "..."]
  }
}
```

#### 500 Internal Server Error

Erreur lors de la génération de l'exercice.

```json
{
  "detail": "Erreur lors de la génération de l'exercice : [message d'erreur]"
}
```

---

## Services internes utilisés

### MathGenerationService

- Génère les données mathématiques de l'exercice
- Fournit l'énoncé, les étapes de résolution et la solution

### GeometryRenderService

- Convertit les figures géométriques en SVG
- Gère les différents types de figures (triangles, symétries, etc.)

### PDFService (à venir)

- Génère un PDF de l'exercice
- Retourne un token pour le téléchargement

### CurriculumService

- Valide le niveau et le chapitre
- Utilise `curriculum_complete.py` comme source de vérité

---

## Notes techniques

- L'`id_exercice` est généré au format : `ex_{niveau}_{chapitre_slug}_{timestamp}`
- Le `pdf_token` est actuellement aligné avec l'`id_exercice` (évolution future : tokens temporaires)
- Les figures SVG sont générées uniquement pour les chapitres géométriques
- Le HTML est sanitizé avant d'être retourné

---

## Exemples d'utilisation

### Exemple 1 : Exercice de géométrie

```bash
curl -X POST http://localhost:8001/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "niveau": "5e",
    "chapitre": "Symétrie axiale",
    "difficulte": "moyen"
  }'
```

### Exemple 2 : Exercice de calcul

```bash
curl -X POST http://localhost:8001/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "niveau": "6e",
    "chapitre": "Fractions",
    "type_exercice": "standard",
    "difficulte": "facile"
  }'
```

### Exemple 3 : Niveau invalide

```bash
curl -X POST http://localhost:8001/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "niveau": "5eme",
    "chapitre": "Symétrie axiale"
  }'
```

**Réponse attendue :** HTTP 422 avec message pédagogique

---

## Évolutions futures

- [ ] Support des exercices multi-questions
- [ ] Génération de PDF asynchrone avec webhooks
- [ ] Cache des exercices générés
- [ ] Support de la langue (français/anglais)
- [ ] API de notation automatique
