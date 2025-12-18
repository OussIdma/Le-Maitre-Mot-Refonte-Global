# 🔍 INVESTIGATION ROOT CAUSE - Admin Preview JSON Invalide

## Symptôme
**Frontend crash** : `Unexpected token 'I', "Internal S"... is not valid JSON`

L'erreur se produit dans le modal de prévisualisation dynamique admin lorsque le backend renvoie une réponse non-JSON (probablement HTML/text).

---

## 📍 FICHIERS ET LIGNES IDENTIFIÉS

### 1. **FRONTEND - Point d'appel**

**Fichier** : `frontend/src/lib/adminApi.js`
- **Ligne 34** : Import de `previewDynamicExercise`
- **Ligne 109-115** : Fonction `previewDynamicExercise()` qui appelle `/api/admin/exercises/preview-dynamic`
- **Ligne 39-42** : **PROBLÈME CRITIQUE** - `await response.json()` sans vérification du Content-Type
  ```javascript
  const response = await fetch(`${BACKEND_URL}${endpoint}`, fetchOptions);
  clearTimeout(timeoutId);
  
  const data = await response.json(); // ❌ CRASH ICI si réponse n'est pas JSON
  ```

**Fichier** : `frontend/src/components/admin/DynamicPreviewModal.js`
- **Ligne 34** : Import de `previewDynamicExercise`
- **Ligne 58-65** : Appel à `previewDynamicExercise()` avec gestion d'erreur basique
- **Ligne 67-71** : Vérification `result.success` mais pas de gestion si `response.json()` échoue

---

### 2. **BACKEND - Endpoint Handler**

**Fichier** : `backend/routes/generators_routes.py`
- **Ligne 104-105** : Définition de l'endpoint `@router.post("/preview-dynamic")`
- **Ligne 113-115** : **PROBLÈME** - Appel à `get_generator_schema()` HORS du try/except
  ```python
  schema = get_generator_schema(request.generator_key.upper())
  if not schema:
      raise HTTPException(status_code=400, detail={...})
  ```
  Si `get_generator_schema()` lève une exception non-HTTPException, elle n'est pas catchée.

- **Ligne 117-148** : Bloc `try` qui catch les exceptions dans la génération
- **Ligne 150-152** : Handler d'exception qui catch `Exception` mais seulement pour le bloc try
  ```python
  except Exception as e:
      logger.error(f"❌ Preview error: {str(e)}")
      raise HTTPException(status_code=500, detail={"error": "preview_failed", "message": str(e)})
  ```

**Fichier** : `backend/routes/generators_routes.py`
- **Ligne 83-92** : Fonction `get_generator_schema_endpoint()` qui utilise `get_generator_schema()`
- **Ligne 85** : Appel à `get_generator_schema()` - peut lever des exceptions

---

### 3. **BACKEND - Fonction Helper**

**Fichier** : `backend/routes/generators_routes.py`
- **Ligne 113** : Appel à `get_generator_schema()` - **FONCTION NON DÉFINIE LOCALEMENT**
- **Ligne 21** : Import `get_generator_schema as factory_get_schema` depuis `backend.generators.factory`
- **Ligne 28** : Import `get_generator_schema as legacy_get_schema` depuis `backend.generators.generator_registry`
- **PROBLÈME** : `get_generator_schema()` est appelée mais n'existe pas - probablement une fonction helper manquante qui devrait combiner `factory_get_schema` et `legacy_get_schema`
- Cette fonction est appelée ligne 113 SANS try/except → **NameError possible** si la fonction n'existe pas

---

### 4. **BACKEND - Gestion globale des exceptions**

**Fichier** : `backend/server.py`
- **Ligne 1-100** : Aucun `@app.exception_handler` trouvé
- **Ligne 4776-4778** : Inclusion du router `generators_router` dans l'app
- **Résultat** : FastAPI utilise son handler par défaut qui peut renvoyer du HTML pour les erreurs 500 non catchées

---

## 🔗 CHAÎNE D'EXCEPTIONS IDENTIFIÉE

### Scénario 1 : Exception avant le try/except
1. **Ligne 113** : `get_generator_schema()` est appelé
2. Si cette fonction lève une exception non-HTTPException (ex: `AttributeError`, `KeyError`, `ImportError`)
3. L'exception n'est **PAS catchée** (hors du try/except)
4. FastAPI handler par défaut intercepte → renvoie HTML/text "Internal Server Error"
5. Frontend ligne 42 : `response.json()` crash avec "Unexpected token 'I'..."

### Scénario 2 : Exception dans le try/except mais sérialisation échoue
1. **Ligne 118-122** : `generate_dynamic_exercise()` lève une exception
2. **Ligne 150-152** : Exception catchée, `HTTPException` levée avec `detail={"error": ..., "message": str(e)}`
3. Si `str(e)` contient des caractères non-JSON ou si FastAPI a un problème de sérialisation
4. FastAPI peut renvoyer du HTML par défaut au lieu de JSON
5. Frontend ligne 42 : `response.json()` crash

