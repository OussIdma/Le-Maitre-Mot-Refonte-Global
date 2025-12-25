# P0 - Correction erreur E11000 duplicate key sur exercise_uid

## 🐛 Problème identifié

**Erreur MongoDB** :
```
E11000 duplicate key error collection: le_maitre_mot_db.admin_exercises 
index: exercise_uid_1 dup key: { exercise_uid: null }
```

**Cause racine** :
- L'index unique `exercise_uid_1` existe sur la collection `admin_exercises` (créé par le script de migration)
- Les exercices créés via l'admin n'avaient pas de `exercise_uid` calculé
- Tous les nouveaux exercices avaient `exercise_uid: null`, violant l'index unique

## ✅ Solution appliquée

### 1. Calcul de `exercise_uid` lors de la création

**Fichier** : `backend/services/exercise_persistence_service.py`

- Ajout de l'import `hashlib`
- Calcul de `exercise_uid` dans `create_exercise()` :
  - Pour les exercices **dynamiques** : utilise `enonce_template_html` + `solution_template_html`
  - Pour les exercices **statiques** : utilise `enonce_html` + `solution_html`
  - Formule : `SHA256(chapter_code|enonce|solution|difficulty)`
- Vérification de doublon avant insertion
- Ajout de `exercise_uid` dans le document créé

### 2. Recalcul de `exercise_uid` lors de la mise à jour

**Fichier** : `backend/services/exercise_persistence_service.py`

- Dans `update_exercise()`, recalcul de `exercise_uid` si le contenu change :
  - Si `enonce_html`, `solution_html`, `enonce_template_html`, `solution_template_html`, `difficulty`, ou `is_dynamic` est modifié
  - Ou si `exercise_uid` est absent (null)
- Vérification de collision avant mise à jour

### 3. Nettoyage des exercices existants

**Script** : `backend/scripts/fix_null_exercise_uid.py`

- Script pour corriger les exercices avec `exercise_uid: null`
- Calcule l'UID manquant pour chaque exercice
- Gère les conflits (si l'UID existe déjà, génère un UID unique avec timestamp)

**Résultat** :
- ✅ 1 exercice corrigé (ID=1, chapter=6E_G07)

## 📋 Validation

### Vérifications effectuées

1. ✅ Aucun exercice avec `exercise_uid: null` restant
2. ✅ Index `exercise_uid_1` unique actif
3. ✅ Nouveaux exercices créés avec `exercise_uid` calculé
4. ✅ Mise à jour d'exercice recalcule `exercise_uid` si nécessaire

### Test manuel

1. Créer un exercice dynamique dans l'admin → ✅ Pas d'erreur E11000
2. Créer un exercice statique dans l'admin → ✅ Pas d'erreur E11000
3. Modifier le contenu d'un exercice → ✅ `exercise_uid` recalculé si nécessaire

## 🔧 Commandes utiles

### Vérifier les exercices avec exercise_uid null
```bash
docker compose exec backend python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client['le_maitre_mot_db']
    count = await db['admin_exercises'].count_documents({'exercise_uid': None})
    print(f'Exercices avec exercise_uid=null: {count}')
    client.close()

asyncio.run(check())
"
```

### Corriger les exercices avec exercise_uid null
```bash
docker compose exec backend python /app/backend/scripts/fix_null_exercise_uid.py
```

## 📝 Notes techniques

- **Cohérence** : La logique de calcul d'UID est identique à celle du script de migration (`migrate_pseudo_static_to_db.py`)
- **Performance** : Le calcul d'UID est rapide (SHA256), pas d'impact notable
- **Sécurité** : Vérification de doublon avant insertion/mise à jour pour éviter les collisions

## ✅ Statut

**RÉSOLU** - Les nouveaux exercices créés via l'admin ont maintenant un `exercise_uid` calculé automatiquement, évitant l'erreur E11000.




