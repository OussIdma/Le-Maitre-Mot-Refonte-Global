# P0 Preset-first Premium Checks (CALCUL_NOMBRES_V1, RAISONNEMENT_MULTIPLICATIF_V1)

Objectif : valider les 3 checks P0 (scope isolation, seed int/repro, preview = save) avec logs et script reproductibles.

## Commandes clés

### Logs backend (grep-friendly)
```
docker logs le-maitre-mot-backend --tail 200 | grep -E "PRESET_OVERRIDE|GEN_PARAMS"
```
Attendu (exemples de format) :
- `[GEN_PARAMS] generator_key=None chapter=6e_G07 ui_params=... effective_params=pending seed=None difficulty=moyen is_dynamic_context=False`
- `[PRESET_OVERRIDE] generator_key=CALCUL_NOMBRES_V1 seed_before=None seed_after=123456 diff_before=facile diff_after=facile applied=true`
- Non-premium : `[PRESET_OVERRIDE] generator_key=THALES_V2 applied=false`

### Script de diagnostic Mongo (python3)
```
python3 scripts/p0_preset_checks.py
```
Alternative sans python local (si docker):
```
docker run --rm -e MONGO_URL=$MONGO_URL -e MONGO_DB_NAME=$MONGO_DB_NAME -e MONGO_COLLECTION=admin_exercises -v $PWD/scripts:/scripts python:3.11-slim python /scripts/p0_preset_checks.py
```
Attendu (format) :
```
=== P0 PRESET CHECKS REPORT ===
{'CHECK2_SEED_INT': 'PASS', 'CHECK3_DIFF_SYNC': 'PASS', 'generator_key': 'CALCUL_NOMBRES_V1', 'id': 12, 'seed': 123456, 'seed_type': 'int', 'difficulty_doc': 'standard', 'difficulty_vars': 'standard'}
{'CHECK2_SEED_INT': 'PASS', 'CHECK3_DIFF_SYNC': 'PASS', 'generator_key': 'RAISONNEMENT_MULTIPLICATIF_V1', 'id': 7, 'seed': 7890, 'seed_type': 'int', 'difficulty_doc': 'standard', 'difficulty_vars': 'standard'}
{'generator_key': 'THALES_V2', 'id': 30, 'note': 'non-premium dynamic sample', 'difficulty_doc': 'moyen', 'difficulty_vars': 'moyen'}
=== END REPORT ===
```

### Vérification manuelle mongosh
```
docker exec -it le-maitre-mot-mongo mongosh le_maitre_mot_db
db.admin_exercises.find({generator_key:"CALCUL_NOMBRES_V1"}).sort({id:-1}).limit(1)
db.admin_exercises.find({generator_key:"RAISONNEMENT_MULTIPLICATIF_V1"}).sort({id:-1}).limit(1)
db.admin_exercises.find({generator_key:{$nin:["CALCUL_NOMBRES_V1","RAISONNEMENT_MULTIPLICATIF_V1"]}, is_dynamic:true}).sort({id:-1}).limit(1)
```
Attendu :
- `variables.seed` est un NumberInt/NumberLong (pas string).
- `difficulty` == `variables.difficulty` pour les premium.
- Vous pouvez vérifier le type en mongosh : `typeof doc.variables.seed`

### Créer un exercice RAISONNEMENT_MULTIPLICATIF_V1 si absent
Si aucun exercice premium RAISONNEMENT_MULTIPLICATIF_V1 n'est présent, créer un exo dynamique minimal via l’API admin (adapter le chapitre si besoin, ex: 6E_SP01). Exigences : is_dynamic=true, generator_key="RAISONNEMENT_MULTIPLICATIF_V1", offer="free", difficulty="facile", variables contenant seed/int + exercise_type + grade + difficulty + preset.
```
curl -X POST "$BACKEND_URL/api/admin/chapters/6E_SP01/exercises" \
  -H "Content-Type: application/json" \
  -d '{
    "is_dynamic": true,
    "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
    "difficulty": "facile",
    "offer": "free",
    "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
    "solution_template_html": "<h4>{{methode}}</h4><div>{{solution}}</div><div>{{calculs_intermediaires}}</div><div>{{reponse_finale}}</div>",
    "variables": {
      "preset": "default",
      "difficulty": "facile",
      "exercise_type": "raisonnement_multiplicatif",
      "grade": "6e",
      "seed": 123456
    },
    "template_variants": []
  }'
```
Ensuite relancer le script ou les requêtes mongosh ci-dessus pour vérifier la création :
```
db.admin_exercises.find({generator_key:"RAISONNEMENT_MULTIPLICATIF_V1"}).sort({id:-1}).limit(1)
typeof db.admin_exercises.findOne({generator_key:"RAISONNEMENT_MULTIPLICATIF_V1"}).variables.seed
```

### Migration DB des presets "default" → "simple"
Pour corriger les documents existants qui ont preset null/""/"default" sur les générateurs premium :
```
db.admin_exercises.updateMany(
  {
    generator_key: { $in: ["CALCUL_NOMBRES_V1", "RAISONNEMENT_MULTIPLICATIF_V1"] },
    $or: [
      { "variables.preset": { $in: [null, "", "default"] } },
      { "variables.preset": { $exists: false } }
    ]
  },
  { $set: { "variables.preset": "simple" } }
)
```
Vérifier ensuite :
```
db.admin_exercises.find(
  { generator_key: { $in: ["CALCUL_NOMBRES_V1", "RAISONNEMENT_MULTIPLICATIF_V1"] } },
  { "variables.preset": 1, generator_key: 1, id: 1 }
).sort({id:-1}).limit(3).pretty()
```

## Interprétation GO / NO-GO
- GO si : tous les logs `PRESET_OVERRIDE applied=true` montrent seed_after int + diff_after cohérente, script affiche PASS, et non-premium montre `applied=false`.
- NO-GO si : seed manquant ou non-int, mismatch difficulty_doc vs variables.difficulty, absence de logs `applied=true` lors d’une sauvegarde premium, ou `applied=false` absent pour un non-premium dynamique.
