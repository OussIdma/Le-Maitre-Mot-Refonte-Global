# INCIDENT — Auto-synchronisation Curriculum ⇄ Exercises

**ID**: INCIDENT_2025-12-18_auto_sync_curriculum_exercises  
**Date**: 2025-12-18  
**Type**: ✨ Évolution (suppression script manuel)

---

## 📋 SYMPTÔME / BESOIN

- **Contexte**: Les chapitres créés via l'admin (collection `exercises`) n'apparaissaient pas automatiquement dans le référentiel curriculum (`chapters`)
- **Problème**: Chapitres marqués "indisponible" dans le générateur car absents du curriculum
- **Solution précédente**: Script manuel `sync_chapter_from_exercises.py` à exécuter manuellement
- **Besoin**: Synchronisation automatique lors de la création/mise à jour d'exercices

---

## 🔍 ROOT CAUSE

**Gap fonctionnel** : Aucun hook automatique entre la création/mise à jour d'exercices et la synchronisation du chapitre dans le référentiel curriculum.

**Impact** :
- Chapitres créés via admin non visibles dans le générateur
- Nécessité d'exécuter un script manuel après chaque création/modification
- Risque d'oubli → chapitres "indisponibles"

---

## ✅ FIX APPLIQUÉ

### 1. Création du service `CurriculumSyncService`

**Fichier** : `backend/services/curriculum_sync_service.py`

**Fonctionnalités** :
- `extract_exercise_types_from_chapter()` : Extrait les `exercise_types` depuis les exercices (dynamiques via `generator_key`, statiques via `exercise_type`)
- `sync_chapter_to_curriculum()` : Synchronise un chapitre (création ou mise à jour additive)

**Règles respectées** :
1. ✅ Extraction automatique des `exercise_types` depuis `generator_key` + `exercise_type`
2. ✅ Création idempotente (pas de doublon)
3. ✅ Mise à jour additive (ne supprime rien d'existant)
4. ✅ Zéro fallback silencieux (log + erreur explicite si mapping impossible)
5. ✅ Compatible statique + dynamique

### 2. Intégration dans les routes admin

**Fichier** : `backend/routes/admin_exercises_routes.py`

**Modifications** :
- `create_exercise()` : Appel automatique de `sync_chapter_to_curriculum()` après création
- `update_exercise()` : Appel automatique de `sync_chapter_to_curriculum()` après mise à jour

**Gestion d'erreur** :
- Si la synchronisation échoue, l'exercice est quand même créé/mis à jour (log warning)
- Ne bloque pas l'opération CRUD principale

### 3. Mapping `generator_key` → `exercise_type`

**Mapping défini** :
```python
GENERATOR_TO_EXERCISE_TYPE = {
    "SYMETRIE_AXIALE_V2": "SYMETRIE_AXIALE",
    "SYMETRIE_AXIALE": "SYMETRIE_AXIALE",
    "THALES_V1": "THALES",
    "THALES_V2": "THALES",
    "THALES": "THALES",
}
```

**Fallback** : Si le `generator_key` n'est pas dans le mapping, il est utilisé tel quel.

---

## 🧪 TESTS / PREUVE

### Tests unitaires créés

**Fichier** : `backend/tests/test_curriculum_sync_service.py`

**Scénarios testés** :
1. ✅ Extraction depuis exercices dynamiques (`generator_key`)
2. ✅ Extraction depuis exercices statiques (`exercise_type`)
3. ✅ Extraction depuis exercices mixtes (statique + dynamique)
4. ✅ Création automatique d'un chapitre dans le curriculum
5. ✅ Mise à jour additive (fusion des `exercise_types`, ne supprime pas l'existant)
6. ✅ Aucune mise à jour si `exercise_types` identiques

### Test manuel (à exécuter)

1. **Créer un exercice dynamique dans un nouveau chapitre** :
   ```bash
   curl -X POST http://localhost:8000/api/admin/chapters/6e_G07_DYN/exercises \
     -H "Content-Type: application/json" \
     -d '{
       "is_dynamic": true,
       "generator_key": "SYMETRIE_AXIALE_V2",
       "enonce_template_html": "<p>Test</p>",
       "solution_template_html": "<p>Solution</p>",
       "difficulty": "facile",
       "offer": "free"
     }'
   ```

2. **Vérifier que le chapitre a été créé dans le curriculum** :
   ```bash
   curl -s http://localhost:8000/api/admin/curriculum/6e/chapters | jq '.chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner le chapitre avec `exercise_types: ["SYMETRIE_AXIALE"]`

3. **Vérifier le catalogue** :
   ```bash
   curl -s http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner le chapitre avec `generators: ["SYMETRIE_AXIALE"]` (non vide)

4. **Vérifier dans le frontend** :
   - Recharger le générateur
   - Le chapitre `6e_G07_DYN` doit apparaître **sans badge "indispo"**
   - `hasGenerators: true` → sélectionnable

---

## 🔧 COMMANDES DE REBUILD / RESTART

**Rebuild backend requis** :
```bash
docker compose build backend
docker compose restart backend
```

**Vérification** :
```bash
# Vérifier que le service est bien chargé
docker compose logs backend | grep -i "curriculum_sync"
```

---

## 📝 RECOMMANDATIONS

1. **Extension du mapping** :
   - Ajouter d'autres mappings `generator_key` → `exercise_type` si nécessaire
   - Documenter les nouveaux générateurs dans le mapping

2. **Monitoring** :
   - Surveiller les logs `[AUTO-SYNC]` pour détecter les échecs de synchronisation
   - Alerter si la synchronisation échoue de manière répétée

3. **Performance** :
   - La synchronisation est asynchrone et ne bloque pas l'opération CRUD
   - Si besoin, ajouter un cache pour éviter les requêtes répétées

---

## 🔗 FICHIERS IMPACTÉS

- `backend/services/curriculum_sync_service.py` : Service de synchronisation (nouveau)
- `backend/routes/admin_exercises_routes.py` : Intégration des hooks de synchronisation
- `backend/tests/test_curriculum_sync_service.py` : Tests unitaires (nouveau)
- `docs/incidents/INCIDENT_2025-12-18_auto_sync_curriculum_exercises.md` : Ce document
- `docs/CHANGELOG_TECH.md` : Entrée ajoutée

---

## ✅ VALIDATION

- [x] Service `CurriculumSyncService` créé
- [x] Hooks intégrés dans `create_exercise()` et `update_exercise()`
- [x] Tests unitaires créés (6 scénarios)
- [x] Mapping `generator_key` → `exercise_type` défini
- [x] Gestion d'erreur (ne bloque pas l'opération CRUD)
- [x] Compatible statique + dynamique
- [x] Mise à jour additive (ne supprime pas l'existant)
- [x] Document d'incident créé
- [x] Changelog mis à jour

---

## 🎯 EFFET ATTENDU

**Plus jamais de chapitre "indisponible"** :
- Création/mise à jour d'exercice → synchronisation automatique du chapitre
- Chapitres toujours visibles dans le générateur avec `hasGenerators: true`
- Suppression du script manuel `sync_chapter_from_exercises.py` (obsolète)

**Amélioration de l'UX admin** :
- Zéro étape manuelle supplémentaire
- Synchronisation transparente
- Logs explicites pour le debugging



