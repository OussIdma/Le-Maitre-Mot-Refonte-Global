# Analyse : Généralisation des template_variants à d'autres chapitres dynamiques

**Date** : 2025-12-18  
**Contexte** : Variants OK sur pilote `6e_TESTS_DYN`. Mission : généraliser sans régression.

---

## 1. Cartographie des pipelines élèves "dynamiques" existants

### 1.1 Pipeline `6e_TESTS_DYN` (PILOTE — fonctionne avec variants)

**Point d'entrée API** :
- `POST /api/v1/exercises/generate` avec `code_officiel="6e_TESTS_DYN"`

**Fichiers impliqués** :
- `backend/routes/exercises_routes.py` (lignes 688-736) : intercept `is_tests_dyn_request()`
- `backend/services/tests_dyn_handler.py` :
  - `is_tests_dyn_request()` (ligne 40) : détection du chapitre
  - `generate_tests_dyn_exercise()` (ligne 333) : sélection template + génération
  - `format_dynamic_exercise()` (ligne 77) : **CŒUR DU PIPELINE** (variants + render + guard)
- `backend/data/tests_dyn_exercises.py` : source de données (templates en Python)

**Workflow** :
1. `generate_tests_dyn_exercise()` sélectionne un template via `get_random_tests_dyn_exercise()` (seed-based)
2. `format_dynamic_exercise()` :
   - Calcule `stable_key = "6E_TESTS_DYN:{id}"` (ligne 207)
   - Si `template_variants` non vide → `choose_template_variant()` (lignes 209-243)
   - Sinon → fallback legacy `enonce_template_html`/`solution_template_html`
   - Appelle le générateur (`generator_key`) pour obtenir les variables
   - Applique les mappings d'alias (triangle/rectangle/carré)
   - Rend les templates avec `render_template()`
   - **Garde anti-{{...}}** (lignes 269-299) : lève `HTTPException(422)` si placeholders résiduels

### 1.2 Pipeline `MathGenerationService` (LEGACY — pas de variants)

**Point d'entrée API** :
- `POST /api/v1/exercises/generate` avec `code_officiel` (ex: `6e_G07`, `6e_N08`, etc.)

**Fichiers impliqués** :
- `backend/routes/exercises_routes.py` (lignes 738-1086) : résolution `code_officiel` → `curriculum_chapter`
- `backend/services/math_generation_service.py` :
  - `generate_math_exercise_specs()` (ligne 34) : génère des `MathExerciseSpec` structurées
  - `_generate_spec_by_type()` (ligne 253) : appelle des générateurs spécifiques (`_gen_symetrie_axiale`, `_gen_thales`, etc.)
- `backend/services/geometry_render_service.py` : génère les SVG depuis les specs

**Workflow** :
1. Résolution `code_officiel` → `curriculum_chapter` (référentiel)
2. Extraction `exercise_types` depuis le curriculum
3. `MathGenerationService` génère des **specs structurées** (pas de templates HTML)
4. Conversion specs → HTML énoncé/solution (via `_convert_math_spec_to_question()` dans `exercise_template_service.py`)
5. Génération SVG depuis les specs géométriques

**⚠️ IMPORTANT** : Ce pipeline **ne génère PAS de templates avec placeholders**. Il produit directement des énoncés HTML finaux. **Pas de variants possibles ici sans refonte majeure**.

### 1.3 Pipelines statiques (GM07/GM08)

**Fichiers** :
- `backend/services/gm07_handler.py` / `gm08_handler.py`
- `backend/data/gm07_exercises.py` / `gm08_exercises.py`

**Caractéristiques** :
- Exercices **figés** (HTML statique, pas de templates)
- **Zéro impact** pour la généralisation des variants

---

## 2. Pourquoi `6e_TESTS_DYN` fonctionne (analyse détaillée)

### 2.1 Sélection de variant

**Fichier** : `backend/services/tests_dyn_handler.py`  
**Fonction** : `format_dynamic_exercise()` (lignes 202-243)

```python
# Ligne 207 : Calcul du stable_key
stable_key = exercise_template.get("stable_key") or f"6E_TESTS_DYN:{exercise_template.get('id')}"

# Lignes 209-243 : Sélection conditionnelle
template_variants = exercise_template.get("template_variants") or []
if template_variants:
    # Construction des objets SimpleNamespace pour choose_template_variant
    variant_objs = [...]
    chosen_variant = choose_template_variant(
        variants=variant_objs,
        seed=seed,
        exercise_id=stable_key,
    )
    enonce_template = chosen_variant.enonce_template_html
    solution_template = chosen_variant.solution_template_html
else:
    # Fallback legacy
    enonce_template = exercise_template.get("enonce_template_html", "")
    solution_template = exercise_template.get("solution_template_html", "")
```

