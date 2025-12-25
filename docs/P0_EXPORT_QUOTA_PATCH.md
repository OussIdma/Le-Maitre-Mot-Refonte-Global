# P0 - Patch Protection Quota Export Standard

## Objectif
Empêcher tout export illimité gratuit via `/api/mathalea/sheets/{id}/export-standard`

---

## Fichiers modifiés

### 1. `backend/routes/mathalea_routes.py`

**Changements**:
- ✅ Ajout imports: `Request`, `timedelta`, `base64`
- ✅ Modification signature `export_standard_pdf()`:
  - Ajout paramètres: `request: Request`, `x_session_token`, `x_guest_id`, `guest_id` (query)
- ✅ Logique de guards:
  1. Si `X-Session-Token` présent → valider session → vérifier Pro
  2. Si Pro → OK, pas de quota
  3. Sinon → exiger `guest_id` (header `X-Guest-ID` OU query `?guest_id=`)
  4. Si `guest_id` absent → HTTP 400
  5. Vérifier quota guest (3 exports / 30 jours)
  6. Si quota dépassé → HTTP 402
  7. Si OK → enregistrer dans `db.exports`
- ✅ Garde "Sujet ≠ Corrigé" inchangé (2 PDFs séparés)

**Diff principal**:

```python
@router.post("/sheets/{sheet_id}/export-standard")
async def export_standard_pdf(
    sheet_id: str,
    request: Request,
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    x_guest_id: Optional[str] = Header(None, alias="X-Guest-ID"),
    guest_id: Optional[str] = Query(None, description="Guest ID (alternative to header)")
):
    # ... imports ...
    from backend.server import validate_session_token, check_user_pro_status, check_guest_quota
    
    # P0: Vérification auth et quota
    is_pro_user = False
    user_email = None
    guest_id_final = None
    
    # 1. Si X-Session-Token présent, vérifier Pro
    if x_session_token:
        try:
            user_email = await validate_session_token(x_session_token)
            if user_email:
                is_pro_user, _ = await check_user_pro_status(user_email)
                # ...
        except Exception as e:
            # Continue comme guest si session invalide
    
    # 2. Si pas Pro, exiger guest_id
    if not is_pro_user:
        guest_id_final = x_guest_id or guest_id
        if not guest_id_final:
            raise HTTPException(status_code=400, detail={...})
        
        # 3. Vérifier le quota guest
        quota_status = await check_guest_quota(guest_id_final)
        if quota_status["quota_exceeded"]:
            raise HTTPException(status_code=402, detail={...})
    
    # ... génération PDF ...
    
    # 5. P0: Enregistrer l'export dans db.exports (si guest)
    if not is_pro_user and guest_id_final:
        export_doc = {
            "guest_id": guest_id_final,
            "sheet_id": sheet_id,
            "type": "sheet_export",
            "created_at": datetime.now(timezone.utc)
        }
        await db.exports.insert_one(export_doc)
    
    # ... retour response ...
```

---

## Fichiers créés

### 2. `backend/tests/test_export_standard_quota.py`

**Tests unitaires**:
- ✅ `test_export_pro_user_no_quota`: Pro user n'a pas de quota
- ✅ `test_export_guest_no_guest_id_400`: Guest sans guest_id retourne 400
- ✅ `test_export_guest_with_quota_ok`: Guest avec quota OK peut exporter
- ✅ `test_export_guest_quota_exceeded_402`: Guest avec quota dépassé retourne 402
- ✅ `test_export_guest_id_query_param`: guest_id peut être passé en query param
- ✅ `test_export_invalid_session_token_treated_as_guest`: Session invalide traité comme guest
- ✅ `test_export_non_pro_user_requires_guest_id`: Utilisateur non-Pro nécessite guest_id

---

## Cas limites couverts

### 1. Session token invalide
- **Comportement**: Traité comme guest, nécessite `guest_id`
- **Test**: `test_export_invalid_session_token_treated_as_guest`

### 2. Utilisateur connecté mais non-Pro
- **Comportement**: Nécessite `guest_id` et vérifie quota
- **Test**: `test_export_non_pro_user_requires_guest_id`

### 3. Guest sans guest_id
- **Comportement**: HTTP 400 avec message explicite
- **Test**: `test_export_guest_no_guest_id_400`

### 4. Quota dépassé
- **Comportement**: HTTP 402 avec détails (exports_used, exports_remaining, action)
- **Test**: `test_export_guest_quota_exceeded_402`

### 5. guest_id en header vs query
- **Comportement**: Les deux sont acceptés (header prioritaire)
- **Test**: `test_export_guest_id_query_param`

