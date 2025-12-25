# Vérification Variables d'Environnement - Mode Développement

## Objectif
Vérifier que les variables d'environnement sont bien configurées pour :
1. **Liens magiques** (magic links) - Envoi d'emails via Brevo
2. **Test version Pro** - Accès Pro en développement

---

## Variables d'environnement requises

### 1. Variables de base (déjà configurées dans docker-compose.yml)

```yaml
ENVIRONMENT=development          # ✅ Configuré
FRONTEND_URL=http://localhost:3000  # ✅ Configuré
MONGO_URL=mongodb://mongo:27017  # ✅ Configuré
DB_NAME=le_maitre_mot_db         # ✅ Configuré
```

### 2. Variables pour les liens magiques (BREVO)

**Variables requises** :
- `BREVO_API_KEY` : Clé API Brevo pour envoyer les emails
- `BREVO_SENDER_EMAIL` : Email expéditeur (doit être vérifié dans Brevo)
- `BREVO_SENDER_NAME` : Nom de l'expéditeur (optionnel, défaut: "Le Maître Mot")

**Où les configurer** :
- Dans `docker-compose.yml` (section `backend.environment`)
- OU dans un fichier `.env` à la racine (chargé automatiquement)

**Exemple dans docker-compose.yml** :
```yaml
backend:
  environment:
    - ENVIRONMENT=development
    - FRONTEND_URL=http://localhost:3000
    - BREVO_API_KEY=xkeysib-xxxxxxxxxxxxx  # ⚠️ À ajouter
    - BREVO_SENDER_EMAIL=noreply@lemaitremot.fr  # ⚠️ À ajouter
    - BREVO_SENDER_NAME=Le Maître Mot  # Optionnel
```

### 3. Variables pour Stripe (Pro)

**Variables requises** :
- `STRIPE_SECRET_KEY` : Clé secrète Stripe (mode test: `sk_test_...`)

**Exemple dans docker-compose.yml** :
```yaml
backend:
  environment:
    - STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx  # ⚠️ À ajouter (mode test)
```

---

## Vérification actuelle

### Variables déjà configurées (docker-compose.yml)

✅ **ENVIRONMENT=development** - Mode développement activé
✅ **FRONTEND_URL=http://localhost:3000** - URL frontend pour liens magiques
✅ **MONGO_URL=mongodb://mongo:27017** - Connexion MongoDB
✅ **DB_NAME=le_maitre_mot_db** - Nom de la base de données

### Variables manquantes (à ajouter)

⚠️ **BREVO_API_KEY** - Requis pour envoyer les liens magiques
⚠️ **BREVO_SENDER_EMAIL** - Requis pour envoyer les liens magiques
⚠️ **STRIPE_SECRET_KEY** - Requis pour les paiements Pro (mode test)

---

## Comment vérifier les variables dans le container

### 1. Vérifier les variables actuellement chargées

```bash
docker-compose exec backend env | grep -E "ENVIRONMENT|FRONTEND_URL|BREVO|STRIPE"
```

### 2. Vérifier si les variables sont définies dans le code

```bash
# Vérifier dans les logs du backend
docker-compose logs backend | grep -E "Brevo|STRIPE|ENVIRONMENT"
```

### 3. Tester l'envoi d'un lien magique

```bash
# Appeler l'endpoint de login magic link
curl -X POST http://localhost:8000/api/auth/login-magic \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Si BREVO_API_KEY manque** :
```
Error: Brevo credentials not configured
```

---

## Mode développement - Accès Pro

### ✅ Mode "auto-Pro" en développement activé !

**Code actuel** (`backend/server.py:3897-3931`) :
```python
# ✅ EN MODE DÉVELOPPEMENT : Créer automatiquement l'utilisateur Pro
environment = os.environ.get('ENVIRONMENT', 'development')
if environment == 'development':
    # Vérifier si l'utilisateur existe déjà
    is_pro, existing_user = await check_user_pro_status(email)
    
    if not is_pro:
        # Créer l'utilisateur Pro automatiquement en mode dev
        # ... création avec expiration 30 jours (monthly) ou 365 jours (yearly) ...
        logger.info(f"✅ DEV MODE: Pro user auto-created for {email}")
```

**✅ Mode développement actif** : Lors du checkout (via `/api/auth/verify-checkout-token`), l'utilisateur Pro est créé automatiquement si `ENVIRONMENT=development`.

**⚠️ Important** : Pour tester les liens magiques, il faut quand même configurer `BREVO_API_KEY` et `BREVO_SENDER_EMAIL`.

### Créer un utilisateur Pro pour tester

**Option 1 : Via MongoDB directement**

```bash
# Se connecter à MongoDB
docker-compose exec mongo mongosh le_maitre_mot_db

