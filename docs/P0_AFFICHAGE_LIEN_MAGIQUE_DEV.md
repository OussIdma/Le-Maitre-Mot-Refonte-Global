# P0 - Affichage Lien Magique en Mode Développement

## Objectif
Afficher le lien magique à l'écran en mode développement pour faciliter les tests, en plus de l'envoi par email.

**Cas d'usage** :
1. **Connexion** : Lien magique pour se connecter à un compte Pro existant
2. **Création de compte** : Lien magique pour confirmer l'email avant checkout Stripe

---

## Fichiers modifiés

### 1. `backend/server.py`

#### Modification 1 : Endpoint `/api/auth/request-login` (connexion)

**Diff** :
```python
# Send magic link email (or log in local dev)
environment = os.environ.get('ENVIRONMENT', 'development')
frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
magic_link = f"{frontend_url}/login/verify?token={raw_token}"

if environment == 'development':
    # Mode local: Log the magic link and return it in response
    logger.info(f"🔗 MAGIC LINK (dev): {magic_link}")
    logger.info(f"   Email: {request_body.email}")
    # Return magic link in dev mode for easy testing
    await auth_service.log_auth_attempt(...)
    return {
        "message": "Si un compte Pro existe pour cette adresse, un lien de connexion a été envoyé",
        "success": True,
        "dev_mode": True,
        "magic_link": magic_link  # ✅ Retourné en mode dev
    }
else:
    # Production: Send email
    email_sent = await send_magic_link_email(...)
```

#### Modification 2 : Endpoint `/api/auth/pre-checkout` (création de compte)

**Diff** :
```python
if environment == 'development':
    # Mode local: Log the checkout link
    logger.info(f"🔗 CHECKOUT LINK (dev): {checkout_link}")
    logger.info(f"   Email: {request_body.email}")
    logger.info(f"   Package: {request_body.package_id}")
    
    # ✅ Retourner le lien dans la réponse pour le frontend
    response_data = {
        "message": "Un lien de confirmation a été envoyé...",
        "success": True,
        "dev_mode": True,  # Indicateur pour le frontend
        "checkout_link": checkout_link,  # ✅ Le lien complet
        "email": request_body.email,
        "package_id": request_body.package_id
    }
    return response_data
```

---

### 2. `frontend/src/components/GlobalLoginModal.js`

#### Modification 1 : État pour stocker le lien magique

**Diff** :
```javascript
// P0: État pour afficher le lien magique en mode dev
const [devMagicLink, setDevMagicLink] = useState(null);
```

#### Modification 2 : Fonction `requestLogin` - Récupérer et stocker le lien

**Diff** :
```javascript
const requestLogin = async (email) => {
  // ...
  try {
    const response = await axios.post(`${API}/auth/request-login`, {
      email: email
    });
    
    setLoginEmailSent(true);
    
    // P0: Afficher le lien magique en mode dev
    if (response.data.dev_mode && response.data.magic_link) {
      setDevMagicLink(response.data.magic_link);
      toast({
        title: "🔗 Lien magique (mode dev)",
        description: "Le lien est affiché ci-dessous pour copier.",
      });
    } else {
      toast({
        title: "Email envoyé",
        description: "Si un compte existe, un email vous a été envoyé.",
      });
    }
  } catch (error) {
    // ...
  }
};
```

#### Modification 3 : Affichage du lien magique dans le modal

**Diff** :
```javascript
{!loginEmailSent ? (
  // ... formulaire ...
) : (
  <>
    {/* P0: Afficher le lien magique en mode dev */}
    {devMagicLink ? (
      <div className="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-sm font-medium text-blue-900">
          🔗 Lien magique (mode développement)
        </p>
        <div className="flex items-center gap-2">
          <Input
            value={devMagicLink}
            readOnly
            className="flex-1 font-mono text-xs bg-white"
          />
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              navigator.clipboard.writeText(devMagicLink);
              toast({
                title: "Lien copié",
                description: "Le lien magique a été copié dans le presse-papier.",
              });
            }}
          >
            Copier
          </Button>
        </div>
        <p className="text-xs text-blue-700">
          Cliquez sur le lien ou copiez-le pour vous connecter.
        </p>
        <Button 
          variant="outline" 
          onClick={() => {
            setLoginEmailSent(false);
            setDevMagicLink(null);
            setLoginEmail("");
          }}
          className="w-full"
        >
          Réessayer
        </Button>
      </div>
    ) : (
      // ... message email envoyé normal ...
    )}
  </>
)}
```

