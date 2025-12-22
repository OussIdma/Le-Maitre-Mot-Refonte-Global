# Synthèse — Réponses aux 4 questions UX Simplifiée
**Date :** 2025-01-XX  
**Objectif :** Réponses consolidées aux 4 questions sur l'UX simplifiée pour générateurs premium.

---

## 📋 Questions traitées

1. Comment structurer l'admin pour 3 radios + presets automatiques ?
2. Comment organiser les templates pour éviter le random ?
3. Quelle gouvernance/preset générique pour tous les futurs générateurs ?
4. Quels tests de validation UI/backend ?

---

## ✅ Question 1 : Structure admin (3 radios + presets automatiques)

### Approche proposée

#### Frontend (`GeneratorParamsForm.js`)

**1. Détection générateur premium** :
- Vérifier si le schéma contient `variant_id` ET `pedagogy_mode`
- Si oui → Générateur premium → Afficher UX simplifiée
- Si non → Générateur classique → Afficher formulaire complet

**2. Interface simplifiée** :
- **3 boutons radio** : Direct, Guidé, Diagnostic
- **1 sélecteur difficulté** : Facile, Moyen, Difficile
- **Section masquée** : "Paramètres techniques" (repliable)

**3. Logique de mapping** :
- Récupérer le niveau depuis le chapitre (ou depuis les presets)
- Lors du choix d'un mode :
  - Construire la clé de preset : `{niveau}_{mode_prof}`
  - Exemple : Mode "Guidé" + Niveau "6e" → Preset `6e_guided`
  - Appliquer le preset correspondant
  - Ajuster `hint_level` selon la difficulté (pour Guidé uniquement)

**4. Section "Paramètres techniques"** :
- Masquée par défaut (repliable)
- Afficher les valeurs préconfigurées (read-only par défaut)
- Badge "Avancé" + avertissement si édition
- Traçabilité : Afficher le preset appliqué (ex: "Preset: 6e_guided")

#### Backend

**1. Créer 9 presets** dans le générateur :
- Format de clé : `{niveau}_{mode_prof}`
- Exemples : `CM2_direct`, `6e_guided`, `5e_diagnostic`
- Paramètres alignés avec le tableau Mode → Paramètres

**2. API de mapping** (optionnel) :
- Endpoint `/api/v1/exercises/generators/{key}/prof-mode-presets`
- Retourne les presets par mode prof (Direct/Guidé/Diagnostic)

---

## ✅ Question 2 : Organisation templates (éviter le random)

### Problème identifié

- Templates actuels minimalistes ("sa", "1") ne reflètent pas les modes
- `template_variants` avec sélection random → pas de contrôle
- `variant_id` peut être aléatoire si non forcé

### Solution proposée

#### Structure DB (Option 1 — Recommandée)

**1 exercice dynamique avec 3 `template_variants`** :

```json
{
  "id": 1,
  "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
  "template_variants": [
    {
      "id": "A",
      "variant_id": "A",
      "enonce_template_html": "{{ENONCE_TEMPLATE_A}}",
      "solution_template_html": "{{SOLUTION_TEMPLATE_A}}",
      "weight": 1
    },
    {
      "id": "B",
      "variant_id": "B",
      "enonce_template_html": "{{ENONCE_TEMPLATE_B}}",
      "solution_template_html": "{{SOLUTION_TEMPLATE_B}}",
      "weight": 1
    },
    {
      "id": "C",
      "variant_id": "C",
      "enonce_template_html": "{{ENONCE_TEMPLATE_C}}",
      "solution_template_html": "{{SOLUTION_TEMPLATE_C}}",
      "weight": 1
    }
  ]
}
```

**Avantages** :
- ✅ 1 seul exercice à créer (pas 3)
- ✅ 3 variants visibles et différenciés
- ✅ Sélection déterministe via `variant_id`
- ✅ Rétrocompatibilité (random si `variant_id` absent)

#### Sélection déterministe

**Découverte technique** :
✅ **La fonction `choose_template_variant` supporte déjà le mode "fixed"** (ligne 36-43 de `dynamic_exercise_engine.py`).

**Implémentation** :

```python
# Dans tests_dyn_handler.py (ligne ~451)
variant_id_from_params = exercise_params.get("variant_id")
if variant_id_from_params:
    # Utiliser le mode "fixed" (déterministe)
    chosen_variant = choose_template_variant(
        variants=variant_objs,
        seed=seed,
        exercise_id=stable_key,
        mode="fixed",
        fixed_variant_id=variant_id_from_params
    )
    # Si variant non trouvé, choose_template_variant lève ValueError
else:
    # Fallback random (compatibilité legacy)
    chosen_variant = choose_template_variant(
        variants=variant_objs,
        seed=seed,
        exercise_id=stable_key,
        mode="seed_random"  # Mode par défaut
    )
    obs_logger.warning(
        "event=variant_random_fallback",
        reason="variant_id_absent",
        **ctx
    )
```

