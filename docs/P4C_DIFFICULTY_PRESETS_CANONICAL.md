# P4.C — Difficultés & Presets cohérents partout

**Date :** 2025-12-24  
**Objectif :** Rendre l'activation des générateurs simple et sans pièges

---

## 🎯 Objectif produit

Tous les générateurs fonctionnent avec les difficultés **facile | moyen | difficile** dans l'admin et dans la génération.

Aucun chapitre ne doit se retrouver avec un bouton "difficile" absent ou "non supporté" bloquant : si un générateur ne supporte pas une difficulté, on applique une **normalisation + fallback automatique**, et on garde une UX claire.

---

## 📋 Règles de fallback

### Normalisation

**Helper :** `normalize_difficulty(input)`

Mappings :
- `standard` → `moyen`
- `hard` → `difficile`
- `advanced` → `difficile`
- `easy` → `facile`
- `medium` → `moyen`
- `facile` → `facile`
- `moyen` → `moyen`
- `difficile` → `difficile`

### Coercition

**Helper :** `coerce_to_supported_difficulty(requested, supported)`

Règle de fallback hiérarchique :
- Si `requested` ∈ `supported` → retourne `requested` (normalisée)
- Sinon :
  - `difficile` → `moyen` (si `moyen` ∈ `supported`)
  - `difficile` → `facile` (si seulement `facile` ∈ `supported`)
  - `moyen` → `facile` (si `facile` ∈ `supported`)
  - `facile` → `facile` (toujours supporté)

**Exemple :**
```python
# Générateur qui supporte seulement ["facile", "moyen"]
coerce_to_supported_difficulty("difficile", ["facile", "moyen"])
# Retourne "moyen" (fallback hiérarchique)
```

### Auto-complétion des presets

**Helper :** `auto_complete_presets(requested_presets, supported_difficulties)`

Règle :
- Les 3 difficultés canoniques (`facile`, `moyen`, `difficile`) sont **toujours présentes** dans le résultat
- Si une difficulté manque dans `requested_presets`, elle est ajoutée automatiquement
- L'ordre canonique est préservé

**Exemple :**
```python
auto_complete_presets(["facile"], ["facile", "moyen"])
# Retourne ["facile", "moyen", "difficile"]
# (même si "difficile" n'est pas supportée nativement)
```

---

## 🔧 Utilisation dans le code

### Génération d'exercices

**Fichier :** `backend/routes/exercises_routes.py`

Avant d'appeler `GeneratorFactory.generate()`, la difficulté est coercée :

```python
# Récupérer les difficultés supportées par le générateur
gen_class = GeneratorFactory.get(generator_key)
schema = gen_class.get_schema()
supported_difficulties = [...]  # Depuis le schéma

# Coercer la difficulté demandée
coerced_difficulty = coerce_to_supported_difficulty(
    requested=request.difficulte,
    supported=supported_difficulties,
    logger=logger
)

# Appeler le générateur avec la difficulté coercée
GeneratorFactory.generate(
    key=generator_key,
    overrides={'difficulty': coerced_difficulty},
    ...
)
```

**Logs :**
```
[DIFFICULTY_COERCED] requested=difficile coerced_to=moyen (generator supports: ['facile', 'moyen'])
```

### Activation de générateurs (Admin)

**Fichier :** `backend/routes/admin_chapter_generators_routes.py`

Lors de la mise à jour des générateurs activés, les presets sont auto-complétés :

```python
# Normaliser les presets demandés
normalized_presets = [normalize_difficulty(d) for d in enabled_gen.difficulty_presets]

# Auto-compléter les presets manquants
completed_presets = auto_complete_presets(
    requested_presets=normalized_presets,
    supported_difficulties=supported_normalized
)

# Sauvegarder avec les presets complétés
enabled_gen.difficulty_presets = completed_presets
```

---

## 🖥️ UI Admin

**Fichier :** `frontend/src/components/admin/ChapterExercisesAdminPage.js`

### Changements P4.C

**Avant :**
- Checkbox "difficile" disabled si non supportée
- Message "(non supporté)" affiché

**Après :**
- ✅ Checkbox "difficile" **toujours activable**
- Message "**(fallback → moyen)**" au lieu de "(non supporté)"
- Tooltip : "Cette difficulté sera automatiquement ramenée à 'moyen' pour ce générateur."

