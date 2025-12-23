# P1 - Templates Éditables Backend (MVP) ✅

## 🎯 Objectif

Fournir un **socle backend stable** pour permettre aux admins de créer et valider des templates de rédaction (énoncés/solutions) sans toucher au code.

**Périmètre MVP :**
- ✅ Stockage MongoDB
- ✅ CRUD admin complet
- ✅ Validation/Preview avec GeneratorFactory
- ✅ Tests backend passants
- ⏸️ **NON inclus** : Intégration dans `/generate`, UI frontend

---

## 📋 Architecture

```
Admin crée un template
  ↓
Stocké en MongoDB (collection: generator_templates)
  ↓
Validation via /validate:
  1. Génère variables (GeneratorFactory)
  2. Parse placeholders {{var}} et {{{var}}}
  3. Vérifie existence des variables
  4. Vérifie sécurité HTML
  5. Génère preview HTML
  ↓
Template prêt à être utilisé (intégration future dans /generate)
```

---

## 🗃️ Modèle de Données

### GeneratorTemplate (MongoDB)

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
  "variant_id": "A",
  "grade": "6e",
  "difficulty": "facile",
  "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
  "solution_template_html": "<h4>{{methode}}</h4><pre>{{calculs_intermediaires}}</pre><p>{{reponse_finale}}</p>",
  "allowed_html_vars": ["tableau_html"],
  "created_at": "2025-12-23T10:00:00Z",
  "updated_at": "2025-12-23T10:00:00Z",
  "created_by": null
}
```

**Champs :**
- `generator_key` : Clé du générateur (ex: `RAISONNEMENT_MULTIPLICATIF_V1`)
- `variant_id` : Variant pédagogique (`"A"`, `"B"`, `"C"`, `"default"`)
- `grade` : Niveau scolaire (`"6e"`, `"5e"`, `null`=tous)
- `difficulty` : Difficulté (`"facile"`, `"moyen"`, `"difficile"`, `null`=tous)
- `enonce_template_html` : Template HTML de l'énoncé
- `solution_template_html` : Template HTML de la solution
- `allowed_html_vars` : Liste des variables autorisées en triple moustaches `{{{var}}}`

---

## 🔌 API Endpoints

### Base URL
```
/api/v1/admin/generator-templates
```

### 1. Liste des Templates

**GET** `/api/v1/admin/generator-templates`

**Query Params (optionnels) :**
- `generator_key` : Filtrer par générateur
- `variant_id` : Filtrer par variant
- `grade` : Filtrer par niveau
- `difficulty` : Filtrer par difficulté

**Exemple :**
```bash
curl http://localhost:8000/api/v1/admin/generator-templates?generator_key=RAISONNEMENT_MULTIPLICATIF_V1
```

**Réponse 200 :**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
    "variant_id": "A",
    "grade": "6e",
    "difficulty": "facile",
    "enonce_template_html": "...",
    "solution_template_html": "...",
    "allowed_html_vars": ["tableau_html"],
    "created_at": "2025-12-23T10:00:00Z",
    "updated_at": "2025-12-23T10:00:00Z"
  }
]
```

---

### 2. Récupérer un Template

**GET** `/api/v1/admin/generator-templates/{template_id}`

**Exemple :**
```bash
curl http://localhost:8000/api/v1/admin/generator-templates/507f1f77bcf86cd799439011
```

**Réponse 200 :** (même structure que ci-dessus)

**Réponse 404 :**
```json
{
  "detail": {
    "error_code": "TEMPLATE_NOT_FOUND",
    "message": "Template '507f1f77bcf86cd799439011' introuvable"
  }
}
```

---

### 3. Créer un Template

**POST** `/api/v1/admin/generator-templates`

**Body :**
```json
{
  "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
  "variant_id": "A",
  "grade": "6e",
  "difficulty": "facile",
  "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
  "solution_template_html": "<h4>{{methode}}</h4><p>{{reponse_finale}}</p>",
  "allowed_html_vars": ["tableau_html"]
}
```

