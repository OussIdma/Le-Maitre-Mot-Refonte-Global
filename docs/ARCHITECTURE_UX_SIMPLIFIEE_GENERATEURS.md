# Architecture UX Simplifiée — Générateurs Dynamiques Premium
**Date :** 2025-01-XX  
**Objectif :** Proposition consolidée pour industrialiser l'UX simplifiée (3 modes prof) pour tous les générateurs dynamiques premium.

---

## 📋 Résumé exécutif

### Problème
- **11 paramètres techniques** exposés dans l'UI admin → incompréhensible pour les profs
- **Templates minimalistes** ("sa", "1") ne reflètent pas les modes A/B/C
- **Sélection aléatoire** des variants → pas de contrôle déterministe
- **Pas de standard** pour les futurs générateurs premium

### Solution proposée

**1. UX simplifiée** :
- 3 boutons radio : Direct, Guidé, Diagnostic
- Paramètres techniques masqués par défaut
- Presets appliqués automatiquement selon mode + niveau

**2. Presets backend** :
- 9 presets : `{niveau}_direct`, `{niveau}_guided`, `{niveau}_diagnostic`
- Mapping Mode → Paramètres techniques documenté

**3. Templates différenciés** :
- 1 exercice avec 3 `template_variants` (A/B/C)
- Sélection déterministe via `choose_template_variant(..., mode="fixed", fixed_variant_id=...)`
- Fallback random si `variant_id` absent (compatibilité)

**4. Gouvernance** :
- Standard "Premium Generator" réutilisable
- Checklist d'intégration pour nouveaux générateurs

### Découverte technique

✅ **La fonction `choose_template_variant` supporte déjà le mode "fixed"** (ligne 36-43 de `dynamic_exercise_engine.py`).  
→ **Pas besoin de modifier cette fonction**, il suffit de l'appeler avec `mode="fixed"` et `fixed_variant_id` au lieu de `mode="seed_random"`.

---

## 🎯 Problématique consolidée

### État actuel (problèmes identifiés)

1. **UX trop complexe** : 11 paramètres techniques exposés → incompréhensible pour les profs
2. **Templates minimalistes** : Templates actuels ("sa", "1") ne reflètent pas les modes A/B/C
3. **Sélection aléatoire** : `template_variants` avec sélection random → pas de contrôle sur le variant
4. **Manque de gouvernance** : Pas de standard pour les futurs générateurs premium

### Objectifs

1. **UX simplifiée** : 3 modes prof (Direct/Guidé/Diagnostic) + difficulté uniquement
2. **Presets automatiques** : Mapping Mode → Paramètres techniques par niveau
3. **Templates différenciés** : 3 variants A/B/C visibles et déterministes
4. **Gouvernance** : Standard réutilisable pour tous les générateurs premium

---

## 📊 Architecture proposée

### 1. Structure UX Admin

#### Interface simplifiée (niveau prof)

