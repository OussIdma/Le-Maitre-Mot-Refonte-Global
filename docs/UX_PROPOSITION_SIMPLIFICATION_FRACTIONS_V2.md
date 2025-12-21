# Proposition UX Simplifiée — SIMPLIFICATION_FRACTIONS_V2
**Date :** 2025-01-XX  
**Objectif :** Simplifier l'interface admin pour les profs en masquant les paramètres techniques et en exposant uniquement 3 modes pédagogiques clairs.

---

## 🎯 Problème identifié

### État actuel (trop complexe)

L'interface admin expose **11 paramètres techniques** :
1. `difficulty` (facile/moyen/difficile) ✅ **Conservé** (nécessaire)
2. `variant_id` (A/B/C) ❌ **Technique** → à masquer
3. `pedagogy_mode` (standard/guided/diagnostic) ❌ **Technique** → à masquer
4. `hint_level` (0-3) ❌ **Technique** → à masquer
5. `include_feedback` (bool) ❌ **Technique** → à masquer
6. `allow_improper` (bool) ❌ **Technique** → à masquer
7. `allow_negative` (bool) ❌ **Technique** → à masquer
8. `force_reducible` (bool) ❌ **Technique** → à masquer
9. `max_denominator` (int) ❌ **Technique** → à masquer
10. `show_svg` (bool) ❌ **Technique** → à masquer
11. `representation` (none/number_line) ❌ **Technique** → à masquer

**Impact** : Le prof voit trop de champs techniques, ne comprend pas leur utilité, et risque de créer des configurations incohérentes.

---

## ✅ Solution proposée : UX simplifiée à 3 modes

### Principe

**Exposer uniquement 3 choix clairs pour le prof** :
- **Direct** : Exercice classique de simplification
- **Guidé** : Exercice avec méthode guidée et indices
- **Diagnostic** : Exercice d'analyse d'erreurs

**Tous les autres paramètres sont préconfigurés automatiquement** selon :
- Le niveau (CM2/6e/5e)
- Le mode choisi (Direct/Guidé/Diagnostic)
- La difficulté (facile/moyen/difficile)

---

## 📊 Structure UX proposée

### Interface admin simplifiée

