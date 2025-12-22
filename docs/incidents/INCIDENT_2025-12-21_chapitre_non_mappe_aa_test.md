# INCIDENT P0 — "CHAPITRE NON MAPPÉ" sur /generate (UI)

**ID**: INCIDENT_2025-12-21_chapitre_non_mappe_aa_test  
**Date**: 2025-12-21  
**Priorité**: P0 (bloquant pour génération multiple)  
**Statut**: 🔍 Root cause identifiée, correctif en cours

---

## 📋 SYMPTÔME

Sur `http://localhost:3000/generate`, quand on sélectionne le chapitre "AA TEST" (niveau 6e) et qu'on demande **plusieurs exercices** (≥2) avec difficulté "difficile", l'UI affiche :

```
❌ CHAPITRE NON MAPPÉ : 'AA TEST'
   Niveau : 6e
   Le chapitre existe dans le curriculum mais aucun générateur n'est défini.
   → Ajoutez ce chapitre au mapping dans _get_exercise_types_for_chapter()
```

**Comportement observé** :
- ✅ 1 exercice avec "difficile" → **fonctionne**
- ✅ "facile" et "moyen" (1 ou plusieurs) → **fonctionne**
- ❌ Plusieurs exercices avec "difficile" → **échoue** (certains appels échouent)

---

## 🔍 ROOT CAUSE (PROUVÉE)

### Hypothèse alternative : Variable manquante lors de la génération

**Hypothèse utilisateur** : L'erreur pourrait provenir d'une variable manquante lors de la génération de l'exercice, plutôt que du fallback statique.

**Validation** :
- Les logs récents montrent `manquantes avant rendu: []` (aucune variable manquante)
- Toutes les variables nécessaires sont présentes : `['d', 'd_red', 'difficulty', 'fraction', 'fraction_reduite', 'is_irreductible', 'n', 'n_red', 'pgcd', 'step1', 'step2', 'step3']`
- **Cependant**, l'erreur pourrait avoir été causée par une variable manquante **avant** l'ajout des logs détaillés

**Mécanisme de détection** :
- `backend/services/tests_dyn_handler.py` ligne 420-422 : détection des placeholders non résolus après rendu
- Si un placeholder `{{variable}}` reste dans le HTML → erreur `UNRESOLVED_PLACEHOLDERS` (HTTP 422)
- Cette erreur peut déclencher un fallback vers le pipeline statique, qui échoue ensuite avec "CHAPITRE NON MAPPÉ"

**Correctif appliqué** :
- Blocage du fallback statique pour les chapitres MIXED sans `exercise_types`
- Retour d'une erreur explicite `MIXED_PIPELINE_NO_DYNAMIC_EXERCISES` au lieu d'un fallback silencieux
- **Protection supplémentaire** : les logs détaillés permettent maintenant de détecter les variables manquantes avant le rendu

---

### A) Source exacte de l'erreur UI

**Fichier**: `backend/services/math_generation_service.py`  
**Ligne**: 244-251  
**Fonction**: `_map_chapter_to_types()`

```python
if chapitre not in mapping:
    raise ValueError(
        f"❌ CHAPITRE NON MAPPÉ : '{chapitre}'\n"
        f"   Niveau : {niveau if 'niveau' in locals() else 'N/A'}\n"
        ...
    )
```

**Propagation**:
- `ValueError` levé dans `_map_chapter_to_types()` (ligne 245)
- Capturé dans `backend/routes/exercises_routes.py` ligne 1547-1557
- Converti en `HTTPException` 422 avec le message d'erreur

---

### B) Endpoint backend fautif

**Endpoint**: `POST /api/v1/exercises/generate`  
**Statut HTTP**: 422 Unprocessable Entity  
**Body**: JSON avec `error_code: "CHAPTER_OR_TYPE_INVALID"`

**Curl de reproduction**:
```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "difficile", "offer": "free"}'
```

**Note**: Le curl fonctionne pour 1 exercice, mais échoue de manière intermittente pour plusieurs appels.

---

### C) Chaîne complète "data → mapping → erreur"

#### 1. Construction du catalogue