```
┌─────────────────────────────────────────────────────────┐
│ Paramètres du générateur                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Mode pédagogique *                                      │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ○ Direct                                          │   │
│ │   Exercice classique                              │   │
│ │                                                    │   │
│ │ ○ Guidé                                           │   │
│ │   Exercice avec méthode guidée et indices         │   │
│ │                                                    │   │
│ │ ○ Diagnostic                                      │   │
│ │   Exercice d'analyse d'erreurs                    │   │
│ └───────────────────────────────────────────────────┘   │
│                                                         │
│ Difficulté *                                            │
│ [Facile ▼] [Moyen ▼] [Difficile ▼]                    │
│                                                         │
│ [ℹ️ Paramètres techniques masqués]                    │
│   (Cliquer pour voir/éditer)                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Section "Paramètres techniques" (masquée, repliable)

- **Read-only par défaut** : Afficher les valeurs préconfigurées
- **Éditable si expert** : Badge "Avancé" + avertissement
- **Traçabilité** : Afficher le preset appliqué (ex: "Preset: 6e_guided")

---

### 2. Mapping Mode Prof → Paramètres techniques

#### Tableau de correspondance (standard)

| Mode Prof | `variant_id` | `pedagogy_mode` | `hint_level` | `include_feedback` | Autres |
|-----------|--------------|-----------------|--------------|-------------------|--------|
| **Direct** | `A` | `standard` | `0` | `false` | Selon niveau |
| **Guidé** | `B` | `guided` | `1-2` (selon difficulté) | `true` | Selon niveau |
| **Diagnostic** | `C` | `diagnostic` | `0` | `true` | Selon niveau |

#### Règles de préconfiguration

1. **`variant_id`** : Toujours aligné avec le mode prof (Direct→A, Guidé→B, Diagnostic→C)
2. **`pedagogy_mode`** : Toujours aligné avec le mode prof
3. **`hint_level`** : 
   - Direct : `0`
   - Guidé : `1` (facile), `2` (moyen/difficile)
   - Diagnostic : `0`
4. **`include_feedback`** : `false` (Direct), `true` (Guidé/Diagnostic)
5. **Paramètres techniques** : Fixés selon niveau (voir presets)

---

### 3. Presets backend (standard)

#### Structure des presets

**Format de clé** : `{niveau}_{mode_prof}`

**Exemples** :
- `CM2_direct`, `6e_direct`, `5e_direct`
- `CM2_guided`, `6e_guided`, `5e_guided`
- `CM2_diagnostic`, `6e_diagnostic`, `5e_diagnostic`

**Paramètres par preset** :
- `variant_id` : Fixé selon mode
- `pedagogy_mode` : Fixé selon mode
- `hint_level` : Fixé selon mode + difficulté (pour Guidé)
- `include_feedback` : Fixé selon mode
- `allow_negative`, `allow_improper`, `force_reducible` : Fixés selon niveau
- `max_denominator` : Fixé selon niveau
- `show_svg`, `representation` : Fixés selon niveau

#### Ajustement dynamique selon difficulté

**Pour le mode Guidé** :
- Si `difficulty = "facile"` → `hint_level = 1`
- Si `difficulty = "moyen"` ou `"difficile"` → `hint_level = 2`

**Pour tous les modes** :
- `max_denominator` peut être ajusté selon difficulté (si nécessaire)

---

### 4. Organisation des templates

#### Problème actuel

- Templates minimalistes ("sa", "1") ne reflètent pas les modes
- `template_variants` avec sélection random → pas de contrôle
- `variant_id` peut être aléatoire si non forcé

#### Solution proposée

**Option 1 : Templates différenciés dans DB (recommandé)**

**Structure** :
- **1 exercice dynamique** avec **3 `template_variants`** :
  - Variant A (Direct) : `variant_id="A"`, templates standard
  - Variant B (Guidé) : `variant_id="B"`, templates avec indices
  - Variant C (Diagnostic) : `variant_id="C"`, templates diagnostic

**Sélection déterministe** :
- Si `variant_id` est fourni dans `variables` → forcer ce variant
- Si `variant_id` absent → fallback sur sélection random (compatibilité)

**Avantages** :
- ✅ 1 seul exercice à créer (pas 3)
- ✅ 3 variants visibles et différenciés
- ✅ Sélection déterministe via `variant_id`
- ✅ Rétrocompatibilité (random si `variant_id` absent)

**Option 2 : 3 exercices séparés (alternative)**

**Structure** :
- **3 exercices dynamiques** :
  - Exercice 1 : Mode Direct (`variant_id="A"` fixé)
  - Exercice 2 : Mode Guidé (`variant_id="B"` fixé)
  - Exercice 3 : Mode Diagnostic (`variant_id="C"` fixé)

**Sélection** :
- Le prof choisit l'exercice correspondant au mode

**Avantages** :
- ✅ Séparation claire
- ✅ Pas de sélection de variant nécessaire

**Inconvénients** :
- ❌ 3 exercices à créer/maintenir
- ❌ Duplication de configuration

**Recommandation** : **Option 1** (1 exercice avec 3 variants)

---

### 5. Sélection déterministe des variants

#### Problème actuel

```python
# tests_dyn_handler.py ligne ~450
variant_id = getattr(chosen_variant, 'variant_id', None)
# chosen_variant peut être aléatoire si template_variants avec weight
```

#### Solution proposée

**Priorité de sélection** :

1. **Si `variant_id` présent dans `variables`** :
   - Chercher le variant avec `variant_id` correspondant
   - Si trouvé → utiliser ce variant (déterministe)
   - Si non trouvé → erreur explicite (pas de fallback random)

2. **Si `variant_id` absent** :
   - Fallback sur sélection random (compatibilité legacy)
   - Log warning : "variant_id absent, sélection random"

**Implémentation suggérée** :

```python
# Dans tests_dyn_handler.py
variant_id_from_params = exercise_params.get("variant_id")
if variant_id_from_params:
    # Utiliser le mode "fixed" de choose_template_variant
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