**Résultat** :
- Si `variant_id` présent → Sélection déterministe (pas de random)
- Si `variant_id` absent → Fallback random (compatibilité)
- Si `variant_id` invalide → Erreur explicite (pas de fallback silencieux)

---

## ✅ Question 3 : Gouvernance/preset générique pour futurs générateurs

### Standard "Premium Generator" (réutilisable)

#### Critères d'éligibilité

Un générateur est éligible à l'UX simplifiée si :
- ✅ Il expose `variant_id` (A/B/C) ou équivalent
- ✅ Il expose `pedagogy_mode` (standard/guided/diagnostic) ou équivalent
- ✅ Il supporte 3 modes pédagogiques distincts
- ✅ Il a des paramètres techniques configurables

#### Structure obligatoire

**1. Presets backend** :
- **9 presets minimum** : `{niveau}_{mode_prof}` (3 niveaux × 3 modes)
- **Format de clé standardisé** : `{niveau}_direct`, `{niveau}_guided`, `{niveau}_diagnostic`
- **Paramètres alignés** avec le tableau Mode → Paramètres

**2. Mapping Mode → Paramètres** :
- **Tableau de correspondance documenté** dans `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_{GENERATOR}.md`
- **Paramètres techniques fixés** selon niveau

**3. Templates** :
- **3 variants différenciés** (A/B/C) dans `template_variants`
- **Chaque variant avec `variant_id` explicite** dans les métadonnées

**4. UI Admin** :
- **3 boutons radio** (Direct/Guidé/Diagnostic)
- **Paramètres techniques masqués** par défaut
- **Section repliable** pour experts

#### Documentation

**Pour chaque générateur premium** :
- Créer `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_{GENERATOR}.md`
- Référencer dans `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`

**Template de documentation** :
- Tableau Mode → Paramètres
- Presets backend (clés techniques)
- Scénarios de test
- Cas d'erreur courants

---

## ✅ Question 4 : Tests de validation UI/backend

### Tests backend

#### 1. Tests de presets

**Objectif** : Vérifier que les presets appliquent les bons paramètres.

**Scénarios** :
- Test `CM2_direct` → `variant_id="A"`, `pedagogy_mode="standard"`, `hint_level=0`, `include_feedback=false`
- Test `6e_guided` → `variant_id="B"`, `pedagogy_mode="guided"`, `hint_level=2`, `include_feedback=true`
- Test `5e_diagnostic` → `variant_id="C"`, `pedagogy_mode="diagnostic"`, `hint_level=0`, `include_feedback=true`

**Validation** :
- Appeler `GeneratorFactory.generate(..., exercise_params=preset.params)`
- Vérifier que `result["variables"]["variant_id"]` correspond
- Vérifier que `result["variables"]["pedagogy_mode"]` correspond

#### 2. Tests de sélection variant déterministe

**Objectif** : Vérifier que la sélection de variant est déterministe (pas de random).

**Scénarios** :
- Test avec `variant_id="A"` dans `variables` → `choose_template_variant(..., mode="fixed", fixed_variant_id="A")` → variant A sélectionné
- Test avec `variant_id="B"` dans `variables` → `choose_template_variant(..., mode="fixed", fixed_variant_id="B")` → variant B sélectionné
- Test avec `variant_id="C"` dans `variables` → `choose_template_variant(..., mode="fixed", fixed_variant_id="C")` → variant C sélectionné
- Test avec `variant_id` absent → `choose_template_variant(..., mode="seed_random")` → fallback random (compatibilité)
- Test avec `variant_id` invalide (ex: "D") → `ValueError` levé (pas de fallback silencieux)

**Validation** :
- Vérifier que `chosen_variant.id == variant_id_from_params`
- Vérifier que les logs contiennent `event=variant_selected` avec `variant_id` correct
- Vérifier qu'aucun log `event=variant_random_fallback` si `variant_id` présent

#### 3. Tests de rétrocompatibilité

**Objectif** : Vérifier que les anciens exercices fonctionnent toujours.

**Scénarios** :
- Test exercice existant sans `variant_id` → fonctionne (random)
- Test exercice existant avec `variant_id` explicite → fonctionne (déterministe)

**Validation** :
- Générer un exercice avec `variant_id` absent → pas d'erreur
- Générer un exercice avec `variant_id` présent → variant correct sélectionné

---

