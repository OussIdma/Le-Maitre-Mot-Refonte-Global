# Analyse v2 : Généralisation des template_variants (Allowlist + Capability DB)

**Date** : 2025-12-18  
**Contexte** : Variants OK sur pilote `6e_TESTS_DYN`. Mission : généraliser avec allowlist explicite (pas de détection implicite).

---

## 1. Liste des chapitres dynamiques existants

### 1.1 Dynamiques template-based (CANDIDATS variants) ✅

| Chapitre | Code officiel | Pipeline | Source données | Compatible variants |
|----------|---------------|----------|----------------|---------------------|
| **TESTS_DYN** | `6e_TESTS_DYN` | Handler dédié (`tests_dyn_handler.py`) | `tests_dyn_exercises.py` → MongoDB | ✅ **OUI** (pilote fonctionnel) |

**Caractéristiques** :
- ✅ Utilise `enonce_template_html` / `solution_template_html` avec placeholders `{{variable}}`
- ✅ Appelle un générateur (`generator_key`) pour obtenir les variables
- ✅ Rend les templates via `render_template()`
- ✅ Garde anti-{{...}} en place

**Fichiers clés** :
- `backend/services/tests_dyn_handler.py::format_dynamic_exercise()` (lignes 77-330)
- `backend/data/tests_dyn_exercises.py` : templates avec `is_dynamic=True` + `generator_key`

---

### 1.2 Dynamiques legacy/spec-based (EXCLUS variants) ❌

| Chapitre | Code officiel | Pipeline | Source données | Compatible variants |
|----------|---------------|----------|----------------|---------------------|
| **Tous autres** | `6e_G07`, `6e_N08`, etc. | `MathGenerationService` | Référentiel curriculum | ❌ **NON** (spec-based) |

**Caractéristiques** :
- ❌ Génère des **specs structurées** (`MathExerciseSpec`) directement
- ❌ Pas de templates HTML avec placeholders
- ❌ Conversion specs → HTML final (pas de rendu template)
- ❌ Refonte majeure nécessaire pour supporter variants

**Fichiers clés** :
- `backend/services/math_generation_service.py` : génère des specs
- `backend/routes/exercises_routes.py` (lignes 738-1086) : pipeline principal

**Exemples de chapitres** :
- `6e_G07` (Symétrie axiale) : `_gen_symetrie_axiale()` → spec → HTML
- `6e_N08` (Fractions) : `_gen_calcul_fractions()` → spec → HTML
- Tous les chapitres via `code_officiel` (sauf GM07/GM08/TESTS_DYN)

---

### 1.3 Statiques (INTOUCHABLES) 🔒

| Chapitre | Code officiel | Pipeline | Compatible variants |
|----------|---------------|----------|---------------------|
| **GM07** | `6e_GM07` | Handler statique (`gm07_handler.py`) | ❌ Statique (zéro impact) |
| **GM08** | `6e_GM08` | Handler statique (`gm08_handler.py`) | ❌ Statique (zéro impact) |

**Caractéristiques** :
- Exercices **figés** (HTML statique, pas de templates)
- **Zéro impact** pour la généralisation des variants

---

## 2. Pourquoi `6e_TESTS_DYN` est compatible (analyse précise)

### 2.1 Pipeline complet

**Point d'entrée API** :
- `POST /api/v1/exercises/generate` avec `code_officiel="6e_TESTS_DYN"`

**Fichiers impliqués** :
- `backend/routes/exercises_routes.py` (lignes 688-736) : intercept `is_tests_dyn_request()`
- `backend/services/tests_dyn_handler.py` :
  - `generate_tests_dyn_exercise()` (ligne 333) : sélection template + appel format
  - `format_dynamic_exercise()` (ligne 77) : **CŒUR DU PIPELINE**

**Workflow détaillé** :

