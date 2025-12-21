# Diagnostic — Pool vide 6E_AA_TEST (facile/moyen)
**Date :** 2025-01-XX  
**Problème :** Génération 6E_AA_TEST en MIXED renvoie 422 "CHAPITRE NON MAPPÉ" pour facile/moyen

---

## 🔍 Diagnostic

### Étape 1 : Lister les exercices en DB

**Script créé** : `backend/scripts/diagnostic_6e_aa_test.py`

**Exécution** :
```bash
docker compose exec backend python /app/backend/scripts/diagnostic_6e_aa_test.py
```

**Résultat attendu** :
- Liste de tous les exercices dynamiques pour `6E_AA_TEST`
- Statistiques par `difficulty` et `offer`
- Test de filtrage pour chaque combinaison

---

### Étape 2 : Vérifier le filtrage dans le pipeline MIXED

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~954-1074)

**Logique actuelle** :
1. Récupération avec filtres `offer` + `difficulty`
2. Si pool vide → retente sans filtres (dégradé)
3. Si toujours vide → 422 explicite

**Logs ajoutés** :
- `event=mixed_pool_filtered` : Pool filtré (DEBUG)
- `event=mixed_no_filtered_exercises` : Aucun exercice avec filtres (WARNING)
- `event=mixed_no_exercises` : Aucun exercice disponible (ERROR) avec diagnostic détaillé

---

### Étape 3 : Tester une requête POST

**Commande** :
```bash
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "facile",
    "offer": "free",
    "seed": 42
  }' | jq '.'
```

**Logs backend** :
```bash
docker compose logs backend | grep -E "mixed_pool_filtered|mixed_no_filtered|mixed_no_exercises|MIXED" | tail -20
```

---

## 🔧 Solution : Migration pour créer exercices faciles/moyens

### Script de migration

**Fichier créé** : `backend/migrations/007_add_facile_moyen_6e_aa_test.py`

**Objectif** :
- Créer 1 exercice "facile" + "free"
- Créer 1 exercice "moyen" + "free"
- Chaque exercice avec 3 `template_variants` A/B/C
- `generator_key`: `SIMPLIFICATION_FRACTIONS_V2`

**Exécution** :
```bash
docker compose exec backend python /app/backend/migrations/007_add_facile_moyen_6e_aa_test.py
```

**Résultat attendu** :
```
✅ Exercice créé : simplif_fractions_v2_facile_free
   - difficulty: facile
   - offer: free
   - variant_id: A

✅ Exercice créé : simplif_fractions_v2_moyen_free
   - difficulty: moyen
   - offer: free
   - variant_id: A

📊 Résumé : 2/2 exercices créés
```

---

## ✅ Validation

### Test 1 : Génération facile

```bash
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "facile",
    "offer": "free",
    "seed": 42
  }' | jq '.metadata.variables | {variant_id, fraction, difficulty}'
```

**Résultat attendu** : HTTP 200, `variables` non vides, `variant_id="A"`

### Test 2 : Génération moyen

```bash
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "moyen",
    "offer": "free",
    "seed": 42
  }' | jq '.metadata.variables | {variant_id, fraction, difficulty}'
```

**Résultat attendu** : HTTP 200, `variables` non vides, `variant_id="A"`

### Test 3 : Vérifier les logs

```bash
docker compose logs backend | grep -E "event=mixed_pool_filtered|event=request_complete.*chosen_path=MIXED" | tail -10
```

**Résultat attendu** :
- `event=mixed_pool_filtered` avec `dynamic_count > 0`
- `event=request_complete` avec `chosen_path=MIXED_dynamic_filtered`

---

## 📋 Procédure complète

### 1. Diagnostic initial

```bash
# Lister les exercices existants
docker compose exec backend python /app/backend/scripts/diagnostic_6e_aa_test.py
```

### 2. Créer les exercices manquants

```bash
# Créer exercices faciles/moyens
docker compose exec backend python /app/backend/migrations/007_add_facile_moyen_6e_aa_test.py
```

### 3. Redémarrer le backend

```bash
docker compose restart backend
```

### 4. Tester la génération

```bash
# Test facile
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "facile", "offer": "free", "seed": 42}'

# Test moyen
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "moyen", "offer": "free", "seed": 42}'
```

### 5. Vérifier les logs

```bash
docker compose logs backend | grep -E "mixed_pool_filtered|request_complete.*MIXED" | tail -20
```

---

## 🎯 DoD (Definition of Done)

- [x] Script de diagnostic créé
- [x] Script de migration créé (exercices faciles/moyens)
- [x] Logs ajoutés dans pipeline MIXED
- [ ] Diagnostic exécuté (liste des exercices en DB)
- [ ] Migration exécutée (exercices créés)
- [ ] Tests POST passants (200, variables non vides)
- [ ] Logs vérifiés (`chosen_path=MIXED_dynamic_filtered`)

---

## 🔍 Points de vérification

### Si le pool est toujours vide après migration

1. **Vérifier le `chapter_code` en DB** :
   - Doit être `6E_AA_TEST` (majuscules, underscore)
   - Pas `6e_AA_TEST` ou `6e_aa_test`

2. **Vérifier les filtres** :
   - `difficulty` : "facile" ou "moyen" (minuscules)
   - `offer` : "free" (minuscules)
   - `is_dynamic` : `true` (booléen)

3. **Vérifier les logs** :
   - `event=mixed_pool_filtered` doit montrer `dynamic_count > 0`
   - Si `dynamic_count=0`, vérifier les filtres appliqués

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Scripts créés, prêts pour diagnostic et correction


