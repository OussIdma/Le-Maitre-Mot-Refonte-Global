# ✅ Templates HTML Premium - Validation P0

## Objectif
Ajouter les templates HTML manquants pour les générateurs premium dans le frontend.

## Modification effectuée

**Fichier modifié :** `frontend/src/components/admin/ChapterExercisesAdminPage.js`

### Templates ajoutés dans `getDynamicTemplates(generatorKey)`

#### 1. RAISONNEMENT_MULTIPLICATIF_V1 (lignes 527-546)

**Variables supportées :**
- `{{consigne}}` - Consigne de l'exercice
- `{{enonce}}` - Énoncé détaillé avec tableaux/contexte
- `{{methode}}` - Nom de la méthode (coefficient_de_proportionnalite, regle_de_trois_pourcentage, formule_vitesse, calcul_echelle)
- `{{calculs_intermediaires}}` - Étapes de calcul détaillées (format texte multiligne)
- `{{solution}}` - Explication textuelle de la solution
- `{{reponse_finale}}` - Réponse finale formatée

**Style visuel :**
```
- Titre "Méthode" en bleu (#2563eb)
- Zone calculs : fond gris clair (#f1f5f9), padding 1rem
- Réponse finale : fond vert clair (#dcfce7), bordure gauche verte (#22c55e)
- white-space: pre-line pour conserver les sauts de ligne
```

**Types d'exercices couverts :**
- Proportionnalité (tableaux)
- Pourcentages
- Vitesse (distance, temps)
- Échelle (cartes)

#### 2. CALCUL_NOMBRES_V1 (lignes 547-566)

**Variables supportées :**
- `{{consigne}}` - Consigne de l'exercice
- `{{enonce}}` - Expression mathématique à calculer
- `{{calculs_intermediaires}}` - Étapes de résolution
- `{{solution}}` - Explication textuelle
- `{{reponse_finale}}` - Résultat final

**Style visuel :**
```
- Titre "Correction" en bleu (#2563eb)
- Zone calculs : même style que RAISONNEMENT_MULTIPLICATIF_V1
- Réponse finale : même style (fond vert avec bordure)
- Énoncé en taille 1.125rem pour meilleure lisibilité
```

**Types d'exercices couverts :**
- Opérations simples (+, -, ×, ÷)
- Priorités opératoires (avec/sans parenthèses)
- Décimaux (comparaison, calculs, arrondis)

---

## État de l'intégration

| Composant | État | Notes |
|-----------|------|-------|
| **Frontend - Templates HTML** | ✅ Ajouté | Lignes 527-566 de ChapterExercisesAdminPage.js |
| **Frontend - Build** | ✅ OK | `docker compose up -d --build frontend` réussi |
| **Frontend - Linting** | ✅ OK | Aucune erreur de syntaxe |
| **Backend - Générateurs** | ✅ Existant | raisonnement_multiplicatif_v1.py et calcul_nombres_v1.py |
| **Backend - Factory** | ✅ Enregistré | @GeneratorFactory.register présent |
| **Backend - Curriculum** | ✅ Mappé | Chapitres 6e_SP01, 6e_SP03, 6e_N04, 6e_N05, 6e_N06 |
| **Backend - Dispatch premium** | ❌ À faire | exercises_routes.py nécessite modifications A, B, C |
| **Backend - RNG Helpers** | ❌ À corriger | Erreur `'>=' not supported between 'Random' and 'int'` |

---

## Validation manuelle

### ✅ Ce qui fonctionne maintenant

1. **Interface Admin** : Les templates apparaissent dans le dropdown des générateurs
   ```
   http://localhost:3000/admin/chapters/6e_SP01
   → Créer exercice → Sélectionner RAISONNEMENT_MULTIPLICATIF_V1
   → Templates pré-remplis
   ```

2. **Preview dynamique** : La modal de preview peut afficher les templates (si générateur accessible)

3. **Structure HTML cohérente** : Format uniforme avec SIMPLIFICATION_FRACTIONS_V2

### ❌ Ce qui ne fonctionne pas encore

1. **Génération via API** : 
   ```bash
   curl -X POST http://localhost:8000/api/v1/exercises/generate \
     -d '{"code_officiel": "6e_SP03", "offer": "pro", "seed": 42}'
   # Retourne toujours exercice legacy (6e_PROP_ACHAT) au lieu de RAISONNEMENT_MULTIPLICATIF_V1
   ```
   **Cause** : Dispatch premium dans `exercises_routes.py` hardcodé sur `DUREES_PREMIUM` uniquement

2. **Erreur RNG dans générateurs** :
   ```python
   # Dans raisonnement_multiplicatif_v1.py ligne 261
   coeff = safe_randrange(self._rng, 2, 6)  # ❌ ERREUR
   # TypeError: '>=' not supported between 'Random' and 'int'
   ```
   **Cause** : `safe_randrange` attend `start:int` pas `Random` en 1er argument

---

## Prochaines étapes (par ordre de priorité)

### P0.1 - Corriger les générateurs (urgent)

**Fichiers à modifier :**
- `backend/generators/raisonnement_multiplicatif_v1.py`
- `backend/generators/calcul_nombres_v1.py`

**Action :** Remplacer toutes les occurrences :
```python
# ❌ AVANT
coeff = safe_randrange(self._rng, 2, 6)
type_exo = safe_random_choice(self._rng, ["a", "b"])

# ✅ APRÈS
coeff = self._rng.randrange(2, 6)
type_exo = self._rng.choice(["a", "b"])
```

Voir le prompt détaillé que j'ai fourni précédemment pour les modifications complètes (A, B, C, D).

### P0.2 - Dispatch premium générique

**Fichier à modifier :**
- `backend/routes/exercises_routes.py` (lignes 1598-1629)

**Action :** Remplacer le bloc `PREMIUM CHECK` hardcodé par un dispatch générique utilisant `GeneratorFactory`.

### P0.3 - Ajouter helpers RNG dans BaseGenerator

**Fichier à modifier :**
- `backend/generators/base_generator.py`

**Action :** Ajouter méthodes `rng_choice()`, `rng_randrange()`, `rng_randint()`.

---

## Commandes de validation finale

```bash
# 1. Vérifier que frontend est à jour
docker compose ps
# → frontend doit être "Up X seconds"

# 2. Tester preview dans admin (visuel)
open http://localhost:3000/admin/chapters/6e_SP01

# 3. Après corrections backend, tester API
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_SP03",
    "difficulte": "moyen",
    "offer": "pro",
    "seed": 42
  }' | jq '.metadata.generator_code, .metadata.is_premium'

# Attendu après corrections :
# "RAISONNEMENT_MULTIPLICATIF_V1"
# true
```

---

## Checklist frontend (✅ Complété)

- [x] Templates HTML définis pour RAISONNEMENT_MULTIPLICATIF_V1
- [x] Templates HTML définis pour CALCUL_NOMBRES_V1
- [x] Variables correctement mappées (consigne, enonce, methode, calculs_intermediaires, solution, reponse_finale)
- [x] Style cohérent avec SIMPLIFICATION_FRACTIONS_V2
- [x] Aucune erreur de linting
- [x] Frontend rebuilder avec succès
- [x] Pas de modification de SIMPLIFICATION_FRACTIONS_V2
- [x] Pas de modification backend (comme demandé)

---

**Date :** 2025-12-22  
**Statut :** ✅ Templates frontend ajoutés - Backend corrections requises pour test complet

