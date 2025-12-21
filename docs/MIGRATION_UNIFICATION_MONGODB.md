# Migration — Unification MongoDB vers le_maitre_mot_db
**Date :** 2025-01-XX  
**Objectif :** Unifier toutes les bases MongoDB en une seule base `le_maitre_mot_db`

---

## 📋 État actuel

### Bases MongoDB utilisées

1. **`mathalea_db`** (base principale actuelle) :
   - Utilisée par `backend/server.py` via `DB_NAME=mathalea_db`
   - Utilisée en dur dans :
     - `backend/services/pro_config_service.py` (ligne 20)
     - `backend/routes/mathalea_routes.py` (ligne 50)
     - `backend/services/exercise_template_service.py` (ligne 39)

2. **`le_maitre_mot`** (base utilisée par certaines migrations) :
   - Utilisée dans les migrations :
     - `006_create_simplification_fractions_v2_exercises.py`
     - `007_add_facile_moyen_6e_aa_test.py`
     - Et d'autres migrations

### Collections à migrer

- `admin_exercises` : Exercices dynamiques/statiques
- `curriculum_chapters` : Chapitres du curriculum
- `user_templates` : Templates utilisateurs (Pro)
- `competences` : Compétences MathALÉA
- `exercise_types` : Types d'exercices
- `exercise_sheets` : Feuilles d'exercices
- `sheet_items` : Items de feuilles

---

## 🔧 Plan d'unification

### Étape 1 : Script de migration (dump/restore)

**Fichier créé** : `backend/migrations/008_unify_mongodb_database.py`

**Fonctionnalités** :
- Copie toutes les collections de `mathalea_db` vers `le_maitre_mot_db`
- Évite les doublons (vérifie `_id` avant insertion)
- Idempotent (peut être exécuté plusieurs fois)
- Logs détaillés pour chaque collection

**Exécution** :
```bash
docker compose exec backend python /app/backend/migrations/008_unify_mongodb_database.py
```

---

### Étape 2 : Mise à jour de la configuration

#### 2.1 docker-compose.yml

**Modifications** :
```yaml
# AVANT
environment:
  - DB_NAME=mathalea_db
  MONGO_INITDB_DATABASE: mathalea_db

# APRÈS
environment:
  - DB_NAME=le_maitre_mot_db
  MONGO_INITDB_DATABASE: le_maitre_mot_db
```

#### 2.2 Fichiers avec `mathalea_db` en dur

**Fichiers à modifier** :

1. **`backend/services/pro_config_service.py`** (ligne 20) :
   ```python
   # AVANT
   db = client.mathalea_db
   
   # APRÈS
   db_name = os.environ.get('DB_NAME', 'le_maitre_mot_db')
   db = client[db_name]
   ```

2. **`backend/routes/mathalea_routes.py`** (ligne 50) :
   ```python
   # AVANT
   db = client.mathalea_db
   
   # APRÈS
   db_name = os.environ.get('DB_NAME', 'le_maitre_mot_db')
   db = client[db_name]
   ```

3. **`backend/services/exercise_template_service.py`** (ligne 39) :
   ```python
   # AVANT
   self.db = self.client.mathalea_db
   
   # APRÈS
   db_name = os.environ.get('DB_NAME', 'le_maitre_mot_db')
   self.db = self.client[db_name]
   ```

#### 2.3 Migrations utilisant `le_maitre_mot`

**Fichiers à vérifier** :
- `006_create_simplification_fractions_v2_exercises.py`
- `007_add_facile_moyen_6e_aa_test.py`
- Autres migrations

**Modification** :
```python
# AVANT
db = client.le_maitre_mot

# APRÈS
db_name = os.environ.get('DB_NAME', 'le_maitre_mot_db')
db = client[db_name]
```

---

### Étape 3 : Redémarrage et vérification

#### 3.1 Redémarrer le backend

```bash
docker compose restart backend
```

#### 3.2 Vérifier la base utilisée

```bash
docker compose exec backend mongosh --eval "db.getName()"
```

