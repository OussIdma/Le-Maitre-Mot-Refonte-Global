# Note de conception : Import/Export d'exercices (Admin)

**Date** : 2025-12-18  
**Statut** : 📋 Analyse — En attente validation  
**Auteur** : CTO / Lead Architect

---

## 🎯 Objectif métier

Permettre l'édition en masse des exercices (énoncés, solutions, variants) via un format externe (CSV/TSV/Excel) pour :
- Réduire les erreurs de saisie HTML manuelle
- Accélérer la création/modification d'exercices
- Faciliter la collaboration (édition hors ligne, outils externes)
- Maintenir la cohérence et le déterminisme

**Contraintes non négociables** :
- Aucun import silencieux (validation stricte avant écriture)
- Zéro perte de données (rollback explicite si erreur)
- Compatible statique + dynamique + variants
- Pas de régression sur le déterminisme (seed, placeholders)

---

## 📊 Périmètre

### 1. Types d'exercices

#### **Statique (legacy)**
- Champs requis : `enonce_html`, `solution_html`
- Champs optionnels : `variables`, `svg_enonce_brief`, `svg_solution_brief`
- Pas de `generator_key`, pas de `template_variants`

#### **Dynamique (template-based)**
- Champs requis : `generator_key`, `enonce_template_html` OU `template_variants`
- Champs optionnels : `variables_schema`
- **Variants** : `template_variants[]` avec `id`, `label`, `weight`, `enonce_template_html`, `solution_template_html`

### 2. Granularité d'export/import

**Niveaux possibles** :
1. **Chapitre complet** : Tous les exercices d'un chapitre (`6E_TESTS_DYN`, `6E_GM07`, etc.)
2. **Filtre par critères** : `offer` (free/pro), `difficulty` (facile/moyen/difficile), `family`
3. **Exercice unique** : Export/import d'un seul exercice (moins utile pour édition en masse)

**Recommandation** : **Chapitre complet** par défaut, avec filtres optionnels.

### 3. Champs exportables

**Métadonnées** :
- `id` (lecture seule, identifiant stable)
- `chapter_code` (lecture seule)
- `family` (CONVERSION, COMPARAISON, etc.)
- `exercise_type` (optionnel)
- `difficulty` (facile, moyen, difficile)
- `offer` (free, pro)
- `needs_svg` (bool)

**Contenu statique** :
- `enonce_html` (HTML pur)
- `solution_html` (HTML pur)
- `variables` (JSON, pour SVG)
- `svg_enonce_brief` (texte)
- `svg_solution_brief` (texte)

**Contenu dynamique** :
- `is_dynamic` (bool)
- `generator_key` (THALES_V1, SYMETRIE_AXIALE_V2, etc.)
- `enonce_template_html` (legacy, si pas de variants)
- `solution_template_html` (legacy, si pas de variants)
- `variables_schema` (JSON)
- `template_variants[]` (tableau de variants)

### 4. Pipelines (chapitre) et validations post-import
- Champ `pipeline` obligatoire dans le fichier d’import (SPEC | TEMPLATE | MIXED).
- Validation post-import :
  - TEMPLATE : doit avoir ≥1 exercice dynamique (is_dynamic=true) pour le chapitre, sinon import refusé.
  - SPEC : doit avoir des `exercise_types` valides dans le curriculum, ou au moins un exercice statique saisi ; sinon import refusé.
  - MIXED : accepte dyn + stat ; s’il n’y a aucun exo pour les filtres offer/difficulty à l’usage, l’API renverra un 422 explicite (NO_EXERCISE_AVAILABLE).
  - Mapping generator_key → exercise_type : source unique = GeneratorFactory (résolution automatique côté backend).

---

## 🔧 Solutions proposées

### **Solution 1 : CSV/TSV multi-feuilles (Recommandée)**

**Format** : Fichier CSV/TSV avec plusieurs sections (feuilles Excel ou fichiers séparés)

**Structure** :
```
exercises.csv (ou exercises.tsv)
├── Section 1 : Métadonnées (1 ligne par exercice)
│   id | chapter_code | family | difficulty | offer | is_dynamic | generator_key | needs_svg
│   1  | 6E_TESTS_DYN | CONVERSION | moyen | free | true | THALES_V1 | true
│
├── Section 2 : Contenu statique (1 ligne par exercice)
│   id | enonce_html | solution_html | variables | svg_enonce_brief | svg_solution_brief
│   1  | <p>...</p>  | <ol>...</ol>  | {"hour":8} | "Horloge 8h" | "Horloge complète"
│
├── Section 3 : Variants (N lignes par exercice, 1 par variant)
│   exercise_id | variant_id | variant_label | weight | enonce_template_html | solution_template_html
│   1           | v1         | Variant 1     | 1      | <p>{{var}}</p>       | <p>Sol: {{var}}</p>
│   1           | v2         | Variant 2     | 10     | <p>{{var}} autre</p> | <p>Sol: {{var}}</p>
```