```
┌─────────────────────────────────────────────────────────┐
│ Paramètres du générateur                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Mode pédagogique *                                      │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ○ Direct                                          │   │
│ │   Exercice classique de simplification            │   │
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

### Section "Paramètres techniques" (masquée par défaut)

Si le prof clique sur "Paramètres techniques masqués", afficher une section repliable avec :
- Tous les paramètres techniques (read-only ou éditables selon besoin)
- Badge "Avancé" pour indiquer que c'est pour les experts
- Avertissement : "Modifier ces paramètres peut affecter le comportement pédagogique"

---

## 🔧 Mapping Mode → Paramètres techniques

### Tableau de correspondance

| Mode Prof | `variant_id` | `pedagogy_mode` | `hint_level` | `include_feedback` | Autres paramètres |
|-----------|--------------|-----------------|--------------|-------------------|-------------------|
| **Direct** | `A` | `standard` | `0` | `False` | Selon niveau (voir presets) |
| **Guidé** | `B` | `guided` | `1-2` (selon niveau) | `True` | Selon niveau (voir presets) |
| **Diagnostic** | `C` | `diagnostic` | `0` | `True` | Selon niveau (voir presets) |

---

## 📋 Presets par niveau et mode

### Presets Direct (variant A, standard)

#### CM2 — Direct
```json
{
  "difficulty": "facile",
  "variant_id": "A",
  "pedagogy_mode": "standard",
  "hint_level": 0,
  "include_feedback": false,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 12,
  "show_svg": true,
  "representation": "number_line"
}
```

#### 6e — Direct
```json
{
  "difficulty": "moyen",
  "variant_id": "A",
  "pedagogy_mode": "standard",
  "hint_level": 0,
  "include_feedback": false,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 20,
  "show_svg": true,
  "representation": "number_line"
}
```

#### 5e — Direct
```json
{
  "difficulty": "difficile",
  "variant_id": "A",
  "pedagogy_mode": "standard",
  "hint_level": 0,
  "include_feedback": false,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 40,
  "show_svg": true,
  "representation": "number_line"
}
```

---

### Presets Guidé (variant B, guided)

#### CM2 — Guidé
```json
{
  "difficulty": "facile",
  "variant_id": "B",
  "pedagogy_mode": "guided",
  "hint_level": 1,
  "include_feedback": true,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 12,
  "show_svg": true,
  "representation": "number_line"
}
```

#### 6e — Guidé
```json
{
  "difficulty": "moyen",
  "variant_id": "B",
  "pedagogy_mode": "guided",
  "hint_level": 2,
  "include_feedback": true,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 20,
  "show_svg": true,
  "representation": "number_line"
}
```

#### 5e — Guidé
```json
{
  "difficulty": "difficile",
  "variant_id": "B",
  "pedagogy_mode": "guided",
  "hint_level": 2,
  "include_feedback": true,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 40,
  "show_svg": true,
  "representation": "number_line"
}
```

---

### Presets Diagnostic (variant C, diagnostic)

#### CM2 — Diagnostic
```json
{
  "difficulty": "facile",
  "variant_id": "C",
  "pedagogy_mode": "diagnostic",
  "hint_level": 0,
  "include_feedback": true,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 12,
  "show_svg": true,
  "representation": "number_line"
}
```

#### 6e — Diagnostic
```json
{
  "difficulty": "moyen",
  "variant_id": "C",
  "pedagogy_mode": "diagnostic",
  "hint_level": 0,
  "include_feedback": true,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 20,
  "show_svg": true,
  "representation": "number_line"
}
```

#### 5e — Diagnostic
```json
{
  "difficulty": "difficile",
  "variant_id": "C",
  "pedagogy_mode": "diagnostic",
  "hint_level": 0,
  "include_feedback": true,
  "allow_negative": false,
  "allow_improper": false,
  "force_reducible": true,
  "max_denominator": 40,
  "show_svg": true,
  "representation": "number_line"
}
```

---

## 🎨 Variantes par difficulté (dans chaque mode)

### Direct — Facile/Moyen/Difficile

| Difficulté | `max_denominator` | `force_reducible` | Notes |
|------------|-------------------|-------------------|-------|
| **Facile** | 12 | `true` | PGCD simples (2, 3, 4, 5) |
| **Moyen** | 20 | `true` | PGCD variés (2, 3, 4, 5, 6, 8, 9, 10) |
| **Difficile** | 40 | `true` | PGCD complexes (2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15) |

### Guidé — Facile/Moyen/Difficile

| Difficulté | `hint_level` | `max_denominator` | Notes |
|------------|--------------|-------------------|-------|
| **Facile** | 1 | 12 | Indices légers |
| **Moyen** | 2 | 20 | Indices modérés |
| **Difficile** | 2 | 40 | Indices modérés (même niveau que moyen) |

### Diagnostic — Facile/Moyen/Difficile

| Difficulté | `max_denominator` | Notes |
|------------|-------------------|-------|
| **Facile** | 12 | Erreurs simples à détecter |
| **Moyen** | 20 | Erreurs variées |
| **Difficile** | 40 | Erreurs complexes |

---

## 📚 Documentation pour support/QA

### Tableau récapitulatif : Mode → Paramètres fixés

| Mode Prof | Variant | Pedagogy | Hint | Feedback | Impropre | Négatif | Réductible | Max Denom | SVG | Représentation |
|-----------|---------|----------|------|----------|----------|---------|------------|-----------|-----|----------------|
| **Direct** | A | standard | 0 | ❌ | ❌ | ❌ | ✅ | Selon niveau | ✅ | number_line |
| **Guidé** | B | guided | 1-2 | ✅ | ❌ | ❌ | ✅ | Selon niveau | ✅ | number_line |
| **Diagnostic** | C | diagnostic | 0 | ✅ | ❌ | ❌ | ✅ | Selon niveau | ✅ | number_line |

### Règles de préconfiguration

1. **`variant_id`** : Toujours aligné avec le mode prof
   - Direct → `A`
   - Guidé → `B`
   - Diagnostic → `C`

2. **`pedagogy_mode`** : Toujours aligné avec le mode prof
   - Direct → `standard`
   - Guidé → `guided`
   - Diagnostic → `diagnostic`

3. **`hint_level`** : Dépend du mode et de la difficulté
   - Direct : Toujours `0` (pas d'indices)
   - Guidé : `1` (facile), `2` (moyen/difficile)
   - Diagnostic : Toujours `0` (pas d'indices, analyse d'erreurs)

4. **`include_feedback`** : Dépend du mode
   - Direct : `false` (pas de feedback)
   - Guidé : `true` (feedback activé)
   - Diagnostic : `true` (feedback activé)

5. **`allow_negative`** : Toujours `false` (sauf cas spéciaux avancés)

6. **`allow_improper`** : Toujours `false` (sauf cas spéciaux avancés)

7. **`force_reducible`** : Toujours `true` (sauf cas spéciaux avancés)

8. **`max_denominator`** : Dépend du niveau et de la difficulté
   - CM2 : 12
   - 6e : 20
   - 5e : 40

9. **`show_svg`** : Toujours `true` (sauf cas spéciaux avancés)

10. **`representation`** : Toujours `number_line` (sauf cas spéciaux avancés)

---

## 🔄 Flux de configuration proposé

### Étape 1 : Le prof sélectionne le mode

```
Prof choisit : "Guidé"
```

### Étape 2 : Le système préremplit automatiquement

```
Backend/Frontend applique le preset :
- variant_id = "B"
- pedagogy_mode = "guided"
- hint_level = 1 (si facile) ou 2 (si moyen/difficile)
- include_feedback = true
- allow_negative = false
- allow_improper = false
- force_reducible = true
- max_denominator = 12 (CM2) / 20 (6e) / 40 (5e)
- show_svg = true
- representation = "number_line"
```

### Étape 3 : Le prof peut ajuster la difficulté

```
Prof change : "facile" → "difficile"
Système ajuste automatiquement :
- hint_level reste à 2 (pour Guidé)
- max_denominator passe à 40 (si 5e)
```

### Étape 4 : (Optionnel) Le prof peut voir/éditer les paramètres techniques

```
Prof clique : "Paramètres techniques masqués"
Système affiche : Tous les paramètres en read-only ou éditables
```

---

## 🎯 Avantages de cette approche

### Pour le prof
- ✅ **3 choix clairs** : Direct, Guidé, Diagnostic
- ✅ **Pas de confusion** : Les paramètres techniques sont masqués
- ✅ **Configuration rapide** : 2 clics (mode + difficulté)
- ✅ **Cohérence garantie** : Les presets assurent des configurations valides

### Pour le support/QA
- ✅ **Documentation claire** : Tableau Mode → Paramètres
- ✅ **Tests simplifiés** : 3 modes × 3 difficultés = 9 scénarios principaux
- ✅ **Traçabilité** : Les paramètres techniques sont toujours présents (masqués mais sauvegardés)

### Pour le système
- ✅ **Rétrocompatibilité** : Les paramètres techniques existent toujours
- ✅ **Flexibilité** : Les experts peuvent toujours modifier les paramètres techniques
- ✅ **Maintenance** : Les presets centralisent la logique de configuration

---

## 🚫 Cas limites et exceptions

### Cas 1 : Prof veut des fractions négatives

**Solution** : Section "Paramètres techniques" → `allow_negative = true`

### Cas 2 : Prof veut des fractions impropres

**Solution** : Section "Paramètres techniques" → `allow_improper = true`

### Cas 3 : Prof veut désactiver le SVG

**Solution** : Section "Paramètres techniques" → `show_svg = false`

### Cas 4 : Prof veut un hint_level personnalisé

**Solution** : Section "Paramètres techniques" → `hint_level = 3` (max)

---

## 📝 Implémentation suggérée (sans code)

### Backend

1. **Créer 9 nouveaux presets** (3 modes × 3 niveaux) :
   - `CM2_direct`, `6e_direct`, `5e_direct`
   - `CM2_guided`, `6e_guided`, `5e_guided`
   - `CM2_diagnostic`, `6e_diagnostic`, `5e_diagnostic`

2. **Ajouter un champ `prof_mode` dans le schéma** (optionnel, pour traçabilité) :
   - `prof_mode`: ENUM ["direct", "guided", "diagnostic"]
   - Ce champ n'est pas utilisé par le générateur, mais permet de savoir quel mode prof a été choisi

### Frontend

1. **Modifier `GeneratorParamsForm.js`** :
   - Afficher uniquement 3 boutons radio : Direct, Guidé, Diagnostic
   - Masquer tous les autres paramètres par défaut
   - Ajouter un bouton "Paramètres techniques" (repliable)
   - Lors du choix d'un mode, appliquer automatiquement le preset correspondant

2. **Logique de mapping** :
   - Mode "Direct" → Preset `{niveau}_direct`
   - Mode "Guidé" → Preset `{niveau}_guided`
   - Mode "Diagnostic" → Preset `{niveau}_diagnostic`
   - Ajuster `hint_level` selon la difficulté (pour Guidé)

---

## ✅ Checklist de validation

### UX
- [ ] 3 modes clairs affichés (Direct, Guidé, Diagnostic)
- [ ] Paramètres techniques masqués par défaut
- [ ] Section "Paramètres techniques" repliable
- [ ] Presets appliqués automatiquement

### Backend
- [ ] 9 presets créés (3 modes × 3 niveaux)
- [ ] Presets alignés avec les tableaux ci-dessus
- [ ] Rétrocompatibilité : anciens exercices fonctionnent toujours

### Tests
- [ ] Test Direct CM2/6e/5e → Paramètres corrects
- [ ] Test Guidé CM2/6e/5e → Paramètres corrects
- [ ] Test Diagnostic CM2/6e/5e → Paramètres corrects
- [ ] Test modification difficulté → Paramètres ajustés
- [ ] Test section "Paramètres techniques" → Affichage correct

---

## 📚 Documentation utilisateur

### Guide rapide pour les profs

**3 modes disponibles** :
1. **Direct** : Exercice classique de simplification
2. **Guidé** : Exercice avec méthode guidée et indices
3. **Diagnostic** : Exercice d'analyse d'erreurs

**Comment utiliser** :
1. Choisir le mode (Direct/Guidé/Diagnostic)
2. Choisir la difficulté (Facile/Moyen/Difficile)
3. Sauvegarder

**Paramètres techniques** :
- Masqués par défaut pour simplifier
- Accessibles via "Paramètres techniques masqués" si besoin

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Proposition prête pour validation

