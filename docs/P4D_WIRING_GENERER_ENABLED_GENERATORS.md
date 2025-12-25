# P4.D — Brancher /generer sur enabled_generators (DB)

## Contexte

### Problème identifié

L'admin permet d'activer des générateurs par chapitre via `enabled_generators` (MongoDB), mais côté PROF (`/generer`), seuls les exercices statiques sont visibles. Le moteur PROF n'utilisait pas la bonne source de vérité :

- **Avant P4.D** : Lecture depuis `curriculum.loader` (fichier JSON) et `exercise_types` (legacy)
- **Après P4.D** : Lecture depuis MongoDB `curriculum_chapters.enabled_generators` (source de vérité unique)

### Impact

- Les générateurs activés en admin ne sont pas visibles côté PROF
- Le moteur PROF ignore `enabled_generators` et utilise encore des mappings legacy
- Pas de visibilité claire sur "pourquoi je ne vois pas de générateur"

## Solution implémentée

### 1. Source de vérité unique : MongoDB

**Fichier** : `backend/routes/exercises_routes.py`

**Changements** :
- Remplacement de `get_chapter_by_official_code()` (JSON) par `CurriculumPersistenceService.get_chapter_by_code()` (MongoDB)
- Lecture de `enabled_generators` depuis le chapitre en DB
- Fallback legacy si chapitre non trouvé en DB (pour compatibilité)

**Code** :
```python
# P4.D - Charger le chapitre depuis MongoDB (source de vérité unique)
chapter_from_db = await curriculum_service_db.get_chapter_by_code(request.code_officiel)
enabled_generators_list = chapter_from_db.get("enabled_generators", []) if chapter_from_db else []
```

### 2. Filtrage des générateurs selon enabled_generators

**Fichier** : `backend/routes/exercises_routes.py`

**Changements** :
- Filtrage des générateurs premium selon `enabled_generators` (au lieu de `exercise_types`)
- Filtrage des exercices dynamiques selon `enabled_generators` dans les pipelines TEMPLATE et MIXED
- Logs `[PROF_GENERATORS]` pour traçabilité

**Code** :
```python
# P4.D - Utiliser enabled_generators depuis la DB (source de vérité unique)
if chapter_from_db and enabled_generators_list:
    enabled_keys = [
        eg.get("generator_key") 
        for eg in enabled_generators_list 
        if eg.get("is_enabled") is True
    ]
    factory_generator_keys = [
        gen_key for gen_key in enabled_keys 
        if gen_key.upper() in available_factory_generators
    ]
```

### 3. Guardrail : vérification que le générateur est activé

**Fichier** : `backend/routes/exercises_routes.py`

**Changements** :
- Vérification que le `generator_key` sélectionné est dans `enabled_generators`
- Erreur 403 explicite si générateur non activé
- Réessai avec un générateur activé si possible

**Code** :
```python
# P4.D - Guardrail : vérifier que le générateur sélectionné est activé
if enabled_generators_for_chapter and selected_generator_key:
    if selected_generator_key.upper() not in [eg.upper() for eg in enabled_generators_for_chapter]:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "GENERATOR_NOT_ENABLED",
                "message": f"Le générateur '{selected_generator_key}' n'est pas activé pour le chapitre...",
                "hint": "Activez ce générateur dans l'admin..."
            }
        )
```

### 4. Endpoint debug DEV-only

**Fichier** : `backend/routes/debug_routes.py`

**Endpoint** : `GET /api/debug/chapters/{code}/generators`

**Protection** : Accessible uniquement si `ENVIRONMENT != production` ou `DEBUG=true`

**Réponse** :
```json
{
  "chapter_code": "6e_G07",
  "enabled_generators_in_db": ["CALCUL_NOMBRES_V1"],
  "factory_list_all_count": 6,
  "active_generators_resolved": [
    {
      "key": "CALCUL_NOMBRES_V1",
      "label": "Calculs numériques",
      "version": "1.0.0",
      "supported_difficulties": ["facile", "moyen", "difficile"],
      "premium": false,
      "exercise_type": "CALCUL_NOMBRES"
    }
  ],
  "warnings": [
    "enabled_generators empty -> prof sees static only"
  ],
  "chapter_found_in_db": true,
  "pipeline": "MIXED"
}
```