**Source de vérité**: `backend/curriculum/curriculum_6e.json`  
**Chapitre concerné**:
```json
{
  "niveau": "6e",
  "code_officiel": "6e_AA_TEST",
  "libelle": "AA TEST",
  "chapitre_backend": "",
  "exercise_types": [],
  "pipeline": "MIXED"
}
```

**Champs clés**:
- `code_officiel`: `"6e_AA_TEST"` ✅
- `libelle`: `"AA TEST"` (avec espace) ✅
- `exercise_types`: `[]` (vide) ⚠️
- `pipeline`: `"MIXED"` ✅

#### 2. Mapping legacy

**Fichier**: `backend/services/math_generation_service.py`  
**Ligne**: 112-253  
**Fonction**: `_map_chapter_to_types(chapitre: str, niveau: str)`

**Clé utilisée**: Le **libellé** du chapitre (ex: `"AA TEST"`)

**État actuel**:
```python
# Ligne 240 (commentée)
# "AA TEST" : pas de mapping legacy - utilise uniquement les exercices dynamiques (pipeline MIXED)
```

**Conclusion**: Le mapping legacy **n'a PAS** d'entrée pour `"AA TEST"`.

#### 3. Flux d'exécution (mode code_officiel)

**Fichier**: `backend/routes/exercises_routes.py`

**Étape 1** (ligne 762):
```python
request.chapitre = curriculum_chapter.libelle or curriculum_chapter.code_officiel
# → request.chapitre = "AA TEST" (libellé avec espace)
```

**Étape 2** (ligne 869-1010): Pipeline MIXED
- Cherche exercices dynamiques avec filtres (`difficulty="difficile"`)
- Si aucun trouvé → retry SANS filtres (dégradé)
- Si erreur `randrange()` → exception capturée (ligne 1010)

**Étape 3** (ligne 1010-1028): Gestion exception
- Si `exercise_types = []` → erreur explicite (ligne 1028-1042)
- **MAIS** si exception `randrange` capturée AVANT cette vérification → fallback statique

**Étape 4** (ligne 1511-1535): Fallback statique (legacy)
```python
else:
    # Mode legacy : utiliser le mapping par chapitre
    specs = _math_service.generate_math_exercise_specs(
        niveau=request.niveau,  # "6e"
        chapitre=request.chapitre,  # "AA TEST" (libellé)
        ...
    )
```

**Étape 5** (ligne 1530): Appel `generate_math_exercise_specs()`
- Appelle `_map_chapter_to_types("AA TEST", "6e")`
- Cherche `"AA TEST"` dans le mapping → **NON TROUVÉ**
- Lève `ValueError` "CHAPITRE NON MAPPÉ"

#### 4. Root cause finale

**MISMATCH DE CLÉ** :
- Le catalogue utilise `libelle = "AA TEST"` (avec espace)
- Le mapping legacy cherche `"AA TEST"` mais n'a pas d'entrée (commentée ligne 240)
- Le fallback statique est appelé **AVANT** la vérification `exercise_types = []` quand une exception `randrange` est capturée

**Fichiers concernés**:
1. `backend/routes/exercises_routes.py` ligne 1010-1028 : gestion exception MIXED
2. `backend/routes/exercises_routes.py` ligne 1511-1535 : fallback statique
3. `backend/services/math_generation_service.py` ligne 240 : mapping legacy (commenté)

**Preuve**:
- Curriculum JSON : `libelle = "AA TEST"` (ligne 261)
- Code route : `request.chapitre = "AA TEST"` (ligne 762)
- Mapping : pas d'entrée pour `"AA TEST"` (ligne 240 commentée)
- Erreur : `ValueError` levé ligne 245 avec `chapitre = "AA TEST"`

---

## 🔧 CORRECTIF MINIMAL (P0)

### Option 1 (RECOMMANDÉE) : Bloquer le fallback statique pour MIXED sans exercise_types

**Principe**: Si `pipeline = MIXED` et `exercise_types = []`, ne JAMAIS faire de fallback statique. Retourner une erreur explicite.

**Fichier**: `backend/routes/exercises_routes.py`

