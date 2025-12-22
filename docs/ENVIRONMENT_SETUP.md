# Configuration de l'environnement - Solution permanente

## Problème résolu

Le backend nécessite la bibliothèque système `libpangoft2-1.0-0` pour que WeasyPrint puisse générer des PDFs. Cette dépendance n'était pas installée de manière persistante, nécessitant une installation manuelle à chaque redémarrage du conteneur.

## Solution implémentée

### 1. Script d'initialisation automatique

Un script Python a été créé dans `/app/scripts/ensure_system_dependencies.py` qui :
- Vérifie si `libpangoft2-1.0-0` est installé
- L'installe automatiquement si nécessaire
- Utilise `dpkg-query` pour une détection fiable

### 2. Intégration au démarrage de l'application

Le script d'initialisation est appelé automatiquement dans `/app/backend/server.py` avant le démarrage de FastAPI :
```python
def ensure_system_dependencies():
    """
    Garantit que toutes les dépendances système critiques sont installées.
    Appelé au démarrage de l'application pour résoudre le problème de libpangoft2-1.0-0.
    """
    ...

# Exécuter la vérification des dépendances au démarrage
ensure_system_dependencies()
```

### 3. Fonctionnement

- À chaque démarrage du backend, le script vérifie automatiquement la présence de la dépendance
- Si elle est manquante, elle est installée automatiquement via `apt-get`
- Le processus de démarrage continue normalement
- Aucune intervention manuelle n'est requise

## Fichiers modifiés

1. **`/app/scripts/ensure_system_dependencies.py`** (CRÉÉ)
   - Script Python autonome pour la gestion des dépendances système
   - Peut être exécuté manuellement : `python3 /app/scripts/ensure_system_dependencies.py`

2. **`/app/backend/server.py`** (MODIFIÉ)
   - Ajout de la fonction `ensure_system_dependencies()` 
   - Appel automatique au démarrage de l'application
   - Imports supplémentaires : `sys`, `subprocess`

## Vérification

Pour vérifier que la solution fonctionne :

```bash
# Vérifier que la dépendance est installée
dpkg -l | grep libpangoft2

# Vérifier les logs de démarrage du backend
tail -n 50 /var/log/supervisor/backend.out.log | grep "dépendances"

# Test de génération PDF
curl -X POST "${BACKEND_URL}/api/mathalea/sheets/{sheet_id}/export-standard" \
  -H "X-Session-Token: Oussama92.18@gmail.com"
```

## Résultats attendus

Dans les logs de démarrage du backend, vous devriez voir :
```
🔧 Vérification des dépendances système...
🔍 Vérification des dépendances système...
✅ libpangoft2-1.0-0 est déjà installé
✅ Toutes les dépendances système sont prêtes
```

Si la dépendance était manquante :
```
🔧 Vérification des dépendances système...
🔍 Vérification des dépendances système...
⚠️  libpangoft2-1.0-0 n'est pas installé, installation en cours...
📦 Installation de libpangoft2-1.0-0...
✅ libpangoft2-1.0-0 installé avec succès
✅ Toutes les dépendances système sont prêtes
```

## Avantages de cette solution

✅ **Automatique** : Aucune intervention manuelle requise
✅ **Robuste** : Détection fiable de l'état d'installation
✅ **Non-bloquant** : L'application démarre même en cas d'erreur d'installation
✅ **Extensible** : Facile d'ajouter d'autres dépendances système si nécessaire
✅ **Traçable** : Logs clairs pour le debugging

## Maintenance future

Pour ajouter de nouvelles dépendances système, modifiez la liste `required_packages` dans `/app/scripts/ensure_system_dependencies.py` :

```python
required_packages = [
    "libpangoft2-1.0-0",
    # Ajouter ici d'autres packages si nécessaire
]
```