**Note** : La fonction `choose_template_variant` supporte déjà le mode "fixed" (ligne 36-43 de `dynamic_exercise_engine.py`). Il suffit de l'utiliser avec `fixed_variant_id` au lieu de chercher manuellement.

---

## 🏗 Gouvernance pour futurs générateurs

### Standard "Premium Generator" (réutilisable)

#### Critères d'éligibilité

Un générateur est éligible à l'UX simplifiée si :
- ✅ Il expose `variant_id` (A/B/C) ou équivalent
- ✅ Il expose `pedagogy_mode` (standard/guided/diagnostic) ou équivalent
- ✅ Il supporte 3 modes pédagogiques distincts
- ✅ Il a des paramètres techniques configurables

#### Structure obligatoire

**1. Presets backend** :
- 9 presets minimum : `{niveau}_{mode_prof}` (3 niveaux × 3 modes)
- Format de clé : `{niveau}_direct`, `{niveau}_guided`, `{niveau}_diagnostic`

**2. Mapping Mode → Paramètres** :
- Tableau de correspondance documenté
- Paramètres techniques fixés selon niveau

**3. Templates** :
- 3 variants différenciés (A/B/C) dans `template_variants`
- Chaque variant avec `variant_id` explicite

**4. UI Admin** :
- 3 boutons radio (Direct/Guidé/Diagnostic)
- Paramètres techniques masqués par défaut
- Section repliable pour experts

---

### Checklist d'intégration (nouveau générateur premium)

#### Backend

- [ ] Générateur expose `variant_id` (A/B/C)
- [ ] Générateur expose `pedagogy_mode` (standard/guided/diagnostic)
- [ ] 9 presets créés (`{niveau}_{mode_prof}`)
- [ ] Presets alignés avec le tableau Mode → Paramètres
- [ ] Mapping documenté dans `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_{GENERATOR}.md`

#### Templates

- [ ] 3 `template_variants` créés avec `variant_id` explicite
- [ ] Variant A : Templates standard (Direct)
- [ ] Variant B : Templates avec indices (Guidé)
- [ ] Variant C : Templates diagnostic (Diagnostic)
- [ ] Chaque variant avec `variant_id` dans les métadonnées

#### UI Admin

- [ ] `GeneratorParamsForm` modifié pour afficher 3 modes
- [ ] Presets appliqués automatiquement selon mode choisi
- [ ] Paramètres techniques masqués par défaut
- [ ] Section "Paramètres techniques" repliable

#### Tests

- [ ] Test Direct CM2/6e/5e → Paramètres corrects
- [ ] Test Guidé CM2/6e/5e → Paramètres corrects
- [ ] Test Diagnostic CM2/6e/5e → Paramètres corrects
- [ ] Test sélection variant déterministe (pas de random)
- [ ] Test rétrocompatibilité (anciens exercices fonctionnent)

---

## 🔧 Implémentation suggérée (sans code)

### Question 1 : Comment structurer l'admin pour 3 radios + presets automatiques ?

#### Approche proposée

**Frontend** :

1. **Modifier `GeneratorParamsForm.js`** :
   - Détecter si le générateur est "premium" (présence de `variant_id` et `pedagogy_mode` dans le schéma)
   - Si premium → Afficher 3 boutons radio (Direct/Guidé/Diagnostic)
   - Si non premium → Afficher le formulaire classique (tous les paramètres)

2. **Logique de mapping** :
   - Récupérer le niveau depuis le chapitre (ou depuis les presets)
   - Lors du choix d'un mode :
     - Construire la clé de preset : `{niveau}_{mode_prof}`
     - Appliquer le preset correspondant
     - Ajuster `hint_level` selon la difficulté (pour Guidé)

3. **Section "Paramètres techniques"** :
   - Masquée par défaut (repliable)
   - Afficher les valeurs préconfigurées (read-only)
   - Badge "Avancé" + avertissement si édition

**Backend** :

