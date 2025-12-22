# Implémentation — Déterminisme Variants V2
**Date :** 2025-01-XX  
**Objectif :** Garantir des modes pédagogiques déterministes (A/B/C) et plus de variété en difficile

---

## ✅ Modifications apportées

### 1. Sélection déterministe dans `tests_dyn_handler.py`

**Fichier modifié** : `backend/services/tests_dyn_handler.py` (lignes ~451-500)

**Changements** :
- ✅ Si `variant_id` présent dans `exercise_params` → `choose_template_variant(..., mode="fixed", fixed_variant_id=variant_id)`
- ✅ Si `variant_id` absent → `choose_template_variant(..., mode="seed_random")` (fallback random, compatibilité legacy)
- ✅ Si `variant_id` invalide → `HTTPException(422)` avec message explicite
- ✅ Logs ajoutés : `event=variant_fixed_selected`, `event=variant_random_fallback`, `event=variant_fixed_error`

**Compatibilité legacy** :
- ✅ Exercices existants sans `variant_id` continuent de fonctionner (random)
- ✅ Structure de sortie inchangée

---

### 2. Script de migration pour exercices dynamiques

**Fichier créé** : `backend/migrations/006_create_simplification_fractions_v2_exercises.py`

**Objectif** : Créer 3 exercices dynamiques pour `6e_AA_TEST` avec difficulté "difficile"

**Structure de chaque exercice** :
- `generator_key`: `SIMPLIFICATION_FRACTIONS_V2`
- `difficulty`: `difficile`
- `offer`: `pro` (premium)
- `template_variants`: 3 variants A/B/C avec `variant_id` explicite
- `variables`: `variant_id` fixé à "A" (peut être modifié via admin pour B ou C)

**Templates utilisés** :
- Variant A (Direct) : Templates standard
- Variant B (Guidé) : Templates avec `{{hint_display}}`
- Variant C (Diagnostic) : Templates avec `{{wrong_simplification}}`

**Exécution** :
```bash
docker compose exec backend python /app/backend/migrations/006_create_simplification_fractions_v2_exercises.py
```

**Note** : Le script vérifie l'existence d'exercices avant création pour éviter les doublons.

---

### 3. Tests de déterminisme

**Fichier créé** : `backend/tests/test_simplification_fractions_v2_determinism.py`

**Tests inclus** :
- ✅ `test_determinism_same_seed_same_variant_id` : Même seed + même variant_id → même résultat
- ✅ `test_determinism_different_variant_ids` : Même seed + variant_id différents → variants différents
- ✅ `test_random_fallback_when_variant_id_absent` : variant_id absent → fallback random
- ✅ `test_variant_id_invalid_raises_error` : variant_id invalide → erreur 422
- ✅ `test_generator_v2_registered` : Générateur enregistré dans Factory
- ✅ `test_generator_v2_generates_variables` : Variables attendues générées

**Exécution** :
```bash
docker compose exec backend pytest backend/tests/test_simplification_fractions_v2_determinism.py -v
```

---

## 📋 Procédure d'application

### Étape 1 : Vérifier la compilation

```bash
docker compose exec backend python -m py_compile backend/services/tests_dyn_handler.py
docker compose exec backend python -m py_compile backend/migrations/006_create_simplification_fractions_v2_exercises.py
```

### Étape 2 : Exécuter la migration

```bash
docker compose exec backend python /app/backend/migrations/006_create_simplification_fractions_v2_exercises.py
```

**Résultat attendu** :
```
✅ Exercice créé : simplif_fractions_v2_difficile_1 (variant_id=A)
✅ Exercice créé : simplif_fractions_v2_difficile_2 (variant_id=A)
✅ Exercice créé : simplif_fractions_v2_difficile_3 (variant_id=A)

📊 Résumé : 3/3 exercices créés
   Chapitre : 6E_AA_TEST
   Générateur : SIMPLIFICATION_FRACTIONS_V2
   Difficulté : difficile
   Chaque exercice a 3 template_variants (A/B/C)
```

### Étape 3 : Redémarrer le backend

```bash
docker compose restart backend
```

### Étape 4 : Exécuter les tests

```bash
docker compose exec backend pytest backend/tests/test_simplification_fractions_v2_determinism.py -v
```

**Résultat attendu** : Tous les tests passent

