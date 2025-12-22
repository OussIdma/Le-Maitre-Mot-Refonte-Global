# 📚 Documentation : Dépendances environnement PDF/SVG

## Vue d'ensemble

Cette documentation détaille la configuration et la gestion des dépendances système nécessaires pour la génération de PDF et SVG dans l'application Le-Maitre-Mot.

### Composants utilisés

| Composant | Version | Rôle |
|-----------|---------|------|
| **WeasyPrint** | 66.0 | Bibliothèque Python principale pour générer des PDF à partir de HTML/CSS |
| **Pango** | libpango-1.0-0 | Bibliothèque de rendu de texte avec support des polices complexes |
| **PangoFT2** | libpangoft2-1.0-0 | Support FreeType pour Pango (gestion avancée des polices) |
| **Cairo** | libcairo2 | Bibliothèque graphique 2D pour le rendu vectoriel |
| **GdkPixbuf** | libgdk-pixbuf2.0-0 | Chargement et manipulation d'images |
| **shared-mime-info** | - | Base de données des types MIME |

---

## 🔧 Pourquoi libpangoft2-1.0-0 est nécessaire ?

**WeasyPrint** utilise **Pango** pour le rendu de texte avancé, notamment :
- Support des polices TrueType/OpenType
- Gestion du texte multilingue (Unicode complet)
- Mise en page complexe (césure, justification)
- Rendu de caractères mathématiques

**libpangoft2-1.0-0** est la bibliothèque système qui permet à Pango d'utiliser **FreeType** pour rendre les polices. Sans cette bibliothèque, WeasyPrint ne peut pas fonctionner.

### Erreur typique sans libpangoft2

```python
OSError: cannot load library 'libpangoft2-1.0-0': 
libpangoft2-1.0-0: cannot open shared object file: No such file or directory.
Additionally, ctypes.util.find_library() did not manage to locate a library called 'libpangoft2-1.0-0'
```

---

## 📦 Installation des dépendances

### Méthode automatique (recommandée)

Le projet inclut un script d'installation automatique :

```bash
# Installation des dépendances système
python3 /app/scripts/ensure_system_dependencies.py
```

Ce script :
1. Vérifie la présence de chaque dépendance
2. Installe automatiquement les packages manquants via `apt-get`
3. Affiche un rapport détaillé

### Méthode manuelle

Si vous devez installer manuellement sur une distribution Debian/Ubuntu :

```bash
sudo apt-get update
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info
```

### Pour Alpine Linux (si applicable)

```bash
apk add --no-cache \
    pango \
    cairo \
    gdk-pixbuf \
    shared-mime-info
```

---

## ✅ Vérification de l'environnement

### Script de vérification complet

Le projet inclut un script de diagnostic :

```bash
# Vérifier l'environnement PDF/SVG
python3 /app/backend/scripts/check_pdf_env.py
```

#### Résultat attendu

```
============================================================
🔍 VÉRIFICATION ENVIRONNEMENT PDF/SVG
============================================================

🔍 Vérification des bibliothèques système...
  ✅ pangoft2-1.0 trouvée : libpangoft2-1.0.so.0
  ✅ pango-1.0 trouvée : libpango-1.0.so.0
  ✅ cairo trouvée : libcairo.so.2
  ✅ gdk_pixbuf-2.0 trouvée : libgdk_pixbuf-2.0.so.0

🐍 Vérification des packages Python...
  ✅ WeasyPrint importé avec succès
  ✅ Pillow importé avec succès
  ✅ Jinja2 importé avec succès

🧪 Test de génération PDF avec WeasyPrint...
  ✅ PDF généré avec succès (7550 octets)
  📄 PDF de test sauvegardé : /tmp/test_weasyprint.pdf

🎨 Test du support SVG...
  ✅ SVG rendu avec succès dans le PDF

============================================================
📊 RÉSUMÉ
============================================================
  System Libs: ✅ OK
  Python Packages: ✅ OK
  Weasyprint Basic: ✅ OK
  Svg Support: ✅ OK

🎉 PDF_ENV_OK - Environnement entièrement fonctionnel !
```

### Vérification manuelle

```bash
# Vérifier la présence d'une bibliothèque
ldconfig -p | grep libpangoft2

# Vérifier l'import Python
python3 -c "import weasyprint; print('✅ WeasyPrint OK')"

# Générer un PDF de test
python3 /app/backend/scripts/check_pdf_env.py
```

---

## 🚀 Script de pre-start

Le projet utilise un script de pre-start pour garantir que toutes les dépendances sont installées **avant** le démarrage du backend.

### Fichier : `/app/scripts/prestart.sh`

```bash
#!/bin/bash
set -e

echo "🚀 BACKEND PRE-START SCRIPT"

# Étape 1 : Installation des dépendances système
python3 /app/scripts/ensure_system_dependencies.py

# Étape 2 : Vérification de l'environnement PDF
python3 /app/backend/scripts/check_pdf_env.py

echo "🎯 Prêt à démarrer le backend !"
```

### Exécution manuelle

```bash
# Exécuter le pre-start avant de démarrer le backend
bash /app/scripts/prestart.sh

# Puis démarrer le backend
sudo supervisorctl restart backend
```