```
1. Intercept dans exercises_routes.py
   └─> is_tests_dyn_request(code_officiel="6e_TESTS_DYN") → True
   └─> generate_tests_dyn_exercise(offer, difficulty, seed)
       └─> get_random_tests_dyn_exercise() : sélection template (seed-based)
       └─> format_dynamic_exercise(template, timestamp, seed)

2. format_dynamic_exercise() (tests_dyn_handler.py:77)
   ├─> Calcul stable_key (ligne 207)
   │   └─> exercise_template.get("stable_key") or f"6E_TESTS_DYN:{id}"
   ├─> Sélection variant (lignes 209-243)
   │   ├─> Si template_variants non vide :
   │   │   └─> choose_template_variant(variants, seed, stable_key)
   │   │       └─> Hash SHA256(stable_key:seed) → sélection pondérée
   │   └─> Sinon : fallback legacy enonce_template_html/solution_template_html
   ├─> Appel générateur (lignes 108-112)
   │   └─> generate_dynamic_exercise(generator_key, seed, difficulty)
   │       └─> Retourne variables + SVG
   ├─> Mappings alias (lignes 136-200)
   │   └─> triangle/rectangle/carré → aliases compatibles
   ├─> Render templates (lignes 263-264)
   │   └─> render_template(enonce_template, all_vars)
   │   └─> render_template(solution_template, all_vars)
   └─> Garde anti-{{...}} (lignes 269-299)
       └─> Regex → détecte {{...}} résiduels
       └─> Si détecté → HTTPException(422) UNRESOLVED_PLACEHOLDERS
```

### 2.2 Points d'entrée clés

**1. Sélection de variant** :
- **Fichier** : `backend/services/tests_dyn_handler.py` (lignes 202-243)
- **Fonction** : `choose_template_variant()` depuis `dynamic_exercise_engine.py`
- **Input** : `template_variants[]`, `seed`, `stable_key`
- **Output** : variant choisi (déterministe)

**2. Rendu des templates** :
- **Fichier** : `backend/services/tests_dyn_handler.py` (lignes 263-264)
- **Service** : `backend/services/template_renderer.py::render_template()`
- **Input** : template HTML + variables dict
- **Output** : HTML final (placeholders remplacés)

**3. Garde anti-{{...}}** :
- **Fichier** : `backend/services/tests_dyn_handler.py` (lignes 269-299)
- **Méthode** : Regex `r"\{\{\s*(\w+)\s*\}\}"`
- **Action** : Si détecté → `HTTPException(422)` avec `error_code="UNRESOLVED_PLACEHOLDERS"`

---

## 3. Stratégie MINIMALE et SAFE (allowlist + capability DB)

### 3.1 Phase A : Allowlist explicite (feature flag)

**Principe** :
- Liste blanche explicite de chapitres autorisés pour les variants
- Feature flag dans le code (pas de détection automatique)
- Contrôle total sur l'activation

**Implémentation proposée** :

```python
# backend/config/variants_config.py (NOUVEAU)
"""
Configuration explicite des chapitres autorisés pour template_variants.
Feature flag : allowlist stricte (pas de détection automatique).
"""

# Allowlist explicite (feature flag)
VARIANTS_ALLOWED_CHAPTERS: Set[str] = {
    "6E_TESTS_DYN",  # Pilote (déjà fonctionnel)
    # Ajouter ici les futurs chapitres validés manuellement
    # Exemple : "6E_G07" (si validé après tests)
}

def is_variants_allowed(chapter_code: str) -> bool:
    """
    Vérifie si un chapitre est autorisé pour les template_variants.
    
    Args:
        chapter_code: Code du chapitre (ex: "6e_TESTS_DYN")
    
    Returns:
        True si le chapitre est dans l'allowlist
    """
    return chapter_code.upper() in VARIANTS_ALLOWED_CHAPTERS
```

**Intégration dans le pipeline** :