**Moteur de sélection** : `backend/services/dynamic_exercise_engine.py::choose_template_variant()`
- Hash SHA256 de `exercise_id:seed`
- Sélection pondérée par `weight`
- **Déterministe** (même seed = même variant)

### 2.2 Rendu des templates

**Fichier** : `backend/services/tests_dyn_handler.py`  
**Lignes** : 263-264

```python
enonce_html = render_template(enonce_template, all_vars)
solution_html = render_template(solution_template, all_vars)
```

**Service** : `backend/services/template_renderer.py::render_template()`
- Remplace `{{variable}}` par les valeurs de `all_vars`
- Gère les alias de variables (triangle/rectangle/carré) via mappings dans `format_dynamic_exercise()` (lignes 136-200)

### 2.3 Garde anti-{{...}}

**Fichier** : `backend/services/tests_dyn_handler.py`  
**Lignes** : 269-299

```python
unresolved_enonce = re.findall(r"\{\{\s*(\w+)\s*\}\}", enonce_html or "")
unresolved_solution = re.findall(r"\{\{\s*(\w+)\s*\}\}", solution_html or "")
unresolved = sorted(set(unresolved_enonce + unresolved_solution))

if unresolved:
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "UNRESOLVED_PLACEHOLDERS",
            ...
        }
    )
```

**Objectif** : **Jamais** de `{{...}}` côté élève. Si un placeholder reste non résolu → erreur JSON explicite.

---

## 3. Stratégie de généralisation MINIMALE (recommandation)

### 3.1 Choix recommandé : **Détection automatique via DB + handler générique**

**Principe** :
- Détecter les exercices dynamiques via `is_dynamic=True` + `generator_key` dans MongoDB
- Créer un handler générique qui réutilise la logique de `format_dynamic_exercise()`
- Intégrer dans le pipeline principal (`exercises_routes.py`) **après** les intercepts GM07/GM08/TESTS_DYN

**Avantages** :
- ✅ **Zéro duplication** : factoriser `format_dynamic_exercise()` en fonction réutilisable
- ✅ **Source de vérité unique** : un seul endroit pour variants + render + guard
- ✅ **Détection automatique** : pas de liste blanche à maintenir
- ✅ **Compatible** : fonctionne pour `6e_TESTS_DYN` (via intercept) et futurs chapitres (via DB)

**Architecture proposée** :

```
backend/services/dynamic_exercise_handler.py (NOUVEAU)
├── format_dynamic_exercise_generic()  # Factorisé depuis tests_dyn_handler
│   ├── Sélection variant (si template_variants)
│   ├── Appel générateur (generator_key)
│   ├── Mappings alias (si nécessaire)
│   ├── Render templates
│   └── Garde anti-{{...}}
└── generate_dynamic_exercise_from_db()  # Nouveau : lit depuis MongoDB
    ├── Requête DB : is_dynamic=True + chapter_code + filters
    ├── Appel format_dynamic_exercise_generic()
    └── Retour exercice formaté

backend/routes/exercises_routes.py
├── Intercepts GM07/GM08/TESTS_DYN (priorité)
└── Nouveau : Détection dynamique via DB
    └── Si exercice trouvé avec is_dynamic=True → generate_dynamic_exercise_from_db()
```

### 3.2 Alternative rejetée : Liste blanche de chapitres

**Pourquoi rejetée** :
- ❌ Maintenance manuelle (ajouter chaque nouveau chapitre)
- ❌ Risque d'oubli
- ❌ Pas de détection automatique

### 3.3 Alternative rejetée : Modifier `MathGenerationService`

**Pourquoi rejetée** :
- ❌ Refonte majeure (génère des specs, pas des templates)
- ❌ Risque de régression élevé
- ❌ Complexité inutile (deux systèmes parallèles)

---

## 4. Risques + garde-fous