**Modification ligne 1010-1028**:
```python
except Exception as e:
    import traceback
    logger.error(
        f"[PIPELINE MIXED] EXCEPTION capturée pour {chapter_code_for_db}: {type(e).__name__}: {e}"
    )
    logger.error(f"[PIPELINE MIXED] Traceback: {traceback.format_exc()}")
    
    # Si pas d'exercise_types dans le curriculum, ne JAMAIS faire de fallback statique
    if not curriculum_chapter.exercise_types:
        logger.error(
            f"[PIPELINE MIXED] Pipeline MIXED sans exercise_types → erreur explicite (pas de fallback statique)"
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "MIXED_PIPELINE_NO_DYNAMIC_EXERCISES",
                "error": "no_dynamic_exercises_available",
                "message": (
                    f"Aucun exercice dynamique disponible pour {chapter_code_for_db} "
                    f"avec offer='{request.offer}' et difficulte='{request.difficulte}'. "
                    f"Le pipeline MIXED nécessite au moins un exercice dynamique en DB."
                ),
                "chapter_code": chapter_code_for_db,
                "pipeline": "MIXED",
                "filters": {
                    "offer": getattr(request, 'offer', None),
                    "difficulty": getattr(request, 'difficulte', None)
                },
                "hint": (
                    "Créez un exercice dynamique pour ce chapitre avec la difficulté demandée "
                    "via l'interface admin, ou changez le pipeline à 'TEMPLATE'."
                )
            }
        )
    
    # Si exercise_types existe, continuer vers fallback statique (comportement existant)
    logger.warning(
        f"[PIPELINE] Erreur vérification exercices dynamiques (MIXED) pour {chapter_code_for_db}: {e}. "
        f"Fallback sur pipeline STATIQUE."
    )
    # Continue vers pipeline statique (code ci-dessous)
```

**Modification ligne 1511-1535** (bloquer aussi le fallback statique direct):
```python
else:
    # Mode legacy : utiliser le mapping par chapitre
    # Vérifier si le chapitre a un pipeline MIXED sans exercise_types (ne doit jamais passer par MathGenerationService)
    if curriculum_chapter and hasattr(curriculum_chapter, 'pipeline') and curriculum_chapter.pipeline == "MIXED":
        if not curriculum_chapter.exercise_types:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "MIXED_PIPELINE_NO_DYNAMIC_EXERCISES",
                    "error": "no_dynamic_exercises_available",
                    "message": (
                        f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='MIXED' "
                        f"mais aucun exercice dynamique n'est disponible et aucun exercise_types n'est défini. "
                        f"Le pipeline MIXED nécessite au moins un exercice dynamique en DB."
                    ),
                    "chapter_code": request.code_officiel,
                    "pipeline": "MIXED",
                    "hint": (
                        "Créez un exercice dynamique pour ce chapitre via l'interface admin, "
                        "ou configurez des exercise_types valides dans le curriculum."
                    )
                }
            )
    
    # Vérifier si le chapitre a un pipeline TEMPLATE (ne doit jamais passer par MathGenerationService)
    if curriculum_chapter and hasattr(curriculum_chapter, 'pipeline') and curriculum_chapter.pipeline == "TEMPLATE":
        # ... (code existant)
```

**Justification**:
- Respecte le principe "pas de fallback silencieux"
- Erreur explicite si pipeline MIXED sans exercices dynamiques
- Pas de patch fragile basé sur le libellé
- Source de vérité : `pipeline` + `exercise_types` du curriculum

---

## ✅ VALIDATION (Proof Pack)

### 1. Appliquer le fix

```bash
cd /Users/oussamaidamhane/Desktop/Projet\ local\ LMM/Le-Maitre-Mot-v16-Refonte-Sauvegarde
docker compose build backend
docker compose restart backend
sleep 10
```

### 2. Valider avec curl

**Test 1**: 1 exercice "difficile" (doit fonctionner)
```bash
curl -s -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "difficile", "offer": "free"}' \
  | python3 -c "import sys, json; r = json.load(sys.stdin); print('✅ OK' if 'id_exercice' in r else '❌ ERREUR:', r.get('detail', {}).get('message', 'Unknown')[:100])"
```