```python
# backend/services/tests_dyn_handler.py (MODIFIÉ)
from backend.config.variants_config import is_variants_allowed

def format_dynamic_exercise(...):
    # ...
    # Sélection variant (lignes 209-243)
    chapter_code = exercise_template.get("chapter_code") or "6E_TESTS_DYN"
    
    # Vérification allowlist explicite
    if template_variants and not is_variants_allowed(chapter_code):
        # Erreur explicite si chapitre non autorisé
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "VARIANTS_NOT_ALLOWED",
                "error": "variants_not_allowed",
                "message": f"Les template_variants ne sont pas autorisés pour le chapitre '{chapter_code}'.",
                "chapter_code": chapter_code,
                "allowed_chapters": list(VARIANTS_ALLOWED_CHAPTERS),
                "hint": "Contactez l'équipe technique pour activer les variants sur ce chapitre."
            }
        )
    
    # Suite du traitement (variants OK)
    if template_variants:
        # ... choose_template_variant() ...
```

**Avantages** :
- ✅ **Contrôle total** : activation manuelle par chapitre
- ✅ **Sécurité** : pas de détection implicite (zéro surprise)
- ✅ **Traçabilité** : liste explicite dans le code
- ✅ **Rollback facile** : retirer un chapitre de l'allowlist

---

### 3.2 Phase B (option) : Capability explicite en DB

**Principe** :
- Champ DB `supports_template_variants: bool` sur chaque exercice
- Vérification explicite avant traitement des variants
- Complément à l'allowlist (double sécurité)

**Modèle Pydantic** :

```python
# backend/services/exercise_persistence_service.py (MODIFIÉ)
class ExerciseCreateRequest(BaseModel):
    # ... champs existants ...
    supports_template_variants: Optional[bool] = Field(
        default=False,
        description=(
            "Capability explicite : cet exercice supporte les template_variants. "
            "Doit être True ET chapitre dans allowlist pour activer les variants."
        )
    )
```

**Schéma MongoDB** :
```json
{
  "chapter_code": "6E_TESTS_DYN",
  "id": 1,
  "is_dynamic": true,
  "generator_key": "THALES_V1",
  "supports_template_variants": true,  // ← NOUVEAU
  "template_variants": [...]
}
```

**Validation dans le handler** :

```python
# backend/services/tests_dyn_handler.py (MODIFIÉ)
def format_dynamic_exercise(...):
    # ...
    chapter_code = exercise_template.get("chapter_code") or "6E_TESTS_DYN"
    supports_variants = exercise_template.get("supports_template_variants", False)
    template_variants = exercise_template.get("template_variants") or []
    
    # Double vérification : allowlist + capability DB
    if template_variants:
        if not is_variants_allowed(chapter_code):
            raise HTTPException(422, detail={"error_code": "VARIANTS_NOT_ALLOWED", ...})
        
        if not supports_variants:
            raise HTTPException(
                422,
                detail={
                    "error_code": "VARIANTS_NOT_SUPPORTED",
                    "error": "variants_not_supported",
                    "message": f"L'exercice {exercise_template.get('id')} n'a pas la capability 'supports_template_variants' activée.",
                    "hint": "Activez 'supports_template_variants' dans l'admin pour utiliser les variants."
                }
            )
    
    # Suite du traitement (variants OK)
    if template_variants:
        # ... choose_template_variant() ...
```

**Avantages** :
- ✅ **Double sécurité** : allowlist + capability DB
- ✅ **Granularité** : contrôle par exercice (pas seulement par chapitre)
- ✅ **Migration progressive** : activer exercice par exercice

**Inconvénients** :
- ⚠️ **Complexité** : deux niveaux de vérification
- ⚠️ **Maintenance** : champ DB à gérer

**Recommandation** : **Phase A uniquement** pour commencer (allowlist suffisante). Phase B si besoin de granularité exercice par exercice.

---

## 4. Source du stable_key

### 4.1 Règle actuelle (TESTS_DYN)

**Fichier** : `backend/services/tests_dyn_handler.py` (ligne 207)