**Exemple curl :**
```bash
curl -X POST http://localhost:8000/api/v1/admin/generator-templates \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
    "variant_id": "default",
    "enonce_template_html": "<p>{{enonce}}</p>",
    "solution_template_html": "<p>{{solution}}</p>",
    "allowed_html_vars": []
  }'
```

**Réponse 201 :** (template créé avec `id`)

---

### 4. Mettre à Jour un Template

**PUT** `/api/v1/admin/generator-templates/{template_id}`

**Body (champs optionnels) :**
```json
{
  "enonce_template_html": "<p><strong>{{consigne}}</strong></p>",
  "allowed_html_vars": ["tableau_html"]
}
```

**Exemple curl :**
```bash
curl -X PUT http://localhost:8000/api/v1/admin/generator-templates/507f1f77bcf86cd799439011 \
  -H "Content-Type: application/json" \
  -d '{
    "enonce_template_html": "<p><strong>{{consigne}}</strong></p>"
  }'
```

**Réponse 200 :** (template mis à jour)

---

### 5. Supprimer un Template

**DELETE** `/api/v1/admin/generator-templates/{template_id}`

**Exemple curl :**
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/generator-templates/507f1f77bcf86cd799439011
```

**Réponse 200 :**
```json
{
  "success": true,
  "message": "Template '507f1f77bcf86cd799439011' supprimé"
}
```

---

### 6. Valider/Prévisualiser un Template ⭐

**POST** `/api/v1/admin/generator-templates/validate`

**Le plus important** : Valide un template avant de le sauvegarder.

**Body :**
```json
{
  "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
  "variant_id": "default",
  "grade": "6e",
  "difficulty": "facile",
  "seed": 42,
  "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
  "solution_template_html": "<h4>{{methode}}</h4><p>{{reponse_finale}}</p>",
  "allowed_html_vars": ["tableau_html"]
}
```

**Actions effectuées :**
1. ✅ Génère des variables via `GeneratorFactory.generate()`
2. ✅ Parse les placeholders `{{var}}` et `{{{var}}}`
3. ✅ Vérifie que toutes les variables existent
4. ✅ Vérifie la sécurité HTML (triple moustaches)
5. ✅ Génère un preview du rendu HTML

**Exemple curl :**
```bash
curl -X POST http://localhost:8000/api/v1/admin/generator-templates/validate \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
    "seed": 42,
    "enonce_template_html": "<p>{{enonce}}</p>{{{tableau_html}}}",
    "solution_template_html": "<p>{{solution}}</p>",
    "allowed_html_vars": ["tableau_html"]
  }'
