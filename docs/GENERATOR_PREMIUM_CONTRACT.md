# CONTRAT GÉNÉRATEUR PREMIUM - SPÉCIFICATIONS OFFICIELLES

**Version**: 1.0.0  
**Date**: 23 décembre 2025  
**Statut**: 🔒 **OBLIGATOIRE** pour tous les générateurs premium

---

## 🎯 OBJECTIF

Ce document définit le **contrat obligatoire** que TOUT générateur premium doit respecter pour être accepté dans le système. Aucune exception n'est autorisée.

---

## 📜 RESPONSABILITÉS DU GÉNÉRATEUR

Un générateur premium DOIT:

1. **Hériter de `BaseGenerator`**
2. **Implémenter TOUTES les méthodes abstraites**
3. **Respecter le déterminisme** (seed fixe → résultat identique)
4. **Produire des variables complètes** (pas de placeholders non résolus)
5. **Sécuriser les sorties HTML** (pas d'injection)
6. **Être compatible admin** (templates HTML définis)
7. **Gérer les erreurs proprement** (HTTPException 422 structurée)
8. **Documenter ses capacités** (meta, schema, presets)

---

## 🔐 SECTION 1 : MÉTADONNÉES (GeneratorMeta)

### Variables OBLIGATOIRES

```python
@classmethod
def get_meta(cls) -> GeneratorMeta:
    return GeneratorMeta(
        key="NOM_GENERATEUR_V1",              # OBLIGATOIRE: Clé unique en MAJUSCULES
        label="Label court",                   # OBLIGATOIRE: Nom affiché (< 50 chars)
        description="Description complète",    # OBLIGATOIRE: Description (100-200 chars)
        version="1.0.0",                       # OBLIGATOIRE: Versionning sémantique
        niveaux=["6e", "5e"],                  # OBLIGATOIRE: Liste des niveaux compatibles
        exercise_type="TYPE_EXERCICE",         # OBLIGATOIRE: Type d'exercice
        svg_mode="NONE",                       # OBLIGATOIRE: "NONE", "SINGLE", "DOUBLE", "AUTO"
        supports_double_svg=False,             # OBLIGATOIRE: bool
        pedagogical_tips="...",                # OPTIONNEL: Conseils pédagogiques
        is_dynamic=True,                       # P1.2: OBLIGATOIRE (bool)
        supported_grades=["6e", "5e"],         # P1.2: OBLIGATOIRE (list)
        supported_chapters=["6e_XX", ...],     # P1.2: OPTIONNEL (list)
    )
```

### Règles de validation

- ✅ `key` doit être unique dans le système
- ✅ `key` doit finir par `_V1`, `_V2`, etc. (versioning)
- ✅ `niveaux` doit contenir au moins 1 niveau valide
- ✅ `exercise_type` doit être cohérent avec la clé
- ✅ `supported_grades` doit être identique ou compatible avec `niveaux`

---

## 📊 SECTION 2 : SCHÉMA DES PARAMÈTRES (ParamSchema)

### Paramètres OBLIGATOIRES

Tout générateur premium DOIT accepter au minimum:

```python
@classmethod
def get_schema(cls) -> List[ParamSchema]:
    return [
        ParamSchema(
            name="seed",
            type=ParamType.INT,
            description="Seed pour reproductibilité (obligatoire)",
            default=None,
            required=True  # ← OBLIGATOIRE
        ),
        ParamSchema(
            name="difficulty",
            type=ParamType.ENUM,
            description="Niveau de difficulté",
            default="moyen",
            options=["facile", "moyen", "difficile"],  # ← Au moins 2 options
            required=False
        ),
        ParamSchema(
            name="grade",
            type=ParamType.ENUM,
            description="Niveau scolaire",
            default="6e",
            options=["6e", "5e"],  # ← Cohérent avec meta.niveaux
            required=False
        ),
        # Autres paramètres spécifiques...
    ]
```

### Règles de validation

- ✅ `seed` DOIT être obligatoire (`required=True`)
- ✅ `difficulty` DOIT avoir au moins 2 niveaux
- ✅ `grade` DOIT être cohérent avec `meta.niveaux`
- ✅ Tous les paramètres DOIVENT avoir un `default` si `required=False`
- ✅ Les `ENUM` DOIVENT avoir une liste `options` non vide

---

## 🎲 SECTION 3 : GESTION DU RNG (Déterminisme)

### Règles STRICTES

1. **INTERDICTION d'utiliser `random.Random` directement**
   ```python
   # ❌ INTERDIT
   import random
   random.randint(1, 10)
   random.choice(['a', 'b'])
   ```

2. **UTILISER UNIQUEMENT les helpers de BaseGenerator**
   ```python
   # ✅ CORRECT
   self.rng_randint(1, 10)
   self.rng_choice(['a', 'b'])
   self.rng_randrange(1, 10)
   ```

3. **INTERDICTION de passer `self._rng` aux fonctions**
   ```python
   # ❌ INTERDIT
   safe_randrange(self._rng, 1, 10)  # TypeError !
   
   # ✅ CORRECT
   self.rng_randrange(1, 10)
   ```

4. **Le seed DOIT être utilisé pour TOUTES les variations**
   - Valeurs numériques
   - Choix d'énoncés/variantes
   - Sélection de méthodes
   - Génération d'erreurs (pour variant C)

### Test de déterminisme

Tout générateur DOIT passer ce test:

```python
def test_determinisme():
    gen1 = MonGenerateur(seed=42)
    gen2 = MonGenerateur(seed=42)
    
    result1 = gen1.generate({"seed": 42, ...})
    result2 = gen2.generate({"seed": 42, ...})
    
    assert result1["variables"]["enonce"] == result2["variables"]["enonce"]
    assert result1["variables"]["solution"] == result2["variables"]["solution"]
```

---

## 📝 SECTION 4 : VARIABLES DE SORTIE OBLIGATOIRES

### Variables MINIMALES (TOUJOURS présentes)

```python
return {
    "enonce": str,                    # OBLIGATOIRE: Texte pur (pas de HTML complexe)
    "consigne": str,                  # OBLIGATOIRE: Consigne courte
    "solution": str,                  # OBLIGATOIRE: Explication textuelle
    "calculs_intermediaires": str,    # OBLIGATOIRE: Étapes de calcul
    "reponse_finale": str,            # OBLIGATOIRE: Réponse finale (nombre ou texte)
    "niveau": str,                    # OBLIGATOIRE: "6e", "5e", etc.
    "type_exercice": str,             # OBLIGATOIRE: Type d'exercice
    "methode": str,                   # OPTIONNEL: Méthode utilisée
    "donnees": dict,                  # OPTIONNEL: Données brutes (pour debug)
    "tableau_html": str,              # P0.4: Si tableau, SÉPARER de enonce
}
```

### Règles de validation

- ✅ TOUTES les variables DOIVENT être non-None
- ✅ Les variables textuelles DOIVENT être non-vides (sauf `donnees`)
- ✅ `enonce` ne DOIT PAS contenir de HTML complexe (max `<br>`)
- ✅ Si tableau, utiliser `tableau_html` séparé (sécurité P0.4)
- ✅ `reponse_finale` DOIT être une chaîne (même pour les nombres)

---

## 🔒 SECTION 5 : SÉCURITÉ HTML

### Règles STRICTES

1. **`enonce` DOIT être du texte pur**
   ```python
   # ✅ CORRECT
   enonce = "Calcule 3 + 5<br><br>Donne le résultat."
   
   # ❌ INTERDIT
   enonce = "<div onclick='alert()'>Calcule</div>"
   enonce = f"{intro}<table>...</table>"  # Utiliser tableau_html !
   ```

2. **HTML structuré DOIT être dans des variables séparées**
   ```python
   # ✅ CORRECT
   return {
       "enonce": "Complète le tableau :",
       "tableau_html": "<table>...</table>"
   }
   ```

3. **Balises INTERDITES dans toutes les variables**
   - `<script>`
   - `<iframe>`
   - `<object>`
   - `<embed>`
   - `<style>` (inline OK)
   - Attributs `onclick`, `onerror`, etc.
   - `javascript:` dans les attributs

4. **Échappement automatique des données utilisateur**
   - Les templates utilisent `{{variable}}` (échappé)
   - Les templates utilisent `{{{variable}}}` UNIQUEMENT pour HTML contrôlé

### Test de sécurité

```python
def test_securite_html():
    result = generateur.generate({...})
    
    enonce = result["variables"]["enonce"]
    solution = result["variables"]["solution"]
    
    # Vérifier pas de balises dangereuses
    assert "<script" not in enonce.lower()
    assert "<iframe" not in enonce.lower()
    assert "javascript:" not in enonce.lower()
```

---

## 🎨 SECTION 6 : VARIÉTÉ DES ÉNONCÉS (P0.1)

### Règles de variabilité

1. **OBLIGATOIRE: Pool de formulations alternatives**
   ```python
   _ENONCE_VARIANTS = {
       "type_exercice_1": [
           "Calcule :",
           "Effectue le calcul suivant :",
           "Détermine le résultat de :",
       ],
   }
   
   _CONSIGNE_VARIANTS = {
       "type_exercice_1": [
           "Effectue le calcul et donne le résultat.",
           "Calcule et indique le résultat.",
       ],
   }
   ```

2. **Utiliser `self.rng_choice()` pour sélectionner**
   ```python
   intro = self.rng_choice(self._ENONCE_VARIANTS["type_exercice"])
   consigne = self.rng_choice(self._CONSIGNE_VARIANTS["type_exercice"])
   ```

3. **Minimum 3 variantes par type d'exercice**

### Test de variété

```python
def test_variete_enonces():
    enonces = set()
    for seed in range(100):
        result = generateur.generate({"seed": seed, ...})
        enonces.add(result["variables"]["enonce"])
    
    # Au moins 3 énoncés différents sur 100 seeds
    assert len(enonces) >= 3
```

---

## 🖼️ SECTION 7 : COMPATIBILITÉ ADMIN (Templates HTML)

### Responsabilité

Le générateur DOIT avoir un template HTML défini dans:
- `frontend/src/components/admin/ChapterExercisesAdminPage.js`
- Fonction `getDynamicTemplates(generatorKey)`

### Structure template MINIMALE

```javascript
if (generatorKey === 'MON_GENERATEUR_V1') {
  return {
    enonce: `<div class="exercise-enonce">
  <p><strong>{{consigne}}</strong></p>
  <p>{{enonce}}</p>
  {{{tableau_html}}}  <!-- Si applicable -->
</div>`,
    solution: `<div class="exercise-solution">
  <h4 style="color: #2563eb; margin-bottom: 1rem;">{{methode}}</h4>
  <div class="calculs" style="background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
    <pre style="white-space: pre-line; font-family: inherit; margin: 0;">{{calculs_intermediaires}}</pre>
  </div>
  <div class="solution-text" style="margin-bottom: 1rem;">
    <p>{{solution}}</p>
  </div>
  <div class="reponse-finale" style="background: #dcfce7; padding: 0.75rem; border-left: 4px solid #22c55e; border-radius: 0.25rem;">
    <p style="margin: 0;"><strong>Réponse finale :</strong> {{reponse_finale}}</p>
  </div>
</div>`
  };
}
```

### Règles de validation

- ✅ Template DOIT utiliser `{{variable}}` pour texte échappé
- ✅ Template DOIT utiliser `{{{variable}}}` UNIQUEMENT pour HTML contrôlé
- ✅ Toutes les variables du générateur DOIVENT être utilisées
- ✅ Pas de variables non définies dans le générateur

---

## ⚠️ SECTION 8 : GESTION DES ERREURS

### Erreurs structurées OBLIGATOIRES

Tout générateur DOIT lever des `HTTPException` avec structure standard:

```python
from fastapi import HTTPException

# ✅ CORRECT
raise HTTPException(
    status_code=422,
    detail={
        "error_code": "INVALID_DIFFICULTY",
        "error": "invalid_difficulty",
        "message": f"Difficulté invalide: {difficulty}",
        "hint": f"Difficultés valides: {', '.join(valid_difficulties)}",
        "context": {
            "difficulty": difficulty,
            "valid_difficulties": valid_difficulties
        }
    }
)
```

### Codes d'erreur standardisés

- `INVALID_EXERCISE_TYPE`: Type d'exercice non supporté
- `INVALID_GRADE`: Niveau scolaire non supporté
- `INVALID_DIFFICULTY`: Difficulté non supportée
- `GENERATION_FAILED`: Erreur pendant la génération
- `SEED_REQUIRED`: Seed manquant
- `PLACEHOLDER_UNRESOLVED`: Variable non résolue

---

## 🧪 SECTION 9 : TESTS OBLIGATOIRES

Tout générateur premium DOIT avoir ces tests:

### 1. Test de métadonnées
```python
def test_meta():
    meta = MonGenerateur.get_meta()
    assert meta.key == "MON_GENERATEUR_V1"
    assert len(meta.niveaux) > 0
    assert meta.is_dynamic is True
```

### 2. Test de schéma
```python
def test_schema():
    schema = MonGenerateur.get_schema()
    # Vérifier seed obligatoire
    seed_param = next((p for p in schema if p.name == "seed"), None)
    assert seed_param is not None
    assert seed_param.required is True
```

### 3. Test de génération basique
```python
def test_generate_basic():
    gen = MonGenerateur(seed=42)
    result = gen.generate({"seed": 42, ...})
    
    assert "variables" in result
    variables = result["variables"]
    
    # Variables obligatoires
    required = ["enonce", "consigne", "solution", "reponse_finale"]
    for var in required:
        assert var in variables
        assert variables[var] is not None
        assert variables[var] != ""
```

### 4. Test de déterminisme
```python
def test_determinisme():
    gen1 = MonGenerateur(seed=42)
    gen2 = MonGenerateur(seed=42)
    
    result1 = gen1.generate({"seed": 42, ...})
    result2 = gen2.generate({"seed": 42, ...})
    
    assert result1["variables"]["enonce"] == result2["variables"]["enonce"]
```

### 5. Test de sécurité HTML
```python
def test_securite_html():
    gen = MonGenerateur(seed=42)
    result = gen.generate({"seed": 42, ...})
    
    enonce = result["variables"]["enonce"]
    
    assert "<script" not in enonce.lower()
    assert "<table" not in enonce  # Doit être dans tableau_html si présent
```

### 6. Test de variété
```python
def test_variete():
    enonces = set()
    for seed in range(50):
        result = MonGenerateur(seed=seed).generate({"seed": seed, ...})
        enonces.add(result["variables"]["enonce"])
    
    assert len(enonces) >= 3  # Au moins 3 variantes
```

### 7. Test d'erreurs 422
```python
def test_erreur_422():
    gen = MonGenerateur(seed=42)
    
    with pytest.raises(HTTPException) as exc:
        gen.generate({"difficulty": "INVALID", ...})
    
    assert exc.value.status_code == 422
    assert "error_code" in exc.value.detail
```

---

## 📚 SECTION 10 : DOCUMENTATION OBLIGATOIRE

Tout générateur premium DOIT avoir:

### 1. Docstring complète

```python
class MonGenerateurV1(BaseGenerator):
    """
    Générateur premium pour [TYPE D'EXERCICES].
    
    Niveaux: 6e, 5e
    Types d'exercices: type1, type2, type3
    
    Caractéristiques:
    - Déterministe (seed obligatoire)
    - Variété d'énoncés (3+ variantes)
    - Sécurité HTML (P0.4)
    - Compatible admin
    
    Exemples:
        >>> gen = MonGenerateurV1(seed=42)
        >>> result = gen.generate({"difficulty": "moyen", "seed": 42})
        >>> print(result["variables"]["enonce"])
    """
```

### 2. Fichier de documentation

`docs/MON_GENERATEUR_V1.md` contenant:
- Objectifs pédagogiques
- Types d'exercices couverts
- Paramètres acceptés
- Exemples de sorties
- Chapitres recommandés

---

## ✅ CHECKLIST DE VALIDATION

Avant de merger un nouveau générateur premium, vérifier:

- [ ] Hérite de `BaseGenerator`
- [ ] `get_meta()` retourne `GeneratorMeta` complet
- [ ] `get_schema()` contient `seed` obligatoire
- [ ] `get_defaults()` implémenté
- [ ] `get_presets()` contient au moins 2 presets
- [ ] `generate()` retourne toutes les variables obligatoires
- [ ] Utilise UNIQUEMENT `self.rng_*()` pour le RNG
- [ ] Variables d'énoncé multiples (3+)
- [ ] `enonce` ne contient pas de HTML complexe
- [ ] Si tableau, utilise `tableau_html` séparé
- [ ] Erreurs 422 structurées avec `error_code`
- [ ] Tests complets (7 tests minimum)
- [ ] Template HTML dans admin
- [ ] Documentation créée
- [ ] Enregistré dans `factory.py`
- [ ] Mappé dans `curriculum_XX.json`

---

## 🚫 ANTI-PATTERNS (INTERDITS)

### ❌ Utiliser `random` directement
```python
import random
random.randint(1, 10)  # ❌ NON DÉTERMINISTE
```

### ❌ Passer `self._rng` aux fonctions
```python
safe_randrange(self._rng, 1, 10)  # ❌ TypeError
```

### ❌ HTML dans `enonce`
```python
enonce = f"<table>{tableau}</table>"  # ❌ Utiliser tableau_html
```

### ❌ Variables manquantes
```python
return {
    "enonce": "...",
    # ❌ Manque consigne, solution, etc.
}
```

### ❌ Erreurs non structurées
```python
raise ValueError("Erreur")  # ❌ Utiliser HTTPException 422
```

### ❌ Énoncés fixes
```python
enonce = "Calcule 3 + 5"  # ❌ Toujours pareil, pas de variété
```

---

## 📊 MÉTRIQUES DE QUALITÉ

Un générateur premium de qualité:

| Métrique | Cible | Excellent |
|----------|-------|-----------|
| Variables obligatoires | 8/8 | 8/8 |
| Variantes d'énoncés | ≥3 | ≥5 |
| Tests passants | 7/7 | 10+ |
| Temps génération | <100ms | <50ms |
| Déterminisme | 100% | 100% |
| Couverture chapitres | ≥2 | ≥5 |

---

## 🔄 VERSIONING

- **V1**: Première version stable
- **V2**: Refonte majeure (incompatibilité)
- **V1.1**: Ajout de features (compatible)

Lors d'une refonte, GARDER l'ancienne version jusqu'à migration complète.

---

## 📞 SUPPORT

En cas de doute sur le contrat:
1. Consulter les générateurs de référence:
   - `RAISONNEMENT_MULTIPLICATIF_V1`
   - `CALCUL_NOMBRES_V1`
2. Exécuter `test_generator_contract.py`
3. Consulter la documentation du projet

---

**Version du contrat**: 1.0.0  
**Dernière mise à jour**: 23 décembre 2025  
**Auteur**: Équipe Le Maître Mot

---

**RÈGLE D'OR**: En cas de doute, privilégier la SIMPLICITÉ et la SÉCURITÉ.




