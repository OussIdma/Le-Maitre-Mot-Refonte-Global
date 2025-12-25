# P4.B — Activation des générateurs dans un chapitre

**Date :** 2025-12-24  
**Objectif :** Simplifier l'activation des générateurs dynamiques dans un chapitre

---

## 🎯 Objectif produit

Un admin doit pouvoir activer un générateur dans un chapitre en **30 secondes**, sans connaître la technique.

---

## 📋 Fonctionnalités

### 1. Standardisation des difficultés

**Problème :** Certains générateurs utilisent `standard` au lieu de `facile/moyen/difficile`.

**Solution :** Helper `normalize_difficulty()` qui mappe automatiquement :
- `standard` → `moyen`
- `facile` → `facile`
- `moyen` → `moyen`
- `difficile` → `difficile`

**Utilisation :**
```python
from backend.utils.difficulty_utils import normalize_difficulty

normalized = normalize_difficulty("standard")  # Retourne "moyen"
```

**Où c'est utilisé :**
- Génération d'exercices (`/api/v1/exercises/generate`)
- Sauvegarde admin_exercises
- API admin
- API prof

---

### 2. Activation des générateurs dans un chapitre

**Modèle de données :**

Un chapitre peut maintenant avoir un champ `enabled_generators` :

```json
{
  "code_officiel": "6e_SP01",
  "enabled_generators": [
    {
      "generator_key": "THALES_V2",
      "difficulty_presets": ["facile", "moyen", "difficile"],
      "min_offer": "free",
      "is_enabled": true
    }
  ]
}
```

**Endpoints API :**

1. **GET `/api/v1/admin/chapters/{code}/generators`**
   - Retourne la liste des générateurs disponibles + ceux activés
   - Difficultés réellement supportées par chaque générateur
   - Warnings si chapitre en mode TEMPLATE/MIXED sans générateurs

2. **PUT `/api/v1/admin/chapters/{code}/generators`**
   - Met à jour la liste des générateurs activés
   - Valide que les générateurs existent
   - Normalise automatiquement les difficultés

3. **POST `/api/v1/admin/chapters/{code}/generators/auto-fill`**
   - Active automatiquement les générateurs GOLD non référencés
   - Suggestions basées sur les `exercise_types` du chapitre
   - Logs explicites de ce qui a été ajouté

---

### 3. UI Admin

**Onglet "🧩 Générateurs" dans `ChapterExercisesAdminPage` :**

- **Section "Activer des générateurs"** en haut de l'onglet
- Liste de tous les générateurs disponibles avec :
  - Nom + `generator_key`
  - Badge "🟢 GOLD" si générateur GOLD
  - Badge "⭐ Premium" si `min_offer=pro`
  - Difficultés réellement supportées
  - Switch pour activer/désactiver
- Si activé : checkboxes pour choisir les difficultés activées
- Bouton "Auto-réparer" pour activer automatiquement les générateurs GOLD non référencés
- Warnings si chapitre en mode TEMPLATE/MIXED sans générateurs

**UX :**
- Si un générateur GOLD n'est dans aucun chapitre → warning en haut
- Difficultés non supportées : checkbox disabled + tooltip "non supporté par ce générateur"
- L'UI affiche toujours `facile/moyen/difficile` (jamais `standard`)

---

### 4. Guardrails

**Backend :**

- Si chapitre en mode `TEMPLATE` ou `MIXED` sans générateurs activés :
  - Warning dans la réponse GET `/chapters/{code}/generators`
  - Logs serveur explicites
  - Génération échoue avec message clair (pas d'erreur cryptique)

**Frontend :**

- Affichage des warnings dans l'UI
- Bouton "Auto-réparer" visible si générateurs GOLD non activés

---

## 🛠️ Utilisation

### Activer un générateur manuellement

1. Aller sur `/admin/chapters/{code}`
2. Onglet "🧩 Générateurs"
3. Section "Activer des générateurs"
4. Trouver le générateur souhaité
5. Activer le switch
6. Choisir les difficultés activées (si nécessaire)

### Auto-fill (activer les générateurs GOLD)

1. Aller sur `/admin/chapters/{code}`
2. Onglet "🧩 Générateurs"
3. Cliquer sur "Auto-réparer"
4. Confirmer les générateurs ajoutés

### Script d'activation en masse

```bash
# Dry-run (voir ce qui serait fait)
python backend/scripts/activate_gold_generators_p4b.py --dry-run

# Appliquer
python backend/scripts/activate_gold_generators_p4b.py --apply
```

---

## 📝 Règles des difficultés

### Difficultés canoniques

Les difficultés affichées dans l'UI sont toujours :
- `facile`
- `moyen`
- `difficile`

### Mapping `standard` → `moyen`

**Pourquoi :** Certains générateurs legacy utilisent `standard` au lieu de `moyen`.

**Solution :** Le helper `normalize_difficulty()` mappe automatiquement `standard` vers `moyen`.

**Exemple :**
- Générateur `CALCUL_NOMBRES_V1` supporte `facile` et `standard`
- Dans l'UI : affiché comme `facile` et `moyen`
- Lors de la génération : `standard` est automatiquement converti en `moyen`

---

## 🔍 Dépannage

### "Aucun générateur disponible"

**Cause :** Tous les générateurs sont désactivés ou aucun générateur n'est enregistré.

**Solution :** Vérifier `GeneratorFactory.list_all()` et `DISABLED_GENERATORS`.

### "Générateur activé mais pas utilisable"

**Cause :** Le chapitre est en mode `SPEC` (statique uniquement).

**Solution :** Changer le pipeline du chapitre à `TEMPLATE` ou `MIXED`.

### "Difficulté non supportée"

**Cause :** Le générateur ne supporte pas toutes les difficultés canoniques.

**Solution :** C'est normal. Seules les difficultés supportées peuvent être activées.

---

## ✅ Checklist de validation

- [ ] Helper `normalize_difficulty()` utilisé partout
- [ ] Endpoints GET/PUT/POST fonctionnent
- [ ] UI Admin affiche les générateurs disponibles
- [ ] Switch activation/désactivation fonctionne
- [ ] Auto-fill active les générateurs GOLD
- [ ] Warnings affichés si chapitre sans générateurs
- [ ] Difficultés normalisées dans l'UI (jamais `standard`)
- [ ] Script d'activation en masse fonctionne

---

## 📚 Références

- **Audit initial :** `docs/AUDIT_INCOHERENCES_GENERATEURS_CHAPITRES.md`
- **Helper difficultés :** `backend/utils/difficulty_utils.py`
- **Endpoints :** `backend/routes/admin_chapter_generators_routes.py`
- **UI :** `frontend/src/components/admin/ChapterExercisesAdminPage.js`
- **Script activation :** `backend/scripts/activate_gold_generators_p4b.py`




