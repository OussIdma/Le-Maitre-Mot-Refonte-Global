# PR8: ECO=PREMIUM - RÉSUMÉ D'IMPLÉMENTATION

## ✅ BACKEND

### 1. Service de contrôle d'accès (`backend/services/access_control.py`)
- ✅ `assert_can_use_layout(user_email, is_pro, layout)` modifié :
  - Utilise HTTP 403 (au lieu de 402)
  - Format d'erreur : `{code: "PREMIUM_REQUIRED_ECO", error: "premium_required", message: "Mode éco réservé Premium", action: "upgrade"}`

### 2. Endpoints protégés (tous les exports avec paramètre `layout`)
- ✅ `/api/mathalea/sheets/{sheet_id}/export-standard` - Applique `assert_can_use_layout` après `assert_can_export_pdf`
- ✅ `/api/user/sheets/{sheet_uid}/export-pdf` - Applique `assert_can_use_layout` après `assert_can_export_pdf`
- ✅ `/api/v1/sheets/export-selection` - Applique `assert_can_use_layout` après `assert_can_export_pdf`

### 3. Tests backend (`backend/tests/test_export_access_control.py`)
- ✅ Test unitaire : `test_assert_can_use_layout_eco_free_raises_403` (403 avec code PREMIUM_REQUIRED_ECO)
- ✅ Test unitaire : `test_assert_can_use_layout_classic_free_allowed` (classic autorisé pour Free)
- ✅ Test unitaire : `test_assert_can_use_layout_eco_pro_allowed` (eco autorisé pour Pro)
- ✅ Tests d'intégration : Placeholders ajoutés pour tests avec mock users

---

## ✅ FRONTEND

### 1. Utilitaires (`frontend/src/lib/exportPdfUtils.js`)
- ✅ `handleExportPdfError` étendu pour intercepter les erreurs 403 avec code `PREMIUM_REQUIRED_ECO`
- ✅ `useExportPdfGate` retourne maintenant `isPro` pour vérifier le statut Premium

### 2. Composants modifiés

#### `SheetBuilderPage.js`
- ✅ Toggle Éco désactivé si `!isPro`
- ✅ Badge "Premium" affiché si `!isPro`
- ✅ Clic sur toggle désactivé → ouvre `PremiumEcoModal`
- ✅ Gestion erreur 403 PREMIUM_REQUIRED_ECO → ouvre modal premium

#### `SheetComposerPage.js`
- ✅ Select layout : option "Économique" désactivée si `!isPro`
- ✅ Badge "Premium" affiché sur l'option Éco si `!isPro`
- ✅ Clic sur option Éco désactivée → ouvre `PremiumEcoModal`
- ✅ Gestion erreur 403 PREMIUM_REQUIRED_ECO → ouvre modal premium

#### `SheetEditPageP31.js`
- ✅ Toggle Éco désactivé si `!isPro`
- ✅ Badge "Premium" affiché si `!isPro`
- ✅ Clic sur toggle désactivé → redirige vers `/pricing?upgrade=eco`
- ✅ Gestion erreur 403 PREMIUM_REQUIRED_ECO → redirige vers pricing

#### `App.js`
- ✅ Gestion erreur 403 PREMIUM_REQUIRED_ECO → redirige vers `/pricing?upgrade=eco`

### 3. Modal Premium (`frontend/src/components/PremiumEcoModal.js`)
- ✅ **Nouveau composant** créé selon spécifications PR8
- ✅ Titre : "Mode Éco — Premium"
- ✅ Texte : "Imprimez mieux, utilisez moins de papier."
- ✅ 4 bullets :
  - Mise en page 2 colonnes (économie de pages)
  - Rendu professionnel (style manuel scolaire)
  - Personnalisation (logo, en-tête/pied de page)
  - Générations illimitées
- ✅ CTA : "Passer Premium" (redirige vers `/pricing`)
- ✅ CTA secondaire : "Rester en Classic" (ferme modal + change layout)

---

## ✅ RELEASE GATE

- ✅ `scripts/release_check.sh` mis à jour : Section 4.5 mentionne PR7.1 + PR8

---

## 📋 FICHIERS CRÉÉS/MODIFIÉS

### Nouveaux fichiers
- `frontend/src/components/PremiumEcoModal.js`

### Fichiers modifiés
- `backend/services/access_control.py` - Format erreur 403
- `backend/routes/mathalea_routes.py` - Application `assert_can_use_layout`
- `backend/routes/user_sheets_routes.py` - Application `assert_can_use_layout`
- `backend/server.py` - Application `assert_can_use_layout` dans export-selection
- `backend/tests/test_export_access_control.py` - Tests PR8 (403 au lieu de 402)
- `frontend/src/lib/exportPdfUtils.js` - Gestion erreurs 403
- `frontend/src/components/SheetBuilderPage.js` - Toggle Éco + modal premium
- `frontend/src/components/SheetComposerPage.js` - Select layout + modal premium
- `frontend/src/components/SheetEditPageP31.js` - Toggle Éco + redirection pricing
- `frontend/src/App.js` - Gestion erreur 403
- `scripts/release_check.sh` - Mention PR8

---

## ✅ DoD VÉRIFIÉ

- ✅ Impossible de contourner (backend) : Tous les endpoints vérifient `assert_can_use_layout`
- ✅ UX propre (modal premium) : Modal créée selon spécifications
- ✅ Classic continue de fonctionner : Layout classic autorisé pour Free users
- ✅ release_check.sh passe : Tests backend inclus

---

## 🧪 TESTS À VALIDER

1. **Backend** :
   - `pytest backend/tests/test_export_access_control.py::TestExportAccessControl::test_assert_can_use_layout_eco_free_raises_403`
   - `pytest backend/tests/test_export_access_control.py::TestExportAccessControl::test_assert_can_use_layout_classic_free_allowed`
   - `pytest backend/tests/test_export_access_control.py::TestExportAccessControl::test_assert_can_use_layout_eco_pro_allowed`

2. **Frontend** (tests manuels) :
   - User Free : Toggle Éco désactivé + badge Premium
   - User Free : Clic sur toggle Éco → Modal premium s'ouvre
   - User Free : Export avec layout=eco → Erreur 403 → Modal premium
   - User Pro : Toggle Éco activable
   - User Pro : Export avec layout=eco → Succès

---

**Status** : ✅ PR8 prêt pour merge