---

## 🐍 Imports lazy de WeasyPrint

Pour éviter les erreurs au démarrage du backend si les dépendances ne sont pas encore installées, **WeasyPrint est importé de manière lazy** (uniquement dans les fonctions qui en ont besoin).

### Avant (❌ import global)

```python
import weasyprint

def generate_pdf():
    pdf = weasyprint.HTML(string=html).write_pdf()
```

### Après (✅ import lazy)

```python
# Pas d'import global

def generate_pdf():
    import weasyprint  # Import seulement quand nécessaire
    pdf = weasyprint.HTML(string=html).write_pdf()
```

**Avantages** :
- Le backend peut démarrer même si WeasyPrint a des problèmes
- L'erreur apparaît seulement lors de l'appel à la génération PDF
- Plus facile de diagnostiquer et corriger en production

---

## 📂 Fichiers de référence

| Fichier | Rôle |
|---------|------|
| `/app/scripts/ensure_system_dependencies.py` | Installation automatique des dépendances système |
| `/app/scripts/prestart.sh` | Script de pre-start (installation + vérification) |
| `/app/backend/scripts/check_pdf_env.py` | Diagnostic complet de l'environnement PDF/SVG |
| `/app/backend/requirements.txt` | Dépendances Python (ligne 128 : weasyprint==66.0) |
| `/app/backend/server.py` | Import lazy de weasyprint (lignes modifiées) |
| `/app/backend/engine/pdf_engine/mathalea_sheet_pdf_builder.py` | Génération PDF avec WeasyPrint |

---

## 🛠️ Maintenance

### Ajouter une nouvelle dépendance système

Modifier `/app/scripts/ensure_system_dependencies.py` :

```python
required_packages = [
    "libpango-1.0-0",
    "libpangoft2-1.0-0",
    "libcairo2",
    "libgdk-pixbuf2.0-0",
    "shared-mime-info",
    "votre-nouveau-package"  # Ajouter ici
]
```

### Mettre à jour WeasyPrint

```bash
# Backend
cd /app/backend
pip install --upgrade weasyprint

# Vérifier la nouvelle version
pip show weasyprint

# Mettre à jour requirements.txt
pip freeze | grep weasyprint >> requirements.txt
```

### Troubleshooting

#### Le backend ne démarre pas

```bash
# 1. Vérifier les logs
tail -n 100 /var/log/supervisor/backend.err.log

# 2. Réinstaller les dépendances
python3 /app/scripts/ensure_system_dependencies.py

# 3. Redémarrer le backend
sudo supervisorctl restart backend
```

#### PDF généré est vide ou corrompu

```bash
# Tester la génération PDF
python3 /app/backend/scripts/check_pdf_env.py

# Vérifier le PDF généré
file /tmp/test_weasyprint.pdf
```

#### Erreur "cannot load library"

```bash
# Vérifier la présence des bibliothèques
ldconfig -p | grep -E "pango|cairo|gdk"

# Réinstaller si nécessaire
sudo apt-get install --reinstall \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0
```

---

## 📊 Versions minimales requises

| Package | Version minimale | Version testée |
|---------|------------------|----------------|
| libpango-1.0-0 | 1.40+ | 1.50.14 |
| libpangoft2-1.0-0 | 1.40+ | 1.50.14 |
| libcairo2 | 1.14+ | 1.16.0 |
| libgdk-pixbuf2.0-0 | 2.36+ | 2.42.10 |
| WeasyPrint (Python) | 60.0+ | 66.0 |

---

## 🎯 Commandes rapides

```bash
# Installation complète
python3 /app/scripts/ensure_system_dependencies.py

# Vérification environnement
python3 /app/backend/scripts/check_pdf_env.py

# Pre-start complet
bash /app/scripts/prestart.sh

# Redémarrer le backend
sudo supervisorctl restart backend

# Tester la génération PDF
curl -X POST http://localhost:8001/api/mathalea/sheets/{sheet_id}/generate-pdf

# Vérifier les logs backend
tail -f /var/log/supervisor/backend.err.log
```

---

## 📌 Notes importantes

### ⚠️ À ne pas supprimer

Les packages suivants sont **critiques** et ne doivent **JAMAIS** être supprimés :
- `libpango-1.0-0`
- `libpangoft2-1.0-0`
- `libcairo2`
- `libgdk-pixbuf2.0-0`

### ✅ Règles de sécurité

- Toujours tester les changements avec `check_pdf_env.py` avant de déployer
- Exécuter `prestart.sh` dans les environnements de CI/CD
- Ne jamais hardcoder de chemins de bibliothèques système
- Utiliser des imports lazy pour WeasyPrint

---

## 📖 Références externes

- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/)
- [Pango Documentation](https://docs.gtk.org/Pango/)
- [Cairo Graphics](https://www.cairographics.org/)
- [GdkPixbuf Documentation](https://docs.gtk.org/gdk-pixbuf/)

---

**Dernière mise à jour** : 2025-01-XX  
**Auteur** : Emergent AI  
**Projet** : Le-Maitre-Mot-v16-Refonte
