# PR10: PACKAGE IMPORT/EXPORT GLOBAL - RÉSUMÉ D'IMPLÉMENTATION

## ✅ OBJECTIF
Ajouter une brique unique d'import/export "package" qui sert TOUS les parcours (admin, migration, partage).
- Export complet d'un niveau (chapitres + exercices + templates)
- Import avec validation stricte + rollback atomique
- Support dry-run
- Zéro régression (endpoints PR4 continuent de fonctionner)

## ✅ IMPLÉMENTATION

### A) Schéma Package v1.0 (`backend/services/package_schema.py`)
- ✅ Modèle Pydantic `PackageV1` avec structure canonique
- ✅ Validation `validate_package_v1()` pour vérifier:
  - schema_version == "pkg-1.0"
  - Cohérence metadata.counts
  - Normalisation chapter_code
- ✅ Helper `normalize_chapter_code()` (UPPER + "-"→"_")

### B) Endpoints Package (`backend/routes/admin_package_routes.py`)
- ✅ **GET /api/admin/package/export?niveau=6e**:
  - Lit curriculum_chapters filtrés par niveau
  - Lit admin_exercises groupés par chapter_code normalisé
  - Lit admin_templates si collection disponible
  - Retourne package v1.0 avec metadata.counts cohérents
  
- ✅ **POST /api/admin/package/import?dry_run=true|false**:
  - Validation stricte du package (schema_version, counts, normalisation)
  - Validation placeholders (réutilise helper PR4)
  - Mode dry-run: validation uniquement, pas d'écriture
  - Mode apply: import atomique avec rollback (batch_id)
  - Création automatique des chapitres si absents (si payload contient curriculum_chapters)

### C) Rollback Atomique
- ✅ Utilise batch_id pour marquer les documents importés
- ✅ En cas d'erreur: delete_many({batch_id}) pour rollback
- ✅ Rollback exercices + templates (chapitres non supprimés car partagés)

### D) Tests (`backend/tests/test_package_import_export.py`)
- ✅ Test 1: export package retourne schema_version pkg-1.0 + metadata.counts cohérents
- ✅ Test 2: import package dry_run ne crée aucun doc mais retourne stats
- ✅ Test 3: import package apply insère chapters + exercises puis export retrouve les mêmes counts
- ✅ Test 4: rollback sur erreur → vérifier 0 reste en DB
- ✅ Test 5: normalisation chapter_code "6e-gm07" → stocke "6E_GM07"

### E) Release Gate
- ✅ `scripts/release_check.sh` mis à jour: Section 4.6 inclut tests package

## 📋 FICHIERS CRÉÉS/MODIFIÉS

### Nouveaux fichiers
- `backend/services/package_schema.py` - Schéma package v1.0
- `backend/routes/admin_package_routes.py` - Endpoints package
- `backend/tests/test_package_import_export.py` - Tests package
- `PR10_PACKAGE_IMPORT_EXPORT.md` - Documentation

### Fichiers modifiés
- `backend/server.py` - Ajout router admin_package
- `scripts/release_check.sh` - Ajout tests package

## ✅ DoD VÉRIFIÉ

- ✅ Export package "niveau" OK
- ✅ Import package dry-run OK
- ✅ Import package apply OK
- ✅ Rollback atomique prouvé par test
- ✅ Normalisation chapter_code prouvée par test
- ✅ Aucune régression sur PR4/PR5/PR7/PR8 (release_check.sh passe)

## 🔧 RÉUTILISATION CODE EXISTANT

- ✅ Réutilise `validate_import_payload_v1` (PR4) pour validation exercices
- ✅ Réutilise `assert_no_unresolved_placeholders` (PR4) pour validation placeholders
- ✅ Réutilise `normalize_chapter_code` (pattern existant: UPPER + "-"→"_")
- ✅ Réutilise pattern batch_id rollback (PR4)

## 🧪 VALIDATION MANUELLE

1. **Export package** :
   ```bash
   curl "http://localhost:8000/api/admin/package/export?niveau=6e"
   ```
   - Vérifier schema_version="pkg-1.0"
   - Vérifier metadata.counts cohérents

2. **Import dry-run** :
   ```bash
   curl -X POST "http://localhost:8000/api/admin/package/import?dry_run=true" \
     -H "Content-Type: application/json" \
     -d @package_6e.json
   ```
   - Vérifier validation="passed"
   - Vérifier qu'aucun doc n'a été créé en DB

3. **Import apply** :
   ```bash
   curl -X POST "http://localhost:8000/api/admin/package/import?dry_run=false" \
     -H "Content-Type: application/json" \
     -d @package_6e.json
   ```
   - Vérifier success=true
   - Vérifier stats (chapters_created, exercises_inserted)
   - Vérifier que les docs sont en DB

4. **Rollback** :
   - Importer un package avec exercice invalide (enonce_html vide)
   - Vérifier 400 + aucun doc en DB

5. **Normalisation** :
   - Importer avec chapter_code "6e-gm07"
   - Vérifier que l'exercice est stocké avec "6E_GM07"

---

**Status** : ✅ PR10 prêt pour merge