**Avantages** :
- ✅ Compatible Excel/Google Sheets (édition visuelle)
- ✅ Séparation claire métadonnées / contenu / variants
- ✅ Facile à parser (CSV standard)
- ✅ Support multi-lignes pour variants (1 ligne = 1 variant)

**Inconvénients** :
- ⚠️ HTML multi-lignes nécessite échappement (guillemets, sauts de ligne)
- ⚠️ JSON (`variables`, `variables_schema`) nécessite échappement JSON dans CSV

**Recommandation** : **TSV (Tab-Separated Values)** plutôt que CSV pour éviter les conflits avec les guillemets HTML.

---

### **Solution 2 : JSON structuré (Alternative robuste)**

**Format** : Fichier JSON avec structure hiérarchique

**Structure** :
```json
{
  "metadata": {
    "chapter_code": "6E_TESTS_DYN",
    "export_date": "2025-12-18T10:00:00Z",
    "export_version": "1.0"
  },
  "exercises": [
    {
      "id": 1,
      "family": "CONVERSION",
      "difficulty": "moyen",
      "offer": "free",
      "is_dynamic": true,
      "generator_key": "THALES_V1",
      "needs_svg": true,
      "enonce_html": "<p>...</p>",
      "solution_html": "<ol>...</ol>",
      "variables": {"hour": 8, "minute": 0},
      "svg_enonce_brief": "Horloge 8h",
      "svg_solution_brief": "Horloge complète",
      "template_variants": [
        {
          "id": "v1",
          "label": "Variant 1",
          "weight": 1,
          "enonce_template_html": "<p>{{var}}</p>",
          "solution_template_html": "<p>Sol: {{var}}</p>"
        }
      ]
    }
  ]
}
```

