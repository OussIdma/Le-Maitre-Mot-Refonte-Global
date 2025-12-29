# P0: Error Codes 422 Standardisés

**Date** : 2025-12-26  
**Objectif** : Standardiser tous les HTTPException(422) avec format `{error_code, message, hint, context}`

---

## Format Standard

```python
{
  "error_code": "ERROR_CODE_NAME",
  "message": "Message lisible pour l'utilisateur",
  "hint": "Action concrète à faire (ex: 'Créez un exercice dynamique pour ce chapitre')",
  "context": {
    "code_officiel": "...",
    "chapter_code": "...",
    "pipeline_mode": "...",
    "offer_input": "...",
    "difficulty_input": "...",
    "total_exercises": 0,
    "dynamic_count": 0,
    "static_count": 0,
    "enabled_generators_count": 0,
    "enabled_generators_sample": [],
    "generator_key_selected": "...",
    "preset": "...",
    "seed": 123
  },
  "error": "error_legacy"  // Si déjà utilisé par le front
}
```

---

## Liste des Error Codes

### 1. CODE_OFFICIEL_INVALID
**Cause** : Le code_officiel n'existe pas dans le référentiel (ni DB ni JSON legacy)  
**Hint** : "Utilisez un code au format 6e_N01, 6e_G01, etc. Vérifiez la casse (6e_G07 vs 6E_G07)."  
**Context requis** : `code_officiel`, `chapter_code`, `chapter_from_db_exists: false`

---

### 2. TEST_CHAPTER_FORBIDDEN
**Cause** : Chapitre de test demandé en mode public (SHOW_TEST_CHAPTERS=false)  
**Hint** : "Les chapitres de test sont réservés au développement. Activez SHOW_TEST_CHAPTERS=true pour y accéder."  
**Context requis** : `code_officiel`, `is_test_chapter: true`

---

### 3. TEST_CHAPTER_UNKNOWN
**Cause** : Pattern de chapitre de test détecté mais non configuré  
**Hint** : "Chapitres de test connus: [...]. Ajoutez 'XXX' à la liste TEST_CHAPTER_CODES dans exercises_routes.py"  
**Context requis** : `code_officiel`, `normalized_code`, `known_test_chapters`

---

### 4. TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES
**Cause** : Pipeline TEMPLATE configuré mais aucun exercice dynamique trouvé  
**Hint** : "Créez au moins un exercice dynamique pour ce chapitre ou changez le pipeline à 'SPEC' ou 'MIXED'."  
**Context requis** : `code_officiel`, `pipeline_mode: "TEMPLATE"`, `total_exercises`, `dynamic_count: 0`, `enabled_generators_count`, `enabled_generators_sample`

---

### 5. MIXED_PIPELINE_NO_EXERCISES_OR_TYPES
**Cause** : Pipeline MIXED mais aucun exercice (dynamique ou statique) trouvé  
**Hint** : "Créez des exercices (dynamiques ou statiques) pour ce chapitre ou configurez exercise_types pour la génération SPEC."  
**Context requis** : `code_officiel`, `pipeline_mode: "MIXED"`, `total_exercises: 0`, `dynamic_count: 0`, `static_count: 0`

---

### 6. NO_EXERCISE_AVAILABLE
**Cause** : Pipeline SPEC mais aucun exercice statique trouvé  
**Hint** : "Ajoutez un exercice statique ou définissez exercise_types pour la génération SPEC."  
**Context requis** : `code_officiel`, `pipeline_mode: "SPEC"`, `static_count: 0`, `offer_input`, `difficulty_input`

---

### 7. SPEC_PIPELINE_INVALID_EXERCISE_TYPES
**Cause** : Pipeline SPEC mais exercise_types invalides ou manquants  
**Hint** : "Configurez des exercise_types valides pour ce chapitre dans l'admin."  
**Context requis** : `code_officiel`, `pipeline_mode: "SPEC"`, `exercise_types` (si disponible)

---

### 8. POOL_EMPTY
**Cause** : Aucun exercice dynamique disponible après filtrage (offer/difficulty/generator)  
**Hint** : "Vérifiez les filtres offer/difficulty ou créez des exercices dynamiques pour ces critères."  
**Context requis** : `code_officiel`, `offer_input`, `difficulty_input`, `offer_effective_query`, `difficulty_effective_query`, `enabled_generators_count`, `dynamic_count: 0`

---

### 9. GENERATOR_NOT_ENABLED
**Cause** : Générateur sélectionné non activé pour ce chapitre  
**Hint** : "Activez ce générateur dans l'admin (section 'Générateurs activés') ou utilisez un autre générateur."  
**Context requis** : `code_officiel`, `generator_key_selected`, `enabled_generators_sample`

---

### 10. ADMIN_TEMPLATE_MISMATCH
**Cause** : Templates contiennent des placeholders non résolvables par le générateur  
**Hint** : "Vérifiez que les placeholders dans les templates correspondent aux variables du générateur."  
**Context requis** : `generator_key_selected`, `template_placeholders` (si disponible)

---

### 11. NO_TESTS_DYN_EXERCISE_FOUND
**Cause** : Aucun exercice dynamique trouvé pour endpoint tests_dyn  
**Hint** : "Utilisez /generate/batch/tests_dyn pour les lots"  
**Context requis** : `offer_input`, `difficulty_input`

---

### 12. NIVEAU_INVALID
**Cause** : Niveau invalide (legacy)  
**Hint** : "Utilisez un niveau valide: 6e, 5e, 4e, 3e"  
**Context requis** : `niveau` (si legacy)

---

### 13. CHAPITRE_INVALID
**Cause** : Chapitre invalide pour le niveau (legacy)  
**Hint** : "Vérifiez que le chapitre existe pour ce niveau"  
**Context requis** : `niveau`, `chapitre`

---

### 14. CHAPTER_OR_TYPE_INVALID
**Cause** : Chapitre ou type d'exercice non mappé dans MathGenerationService  
**Hint** : "Ajoutez le chapitre dans MathGenerationService._get_exercise_types_for_chapter ou configurez un pipeline dynamique/statique"  
**Context requis** : `code_officiel`, `exercise_type` (si disponible)

---

## Logs Obligatoires

### [DIAG_FLOW]
- **Entrée** : Au début de `/generate`
- **Après filtrage** : Après filtrage dynamique/statique

### [DIAG_422]
- **Avant chaque raise 422** : Avec error_code, code_officiel, pipeline, comptages

---

## Tests

Voir `backend/tests/test_diag_422.py` pour tests de validation.