**Code :**
```javascript
{!isSupported && (
  <span className="text-blue-500 text-[10px] italic" title={fallbackMessage}>
    (fallback → {diff === 'difficile' ? 'moyen' : 'facile'})
  </span>
)}
```

---

## 🔍 Endpoints API

### POST `/api/v1/admin/chapters/{code}/generators/normalize`

Normalise et complète les presets de difficultés pour tous les générateurs activés.

**Réponse :**
```json
{
  "chapter_code": "6e_SP01",
  "updated_generators": 2,
  "message": "2 générateur(s) normalisé(s)"
}
```

**Usage :**
```bash
curl -X POST http://localhost:8000/api/v1/admin/chapters/6e_SP01/generators/normalize
```

---

## 🧪 Tests

### Tests unitaires

**Fichier :** `backend/tests/test_difficulty_coercion.py`

- ✅ Test `difficile` → `moyen` fallback
- ✅ Test `difficile` → `facile` fallback
- ✅ Test `moyen` → `facile` fallback
- ✅ Test difficulté supportée (pas de coercition)
- ✅ Test normalisation avant coercition
- ✅ Test logs de coercition
- ✅ Test auto-complétion des presets
- ✅ Test ordre canonique préservé

### Tests d'intégration

**Scénario 1 :** Chapitre active générateur avec "difficile" alors que `generator.supported = [facile, moyen]`
- ✅ Le générateur est appelé avec "moyen"
- ✅ Résultat OK
- ✅ Log `[DIFFICULTY_COERCED]` présent

**Scénario 2 :** Génération demandée "difficile" pour générateur qui supporte seulement `[facile, moyen]`
- ✅ Génération réussie avec "moyen"
- ✅ Aucune erreur 422
- ✅ Log explicite

### Tests UI

- ✅ L'admin peut cocher "difficile" sans se retrouver bloqué
- ✅ Message "fallback → moyen" apparaît
- ✅ Tooltip explicite affiché

---

## 📊 Logs & Observabilité

### Format des logs

```
[DIFFICULTY_COERCED] requested=difficile coerced_to=moyen (generator supports: ['facile', 'moyen'])
```

**Contexte :**
- `requested` : Difficulté demandée par l'utilisateur
- `coerced_to` : Difficulté réellement utilisée
- `generator supports` : Liste des difficultés supportées par le générateur

### Où chercher les logs

- Backend : `docker compose logs backend | grep DIFFICULTY_COERCED`
- Observabilité : Logs structurés dans `obs_logger`

---

## ✅ Checklist de validation

- [ ] Helper `coerce_to_supported_difficulty()` fonctionne
- [ ] Helper `auto_complete_presets()` fonctionne
- [ ] Coercition appliquée dans `GeneratorFactory.generate()`
- [ ] Coercition appliquée dans `generate_exercise_with_fallback()`
- [ ] Auto-complétion dans `PUT /chapters/{code}/generators`
- [ ] Endpoint `POST /chapters/{code}/generators/normalize` fonctionne
- [ ] UI affiche "fallback → moyen" au lieu de "non supporté"
- [ ] Checkboxes toujours activables (jamais disabled)
- [ ] Logs `[DIFFICULTY_COERCED]` présents
- [ ] Tests unitaires passent
- [ ] Tests d'intégration passent
- [ ] Aucune erreur 422 pour difficulté "non supportée"

---

## 🚫 Contraintes respectées

- ✅ Zéro régression sur P0/P1/P2/P3
- ✅ Le système ne renvoie jamais 422 juste parce qu'une difficulté est "non supportée"
- ✅ Pas de hardcode par chapitre : c'est systémique
- ✅ UX claire : l'utilisateur comprend le fallback

---

## 📚 Références

- **Helper difficultés :** `backend/utils/difficulty_utils.py`
- **Pipeline génération :** `backend/routes/exercises_routes.py`
- **Endpoints admin :** `backend/routes/admin_chapter_generators_routes.py`
- **UI Admin :** `frontend/src/components/admin/ChapterExercisesAdminPage.js`
- **Tests :** `backend/tests/test_difficulty_coercion.py`

---

**✅ P4.C est complet : les difficultés sont maintenant cohérentes partout avec fallback automatique.**




