# P0 - Fix Régressions / Bypass Quota

## Objectif
Corriger 3 points critiques pour éviter régressions et bypass du quota

---

## 1. useAuth() doit être utilisé ailleurs que ExerciseGeneratorPage

### Problème
Si `useAuth()` n'est utilisé que dans `ExerciseGeneratorPage`, les autres pages (`SheetBuilderPage`, `MyExercisesPage`, `MySheetsPage`) gardent leur logique d'auth manuelle, créant des incohérences (une page "voit Pro", l'autre non).

### Solution
Intégrer `useAuth()` dans **SheetBuilderPage** et **MyExercisesPage** (minimum P0).

### Fichiers modifiés

#### `frontend/src/components/SheetBuilderPage.js`

**Diff 1** - Import useAuth

```diff
import UpgradeProModal from "./UpgradeProModal";
import { useToast } from "../hooks/use-toast";
+ import { useAuth } from "../hooks/useAuth";
```

**Diff 2** - Remplacer état auth manuel par useAuth()

```diff
- // États pour l'utilisateur et Pro
- const [userEmail, setUserEmail] = useState("");
- const [isPro, setIsPro] = useState(false);
- const [sessionToken, setSessionToken] = useState("");
+ // P0: Utiliser useAuth() pour cohérence avec ExerciseGeneratorPage
+ const { sessionToken, userEmail, isPro } = useAuth();
```

**Diff 3** - Supprimer useEffect d'initialisation auth

```diff
- // Initialiser l'authentification
- useEffect(() => {
-   const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
-   const storedEmail = localStorage.getItem('lemaitremot_user_email');
-   const loginMethod = localStorage.getItem('lemaitremot_login_method');
-   
-   if (storedSessionToken && storedEmail && loginMethod === 'session') {
-     setSessionToken(storedSessionToken);
-     setUserEmail(storedEmail);
-     setIsPro(true);
-     console.log('✅ Session Pro détectée:', storedEmail);
-   }
- }, []);
+ // P0: Plus besoin d'initialiser auth manuellement - useAuth() le fait
```

**Diff 4** - handleLogout: supprimer setState

```diff
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
-     setSessionToken("");
-     setUserEmail("");
-     setIsPro(false);
+     // P0: useAuth() se mettra à jour automatiquement via l'événement storage
+     // Plus besoin de setSessionToken/setUserEmail/setIsPro
```

#### `frontend/src/components/MyExercisesPage.js`

**Diff 1** - Import useAuth

```diff
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
+ import { useAuth } from "../hooks/useAuth";
```

**Diff 2** - Remplacer état auth manuel par useAuth()

```diff
- const [exercises, setExercises] = useState([]);
- const [loading, setLoading] = useState(true);
- const [userEmail, setUserEmail] = useState("");
- const [isPro, setIsPro] = useState(false);
- const [sessionToken, setSessionToken] = useState("");
+ // P0: Utiliser useAuth() pour cohérence avec ExerciseGeneratorPage
+ const { sessionToken, userEmail, isPro } = useAuth();
+ 
+ const [exercises, setExercises] = useState([]);
+ const [loading, setLoading] = useState(true);
```

**Diff 3** - Simplifier useEffect

```diff
- useEffect(() => {
-   const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
-   const storedEmail = localStorage.getItem('lemaitremot_user_email');
-   const loginMethod = localStorage.getItem('lemaitremot_login_method');
-   
-   if (storedSessionToken && storedEmail && loginMethod === 'session') {
-     setSessionToken(storedSessionToken);
-     setUserEmail(storedEmail);
-     setIsPro(true);
-     loadExercises();
-   } else {
-     sessionStorage.setItem('postLoginRedirect', '/mes-exercices');
-     setLoading(false);
-   }
- }, []);
- 
- // BUG-003: Recharger les exercices quand sessionToken devient disponible après login
- useEffect(() => {
-   if (sessionToken && isPro) {
-     loadExercises();
-   }
- }, [sessionToken, isPro]);
+ // P0: Plus besoin d'initialiser auth manuellement - useAuth() le fait
+ // Charger les exercices quand sessionToken devient disponible
+ useEffect(() => {
+   if (sessionToken && isPro) {
+     loadExercises();
+   } else if (!sessionToken) {
+     sessionStorage.setItem('postLoginRedirect', '/mes-exercices');
+     setLoading(false);
+   }
+ }, [sessionToken, isPro]);
```

**Diff 4** - loadExercises: utiliser sessionToken de useAuth()

```diff
  const loadExercises = async () => {
    try {
      setLoading(true);
      
-     const sessionToken = localStorage.getItem('lemaitremot_session_token');
+     // P0: Utiliser sessionToken de useAuth() au lieu de localStorage
      if (!sessionToken) {
        setLoading(false);
        return;
      }
```

**Diff 5** - handleLogout: supprimer setState

```diff
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
-     setSessionToken("");
-     setUserEmail("");
-     setIsPro(false);
+     // P0: useAuth() se mettra à jour automatiquement via l'événement storage
+     // Plus besoin de setSessionToken/setUserEmail/setIsPro
```

---

## 2. guest_id : attention au "regen"

### Problème
Si `SheetBuilderPage` crée un `guest_id` quand absent, ça peut fragmenter le quota (et donner plus de gratuits si ça régénère trop facilement).

### Solution
**Règle**: Ne jamais générer `guest_id` ailleurs que dans `App.js`. Ailleurs : juste "lire et exiger".

### Fichiers modifiés

#### `frontend/src/components/SheetBuilderPage.js`

**Diff 1** - loadQuotaStatus: ne pas créer guest_id

```diff
  // P0: Fonction pour charger le quota
+ // IMPORTANT: Ne JAMAIS créer guest_id ici - seulement lire depuis App.js
  const loadQuotaStatus = async () => {
    try {
      setQuotaLoading(true);
      const guestId = localStorage.getItem('lemaitremot_guest_id');
      
      if (!guestId) {
-       // Créer un guest_id si absent
-       const newGuestId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
-       localStorage.setItem('lemaitremot_guest_id', newGuestId);
-       
-       // Charger avec le nouveau guest_id
-       const response = await axios.get(`${API}/quota/check?guest_id=${newGuestId}`);
-       setQuotaStatus(response.data);
-       return;
+       // P0 FIX: Ne pas créer guest_id ici - App.js le fait
+       // Si absent, attendre qu'App.js le crée (ou afficher message)
+       console.warn('[QUOTA] guest_id absent - App.js devrait le créer');
+       return;
      }
```

**Diff 2** - handleGeneratePDF: ne pas créer guest_id

```diff
    // P0: Vérifier le quota avant export (si !isPro)
    if (!isPro) {
      const guestId = localStorage.getItem('lemaitremot_guest_id');
      
      if (!guestId) {
-       // Créer un guest_id si absent
-       const newGuestId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
-       localStorage.setItem('lemaitremot_guest_id', newGuestId);
+       // P0 FIX: Ne pas créer guest_id ici - App.js le fait
+       toast({
+         title: "Erreur",
+         description: "Guest ID manquant. Veuillez rafraîchir la page.",
+         variant: "destructive"
+       });
+       return;
      }
      
      // Vérifier le quota
      try {
-       const quotaResponse = await axios.get(`${API}/quota/check?guest_id=${guestId || localStorage.getItem('lemaitremot_guest_id')}`);
+       const quotaResponse = await axios.get(`${API}/quota/check?guest_id=${guestId}`);
        const quota = quotaResponse.data;
```

---

## 3. Backend export-standard : choisir UNE seule méthode de guest_id

### Problème
"header + query acceptés" = dette technique et cas bizarres (quelle méthode prioritaire ?).

### Solution
**Décision**: `X-Guest-ID` uniquement (header). Supprimer le paramètre query `guest_id`.

### Fichiers modifiés

#### `backend/routes/mathalea_routes.py`

**Diff 1** - Supprimer paramètre query guest_id

```diff
@router.post("/sheets/{sheet_id}/export-standard")
async def export_standard_pdf(
    sheet_id: str,
    request: Request,
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
-   x_guest_id: Optional[str] = Header(None, alias="X-Guest-ID"),
-   guest_id: Optional[str] = Query(None, description="Guest ID (alternative to header)")
+   x_guest_id: Optional[str] = Header(None, alias="X-Guest-ID")
):
```

**Diff 2** - Docstring: préciser header uniquement

```diff
    Guards:
    - Si X-Session-Token présent: vérifie Pro (pas de quota si Pro)
-   - Sinon: exige guest_id (header X-Guest-ID ou query ?guest_id=)
+   - Sinon: exige X-Guest-ID (header uniquement - P0 FIX: une seule méthode)
    - Guest: quota 3 exports / 30 jours (compté dans db.exports)
```

**Diff 3** - Logique: utiliser uniquement x_guest_id

```diff
    # 2. Si pas Pro, exiger X-Guest-ID (header uniquement - P0 FIX)
    if not is_pro_user:
-       guest_id_final = x_guest_id or guest_id
+       guest_id_final = x_guest_id
        if not guest_id_final:
            logger.warning(
+               f"[EXPORT_QUOTA] user_type=guest sheet_id={sheet_id} - X-Guest-ID manquant"
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "guest_id_required",
-                   "message": "Guest ID requis pour les utilisateurs non-Pro. Fournissez X-Guest-ID (header) ou guest_id (query).",
+                   "message": "Guest ID requis pour les utilisateurs non-Pro. Fournissez X-Guest-ID (header).",
                    "hint": "Les utilisateurs Pro peuvent utiliser X-Session-Token pour un accès illimité."
                }
            )
```

**Diff 4** - Améliorer logs avec user_type, guest_id, exports_used

```diff
    # 1. Si X-Session-Token présent, vérifier Pro
+   user_type = "guest"  # Par défaut
    if x_session_token:
        try:
            user_email = await validate_session_token(x_session_token)
            if user_email:
                is_pro_user, _ = await check_user_pro_status(user_email)
                if is_pro_user:
+                   user_type = "pro"
                    logger.info(
-                       f"[EXPORT_QUOTA] Pro user {user_email} - pas de quota"
+                       f"[EXPORT_QUOTA] user_type=pro user_email={user_email} sheet_id={sheet_id} - pas de quota"
                    )
                else:
+                   user_type = "non_pro"
                    logger.info(
-                       f"[EXPORT_QUOTA] User {user_email} n'est pas Pro - nécessite guest_id"
+                       f"[EXPORT_QUOTA] user_type=non_pro user_email={user_email} sheet_id={sheet_id} - nécessite guest_id"
                    )
        except Exception as e:
-           logger.warning(f"[EXPORT_QUOTA] Erreur validation session: {e}")
+           logger.warning(f"[EXPORT_QUOTA] Erreur validation session: {e} - traité comme guest")
            # Continue comme guest si session invalide
```

**Diff 5** - Logs quota avec user_type, guest_id, exports_used

```diff
        if quota_status["quota_exceeded"]:
            logger.warning(
-               f"[EXPORT_QUOTA] Quota dépassé pour guest_id={guest_id_final[:8]}... "
-               f"(exports_used={quota_status['exports_used']}, max={quota_status['max_exports']})"
+               f"[EXPORT_QUOTA] user_type=guest guest_id={guest_id_final[:8]}... sheet_id={sheet_id} "
+               f"exports_used={quota_status['exports_used']} max_exports={quota_status['max_exports']} - QUOTA_EXCEEDED"
            )
            raise HTTPException(...)
        
        logger.info(
-           f"[EXPORT_QUOTA] Quota OK pour guest_id={guest_id_final[:8]}... "
-           f"(exports_used={quota_status['exports_used']}, remaining={quota_status['exports_remaining']})"
+           f"[EXPORT_QUOTA] user_type=guest guest_id={guest_id_final[:8]}... sheet_id={sheet_id} "
+           f"exports_used={quota_status['exports_used']} exports_remaining={quota_status['exports_remaining']} - QUOTA_OK"
        )
```

**Diff 6** - Log enregistrement export

```diff
                await db.exports.insert_one(export_doc)
                logger.info(
-                   f"[EXPORT_QUOTA] Export enregistré pour guest_id={guest_id_final[:8]}..."
+                   f"[EXPORT_QUOTA] user_type=guest guest_id={guest_id_final[:8]}... sheet_id={sheet_id} "
+                   f"- export enregistré dans db.exports"
                )
```

---

## Résumé des changements

### Frontend
- ✅ **SheetBuilderPage**: Utilise `useAuth()` au lieu de logique manuelle
- ✅ **MyExercisesPage**: Utilise `useAuth()` au lieu de logique manuelle
- ✅ **SheetBuilderPage**: Ne crée plus `guest_id` (seulement lit depuis App.js)
- ✅ **handleLogout**: Supprime setState (useAuth() se met à jour automatiquement)

### Backend
- ✅ **export-standard**: Accepte uniquement `X-Guest-ID` (header), plus de query param
- ✅ **Logs améliorés**: Format standardisé `user_type=pro/guest guest_id=... sheet_id=... exports_used=...`

### Bénéfices
- ✅ **Cohérence**: Toutes les pages utilisent `useAuth()` → même comportement
- ✅ **Pas de fragmentation quota**: `guest_id` créé uniquement dans App.js
- ✅ **Simplicité backend**: Une seule méthode pour `guest_id` (header)
- ✅ **Observabilité**: Logs clairs avec `user_type`, `guest_id`, `exports_used`

---

## Tests manuels

### Test 1: useAuth() cohérent entre pages
1. ✅ Ouvrir `ExerciseGeneratorPage` → Vérifier `isPro` affiché
2. ✅ Ouvrir `SheetBuilderPage` → Vérifier `isPro` affiché (même valeur)
3. ✅ Ouvrir `MyExercisesPage` → Vérifier `isPro` affiché (même valeur)
4. ✅ Se connecter en Pro → Vérifier que les 3 pages se mettent à jour automatiquement

### Test 2: guest_id non régénéré
1. ✅ Supprimer `lemaitremot_guest_id` du localStorage
2. ✅ Ouvrir `SheetBuilderPage` directement (sans passer par App.js)
3. ✅ **VÉRIFIER**: Pas de création de `guest_id` dans SheetBuilderPage
4. ✅ **VÉRIFIER**: Message d'erreur si export tenté sans `guest_id`

### Test 3: Backend accepte uniquement X-Guest-ID
1. ✅ Tenter export avec `?guest_id=test` (query) → **VÉRIFIER**: 400
2. ✅ Tenter export avec `X-Guest-ID: test` (header) → **VÉRIFIER**: 200 (si quota OK)
3. ✅ Vérifier logs: format `user_type=guest guest_id=... sheet_id=... exports_used=...`