### 6. Pro user
- **Comportement**: Pas de quota, pas d'enregistrement dans db.exports
- **Test**: `test_export_pro_user_no_quota`

---

## Structure db.exports

Document inséré pour chaque export guest:
```json
{
  "guest_id": "guest_123",
  "sheet_id": "sheet_456",
  "type": "sheet_export",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Index recommandé** (à créer manuellement si nécessaire):
```javascript
db.exports.createIndex({ "guest_id": 1, "created_at": 1 })
```

---

## Checklist de tests manuels

### Test 1: Export Pro (pas de quota)
1. ✅ Se connecter avec un compte Pro
2. ✅ Créer une fiche dans SheetBuilderPage
3. ✅ Exporter PDF (avec `X-Session-Token`)
4. ✅ **VÉRIFIER**: Export réussit (200)
5. ✅ **VÉRIFIER**: Aucun document dans `db.exports` pour cet export
6. ✅ **VÉRIFIER**: Les 2 PDFs (élève + corrigé) sont générés

### Test 2: Export Guest (quota OK)
1. ✅ Être déconnecté (ou utiliser un guest_id)
2. ✅ Créer une fiche
3. ✅ Exporter PDF avec `X-Guest-ID: test_guest_123`
4. ✅ **VÉRIFIER**: Export réussit (200)
5. ✅ **VÉRIFIER**: Document créé dans `db.exports`:
   ```javascript
   db.exports.findOne({guest_id: "test_guest_123", type: "sheet_export"})
   ```
6. ✅ **VÉRIFIER**: Les 2 PDFs sont générés

### Test 3: Export Guest (quota dépassé)
1. ✅ Créer 3 exports avec le même `guest_id` dans les 30 derniers jours
2. ✅ Tenter un 4ème export avec le même `guest_id`
3. ✅ **VÉRIFIER**: HTTP 402 avec message:
   ```json
   {
     "error": "quota_exceeded",
     "action": "upgrade_required",
     "message": "Limite de 3 exports gratuits atteinte...",
     "exports_used": 3,
     "exports_remaining": 0,
     "max_exports": 3
   }
   ```

### Test 4: Export Guest sans guest_id
1. ✅ Être déconnecté
2. ✅ Tenter export sans `X-Guest-ID` ni `?guest_id=`
3. ✅ **VÉRIFIER**: HTTP 400 avec message:
   ```json
   {
     "error": "guest_id_required",
     "message": "Guest ID requis pour les utilisateurs non-Pro...",
     "hint": "Les utilisateurs Pro peuvent utiliser X-Session-Token..."
   }
   ```

### Test 5: Export avec guest_id en query param
1. ✅ Être déconnecté
2. ✅ Exporter avec `?guest_id=test_guest_query`
3. ✅ **VÉRIFIER**: Export réussit (200)
4. ✅ **VÉRIFIER**: Document créé dans `db.exports`

### Test 6: Session token invalide
1. ✅ Envoyer `X-Session-Token: invalid_token` + `X-Guest-ID: test_guest`
2. ✅ **VÉRIFIER**: Export réussit comme guest (200)
3. ✅ **VÉRIFIER**: Document créé dans `db.exports` avec `guest_id`

### Test 7: Utilisateur connecté mais non-Pro
1. ✅ Se connecter avec un compte non-Pro
2. ✅ Tenter export avec `X-Session-Token` mais sans `guest_id`
3. ✅ **VÉRIFIER**: HTTP 400 (guest_id requis)
4. ✅ Ajouter `X-Guest-ID: test_guest`
5. ✅ **VÉRIFIER**: Export réussit comme guest (200)

### Test 8: Séparation Sujet/Corrigé préservée
1. ✅ Exporter (Pro ou Guest)
2. ✅ **VÉRIFIER**: Response contient `student_pdf` et `correction_pdf` séparés
3. ✅ **VÉRIFIER**: Les 2 PDFs sont différents (un avec énoncé, un avec corrigé)

---

## Résumé

### Protection implémentée
- ✅ Pro users: Pas de quota (illimité)
- ✅ Guest users: Quota 3 exports / 30 jours
- ✅ Validation: Session token → Pro status
- ✅ Fallback: Session invalide → traité comme guest
- ✅ Enregistrement: Chaque export guest enregistré dans `db.exports`

### Séparation Sujet/Corrigé
- ✅ **Préservée**: Les 2 PDFs restent séparés (`student_pdf` et `correction_pdf`)
- ✅ Aucun changement dans la génération PDF

### Tests
- ✅ 7 tests unitaires créés
- ✅ 8 tests manuels définis
- ✅ Cas limites couverts