#### Modification 4 : Reset du lien magique quand le modal se ferme

**Diff** :
```javascript
useEffect(() => {
  if (!showLoginModal) {
    setLoginEmail("");
    setLoginPassword("");
    setLoginEmailSent(false);
    setLoginLoading(false);
    setLoginTab("magic");
    setDevMagicLink(null); // P0: Reset magic link
  }
}, [showLoginModal]);
```

---

### 3. `frontend/src/App.js`

#### Modification 1 : État pour stocker le lien checkout

**Diff** :
```javascript
// P0: État pour afficher le lien magique en mode dev
const [devCheckoutLink, setDevCheckoutLink] = useState(null);
```

#### Modification 2 : Fonction `handleUpgradeClick` - Utiliser pre-checkout

**Diff** :
```javascript
const handleUpgradeClick = async (packageId) => {
  if (!paymentEmail || !paymentEmail.includes('@')) {
    alert('Veuillez saisir une adresse email valide');
    return;
  }
  
  setPaymentLoading(true);
  setDevCheckoutLink(null); // Reset
  
  try {
    // P0: Appeler pre-checkout pour obtenir le lien magique
    const preCheckoutResponse = await axios.post(`${API}/auth/pre-checkout`, {
      email: paymentEmail,
      package_id: packageId
    });
    
    // P0: Afficher le lien magique en mode dev
    if (preCheckoutResponse.data.dev_mode && preCheckoutResponse.data.checkout_link) {
      setDevCheckoutLink(preCheckoutResponse.data.checkout_link);
      toast({
        title: "🔗 Lien magique (mode dev)",
        description: "Le lien de confirmation est affiché ci-dessous pour copier.",
      });
      setPaymentLoading(false);
      return; // Ne pas continuer, l'utilisateur doit cliquer sur le lien
    }
    
    // En production, l'email est envoyé, on affiche un message
    toast({
      title: "Email envoyé",
      description: "Un lien de confirmation a été envoyé à votre adresse email.",
    });
    
  } catch (error) {
    // ... gestion erreurs ...
  } finally {
    setPaymentLoading(false);
  }
};
```

#### Modification 3 : Affichage du lien checkout dans le modal

**Diff** :
```javascript
{/* Payment Modal */}
<Dialog open={showPaymentModal} onOpenChange={(open) => {
  setShowPaymentModal(open);
  if (!open) {
    setDevCheckoutLink(null); // Reset quand le modal se ferme
  }
}}>
  {/* ... email input et packages ... */}
  
  {/* P0: Afficher le lien magique en mode dev */}
  {devCheckoutLink && (
    <div className="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded-md">
      <p className="text-sm font-medium text-blue-900">
        🔗 Lien magique (mode développement)
      </p>
      <div className="flex items-center gap-2">
        <Input
          value={devCheckoutLink}
          readOnly
          className="flex-1 font-mono text-xs bg-white"
        />
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            navigator.clipboard.writeText(devCheckoutLink);
            toast({
              title: "Lien copié",
              description: "Le lien magique a été copié dans le presse-papier.",
            });
          }}
        >
          Copier
        </Button>
      </div>
      <p className="text-xs text-blue-700">
        Cliquez sur le lien ou copiez-le pour continuer le checkout.
      </p>
      <Button
        variant="outline"
        size="sm"
        onClick={() => {
          window.open(devCheckoutLink, '_blank');
        }}
        className="w-full"
      >
        Ouvrir le lien
      </Button>
    </div>
  )}
  
  {/* ... footer ... */}
</Dialog>
```

---

## Comportement

### Mode développement (`ENVIRONMENT=development`)

#### 1. Connexion (GlobalLoginModal)

1. ✅ User entre son email
2. ✅ Clique sur "Recevoir un lien de connexion"
3. ✅ **Le lien magique s'affiche dans le modal** avec :
   - Input en lecture seule avec le lien complet
   - Bouton "Copier" pour copier dans le presse-papier
   - Message explicatif
   - Bouton "Réessayer" pour recommencer
4. ✅ User peut copier le lien et l'ouvrir dans un nouvel onglet

#### 2. Création de compte (App.js - Payment Modal)

1. ✅ User entre son email
2. ✅ Choisit un package (mensuel ou annuel)
3. ✅ Clique sur "Choisir Mensuel" ou "Choisir Annuel"
4. ✅ **Le lien checkout s'affiche dans le modal** avec :
   - Input en lecture seule avec le lien complet
   - Bouton "Copier" pour copier dans le presse-papier
   - Bouton "Ouvrir le lien" pour ouvrir dans un nouvel onglet
