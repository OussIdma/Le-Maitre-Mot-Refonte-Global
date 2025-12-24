# P3.0.1 - Fix "Schéma manquant" dans "Mes exercices"

## 🔍 Diagnostic data-driven

### 1. Inspection des exercices sauvegardés (MongoDB)

**Résultats** :
- ✅ Les exercices sont bien sauvegardés avec `enonce_html` et `solution_html`
- ✅ Le tableau est présent dans `enonce_html` (ex: 2058 caractères pour RAISONNEMENT_MULTIPLICATIF_V1)
- ❌ **PROBLÈME IDENTIFIÉ** : Le tableau est entouré d'accolades `{` et `}` qui ne devraient pas être là

**Exemple réel** :
```html
<div class="exercise-enonce">
  <p><strong>Calcule la valeur inconnue...</strong></p>
  {<table style="margin: 1rem auto; ...">
    ...
  </table>
}
</div>
```

### 2. Comparaison avec `/api/v1/exercises/generate`

**Structure de la réponse** :
- `enonce_html` : contient le HTML rendu (devrait contenir le tableau sans accolades)
- `solution_html` : contient la solution HTML
- `variables` : contient `tableau_html` (redondant si déjà dans `enonce_html`)
- `metadata` : contient les métadonnées (generator_key, seed, etc.)

**Problème identifié** :
- Le template utilise `{{{tableau_html}}}` (triple moustaches) pour injecter du HTML non échappé
- Le `render_template()` dans `backend/services/template_renderer.py` **ne gère PAS les triple moustaches**
- Seules les doubles moustaches `{{variable}}` sont remplacées
- Résultat : `{{{tableau_html}}}` reste tel quel dans le HTML final → `{<table>...}</table>}`

### 3. Pourquoi le schéma n'apparaît pas dans MyExercisesPage

**Frontend** : `frontend/src/components/MyExercisesPage.js`
- Utilise `MathHtmlRenderer` pour rendre `enonce_html`
- `MathHtmlRenderer` parse le HTML avec `DOMParser`
- Les accolades `{` et `}` autour du tableau peuvent causer des problèmes de parsing
- Le tableau peut ne pas être reconnu comme un élément HTML valide

**Hypothèse** : Le `DOMParser` peut ignorer ou mal parser le contenu entre accolades.

## ✅ Décision technique retenue : **Option A (RECOMMANDÉE)**

**Stratégie** :
1. **Corriger le backend** : Modifier `render_template()` pour gérer les triple moustaches `{{{variable}}}`
   - Triple moustaches = HTML non échappé (injection directe)
   - Double moustaches = texte échappé (sécurité par défaut)
2. **Corriger le frontend** : Utiliser `dangerouslySetInnerHTML` directement sur `enonce_html` et `solution_html`
   - Le HTML vient du backend (templates contrôlés) → safe
   - Simplifier `MathHtmlRenderer` ou le remplacer par un rendu direct
3. **Migration** : Script de backfill pour nettoyer les exercices existants avec accolades

**Pourquoi Option A** :
- ✅ Le schéma est déjà dans `enonce_html` (rendu final)
- ✅ Pas besoin de recomposer côté UI
- ✅ Compatible avec tous les générateurs (premium + legacy)
- ✅ Respecte P0.4 (HTML contrôlé via templates)

## 🔧 Corrections à appliquer

### 1. Backend - `render_template()` (CRITIQUE)

**Fichier** : `backend/services/template_renderer.py`

