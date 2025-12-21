# Tableau de référence — Mode Prof → Paramètres techniques
**Générateur :** SIMPLIFICATION_FRACTIONS_V2  
**Date :** 2025-01-XX  
**Usage :** Support / QA / Documentation

---

## 📊 Tableau récapitulatif

| Mode Prof | `variant_id` | `pedagogy_mode` | `hint_level` | `include_feedback` | `allow_improper` | `allow_negative` | `force_reducible` | `max_denominator` | `show_svg` | `representation` |
|-----------|--------------|-----------------|--------------|-------------------|------------------|------------------|-------------------|-------------------|------------|------------------|
| **Direct** | `A` | `standard` | `0` | `false` | `false` | `false` | `true` | 12 (CM2)<br>20 (6e)<br>40 (5e) | `true` | `number_line` |
| **Guidé** | `B` | `guided` | `1` (facile)<br>`2` (moyen/difficile) | `true` | `false` | `false` | `true` | 12 (CM2)<br>20 (6e)<br>40 (5e) | `true` | `number_line` |
| **Diagnostic** | `C` | `diagnostic` | `0` | `true` | `false` | `false` | `true` | 12 (CM2)<br>20 (6e)<br>40 (5e) | `true` | `number_line` |

---

## 🔍 Détails par mode

### Mode "Direct"

**Description** : Exercice classique de simplification de fractions.

**Paramètres fixes** :
- `variant_id`: `A`
- `pedagogy_mode`: `standard`
- `hint_level`: `0` (pas d'indices)
- `include_feedback`: `false` (pas de feedback)
- `allow_improper`: `false`
- `allow_negative`: `false`
- `force_reducible`: `true`
- `show_svg`: `true`
- `representation`: `number_line`

**Paramètres variables** :
- `difficulty`: `facile` / `moyen` / `difficile` (choisi par le prof)
- `max_denominator`: 12 (CM2), 20 (6e), 40 (5e) (selon niveau)

**Résultat attendu** :
- Énoncé : "Simplifier la fraction : X/Y"
- Solution : Étapes de calcul avec PGCD

---

### Mode "Guidé"

**Description** : Exercice avec méthode guidée et indices contextuels.

**Paramètres fixes** :
- `variant_id`: `B`
- `pedagogy_mode`: `guided`
- `include_feedback`: `true` (feedback activé)
- `allow_improper`: `false`
- `allow_negative`: `false`
- `force_reducible`: `true`
- `show_svg`: `true`
- `representation`: `number_line`

**Paramètres variables** :
- `difficulty`: `facile` / `moyen` / `difficile` (choisi par le prof)
- `hint_level`: `1` (si facile), `2` (si moyen/difficile)
- `max_denominator`: 12 (CM2), 20 (6e), 40 (5e) (selon niveau)

**Résultat attendu** :
- Énoncé : "Simplifier la fraction : X/Y" + indice contextuel
- Solution : Méthode guidée + étapes de calcul

---

### Mode "Diagnostic"

**Description** : Exercice d'analyse d'erreurs (fausse simplification à analyser).

**Paramètres fixes** :
- `variant_id`: `C`
- `pedagogy_mode`: `diagnostic`
- `hint_level`: `0` (pas d'indices)
- `include_feedback`: `true` (feedback activé)
- `allow_improper`: `false`
- `allow_negative`: `false`
- `force_reducible`: `true`
- `show_svg`: `true`
- `representation`: `number_line`

**Paramètres variables** :
- `difficulty`: `facile` / `moyen` / `difficile` (choisi par le prof)
- `max_denominator`: 12 (CM2), 20 (6e), 40 (5e) (selon niveau)

**Résultat attendu** :
- Énoncé : "Analyse cette simplification : Fraction initiale X/Y, Simplification proposée Z/W. Cette simplification est-elle correcte ?"
- Solution : Vérification + conclusion + simplification correcte

---

## 📋 Presets backend (référence technique)

### Presets Direct

| Clé | Niveau | Difficulté | `max_denominator` |
|-----|--------|------------|-------------------|
| `CM2_direct` | CM2 | facile | 12 |
| `6e_direct` | 6e | moyen | 20 |
| `5e_direct` | 5e | difficile | 40 |

### Presets Guidé

| Clé | Niveau | Difficulté | `hint_level` | `max_denominator` |
|-----|--------|------------|--------------|-------------------|
| `CM2_guided` | CM2 | facile | 1 | 12 |
| `6e_guided` | 6e | moyen | 2 | 20 |
| `5e_guided` | 5e | difficile | 2 | 40 |

### Presets Diagnostic

| Clé | Niveau | Difficulté | `max_denominator` |
|-----|--------|------------|-------------------|
| `CM2_diagnostic` | CM2 | facile | 12 |
| `6e_diagnostic` | 6e | moyen | 20 |
| `5e_diagnostic` | 5e | difficile | 40 |

---

## 🧪 Scénarios de test

### Test 1 : Direct CM2 Facile
- **Mode** : Direct
- **Niveau** : CM2
- **Difficulté** : Facile
- **Paramètres attendus** :
  - `variant_id`: `A`
  - `pedagogy_mode`: `standard`
  - `hint_level`: `0`
  - `include_feedback`: `false`
  - `max_denominator`: `12`
- **Résultat** : Exercice classique avec fractions simples

### Test 2 : Guidé 6e Moyen
- **Mode** : Guidé
- **Niveau** : 6e
- **Difficulté** : Moyen
- **Paramètres attendus** :
  - `variant_id`: `B`
  - `pedagogy_mode`: `guided`
  - `hint_level`: `2`
  - `include_feedback`: `true`
  - `max_denominator`: `20`
- **Résultat** : Exercice guidé avec indices niveau 2

### Test 3 : Diagnostic 5e Difficile
- **Mode** : Diagnostic
- **Niveau** : 5e
- **Difficulté** : Difficile
- **Paramètres attendus** :
  - `variant_id`: `C`
  - `pedagogy_mode`: `diagnostic`
  - `hint_level`: `0`
  - `include_feedback`: `true`
  - `max_denominator`: `40`
- **Résultat** : Exercice diagnostic avec fractions complexes

---

## ⚠️ Cas d'erreur courants

### Erreur 1 : Mode "Direct" mais `variant_id = "B"`
**Cause** : Preset mal appliqué ou modification manuelle  
**Solution** : Vérifier que le preset `{niveau}_direct` est appliqué

### Erreur 2 : Mode "Guidé" mais `hint_level = 0`
**Cause** : Preset mal appliqué  
**Solution** : Vérifier que `hint_level` est à `1` (facile) ou `2` (moyen/difficile)

### Erreur 3 : Mode "Diagnostic" mais `include_feedback = false`
**Cause** : Preset mal appliqué  
**Solution** : Vérifier que `include_feedback` est à `true`

---

## 📝 Notes techniques

- **Rétrocompatibilité** : Les exercices existants avec paramètres techniques explicites continuent de fonctionner
- **Flexibilité** : Les experts peuvent toujours modifier les paramètres techniques via la section "Paramètres techniques"
- **Traçabilité** : Le champ `prof_mode` (si ajouté) permet de savoir quel mode prof a été choisi

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Référence pour support/QA