```python
stable_key = exercise_template.get("stable_key") or f"6E_TESTS_DYN:{exercise_template.get('id')}"
```

**Logique** :
1. Si `exercise_template["stable_key"]` existe → utiliser tel quel
2. Sinon → calculer `"{chapter_code}:{id}"`

### 4.2 Recommandation pour généralisation

**Option 1 : Champ DB dédié (RECOMMANDÉ)** ✅

```python
# Schéma MongoDB
{
  "chapter_code": "6E_TESTS_DYN",
  "id": 1,
  "stable_key": "6E_TESTS_DYN:1",  // ← Champ dédié (optionnel)
  ...
}
```

**Règle de calcul** :
```python
# backend/services/tests_dyn_handler.py (MODIFIÉ)
def format_dynamic_exercise(...):
    # ...
    # Calcul stable_key (priorité : champ DB > règle métier)
    stable_key = (
        exercise_template.get("stable_key")  # 1. Champ DB explicite
        or f"{chapter_code}:{exercise_template.get('id')}"  # 2. Règle métier
    )
```

**Avantages** :
- ✅ **Flexibilité** : override possible si besoin
- ✅ **Traçabilité** : champ explicite en DB
- ✅ **Compatibilité** : fallback automatique si absent

**Option 2 : Règle métier uniquement (ALTERNATIVE)**

```python
# Toujours calculer (pas de champ DB)
stable_key = f"{chapter_code}:{exercise_template.get('id')}"
```

**Avantages** :
- ✅ **Simplicité** : pas de champ DB à gérer
- ✅ **Cohérence** : même règle partout

**Inconvénients** :
- ❌ **Rigidité** : pas d'override possible

**Recommandation** : **Option 1** (champ DB + fallback règle métier) pour flexibilité future.

---

## 5. Risques + garde-fous

### 5.1 Risques identifiés

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| **Seed non déterministe** | 🔴 Bloquant | Faible | Utiliser `seed` tel quel (SHA256) |
| **Placeholders non résolus** | 🔴 Bloquant | Moyen | Garde anti-{{...}} obligatoire |
| **Chapitre non autorisé utilise variants** | 🟡 Erreur utilisateur | Moyen | Allowlist + erreur JSON explicite |
| **Fallback silencieux vers legacy** | 🟡 Régression | Faible | Erreur JSON si variants présents mais non autorisés |
| **Générateur inconnu** | 🟡 Erreur utilisateur | Faible | Erreur JSON `GENERATOR_NOT_FOUND` |
| **Régression GM07/GM08** | 🔴 Bloquant | Faible | Intercepts en priorité absolue |
| **Régression TESTS_DYN** | 🔴 Bloquant | Faible | Tests non-régression obligatoires |

### 5.2 Garde-fous obligatoires

**1. Déterminisme seed** :
- ✅ Utiliser `seed` tel quel (pas de `random.seed()` global)
- ✅ `choose_template_variant()` utilise SHA256 (déterministe)
- ✅ Même seed + même chapitre + même exercice = même variant

**2. Zéro placeholder résiduel** :
- ✅ Garde anti-{{...}} **obligatoire** dans `format_dynamic_exercise()`
- ✅ Erreur JSON `UNRESOLVED_PLACEHOLDERS` si détecté
- ✅ Regex : `r"\{\{\s*(\w+)\s*\}\}"`

**3. Erreurs JSON-safe** :
- ✅ Toutes les erreurs via `HTTPException` (FastAPI)
- ✅ Handler global dans `server.py` (déjà en place)
- ✅ Codes d'erreur explicites : `VARIANTS_NOT_ALLOWED`, `VARIANTS_NOT_SUPPORTED`, etc.