**Avantages** :
- ✅ Structure native (pas d'échappement HTML/JSON)
- ✅ Validation facile (schéma JSON Schema)
- ✅ Support multi-lignes natif
- ✅ Métadonnées d'export (version, date)

**Inconvénients** :
- ⚠️ Moins accessible pour édition manuelle (nécessite éditeur JSON)
- ⚠️ Pas de support Excel natif (nécessite conversion)

**Recommandation** : **Format de secours** pour validation/storage, mais pas pour édition manuelle.

---

### **Solution 3 : Excel multi-feuilles (Hybride)**

**Format** : Fichier Excel (.xlsx) avec 3 feuilles

**Structure** :
- **Feuille 1 "Exercises"** : Métadonnées + contenu statique (1 ligne = 1 exercice)
- **Feuille 2 "Variants"** : Variants (1 ligne = 1 variant, colonne `exercise_id` pour lien)
- **Feuille 3 "Metadata"** : Informations d'export (date, version, chapitre)

**Avantages** :
- ✅ Édition visuelle Excel (formatage, couleurs, validation)
- ✅ Support multi-lignes dans cellules (HTML)
- ✅ Séparation claire (feuilles distinctes)
- ✅ Validation Excel possible (listes déroulantes pour `difficulty`, `offer`, etc.)

**Inconvénients** :
- ⚠️ Dépendance bibliothèque Python (`openpyxl` ou `pandas`)
- ⚠️ Taille fichier plus importante
- ⚠️ Risque de corruption si édition manuelle incorrecte

**Recommandation** : **Option premium** pour utilisateurs avancés, mais pas par défaut.

---

## 🛡️ Validation et garde-fous

### 1. Validation des placeholders

**Problème** : Placeholders cassés (`{{variable}}` mal formés ou variables inconnues)

**Solution** :
```python
def validate_placeholders(template_html: str, generator_key: str) -> List[str]:
    """
    Valide les placeholders dans un template.
    
    Returns:
        Liste des erreurs (vide si OK)
    """
    errors = []
    
    # 1. Extraction placeholders
    placeholders = re.findall(r'\{\{([a-zA-Z0-9_]+)\}\}', template_html)
    
    # 2. Vérifier format (pas de {{variable malformé}})
    malformed = re.findall(r'\{\{[^}]+\}\}', template_html)
    if malformed:
        errors.append(f"Placeholders malformés: {malformed}")
    
    # 3. Vérifier variables connues (via generator_key)
    if generator_key:
        known_vars = get_generator_variables(generator_key)  # Ex: ["cote_initial", "cote_final"]
        unknown = [p for p in placeholders if p not in known_vars]
        if unknown:
            errors.append(f"Variables inconnues pour {generator_key}: {unknown}")
    
    return errors
```

**Enforcement** : ❌ **Refuser l'import** si placeholders invalides (pas de fallback silencieux).

---

### 2. Validation HTML

**Problème** : HTML mal formé, balises non fermées, caractères spéciaux

**Solution** :
```python
def validate_html(html: str, field_name: str) -> List[str]:
    """
    Valide la structure HTML basique.
    
    Returns:
        Liste des erreurs (vide si OK)
    """
    errors = []
    
    # 1. Vérifier balises fermées (comptage simple)
    open_tags = re.findall(r'<([a-zA-Z]+)[^>]*>', html)
    close_tags = re.findall(r'</([a-zA-Z]+)>', html)
    
    # Vérifier correspondance (simplifié, pas de parsing complet)
    for tag in set(open_tags):
        if open_tags.count(tag) != close_tags.count(tag):
            errors.append(f"{field_name}: balise <{tag}> non fermée")
    
    # 2. Vérifier caractères interdits (LaTeX, Markdown)
    if '$' in html or '$$' in html:
        errors.append(f"{field_name}: LaTeX détecté (utiliser HTML pur)")
    if '**' in html or '__' in html:
        errors.append(f"{field_name}: Markdown détecté (utiliser <strong>, <em>)")
    
    return errors
```

**Enforcement** : ⚠️ **Avertissement** pour HTML mal formé, mais accepter si structure basique OK (pas de parsing complet HTML).

---

### 3. Validation de cohérence

**Problème** : Incohérences entre champs (ex: `is_dynamic=True` mais pas de `generator_key`)

**Solution** :
```python
def validate_exercise_coherence(exercise: Dict) -> List[str]:
    """
    Valide la cohérence d'un exercice (statique vs dynamique).
    
    Returns:
        Liste des erreurs (vide si OK)
    """
    errors = []
    
    is_dynamic = exercise.get("is_dynamic", False)
    
    if is_dynamic:
        # Dynamique : doit avoir generator_key
        if not exercise.get("generator_key"):
            errors.append("is_dynamic=True mais generator_key manquant")
        
        # Dynamique : doit avoir templates (legacy OU variants)
        has_legacy = bool(exercise.get("enonce_template_html"))
        has_variants = bool(exercise.get("template_variants"))
        
        if not (has_legacy or has_variants):
            errors.append("is_dynamic=True mais aucun template (legacy ou variants)")
    else:
        # Statique : doit avoir enonce_html + solution_html
        if not exercise.get("enonce_html"):
            errors.append("is_dynamic=False mais enonce_html manquant")
        if not exercise.get("solution_html"):
            errors.append("is_dynamic=False mais solution_html manquant")
    
    return errors
```

**Enforcement** : ❌ **Refuser l'import** si incohérence (pas de correction automatique).

---

### 4. Validation des variants

**Problème** : Variants avec `id` dupliqué, `weight` invalide, templates vides

**Solution** :
```python
def validate_template_variants(variants: List[Dict], exercise_id: int) -> List[str]:
    """
    Valide les template_variants d'un exercice.
    
    Returns:
        Liste des erreurs (vide si OK)
    """
    errors = []
    
    if not variants:
        return errors  # Pas de variants = OK (legacy)
    
    # 1. Vérifier IDs uniques
    ids = [v.get("id") for v in variants]
    duplicates = [id for id in ids if ids.count(id) > 1]
    if duplicates:
        errors.append(f"Exercise {exercise_id}: variant IDs dupliqués: {duplicates}")
    
    # 2. Vérifier weight >= 1
    for v in variants:
        if v.get("weight", 0) < 1:
            errors.append(f"Exercise {exercise_id}: variant {v.get('id')} a weight < 1")
        
        # 3. Vérifier templates non vides
        if not v.get("enonce_template_html"):
            errors.append(f"Exercise {exercise_id}: variant {v.get('id')} a enonce_template_html vide")
        if not v.get("solution_template_html"):
            errors.append(f"Exercise {exercise_id}: variant {v.get('id')} a solution_template_html vide")
    
    return errors
```

**Enforcement** : ❌ **Refuser l'import** si variants invalides.

---

## 🔄 Flux sécurisé

### Phase 1 : Export

**Endpoint** : `GET /api/admin/chapters/{chapter_code}/exercises/export?format=tsv&offer=free&difficulty=moyen`

**Réponse** :
- Fichier téléchargeable (TSV/JSON/Excel)
- Métadonnées d'export (date, version, nombre d'exercices)
- Hash de validation (SHA256) pour détecter modifications