1. **Créer 9 presets** dans le générateur :
   - Format : `{niveau}_{mode_prof}`
   - Paramètres alignés avec le tableau Mode → Paramètres

2. **API de mapping** (optionnel) :
   - Endpoint `/api/v1/exercises/generators/{key}/prof-mode-presets`
   - Retourne les presets par mode prof (Direct/Guidé/Diagnostic)

---

### Question 2 : Comment organiser les templates pour éviter le random ?

#### Approche proposée

**Structure DB** :

1. **1 exercice dynamique** avec **3 `template_variants`** :
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

2. **Sélection déterministe** :
   - Si `variant_id` présent dans `variables` → chercher le variant correspondant
   - Si trouvé → utiliser ce variant (pas de random)
   - Si non trouvé → erreur explicite

**Modification `tests_dyn_handler.py`** :

1. **Utiliser le mode "fixed" de `choose_template_variant`** :
   - La fonction `choose_template_variant` supporte déjà `mode="fixed"` avec `fixed_variant_id`
   - Si `variant_id` présent dans `exercise_params` :
     - Appeler `choose_template_variant(..., mode="fixed", fixed_variant_id=variant_id)`
     - Si trouvé → variant sélectionné (déterministe)
     - Si non trouvé → erreur explicite (ValueError)

2. **Fallback random** :
   - Uniquement si `variant_id` absent (compatibilité legacy)
   - Appeler `choose_template_variant(..., mode="seed_random")` (comportement actuel)
   - Log warning : "variant_id absent, sélection random"

---

### Question 3 : Quelle gouvernance pour tous les futurs générateurs ?

#### Standard "Premium Generator"

**Critères d'éligibilité** :
- Générateur expose `variant_id` (A/B/C) ou équivalent
- Générateur expose `pedagogy_mode` (standard/guided/diagnostic) ou équivalent
- Générateur supporte 3 modes pédagogiques distincts

**Structure obligatoire** :

1. **Presets backend** :
   - 9 presets : `{niveau}_direct`, `{niveau}_guided`, `{niveau}_diagnostic`
   - Format de clé standardisé

2. **Mapping Mode → Paramètres** :
   - Tableau de correspondance documenté
   - Paramètres techniques fixés selon niveau

3. **Templates** :
   - 3 variants différenciés (A/B/C) dans `template_variants`
   - Chaque variant avec `variant_id` explicite

4. **UI Admin** :
   - 3 boutons radio (Direct/Guidé/Diagnostic)
   - Paramètres techniques masqués par défaut

**Documentation** :
- Créer `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_{GENERATOR}.md` pour chaque générateur premium
- Référencer dans `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`

---

### Question 4 : Quels tests de validation UI/backend ?

#### Tests backend

**1. Tests de presets** :
- Test `CM2_direct` → `variant_id="A"`, `pedagogy_mode="standard"`, `hint_level=0`
- Test `6e_guided` → `variant_id="B"`, `pedagogy_mode="guided"`, `hint_level=2`
- Test `5e_diagnostic` → `variant_id="C"`, `pedagogy_mode="diagnostic"`, `hint_level=0`

**2. Tests de sélection variant** :
- Test avec `variant_id="A"` dans `variables` → variant A sélectionné (déterministe)
- Test avec `variant_id="B"` dans `variables` → variant B sélectionné (déterministe)
- Test avec `variant_id="C"` dans `variables` → variant C sélectionné (déterministe)
- Test avec `variant_id` absent → fallback random (compatibilité)

**3. Tests de rétrocompatibilité** :
- Test exercice existant sans `variant_id` → fonctionne (random)
- Test exercice existant avec `variant_id` explicite → fonctionne (déterministe)

#### Tests UI

**1. Tests de sélection mode** :
- Test sélection "Direct" → Preset `{niveau}_direct` appliqué
- Test sélection "Guidé" → Preset `{niveau}_guided` appliqué
- Test sélection "Diagnostic" → Preset `{niveau}_diagnostic` appliqué

**2. Tests de modification difficulté** :
- Test changement difficulté (facile → difficile) → `hint_level` ajusté (pour Guidé)

**3. Tests de section "Paramètres techniques"** :
- Test affichage masqué → Paramètres non visibles
- Test clic "Paramètres techniques" → Paramètres visibles (read-only)
- Test édition (si expert) → Paramètres éditables

