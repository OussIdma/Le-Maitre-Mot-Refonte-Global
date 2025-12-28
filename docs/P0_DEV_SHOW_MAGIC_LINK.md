# P0 DEV LOGIN - Affichage du Magic Link en Mode Développement

## Contexte

En environnement de développement, on ne veut pas envoyer d'emails réels. Cette fonctionnalité permet d'afficher le lien magique directement dans l'interface utilisateur après la saisie de l'email.

## Variable d'environnement

### `DEV_SHOW_MAGIC_LINK`

**Type:** String (boolean-like)  
**Valeurs acceptées:** `'1'`, `'true'`, `'True'` (actif) | `'0'`, `'false'`, `'False'` ou non défini (inactif)  
**Défaut:** `'0'` (désactivé)

**Description:**  
Active l'affichage du lien magique dans l'UI au lieu d'envoyer un email. En mode dev, le backend retourne le lien dans la réponse JSON et le frontend l'affiche dans un bloc copiable avec un bouton "Ouvrir le lien".

## Configuration

### Backend

Ajouter dans `.env` ou variables d'environnement Docker :

```bash
DEV_SHOW_MAGIC_LINK=1
FRONTEND_URL=http://localhost:3000
```

### Frontend

Aucune configuration nécessaire. Le frontend détecte automatiquement la présence de `magic_link_url` dans la réponse.

## Comportement

### Mode DEV (`DEV_SHOW_MAGIC_LINK=1`)

1. **Backend:**
   - Ne tente PAS d'envoyer d'email
   - Retourne dans la réponse JSON :
     ```json
     {
       "message": "Si un compte Pro existe pour cette adresse, un lien de connexion a été envoyé",
       "success": true,
       "dev_mode": true,
       "magic_link_url": "http://localhost:3000/login/verify?token=...",
       "email": "user@example.com",
       "expires_in": 900
     }
     ```
   - Log le lien dans les logs backend : `🔗 MAGIC LINK (dev): ...`

2. **Frontend (`GlobalLoginModal`):**
   - Affiche un bloc bleu avec :
     - Le lien magique dans un champ input en lecture seule (copiable)
     - Bouton "Copier" pour copier le lien
     - Bouton "Ouvrir le lien" pour ouvrir directement le lien
     - Indication de la durée de validité (15 minutes)
     - Bouton "Réessayer" pour recommencer

### Mode PROD (`DEV_SHOW_MAGIC_LINK` non défini ou `0`)

1. **Backend:**
   - Envoie l'email via Brevo
   - Retourne une réponse neutre (sans `magic_link_url`)
   - Ne révèle pas si l'utilisateur existe ou non (sécurité)

2. **Frontend:**
   - Affiche le message standard "Email envoyé"
   - Pas de lien affiché

## Tests

### Test DEV

1. Définir `DEV_SHOW_MAGIC_LINK=1` dans `.env` backend
2. Redémarrer le backend
3. Ouvrir le modal de connexion
4. Saisir un email Pro valide
5. **Vérifier:**
   - ✅ Le bloc avec le lien magique s'affiche
   - ✅ Le bouton "Copier" fonctionne
   - ✅ Le bouton "Ouvrir le lien" ouvre le lien et connecte l'utilisateur
   - ✅ La durée de validité est affichée (15 minutes)

### Test PROD

1. Ne pas définir `DEV_SHOW_MAGIC_LINK` ou le mettre à `0`
2. Redémarrer le backend
3. Ouvrir le modal de connexion
4. Saisir un email Pro valide
5. **Vérifier:**
   - ✅ Le message "Email envoyé" s'affiche
   - ✅ Aucun lien n'est affiché
   - ✅ L'email est bien envoyé (vérifier la boîte mail)

## Fichiers modifiés

### Backend
- `backend/server.py` : Endpoint `/api/auth/request-login`
  - Utilise `DEV_SHOW_MAGIC_LINK` au lieu de `ENVIRONMENT == 'development'`
  - Retourne `magic_link_url`, `email`, `expires_in` en mode dev

### Frontend
- `frontend/src/components/GlobalLoginModal.js` :
  - Détecte `response.data.magic_link_url`
  - Affiche le bloc avec lien copiable et bouton "Ouvrir le lien"
  - Affiche la durée de validité
  
- `frontend/src/App.js` :
  - Gère aussi le magic link en mode dev (log dans console)

## Sécurité

- En mode PROD, aucun lien n'est jamais retourné dans la réponse
- Le backend utilise toujours une réponse neutre (ne révèle pas si l'utilisateur existe)
- Le token expire après 15 minutes
- Le token ne peut être utilisé qu'une seule fois

## Notes

- Le lien magique est valide pendant **15 minutes** (900 secondes)
- Le token est unique et ne peut être utilisé qu'une seule fois
- En mode dev, aucun email n'est envoyé (économie de coûts Brevo)


