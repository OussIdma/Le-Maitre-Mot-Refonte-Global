# Plan d'Implémentation — UX Simplifiée Générateurs Premium
**Date :** 2025-01-XX  
**Statut :** 📋 Plan validable  
**Objectif :** Finaliser et valider l'architecture "3 modes prof + presets + templates déterministes"

---

## 📋 Table des matières

1. [Confirmation du modèle cible](#1-confirmation-du-modèle-cible)
2. [Plan d'implémentation phasé](#2-plan-dimplémentation-phasé)
3. [Vérification compatibilité legacy](#3-vérification-compatibilité-legacy)
4. [Go/No-Go et prérequis](#4-gonogo-et-prérequis)

---

## 1. Confirmation du modèle cible

### 1.1 Admin UI (Frontend)

**Interface simplifiée** :
- ✅ **3 boutons radio** : Direct, Guidé, Diagnostic
- ✅ **1 sélecteur difficulté** : Facile, Moyen, Difficile
- ✅ **Section masquée** : "Paramètres techniques" (repliable, read-only par défaut)

**Comportement** :
- Détection automatique générateur premium (présence `variant_id` + `pedagogy_mode` dans schéma)
- Application automatique des presets selon mode + niveau
- Traçabilité : affichage du preset appliqué (ex: "Preset: 6e_guided")

**Fichiers concernés** :
- `frontend/src/components/admin/GeneratorParamsForm.js` (ou composant équivalent)
- `frontend/src/components/admin/ChapterExercisesAdminPage.js` (intégration)

---

### 1.2 Backend / Presets

**Structure** :
- ✅ **9 presets** : `{niveau}_{mode_prof}` (CM2/6e/5e × direct/guided/diagnostic)
- ✅ **Format de clé** : `CM2_direct`, `6e_guided`, `5e_diagnostic`, etc.
- ✅ **Paramètres appliqués automatiquement** :
  - `variant_id` : A (Direct), B (Guidé), C (Diagnostic)
  - `pedagogy_mode` : standard (Direct), guided (Guidé), diagnostic (Diagnostic)
  - `hint_level` : 0 (Direct/Diagnostic), 1-2 (Guidé selon difficulté)
  - `include_feedback` : false (Direct), true (Guidé/Diagnostic)
  - `max_denominator` : 12 (CM2), 20 (6e), 40 (5e)
  - Autres paramètres techniques fixés selon niveau

**Fichiers concernés** :
- `backend/generators/simplification_fractions_v2.py` (méthode `get_presets()`)
- `backend/generators/base_generator.py` (structure `Preset` - déjà OK)

---

### 1.3 Templates (DB)

**Structure** :
- ✅ **1 exercice dynamique** avec **3 `template_variants`** :
  - Variant A (Direct) : `variant_id="A"`, templates standard
  - Variant B (Guidé) : `variant_id="B"`, templates avec indices
  - Variant C (Diagnostic) : `variant_id="C"`, templates diagnostic

**Sélection déterministe** :
- ✅ Si `variant_id` présent dans `variables` → `choose_template_variant(..., mode="fixed", fixed_variant_id=variant_id)`
- ✅ Si `variant_id` absent → `choose_template_variant(..., mode="seed_random")` (fallback random, compatibilité legacy)

**Fichiers concernés** :
- `backend/services/tests_dyn_handler.py` (ligne ~451, modification de l'appel à `choose_template_variant`)
- DB MongoDB : collection `admin_exercises` (champ `template_variants`)

---

### 1.4 Gouvernance

**Standard "Premium Generator"** :
- ✅ Critères d'éligibilité : `variant_id` + `pedagogy_mode` + 3 modes distincts
- ✅ Structure obligatoire : 9 presets, mapping documenté, 3 variants, UI simplifiée
- ✅ Documentation : `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_{GENERATOR}.md` pour chaque générateur

**Fichiers concernés** :
- `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` (mise à jour)
- `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_SIMPLIFICATION_FRACTIONS_V2.md` (création)

---

## 2. Plan d'implémentation phasé

### Phase 1 : Backend / Presets + Sélection déterministe

**Objectif** : Créer les 9 presets et activer la sélection déterministe des variants.

#### Fichiers à modifier

1. **`backend/generators/simplification_fractions_v2.py`** :
   - Modifier `get_presets()` pour ajouter 9 presets :
     - `CM2_direct`, `6e_direct`, `5e_direct`
     - `CM2_guided`, `6e_guided`, `5e_guided`
     - `CM2_diagnostic`, `6e_diagnostic`, `5e_diagnostic`
   - Chaque preset avec paramètres alignés selon tableau Mode → Paramètres

2. **`backend/services/tests_dyn_handler.py`** (ligne ~451) :
   - Modifier l'appel à `choose_template_variant` :
     ```python
     # AVANT
     chosen_variant = choose_template_variant(
         variants=variant_objs,
         seed=seed,
         exercise_id=stable_key,
     )
     
     # APRÈS
     variant_id_from_params = exercise_params.get("variant_id")
     if variant_id_from_params:
         # Sélection déterministe
         chosen_variant = choose_template_variant(
             variants=variant_objs,
             seed=seed,
             exercise_id=stable_key,
             mode="fixed",
             fixed_variant_id=variant_id_from_params
         )
     else:
         # Fallback random (compatibilité legacy)
         chosen_variant = choose_template_variant(
             variants=variant_objs,
             seed=seed,
             exercise_id=stable_key,
             mode="seed_random"
         )
         obs_logger.warning(
             "event=variant_random_fallback",
             reason="variant_id_absent",
             **ctx
         )
     ```

#### Tests à exécuter

**Backend** :
- [ ] Test `CM2_direct` preset → `variant_id="A"`, `pedagogy_mode="standard"`, `hint_level=0`
- [ ] Test `6e_guided` preset → `variant_id="B"`, `pedagogy_mode="guided"`, `hint_level=2`
- [ ] Test `5e_diagnostic` preset → `variant_id="C"`, `pedagogy_mode="diagnostic"`, `hint_level=0`
- [ ] Test sélection variant avec `variant_id="A"` → variant A sélectionné (déterministe)
- [ ] Test sélection variant avec `variant_id` absent → fallback random (compatibilité)
- [ ] Test sélection variant avec `variant_id` invalide → `ValueError` levé

**Rétrocompatibilité** :
- [ ] Test exercice existant sans `variant_id` → fonctionne (random)
- [ ] Test exercice existant avec `variant_id` explicite → fonctionne (déterministe)

#### DoD Phase 1

- [x] 9 presets créés dans `simplification_fractions_v2.py`
- [ ] Sélection déterministe activée dans `tests_dyn_handler.py`
- [ ] Tous les tests backend passants
- [ ] Rétrocompatibilité vérifiée (exercices existants fonctionnent)
- [ ] Logs pipeline OK (pas de régression)

**Risques identifiés** :
- ⚠️ **Risque faible** : Si `variant_id` invalide, `ValueError` levé → erreur 500 au lieu de 422.  
  **Mitigation** : Capturer `ValueError` et lever `HTTPException(422)` avec message explicite.

---

### Phase 2 : Templates (3 variants différenciés)

**Objectif** : Créer/migrer les templates avec 3 variants A/B/C distincts.

#### Fichiers à modifier

1. **DB MongoDB** : Collection `admin_exercises`
   - Créer/migrer 1 exercice dynamique avec 3 `template_variants` :
     - Variant A : Templates standard (Direct)
     - Variant B : Templates guidés (Guidé)
     - Variant C : Templates diagnostic (Diagnostic)
   - Chaque variant avec `variant_id` explicite dans les métadonnées

2. **Migration script** (optionnel) :
   - `backend/migrations/006_add_variant_id_to_template_variants.py`
   - Ajouter `variant_id` aux `template_variants` existants si absent

#### Tests à exécuter

**Templates** :
- [ ] Test sélection variant A → Templates standard utilisés
- [ ] Test sélection variant B → Templates guidés utilisés
- [ ] Test sélection variant C → Templates diagnostic utilisés
- [ ] Test placeholders : tous les placeholders des 3 variants sont résolus

**Rétrocompatibilité** :
- [ ] Test exercice existant sans `template_variants` → fonctionne (fallback legacy)

#### DoD Phase 2

- [ ] 3 `template_variants` créés avec `variant_id` explicite
- [ ] Variant A : Templates standard (Direct)
- [ ] Variant B : Templates guidés (Guidé)
- [ ] Variant C : Templates diagnostic (Diagnostic)
- [ ] Tous les tests templates passants
- [ ] Migration DB pour exercices existants (si nécessaire)

**Risques identifiés** :
- ⚠️ **Risque moyen** : Templates minimalistes actuels ("sa", "1") ne reflètent pas les modes.  
  **Mitigation** : Utiliser les templates définis dans `simplification_fractions_v2.py` (ENONCE_TEMPLATE_A/B/C, SOLUTION_TEMPLATE_A/B/C).

---

### Phase 3 : UI Admin (3 modes + masquage)

**Objectif** : Simplifier l'interface admin pour les profs.

#### Fichiers à modifier

1. **`frontend/src/components/admin/GeneratorParamsForm.js`** (ou composant équivalent) :
   - Détecter générateur premium (présence `variant_id` + `pedagogy_mode` dans schéma)
   - Si premium → Afficher 3 boutons radio (Direct/Guidé/Diagnostic)
   - Si non premium → Afficher formulaire classique (tous les paramètres)
   - Masquer paramètres techniques par défaut (section repliable)
   - Appliquer presets automatiquement selon mode + niveau

2. **`frontend/src/components/admin/ChapterExercisesAdminPage.js`** :
   - Intégrer le composant simplifié dans le formulaire de création/édition d'exercice

#### Tests à exécuter

**UI** :
- [ ] Test sélection "Direct" → Preset `{niveau}_direct` appliqué
- [ ] Test sélection "Guidé" → Preset `{niveau}_guided` appliqué
- [ ] Test sélection "Diagnostic" → Preset `{niveau}_diagnostic` appliqué
- [ ] Test modification difficulté → `hint_level` ajusté (pour Guidé uniquement)
- [ ] Test section "Paramètres techniques" → Masquée par défaut, repliable
- [ ] Test section "Paramètres techniques" → Valeurs préconfigurées affichées (read-only)

**E2E** :
- [ ] Test création exercice avec mode "Direct" → Exercice créé avec `variant_id="A"`
- [ ] Test création exercice avec mode "Guidé" → Exercice créé avec `variant_id="B"`
- [ ] Test création exercice avec mode "Diagnostic" → Exercice créé avec `variant_id="C"`

#### DoD Phase 3

- [ ] 3 boutons radio (Direct/Guidé/Diagnostic) affichés pour générateurs premium
- [ ] Presets appliqués automatiquement selon mode + niveau
- [ ] Paramètres techniques masqués par défaut
- [ ] Section "Paramètres techniques" repliable
- [ ] Tous les tests UI passants
- [ ] Tests E2E passants

**Risques identifiés** :
- ⚠️ **Risque faible** : Détection générateur premium peut échouer si schéma mal structuré.  
  **Mitigation** : Vérifier présence explicite de `variant_id` ET `pedagogy_mode` dans `get_schema()`.

---

### Phase 4 : Documentation + Support / QA

**Objectif** : Documenter le standard et créer les outils de support.

#### Fichiers à créer/modifier

1. **`docs/SUPPORT_TABLEAU_MODE_PARAMETRES_SIMPLIFICATION_FRACTIONS_V2.md`** :
   - Tableau Mode → Paramètres techniques
   - Presets backend (clés techniques)
   - Scénarios de test
   - Cas d'erreur courants

2. **`docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`** :
   - Mettre à jour avec section "Premium Generator"
   - Checklist d'intégration pour nouveaux générateurs premium

3. **`docs/ARCHITECTURE_UX_SIMPLIFIEE_GENERATEURS.md`** :
   - Mettre à jour avec résultats d'implémentation

#### Tests à exécuter

**Documentation** :
- [ ] Tableau Mode → Paramètres documenté et validé
- [ ] Checklist d'intégration créée et testée
- [ ] Guide utilisateur pour les profs créé

#### DoD Phase 4

- [ ] Tableau Mode → Paramètres documenté
- [ ] Standard "Premium Generator" documenté
- [ ] Checklist d'intégration créée
- [ ] Guide utilisateur pour les profs créé

**Risques identifiés** :
- ⚠️ **Risque faible** : Documentation non maintenue à jour.  
  **Mitigation** : Intégrer la documentation dans le processus de création de générateurs.

---

## 3. Vérification compatibilité legacy

### 3.1 Structure de sortie

**Vérification** : La structure de sortie de `format_dynamic_exercise()` reste inchangée.

**Structure actuelle** (ligne 563-592 de `tests_dyn_handler.py`) :
```python
return {
    "id_exercice": exercise_id,
    "niveau": "6e",
    "chapitre": chapter_code,
    "enonce_html": enonce_html,
    "solution_html": solution_html,
    "figure_svg": gen_result.get("figure_svg_enonce"),
    "figure_svg_enonce": gen_result.get("figure_svg_enonce"),
    "figure_svg_solution": gen_result.get("figure_svg_solution"),
    "svg": gen_result.get("figure_svg_enonce"),
    "pdf_token": exercise_id,
    "metadata": {
        "code_officiel": chapter_code,
        "difficulte": difficulty,
        "difficulty": difficulty,
        "is_premium": is_premium,
        "offer": "pro" if is_premium else "free",
        "generator_code": f"{chapter_code}_{generator_key}",
        "family": exercise_template["family"],
        "exercise_type": exercise_template.get("exercise_type"),
        "exercise_id": exercise_template["id"],
        "is_dynamic": True,
        "generator_key": generator_key,
        "seed_used": seed,
        "variables": variables,
        "variables_used": {"source": "generator", **variables},
        "source": "dynamic_generator",
        "needs_svg": exercise_template.get("needs_svg", True)
    }
}
```

**Impact des changements** :
- ✅ **Aucun changement** : La structure de sortie reste identique
- ✅ **Variables** : `variables` contient `variant_id` si fourni, mais structure inchangée
- ✅ **Metadata** : Aucun champ supprimé, seulement ajout possible de `variant_id` dans `variables`

**Conclusion** : ✅ **Aucune rupture de structure de sortie**

---

### 3.2 Paramètres techniques non fournis

**Vérification** : Si paramètres techniques non fournis, defaults actuels appliqués.

**Comportement actuel** :
- `exercise_params = exercise_template.get("variables") or {}`
- Fusion avec `overrides` (ligne 148-155 de `tests_dyn_handler.py`)
- Générateur applique ses defaults si paramètre absent

**Impact des changements** :
- ✅ **Aucun changement** : Si `variant_id` absent, fallback random (compatibilité legacy)
- ✅ **Defaults** : Les defaults du générateur restent inchangés
- ✅ **Presets** : Les presets sont appliqués uniquement si mode prof choisi (nouveau comportement)

**Conclusion** : ✅ **Compatibilité legacy préservée**

---

### 3.3 variant_id absent

**Vérification** : Si `variant_id` absent, comportement legacy préservé.

**Comportement actuel** :
- `choose_template_variant(..., mode="seed_random")` → sélection random

**Comportement après changement** :
- Si `variant_id` absent → `choose_template_variant(..., mode="seed_random")` (fallback random)
- Si `variant_id` présent → `choose_template_variant(..., mode="fixed", fixed_variant_id=variant_id)` (déterministe)

**Impact** :
- ✅ **Aucun changement** : Comportement legacy préservé si `variant_id` absent
- ✅ **Amélioration** : Sélection déterministe si `variant_id` présent

**Conclusion** : ✅ **Compatibilité legacy préservée**

---

### 3.4 Exercices existants

**Vérification** : Les exercices existants continuent de fonctionner.

**Scénarios** :
1. **Exercice sans `variant_id`** :
   - ✅ Fonctionne (fallback random)
   - ✅ Aucun changement de comportement

2. **Exercice avec `variant_id` explicite** :
   - ✅ Fonctionne (sélection déterministe)
   - ✅ Amélioration : sélection déterministe au lieu de random

3. **Exercice sans `template_variants`** :
   - ✅ Fonctionne (fallback legacy, ligne 471-474 de `tests_dyn_handler.py`)

**Conclusion** : ✅ **Aucune rupture pour exercices existants**

---

## 4. Go/No-Go et prérequis

### 4.1 Go/No-Go

**✅ GO** — Conditions remplies :

1. ✅ **Architecture validée** : Modèle cible confirmé, découverte technique (`choose_template_variant` supporte déjà `mode="fixed"`)
2. ✅ **Compatibilité legacy vérifiée** : Aucune rupture de structure de sortie, comportement legacy préservé
3. ✅ **Plan d'implémentation détaillé** : 4 phases avec DoD, tests, risques identifiés
4. ✅ **Risques maîtrisés** : Tous les risques identifiés avec mitigations

---

### 4.2 Prérequis avant implémentation

#### Techniques

1. **Backend** :
   - [ ] Docker backend opérationnel
   - [ ] MongoDB accessible
   - [ ] Tests unitaires passants (état actuel)
   - [ ] Logs pipeline OK (pas de régression)

2. **Frontend** :
   - [ ] Environnement de développement opérationnel
   - [ ] Composants admin accessibles
   - [ ] Tests UI passants (état actuel)

3. **DB** :
   - [ ] Backup MongoDB avant migration (si nécessaire)
   - [ ] Accès en écriture pour création/migration templates

#### Produit / Métier

1. **Validation PO** :
   - [ ] UX simplifiée validée (3 modes prof)
   - [ ] Mapping Mode → Paramètres validé
   - [ ] Presets validés (9 presets par niveau)

2. **Validation UX** :
   - [ ] Interface simplifiée validée (3 radios + difficulté)
   - [ ] Section "Paramètres techniques" validée (masquée, repliable)

3. **Validation Support/QA** :
   - [ ] Tableau Mode → Paramètres validé
   - [ ] Scénarios de test validés

---

### 4.3 Ordre d'implémentation recommandé

**Séquence** :
1. **Phase 1** (Backend/Presets) → **Phase 2** (Templates) → **Phase 3** (UI Admin) → **Phase 4** (Documentation)

**Justification** :
- Phase 1 : Fondations backend (presets + sélection déterministe)
- Phase 2 : Templates différenciés (nécessite Phase 1 pour sélection déterministe)
- Phase 3 : UI Admin (nécessite Phase 1 + Phase 2 pour tests E2E)
- Phase 4 : Documentation (nécessite Phases 1-3 pour résultats d'implémentation)

---

### 4.4 Critères de validation finale

**DoD Global** :
- [ ] Toutes les phases complétées avec DoD respectés
- [ ] Tous les tests passants (backend, UI, E2E)
- [ ] Rétrocompatibilité vérifiée (exercices existants fonctionnent)
- [ ] Documentation complète et à jour
- [ ] Logs pipeline OK (pas de régression)

**Validation PO** :
- [ ] UX simplifiée fonctionnelle (3 modes prof)
- [ ] Presets appliqués automatiquement
- [ ] Paramètres techniques masqués par défaut

**Validation Support/QA** :
- [ ] Tableau Mode → Paramètres disponible
- [ ] Scénarios de test documentés
- [ ] Guide utilisateur pour les profs disponible

---

## 📊 Résumé exécutif

### Modèle cible confirmé

✅ **Admin UI** : 3 radios (Direct/Guidé/Diagnostic) + difficulté, section "Paramètres techniques" masquée  
✅ **Backend/Presets** : 9 presets `{niveau}_{mode_prof}` appliqués automatiquement  
✅ **Templates** : 1 exercice avec 3 `template_variants` A/B/C, sélection déterministe via `mode="fixed"`  
✅ **Gouvernance** : Standard "Premium Generator" réutilisable

### Plan d'implémentation

✅ **4 phases** avec DoD, tests, risques identifiés  
✅ **Fichiers ciblés** : `simplification_fractions_v2.py`, `tests_dyn_handler.py`, `GeneratorParamsForm.js`, DB MongoDB  
✅ **Compatibilité legacy** : Aucune rupture, comportement legacy préservé

### Go/No-Go

✅ **GO** — Conditions remplies, prérequis identifiés, ordre d'implémentation recommandé

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Plan validable par PO/Architecte/UX/QA  
**Prochaine étape :** Validation du plan, puis ouverture de l'implémentation Phase 1