#### Tests end-to-end

**1. Tests de génération** :
- Test génération Direct CM2 → Exercice avec variant A
- Test génération Guidé 6e → Exercice avec variant B + indices
- Test génération Diagnostic 5e → Exercice avec variant C + feedback

**2. Tests de déterminisme** :
- Test même seed + même mode → Même variant sélectionné
- Test même seed + même mode → Même exercice généré

---

## 📋 Plan d'implémentation (phases)

### Phase 1 : Backend (presets + sélection déterministe)

1. **Créer 9 presets** dans `SIMPLIFICATION_FRACTIONS_V2` :
   - `CM2_direct`, `6e_direct`, `5e_direct`
   - `CM2_guided`, `6e_guided`, `5e_guided`
   - `CM2_diagnostic`, `6e_diagnostic`, `5e_diagnostic`

2. **Modifier `tests_dyn_handler.py`** :
   - Ajouter logique de sélection déterministe (priorité `variant_id`)
   - Fallback random si `variant_id` absent

3. **Tests backend** :
   - Tests de presets
   - Tests de sélection variant déterministe

### Phase 2 : Templates (3 variants différenciés)

1. **Créer/migrer templates** :
   - 1 exercice dynamique avec 3 `template_variants`
   - Variant A : Templates standard
   - Variant B : Templates avec indices
   - Variant C : Templates diagnostic

2. **Migration DB** :
   - Script pour ajouter `variant_id` aux `template_variants` existants

3. **Tests templates** :
   - Test sélection variant A → Templates standard
   - Test sélection variant B → Templates guidés
   - Test sélection variant C → Templates diagnostic

### Phase 3 : UI Admin (3 modes + masquage)

1. **Modifier `GeneratorParamsForm.js`** :
   - Détecter générateur premium
   - Afficher 3 boutons radio (Direct/Guidé/Diagnostic)
   - Masquer paramètres techniques par défaut
   - Appliquer presets automatiquement

2. **Section "Paramètres techniques"** :
   - Repliable, read-only par défaut
   - Éditable si expert

3. **Tests UI** :
   - Tests de sélection mode
   - Tests de modification difficulté
   - Tests de section "Paramètres techniques"

### Phase 4 : Documentation + gouvernance

1. **Documentation** :
   - Mettre à jour `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`
   - Créer `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_SIMPLIFICATION_FRACTIONS_V2.md`
   - Documenter le standard "Premium Generator"

2. **Gouvernance** :
   - Checklist d'intégration pour nouveaux générateurs premium
   - Template de documentation pour support/QA

---

## ✅ Définition of Done

### Backend

- [ ] 9 presets créés (`{niveau}_{mode_prof}`)
- [ ] Sélection variant déterministe (priorité `variant_id`)
- [ ] Fallback random si `variant_id` absent (compatibilité)
- [ ] Tests de presets passants
- [ ] Tests de sélection variant passants

### Templates

- [ ] 3 `template_variants` créés avec `variant_id` explicite
- [ ] Variant A : Templates standard (Direct)
- [ ] Variant B : Templates guidés (Guidé)
- [ ] Variant C : Templates diagnostic (Diagnostic)
- [ ] Migration DB pour exercices existants

### UI Admin

- [ ] 3 boutons radio (Direct/Guidé/Diagnostic) affichés
- [ ] Presets appliqués automatiquement
- [ ] Paramètres techniques masqués par défaut
- [ ] Section "Paramètres techniques" repliable
- [ ] Tests UI passants

### Documentation

- [ ] Tableau Mode → Paramètres documenté
- [ ] Standard "Premium Generator" documenté
- [ ] Checklist d'intégration créée
- [ ] Guide utilisateur pour les profs

### Rétrocompatibilité

- [ ] Anciens exercices fonctionnent (random si `variant_id` absent)
- [ ] Nouveaux exercices utilisent sélection déterministe
- [ ] Logs pipeline OK (pas de régression)

---

## 📚 Références

- **Proposition UX** : `docs/UX_PROPOSITION_SIMPLIFICATION_FRACTIONS_V2.md`
- **Tableau support/QA** : `docs/SUPPORT_TABLEAU_MODE_PARAMETRES_V2.md`
- **Procédure création générateur** : `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Proposition consolidée prête pour validation

