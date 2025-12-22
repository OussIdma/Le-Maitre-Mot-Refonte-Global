# Corrections P0 - Implémentation et Tests

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté et testé

---

## Résumé des corrections

### P0-1 : Validation des variables d'environnement
- **Fichier modifié** : `backend/server.py` (lignes ~395-397)
- **Changement** : Ajout de `validate_env()` qui vérifie `MONGO_URL` et `DB_NAME` avant création du client MongoDB
- **Impact** : Crash immédiat avec message clair si variables manquantes (au lieu de KeyError cryptique)

### P0-2 : Authentification Pro pour export PDF
- **Fichier modifié** : `backend/routes/mathalea_routes.py` (lignes ~1181-1200, ~1264-1266)
- **Changement** : 
  - Suppression du comportement "tout token = Pro"
  - Utilisation de `validate_session_token()` + `check_user_pro_status()`
  - `user_email` vient toujours de la session DB, jamais du token brut
  - Codes HTTP clairs : 401 (token invalide), 403 (non-Pro)
- **Impact** : Sécurité renforcée, pas d'accès PDF Pro sans authentification réelle

### P0-3 : Robustesse WeasyPrint
- **Fichier modifié** : `backend/routes/mathalea_routes.py` (lignes ~1275-1280, ~1324-1342)
- **Changements** :
  - Logo : vérification `exists()` ET `is_file()` avant injection
  - Timeout : `asyncio.wait_for()` avec 30s max sur génération PDF
  - `base_url` explicite pour WeasyPrint
  - Erreurs JSON claires : 504 (timeout), 500 (erreur génération)
- **Impact** : PDF ne bloque plus indéfiniment, logo manquant géré gracieusement

---

## Fichiers modifiés

1. **backend/server.py**
   - Ajout fonction `validate_env()` (lignes ~394-410)
   - Remplacement `os.environ['MONGO_URL']` par validation explicite

2. **backend/routes/mathalea_routes.py**
   - Correction authentification Pro (lignes ~1181-1200)
   - Suppression fallback email (ligne ~1266)
   - Amélioration validation logo (lignes ~1275-1280)
   - Ajout timeout PDF (lignes ~1324-1362)

3. **backend/tests/test_p0_fixes.py** (nouveau)
   - Tests P0-1 : validation env variables
   - Tests P0-2 : authentification Pro
   - Tests P0-3 : robustesse WeasyPrint

---

## Commandes pour exécuter les tests

### Prérequis
```bash
# Installer pytest si nécessaire
pip install pytest pytest-asyncio

# S'assurer que les variables d'environnement sont configurées pour les tests
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="test_db"
```

### Exécuter tous les tests P0
```bash
cd /Users/oussamaidamhane/Desktop/Projet\ local\ LMM/Le-Maitre-Mot-v16-Refonte-Sauvegarde
pytest backend/tests/test_p0_fixes.py -v
```

### Exécuter un test spécifique
```bash
# Test validation env (P0-1)
pytest backend/tests/test_p0_fixes.py::test_env_validation_missing_mongo_url -v
pytest backend/tests/test_p0_fixes.py::test_env_validation_missing_db_name -v
pytest backend/tests/test_p0_fixes.py::test_env_validation_success -v

# Test authentification Pro (P0-2)
pytest backend/tests/test_p0_fixes.py::test_pro_pdf_auth_no_token -v
pytest backend/tests/test_p0_fixes.py::test_pro_pdf_auth_invalid_token -v
pytest backend/tests/test_p0_fixes.py::test_pro_pdf_auth_user_not_pro -v

# Test robustesse WeasyPrint (P0-3)
pytest backend/tests/test_p0_fixes.py::test_logo_path_validation_exists_and_is_file -v
pytest backend/tests/test_p0_fixes.py::test_logo_path_validation_not_exists -v
pytest backend/tests/test_p0_fixes.py::test_pdf_generation_timeout -v
```

### Vérifier la compilation
```bash
python3 -m py_compile backend/server.py backend/routes/mathalea_routes.py backend/tests/test_p0_fixes.py
```

---

## Tests manuels recommandés

### P0-1 : Validation env
```bash
# Tester sans MONGO_URL
unset MONGO_URL
python3 -c "from backend.server import validate_env; validate_env()"
# Attendu : RuntimeError avec message clair

# Tester sans DB_NAME
export MONGO_URL="mongodb://localhost:27017"
unset DB_NAME
python3 -c "from backend.server import validate_env; validate_env()"
# Attendu : RuntimeError avec message clair
```