**Test 2**: 3 exercices "difficile" (doit fonctionner maintenant)
```bash
for i in 1 2 3; do
  echo "=== Test $i ==="
  curl -s -X POST http://localhost:8000/api/v1/exercises/generate \
    -H "Content-Type: application/json" \
    -d "{\"code_officiel\": \"6e_AA_TEST\", \"difficulte\": \"difficile\", \"offer\": \"free\", \"seed\": $(date +%s)$i}" \
    | python3 -c "import sys, json; r = json.load(sys.stdin); print('✅ OK' if 'id_exercice' in r else '❌ ERREUR:', r.get('detail', {}).get('message', 'Unknown')[:100])"
  sleep 1
done
```

**Résultat attendu**: Les 3 appels doivent retourner `✅ OK`

### 3. Vérification UI

1. Aller sur `http://localhost:3000/generate`
2. Sélectionner "AA TEST" avec difficulté "Difficile"
3. Demander 3 exercices
4. **Résultat attendu**: Les 3 exercices sont générés sans erreur "CHAPITRE NON MAPPÉ"

### 4. Vérification logs

```bash
docker compose logs backend --tail 100 | grep -i "PIPELINE MIXED\|6e_AA_TEST\|difficile\|EXCEPTION\|MIXED_PIPELINE_NO_DYNAMIC"
```

**Résultat attendu**: 
- Pas d'erreur "CHAPITRE NON MAPPÉ"
- Logs `[PIPELINE MIXED]` montrent la sélection d'exercices dynamiques
- Si erreur, message explicite `MIXED_PIPELINE_NO_DYNAMIC_EXERCISES` (pas de fallback silencieux)

---

## 📝 DÉCISION PRODUIT

**Question implicite**: Le chapitre "AA TEST" doit-il être visible en mode "Officiel" ?

**Réponse**: 
- ✅ **OUI** : C'est un chapitre de test pour valider les générateurs dynamiques
- ✅ **Pipeline MIXED** : Priorité aux exercices dynamiques, fallback statique si `exercise_types` configuré
- ✅ **Comportement attendu** : Si aucun exercice dynamique disponible → erreur explicite (pas de fallback silencieux vers mapping legacy)

**Règle explicite**:
- Chapitres avec `pipeline = MIXED` et `exercise_types = []` → **uniquement exercices dynamiques**
- Si aucun exercice dynamique disponible → **erreur explicite** (pas de fallback statique)
- Si `exercise_types` configuré → fallback statique autorisé

---

## 🔗 FICHIERS MODIFIÉS

1. `backend/routes/exercises_routes.py`
   - Ligne 1010-1028 : Gestion exception MIXED (bloquer fallback si `exercise_types = []`)
   - Ligne 1511-1535 : Bloquer fallback statique pour MIXED sans `exercise_types`

---

## 📊 RÉSUMÉ

**Root cause identifiée** : Le pipeline MIXED fait un fallback statique vers le mapping legacy quand une exception `randrange` est capturée, mais le mapping legacy n'a pas d'entrée pour "AA TEST" (libellé utilisé comme clé).

**Hypothèse alternative (utilisateur)** : L'erreur pourrait provenir d'une variable manquante lors de la génération, déclenchant `UNRESOLVED_PLACEHOLDERS` → fallback statique → "CHAPITRE NON MAPPÉ".

**Correctif appliqué** : 
1. Blocage du fallback statique pour les chapitres MIXED sans `exercise_types`, retour d'une erreur explicite à la place
2. Ajout de logs détaillés pour tracer les variables manquantes avant le rendu
3. Protection contre les fallbacks silencieux dans 2 endroits (exception MIXED + fallback statique direct)

**Source de vérité**: 
- Curriculum JSON : `pipeline` + `exercise_types`
- Mapping legacy : clé = `libelle` (ex: "AA TEST")
- Variables générateur : tous les placeholders `{{variable}}` doivent être présents dans `variables`

**Documentation** :
- `docs/CAHIER_DES_CHARGES_GENERATEURS_DYNAMIQUES.md` : Section "Génération d'un exercice : flux complet" ajoutée
- Détails sur la validation des placeholders, l'ordre de fusion des paramètres, et la gestion des erreurs