**Format TSV recommandé** :
```tsv
# Metadata
# chapter_code: 6E_TESTS_DYN
# export_date: 2025-12-18T10:00:00Z
# export_version: 1.0
# exercise_count: 5
# export_hash: abc123...

# Exercises
id	chapter_code	family	difficulty	offer	is_dynamic	generator_key	needs_svg	enonce_html	solution_html	variables	svg_enonce_brief	svg_solution_brief
1	6E_TESTS_DYN	CONVERSION	moyen	free	true	THALES_V1	true	<p>{{cote_initial}}</p>	<ol>...</ol>	{}	""	""
```

**Variants dans fichier séparé** : `exercises_variants.tsv`
```tsv
exercise_id	variant_id	variant_label	weight	enonce_template_html	solution_template_html
1	v1	Variant 1	1	<p>{{cote_initial}}</p>	<p>Sol: {{cote_final}}</p>
1	v2	Variant 2	10	<p>{{cote_initial}} autre</p>	<p>Sol: {{cote_final}}</p>
```

---

### Phase 2 : Modification (hors système)

**Utilisateur** :
1. Télécharge le fichier TSV
2. Édite dans Excel/Google Sheets/éditeur texte
3. Modifie les champs HTML, ajoute/supprime des variants
4. Sauvegarde le fichier

**Risques** :
- Corruption du format (guillemets, sauts de ligne)
- Placeholders cassés
- HTML mal formé

**Mitigation** : Validation stricte à l'import (Phase 3).

---

### Phase 3 : Validation (avant import)

**Endpoint** : `POST /api/admin/chapters/{chapter_code}/exercises/validate-import`

**Payload** : Fichier TSV/JSON/Excel (multipart/form-data)

**Réponse** :
```json
{
  "valid": false,
  "errors": [
    {
      "exercise_id": 1,
      "field": "enonce_template_html",
      "error_code": "INVALID_PLACEHOLDER",
      "message": "Variable inconnue: {{cote_malforme}}",
      "hint": "Variables disponibles pour THALES_V1: cote_initial, cote_final, ..."
    },
    {
      "exercise_id": 2,
      "field": "template_variants",
      "error_code": "DUPLICATE_VARIANT_ID",
      "message": "Variant IDs dupliqués: ['v1', 'v1']"
    }
  ],
  "warnings": [
    {
      "exercise_id": 3,
      "field": "enonce_html",
      "warning_code": "MALFORMED_HTML",
      "message": "Balise <p> non fermée"
    }
  ],
  "summary": {
    "total_exercises": 10,
    "valid_exercises": 8,
    "invalid_exercises": 2,
    "total_variants": 15,
    "valid_variants": 14,
    "invalid_variants": 1
  }
}
```

**Comportement** :
- ✅ **Validation complète** avant toute écriture DB
- ✅ **Erreurs détaillées** (exercise_id, field, message)
- ✅ **Warnings** (HTML mal formé mais récupérable)
- ❌ **Refus si erreurs bloquantes** (placeholders invalides, incohérences)

---

### Phase 4 : Import (si validation OK)

**Endpoint** : `POST /api/admin/chapters/{chapter_code}/exercises/import?dry_run=false`

**Payload** : Fichier TSV/JSON/Excel (multipart/form-data)