**Résultat attendu** : `le_maitre_mot_db`

#### 3.3 Compter les exercices

```bash
docker compose exec backend mongosh le_maitre_mot_db --eval "db.admin_exercises.countDocuments({chapter_code:'6E_AA_TEST'})"
```

**Résultat attendu** : Nombre identique à avant la migration

#### 3.4 Tester la génération

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

**Résultat attendu** : HTTP 200, `variables` non vides

---

## 📋 Procédure complète

### 1. Backup (optionnel mais recommandé)

```bash
# Backup de mathalea_db
docker compose exec mongo mongodump --db=mathalea_db --out=/data/backup/mathalea_db_$(date +%Y%m%d)

# Backup de le_maitre_mot (si existe)
docker compose exec mongo mongodump --db=le_maitre_mot --out=/data/backup/le_maitre_mot_$(date +%Y%m%d)
```

### 2. Exécuter la migration

```bash
docker compose exec backend python /app/backend/migrations/008_unify_mongodb_database.py
```

### 3. Mettre à jour la configuration

**docker-compose.yml** :
- Changer `DB_NAME=mathalea_db` → `DB_NAME=le_maitre_mot_db`
- Changer `MONGO_INITDB_DATABASE: mathalea_db` → `MONGO_INITDB_DATABASE: le_maitre_mot_db`

**Fichiers backend** :
- `backend/services/pro_config_service.py`
- `backend/routes/mathalea_routes.py`
- `backend/services/exercise_template_service.py`
- Migrations utilisant `le_maitre_mot`

### 4. Redémarrer

```bash
docker compose restart backend
```

### 5. Vérifications

```bash
# Vérifier la base
docker compose exec backend mongosh --eval "db.getName()"

# Compter les exercices
docker compose exec backend mongosh le_maitre_mot_db --eval "db.admin_exercises.countDocuments({chapter_code:'6E_AA_TEST'})"

# Tester la génération
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_AA_TEST","difficulte":"facile","offer":"free","seed":42}'
```

---

## ✅ DoD (Definition of Done)

- [ ] Script de migration exécuté avec succès
- [ ] docker-compose.yml mis à jour
- [ ] Fichiers avec `mathalea_db` en dur mis à jour
- [ ] Migrations utilisant `le_maitre_mot` mises à jour
- [ ] Backend redémarré
- [ ] Vérification : `db.getName()` → `le_maitre_mot_db`
- [ ] Vérification : Nombre d'exercices identique
- [ ] Test génération : HTTP 200, variables non vides
- [ ] Documentation mise à jour

---

## 🔍 Points de vérification

### Si la migration échoue

1. **Vérifier les collections source** :
   ```bash
   docker compose exec mongo mongosh mathalea_db --eval "db.getCollectionNames()"
   ```

2. **Vérifier les collections cible** :
   ```bash
   docker compose exec mongo mongosh le_maitre_mot_db --eval "db.getCollectionNames()"
   ```

3. **Vérifier les doublons** :
   ```bash
   docker compose exec mongo mongosh le_maitre_mot_db --eval "db.admin_exercises.countDocuments({})"
   ```

### Si le backend ne démarre pas

1. **Vérifier les logs** :
   ```bash
   docker compose logs backend | tail -50
   ```

2. **Vérifier la connexion MongoDB** :
   ```bash
   docker compose exec backend mongosh --eval "db.adminCommand('ping')"
   ```

---

## 📝 Notes importantes

### Préservation des données

- ✅ **Aucune suppression** : Les données de `mathalea_db` sont préservées
- ✅ **Doublons évités** : Vérification par `_id` avant insertion
- ✅ **Idempotent** : La migration peut être exécutée plusieurs fois

### Compatibilité

- ✅ **Structure inchangée** : Les collections gardent leur structure
- ✅ **Index préservés** : Les index existants sont copiés
- ✅ **Pas de régression** : Toutes les fonctionnalités existantes fonctionnent

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Plan prêt pour exécution