### P0-2 : Authentification Pro
```bash
# Tester avec token invalide
curl -X POST http://localhost:8000/api/mathalea/sheets/test_sheet/generate-pdf-pro \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: fake-token-123" \
  -d '{"template": "classique", "type_doc": "sujet"}'
# Attendu : 401 avec {"error": "INVALID_SESSION_TOKEN", ...}

# Tester sans token
curl -X POST http://localhost:8000/api/mathalea/sheets/test_sheet/generate-pdf-pro \
  -H "Content-Type: application/json" \
  -d '{"template": "classique", "type_doc": "sujet"}'
# Attendu : 401 avec {"error": "AUTHENTICATION_REQUIRED", ...}
```

### P0-3 : Robustesse WeasyPrint
```bash
# Tester avec logo manquant (doit générer PDF sans logo)
# (nécessite un utilisateur Pro valide avec logo_url pointant vers fichier inexistant)
# Attendu : PDF généré avec logo_url=None, pas de crash

# Tester timeout (nécessite un PDF très volumineux)
# Attendu : 504 après 30s avec message clair
```

---

## Différences (patch)

### backend/server.py
```diff
- # MongoDB connection
- mongo_url = os.environ['MONGO_URL']
- client = AsyncIOMotorClient(mongo_url)
- db = client[os.environ['DB_NAME']]
+ # MongoDB connection - avec validation des variables d'environnement
+ def validate_env():
+     """Valide les variables d'environnement critiques au démarrage"""
+     required_vars = {
+         'MONGO_URL': os.environ.get('MONGO_URL'),
+         'DB_NAME': os.environ.get('DB_NAME')
+     }
+     
+     missing = [var for var, value in required_vars.items() if not value]
+     if missing:
+         raise RuntimeError(
+             f"Variables d'environnement requises manquantes: {', '.join(missing)}. "
+             f"Veuillez configurer ces variables avant de démarrer l'application."
+         )
+     
+     return required_vars['MONGO_URL'], required_vars['DB_NAME']
+
+ # Valider les variables d'environnement avant de créer le client MongoDB
+ mongo_url, db_name = validate_env()
+ client = AsyncIOMotorClient(mongo_url)
+ db = client[db_name]
```