**Options** :
- `dry_run=true` : Validation uniquement (pas d'écriture DB)
- `dry_run=false` : Import réel (écriture DB)

**Réponse** :
```json
{
  "success": true,
  "imported_count": 8,
  "skipped_count": 2,
  "created_count": 0,
  "updated_count": 8,
  "errors": [],
  "backup_id": "backup_2025-12-18_10-00-00_abc123"
}
```

**Comportement** :
1. **Backup automatique** : Sauvegarde MongoDB avant import (rollback possible)
2. **Transaction** : Import atomique (tout ou rien si `dry_run=false`)
3. **Logging** : Tous les changements loggés (audit trail)
4. **Rollback** : Endpoint `POST /api/admin/chapters/{chapter_code}/exercises/rollback/{backup_id}`

---

## 🎨 Impacts UX admin

### 1. Interface d'export

**Ajout dans `ChapterExercisesAdminPage.js`** :
- Bouton **"Exporter"** (dropdown : TSV, JSON, Excel)
- Filtres : `offer`, `difficulty`, `family`
- Téléchargement direct (pas de modal)

**UX** : Simple, 1 clic, fichier téléchargeable immédiatement.

---

### 2. Interface d'import

**Ajout dans `ChapterExercisesAdminPage.js`** :
- Bouton **"Importer"** → Modal avec :
  - Upload fichier (drag & drop)
  - Option `dry_run` (checkbox)
  - Bouton **"Valider"** (validation uniquement)
  - Bouton **"Importer"** (import réel)

**Affichage résultats** :
- Tableau d'erreurs (si validation échoue)
- Résumé (X exercices importés, Y créés, Z mis à jour)
- Lien rollback (si import réussi)

**UX** : Processus en 2 étapes (validation → import) pour éviter erreurs.

---

### 3. Gestion des variants

**Problème** : Variants dans fichier séparé (TSV) ou intégré (JSON/Excel)

**Solution recommandée** :
- **TSV** : Fichier séparé `exercises_variants.tsv` (1 ligne = 1 variant)
- **JSON** : Intégré dans structure `exercises[].template_variants[]`
- **Excel** : Feuille séparée "Variants"

**UX** : Cohérent avec structure données (variants = sous-éléments d'exercices).

---

## 📚 Impacts pédagogiques

### 1. Déterminisme préservé

**Risque** : Modification accidentelle de `id` ou `stable_key` → changement de variant sélectionné

**Mitigation** :
- ✅ `id` en **lecture seule** dans export (colonne grisée)
- ✅ Validation : `id` ne peut pas être modifié (erreur si changement)
- ✅ `stable_key` calculé automatiquement (pas exportable)

---

### 2. Placeholders préservés

**Risque** : Suppression/altération de placeholders `{{variable}}` → exercice cassé côté élève

**Mitigation** :
- ✅ Validation stricte : placeholders invalides → **refus import**
- ✅ Liste des variables disponibles affichée dans erreur
- ✅ Preview avant import (optionnel) : génération test avec seed fixe

---

### 3. Cohérence pédagogique

**Risque** : Modification de `difficulty` ou `family` → incohérence avec contenu

**Mitigation** :
- ✅ Validation : `difficulty` doit être dans `["facile", "moyen", "difficile"]`
- ✅ Validation : `family` doit être dans liste connue
- ✅ Warnings si changement majeur (ex: `difficulty: facile → difficile`)

---

## 🎯 Recommandation finale

### **Format recommandé : TSV (Tab-Separated Values)**

**Justification** :
1. ✅ **Compatible Excel/Google Sheets** (édition visuelle)
2. ✅ **Évite conflits guillemets** (pas de délimiteur CSV problématique)
3. ✅ **Support multi-lignes** (échappement `\n` dans cellules)
4. ✅ **Parsing simple** (bibliothèque standard Python)
5. ✅ **Séparation claire** : Fichier principal + fichier variants

**Structure** :
- `exercises.tsv` : Métadonnées + contenu (1 ligne = 1 exercice)
- `exercises_variants.tsv` : Variants (1 ligne = 1 variant, colonne `exercise_id`)

**Format alternatif** : JSON pour validation/storage (pas pour édition manuelle).

---

### **Flux recommandé**

1. **Export** : `GET /api/admin/chapters/{chapter_code}/exercises/export?format=tsv`
2. **Modification** : Édition hors ligne (Excel/éditeur)
3. **Validation** : `POST /api/admin/chapters/{chapter_code}/exercises/validate-import` (dry-run)
4. **Import** : `POST /api/admin/chapters/{chapter_code}/exercises/import?dry_run=false`
5. **Rollback** (si erreur) : `POST /api/admin/chapters/{chapter_code}/exercises/rollback/{backup_id}`

---

### **Priorités d'implémentation**

**Phase 1 (MVP)** :
- Export TSV (chapitre complet)
- Import TSV avec validation stricte
- Backup automatique avant import

**Phase 2 (Amélioration)** :
- Filtres export (offer, difficulty)
- Format Excel (optionnel)
- Preview avant import

**Phase 3 (Avancé)** :
- Import partiel (mise à jour sélective)
- Historique des imports (audit trail)
- Templates d'export (formats personnalisés)

---

## ✅ Validation requise

**Avant implémentation** :
- [ ] Validation format TSV (structure, échappement)
- [ ] Validation règles métier (placeholders, HTML, cohérence)
- [ ] Validation UX (flux admin, messages d'erreur)
- [ ] Validation pédagogique (déterminisme, placeholders)

**Statut** : 📋 **En attente validation CTO** avant développement.

---

**Références** :
- Structure exercices : `backend/services/exercise_persistence_service.py`
- Validation placeholders : `backend/services/tests_dyn_handler.py` (lignes 48-57)
- Modèles Pydantic : `backend/services/exercise_persistence_service.py` (lignes 32-178)