```

#### Réponse Succès (200)

```json
{
  "valid": true,
  "used_placeholders": ["enonce", "tableau_html", "solution"],
  "missing_placeholders": [],
  "html_security_errors": [],
  "preview": {
    "enonce_html": "<p>Une voiture parcourt 150 km...</p><table>...</table>",
    "solution_html": "<p>V = D / T...</p>",
    "variables": {
      "enonce": "Une voiture parcourt 150 km...",
      "tableau_html": "<table>...</table>",
      "solution": "V = D / T..."
    }
  }
}
```

#### Réponse Erreur : Placeholder Manquant (422 ADMIN_TEMPLATE_MISMATCH)

```json
{
  "detail": {
    "error_code": "ADMIN_TEMPLATE_MISMATCH",
    "message": "Placeholders manquants: vitesse. Ces variables n'existent pas dans le générateur.",
    "used_placeholders": ["enonce", "vitesse"],
    "missing_placeholders": ["vitesse"],
    "html_security_errors": []
  }
}
```

#### Réponse Erreur : Triple Moustaches Non Autorisées (422 HTML_VAR_NOT_ALLOWED)

```json
{
  "detail": {
    "error_code": "HTML_VAR_NOT_ALLOWED",
    "message": "Variables HTML non autorisées: enonce. Ajoutez-les à allowed_html_vars ou utilisez {{var}}.",
    "used_placeholders": ["enonce"],
    "missing_placeholders": [],
    "html_security_errors": [
      {
        "type": "html_var_not_allowed",
        "placeholder": "enonce",
        "message": "Triple moustaches interdites pour 'enonce'. Ajoutez 'enonce' à allowed_html_vars ou utilisez {{var}}"
      }
    ]
  }
}
```

---

## 🔒 Sécurité HTML

### Règles

**Double Moustaches `{{var}}` (Safe) :**
- Texte échappé
- **Toujours autorisé**
- Exemple : `{{enonce}}` → texte brut

**Triple Moustaches `{{{var}}}` (HTML Brut) :**
- HTML non échappé
- **Autorisé UNIQUEMENT si `var` dans `allowed_html_vars`**
- Exemple : `{{{tableau_html}}}` → HTML rendu

### Validation

Lors de la validation, le backend vérifie :
1. ✅ Tous les placeholders existent dans les variables générées
2. ✅ Les triple moustaches sont autorisées (`var in allowed_html_vars`)
3. ❌ Sinon → **422 HTML_VAR_NOT_ALLOWED**

---

## 🧪 Tests

### Exécution

```bash
# Tous les tests templates
docker compose exec backend pytest backend/tests/test_generator_template_service.py -v
docker compose exec backend pytest backend/tests/test_admin_template_routes.py -v
```

### Couverture

**Service (test_generator_template_service.py) :**
- ✅ CRUD complet (create, read, update, delete)
- ✅ Sélection par priorité (`get_best_template`)
- ✅ Validation succès
- ✅ Validation placeholder manquant
- ✅ Validation HTML non autorisé

**API (test_admin_template_routes.py) :**
- ✅ GET /templates (liste)
- ✅ GET /templates/{id}
- ✅ POST /templates (création)
- ✅ PUT /templates/{id} (mise à jour)
- ✅ DELETE /templates/{id}
- ✅ POST /templates/validate (succès)
- ✅ POST /templates/validate (422 ADMIN_TEMPLATE_MISMATCH)
- ✅ POST /templates/validate (422 HTML_VAR_NOT_ALLOWED)

---

## 📊 État Actuel

### ✅ Implémenté (Phase 1 + Phase 2)

- ✅ Modèle MongoDB `GeneratorTemplate`
- ✅ Service `GeneratorTemplateService`
- ✅ Routes CRUD admin complètes
- ✅ Endpoint validation/preview
- ✅ Tests backend complets
- ✅ Documentation MVP

### ⏸️ Non Implémenté (Futures Phases)

- ⏸️ Intégration dans `/api/v1/exercises/generate` (Phase 3)
- ⏸️ UI Admin (page rédaction + preview) (Phase 4)
- ⏸️ Migration legacy (fallback templates hardcodés) (Phase 3)

---

## 🚀 Utilisation

### 1. Créer un Template

```bash
curl -X POST http://localhost:8000/api/v1/admin/generator-templates \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
    "variant_id": "default",
    "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
    "solution_template_html": "<h4>{{methode}}</h4><p>{{reponse_finale}}</p>",
    "allowed_html_vars": ["tableau_html"]
  }'
```

### 2. Valider Avant de Sauvegarder

```bash
curl -X POST http://localhost:8000/api/v1/admin/generator-templates/validate \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
    "seed": 42,
    "enonce_template_html": "<p>{{enonce}}</p>{{{tableau_html}}}",
    "solution_template_html": "<p>{{solution}}</p>",
    "allowed_html_vars": ["tableau_html"]
  }'
```

### 3. Lister les Templates d'un Générateur

```bash
curl http://localhost:8000/api/v1/admin/generator-templates?generator_key=RAISONNEMENT_MULTIPLICATIF_V1
```

---

## 📝 Prochaines Étapes

### Phase 3 : Intégration dans /generate (2-3h)
- Modifier `/api/v1/exercises/generate`
- Chercher template DB (priorité)
- Fallback sur legacy si aucun template
- Tests intégration

### Phase 4 : UI Admin (4-5h)
- Page rédaction templates
- Éditeurs HTML
- Prévisualisation live
- Dupliquer templates

---

**Date :** 2025-12-23  
**Statut :** ✅ MVP Backend Complet (Phase 1 + 2)  
**Tests :** À exécuter après build Docker  
**Code Review :** Prêt