### Scénario 3 : Exception lors de la création de DynamicPreviewResponse
1. **Ligne 140-148** : Création de `DynamicPreviewResponse(...)`
2. Si un champ contient une valeur non-sérialisable (ex: objet complexe)
3. Pydantic/FastAPI peut lever une exception non catchée
4. FastAPI handler par défaut → HTML/text
5. Frontend ligne 42 : `response.json()` crash

---

## 📊 FORMAT DE RÉPONSE ATTENDU vs RÉEL

### Attendu (JSON)
```json
{
  "error": "preview_failed",
  "message": "..."
}
```
**Content-Type** : `application/json`

### Réel (en cas d'erreur non catchée)
```
Internal Server Error
```
**Content-Type** : `text/html` ou `text/plain`

---

## 🎯 ROOT CAUSE PRÉCIS

**Problème principal** : 
- Le frontend fait `response.json()` **sans vérifier** le Content-Type ou le statut HTTP
- Le backend peut renvoyer du HTML/text si une exception n'est pas catchée ou si la sérialisation JSON échoue
- Pas de handler global d'exceptions dans FastAPI pour garantir du JSON

**Lignes fautives** :
1. `frontend/src/lib/adminApi.js:42` - `await response.json()` sans vérification
2. `backend/routes/generators_routes.py:113` - Appel à `get_generator_schema()` hors try/except
3. `backend/server.py` - Pas de handler global d'exceptions

---

## 📝 EXEMPLE DE RÉPONSE PROBLÉMATIQUE

**Headers** :
```
HTTP/1.1 500 Internal Server Error
Content-Type: text/html; charset=utf-8
```

**Body** :
```html
<!DOCTYPE html>
<html>
<head>
    <title>Internal Server Error</title>
</head>
<body>
    <h1>Internal Server Error</h1>
    <p>...</p>
</body>
</html>
```

Le frontend essaie de parser ça comme JSON → crash.

---

## ✅ CORRECTIFS APPLIQUÉS

### 1. **Backend - Handler global FastAPI** ✅
**Fichier** : `backend/server.py`
- **Lignes 400-470** : Ajout de `@app.exception_handler(Exception)` pour garantir JSON même en 500
- **Lignes 472-490** : Ajout de `@app.exception_handler(RequestValidationError)` pour validation errors
- **Résultat** : Toute exception non catchée renvoie du JSON structuré avec `error_code: "INTERNAL_SERVER_ERROR"`

### 2. **Backend - Wrapper complet preview_dynamic** ✅
**Fichier** : `backend/routes/generators_routes.py`
- **Lignes 40-52** : Ajout de la fonction helper `get_generator_schema()` qui combine Factory et Legacy
- **Lignes 104-200** : Wrapper COMPLET de `preview_dynamic_exercise()` dans try/except
  - `get_generator_schema()` maintenant dans le try
  - Utilisation de `JSONResponse` explicite pour toutes les erreurs
  - Format structuré : `{error_code, error, message, success, ...}`
- **Lignes 82-110** : `get_generator_schema_endpoint()` également wrappé dans try/except

### 3. **Frontend - Parsing défensif** ✅
**Fichier** : `frontend/src/lib/adminApi.js`
- **Lignes 37-65** : Parsing défensif ajouté
  - Vérification `Content-Type` avant `JSON.parse()`
  - Lecture `response.text()` si non-JSON
  - Construction d'erreur structurée `{error_code, message, details}`
  - Plus jamais de crash sur `response.json()`

### 4. **Tests de validation**
- ✅ Cas nominal preview OK → affiche preview
- ✅ Cas exception backend forcée → frontend affiche message lisible, pas de crash
- ✅ GM07/GM08 non impactés (pas de modification des routes legacy)

---

## 📝 FORMAT DE RÉPONSE APRÈS CORRECTIF

### Backend - Erreur 500 (exception non catchée)
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "error": "internal_server_error",
  "message": "Une erreur interne s'est produite",
  "details": "..."
}
```
**Content-Type** : `application/json` ✅

### Backend - Erreur preview
```json
{
  "error_code": "preview_failed",
  "error": "preview_failed",
  "message": "Erreur interne lors de la prévisualisation",
  "success": false,
  "enonce_html": "",
  "solution_html": "",
  "variables_used": {},
  "svg_enonce": null,
  "svg_solution": null,
  "errors": ["..."]
}
```
**Content-Type** : `application/json` ✅

### Frontend - Réponse non-JSON (fallback)
```javascript
{
  success: false,
  error: "Réponse non-JSON du serveur (Content-Type: text/html): Internal Server Error...",
  error_details: {
    error_code: "non_json_response",
    message: "...",
    details: "..."
  }
}
```
**Résultat** : Pas de crash, message lisible affiché ✅

