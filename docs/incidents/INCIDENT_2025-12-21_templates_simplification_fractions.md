# Incident — Templates incorrects pour SIMPLIFICATION_FRACTIONS_V1

**ID :** INCIDENT_2025-12-21_templates_simplification_fractions  
**Date :** 2025-12-21  
**Sévérité :** Bloquant (génération d'exercices)

---

## 📋 Symptôme

Lors de la génération d'exercices pour le chapitre `6e_AA_TEST` (pipeline MIXED) :
- Erreur `UNRESOLVED_PLACEHOLDERS` 
- Fallback vers pipeline statique
- Erreur finale : `❌ CHAPITRE NON MAPPÉ : 'AA TEST'`

**Message d'erreur complet :**
```
❌ CHAPITRE NON MAPPÉ : 'AA TEST'
Niveau : 6e
Le chapitre existe dans le curriculum mais aucun générateur n'est défini.
→ Ajoutez ce chapitre au mapping dans _get_exercise_types_for_chapter()
```

---

## 🔍 Root Cause (prouvée)

**Analyse des logs backend :**
```
[ERROR] UNRESOLVED_PLACEHOLDERS pour ex ex_6e_aa_test_1_...
restants: ['axe_equation', 'axe_label', 'figure_description', 'points_labels', 'points_symmetric_labels']
clés fournies: ['d', 'd_red', 'difficulty', 'fraction', 'fraction_reduite', 'is_irreductible', 'n', 'n_red', 'pgcd', 'step1', 'step2', 'step3']
```

**Problème identifié :**
1. Le chapitre `6e_AA_TEST` a des exercices dynamiques avec `generator_key=SIMPLIFICATION_FRACTIONS_V1`
2. Le générateur `SIMPLIFICATION_FRACTIONS_V1` génère correctement les variables : `fraction`, `n`, `d`, `pgcd`, `n_red`, `d_red`, `fraction_reduite`, `step1`, `step2`, `step3`, etc.
3. **MAIS** les templates en DB utilisent des placeholders de **SYMETRIE_AXIALE** : `axe_equation`, `axe_label`, `figure_description`, `points_labels`, `points_symmetric_labels`
4. Ces placeholders ne sont pas générés par `SIMPLIFICATION_FRACTIONS_V1`
5. Erreur `UNRESOLVED_PLACEHOLDERS` → fallback pipeline statique → fallback legacy → "CHAPITRE NON MAPPÉ"

**Cause racine :** Les templates en DB ont été créés avec des placeholders incorrects (probablement copiés depuis un exercice SYMETRIE_AXIALE).

---

## ✅ Fix appliqué

**Script de migration créé :** `backend/migrations/005_fix_simplification_fractions_templates.py`

**Actions effectuées :**
1. Détection automatique des exercices avec `generator_key=SIMPLIFICATION_FRACTIONS_V1` ayant des placeholders incorrects
2. Remplacement des templates énoncé/solution par les templates corrects :
   - **Énoncé :** `<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>`
   - **Solution :** Template avec `{{step1}}`, `{{step2}}`, `{{step3}}`, `{{fraction_reduite}}`
3. Correction également des `template_variants` si présents

**Résultat de la migration :**
```
✅ Migration terminée: 1 exercices corrigés, 0 ignorés, 0 erreurs
  - Exercice 6E_AA_TEST/1 corrigé
  - 3 variants corrigés (v1, v2, v3)
```

---

## 🧪 Tests / Preuve

**Avant le fix :**
```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "difficile", "offer": "free"}'
```
→ Erreur `UNRESOLVED_PLACEHOLDERS` → `CHAPITRE NON MAPPÉ`

**Après le fix :**
```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "difficile", "offer": "free", "seed": 42}'
```
→ ✅ Exercice généré avec succès

**Logs backend après fix :**
```
[INFO] [PIPELINE] ✅ Exercice dynamique généré (MIXED, priorité dynamique): 
  chapter_code=6E_AA_TEST, exercise_id=1
```

**Vérification des placeholders :**
- ✅ Tous les placeholders utilisés dans les templates sont présents dans les variables générées
- ✅ Plus d'erreur `UNRESOLVED_PLACEHOLDERS`
- ✅ Pipeline MIXED fonctionne correctement

---

## 🔧 Commandes de rebuild / restart

**Pour appliquer le fix :**
```bash
# 1. Reconstruire l'image backend (inclut le script de migration)
docker compose build backend

# 2. Redémarrer le backend
docker compose up -d backend

# 3. Exécuter la migration
docker compose exec backend python /app/backend/migrations/005_fix_simplification_fractions_templates.py
```

**Vérification :**
```bash
# Tester la génération
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "difficile", "offer": "free", "seed": 42}'
```

---

## 📝 Notes

- Le script de migration est **idempotent** : peut être relancé sans erreur
- Le script détecte automatiquement les exercices à corriger
- Les `template_variants` sont également corrigés si présents
- Le problème était spécifique aux exercices avec `SIMPLIFICATION_FRACTIONS_V1` ayant des templates incorrects

---

## 🔄 Prévention

**Recommandations :**
1. Lors de la création d'un exercice dynamique, valider que les placeholders des templates correspondent aux variables générées par le générateur
2. Ajouter une validation côté admin pour vérifier la cohérence `generator_key` ↔ placeholders
3. Utiliser les templates de référence fournis dans le générateur (ex: `ENONCE_TEMPLATE`, `SOLUTION_TEMPLATE` dans `simplification_fractions_v1.py`)

---

**Document créé le :** 2025-12-21  
**Statut :** ✅ Résolu