### 5. Messages d'erreur améliorés

**Changements** :
- Message clair si aucun générateur activé : "Aucun générateur activé pour ce chapitre. Activez au moins un générateur dans l'admin..."
- Message si générateurs activés mais aucun exercice : "Aucun exercice dynamique trouvé pour les générateurs activés: ..."
- Inclusion de `enabled_generators` dans le contexte des erreurs

## Logs et observabilité

### Tags de log

- `[CHAPTER_LOAD]` : Source du chapitre (db/json) et `enabled_generators`
- `[PROF_GENERATORS]` : Générateurs résolus et filtrés selon `enabled_generators`

### Exemples de logs

```
[CHAPTER_LOAD] source=db code=6e_G07 enabled_generators=['CALCUL_NOMBRES_V1']
[PROF_GENERATORS] chapter=6e_G07 enabled_in_db=['CALCUL_NOMBRES_V1'] resolved=['CALCUL_NOMBRES_V1']
[PROF_GENERATORS] Filtré 3 exercices dynamiques parmi 5 selon enabled_generators=['CALCUL_NOMBRES_V1']
```

## Tests manuels

### Test 1 — Visibilité

**Scénario** :
1. Activer `CALCUL_NOMBRES_V1` sur `6e_G07` en admin
2. Aller sur `/generer` avec `code_officiel=6e_G07`
3. Vérifier que "Calculs numériques" est visible dans les options générateurs / dynamique

**Résultat attendu** :
- ✅ Le générateur `CALCUL_NOMBRES_V1` est visible et utilisable
- ✅ Les exercices dynamiques avec ce générateur sont générés

### Test 2 — Guardrail

**Scénario** :
1. Désactiver `CALCUL_NOMBRES_V1` sur `6e_G07` en admin
2. Tenter de générer avec `code_officiel=6e_G07` et un exercice dynamique utilisant `CALCUL_NOMBRES_V1`

**Résultat attendu** :
- ✅ Erreur 403/422 explicite : "Le générateur 'CALCUL_NOMBRES_V1' n'est pas activé..."
- ✅ Message clair avec hint pour activer le générateur

### Test 3 — Debug

**Scénario** :
1. Appeler `GET /api/debug/chapters/6e_G07/generators` (en mode dev)
2. Vérifier la réponse

**Résultat attendu** :
- ✅ `enabled_generators_in_db` : Liste des générateurs activés
- ✅ `active_generators_resolved` : Infos complètes des générateurs résolus
- ✅ `warnings` : Avertissements (ex: "enabled_generators empty -> prof sees static only")

### Test 4 — Fallback conservé

**Scénario** :
1. Forcer une erreur DYNAMIC (ex: générateur désactivé)
2. Vérifier que le fallback STATIC continue de fonctionner

**Résultat attendu** :
- ✅ Si DYNAMIC échoue → fallback STATIC fonctionne
- ✅ Les exercices statiques restent disponibles même si aucun générateur n'est activé

## Migration

### Compatibilité

- **Fallback legacy** : Si chapitre non trouvé en DB, lecture depuis JSON (compatibilité)
- **Logs de migration** : Warnings si chapitre trouvé en JSON mais pas en DB

### Migration recommandée

1. S'assurer que tous les chapitres sont en MongoDB
2. Vérifier que `enabled_generators` est correctement rempli pour chaque chapitre
3. Utiliser l'endpoint debug pour diagnostiquer les problèmes

## Références

- **P4.B** : Gestion des générateurs activés (`docs/P4B_ENABLED_GENERATORS.md`)
- **Service** : `backend/services/curriculum_persistence_service.py`
- **Routes** : `backend/routes/exercises_routes.py`
- **Debug** : `backend/routes/debug_routes.py`

## Auteur

P4.D — Brancher /generer sur enabled_generators (DB)
Date : 2024