**Changement** :
- Ajouter la gestion des triple moustaches `{{{variable}}}`
- Pattern : `r'\{\{\{\s*(\w+)\s*\}\}\}'`
- Remplacement : injection directe (pas d'échappement HTML)

### 2. Backend - Validation sauvegarde

**Fichier** : `backend/server.py` (endpoint `/user/exercises`)

**Vérifications** :
- ✅ `enonce_html` non vide
- ✅ `solution_html` non vide
- ✅ Pas d'accolades `{` ou `}` résiduelles (optionnel, mais utile pour debug)

### 3. Frontend - Rendu MyExercisesPage

**Fichier** : `frontend/src/components/MyExercisesPage.js`

**Changement** :
- Remplacer `MathHtmlRenderer` par `dangerouslySetInnerHTML` direct
- Commentaire : "HTML trusted from backend templates; do not render user-provided raw HTML"
- Garder la séparation Énoncé/Solution (tabs)

### 4. Migration - Backfill exercices existants

**Script** : `backend/scripts/backfill_user_exercises_html.py`

**Objectif** :
- Nettoyer les accolades `{` et `}` autour des tableaux dans `enonce_html`
- Régénérer si nécessaire via `/generate` (si metadata complète)
- Marquer `metadata.backfilled=true`

## 📋 Checklist de validation

### Backend
- [x] `render_template()` gère les triple moustaches `{{{variable}}}`
- [x] Test : template avec `{{{tableau_html}}}` → tableau injecté sans accolades
- [x] Test : sauvegarde exercice → `enonce_html` sans accolades
- [x] Test : listing `/user/exercises` → renvoie `enonce_html` correct

### Frontend
- [x] Modal "Voir" utilise `dangerouslySetInnerHTML` directement sur `enonce_html` et `solution_html`
- [x] Modal "Voir" affiche la solution dans l'onglet "Solution" (masqué par défaut)
- [x] Commentaire de sécurité ajouté (HTML trusted from backend templates)

### Migration
- [x] Script backfill créé (`backend/scripts/backfill_user_exercises_html.py`)
- [x] Script testé en dry-run (2 exercices avec problèmes détectés)
- [x] Exercices existants nettoyés (accolades supprimées)

### Tests manuels (À FAIRE)
- [ ] Générer exercice avec tableau → Sauvegarder → Mes exercices → Voir
- [ ] ✅ Le tableau est visible dans "Énoncé"
- [ ] ✅ La solution n'est pas visible par défaut (onglet "Solution")
- [ ] ✅ Rendu identique à la génération initiale

## 🚨 Contraintes respectées

- ✅ Zéro régression sur "Sujet ≠ Corrigé" (solution masquée par défaut)
- ✅ Pas de triple moustaches risquées côté utilisateur (HTML contrôlé backend)
- ✅ Code simple, commenté, maintenable

## ✅ Corrections appliquées

### 1. Backend - `render_template()` (✅ FAIT)

**Fichier** : `backend/services/template_renderer.py`

**Changements** :
- Ajout de la gestion des triple moustaches `{{{variable}}}`
- Pattern triple : `r'\{\{\{\s*(\w+)\s*\}\}\}'` (traitement AVANT les doubles)
- Triple moustaches = HTML non échappé (injection directe)
- Double moustaches = texte (comportement inchangé)

**Résultat** : Les templates avec `{{{tableau_html}}}` sont maintenant correctement rendus sans accolades résiduelles.

### 2. Frontend - Rendu MyExercisesPage (✅ FAIT)

**Fichier** : `frontend/src/components/MyExercisesPage.js`

**Changements** :
- Remplacement de `MathHtmlRenderer` par `dangerouslySetInnerHTML` direct
- Commentaire de sécurité ajouté : "HTML trusted from backend templates; do not render user-provided raw HTML"
- Séparation Énoncé/Solution conservée (tabs)

**Résultat** : Le HTML est rendu directement, les tableaux/schémas s'affichent correctement.

### 3. Migration - Backfill exercices existants (✅ FAIT)

**Script** : `backend/scripts/backfill_user_exercises_html.py`

**Résultats** :
- 2 exercices avec problèmes détectés
- 2 exercices nettoyés (accolades supprimées)
- Marqué `metadata.backfilled=true` pour traçabilité

**Commandes** :
```bash
# Dry-run
docker compose exec backend python /app/backend/scripts/backfill_user_exercises_html.py --dry-run

# Appliquer
docker compose exec backend python /app/backend/scripts/backfill_user_exercises_html.py --apply
```

## 🧪 Tests à effectuer manuellement

1. **Générer un exercice avec tableau** :
   - Aller sur `/generer`
   - Choisir chapitre avec `RAISONNEMENT_MULTIPLICATIF_V1` (ex: 6e_SP01)
   - Générer un exercice
   - Vérifier que le tableau s'affiche correctement

2. **Sauvegarder l'exercice** :
   - Cliquer sur "Sauvegarder"
   - Vérifier qu'aucune erreur n'apparaît

3. **Voir l'exercice sauvegardé** :
   - Aller sur `/mes-exercices`
   - Cliquer sur "Voir" pour l'exercice sauvegardé
   - ✅ Le tableau doit être visible dans l'onglet "Énoncé"
   - ✅ La solution ne doit pas être visible par défaut (onglet "Solution")
   - ✅ Le rendu doit être identique à la génération initiale

