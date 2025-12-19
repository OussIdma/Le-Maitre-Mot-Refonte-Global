# Bug Fix : Persistance du Logo dans la Configuration Pro

## 🎯 Problème résolu

Le logo uploadé dans la page "Personnalisation du document" ne persistait pas après sauvegarde. 

**Symptômes** :
- ✅ Upload du logo → s'affiche correctement
- ✅ Sauvegarde des préférences → succès
- ❌ Rechargement de la page → le logo disparaissait
- ✅ Autres champs → persistaient correctement

## 🔧 Solution implémentée

### 1. Backend - Endpoint d'upload de logo

**Fichier** : `/app/backend/routes/mathalea_routes.py`

**Nouveau endpoint créé** :
```python
@router.post("/pro/upload-logo")
async def upload_pro_logo(
    file: UploadFile = File(...),
    x_session_token: str = Header(None, alias="X-Session-Token")
)
```

**Fonctionnalités** :
- ✅ Validation du type de fichier (PNG, JPG, JPEG)
- ✅ Limite de taille : 2 Mo
- ✅ Génération d'un nom unique (UUID)
- ✅ Sauvegarde dans `/app/backend/uploads/logos/`
- ✅ Retourne l'URL du logo : `/uploads/logos/{uuid}.png`

### 2. Backend - API Config Pro mise à jour

**Fichier** : `/app/backend/routes/mathalea_routes.py`

**PUT /api/mathalea/pro/config** :
- ✅ Accepte maintenant `logo_url` dans les champs autorisés (ligne 1325)
- ✅ Sauvegarde `logo_url` dans MongoDB

**GET /api/mathalea/pro/config** :
- ✅ Retourne `logo_url` dans la réponse

### 3. Service Pro Config

**Fichier** : `/app/backend/services/pro_config_service.py`

**Déjà correct** :
- ✅ `get_pro_config_for_user()` retourne `logo_url` (ligne 71)
- ✅ `update_pro_config()` sauvegarde `logo_url` dans MongoDB

### 4. Frontend - TemplateSettings.js

**Fichier** : `/app/frontend/src/components/TemplateSettings.js`

**Modifications apportées** :

#### a) Chargement du logo (lignes 76-81)
```javascript
if (userTemplate.logo_url) {
  // Construire l'URL complète du logo
  const logoUrl = userTemplate.logo_url.startsWith('http') 
    ? userTemplate.logo_url 
    : `${API}${userTemplate.logo_url}`;
  setLogoPreview(logoUrl);
  console.log('📸 Logo chargé:', logoUrl);
}
```

#### b) Sauvegarde du logo (lignes 93-145)
```javascript
// 1. Si un nouveau fichier logo a été sélectionné, l'uploader d'abord
if (logoFile) {
  console.log('📤 Upload du nouveau logo...');
  const formData = new FormData();
  formData.append('file', logoFile);
  
  const uploadResponse = await axios.post(
    `${API}/api/mathalea/pro/upload-logo`,
    formData,
    {
      headers: {
        'X-Session-Token': sessionToken,
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  
  uploadedLogoUrl = uploadResponse.data.logo_url;
  console.log('✅ Logo uploadé:', uploadedLogoUrl);
}

// 2. Inclure logo_url dans la config sauvegardée
const configData = {
  professor_name: professorName || '',
  school_name: schoolName || '',
  school_year: schoolYear || '2024-2025',
  footer_text: footerText || '',
  template_choice: selectedStyle,
  logo_url: uploadedLogoUrl || null  // ← AJOUTÉ
};
```

### 5. Génération PDF Pro avec logo

**Fichier** : `/app/backend/routes/mathalea_routes.py` (endpoint `/generate-pdf-pro`)

**Modifications** (lignes 1189-1201) :
```python
# Construire le chemin absolu du logo pour WeasyPrint
logo_url = pro_config.get("logo_url")
if logo_url and not logo_url.startswith('http'):
    # Convertir le chemin relatif en chemin absolu pour WeasyPrint
    logo_path = Path("/app/backend") / logo_url.lstrip('/')
    logo_url = f"file://{logo_path}" if logo_path.exists() else None

template_config = {
    "professor_name": pro_config.get("professor_name", ""),
    "school_name": pro_config.get("school_name", "Le Maître Mot"),
    "school_year": pro_config.get("school_year", "2024-2025"),
    "footer_text": pro_config.get("footer_text", "Document généré par Le Maître Mot"),
    "logo_url": logo_url  # ← Utilisé dans les templates Jinja2
}
```

