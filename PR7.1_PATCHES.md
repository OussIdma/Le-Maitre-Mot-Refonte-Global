# PATCHES MINIMAUX PR7.1

## PATCH 1: `/api/mathalea/sheets/{sheet_id}/generate-pdf` - Ajouter assert_can_export_pdf

**Fichier**: `backend/routes/mathalea_routes.py`

**Ligne**: 994 (fonction `generate_sheet_pdf`)

**Changement**:
```python
@router.post("/sheets/{sheet_id}/generate-pdf")
async def generate_sheet_pdf(
    sheet_id: str,
    request: Request,  # AJOUTER
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")  # AJOUTER
):
    """
    Générer les 3 PDFs pour une feuille d'exercices
    
    Sprint D & E - Pipeline PDF complet avec IA optionnelle:
    1. Récupère la feuille et génère le preview
    2. Si IA activée: enrichit les énoncés/corrections
    3. Génère 3 PDFs: sujet, élève, corrigé
    4. Retourne les PDFs en base64
    
    PR7.1: Export PDF nécessite un compte (Free ou Pro)
    
    Returns:
        Dict avec 3 clés contenant les PDFs en base64:
        - subject_pdf: PDF sujet (pour professeur)
        - student_pdf: PDF élève (pour distribution)
        - correction_pdf: PDF corrigé (avec solutions)
    """
    from backend.services.access_control import assert_can_export_pdf  # AJOUTER
    from backend.server import validate_session_token  # AJOUTER
    
    # PR7.1: Vérifier l'authentification  # AJOUTER
    user_email = None  # AJOUTER
    if x_session_token:  # AJOUTER
        user_email = await validate_session_token(x_session_token)  # AJOUTER
    assert_can_export_pdf(user_email)  # AJOUTER
    
    from engine.pdf_engine.mathalea_sheet_pdf_builder import (
        build_sheet_subject_pdf,
        build_sheet_student_pdf,
        build_sheet_correction_pdf
    )
    # ... reste du code inchangé ...
```

---

## PATCH 2: `/api/export/advanced` - Utiliser assert_can_export_pdf + harmoniser format

**Fichier**: `backend/server.py`

**Ligne**: 5709 (fonction `export_pdf_advanced`)

**Changement**:
```python
@api_router.post("/export/advanced")
async def export_pdf_advanced(request: EnhancedExportRequest, http_request: Request):
    """Export document as PDF with advanced layout options (Pro only)"""
    try:
        # PR7.1: Check authentication using centralized access control
        from backend.services.access_control import assert_can_export_pdf
        
        session_token = http_request.headers.get("X-Session-Token")
        user_email = None
        
        if session_token:
            user_email = await validate_session_token(session_token)
        
        # PR7.1: Valider qu'un compte est requis (retourne 401 avec code AUTH_REQUIRED_EXPORT)
        assert_can_export_pdf(user_email)
        
        # Vérifier que l'utilisateur est Pro
        is_pro, user = await check_user_pro_status(user_email)
        if not is_pro:
            raise HTTPException(status_code=403, detail="Fonctionnalité Pro uniquement")
        
        logger.info(f"Advanced PDF export requested by Pro user: {user_email}")
        
        # ... reste du code inchangé ...
```

**Résultat**: Format d'erreur 401 harmonisé avec les autres endpoints.

---

## PATCH 3: `ProExportModal.js` - Ajouter checkBeforeExport (optionnel mais recommandé)

**Fichier**: `frontend/src/components/ProExportModal.js`

**Ligne**: 142 (fonction `callGenerateProPdf`)

**Changement**:
```javascript
import { useExportPdfGate } from "../lib/exportPdfUtils";  // AJOUTER

const ProExportModal = ({
  isOpen,
  onClose,
  sheetId,
  sessionToken,
  // ... autres props
}) => {
  // PR7.1: Utiliser le hook de gating pour les exports PDF
  const { canExport, checkBeforeExport, handleExportError } = useExportPdfGate();  // AJOUTER
  
  const callGenerateProPdf = async () => {
    if (!sheetId) {
      throw new Error("SheetId manquant pour l'export Pro.");
    }
    
    // PR7.1: Vérifier si l'utilisateur peut exporter (compte requis)
    if (!checkBeforeExport(() => callGenerateProPdf())) {  // AJOUTER
      // Modal "Créer un compte" ouverte, ne pas appeler l'API
      return;  // AJOUTER
    }
    
    // ... reste du code inchangé ...
  };
  
  const handleExportSubject = async () => {
    setExportError("");
    setIsExportingSubject(true);
    try {
      const data = await callGenerateProPdf();
      // ... reste du code inchangé ...
    } catch (err) {
      console.error("Erreur export Sujet Pro :", err);
      
      // PR7.1: Gérer les erreurs d'authentification  // AJOUTER
      if (handleExportError(err, { type: 'export_pdf' })) {  // AJOUTER
        // Erreur gérée (modal ouverte), ne pas afficher d'autre message  // AJOUTER
        setIsExportingSubject(false);  // AJOUTER
        return;  // AJOUTER
      }  // AJOUTER
      
      setExportError(
        err?.message ||
          "Une erreur est survenue lors de l'export du Sujet Pro."
      );
    } finally {
      setIsExportingSubject(false);
    }
  };
  
  // Même chose pour handleExportCorrection
  // ...
};
```

**Note**: Ce patch est optionnel car `ProExportModal` est probablement utilisé uniquement pour les Pro, mais il garantit la cohérence avec les autres composants.

---

## PATCH 4: Test backend pour `/api/mathalea/sheets/{sheet_id}/generate-pdf`

**Fichier**: `backend/tests/test_export_access_control.py`

**Ajout**:
```python
def test_generate_pdf_no_token_returns_401(self, client, mock_sheet_id):
    """Test: POST /api/mathalea/sheets/{sheet_id}/generate-pdf sans token => 401 AUTH_REQUIRED_EXPORT"""
    response = client.post(
        f"/api/mathalea/sheets/{mock_sheet_id}/generate-pdf"
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "AUTH_REQUIRED_EXPORT"
    assert data["detail"]["error"] == "AUTH_REQUIRED_EXPORT"
```

---

## ORDRE D'APPLICATION

1. **PATCH 1** (backend) - Critique P0
2. **PATCH 2** (backend) - Critique P0
3. **PATCH 4** (tests) - Validation
4. **PATCH 3** (frontend) - Optionnel mais recommandé

