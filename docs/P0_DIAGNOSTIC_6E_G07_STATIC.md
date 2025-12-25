# P0 - Diagnostic : 6e_G07 retourne exercice statique au lieu de dynamique

## Problème signalé

Lors de la génération pour le chapitre **6e_G07 (Symétrie axiale)**, un exercice **statique** est retourné ("test énoncé créer statique") au lieu d'un exercice **dynamique** avec le générateur `SYMETRIE_AXIALE_V2`.

## Logs de diagnostic ajoutés

### 1. Dans `generate_exercise_with_fallback()` (ligne ~90)

**Logs ajoutés** :
- `[FALLBACK_DEBUG]` : Total d'exercices récupérés, filtres appliqués
- `[FALLBACK_DEBUG]` : Détails de chaque exercice (id, is_dynamic, generator_key, offer, difficulty)
- `[FALLBACK_DEBUG]` : Nombre d'exercices dynamiques vs statiques
- `[FALLBACK_DEBUG]` : Filtrage selon `enabled_generators`
- `[FALLBACK_DEBUG]` : Tentative de fallback STATIC
- `[FALLBACK_STATIC]` : ⚠️ Avertissement quand un exercice statique est utilisé

### 2. Dans le routage pipeline (ligne ~1052)

**Logs ajoutés** :
- `[PIPELINE_DEBUG]` : Pipeline détecté (TEMPLATE/MIXED/SPEC)
- `[PIPELINE_DEBUG]` : `enabled_generators` depuis la DB

## Causes possibles

### Cause 1 : Pipeline "SPEC" au lieu de "TEMPLATE" ou "MIXED"

**Symptôme** : Le chapitre 6e_G07 a `pipeline="SPEC"` dans MongoDB, donc il ne passe jamais par `generate_exercise_with_fallback()`.

**Vérification** :
```bash
# Dans MongoDB
db.curriculum_chapters.findOne({code_officiel: "6E_G07"}, {pipeline: 1})
```

**Solution** : Changer le pipeline à `"TEMPLATE"` ou `"MIXED"` dans MongoDB.

### Cause 2 : Exercices dynamiques non marqués comme `is_dynamic: true`

**Symptôme** : Les exercices dynamiques existent en DB mais `is_dynamic` est `false` ou absent.

**Vérification** :
```bash
# Dans MongoDB
db.exercises.find(
  {chapter_code: "6E_G07", generator_key: "SYMETRIE_AXIALE_V2"},
  {id: 1, is_dynamic: 1, generator_key: 1, enonce_html: 1}
)
```

**Solution** : Mettre à jour les exercices dynamiques :
```javascript
db.exercises.updateMany(
  {chapter_code: "6E_G07", generator_key: "SYMETRIE_AXIALE_V2"},
  {$set: {is_dynamic: true}}
)
```

### Cause 3 : Générateur non activé dans `enabled_generators`

**Symptôme** : `SYMETRIE_AXIALE_V2` n'est pas dans `enabled_generators` pour 6e_G07.

**Vérification** :
```bash
# Dans MongoDB
db.curriculum_chapters.findOne(
  {code_officiel: "6E_G07"},
  {enabled_generators: 1}
)
```

**Solution** : Activer le générateur dans l'admin ou directement en DB.

### Cause 4 : Pipeline "MIXED" mais aucun exercice dynamique trouvé

**Symptôme** : Le pipeline est "MIXED" mais `dynamic_exercises` est vide, donc fallback vers STATIC.

**Vérification** : Voir les logs `[FALLBACK_DEBUG]` pour comprendre pourquoi.

**Solution** : Vérifier que les exercices dynamiques existent et sont correctement marqués.

## Actions de diagnostic

### Étape 1 : Vérifier le pipeline du chapitre

```bash
# Se connecter à MongoDB
docker exec -it le-maitre-mot-mongo mongosh le_maitre_mot_db

# Vérifier le pipeline
db.curriculum_chapters.findOne({code_officiel: "6E_G07"}, {pipeline: 1, enabled_generators: 1})
```

### Étape 2 : Vérifier les exercices en DB

```bash
# Compter les exercices dynamiques
db.exercises.countDocuments({chapter_code: "6E_G07", is_dynamic: true})

# Lister les exercices dynamiques
db.exercises.find(
  {chapter_code: "6E_G07", is_dynamic: true},
  {id: 1, generator_key: 1, is_dynamic: 1, offer: 1, difficulty: 1}
).pretty()

# Lister TOUS les exercices (dynamiques + statiques)
db.exercises.find(
  {chapter_code: "6E_G07"},
  {id: 1, is_dynamic: 1, generator_key: 1, offer: 1, difficulty: 1, enonce_html: 1}
).pretty()
```

### Étape 3 : Générer un exercice et vérifier les logs

1. Générer un exercice pour 6e_G07 via `/generer`
2. Vérifier les logs backend pour :
   - `[PIPELINE_DEBUG]` : Pipeline détecté
   - `[FALLBACK_DEBUG]` : Exercices récupérés
   - `[FALLBACK_STATIC]` : Si un exercice statique est utilisé

### Étape 4 : Vérifier les logs backend

```bash
# Voir les logs du backend
docker logs le-maitre-mot-backend --tail 100 | grep -E "FALLBACK_DEBUG|PIPELINE_DEBUG|FALLBACK_STATIC|6E_G07"
```

## Solutions selon la cause

### Si pipeline = "SPEC"

**Solution** : Changer le pipeline à "TEMPLATE" ou "MIXED" :

```javascript
// Dans MongoDB
db.curriculum_chapters.updateOne(
  {code_officiel: "6E_G07"},
  {$set: {pipeline: "MIXED"}}
)
```

### Si exercices dynamiques non marqués

**Solution** : Marquer les exercices dynamiques :

```javascript
// Dans MongoDB
db.exercises.updateMany(
  {
    chapter_code: "6E_G07",
    generator_key: "SYMETRIE_AXIALE_V2"
  },
  {
    $set: {is_dynamic: true}
  }
)
```

### Si générateur non activé

**Solution** : Activer le générateur dans l'admin ou directement :

```javascript
// Dans MongoDB
db.curriculum_chapters.updateOne(
  {code_officiel: "6E_G07"},
  {
    $push: {
      enabled_generators: {
        generator_key: "SYMETRIE_AXIALE_V2",
        is_enabled: true
      }
    }
  }
)
```

## Checklist de diagnostic

- [ ] Vérifier le pipeline du chapitre 6e_G07 dans MongoDB
- [ ] Vérifier que les exercices dynamiques existent avec `is_dynamic: true`
- [ ] Vérifier que `SYMETRIE_AXIALE_V2` est dans `enabled_generators`
- [ ] Générer un exercice et vérifier les logs `[FALLBACK_DEBUG]`
- [ ] Vérifier si le pipeline passe par `generate_exercise_with_fallback()` ou par le legacy

## Prochaines étapes

1. **Exécuter les commandes de diagnostic** ci-dessus
2. **Analyser les logs** `[FALLBACK_DEBUG]` et `[PIPELINE_DEBUG]`
3. **Appliquer la solution** selon la cause identifiée
4. **Tester à nouveau** la génération pour 6e_G07