5. ✅ User clique sur le lien → Redirigé vers `/checkout?token=...`
6. ✅ Le token est vérifié → Session créée → Checkout Stripe

### Mode production (`ENVIRONMENT=production`)

- ✅ Le lien magique est **uniquement envoyé par email**
- ✅ Aucun lien n'est affiché à l'écran (sécurité)
- ✅ Comportement normal avec Brevo

---

## Tests manuels

### Test 1 : Connexion avec lien magique (dev)

1. ✅ Ouvrir `/` ou n'importe quelle page
2. ✅ Cliquer sur "Se connecter" (ouvre GlobalLoginModal)
3. ✅ Entrer un email Pro existant (ex: `test@example.com`)
4. ✅ Cliquer sur "Recevoir un lien de connexion"
5. ✅ **VÉRIFIER** : Le lien magique s'affiche dans le modal
6. ✅ **VÉRIFIER** : Format du lien : `http://localhost:3000/login/verify?token=...`
7. ✅ Cliquer sur "Copier"
8. ✅ **VÉRIFIER** : Toast "Lien copié" s'affiche
9. ✅ Ouvrir un nouvel onglet et coller le lien
10. ✅ **VÉRIFIER** : Connexion réussie, redirection vers la page d'origine

### Test 2 : Création de compte avec lien checkout (dev)

1. ✅ Ouvrir `/pricing` ou cliquer sur "Passer à Pro"
2. ✅ Entrer un email (ex: `newuser@example.com`)
3. ✅ Choisir "Mensuel" ou "Annuel"
4. ✅ Cliquer sur "Choisir Mensuel" ou "Choisir Annuel"
5. ✅ **VÉRIFIER** : Le lien checkout s'affiche dans le modal
6. ✅ **VÉRIFIER** : Format du lien : `http://localhost:3000/checkout?token=...`
7. ✅ Cliquer sur "Ouvrir le lien"
8. ✅ **VÉRIFIER** : Redirection vers `/checkout?token=...`
9. ✅ **VÉRIFIER** : Token vérifié, session créée, utilisateur Pro créé automatiquement (mode dev)
10. ✅ **VÉRIFIER** : Redirection vers Stripe Checkout (ou affichage du package si Stripe non configuré)

### Test 3 : Reset du lien magique

1. ✅ Ouvrir le modal de connexion
2. ✅ Demander un lien magique (lien affiché)
3. ✅ Fermer le modal
4. ✅ Rouvrir le modal
5. ✅ **VÉRIFIER** : Le lien magique n'est plus affiché (reset)

### Test 4 : Mode production (si configuré)

1. ✅ Changer `ENVIRONMENT=production` dans docker-compose.yml
2. ✅ Redémarrer le backend
3. ✅ Tester la connexion
4. ✅ **VÉRIFIER** : Aucun lien magique affiché (seulement email)
5. ✅ **VÉRIFIER** : Email envoyé via Brevo (si configuré)

---

## Résumé des changements

### Backend
- ✅ `/api/auth/request-login` : Retourne `magic_link` en mode dev
- ✅ `/api/auth/pre-checkout` : Retourne `checkout_link` en mode dev
- ✅ Les deux endpoints loggent le lien dans les logs serveur

### Frontend
- ✅ **GlobalLoginModal** : Affiche le lien magique de connexion en mode dev
- ✅ **App.js Payment Modal** : Affiche le lien checkout en mode dev
- ✅ Bouton "Copier" pour copier le lien dans le presse-papier
- ✅ Bouton "Ouvrir le lien" pour le checkout
- ✅ Reset automatique quand les modals se ferment

### UX
- ✅ **Mode dev** : Lien visible et copiable pour faciliter les tests
- ✅ **Mode production** : Lien uniquement par email (sécurité)
- ✅ Toast de confirmation quand le lien est copié
- ✅ Design cohérent avec le reste de l'application

---

## Notes importantes

1. **Sécurité** : Le lien magique n'est affiché qu'en mode développement (`ENVIRONMENT=development`)
2. **Production** : En production, le lien est uniquement envoyé par email (pas d'affichage)
3. **Expiration** : Les liens magiques expirent après 15 minutes (géré par le backend)
4. **Usage unique** : Chaque lien ne peut être utilisé qu'une seule fois (géré par le backend)



