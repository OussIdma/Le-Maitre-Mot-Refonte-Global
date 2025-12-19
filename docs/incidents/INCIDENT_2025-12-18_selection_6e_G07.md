## INCIDENT – Sélection d'exercice pour 6e_G07 (Symétrie) non alignée sur le pool attendu

### 1. Métadonnées

- **ID incident** : `INCIDENT_2025-12-18_selection_6e_G07`
- **Date** : 2025-12-18
- **Chapitre** : `6e_G07` – Symétrie axiale
- **Environnement** : local (backend Docker, `/api/v1/exercises/generate`)
- **Gravité** : P2 (cohérence pédagogique / sélection de générateur)

### 2. Symptôme

- **Requête élève** :  
  `POST /api/v1/exercises/generate` avec `{"code_officiel":"6e_G07","difficulte":"difficile","seed":12345}`.
- **Comportement attendu** (selon la configuration métier) :  
  sélection dans un pool purement "symétrie axiale" (aucun générateur de type THALES ou d'un autre chapitre).
- **Comportement observé (build courant)** :  
  - pipeline utilisé : génération legacy via `MathGenerationService` avec types `[SYMETRIE_AXIALE, SYMETRIE_PROPRIETES]` (logs).  
  - l'exercice retourné est de type `MathExerciseType.SYMETRIE_AXIALE` ou `SYMETRIE_PROPRIETES` (pas THALES dans ce build), mais **la sélection des types n'est pas liée au seed** et **n'est pas pilotée par le pool admin de générateurs (Factory)**.

### 3. Reproduction (backend local)

```bash
curl -v "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_G07","difficulte":"difficile","seed":12345}'
```

**Réponse JSON (extrait)** :

```json
{
  "id_exercice": "ex_6e_sym-trie-axiale_1766063247",
  "niveau": "6e",
  "chapitre": "Symétrie axiale",
  "metadata": {
    "difficulte": "difficile",
    "domaine": "Espace et géométrie",
    "has_figure": false,
    "is_fallback": false,
    "generator_code": "6e_SYMETRIE_PROPRIETES",
    "offer": "free"
  }
}
```

Logs associés :

```text
[INFO][lemaitremot][] Types d'exercices filtrés pour 6e_G07 (offer=free): ['SYMETRIE_AXIALE', 'SYMETRIE_PROPRIETES']
[INFO][lemaitremot][] Génération exercice (mode officiel): code=6e_G07, chapitre_backend=Symétrie axiale, exercise_types=['SYMETRIE_AXIALE', 'SYMETRIE_PROPRIETES']
[INFO][lemaitremot][] Exercice généré: type=MathExerciseType.SYMETRIE_PROPRIETES, has_figure=False
```

### 4. Root cause

- **Fichiers analysés** :
  - `backend/routes/exercises_routes.py`
  - `backend/services/math_generation_service.py`
  - `backend/models/math_models.py`
  - `backend/curriculum/curriculum_6e.json`
  - `docs/INVESTIGATION_SELECTION_POOL.md`

- **Source de vérité actuelle pour 6e_G07** :  
  `backend/curriculum/curriculum_6e.json` déclare :

  ```json
  {
    "code_officiel": "6e_G07",
    "chapitre_backend": "Symétrie axiale",
    "exercise_types": ["SYMETRIE_AXIALE", "SYMETRIE_PROPRIETES"]
  }
  ```

- **Pipeline réel** :
  1. `exercises_routes.generate_exercise` détecte le mode "code_officiel".
  2. `get_chapter_by_official_code("6e_G07")` renvoie le chapitre ci-dessus.
  3. Les `exercise_types` sont convertis en `MathExerciseType` via :

     ```python
     exercise_types_override = [
       MathExerciseType[et] for et in filtered_types
       if hasattr(MathExerciseType, et)
     ]
     ```

  4. `MathGenerationService.generate_math_exercise_specs_with_types()` est appelé avec ces types.

- **Incohérence métier potentielle** :
  - Côté admin, le "pool" de générateurs peut être configuré avec des clés **Factory** (`THALES_V2`, `SYMETRIE_AXIALE_V2`, etc.).
  - Si l’admin configure `exercise_types` avec des clés **non connues** de `MathExerciseType` (ex. `SYMETRIE_AXIALE_V2`), le code actuel :
    - filtre silencieusement ces types (car `hasattr(MathExerciseType, et)` est `False`),
    - peut se retrouver avec `exercise_types_override` vide,
    - et **retomber silencieusement** sur le mapping legacy `_map_chapter_to_types(chapitre_backend)` qui n’a aucun lien avec le pool admin (et pourrait, dans d’autres chapitres, contenir THALES ou d’autres générateurs non souhaités).

**Root cause** :  
La conversion `exercise_types` → `MathExerciseType` ignore silencieusement les types inconnus et autorise un **fallback implicite** vers le mapping legacy, ce qui découple la sélection élève du pool métier/admin et ouvre la porte à des générateurs inattendus (THALES, autres types hérités) si la config curriculum/admin utilise des noms de générateurs Factory non encore pris en charge côté `MathExerciseType`.

### 5. Fix appliqué

- **Fichier modifié** : `backend/routes/exercises_routes.py`
- **Changement** : conversion **stricte** des `exercise_types` du curriculum :

  - Séparation en deux listes :
    - `valid_types` : noms présents dans `MathExerciseType`.
    - `invalid_types` : noms inconnus.
  - Comportement :
    - Si `valid_types` non vide et `invalid_types` non vide :
      - log d’un **warning explicite** listant les types inconnus ;
      - poursuite avec les types valides uniquement.
    - Si `filtered_types` non vide mais `valid_types` vide (tous les types inconnus) :
      - **levée d’un `HTTPException(422)`** avec :
        - `error_code = "INVALID_CURRICULUM_EXERCISE_TYPES"`
        - détail : `chapter_code`, `exercise_types_configured`, hint pour corriger `MathExerciseType` / `curriculum_6e`.
      - **AUCUN fallback** vers `_map_chapter_to_types`.

Extrait du nouveau code :

```startLine:endLine:backend/routes/exercises_routes.py
valid_types = []
invalid_types = []
for et in filtered_types:
    if hasattr(MathExerciseType, et):
        valid_types.append(MathExerciseType[et])
    else:
        invalid_types.append(et)

exercise_types_override = valid_types

if filtered_types and not valid_types:
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "INVALID_CURRICULUM_EXERCISE_TYPES",
            "error": "invalid_exercise_types",
            "message": (
                f"Les exercise_types configurés pour le chapitre "
                f"'{request.code_officiel}' ne correspondent à aucun "
                f"MathExerciseType connu: {filtered_types}."
            ),
            "chapter_code": request.code_officiel,
            "exercise_types_configured": filtered_types,
            "hint": (
                "Ajoutez ces types dans MathExerciseType ou corrigez "
                "le référentiel curriculum_6e."
            ),
        },
    )
```

### 6. Tests

#### 6.1 Test de non-régression 6e_G07 (build actuel)

```bash
curl -s -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_G07","difficulte":"difficile","seed":12345}' | jq .
```

**Attendu** :
- `status HTTP 200` ;
- `metadata.generator_code` appartient à la famille SYMETRIE (`6e_SYMETRIE_AXIALE` ou `6e_SYMETRIE_PROPRIETES`) ;
- aucun THALES ni autre chapitre étranger ;
- comportement identique à avant fix pour les noms de types déjà valides.

#### 6.2 Test de garde-fou sur types inconnus

1. Modifier temporairement `backend/curriculum/curriculum_6e.json` pour mettre :

   ```json
   "exercise_types": ["SYMETRIE_AXIALE_V2"]
   ```

2. Redémarrer le backend, puis :

   ```bash
   curl -s -X POST "http://localhost:8000/api/v1/exercises/generate" \
     -H "Content-Type: application/json" \
     -d '{"code_officiel":"6e_G07","difficulte":"difficile","seed":12345}' | jq .
   ```

**Attendu** :
- `status HTTP 422` ;
- `error_code = "INVALID_CURRICULUM_EXERCISE_TYPES"` ;
- `detail.exercise_types_configured = ["SYMETRIE_AXIALE_V2"]` ;
- message expliquant que ces types ne sont pas connus dans `MathExerciseType`.

### 7. Risques résiduels & pistes

- **Seed** : la sélection du type d’exercice (`SYMETRIE_AXIALE` vs `SYMETRIE_PROPRIETES`) par `MathGenerationService` reste pilotée par le `random` interne et **n’exploite pas encore `request.seed`** — ce point reste à adresser pour une déterminisme complet par seed pour tous les chapitres legacy.
- **Factory vs legacy** : ce fix empêche le fallback silencieux vers le mapping legacy lorsque le curriculum est configuré avec des types purement “Factory” (ex. `*_V2`), mais il n’intègre pas encore ces générateurs Factory dans `/api/v1/exercises/generate`. Une migration progressive sera nécessaire pour brancher certains chapitres (comme 6e_G07) sur les générateurs Factory (SYMETRIE_AXIALE_V2) de façon contrôlée.
- **Admin vs élève** : l’admin peut continuer à configurer des types ou générateurs qui ne sont pas encore reconnus côté élève ; désormais, l’erreur est explicite côté API au lieu de retomber sur un autre générateur, mais une UX d’administration devra aider à valider les types disponibles.




