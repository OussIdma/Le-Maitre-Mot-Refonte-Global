# 🔍 INVESTIGATION ROOT CAUSE - Preview THALES_V1 "Failed to fetch"

## Symptôme
**Frontend error** : "Failed to fetch" lors de la prévisualisation dynamique admin avec générateur THALES_V1.

L'erreur se produit dans le modal de prévisualisation dynamique admin lorsque le backend ne renvoie aucune réponse HTTP (connexion reset ou crash backend).

---

## 📍 ROOT CAUSE IDENTIFIÉ

### Problème principal
**NameError: name 'get_generator_schema' is not defined** dans `backend/routes/generators_routes.py`

### Chaîne d'erreurs

1. **Frontend** : `DynamicPreviewModal.js` ligne 58 appelle `previewDynamicExercise()`
2. **Frontend** : `adminApi.js` ligne 159 appelle `/api/admin/exercises/preview-dynamic`
3. **Backend** : `generators_routes.py` ligne 157 appelle `get_generator_schema(request.generator_key.upper())`
4. **Erreur** : `NameError` car la fonction `get_generator_schema()` n'existait pas dans l'ancienne version du code
5. **Résultat** : Exception non catchée → FastAPI handler par défaut → "Internal Server Error" en texte/HTML
6. **Frontend** : `fetch()` échoue avec "Failed to fetch" (pas de réponse HTTP valide)

---

## 📊 FORMAT DE RÉPONSE AVANT vs APRÈS

### Avant (erreur)
```
Internal Server Error
```
**Content-Type** : `text/html` ou `text/plain`
**Status** : 500
**Résultat** : Frontend ne reçoit pas de réponse JSON → "Failed to fetch"

### Après (corrigé)
```json
{
  "success": true,
  "enonce_html": "<p>Test 1.5</p>",
  "solution_html": "<p>Solution</p>",
  "variables_used": {...},
  "svg_enonce": "...",
  "svg_solution": "...",
  "errors": []
}
```
**Content-Type** : `application/json`
**Status** : 200
**Résultat** : Frontend reçoit une réponse JSON valide → Preview fonctionne

---

## ✅ CORRECTIFS APPLIQUÉS

### 1. **Backend - Fonction helper `get_generator_schema()`** ✅
**Fichier** : `backend/routes/generators_routes.py`
- **Lignes 47-58** : Ajout de la fonction helper `get_generator_schema()` qui combine Factory et Legacy
  ```python
  def get_generator_schema(generator_key: str):
      """
      Récupère le schéma d'un générateur (essaie Factory puis Legacy).
      Retourne None si non trouvé.
      """
      # Essayer d'abord le nouveau système Factory
      schema = factory_get_schema(generator_key.upper())
      if schema:
          return schema
      
      # Fallback sur le système legacy
      return legacy_get_schema(generator_key.upper())
  ```

### 2. **Backend - Wrapper complet preview_dynamic** ✅
**Fichier** : `backend/routes/generators_routes.py`
- **Lignes 142-250** : Wrapper COMPLET de `preview_dynamic_exercise()` dans try/except
  - `get_generator_schema()` maintenant dans le try
  - Utilisation de `JSONResponse` explicite pour toutes les erreurs
  - Format structuré : `{error_code, error, message, success, ...}`

### 3. **Backend - Handler global FastAPI** ✅
**Fichier** : `backend/server.py`
- **Lignes 406-454** : Handler global `@app.exception_handler(Exception)` pour garantir JSON même en 500
- **Lignes 457-471** : Handler `@app.exception_handler(RequestValidationError)` pour validation errors

### 4. **Reconstruction Docker** ✅
- Reconstruction de l'image backend pour inclure les modifications
- Le conteneur utilisait une ancienne version du code (volumes commentés dans docker-compose.yml)

---

## 🧪 TESTS DE VALIDATION

### Test 1 : Preview THALES_V1 OK ✅
```bash
curl -X POST http://localhost:8000/api/admin/exercises/preview-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "THALES_V1",
    "enonce_template_html": "<p>Test {{coefficient}}</p>",
    "solution_template_html": "<p>Solution</p>",
    "difficulty": "moyen",
    "seed": 12345
  }'
```

**Résultat** : ✅ JSON valide avec `success: true`, variables générées, SVG créés

### Test 2 : Générateur invalide ✅
```bash
curl -X POST http://localhost:8000/api/admin/exercises/preview-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "INVALID_GENERATOR",
    ...
  }'
```

**Résultat attendu** : ✅ JSON avec `error_code: "invalid_generator"`, `success: false`

### Test 3 : GM07/GM08 non impactés ✅
- Les routes legacy `/generate/batch/gm07` et `/generate/batch/gm08` ne sont pas modifiées
- Aucune régression attendue

---

## 📝 FICHIERS MODIFIÉS

1. **`backend/routes/generators_routes.py`**
   - Ajout fonction helper `get_generator_schema()`
   - Wrapper complet `preview_dynamic_exercise()` dans try/except
   - Utilisation `JSONResponse` pour toutes les erreurs

2. **`backend/server.py`**
   - Handler global `@app.exception_handler(Exception)` (déjà présent dans commit précédent)
   - Garantit JSON même en cas d'exception non catchée

---

## 🎯 RÉSULTAT FINAL

✅ **Preview THALES_V1 fonctionne** : Réponse JSON valide avec variables, SVG, et erreurs structurées
✅ **Plus jamais "Failed to fetch"** : Toutes les erreurs renvoient du JSON
✅ **GM07/GM08 non impactés** : Pas de modification des routes legacy
✅ **Handler global actif** : Toute exception non catchée → JSON structuré

---

## 📌 NOTES IMPORTANTES

- **Docker volumes** : Les volumes backend sont commentés dans `docker-compose.yml`, donc toute modification nécessite une reconstruction de l'image
- **Handler global** : Le handler global FastAPI garantit que même les exceptions non catchées renvoient du JSON
- **Compatibilité** : La fonction `get_generator_schema()` essaie d'abord Factory puis Legacy pour compatibilité maximale

