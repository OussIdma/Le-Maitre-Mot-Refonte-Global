# INCIDENT — Générateurs dynamiques manquants dans l'admin

**ID**: INCIDENT_2025-12-18_generateurs_dynamiques_manquants_admin  
**Date**: 2025-12-18  
**Type**: 🐛 Bug fix (admin UI)

---

## 📋 SYMPTÔME

- **Contexte**: Création/modification d'un chapitre dynamique dans l'admin
- **Problème**: Lors de la création d'un chapitre, la liste des générateurs proposés ne contient que des générateurs statiques (ex: "TRIANGLE_QUELCONQUE", "RECTANGLE", etc.)
- **Comportement observé**: 
  - Impossible de sélectionner un générateur dynamique (comme "AGRANDISSEMENT_REDUCTION" utilisé pour "Tests Dynamiques")
  - Le chapitre reste "indisponible" car il n'a pas de générateur dans le curriculum
  - Un chapitre test créé par l'agent IA ("Tests Dynamiques") fonctionne car il a été créé avec `exercise_types: ["AGRANDISSEMENT_REDUCTION"]` directement dans le curriculum_6e.json
- **Attendu**: Les générateurs dynamiques doivent être disponibles dans la liste des générateurs proposés dans l'admin

---

## 🔍 ROOT CAUSE

**Source de vérité incomplète** : La fonction `get_available_generators()` dans `CurriculumPersistenceService` retournait uniquement les générateurs statiques (`MathExerciseType`), sans inclure les générateurs dynamiques.

**Fichier** : `backend/services/curriculum_persistence_service.py::get_available_generators()`

**Ligne 335-345** : 
```python
async def get_available_generators(self) -> List[str]:
    try:
        from models.math_models import MathExerciseType
        return [e.name for e in MathExerciseType]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des générateurs: {e}")
        return []
```

**Problème** :
- Ne retournait que les `MathExerciseType` (générateurs statiques)
- N'incluait pas les `exercise_types` extraits depuis les générateurs dynamiques (`GeneratorFactory`)
- Résultat : l'admin ne proposait que des générateurs statiques, impossible de créer un chapitre dynamique avec un générateur dynamique

**Exemple** :
- Le générateur dynamique `THALES_V1` a un `exercise_type: "AGRANDISSEMENT_REDUCTION"` dans ses métadonnées
- Mais "AGRANDISSEMENT_REDUCTION" n'était pas dans la liste des générateurs disponibles dans l'admin
- Donc impossible de sélectionner ce générateur lors de la création d'un chapitre dynamique

---

## ✅ FIX APPLIQUÉ

**Fichier** : `backend/services/curriculum_persistence_service.py`

**Modification** : Enrichissement de `get_available_generators()` pour inclure les générateurs dynamiques.

**Stratégie** :
1. **Générateurs statiques** : Récupérer tous les `MathExerciseType` (comme avant)
2. **Générateurs dynamiques** : Récupérer tous les générateurs depuis `GeneratorFactory` et extraire leurs `exercise_types` via `_get_exercise_type_from_generator()`
3. **Fusion** : Combiner les deux listes (sans doublons) et retourner la liste triée

**Code clé** :
```python
async def get_available_generators(self) -> List[str]:
    generators = set()
    
    # 1. Générateurs statiques (MathExerciseType)
    try:
        from models.math_models import MathExerciseType
        for e in MathExerciseType:
            generators.add(e.name)
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des générateurs statiques: {e}")
    
    # 2. Générateurs dynamiques (GeneratorFactory)
    try:
        from backend.generators.factory import GeneratorFactory
        from backend.services.curriculum_sync_service import _get_exercise_type_from_generator
        
        factory_generators = GeneratorFactory.list_all()
        
        for gen_info in factory_generators:
            generator_key = gen_info.get("key")
            if generator_key:
                # Extraire l'exercise_type depuis les métadonnées ou le mapping
                exercise_type = _get_exercise_type_from_generator(generator_key)
                if exercise_type:
                    generators.add(exercise_type)
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des générateurs dynamiques: {e}")
    
    # Retourner la liste triée
    return sorted(list(generators))
```

**Avantages** :
- ✅ Les générateurs dynamiques sont maintenant disponibles dans l'admin
- ✅ L'admin peut créer/modifier un chapitre dynamique avec un générateur dynamique
- ✅ Source de vérité enrichie : générateurs statiques + dynamiques
- ✅ Logging explicite pour le debugging