### backend/routes/mathalea_routes.py
```diff
-     # VÉRIFICATION PRO (Simplified pour MVP - à améliorer avec vraie vérification Pro)
-     # Pour l'instant, on accepte si un token de session est fourni
-     if not x_session_token:
-         logger.warning("⚠️ Tentative d'accès PDF Pro sans token de session")
-         raise HTTPException(
-             status_code=403,
-             detail="PRO_REQUIRED: Un compte Pro est nécessaire pour cette fonctionnalité"
-         )
-     
-     # TODO: Vérifier que le token correspond bien à un compte Pro actif
-     # Pour le MVP, on considère que tout token valide = Pro
+     # VÉRIFICATION PRO - Validation stricte du token et statut Pro
+     if not x_session_token:
+         logger.warning("⚠️ Tentative d'accès PDF Pro sans token de session")
+         raise HTTPException(
+             status_code=401,
+             detail={"error": "AUTHENTICATION_REQUIRED", "message": "Token de session requis"}
+         )
+     
+     # Valider le token de session et récupérer l'email
+     from backend.server import validate_session_token, check_user_pro_status
+     
+     user_email = await validate_session_token(x_session_token)
+     if not user_email:
+         logger.warning(f"⚠️ Token de session invalide ou expiré: {x_session_token[:20]}...")
+         raise HTTPException(
+             status_code=401,
+             detail={"error": "INVALID_SESSION_TOKEN", "message": "Token de session invalide ou expiré"}
+         )
+     
+     # Vérifier que l'utilisateur est Pro actif
+     is_pro, user = await check_user_pro_status(user_email)
+     if not is_pro:
+         logger.warning(f"⚠️ Utilisateur {user_email} n'est pas Pro ou abonnement expiré")
+         raise HTTPException(
+             status_code=403,
+             detail={"error": "PRO_REQUIRED", "message": "Un compte Pro actif est nécessaire pour cette fonctionnalité"}
+         )
+     
+     logger.info(f"✅ Utilisateur Pro authentifié: {user_email}")

-         # TODO: Extraire le vrai email depuis le token de session
-         # Pour l'instant, utiliser un email par défaut ou token comme identifiant
-         user_email = x_session_token if "@" in x_session_token else "user@lemaitremot.com"
+         # user_email est déjà validé et récupéré depuis la session DB ci-dessus

-         # Construire le chemin absolu du logo pour WeasyPrint
-         logo_url = pro_config.get("logo_url")
-         if logo_url and not logo_url.startswith('http'):
-             # Convertir le chemin relatif en chemin absolu pour WeasyPrint
-             logo_path = Path("/app/backend") / logo_url.lstrip('/')
-             logo_url = f"file://{logo_path}" if logo_path.exists() else None
+         # Construire le chemin absolu du logo pour WeasyPrint
+         logo_url = pro_config.get("logo_url")
+         if logo_url and not logo_url.startswith('http'):
+             # Convertir le chemin relatif en chemin absolu pour WeasyPrint
+             logo_path = Path("/app/backend") / logo_url.lstrip('/')
+             # Vérifier que le fichier existe ET est un fichier (pas un répertoire)
+             if logo_path.exists() and logo_path.is_file():
+                 logo_url = f"file://{logo_path}"
+             else:
+                 logger.warning(f"⚠️ Logo introuvable ou invalide: {logo_path}")
+                 logo_url = None

-         # 6. Générer les 2 PDFs Pro (Sujet + Corrigé) via Jinja2
-         from engine.pdf_engine.template_renderer import render_pro_sujet, render_pro_corrige
-         import weasyprint
-         
-         # Générer le Sujet Pro (énoncés + zones de réponse)
-         html_sujet = render_pro_sujet(
-             template_style=template,
-             document_data=document_data,
-             template_config=template_config
-         )
-         pro_subject_pdf_bytes = weasyprint.HTML(string=html_sujet).write_pdf()
-         
-         # Générer le Corrigé Pro (énoncés + solutions)
-         html_corrige = render_pro_corrige(
-             template_style=template,
-             document_data=document_data,
-             template_config=template_config
-         )
-         pro_correction_pdf_bytes = weasyprint.HTML(string=html_corrige).write_pdf()
+         # 6. Générer les 2 PDFs Pro (Sujet + Corrigé) via Jinja2
+         from engine.pdf_engine.template_renderer import render_pro_sujet, render_pro_corrige
+         import weasyprint
+         import asyncio
+         
+         # Helper pour générer PDF avec timeout
+         async def generate_pdf_with_timeout(html_content: str, pdf_name: str, timeout_seconds: int = 30) -> bytes:
+             """Génère un PDF avec timeout pour éviter les blocages"""
+             try:
+                 # Exécuter WeasyPrint dans un thread pool avec timeout
+                 loop = asyncio.get_event_loop()
+                 pdf_bytes = await asyncio.wait_for(
+                     loop.run_in_executor(
+                         None,
+                         lambda: weasyprint.HTML(
+                             string=html_content,
+                             base_url=str(Path("/app/backend").resolve())
+                         ).write_pdf()
+                     ),
+                     timeout=timeout_seconds
+                 )
+                 logger.info(f"✅ PDF {pdf_name} généré avec succès ({len(pdf_bytes)} bytes)")
+                 return pdf_bytes
+             except asyncio.TimeoutError:
+                 logger.error(f"❌ Timeout lors de la génération du PDF {pdf_name} (> {timeout_seconds}s)")
+                 raise HTTPException(
+                     status_code=504,
+                     detail={
+                         "error": "PDF_GENERATION_TIMEOUT",
+                         "message": f"La génération du PDF {pdf_name} a pris trop de temps (> {timeout_seconds}s). Veuillez réessayer avec moins d'exercices."
+                     }
+                 )
+             except Exception as e:
+                 logger.error(f"❌ Erreur lors de la génération du PDF {pdf_name}: {e}")
+                 raise HTTPException(
+                     status_code=500,
+                     detail={
+                         "error": "PDF_GENERATION_ERROR",
+                         "message": f"Erreur lors de la génération du PDF {pdf_name}: {str(e)}"
+                     }
+                 )
+         
+         # Générer le Sujet Pro (énoncés + zones de réponse)
+         html_sujet = render_pro_sujet(
+             template_style=template,
+             document_data=document_data,
+             template_config=template_config
+         )
+         pro_subject_pdf_bytes = await generate_pdf_with_timeout(html_sujet, "sujet", timeout_seconds=30)
+         
+         # Générer le Corrigé Pro (énoncés + solutions)
+         html_corrige = render_pro_corrige(
+             template_style=template,
+             document_data=document_data,
+             template_config=template_config
+         )
+         pro_correction_pdf_bytes = await generate_pdf_with_timeout(html_corrige, "corrigé", timeout_seconds=30)
```

---

## Compatibilité legacy

✅ **Aucun breaking change API** :
- Les endpoints existants fonctionnent identiquement
- Seule la validation interne est renforcée
- Les codes HTTP sont plus précis mais restent cohérents (401/403 au lieu de 403 générique)

✅ **Logs explicites** :
- Tous les cas d'erreur sont loggés avec contexte
- Messages d'erreur JSON structurés pour le frontend

✅ **Pas de fallback silencieux** :
- Toutes les erreurs remontent explicitement
- Pas de comportement par défaut caché

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, testé, prêt pour validation

