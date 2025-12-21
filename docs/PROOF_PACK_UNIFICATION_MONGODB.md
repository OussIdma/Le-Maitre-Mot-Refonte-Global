# Proof Pack — Unification MongoDB
**Date :** 2025-01-XX  
**Objectif :** Vérifier que l'unification MongoDB fonctionne correctement

---

## ✅ Commandes de vérification

### 1. Vérifier la base utilisée par le backend

```bash
docker compose exec backend mongosh --eval "db.getName()"
```

**Résultat attendu** :
```
le_maitre_mot_db
```

---

### 2. Compter les exercices pour 6E_AA_TEST

```bash
docker compose exec backend mongosh le_maitre_mot_db --eval "db.admin_exercises.countDocuments({chapter_code:'6E_AA_TEST'})"
```

**Résultat attendu** :
```
Nombre identique à avant la migration (ex: 3, 5, etc.)
```

---

### 3. Lister les collections dans la base unifiée

```bash
docker compose exec backend mongosh le_maitre_mot_db --eval "db.getCollectionNames()"
```

**Résultat attendu** :
```
[
  'admin_exercises',
  'curriculum_chapters',
  'user_templates',
  'competences',
  'exercise_types',
  'exercise_sheets',
  'sheet_items'
]
```

---

### 4. Tester la génération d'exercice (facile)

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

**Résultat attendu** :
```json
{
  "variant_id": "A",
  "fraction": "6/8",
  "difficulty": "facile"
}
```

**HTTP Status** : `200 OK`

---

### 5. Tester la génération d'exercice (moyen)

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

**Résultat attendu** :
```json
{
  "variant_id": "A",
  "fraction": "12/20",
  "difficulty": "moyen"
}
```

**HTTP Status** : `200 OK`

---

### 6. Vérifier les logs backend (pas d'erreur MongoDB)

```bash
docker compose logs backend | grep -i "mongo\|database\|db_name" | tail -20
```

**Résultat attendu** :
- Aucune erreur de connexion
- Aucune erreur "database not found"
- Logs normaux de démarrage

---

### 7. Vérifier que mathalea_db existe toujours (backup)

```bash
docker compose exec backend mongosh mathalea_db --eval "db.getCollectionNames()"
```

**Résultat attendu** :
```
Les collections originales sont toujours présentes (backup préservé)
```

---

## 📋 Checklist de validation

- [ ] `db.getName()` → `le_maitre_mot_db`
- [ ] Nombre d'exercices identique à avant
- [ ] Collections présentes dans `le_maitre_mot_db`
- [ ] Génération facile : HTTP 200, variables non vides
- [ ] Génération moyen : HTTP 200, variables non vides
- [ ] Pas d'erreur MongoDB dans les logs
- [ ] `mathalea_db` toujours présent (backup)

---

## 🔍 En cas d'erreur

### Erreur : "database not found"

**Cause** : La migration n'a pas été exécutée ou a échoué.

**Solution** :
```bash
# Réexécuter la migration
docker compose exec backend python /app/backend/migrations/008_unify_mongodb_database.py

# Vérifier les logs
docker compose logs backend | grep -i "migration\|unify" | tail -20
```

---

### Erreur : "collection not found"

**Cause** : Les collections n'ont pas été copiées.

**Solution** :
```bash
# Vérifier les collections dans mathalea_db
docker compose exec backend mongosh mathalea_db --eval "db.getCollectionNames()"

# Vérifier les collections dans le_maitre_mot_db
docker compose exec backend mongosh le_maitre_mot_db --eval "db.getCollectionNames()"

# Réexécuter la migration si nécessaire
docker compose exec backend python /app/backend/migrations/008_unify_mongodb_database.py
```

---

### Erreur : "Network Error" lors de la génération

**Cause** : Le backend n'arrive pas à se connecter à MongoDB.

**Solution** :
```bash
# Vérifier la connexion MongoDB
docker compose exec backend mongosh --eval "db.adminCommand('ping')"

# Vérifier les variables d'environnement
docker compose exec backend env | grep -E "MONGO_URL|DB_NAME"

# Redémarrer le backend
docker compose restart backend
```

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Prêt pour validation