### 4.1 Risques identifiés

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| **Seed non déterministe** | 🔴 Bloquant | Faible | Utiliser `seed` tel quel (pas de dérivation) |
| **Placeholders non résolus** | 🔴 Bloquant | Moyen | Garde anti-{{...}} obligatoire (copie depuis TESTS_DYN) |
| **Fallback silencieux vers legacy** | 🟡 Régression | Moyen | Erreur JSON explicite si `is_dynamic=True` mais générateur absent |
| **Générateur inconnu** | 🟡 Erreur utilisateur | Faible | Erreur JSON `GENERATOR_NOT_FOUND` |
| **Template_variants vide mais is_dynamic=True** | 🟡 Incohérence | Faible | Validation DB (déjà en place via `_validate_exercise_data`) |
| **Régression GM07/GM08** | 🔴 Bloquant | Faible | Intercepts en priorité (avant détection DB) |

### 4.2 Garde-fous obligatoires

1. **Déterminisme seed** :
   - ✅ Utiliser `seed` tel quel (pas de `random.seed()` global)
   - ✅ `choose_template_variant()` utilise SHA256 (déterministe)

2. **Zéro placeholder résiduel** :
   - ✅ Garde anti-{{...}} **obligatoire** dans `format_dynamic_exercise_generic()`
   - ✅ Erreur JSON `UNRESOLVED_PLACEHOLDERS` si détecté

3. **Erreurs JSON-safe** :
   - ✅ Toutes les erreurs via `HTTPException` (FastAPI)
   - ✅ Handler global dans `server.py` (déjà en place)

4. **Pas de fallback silencieux** :
   - ✅ Si `is_dynamic=True` mais `generator_key` absent → erreur `GENERATOR_KEY_REQUIRED`
   - ✅ Si générateur inconnu → erreur `GENERATOR_NOT_FOUND`

5. **Non-régression GM07/GM08** :
   - ✅ Intercepts en **priorité absolue** (avant détection DB)
   - ✅ Tests de non-régression obligatoires

---

## 5. Plan d'implémentation (3 étapes max)

### Étape 1 : Factorisation de `format_dynamic_exercise()`

**Objectif** : Extraire la logique de `tests_dyn_handler.py` en fonction générique réutilisable.

**Fichiers** :
- `backend/services/dynamic_exercise_handler.py` (NOUVEAU)
  - `format_dynamic_exercise_generic(exercise_template, seed, stable_key_override=None)`
    - Copie la logique de `format_dynamic_exercise()` (variants + render + guard)
    - Paramètre `stable_key_override` pour permettre `"{chapter_code}:{id}"` personnalisé
- `backend/services/tests_dyn_handler.py` (MODIFIÉ)
  - `format_dynamic_exercise()` appelle `format_dynamic_exercise_generic()`
  - Conserve la compatibilité (même signature publique)

**Tests** :
- ✅ Tests unitaires sur `format_dynamic_exercise_generic()` (variants, legacy, guard)
- ✅ Tests non-régression `6e_TESTS_DYN` (même seed → même résultat)

**Livrables** :
- Fichier `dynamic_exercise_handler.py`
- Tests unitaires
- Incident `INCIDENT_YYYY-MM-DD_template_variants_factorisation.md`

---

### Étape 2 : Détection automatique via DB + intégration pipeline principal

**Objectif** : Détecter les exercices dynamiques depuis MongoDB et les traiter via le handler générique.

**Fichiers** :
- `backend/services/dynamic_exercise_handler.py` (MODIFIÉ)
  - `generate_dynamic_exercise_from_db(chapter_code, offer, difficulty, seed)`
    - Requête MongoDB : `is_dynamic=True` + `chapter_code` + filtres `offer`/`difficulty`
    - Sélection déterministe via seed (même logique que `get_random_tests_dyn_exercise()`)
    - Appel `format_dynamic_exercise_generic()`
    - Retour exercice formaté ou `None`
- `backend/routes/exercises_routes.py` (MODIFIÉ)
  - **Après** les intercepts GM07/GM08/TESTS_DYN (ligne ~737)
  - **Avant** le pipeline `MathGenerationService` (ligne ~738)
  - Nouveau bloc :
    ```python
    # Détection automatique exercices dynamiques depuis DB
    if request.code_officiel:
        from backend.services.dynamic_exercise_handler import generate_dynamic_exercise_from_db
        dyn_exercise = generate_dynamic_exercise_from_db(
            chapter_code=request.code_officiel,
            offer=request.offer,
            difficulty=request.difficulte,
            seed=request.seed
        )
        if dyn_exercise:
            logger.info(f"✅ Dynamic exercise from DB: {dyn_exercise['id_exercice']}")
            return dyn_exercise
    ```

