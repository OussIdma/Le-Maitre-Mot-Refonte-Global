# Fix: Affichage en Lot (Vision Prof) - UI Batch Generation

## Contexte

La page `/generer` affichait initialement un exercice à la fois avec pagination (boutons Précédent/Suivant). Cette UX n'était pas adaptée pour les professeurs qui ont besoin de voir plusieurs exercices en même temps pour préparer leurs cours.

## Décisions UX

### Affichage en lot
- **Vision prof** : Afficher plusieurs exercices sur une seule page
- **Défaut** : 5 exercices par lot
- **Options** : 3, 5, ou 10 exercices (sélecteur dans le formulaire)

### Suppression de la pagination
- Suppression des boutons "Précédent/Suivant"
- Tous les exercices du lot sont visibles simultanément
- Scroll vertical pour naviguer dans le lot

### Solutions repliables
- Les solutions sont masquées par défaut (Collapsible)
- Clic sur "Voir la correction" pour afficher/masquer
- Permet de voir rapidement tous les énoncés sans être distrait par les solutions

### Actions disponibles
1. **Générer le lot** : Génère un nouveau lot d'exercices
2. **Régénérer** : Régénère le lot avec les mêmes paramètres mais un nouveau seed (nouveaux exercices)
3. **Effacer** : Vide la liste des exercices

## Implémentation

### States ajoutés
- `batchSize` (défaut: 5) : Nombre d'exercices à générer
- `batchSeed` : Seed de base pour le lot (pour reproductibilité)
- `isGeneratingBatch` : Indicateur de génération en cours

### Génération séquentielle
- **Pourquoi séquentiel ?** : Évite la surcharge du backend et permet une meilleure gestion des erreurs
- **Seed déterministe** : `baseSeed + i` pour chaque exercice du lot
- **Gestion d'erreurs** :
  - Si erreur 422 structurée (POOL_EMPTY, PLACEHOLDER_UNRESOLVED, etc.) : toast + arrêt du batch
  - Si erreur réseau/500 : toast générique + arrêt du batch
  - Les exercices déjà générés sont conservés (batch partiel)

### Cas spéciaux
- **GM07/GM08** : Utilisent les endpoints batch dédiés (comportement inchangé)
- **Autres chapitres** : Génération séquentielle avec appels individuels

### Affichage
- Header "Lot de N exercices" avec indicateur de génération
- Liste verticale d'exercices numérotés (Exercice 1, Exercice 2, ...)
- Chaque exercice affiche :
  - Badges (niveau, chapitre, difficulté, premium si applicable)
  - Figure SVG (si présente)
  - Énoncé (toujours visible)
  - Solution (repliable, masquée par défaut)

## Compatibilité

- ✅ **Backend** : Aucune modification
- ✅ **API** : Utilise les mêmes endpoints existants
- ✅ **Erreurs 422** : Gestion conservée (toasts avec error_code)
- ✅ **Smoke test** : Inchangé (teste l'API, pas l'UI)
- ✅ **Mode Standard/grade/catalog** : Tous conservés

## Tests manuels

1. **batchSize=5 par défaut** : Vérifier que le sélecteur affiche 5 par défaut
2. **Générer → affiche 5 exercices** : Générer un lot et vérifier l'affichage
3. **Changer batchSize (3/10)** : Changer le nombre et vérifier que le bon nombre s'affiche
4. **Régénérer → nouveau lot** : Vérifier que les IDs sont différents
5. **Erreur 422 → toast clair** : Tester avec un chapitre sans exercices disponibles
6. **Effacer → liste vide** : Vérifier que le bouton efface bien la liste

## Notes techniques

- Les solutions utilisent `Collapsible` de Radix UI (déjà présent dans le projet)
- Le seed est déterministe pour permettre la reproductibilité
- La génération séquentielle évite les timeouts et surcharges
- Les erreurs sont gérées proprement avec arrêt du batch (pas de spinner infini)