**4. Pas de fallback silencieux** :
- ✅ Si `template_variants` présents mais chapitre non autorisé → erreur `VARIANTS_NOT_ALLOWED`
- ✅ Si `template_variants` présents mais `supports_template_variants=False` → erreur `VARIANTS_NOT_SUPPORTED`
- ✅ Si générateur inconnu → erreur `GENERATOR_NOT_FOUND`

**5. Non-régression GM07/GM08/TESTS_DYN** :
- ✅ Intercepts en **priorité absolue** (avant allowlist)
- ✅ Tests non-régression obligatoires
- ✅ Script seeds : 30 seeds fixes → vérifier déterminisme

---

## 6. Plan d'implémentation (3 étapes max)

### Étape 1 : Allowlist explicite + intégration handler

**Objectif** : Créer l'allowlist et l'intégrer dans `format_dynamic_exercise()`.

**Fichiers** :
- `backend/config/variants_config.py` (NOUVEAU)
  - `VARIANTS_ALLOWED_CHAPTERS: Set[str] = {"6E_TESTS_DYN"}`
  - `is_variants_allowed(chapter_code: str) -> bool`
- `backend/services/tests_dyn_handler.py` (MODIFIÉ)
  - Import `is_variants_allowed`
  - Vérification allowlist avant traitement variants (ligne ~209)
  - Erreur JSON `VARIANTS_NOT_ALLOWED` si chapitre non autorisé

**Tests** :
- ✅ Test unitaire : `is_variants_allowed("6E_TESTS_DYN")` → True
- ✅ Test unitaire : `is_variants_allowed("6E_G07")` → False
- ✅ Test non-régression : `6e_TESTS_DYN` fonctionne toujours (seed fixe → même variant)

**Livrables** :
- Fichier `variants_config.py`
- Modifications `tests_dyn_handler.py`
- Tests unitaires
- Incident `INCIDENT_YYYY-MM-DD_template_variants_allowlist.md`

---

### Étape 2 : Handler générique pour autres chapitres (optionnel)

**Objectif** : Factoriser `format_dynamic_exercise()` pour réutilisation sur autres chapitres.

**Fichiers** :
- `backend/services/dynamic_exercise_handler.py` (NOUVEAU)
  - `format_dynamic_exercise_generic(exercise_template, seed, chapter_code)`
    - Copie logique de `format_dynamic_exercise()` (variants + render + guard)
    - Paramètre `chapter_code` pour calcul `stable_key`
    - Vérification allowlist intégrée
- `backend/services/tests_dyn_handler.py` (MODIFIÉ)
  - `format_dynamic_exercise()` appelle `format_dynamic_exercise_generic()`
  - Conserve compatibilité (même signature publique)

**Tests** :
- ✅ Tests unitaires sur `format_dynamic_exercise_generic()` (variants, legacy, guard)
- ✅ Test non-régression `6e_TESTS_DYN` (même seed → même résultat)

**Livrables** :
- Fichier `dynamic_exercise_handler.py`
- Modifications `tests_dyn_handler.py`
- Tests unitaires
- Incident `INCIDENT_YYYY-MM-DD_template_variants_handler_generic.md`

**Note** : Cette étape est **optionnelle** si on reste uniquement sur `6e_TESTS_DYN` pour l'instant.

---

### Étape 3 : Activation d'un nouveau chapitre (exemple)

**Objectif** : Activer les variants sur un nouveau chapitre (ex: `6e_G07` avec exercices dynamiques).

**Prérequis** :
- Chapitre doit avoir des exercices dynamiques template-based en MongoDB
- Exercices doivent avoir `is_dynamic=True` + `generator_key` + `enonce_template_html`

**Actions** :
1. Ajouter le chapitre dans l'allowlist :
   ```python
   # backend/config/variants_config.py
   VARIANTS_ALLOWED_CHAPTERS: Set[str] = {
       "6E_TESTS_DYN",
       "6E_G07",  # ← NOUVEAU
   }
   ```
2. Créer un handler dédié (ou réutiliser handler générique si Étape 2 faite)
3. Intégrer dans `exercises_routes.py` (après intercepts GM07/GM08/TESTS_DYN)

