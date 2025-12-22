# Guide Admin : Créer un exercice dynamique en 2 minutes

## Qu'est-ce qu'un exercice dynamique ?

Un exercice **dynamique** utilise des templates avec des variables `{{variable}}` qui sont remplacées par des valeurs générées automatiquement. Cela permet de créer une **infinité de variantes** à partir d'un seul template.

## Étapes de création

### 1. Accéder à l'admin
- Aller sur `/admin/curriculum`
- Sélectionner un chapitre (ex: `6e_TESTS_DYN`)
- Cliquer sur "Ajouter"

### 2. Activer le mode dynamique
- Dans la modal, activer le switch **"Exercice dynamique (template)"** 🎲
- Un panneau violet apparaît avec les options dynamiques

### 3. Choisir un générateur
- Sélectionner un générateur dans le dropdown (ex: `THALES_V1`)
- Les **variables disponibles** s'affichent automatiquement
- Cliquer sur une variable pour la copier

### 4. Écrire les templates
Les templates sont pré-remplis avec un exemple. Adaptez-les selon vos besoins :

**Énoncé :**
```html
<p>On considère {{figure_type_article}} de côté <strong>{{cote_initial}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient {{coefficient_str}}.</p>
<p>Quelle est la mesure du côté obtenu ?</p>
```

**Solution :**
```html
<h4>Correction</h4>
<ol>
  <li><strong>Méthode :</strong> On multiplie par le coefficient.</li>
  <li><strong>Calcul :</strong> {{cote_initial}} × {{coefficient_str}} = {{cote_final}}</li>
  <li><strong>Réponse :</strong> Le côté mesure {{cote_final}} cm.</li>
</ol>
```

### 5. Prévisualiser
- Cliquer sur **"Prévisualiser un exemple généré"**
- Un exercice est généré avec des valeurs aléatoires
- Vérifier que le rendu est correct
- Si des variables sont inconnues, une alerte s'affiche

### 6. Sauvegarder
- Cliquer sur "Créer"
- L'exercice est prêt à être utilisé !

## Variables disponibles (THALES_V1)

| Variable | Type | Description | Exemple |
|----------|------|-------------|---------|
| `{{figure_type}}` | string | Type de figure | `triangle` |
| `{{figure_type_article}}` | string | Avec article | `un triangle` |
| `{{coefficient}}` | number | Coefficient | `2` |
| `{{coefficient_str}}` | string | Coefficient texte | `"2"` |
| `{{transformation}}` | string | Type | `agrandissement` |
| `{{cote_initial}}` | number | Côté départ | `5` |
| `{{cote_final}}` | number | Côté arrivée | `10` |
| `{{aire_initiale}}` | number | Aire départ | `25` |
| `{{aire_finale}}` | number | Aire arrivée | `100` |

## Mode SVG AUTO

Par défaut, le **mode AUTO** est activé :
- Les figures SVG sont générées automatiquement
- Pas besoin d'écrire de "brief SVG"
- Le générateur crée les figures à partir des variables

## Conseils

✅ **DO**
- Utiliser les templates exemples comme base
- Prévisualiser avant de sauvegarder
- Vérifier que toutes les variables existent

❌ **DON'T**
- Ne pas inventer de variables (elles ne seront pas remplacées)
- Ne pas utiliser de LaTeX (`$...$`)
- Ne pas mélanger statique et dynamique dans le même exercice

## Dépannage

**"Variable inconnue" dans le preview :**
→ Vérifiez l'orthographe exacte de la variable

**"La requête a expiré" :**
→ Problème de connexion, cliquez sur "Réessayer"

**Le SVG ne s'affiche pas :**
→ Vérifiez que "Nécessite un SVG" est coché

---
*Dernière mise à jour : Décembre 2025*
