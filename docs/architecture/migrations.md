# Migration vers une base de données comme source de vérité

## Objectif

Arrêter toute écriture dynamique dans `backend/data/*.py` qui causait des comportements fantômes et des risques de crash/rollback.
Passer à MongoDB comme source de vérité unique pour les exercices.

## Problème identifié

Le système d'origine écrivait dynamiquement des fichiers Python dans `backend/data/*.py` pendant l'exécution, ce qui posait plusieurs problèmes :
- Risque de corruption de fichiers en production
- Comportements fantômes difficiles à diagnostiquer
- Risques de rollback lors de déploiements
- Difficile de gérer la concurrence entre plusieurs instances

## Solution mise en œuvre

### 1. Mode lecture seule (READONLY_CODEBASE)

Un nouveau flag d'environnement `READONLY_CODEBASE=true` a été ajouté pour empêcher toute écriture dans les fichiers Python :

```python
READONLY_CODEBASE = os.getenv("READONLY_CODEBASE", "false").lower() == "true"
```

Quand ce flag est activé :
- Toute tentative d'écriture dans `backend/data/*.py` lève une `HTTPException(503)` avec le code `"READONLY_MODE"`
- L'interface admin affiche un message clair à l'utilisateur
- Le système continue de fonctionner mais utilise uniquement la base de données

### 2. Script de migration

Un script de migration `backend/scripts/migrate_data_files_to_db.py` a été créé pour :

- Lire les fichiers Python existants (`gm07_exercises.py`, `gm08_exercises.py`, `tests_dyn_exercises.py`)
- Insérer/upsert les exercices dans MongoDB (`admin_exercises` collection) si absents
- Calculer un UID stable pour chaque exercice basé sur son contenu pour éviter les doublons
- Afficher un résumé : `inserted/updated/skipped`

### 3. Modifications apportées

#### Fichier : `backend/services/exercise_persistence_service.py`

- Ajout du flag `READONLY_CODEBASE`
- Modification de la méthode `_sync_to_python_file()` pour vérifier le flag avant d'écrire
- Modification de la méthode `_reload_handler()` pour tenir compte du mode lecture seule

#### Fichier : `backend/scripts/migrate_data_files_to_db.py`

Script autonome pour migrer les données existantes vers MongoDB.

## Procédure de migration

### Phase 1 : Préparation

1. Sauvegarder les fichiers Python existants :
   ```bash
   cp backend/data/gm07_exercises.py backup_gm07_exercises_$(date +%Y%m%d_%H%M%S).py
   cp backend/data/gm08_exercises.py backup_gm08_exercises_$(date +%Y%m%d_%H%M%S).py
   cp backend/data/tests_dyn_exercises.py backup_tests_dyn_exercises_$(date +%Y%m%d_%H%M%S).py
   ```

2. Arrêter les services en écriture (admin UI, API d'ajout/modification d'exercices)

### Phase 2 : Migration des données

1. Lancer le script de migration :
   ```bash
   cd backend
   python scripts/migrate_data_files_to_db.py
   ```

2. Vérifier le résumé : `inserted/updated/skipped`
   - `inserted` : nouveaux exercices ajoutés à la base
   - `updated` : exercices existants mis à jour (contenu changé)
   - `skipped` : exercices inchangés, déjà présents

### Phase 3 : Activation du mode lecture seule

1. Définir la variable d'environnement :
   ```bash
   export READONLY_CODEBASE=true
   ```

2. Redémarrer les services

### Phase 4 : Validation

1. Vérifier que les exercices sont accessibles via l'interface admin
2. Tester la génération d'exercices
3. Confirmer qu'aucune écriture dans `backend/data/*.py` n'a lieu

## Avantages

- **Stabilité** : Plus de risque de corruption de fichiers en production
- **Fiabilité** : MongoDB comme source de vérité unique
- **Scalabilité** : Meilleure gestion de la concurrence
- **Traçabilité** : Historique des modifications dans la base de données
- **Sécurité** : Empêche les modifications accidentelles de fichiers système

## Rollback (si nécessaire)

Pour revenir au comportement précédent :
1. Définir `READONLY_CODEBASE=false`
2. Redémarrer les services
3. Le système revient à l'écriture dans les fichiers Python (si nécessaire)

## Points de vigilance

- Le script de migration ne supprime pas les fichiers Python existants
- Les modifications futures se font uniquement dans la base de données
- Le mode lecture seule empêche TOUTE écriture dans les fichiers Python
- Il est recommandé de conserver les sauvegardes des fichiers originaux