**Tests** :
- ✅ Test manuel : créer un exercice dynamique dans MongoDB (chapitre `6e_G07` par exemple)
- ✅ Test API : `curl` avec `code_officiel=6e_G07` → vérifier que l'exercice dynamique est retourné
- ✅ Test non-régression : `6e_TESTS_DYN` toujours via intercept (pas de double traitement)
- ✅ Test non-régression : GM07/GM08 toujours statiques

**Livrables** :
- Modifications `dynamic_exercise_handler.py` + `exercises_routes.py`
- Tests unitaires + manuels
- Incident `INCIDENT_YYYY-MM-DD_template_variants_generalisation.md`

---

### Étape 3 : Tests de non-régression + documentation

**Objectif** : Valider la généralisation sur plusieurs chapitres et documenter.

**Tests** :
- ✅ **Script seeds** : 30 seeds fixes → vérifier déterminisme (même seed = même variant)
- ✅ **Test multi-chapitres** : créer 2-3 exercices dynamiques (chapitres différents) → vérifier que chacun fonctionne
- ✅ **Test non-régression GM07/GM08** : vérifier que les exercices statiques ne sont pas impactés
- ✅ **Test guard anti-{{...}}** : injecter un placeholder manquant → vérifier erreur JSON

**Documentation** :
- ✅ Mise à jour `docs/CHANGELOG_TECH.md`
- ✅ Ajout section dans `README_admin_dynamic.md` (si existe) : "Créer un exercice dynamique avec variants"

**Livrables** :
- Script de test seeds (`scripts/test_variants_generalisation.sh`)
- Tests unitaires complémentaires
- Documentation mise à jour

---

## 6. Checklist de validation

### Avant implémentation
- [ ] Validation de la stratégie (détection DB vs liste blanche)
- [ ] Validation du plan 3 étapes

### Après Étape 1
- [ ] `format_dynamic_exercise_generic()` factorisé
- [ ] Tests unitaires passent
- [ ] `6e_TESTS_DYN` fonctionne toujours (non-régression)

### Après Étape 2
- [ ] Détection DB fonctionne
- [ ] Exercice dynamique créé dans MongoDB → généré correctement
- [ ] GM07/GM08 non impactés (tests non-régression)

### Après Étape 3
- [ ] Script seeds : déterminisme validé
- [ ] Multi-chapitres : 2-3 chapitres testés
- [ ] Guard anti-{{...}} : erreur JSON si placeholder résiduel
- [ ] Documentation à jour

---

## 7. Fichiers cités (références)

### Backend
- `backend/routes/exercises_routes.py` : point d'entrée API, intercepts GM07/GM08/TESTS_DYN
- `backend/services/tests_dyn_handler.py` : handler pilote `6e_TESTS_DYN` (variants intégrés)
- `backend/services/dynamic_exercise_engine.py` : moteur de sélection de variant (`choose_template_variant`)
- `backend/services/template_renderer.py` : rendu des templates (`render_template`)
- `backend/services/math_generation_service.py` : pipeline legacy (specs structurées, pas de templates)
- `backend/services/exercise_persistence_service.py` : CRUD MongoDB, modèles Pydantic (`TemplateVariant`)
- `backend/data/tests_dyn_exercises.py` : source de données pilote (templates Python)

### Frontend (non impacté pour l'instant)
- `frontend/src/components/admin/ChapterExercisesAdminPage.js` : UI admin (variants déjà supportés)
- `frontend/src/lib/adminApi.js` : API client admin

---

## 8. Recommandations de simplification (futures)

1. **Unifier les sources de données** :
   - Actuellement : `tests_dyn_exercises.py` (Python) vs MongoDB (autres chapitres)
   - Recommandation : migrer `6e_TESTS_DYN` vers MongoDB pour cohérence

2. **Factoriser les mappings d'alias** :
   - Actuellement : mappings triangle/rectangle/carré dans `format_dynamic_exercise()`
   - Recommandation : extraire en fonction réutilisable `_apply_figure_aliases(figure_type, variables)`

3. **Centraliser la détection de générateurs** :
   - Actuellement : `GENERATORS_REGISTRY` dans `thales_generator.py` + Factory dans `generators/factory.py`
   - Recommandation : un seul registre unifié (Factory = source de vérité)

---

**FIN DE L'ANALYSE**

**Prochaine étape** : Validation de la stratégie recommandée (détection DB + handler générique) avant implémentation.