### Tests UI

#### 1. Tests de sélection mode

**Objectif** : Vérifier que la sélection d'un mode applique le bon preset.

**Scénarios** :
- Test sélection "Direct" → Preset `{niveau}_direct` appliqué
- Test sélection "Guidé" → Preset `{niveau}_guided` appliqué
- Test sélection "Diagnostic" → Preset `{niveau}_diagnostic` appliqué

**Validation** :
- Vérifier que `formData.variables.variant_id` correspond au mode
- Vérifier que `formData.variables.pedagogy_mode` correspond au mode
- Vérifier que les paramètres techniques sont préremplis

#### 2. Tests de modification difficulté

**Objectif** : Vérifier que le changement de difficulté ajuste les paramètres.

**Scénarios** :
- Test changement difficulté (facile → difficile) → `hint_level` ajusté (pour Guidé uniquement)
- Test changement difficulté (facile → difficile) → `max_denominator` ajusté (si nécessaire)

**Validation** :
- Vérifier que `hint_level` passe de `1` à `2` (pour Guidé)
- Vérifier que les autres paramètres restent inchangés

#### 3. Tests de section "Paramètres techniques"

**Objectif** : Vérifier que la section masquée fonctionne correctement.

**Scénarios** :
- Test affichage masqué → Paramètres non visibles
- Test clic "Paramètres techniques" → Paramètres visibles (read-only)
- Test édition (si expert) → Paramètres éditables

**Validation** :
- Vérifier que les paramètres sont masqués par défaut
- Vérifier que les valeurs préconfigurées sont affichées (read-only)
- Vérifier que l'édition est possible si expert

---

### Tests end-to-end

#### 1. Tests de génération

**Objectif** : Vérifier que la génération produit les bons résultats.

**Scénarios** :
- Test génération Direct CM2 → Exercice avec variant A, templates standard
- Test génération Guidé 6e → Exercice avec variant B, templates guidés, indices niveau 2
- Test génération Diagnostic 5e → Exercice avec variant C, templates diagnostic, feedback activé

**Validation** :
- Vérifier que `result["variables"]["variant_id"]` correspond
- Vérifier que `result["variables"]["pedagogy_mode"]` correspond
- Vérifier que les templates utilisés correspondent au variant

#### 2. Tests de déterminisme

**Objectif** : Vérifier que la génération est déterministe.

**Scénarios** :
- Test même seed + même mode → Même variant sélectionné
- Test même seed + même mode → Même exercice généré

**Validation** :
- Générer 2 fois avec même seed + même mode → résultats identiques
- Vérifier que `variant_id` est identique
- Vérifier que les variables sont identiques

---

## 📊 Tableau récapitulatif des solutions

| Question | Solution | Fichiers concernés | Priorité |
|----------|----------|---------------------|----------|
| **1. Structure admin** | 3 radios + presets automatiques | `GeneratorParamsForm.js`, `backend/generators/{generator}.py` | P0 |
| **2. Organisation templates** | 3 variants + sélection déterministe | `tests_dyn_handler.py`, DB `template_variants` | P0 |
| **3. Gouvernance** | Standard "Premium Generator" | `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` | P1 |
| **4. Tests validation** | Suite de tests UI/backend | `backend/tests/`, tests E2E | P0 |

---

## 🎯 Points clés à retenir

### Découverte technique importante

✅ **La fonction `choose_template_variant` supporte déjà le mode "fixed"** (ligne 36-43 de `dynamic_exercise_engine.py`).  
→ **Pas besoin de modifier cette fonction**, il suffit de l'appeler avec `mode="fixed"` et `fixed_variant_id` au lieu de `mode="seed_random"`.

### Architecture recommandée

1. **1 exercice avec 3 variants** (Option 1) plutôt que 3 exercices séparés
2. **Sélection déterministe** via `choose_template_variant(..., mode="fixed", fixed_variant_id=...)`
3. **Fallback random** si `variant_id` absent (compatibilité legacy)
4. **9 presets backend** (`{niveau}_{mode_prof}`) pour préconfiguration automatique

### Gouvernance

- **Standard réutilisable** pour tous les générateurs premium
- **Checklist d'intégration** pour nouveaux générateurs
- **Documentation support/QA** pour chaque générateur premium

---

## 📚 Documents de référence

- **Architecture complète** : `docs/ARCHITECTURE_UX_SIMPLIFIEE_GENERATEURS.md`
- **Proposition UX** : `docs/UX_PROPOSITION_SIMPLIFICATION_FRACTIONS_V2.md`
- **Tableau support/QA** : `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_V2.md`
- **Procédure création générateur** : `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Synthèse prête pour validation


