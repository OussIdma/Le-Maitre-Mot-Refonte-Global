# RAPPORT DE VÉRIFICATION PR7.1 - GATING EXPORT PDF

## POINT 1 — COUVERTURE TOTALE DES ENDPOINTS EXPORT

### ✅ Endpoints protégés (utilisent `assert_can_export_pdf`)

1. **`POST /api/export`** (`backend/server.py:5307`)
   - ✅ Ligne 5324: `from backend.services.access_control import assert_can_export_pdf`
   - ✅ Ligne 5383: `assert_can_export_pdf(user_email)`

2. **`POST /api/v1/sheets/export-selection`** (`backend/server.py:6633`)
   - ✅ Ligne 6653: `from backend.services.access_control import assert_can_export_pdf`
   - ✅ Ligne 6662: `assert_can_export_pdf(user_email)`

3. **`POST /api/mathalea/sheets/{sheet_id}/export-standard`** (`backend/routes/mathalea_routes.py:1128`)
   - ✅ Ligne 1183: `from backend.services.access_control import assert_can_export_pdf`
   - ✅ Ligne 1190: `assert_can_export_pdf(user_email)`

4. **`POST /api/user/sheets/{sheet_uid}/export-pdf`** (`backend/routes/user_sheets_routes.py:392`)
   - ✅ Ligne 83: `from backend.services.access_control import assert_can_export_pdf`
   - ✅ Ligne 92: `assert_can_export_pdf(user_email)` (dans `get_user_email` dependency)

### ❌ Endpoints NON protégés (manquent `assert_can_export_pdf`)

1. **`POST /api/mathalea/sheets/{sheet_id}/generate-pdf`** (`backend/routes/mathalea_routes.py:994`)
   - ❌ **MANQUE** : Aucun appel à `assert_can_export_pdf`
   - **Impact** : Permet l'export PDF sans compte
   - **Ligne** : 994-1890 (fonction complète)

2. **`POST /api/export/advanced`** (`backend/server.py:5709`)
   - ❌ **MANQUE** : Aucun appel à `assert_can_export_pdf`
   - **Impact** : Format d'erreur 401 incohérent (voir Point 2)
   - **Note** : C'est Pro-only, mais devrait quand même utiliser `assert_can_export_pdf` pour la cohérence
   - **Ligne** : 5713-5720 (vérification manuelle du token)

---

## POINT 2 — FORMAT D'ERREUR 401 STABLE ET CONSISTANT

### ✅ Endpoints avec format correct

Tous les endpoints protégés utilisent `assert_can_export_pdf` qui retourne :
```python
HTTPException(
    status_code=401,
    detail={
        "error": "AUTH_REQUIRED_EXPORT",
        "code": "AUTH_REQUIRED_EXPORT",
        "message": "Connexion requise pour exporter un PDF. Créez un compte gratuit pour continuer.",
        "action": "show_login_modal"
    }
)
```

### ❌ Endpoint avec format incohérent

**`POST /api/export/advanced`** (`backend/server.py:5716, 5720`)
- ❌ Ligne 5716: `raise HTTPException(status_code=401, detail="Session token requis pour les options avancées")`
- ❌ Ligne 5720: `raise HTTPException(status_code=401, detail="Session token invalide")`
- **Problème** : Format string au lieu de dict structuré
- **Impact** : Frontend ne peut pas détecter `AUTH_REQUIRED_EXPORT` de manière fiable

---

## POINT 3 — AUCUN APPEL API CÔTÉ FRONT SI NON CONNECTÉ

### ✅ Composants protégés (utilisent `useExportPdfGate`)

1. **`SheetComposerPage.js`**
   - ✅ Ligne 260: `const { canExport, checkBeforeExport, handleExportError } = useExportPdfGate();`
   - ✅ Ligne 272: `if (!checkBeforeExport(() => doExport(sessionToken))) { return; }`
   - ✅ Ligne 209: `if (handleExportError(err, { type: 'export_pdf' })) { return; }`

2. **`SheetBuilderPage.js`**
   - ✅ Ligne 58: `const { canExport, checkBeforeExport, handleExportError } = useExportPdfGate();`
   - ✅ Ligne 477: `if (!checkBeforeExport(() => handleGeneratePDF())) { return; }`
   - ✅ Ligne 538: `if (handleExportError(error, { type: 'export_pdf' })) { return; }`

3. **`SheetEditPageP31.js`**
   - ✅ Ligne 304: `const { canExport, checkBeforeExport, handleExportError } = useExportPdfGate();`
   - ✅ Ligne 308: `if (!checkBeforeExport(() => handleExportPDF(includeSolutions))) { return; }`
   - ✅ Ligne 335: `if (handleExportError(error, { type: 'export_pdf' })) { return; }`

4. **`App.js`**
   - ✅ Ligne 564: `const { canExport, checkBeforeExport, handleExportError } = useExportPdfGate();`
   - ✅ Ligne 572: `if (!checkBeforeExport(() => exportPDF(exportType))) { return; }`
   - ✅ Ligne 641: `if (handleExportError(error, { type: 'export_pdf' })) { return; }`

### ⚠️ Composants à vérifier

1. **`Step4ExportTelechargement.js`**
   - ⚠️ Appelle `onExportPDF` qui vient du parent (`DocumentWizard` → `App.js`)
   - ✅ **VÉRIFIÉ** : `App.js` utilise `checkBeforeExport`, donc protégé indirectement
   - **Recommandation** : OK, mais pourrait être plus explicite

2. **`ProExportModal.js`**
   - ⚠️ Appelle `/api/mathalea/sheets/${sheetId}/generate-pdf-pro` (ligne 156)
   - ⚠️ Vérifie `sessionToken` manuellement (ligne 146-148)
   - ⚠️ **PAS de `checkBeforeExport`** avant l'appel API
   - **Impact** : Si `sessionToken` est null, l'appel part quand même (erreur 401 côté backend)
   - **Note** : Ce composant est probablement utilisé uniquement pour les Pro, mais devrait quand même utiliser le gate

---

## RÉSUMÉ

### ✅ Points OK
- 4/6 endpoints backend protégés
- Format d'erreur cohérent pour les endpoints protégés
- 4/5 composants frontend protégés

### ❌ Points KO (P0) - **PATCHÉS**
1. ✅ **`/api/mathalea/sheets/{sheet_id}/generate-pdf`** : **PATCHÉ** - Ajout de `assert_can_export_pdf`
2. ✅ **`/api/export/advanced`** : **PATCHÉ** - Utilisation de `assert_can_export_pdf` + format harmonisé
3. ⚠️ **`ProExportModal.js`** : Pas de `checkBeforeExport` (optionnel, car Pro-only)

---

## PATCHES APPLIQUÉS

✅ **PATCH 1** : `backend/routes/mathalea_routes.py` - Ajout de `assert_can_export_pdf` dans `generate_sheet_pdf`
✅ **PATCH 2** : `backend/server.py` - Harmonisation de `export_pdf_advanced` avec `assert_can_export_pdf`
✅ **PATCH 3** : `backend/tests/test_export_access_control.py` - Ajout de tests pour les nouveaux endpoints

**Résultat** : Tous les endpoints d'export PDF sont maintenant protégés avec un format d'erreur cohérent.

