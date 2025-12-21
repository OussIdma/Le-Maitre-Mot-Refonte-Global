# Générateur SIMPLIFICATION_FRACTIONS_V2 — Documentation Fonctionnelle

**Version :** 2.0.0  
**Date :** 2025-01-XX  
**Type :** Documentation fonctionnelle des paramètres (mode d'emploi pratique)

---

## 🎯 Vue d'ensemble

Ce document décrit **concrètement** ce que fait chaque paramètre du générateur `SIMPLIFICATION_FRACTIONS_V2`, sans théorie pédagogique.  
**Objectif :** permettre aux développeurs frontend et aux admins de comprendre rapidement l'effet de chaque paramètre.

---

## 🎛️ Paramètres GOLD — À quoi ils servent concrètement

### 1️⃣ `difficulty` : niveau de calcul

**👉 Change les nombres, la complexité, les pièges**

- **`facile`** : petits nombres, cas évidents
- **`moyen`** : PGCD non trivial, vigilance requise
- **`difficile`** : grands nombres, signes, cas limites

**➡️ Agit sur les données générées, pas sur le texte.**

**Exemple :**
- `difficulty="facile"` → peut générer `6/8` (PGCD = 2, évident)
- `difficulty="difficile"` → peut générer `42/56` (PGCD = 14, moins évident)

---

### 2️⃣ `variant_id` (A / B / C) : type d'énoncé

**👉 Change la forme de la question**

- **`A`** : direct (calcul pur)
- **`B`** : guidé (méthode attendue)
- **`C`** : diagnostic (juger une erreur)

**➡️ Même données, énoncé différent.**

**Exemple avec la fraction `12/18` :**
- `variant_id="A"` → "Simplifier la fraction : 12/18"
- `variant_id="B"` → "Simplifier la fraction : 12/18" + indice selon `hint_level`
- `variant_id="C"` → "Analyse cette simplification : 12/18 = 6/18 (proposée). Est-elle correcte ?"

---

### 3️⃣ `pedagogy_mode` : scénario pédagogique

**👉 Change l'accompagnement**

- **`standard`** : pas d'aide
- **`guided`** : indices activables
- **`diagnostic`** : raisonnement critique

**➡️ Contrôle indices + feedback, pas les calculs.**

**Exemple :**
- `pedagogy_mode="standard"` → exercice "sec", pas d'indices
- `pedagogy_mode="guided"` → indices disponibles selon `hint_level`
- `pedagogy_mode="diagnostic"` → exercice de type "vérifier si c'est correct"

---

### 4️⃣ `hint_level` (0 → 3) : niveau d'aide

**👉 Sélectionne l'indice fourni**

- **`0`** : aucun indice
- **`1`** : rappel simple (ex: "Le PGCD de 12 et 18 est 6")
- **`2`** : méthode (ex: "Divise 12 par 6 et 18 par 6")
- **`3`** : quasi-solution (ex: "12 ÷ 6 = 2 et 18 ÷ 6 = 3")

**➡️ Déterministe, pas adaptatif.**

**Note :** Les indices ne s'accumulent pas. Si `hint_level=2`, seul l'indice de niveau 2 est fourni (pas les niveaux 1 et 2).

---

### 5️⃣ `include_feedback` : messages d'erreurs

**👉 Ajoute ou non les feedbacks prêts à l'emploi**

- **`true`** : messages disponibles (ex: "Erreur : vous avez divisé seulement le numérateur...")
- **`false`** : exercice "sec", pas de feedback pré-construit

**➡️ N'influence pas la correction, seulement l'UX.**

**Exemple de feedback disponible :**
```json
{
  "divide_numerator_only": {
    "message": "Erreur : vous avez divisé seulement le numérateur. Il faut diviser le numérateur ET le dénominateur par le même nombre."
  }
}
```

---

### 6️⃣ `force_reducible` : PGCD garanti

**👉 Contrôle si la fraction doit être réductible**

- **`true`** : PGCD > 1 obligatoire (fraction toujours réductible)
- **`false`** : PGCD = 1 possible (fraction irréductible autorisée)

**➡️ Sert à couvrir le chapitre "fraction irréductible".**

**Exemple :**
- `force_reducible=true` → génère toujours `12/18` (PGCD = 6) ou `8/12` (PGCD = 4)
- `force_reducible=false` → peut générer `7/11` (PGCD = 1, irréductible)

---

### 7️⃣ `allow_negative` : signe

**👉 Autorise ou non les fractions négatives**

- **`true`** : fractions négatives possibles (ex: `-12/18`)
- **`false`** : fractions positives uniquement

**➡️ Signe toujours sur le numérateur.**

**Exemple :**
- `allow_negative=true` → peut générer `-12/18` (pas `12/-18`)
- `allow_negative=false` → génère uniquement `12/18`, `8/12`, etc.

---

### 8️⃣ `allow_improper` : fraction impropre

**👉 Autorise n ≥ d**

- **`false`** : fractions propres uniquement (< 1, ex: `3/4`, `7/8`)
- **`true`** : fractions ≥ 1 autorisées (ex: `5/4`, `8/3`)

**➡️ Chapitres avancés uniquement.**

**Exemple :**
- `allow_improper=false` → génère `3/4`, `7/8`, `5/6` (toujours < 1)
- `allow_improper=true` → peut générer `5/4`, `8/3`, `12/5` (≥ 1)

---

### 9️⃣ `show_svg` / `representation` : affichage visuel

**👉 Contrôle l'affichage visuel**

- **`show_svg=true`** + **`representation="number_line"`** : SVG de droite graduée affiché
- **`show_svg=false`** ou **`representation="none"`** : pas de SVG

**➡️ Données identiques, SVG présent ou non.**

**Note :** Le SVG montre la position de la fraction sur une droite graduée de 0 à 1 (pour fractions propres).

---

## 🔑 Règle d'utilisation SIMPLE (site)

### Mapping pratique

| Besoin | Paramètre à changer |
|--------|-------------------|
| Niveau / Chapitre | Fixe `generator_key` (déjà fait) |
| Facile / Moyen / Difficile | Change `difficulty` |
| Changer l'exercice (même type) | Change le `seed` |
| Changer la formulation | Change `variant_id` |
| Besoin d'aide | Augmente `hint_level` |
| Fractions irréductibles | `force_reducible=false` |
| Fractions négatives | `allow_negative=true` |
| Fractions impropres | `allow_improper=true` |
| Pas de visuel | `show_svg=false` |

---

## 🧠 En résumé (très important)

✅ **Les paramètres ne cassent rien**  
✅ **Ils ne changent jamais la structure de sortie**  
✅ **Ils permettent de couvrir tous les chapitres avec un seul générateur**

👉 **C'est exactement pour ça que l'ÉTALON est robuste.**

---

## 📋 Exemples de combinaisons par chapitre

### Chapitre "Simplification de fractions" (6e, niveau moyen)

```json
{
  "difficulty": "moyen",
  "variant_id": "A",
  "pedagogy_mode": "standard",
  "hint_level": 0,
  "include_feedback": false,
  "force_reducible": true,
  "allow_negative": false,
  "allow_improper": false,
  "show_svg": true,
  "representation": "number_line"
}
```

### Chapitre "Fractions irréductibles" (5e)

```json
{
  "difficulty": "moyen",
  "variant_id": "A",
  "pedagogy_mode": "standard",
  "hint_level": 0,
  "include_feedback": false,
  "force_reducible": false,  // ← Changé
  "allow_negative": false,
  "allow_improper": false,
  "show_svg": true,
  "representation": "number_line"
}
```

### Chapitre "Fractions relatives" (5e)

```json
{
  "difficulty": "moyen",
  "variant_id": "A",
  "pedagogy_mode": "standard",
  "hint_level": 0,
  "include_feedback": false,
  "force_reducible": true,
  "allow_negative": true,  // ← Changé
  "allow_improper": false,
  "show_svg": true,
  "representation": "number_line"
}
```

### Chapitre "Simplification guidée" (6e, avec aide)

```json
{
  "difficulty": "facile",
  "variant_id": "B",  // ← Changé
  "pedagogy_mode": "guided",  // ← Changé
  "hint_level": 1,  // ← Changé
  "include_feedback": true,  // ← Changé
  "force_reducible": true,
  "allow_negative": false,
  "allow_improper": false,
  "show_svg": true,
  "representation": "number_line"
}
```

### Chapitre "Diagnostic d'erreurs" (5e)

```json
{
  "difficulty": "moyen",
  "variant_id": "C",  // ← Changé
  "pedagogy_mode": "diagnostic",  // ← Changé
  "hint_level": 0,
  "include_feedback": true,
  "force_reducible": true,
  "allow_negative": false,
  "allow_improper": false,
  "show_svg": true,
  "representation": "number_line"
}
```

---

## 🔧 Structure de sortie (invariante)

**Peu importe les paramètres, la structure de sortie est toujours :**

```json
{
  "variables": {
    "fraction": "12/18",
    "n": 12,
    "d": 18,
    "pgcd": 6,
    "n_red": 2,
    "d_red": 3,
    "fraction_reduite": "2/3",
    "step1": "PGCD(12, 18) = 6",
    "step2": "On divise numérateur et dénominateur par 6",
    "step3": "12 ÷ 6 = 2 et 18 ÷ 6 = 3",
    "is_irreductible": false,
    "difficulty": "moyen",
    // Variables V2 selon variant_id
    "variant_id": "A",
    "pedagogy_mode": "standard",
    "hint_level": 0,
    "include_feedback": false,
    "is_improper": false
  },
  "geo_data": {
    "n": 12,
    "d": 18,
    "n_red": 2,
    "d_red": 3,
    "pgcd": 6,
    "difficulty": "moyen",
    "representation": "number_line",
    "variant_id": "A"
  },
  "figure_svg_enonce": "<svg>...</svg>",
  "figure_svg_solution": "<svg>...</svg>",
  "meta": {
    "exercise_type": "FRACTIONS",
    "difficulty": "moyen",
    "question_type": "simplifier",
    "variant_id": "A",
    "pedagogy_mode": "standard"
  },
  "results": {
    "n_red": 2,
    "d_red": 3,
    "pgcd": 6
  }
}
```

---

## 📚 Références techniques

- **Fichier source :** `backend/generators/simplification_fractions_v2.py`
- **Tests :** `backend/tests/test_simplification_fractions_v2.py`
- **Cahier des charges :** `docs/CAHIER_DES_CHARGES_GENERATEURS_DYNAMIQUES.md`

---

**Document créé le :** 2025-01-XX  
**Dernière mise à jour :** 2025-01-XX  
**Version :** 1.0.0