---

## 🧪 TESTS / PREUVE

### Test 1 : Vérifier que les générateurs dynamiques sont disponibles

1. **Appeler l'endpoint des options** :
   ```bash
   curl -s http://localhost:8000/api/admin/curriculum/options | jq '.generators'
   ```

2. **Vérifier que les générateurs dynamiques sont présents** :
   - Doit contenir "AGRANDISSEMENT_REDUCTION" (extrait depuis THALES_V1)
   - Doit contenir "SYMETRIE_AXIALE" (extrait depuis SYMETRIE_AXIALE_V2)
   - Doit contenir tous les générateurs statiques (TRIANGLE_QUELCONQUE, RECTANGLE, etc.)

3. **Vérifier dans l'admin** :
   - Ouvrir la page de création/modification d'un chapitre
   - La liste des générateurs doit contenir les générateurs dynamiques
   - Sélectionner "AGRANDISSEMENT_REDUCTION" pour un chapitre dynamique
   - Le chapitre doit être créé avec ce générateur et devenir disponible

### Test 2 : Créer un chapitre dynamique avec un générateur dynamique

1. **Créer un chapitre dynamique via l'admin** :
   - Code officiel : `6e_G07_DYN`
   - Libellé : "Géométrie Dynamique"
   - Domaine : "Géométrie"
   - **Générateurs** : Sélectionner "AGRANDISSEMENT_REDUCTION" (maintenant disponible)
   - Statut : "beta"

2. **Vérifier que le chapitre a été créé** :
   ```bash
   curl -s http://localhost:8000/api/admin/curriculum/6e/chapters | jq '.chapitres[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner le chapitre avec `exercise_types: ["AGRANDISSEMENT_REDUCTION"]`

3. **Vérifier que le chapitre est disponible** :
   ```bash
   curl -s http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner `generators: ["AGRANDISSEMENT_REDUCTION"]` (non vide)
   - Le chapitre doit être sélectionnable dans le frontend (pas de badge "indispo")

---

## 🔧 COMMANDES DE REBUILD / RESTART

**Rebuild backend requis** :
```bash
docker compose build backend
docker compose restart backend
```

**Vérification** :
```bash
# Vérifier que les générateurs dynamiques sont disponibles
curl -s http://localhost:8000/api/admin/curriculum/options | jq '.generators | length'
# Doit retourner un nombre plus élevé qu'avant (inclut maintenant les générateurs dynamiques)
```

---

## 📝 RECOMMANDATIONS

1. **Extension future** :
   - Ajouter d'autres générateurs dynamiques au besoin
   - Les générateurs Factory utilisent automatiquement leurs métadonnées (pas besoin de mapping manuel)

2. **Documentation** :
   - Documenter que les générateurs dynamiques sont maintenant disponibles dans l'admin
   - Expliquer comment créer un chapitre dynamique avec un générateur dynamique

3. **UX Admin** :
   - Peut-être ajouter un indicateur visuel dans l'admin pour distinguer les générateurs statiques des dynamiques
   - Ou regrouper les générateurs par type (statique vs dynamique)

---

## 🔗 FICHIERS IMPACTÉS

- `backend/services/curriculum_persistence_service.py` : Enrichissement de `get_available_generators()`
- `docs/incidents/INCIDENT_2025-12-18_generateurs_dynamiques_manquants_admin.md` : Ce document
- `docs/CHANGELOG_TECH.md` : Entrée ajoutée

---

## ✅ VALIDATION

- [x] Générateurs dynamiques inclus dans la liste des générateurs disponibles
- [x] Extraction automatique depuis GeneratorFactory
- [x] Fusion avec les générateurs statiques (sans doublons)
- [x] Logging explicite pour le debugging
- [x] Tests manuels documentés
- [x] Document d'incident créé
- [x] Changelog mis à jour

---

## 🎯 EFFET ATTENDU

**Générateurs dynamiques disponibles dans l'admin** :
- Création/modification d'un chapitre dynamique → sélection d'un générateur dynamique (ex: "AGRANDISSEMENT_REDUCTION")
- Le chapitre est créé avec le générateur dynamique → devient disponible dans le catalogue
- Plus besoin de modifier manuellement le curriculum_6e.json pour ajouter un générateur dynamique

**Source de vérité enrichie** :
- Générateurs statiques (MathExerciseType) + générateurs dynamiques (GeneratorFactory)
- Extraction automatique depuis les métadonnées des générateurs Factory


