# Procédure complète — Ajout d'un template dynamique

**Version :** 1.0.0  
**Date :** 2025-12-21  
**Objectif :** Procédure exhaustive pour créer un exercice dynamique sans bug, utilisable par un agent IA.

---

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Étape 1 : Identifier le générateur](#étape-1--identifier-le-générateur)
3. [Étape 2 : Récupérer les templates de référence](#étape-2--récupérer-les-templates-de-référence)
4. [Étape 3 : Extraire les placeholders attendus](#étape-3--extraire-les-placeholders-attendus)
5. [Étape 4 : Créer l'exercice dynamique via l'admin](#étape-4--créer-lexercice-dynamique-via-ladmin)
6. [Étape 5 : Valider les placeholders](#étape-5--valider-les-placeholders)
7. [Étape 6 : Tester la génération](#étape-6--tester-la-génération)
8. [Checklist complète](#checklist-complète)
9. [Dépannage](#dépannage)

---

## ✅ Prérequis

- [ ] Le générateur dynamique existe et est enregistré dans `GeneratorFactory`
  - **⚠️ Si le générateur n'existe pas** : Voir `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`
- [ ] Le chapitre existe dans le curriculum avec `pipeline="TEMPLATE"` ou `pipeline="MIXED"`
- [ ] Accès à l'interface admin : `http://localhost:3000/admin/curriculum/{chapter_code}/exercises`
- [ ] Backend et MongoDB opérationnels
- [ ] Backend rebuild/restart effectué après toute modification de code Python

---

## 🔍 Étape 1 : Identifier le générateur

### 1.1 Vérifier que le générateur existe

**Commande :**
```bash
curl -s http://localhost:8000/api/v1/exercises/generators | jq '.[] | select(.key == "VOTRE_GENERATEUR_KEY")'
```

**Résultat attendu :** Le générateur doit apparaître dans la liste.

### 1.2 Récupérer le schéma complet du générateur

**Commande :**
```bash
curl -s http://localhost:8000/api/v1/exercises/generators/VOTRE_GENERATEUR_KEY/full-schema | jq '.'
```

**Informations à noter :**
- `meta.key` : clé du générateur (ex: `SIMPLIFICATION_FRACTIONS_V1`)
- `meta.exercise_type` : type d'exercice (ex: `FRACTIONS`)
- `meta.niveaux` : niveaux supportés (ex: `["CM2", "6e", "5e"]`)

---

## 📝 Étape 2 : Récupérer les templates de référence

### 2.1 Localiser le fichier du générateur

**Chemin :** `backend/generators/{generator_key_lowercase}.py`

**Exemple :**
- `SIMPLIFICATION_FRACTIONS_V1` → `backend/generators/simplification_fractions_v1.py`

### 2.2 Extraire les templates de référence

**Dans le fichier du générateur, chercher :**
- `ENONCE_TEMPLATE` (ou `ENONCE_TEMPLATE_HTML`)
- `SOLUTION_TEMPLATE` (ou `SOLUTION_TEMPLATE_HTML`)

**Exemple (SIMPLIFICATION_FRACTIONS_V1) :**
```python
ENONCE_TEMPLATE = "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>"

SOLUTION_TEMPLATE = """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""
```

**⚠️ IMPORTANT :** Utiliser **EXACTEMENT** ces templates comme base. Ne pas copier des templates d'un autre générateur.

---

## 🔎 Étape 3 : Extraire les placeholders attendus

### 3.1 Méthode 1 : Depuis les templates de référence

**Extraction manuelle :**
- Chercher tous les `{{variable}}` dans `ENONCE_TEMPLATE` et `SOLUTION_TEMPLATE`
- Lister les placeholders uniques

**Exemple :**
- `{{fraction}}`, `{{step1}}`, `{{step2}}`, `{{step3}}`, `{{fraction_reduite}}`

### 3.2 Méthode 2 : Tester la génération du générateur

**Commande :**
```bash
curl -X POST http://localhost:8000/api/v1/exercises/generators/preview-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "VOTRE_GENERATEUR_KEY",
    "difficulty": "moyen",
    "seed": 42
  }' | jq '.variables | keys'
```

**Résultat attendu :** Liste des clés de variables générées.

**⚠️ VÉRIFICATION CRITIQUE :**
- Tous les placeholders des templates doivent être présents dans les variables générées
- Si un placeholder n'est pas généré → **ERREUR BLOQUANTE**

### 3.3 Méthode 3 : Lire le code du générateur

**Dans `generate()` du générateur, identifier :**
- Les variables retournées dans `result["variables"]`
- Les variables retournées dans `result["results"]`

**Note :** Les deux sont fusionnés pour le rendu des templates.

---

## 🎨 Étape 4 : Créer l'exercice dynamique via l'admin

### 4.1 Accéder à la page admin

**URL :** `http://localhost:3000/admin/curriculum/{chapter_code}/exercises`

**Exemple :** `http://localhost:3000/admin/curriculum/6e_AA_TEST/exercises`

### 4.2 Remplir le formulaire

**Champs obligatoires :**

1. **Titre** (optionnel mais recommandé)
   - Exemple : "Simplification de fractions - Niveau difficile"

2. **Générateur** (`generator_key`)
   - Sélectionner dans la liste déroulante
   - ⚠️ Vérifier que le générateur correspond bien au chapitre

3. **Difficulté** (`difficulty`)
   - `facile`, `moyen`, ou `difficile`

4. **Offre** (`offer`)
   - `free` ou `pro`

5. **Exercice dynamique** (`is_dynamic`)
   - ✅ Cocher la case

6. **Paramètres du générateur** (`variables`) — Optionnel mais recommandé
   - Après avoir sélectionné le générateur, un formulaire de paramètres apparaît
   - Les paramètres disponibles dépendent du générateur (ex: `allow_negative`, `max_denominator`, `show_svg`, etc.)
   - **Presets disponibles** : Certains générateurs proposent des presets pré-configurés (ex: "CM2 Facile", "6e Moyen")
   - **Valeurs par défaut** : Si aucun paramètre n'est renseigné, les valeurs par défaut du générateur seront utilisées
   - ⚠️ **Important** : Ces paramètres contrôlent le comportement du générateur, pas les templates
   - Exemple pour `SIMPLIFICATION_FRACTIONS_V1` :
     - `difficulty` : niveau de difficulté (déjà défini dans le champ "Difficulté" ci-dessus)
     - `allow_negative` : autoriser les fractions négatives
     - `max_denominator` : dénominateur maximum (ex: 60)
     - `force_reducible` : forcer une fraction réductible (PGCD > 1)
     - `show_svg` : afficher le SVG de la droite graduée
     - `representation` : type de représentation visuelle ("none" ou "number_line")

7. **Template énoncé** (`enonce_template_html`)
   - **COPIER EXACTEMENT** le `ENONCE_TEMPLATE` du générateur
   - ⚠️ Ne pas modifier les placeholders
   - ⚠️ Ne pas copier un template d'un autre générateur

8. **Template solution** (`solution_template_html`)
   - **COPIER EXACTEMENT** le `SOLUTION_TEMPLATE` du générateur
   - ⚠️ Même précaution que pour l'énoncé

9. **Variants** (`template_variants`) — Optionnel
   - Si plusieurs variants sont souhaités, ajouter des variants
   - Chaque variant doit utiliser les mêmes placeholders que le template principal

### 4.3 Sauvegarder

**Cliquer sur "Créer l'exercice" ou "Enregistrer"**

**Vérification :**
- L'exercice apparaît dans la liste
- Le champ `is_dynamic` est à `true`
- Le champ `generator_key` est correct
- Les paramètres du générateur (si configurés) sont sauvegardés dans le champ `variables`

---

## ✅ Étape 5 : Valider les placeholders

### 5.1 Vérification automatique (script Python)

**⚠️ RECOMMANDÉ : Utiliser le script de validation avant de sauvegarder**

**Méthode 1 : Validation depuis templates (avant sauvegarde)**
```bash
docker compose exec backend python /app/backend/scripts/validate_template_placeholders.py \
  --generator SIMPLIFICATION_FRACTIONS_V1 \
  --enonce-template "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>" \
  --solution-template "<ol><li>{{step1}}</li><li>{{step2}}</li><li>{{step3}}</li><li><strong>Résultat :</strong> {{fraction_reduite}}</li></ol>" \
  --difficulty moyen
```

**Méthode 2 : Validation depuis DB (après sauvegarde)**
```bash
docker compose exec backend python /app/backend/scripts/validate_template_placeholders.py \
  --chapter-code 6E_AA_TEST \
  --exercise-id 1
```

**Résultat attendu :**
- ✅ `Validation réussie`
- ❌ Si erreur → **CORRIGER IMMÉDIATEMENT** avant de continuer

### 5.2 Vérification automatique (via API)

**Alternative : Utiliser l'API preview**
```bash
# Tester la génération avec preview
curl -X POST http://localhost:8000/api/v1/exercises/generators/preview-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "VOTRE_GENERATEUR_KEY",
    "difficulty": "moyen",
    "seed": 42,
    "enonce_template_html": "TEMPLATE_ENONCE",
    "solution_template_html": "TEMPLATE_SOLUTION"
  }' | jq '.errors'
```

**Résultat attendu :**
- `errors` doit être un tableau vide `[]`
- Si des erreurs apparaissent → **CORRIGER IMMÉDIATEMENT**

### 5.3 Vérification manuelle

**Checklist :**
- [ ] Tous les placeholders de l'énoncé sont présents dans les variables générées
- [ ] Tous les placeholders de la solution sont présents dans les variables générées
- [ ] Aucun placeholder d'un autre générateur n'est présent (ex: `axe_equation` pour SIMPLIFICATION_FRACTIONS_V1)
- [ ] Les placeholders sont correctement formatés : `{{variable}}` (pas `{{ variable }}` ou `{variable}`)

---

## 🧪 Étape 6 : Tester la génération

### 6.1 Test via l'interface élève

**URL :** `http://localhost:3000/generate`

**Actions :**
1. Sélectionner le niveau (ex: `6e`)
2. Sélectionner le domaine
3. Sélectionner le chapitre
4. Sélectionner la difficulté
5. Cliquer sur "Générer"

**Résultat attendu :**
- ✅ Exercice généré avec succès
- ✅ Énoncé affiché correctement (pas de `{{variable}}` visible)
- ✅ Solution affichée correctement
- ✅ SVG affiché si applicable

### 6.2 Test via API

**Commande :**
```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "difficile",
    "offer": "free",
    "seed": 42
  }' | jq '.enonce_html, .solution_html'
```

**Résultat attendu :**
- `enonce_html` ne contient **AUCUN** `{{variable}}`
- `solution_html` ne contient **AUCUN** `{{variable}}`
- Les valeurs sont correctement remplacées

### 6.3 Vérifier les logs backend

**Commande :**
```bash
docker compose logs backend --tail 50 | grep -i "PIPELINE\|UNRESOLVED\|6e_AA_TEST"
```

**Résultat attendu :**
- ✅ `[PIPELINE] ✅ Exercice dynamique généré (MIXED, priorité dynamique)`
- ❌ **AUCUN** `UNRESOLVED_PLACEHOLDERS`
- ❌ **AUCUN** `CHAPITRE NON MAPPÉ`

---

## 📋 Checklist complète

### Avant de créer l'exercice

- [ ] Le générateur existe et est enregistré dans `GeneratorFactory`
- [ ] Le chapitre existe avec `pipeline="TEMPLATE"` ou `pipeline="MIXED"`
- [ ] Les templates de référence ont été extraits du fichier du générateur
- [ ] Les placeholders attendus ont été identifiés
- [ ] Un test de génération a été effectué pour vérifier les variables disponibles

### Lors de la création

- [ ] Le `generator_key` sélectionné correspond au générateur souhaité
- [ ] Le template énoncé est **EXACTEMENT** copié depuis `ENONCE_TEMPLATE` du générateur
- [ ] Le template solution est **EXACTEMENT** copié depuis `SOLUTION_TEMPLATE` du générateur
- [ ] Aucun placeholder d'un autre générateur n'est présent
- [ ] Les variants (si présents) utilisent les mêmes placeholders

### Après la création

- [ ] Validation automatique des placeholders (API preview)
- [ ] Test de génération via l'interface élève
- [ ] Test de génération via l'API
- [ ] Vérification des logs backend (pas d'erreur `UNRESOLVED_PLACEHOLDERS`)
- [ ] Vérification que l'énoncé/solution ne contient pas de `{{variable}}` visible

---

## 🔧 Dépannage

### Erreur : `UNRESOLVED_PLACEHOLDERS`

**Symptôme :**
```
[ERROR] UNRESOLVED_PLACEHOLDERS pour ex ex_6e_aa_test_1_...
restants: ['variable1', 'variable2']
```

**Causes possibles :**
1. Template copié depuis un autre générateur
2. Placeholder mal orthographié
3. Variable non générée par le générateur

**Solution :**
1. Vérifier que le template correspond au générateur
2. Comparer les placeholders avec les variables générées (étape 3.2)
3. Corriger le template en utilisant les templates de référence

### Erreur : `CHAPITRE NON MAPPÉ`

**Symptôme :**
```
❌ CHAPITRE NON MAPPÉ : 'AA TEST'
```

**Causes possibles :**
1. Erreur `UNRESOLVED_PLACEHOLDERS` → fallback pipeline statique → chapitre non mappé
2. Pipeline incorrect (`SPEC` au lieu de `TEMPLATE` ou `MIXED`)
3. Aucun exercice dynamique en DB

**Solution :**
1. Vérifier les logs backend pour `UNRESOLVED_PLACEHOLDERS`
2. Corriger les templates si nécessaire
3. Vérifier le pipeline du chapitre
4. Vérifier qu'au moins un exercice dynamique existe en DB

### Erreur : Générateur non trouvé

**Symptôme :**
```
generator_key not found: VOTRE_GENERATEUR_KEY
```

**Causes possibles :**
1. Générateur non enregistré dans `GeneratorFactory`
2. Import manquant dans `backend/generators/factory.py`

**Solution :**
1. Vérifier que le générateur est importé dans `factory.py`
2. Vérifier que le décorateur `@GeneratorFactory.register` est présent
3. Redémarrer le backend

---

## 📚 Exemples

### Exemple 1 : SIMPLIFICATION_FRACTIONS_V1

**Générateur :** `SIMPLIFICATION_FRACTIONS_V1`  
**Fichier :** `backend/generators/simplification_fractions_v1.py`

**Templates de référence :**
```html
<!-- Énoncé -->
<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>

<!-- Solution -->
<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>
```

**Placeholders attendus :**
- `fraction`, `step1`, `step2`, `step3`, `fraction_reduite`

**Variables générées (exemple) :**
```json
{
  "fraction": "18/24",
  "n": 18,
  "d": 24,
  "pgcd": 6,
  "n_red": 3,
  "d_red": 4,
  "fraction_reduite": "3/4",
  "step1": "PGCD(18,24) = 6",
  "step2": "On divise numérateur et dénominateur par 6",
  "step3": "18 ÷ 6 = 3, 24 ÷ 6 = 4",
  "is_irreductible": false,
  "difficulty": "moyen"
}
```

**✅ Validation :** Tous les placeholders sont présents dans les variables.

---

## 🎯 Règles d'or

1. **Toujours utiliser les templates de référence du générateur**
   - Ne jamais copier un template d'un autre générateur
   - Ne jamais inventer des placeholders

2. **Valider avant de sauvegarder**
   - Utiliser l'API preview pour vérifier les placeholders
   - Tester la génération avant de considérer l'exercice terminé

3. **Vérifier les logs**
   - Après chaque création, vérifier les logs backend
   - Chercher `UNRESOLVED_PLACEHOLDERS` ou autres erreurs

4. **Documenter les variants**
   - Si plusieurs variants sont créés, documenter les différences
   - S'assurer que tous les variants utilisent les mêmes placeholders

---

---

## 🔗 Procédure complémentaire

**Si vous devez créer un nouveau générateur** (pas juste ajouter un template) :
👉 Voir `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`

Cette procédure couvre :
- Création complète d'un générateur (fichier, imports, métadonnées, schéma, tests)
- Enregistrement dans `GeneratorFactory`
- Pièges courants et solutions
- Validation et déploiement

---

**Document créé le :** 2025-12-21  
**Dernière mise à jour :** 2025-01-XX  
**Statut :** ✅ Validé

