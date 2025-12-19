# INCIDENT — Correction extraction exercise_type depuis generator_key

**ID**: INCIDENT_2025-12-18_auto_sync_exercise_type_extraction  
**Date**: 2025-12-18  
**Type**: 🐛 Bug fix (auto-sync)

---

## 📋 SYMPTÔME

- **Contexte**: Chapitre créé avec un exercice dynamique via l'admin
- **Problème**: Le chapitre n'est pas sélectionnable dans le générateur (badge "indisponible")
- **Comportement observé**: Le chapitre devient sélectionnable seulement quand un exercice statique est ajouté
- **Attendu**: Le chapitre doit être sélectionnable dès qu'un exercice dynamique est créé

---

## 🔍 ROOT CAUSE

**Problème dans `CurriculumSyncService.extract_exercise_types_from_chapter()`** :

1. **Mapping statique incomplet** : Le mapping `GENERATOR_TO_EXERCISE_TYPE` ne contenait que quelques générateurs (`SYMETRIE_AXIALE_V2`, `THALES_V1`, `THALES_V2`). Si un `generator_key` n'était pas dans le mapping, le fallback utilisait le `generator_key` tel quel, qui peut ne pas correspondre à un `exercise_type` valide dans le curriculum.

2. **Non-utilisation des métadonnées** : Les générateurs Factory (`SYMETRIE_AXIALE_V2`, `THALES_V2`) ont des métadonnées (`GeneratorMeta.exercise_type`) qui contiennent l'`exercise_type` correct, mais le service ne les utilisait pas.

3. **Résultat** : Si le `generator_key` n'était pas dans le mapping statique, l'`exercise_type` extrait était incorrect ou vide → chapitre créé sans `exercise_types` → `hasGenerators: false` → badge "indisponible".

---

## ✅ FIX APPLIQUÉ

### 1. Extraction automatique depuis les métadonnées du générateur

**Fichier** : `backend/services/curriculum_sync_service.py`

**Nouvelle fonction** : `_get_exercise_type_from_generator()`

**Stratégie** :
1. **Essayer d'abord via `GeneratorFactory`** : Récupérer les métadonnées du générateur (`GeneratorMeta.exercise_type`)
2. **Fallback sur le mapping statique** : Si les métadonnées ne sont pas disponibles
3. **Dernier fallback** : Utiliser le `generator_key` normalisé (uppercase)

**Avantages** :
- ✅ Fonctionne pour tous les générateurs Factory (métadonnées disponibles)
- ✅ Compatible avec les générateurs legacy (mapping statique)
- ✅ Logging explicite pour le debugging

### 2. Amélioration du logging

**Ajouts** :
- Log `INFO` quand des `exercise_types` sont détectés
- Log `ERROR` si aucun `exercise_type` n'est détecté (avec message explicite)
- Log `DEBUG` pour chaque extraction d'`exercise_type`

### 3. Endpoint de synchronisation manuelle

**Fichier** : `backend/routes/admin_exercises_routes.py`

**Nouvel endpoint** : `POST /api/admin/chapters/{chapter_code}/sync-curriculum`

**Utilité** : Permet de forcer la re-synchronisation d'un chapitre "indisponible" sans avoir à créer/modifier un exercice.

---

## 🧪 TESTS / PREUVE

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

2. **Vérifier les logs backend** :
   ```bash
   docker compose logs backend | grep -i "CURRICULUM_SYNC"
   ```
   - Doit afficher : `✅ Exercise types détectés pour 6E_G07_DYN: ['SYMETRIE_AXIALE']`
   - Doit afficher : `exercise_type extrait depuis métadonnées pour SYMETRIE_AXIALE_V2: SYMETRIE_AXIALE`

3. **Vérifier que le chapitre a été créé dans le curriculum** :
   ```bash
   curl -s http://localhost:8000/api/admin/curriculum/6e/chapters | jq '.chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner le chapitre avec `exercise_types: ["SYMETRIE_AXIALE"]` (non vide)

4. **Vérifier le catalogue** :
   ```bash
   curl -s http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner le chapitre avec `generators: ["SYMETRIE_AXIALE"]` (non vide)

5. **Vérifier dans le frontend** :
   - Recharger le générateur
   - Le chapitre `6e_G07_DYN` doit apparaître **sans badge "indispo"**
   - `hasGenerators: true` → sélectionnable

### Test de synchronisation manuelle

Si le chapitre est toujours "indisponible" après création d'exercice :

```bash
curl -X POST http://localhost:8000/api/admin/chapters/6e_G07_DYN/sync-curriculum
```

- Doit retourner : `{"success": true, "exercise_types": ["SYMETRIE_AXIALE"], ...}`

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

1. **Extension future** :
   - Ajouter d'autres générateurs au mapping statique si nécessaire (pour compatibilité legacy)
   - Les générateurs Factory utilisent automatiquement les métadonnées (pas besoin de mapping)

2. **Monitoring** :
   - Surveiller les logs `[CURRICULUM_SYNC]` pour détecter les cas où l'extraction échoue
   - Alerter si un chapitre est créé sans `exercise_types` (log ERROR)

3. **Documentation** :
   - Documenter que les générateurs Factory doivent avoir `GeneratorMeta.exercise_type` défini
   - Ajouter une validation dans les tests pour s'assurer que tous les générateurs ont un `exercise_type`

---

## 🔗 FICHIERS IMPACTÉS

- `backend/services/curriculum_sync_service.py` : Extraction automatique depuis métadonnées
- `backend/routes/admin_exercises_routes.py` : Endpoint de synchronisation manuelle
- `docs/incidents/INCIDENT_2025-12-18_auto_sync_exercise_type_extraction.md` : Ce document
- `docs/CHANGELOG_TECH.md` : Entrée ajoutée

---

## ✅ VALIDATION

- [x] Extraction automatique depuis `GeneratorMeta.exercise_type` implémentée
- [x] Fallback sur mapping statique conservé
- [x] Logging amélioré (INFO/ERROR/DEBUG)
- [x] Endpoint de synchronisation manuelle créé
- [x] Tests manuels documentés
- [x] Document d'incident créé
- [x] Changelog mis à jour

---

## 🎯 EFFET ATTENDU

**Chapitres dynamiques sélectionnables** :
- Création d'un exercice dynamique → extraction correcte de l'`exercise_type` depuis les métadonnées
- Chapitre créé avec `exercise_types` non vide → `hasGenerators: true` → sélectionnable
- Plus besoin d'ajouter un exercice statique pour rendre le chapitre sélectionnable

**Amélioration de la robustesse** :
- Fonctionne pour tous les générateurs Factory (métadonnées)
- Compatible avec les générateurs legacy (mapping statique)
- Logging explicite pour le debugging



