# Déploiement - Exigences et Configuration

## Dépendances Système Requises

### WeasyPrint - Génération PDF
**Bibliothèque système requise** : `libpangoft2-1.0-0`

**Problème** : Sans cette bibliothèque, le backend ne peut pas démarrer car WeasyPrint (utilisé pour la génération de PDF) échoue lors de l'import.

**Solution** : Installer la bibliothèque au niveau du container/système.

### Installation (Debian/Ubuntu)
```bash
apt-get update && apt-get install -y libpangoft2-1.0-0 && rm -rf /var/lib/apt/lists/*
```

### Installation Persistante (Dockerfile)
Si vous utilisez un Dockerfile pour construire l'image, ajoutez ces lignes :

```dockerfile
# Install system dependencies for WeasyPrint
RUN apt-get update && \
    apt-get install -y libpangoft2-1.0-0 && \
    rm -rf /var/lib/apt/lists/*
```

**Placement recommandé** : Après l'installation des dépendances système de base, avant l'installation des packages Python.

### Alternative (Script d'initialisation)
Si la modification du Dockerfile n'est pas possible, créer un script d'initialisation qui s'exécute au démarrage du container :

```bash
#!/bin/bash
# /app/init.sh
apt-get update && apt-get install -y libpangoft2-1.0-0 && rm -rf /var/lib/apt/lists/*
```

---

## ✅ Fix Appliqué
- Date : 2025-12-07
- Méthode : Installation manuelle de `libpangoft2-1.0-0` 
- Status : Temporaire (perdu au redémarrage du container)
- Action requise : Intégrer l'installation dans le Dockerfile ou script d'initialisation pour la rendre permanente

---

## Notes Techniques
- Cette dépendance est nécessaire pour le rendu de polices dans les PDF générés par WeasyPrint
- Sans elle, le serveur backend affiche : `OSError: cannot load library 'libpangoft2-1.0-0'`
- Impact : Le backend ne démarre pas, rendant l'application inutilisable