# Créer un utilisateur Pro (expiration dans 1 an)
db.pro_users.insertOne({
  "email": "test@example.com",
  "subscription_type": "monthly",
  "subscription_expires": new Date(Date.now() + 365 * 24 * 60 * 60 * 1000), // 1 an
  "stripe_customer_id": "test_customer",
  "created_at": new Date(),
  "updated_at": new Date()
})
```

**Option 2 : Via l'API (si endpoint existe)**

```bash
# Créer un utilisateur Pro via API (si endpoint admin existe)
curl -X POST http://localhost:8000/api/admin/users/pro \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "subscription_type": "monthly"}'
```

---

## Checklist de configuration

### Pour les liens magiques

- [ ] `BREVO_API_KEY` configurée dans docker-compose.yml ou .env
- [ ] `BREVO_SENDER_EMAIL` configurée (email vérifié dans Brevo)
- [ ] `BREVO_SENDER_NAME` configurée (optionnel)
- [ ] `FRONTEND_URL` = `http://localhost:3000` (déjà OK)
- [ ] Tester l'envoi d'un lien magique

### Pour tester Pro

- [x] `ENVIRONMENT=development` configuré (✅ déjà fait dans docker-compose.yml)
- [ ] `STRIPE_SECRET_KEY` configurée (mode test: `sk_test_...`) - **Optionnel en dev** (auto-Pro activé)
- [ ] Tester le checkout avec un email → L'utilisateur Pro sera créé automatiquement
- [ ] Vérifier que `check_user_pro_status` retourne `True` après checkout

---

## Actions à faire

### 1. Ajouter les variables BREVO dans docker-compose.yml

```yaml
backend:
  environment:
    # ... variables existantes ...
    - BREVO_API_KEY=xkeysib-xxxxxxxxxxxxx  # À obtenir depuis Brevo
    - BREVO_SENDER_EMAIL=noreply@lemaitremot.fr  # Email vérifié dans Brevo
    - BREVO_SENDER_NAME=Le Maître Mot
```

### 2. Ajouter STRIPE_SECRET_KEY (mode test)

```yaml
backend:
  environment:
    # ... variables existantes ...
    - STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx  # Clé test Stripe
```

### 3. Redémarrer les containers

```bash
docker-compose down
docker-compose up -d
```

### 4. Vérifier les variables

```bash
docker-compose exec backend env | grep -E "BREVO|STRIPE|ENVIRONMENT|FRONTEND"
```

### 5. Tester le mode auto-Pro (optionnel - déjà activé)

**✅ Pas besoin de créer manuellement** : Le mode dev crée automatiquement l'utilisateur Pro lors du checkout.

**Pour tester** :
1. Aller sur `/pricing`
2. Choisir un package
3. Entrer un email
4. Cliquer sur "S'abonner"
5. L'utilisateur Pro sera créé automatiquement (expiration 30 jours pour monthly, 365 jours pour yearly)

**Alternative : Créer manuellement si besoin**

```bash
docker-compose exec mongo mongosh le_maitre_mot_db --eval '
db.pro_users.insertOne({
  "email": "test@example.com",
  "subscription_type": "monthly",
  "subscription_expires": new Date(Date.now() + 365 * 24 * 60 * 60 * 1000),
  "stripe_customer_id": "test_customer",
  "created_at": new Date(),
  "updated_at": new Date()
})
'
```

---

## Résumé

### ✅ Déjà configuré
- `ENVIRONMENT=development`
- `FRONTEND_URL=http://localhost:3000`
- MongoDB configuré

### ⚠️ À configurer
- `BREVO_API_KEY` (pour liens magiques)
- `BREVO_SENDER_EMAIL` (pour liens magiques)
- `STRIPE_SECRET_KEY` (pour paiements Pro - mode test)

### 📝 À faire
1. ✅ `ENVIRONMENT=development` - **Déjà configuré**
2. ⚠️ Ajouter `BREVO_API_KEY` et `BREVO_SENDER_EMAIL` dans `docker-compose.yml` (pour liens magiques)
3. ⚠️ Ajouter `STRIPE_SECRET_KEY` (optionnel en dev - auto-Pro activé)
4. Redémarrer les containers : `docker-compose restart backend`
5. Tester le lien magique et l'accès Pro

**Note** : Le mode auto-Pro est déjà activé, donc pas besoin de créer manuellement un utilisateur Pro. Il sera créé automatiquement lors du checkout en mode dev.