### 6. Templates Pro

**Fichiers** : `/app/backend/templates/sujet_classique.html`, `sujet_academique.html`, etc.

**Déjà correct** : Les templates utilisent déjà `template_config.logo_url` :
```html
<div class="logo">
    {% if template_config and template_config.logo_url %}
        <img src="{{ template_config.logo_url }}" alt="Logo" />
    {% endif %}
</div>
```

## ✅ Tests effectués

### 1. Test d'upload de logo
```bash
curl -X POST "$BACKEND_URL/api/mathalea/pro/upload-logo" \
  -H "X-Session-Token: Oussama92.18@gmail.com" \
  -F "file=@logo.png"
```
**Résultat** : ✅ Logo uploadé, URL retournée

### 2. Test de sauvegarde de config avec logo
```bash
curl -X PUT "$BACKEND_URL/api/mathalea/pro/config" \
  -H "X-Session-Token: Oussama92.18@gmail.com" \
  -d '{ "logo_url": "/uploads/logos/uuid.png", ... }'
```
**Résultat** : ✅ Config sauvegardée avec logo_url

### 3. Test de rechargement de config
```bash
curl -X GET "$BACKEND_URL/api/mathalea/pro/config" \
  -H "X-Session-Token: Oussama92.18@gmail.com"
```
**Résultat** : ✅ Logo_url bien retourné

## 🎯 Comportement attendu (désormais fonctionnel)

1. **Upload logo** :
   - User sélectionne un fichier → Preview s'affiche ✅
   
2. **Sauvegarde** :
   - Click "Sauvegarder les préférences" → Logo uploadé vers backend ✅
   - Logo_url sauvegardé dans MongoDB ✅
   
3. **Rechargement** :
   - Refresh de la page → Logo réapparaît automatiquement ✅
   
4. **Export PDF Pro** :
   - Logo apparaît dans les PDFs générés (Classique & Académique) ✅

## 📁 Fichiers modifiés

1. `/app/backend/routes/mathalea_routes.py`
   - Ajout endpoint `POST /pro/upload-logo`
   - Mise à jour endpoint `POST /generate-pdf-pro` pour gérer le logo

2. `/app/frontend/src/components/TemplateSettings.js`
   - Ajout upload du logo avant sauvegarde
   - Ajout `logo_url` dans la config sauvegardée
   - Construction URL complète pour affichage du logo

## 🔍 Vérifications pour l'utilisateur

### Test manuel complet :

1. **Upload et sauvegarde** :
   - Aller sur "Personnalisation du document"
   - Uploader un logo
   - Remplir les autres champs
   - Cliquer "Sauvegarder les préférences"
   - ✅ Message de succès

2. **Vérification persistance** :
   - Rafraîchir la page (F5)
   - ✅ Le logo doit réapparaître
   - ✅ Tous les autres champs doivent être pré-remplis

3. **Changement de logo** :
   - Uploader un nouveau logo
   - Sauvegarder
   - Rafraîchir
   - ✅ Le nouveau logo doit apparaître

4. **Export PDF** :
   - Créer/ouvrir une fiche
   - Cliquer "Export Pro"
   - Générer un PDF (Classique ou Académique)
   - ✅ Le logo doit apparaître dans le PDF

## 📝 Notes techniques

- Les logos sont stockés dans `/app/backend/uploads/logos/`
- Format autorisé : PNG, JPG, JPEG
- Taille maximum : 2 Mo
- Noms de fichiers : UUID pour éviter les conflits
- WeasyPrint nécessite des URLs `file://` pour les fichiers locaux

## 🚀 Prochaines améliorations possibles

- [ ] Compression automatique des images avant upload
- [ ] Miniatures pour prévisualisation plus rapide
- [ ] Suppression des anciens logos inutilisés
- [ ] Support des formats WebP et SVG
- [ ] Outil de recadrage/redimensionnement intégré