**Tests** :
- ✅ Test manuel : créer un exercice dynamique avec variants dans MongoDB (`6e_G07`)
- ✅ Test API : `curl` avec `code_officiel=6e_G07` → vérifier que variants fonctionnent
- ✅ Test non-régression : GM07 statique non impacté (intercept en priorité)

**Livrables** :
- Modifications `variants_config.py` + handler
- Tests manuels + API
- Incident `INCIDENT_YYYY-MM-DD_template_variants_activation_G07.md`

---

## 7. Checklist de validation

### Avant implémentation
- [ ] Validation de la stratégie (allowlist vs détection automatique)
- [ ] Validation du plan 3 étapes
- [ ] Choix : Phase B (capability DB) ou Phase A uniquement

### Après Étape 1
- [ ] `variants_config.py` créé avec allowlist
- [ ] Vérification allowlist dans `format_dynamic_exercise()`
- [ ] Tests unitaires passent
- [ ] `6e_TESTS_DYN` fonctionne toujours (non-régression)

### Après Étape 2 (optionnel)
- [ ] `format_dynamic_exercise_generic()` factorisé
- [ ] Tests unitaires passent
- [ ] `6e_TESTS_DYN` fonctionne toujours (non-régression)

### Après Étape 3
- [ ] Nouveau chapitre dans allowlist
- [ ] Handler intégré dans pipeline
- [ ] Exercice dynamique avec variants → généré correctement
- [ ] GM07/GM08 non impactés (tests non-régression)

---

## 8. Fichiers cités (références)

### Backend
- `backend/routes/exercises_routes.py` : point d'entrée API, intercepts GM07/GM08/TESTS_DYN
- `backend/services/tests_dyn_handler.py` : handler pilote `6e_TESTS_DYN` (variants intégrés)
  - `format_dynamic_exercise()` (lignes 77-330) : cœur du pipeline
  - `stable_key` calcul (ligne 207)
  - Sélection variant (lignes 209-243)
  - Garde anti-{{...}} (lignes 269-299)
- `backend/services/dynamic_exercise_engine.py` : moteur de sélection de variant (`choose_template_variant`)
- `backend/services/template_renderer.py` : rendu des templates (`render_template`)
- `backend/services/math_generation_service.py` : pipeline legacy (specs structurées, pas de templates)
- `backend/services/exercise_persistence_service.py` : CRUD MongoDB, modèles Pydantic (`TemplateVariant`)
- `backend/data/tests_dyn_exercises.py` : source de données pilote (templates Python)

### Frontend (non impacté pour l'instant)
- `frontend/src/components/admin/ChapterExercisesAdminPage.js` : UI admin (variants déjà supportés)
- `frontend/src/lib/adminApi.js` : API client admin

---

## 9. Recommandations finales

### Stratégie recommandée : **Phase A uniquement** (allowlist)

**Justification** :
- ✅ **Suffisant** : contrôle total par chapitre
- ✅ **Simple** : pas de champ DB supplémentaire
- ✅ **Sécurisé** : pas de détection implicite
- ✅ **Évolutif** : Phase B possible si besoin granularité exercice

### Source stable_key : **Champ DB + fallback règle métier**

**Justification** :
- ✅ **Flexibilité** : override possible si besoin
- ✅ **Compatibilité** : fallback automatique si absent
- ✅ **Traçabilité** : champ explicite en DB

### Plan d'implémentation : **Étape 1 obligatoire, Étape 2 optionnelle**

**Justification** :
- Étape 1 : **Obligatoire** pour sécuriser l'allowlist
- Étape 2 : **Optionnelle** (factorisation utile si plusieurs chapitres)
- Étape 3 : **À la demande** (activation progressive)

---

**FIN DE L'ANALYSE V2**

**Prochaine étape** : Validation de la stratégie (allowlist explicite) avant implémentation.



