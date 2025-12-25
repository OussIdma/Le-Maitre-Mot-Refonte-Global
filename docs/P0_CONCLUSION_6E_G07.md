# P0 - Conclusion : Cause exacte et Fix minimal pour 6e_G07

## Cause exacte (à déterminer après diagnostic)

**Hypothèses** (à valider avec les logs et MongoDB) :

### Hypothèse 1 : Cause C - Exercices dynamiques n'existent pas pour chapter_code

**Preuve attendue** :
```javascript
// Dans MongoDB
db.admin_exercises.countDocuments({chapter_code: "6E_G07", is_dynamic: true})
// → Retourne 0
```

**Fix minimal** :
- Créer des exercices dynamiques avec `chapter_code: "6E_G07"` et `is_dynamic: true`
- OU corriger le `chapter_code` des exercices dynamiques existants

### Hypothèse 2 : Cause B - Exercices dynamiques filtrés par enabled_generators

**Preuve attendue** :
```javascript
// Dans MongoDB
db.curriculum_chapters.findOne({code_officiel: "6e_G07"}, {enabled_generators: 1})
// → enabled_generators ne contient pas "SYMETRIE_AXIALE_V2" ou "SYMETRIE_PROPRIETES"
```

**Fix minimal** :
- Activer les générateurs dans l'admin ou directement en DB :
```javascript
db.curriculum_chapters.updateOne(
  {code_officiel: "6e_G07"},
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

### Hypothèse 3 : Cause A - Pipeline non lu ou incorrect

**Preuve attendue** :
```javascript
// Dans MongoDB
db.curriculum_chapters.findOne({code_officiel: "6e_G07"}, {pipeline: 1})
// → pipeline est null, "SPEC", ou autre chose que "MIXED"
```

**Fix minimal** :
```javascript
db.curriculum_chapters.updateOne(
  {code_officiel: "6e_G07"},
  {$set: {pipeline: "MIXED"}}
)
```

### Hypothèse 4 : Cause C - Problème de casse chapter_code

**Preuve attendue** :
```javascript
// Les exercices dynamiques ont un chapter_code différent
db.admin_exercises.find(
  {generator_key: {$regex: "SYMETRIE", $options: "i"}},
  {chapter_code: 1, is_dynamic: 1}
).pretty()
// → chapter_code est "6e_G07" ou "6e_g07" au lieu de "6E_G07"
```

**Fix minimal** :
- Normaliser tous les `chapter_code` en uppercase :
```javascript
db.admin_exercises.updateMany(
  {chapter_code: {$regex: "^6[Ee]_G07$", $options: "i"}},
  {$set: {chapter_code: "6E_G07"}}
)
```

### Hypothèse 5 : Cause C - is_dynamic non marqué

**Preuve attendue** :
```javascript
// Les exercices ont generator_key mais is_dynamic est false ou absent
db.admin_exercises.find(
  {chapter_code: "6E_G07", generator_key: {$regex: "SYMETRIE", $options: "i"}},
  {is_dynamic: 1, generator_key: 1}
).pretty()
// → is_dynamic est false ou null
```

**Fix minimal** :
```javascript
db.admin_exercises.updateMany(
  {
    chapter_code: "6E_G07",
    generator_key: {$regex: "SYMETRIE", $options: "i"}
  },
  {$set: {is_dynamic: true}}
)
```

## Processus de diagnostic

### Étape 1 : Exécuter le script de diagnostic

```bash
python scripts/diagnostic_6e_g07.py
```

### Étape 2 : Générer un exercice et vérifier les logs

1. Générer un exercice pour 6e_G07 via `/generer`
2. Vérifier les logs backend :
```bash
docker logs le-maitre-mot-backend --tail 200 | grep -E "DIAG_6E_G07|FALLBACK_DEBUG|PIPELINE_DEBUG|FALLBACK_STATIC"
```

### Étape 3 : Vérifier MongoDB manuellement

```javascript
// 1. Vérifier le chapitre
db.curriculum_chapters.findOne({code_officiel: "6e_G07"}, {pipeline: 1, enabled_generators: 1})

// 2. Vérifier les exercices dynamiques
db.admin_exercises.countDocuments({chapter_code: "6E_G07", is_dynamic: true})

// 3. Vérifier les exercices avec generator_key SYMETRIE
db.admin_exercises.find(
  {chapter_code: "6E_G07", generator_key: {$regex: "SYMETRIE", $options: "i"}},
  {id: 1, generator_key: 1, is_dynamic: 1}
).pretty()
```

## Format de sortie attendu

Après diagnostic, remplir :

```
Cause exacte: [A/B/C/D/E] - [Description]

Preuve:
- Fichier/ligne: [fichier:ligne]
- Log: [exemple de log]
- Requête MongoDB: [requête + résultat]

Fix minimal:
[Diff proposé ou commande MongoDB]

Test manuel:
1. [Étape 1]
2. [Étape 2]
3. [Étape 3]
```

## Logs de diagnostic disponibles

Tous les logs sont préfixés avec `[DIAG_6E_G07]` pour faciliter le filtrage :

- `[DIAG_6E_G07] code_officiel=... → chapter_code_for_db=...`
- `[DIAG_6E_G07] chapter_from_db.pipeline=...`
- `[DIAG_6E_G07] enabled_generators_for_chapter=...`
- `[DIAG_6E_G07] MongoDB query: collection='admin_exercises', query=...`
- `[DIAG_6E_G07] total_exercises=...`
- `[DIAG_6E_G07] dynamic_exercises_count=...`
- `[DIAG_6E_G07] static_exercises_count=...`
- `[FALLBACK_STATIC] ⚠️ Utilisation d'un exercice STATIC pour 6E_G07: ...`