### Étape 5 : Tests API manuels

**Test 1 : Déterminisme avec variant_id** :
```bash
# Générer avec variant_id="A"
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "niveau": "6e",
    "chapitre": "AA TEST",
    "difficulty": "difficile",
    "offer": "pro",
    "seed": 12345
  }' | jq '.metadata.variables.variant_id'

# Répéter avec même seed → même variant_id
```

**Test 2 : Variété via pool d'exercices** :
```bash
# Générer 5 exercices avec difficulté "difficile"
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d "{
      \"niveau\": \"6e\",
      \"chapitre\": \"AA TEST\",
      \"difficulty\": \"difficile\",
      \"offer\": \"pro\",
      \"seed\": $i
    }" | jq '.metadata.exercise_id'
done

# Vérifier que les exercise_id sont différents (variété via pool)
```

**Test 3 : Fallback random (compatibilité legacy)** :
```bash
# Créer un exercice sans variant_id dans variables
# Générer plusieurs fois → variants différents (random)
```

---

## 🔍 Vérifications

### Logs backend

**Vérifier les logs de sélection variant** :
```bash
docker compose logs backend | grep "variant_fixed_selected\|variant_random_fallback"
```

**Logs attendus** :
- `event=variant_fixed_selected` si `variant_id` présent
- `event=variant_random_fallback` si `variant_id` absent

### Structure DB

**Vérifier les exercices créés** :
```bash
docker compose exec mongo mongosh le_maitre_mot --eval "
  db.admin_exercises.find({
    chapter_code: '6E_AA_TEST',
    generator_key: 'SIMPLIFICATION_FRACTIONS_V2',
    difficulty: 'difficile'
  }).forEach(ex => {
    print('ID:', ex.id);
    print('Variants:', ex.template_variants?.map(v => v.variant_id || v.id));
    print('---');
  })
"
```

**Résultat attendu** : 3 exercices avec `template_variants` contenant A, B, C

---

## ✅ DoD (Definition of Done)

### Backend

- [x] Sélection déterministe implémentée (`mode="fixed"` si `variant_id` présent)
- [x] Fallback random préservé (compatibilité legacy)
- [x] Erreur explicite si `variant_id` invalide
- [x] Logs ajoutés pour traçabilité

### Migration

- [x] Script de migration créé
- [x] 3 exercices dynamiques créés pour "difficile"
- [x] Chaque exercice avec 3 `template_variants` A/B/C
- [x] `variant_id` fixé dans `variables` (modifiable via admin)

### Tests

- [x] Tests de déterminisme créés
- [x] Tests de compatibilité legacy créés
- [x] Tests de validation `variant_id` invalide créés

### Validation

- [ ] Migration exécutée avec succès
- [ ] Tests unitaires passants
- [ ] Tests API manuels validés
- [ ] Logs backend vérifiés
- [ ] Structure DB vérifiée

---

## 📝 Notes

### Variété en "difficile"

**Comment ça marche** :
- 3 exercices dynamiques créés pour "difficile"
- Chaque exercice peut générer des fractions différentes (via seed)
- La variété vient du **pool d'exercices**, pas du mélange des modes
- Si on veut forcer un mode spécifique (A/B/C), on modifie `variables.variant_id` dans l'admin

### Modification du variant_id dans l'admin

**Pour changer le mode d'un exercice** :
1. Aller dans l'admin : `/admin/curriculum/6e_AA_TEST/exercises`
2. Éditer l'exercice
3. Dans "Paramètres du générateur", modifier `variant_id` :
   - `"A"` → Direct
   - `"B"` → Guidé
   - `"C"` → Diagnostic
4. Sauvegarder

**Note** : Chaque exercice a 3 `template_variants` (A/B/C), mais `variables.variant_id` détermine lequel est utilisé.

---

## 🚀 Prochaines étapes (optionnel)

### Symétrie Axiale "multi-formes"

**Note** : Un futur générateur Symétrie Axiale "multi-formes" est souhaité, à traiter après validation fractions V2.

**Approche similaire** :
- Créer plusieurs exercices dynamiques avec différentes formes (point, segment, triangle, etc.)
- Chaque exercice avec `template_variants` si nécessaire
- Utiliser `variant_id` pour sélection déterministe si applicable

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémentation complète, prête pour validation


