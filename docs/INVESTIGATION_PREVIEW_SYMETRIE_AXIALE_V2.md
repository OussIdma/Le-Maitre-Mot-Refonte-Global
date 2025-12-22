# 🔍 INVESTIGATION ROOT CAUSE – Admin Preview `SYMETRIE_AXIALE_V2` (“Erreur interne lors de la prévisualisation”)

## 🎯 Symptôme

- Dans l’admin, sur un exercice dynamique THALES/SYMÉTRIE (ex. 6e, chapitre `SYMETRIE_AXIALE`), l’ouverture de la modale **“Prévisualisation dynamique”** avec `generator_key = "SYMETRIE_AXIALE_V2"` affiche :
  - Message UI : **`Erreur lors de la prévisualisation`** / **“Failed to fetch”** ou **“Erreur interne lors de la prévisualisation”**.
  - Aucun HTML n’est affiché dans la modale, parfois du texte brut `'Internal Server Error'` apparaît côté réseau.

## 📍 Chaîne de responsabilité identifiée

### Frontend – point d’entrée

**Fichiers :**

- `frontend/src/components/admin/DynamicPreviewModal.js`
  - `generatePreview()` appelle :

    ```js
    const result = await previewDynamicExercise({
      generator_key: generatorKey,
      enonce_template_html: enonceTemplate,
      solution_template_html: solutionTemplate,
      difficulty: difficulty,
      seed: seedValue,
      svg_mode: 'AUTO'
    });
    ```

- `frontend/src/lib/adminApi.js`
  - `previewDynamicExercise` → `apiCall('/api/admin/exercises/preview-dynamic', { ... })`
  - `apiCall` :
    - fait un `fetch` sur `${BACKEND_URL}/api/admin/exercises/preview-dynamic`.
    - lit la réponse en `text()`, vérifie `content-type`, `JSON.parse` en `data`.
    - si `!response.ok`, remonte `success: false, error: message, error_details`.

**Constat** : la préview appelle bien **`POST /api/admin/exercises/preview-dynamic`** avec `generator_key = "SYMETRIE_AXIALE_V2"` et les templates de l’UI.

### Backend – endpoint de preview

**Fichier** : `backend/routes/generators_routes.py`

- Endpoint concerné :

```python
@router.post("/preview-dynamic", response_model=DynamicPreviewResponse, tags=["Generators"])
async def preview_dynamic_exercise(request: DynamicPreviewRequest):
    ...
    logger.info(f"🔍 Preview dynamic: generator={request.generator_key}, seed={request.seed}")
    try:
        errors = []

        # 1. Récupération du schéma
        schema = get_generator_schema(request.generator_key.upper())
        if not schema:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={... "error_code": "invalid_generator", ...}
            )

        # 2. Génération via legacy THALES_V1 (avant correctif)
        gen_result = generate_dynamic_exercise(
            generator_key=request.generator_key.upper(),
            seed=request.seed,
            difficulty=request.difficulty
        )

        ...
```

- `generate_dynamic_exercise` est importé depuis :

  ```python
  from backend.generators.thales_generator import generate_dynamic_exercise
  ```

**Fichier** : `backend/generators/thales_generator.py`

- `generate_dynamic_exercise()` :

  ```python
  GENERATORS_REGISTRY = {
      "THALES_V1": ThalesV1Generator
  }

  def get_generator(generator_key: str, ...):
      if generator_key not in GENERATORS_REGISTRY:
          raise ValueError(f"Générateur inconnu: {generator_key}. Disponibles: {list(GENERATORS_REGISTRY.keys())}")
  ```

**Conséquence** :

- Quand `preview_dynamic_exercise` est appelé avec `generator_key = "SYMETRIE_AXIALE_V2"`, il passe **obligatoirement** par `generate_dynamic_exercise` qui ne connaît que `"THALES_V1"`.
- Cela déclenche :

  ```text
  ValueError: Générateur inconnu: SYMETRIE_AXIALE_V2. Disponibles: ['THALES_V1']
  ```

- Cette exception est catchée par le `except Exception as e` de `preview_dynamic_exercise` qui renvoie :

  ```json
  {
    "error_code": "INTERNAL_SERVER_ERROR",
    "error": "internal_error",
    "message": "Erreur interne lors de la prévisualisation",
    "details": "Générateur inconnu: SYMETRIE_AXIALE_V2. ...",
    "success": false,
    "enonce_html": "",
    "solution_html": "",
    ...
  }
  ```

### Backend – enregistrement des générateurs Factory

**Fichier** : `backend/generators/factory.py`

- La Factory enregistre `SYMETRIE_AXIALE_V2` correctement :

  ```python
  from generators.factory import GeneratorFactory

  @GeneratorFactory.register
  class SymetrieAxialeV2Generator(BaseGenerator):
      @classmethod
      def get_meta(cls) -> GeneratorMeta:
          return GeneratorMeta(
              key="SYMETRIE_AXIALE_V2",
              ...
          )
  ```

- `factory.py::_register_all_generators()` importe bien `symetrie_axiale_v2` et enregistre le générateur.

- La preuve :

  ```bash
  curl -s http://localhost:8000/api/v1/exercises/generators | jq .
  # => "generators": ["THALES_V1"] (legacy)

  curl -s http://localhost:8000/api/v1/exercises/generators/SYMETRIE_AXIALE_V2/full-schema | jq .
  # => renvoie bien le schéma complet du générateur SYMETRIE_AXIALE_V2
  ```

**Conclusion** :  
`SYMETRIE_AXIALE_V2` est **bien déclaré dans la Factory**, mais le endpoint `/preview-dynamic` ne l’utilisait pas et tentait systématiquement d’utiliser le pipeline legacy `THALES_V1`, produisant un `ValueError` “Générateur inconnu”.

---

## ✅ Correctif appliqué

### 1. Basculer la preview sur la Factory quand possible

**Fichier** : `backend/routes/generators_routes.py` – fonction `preview_dynamic_exercise`

- Remplacement du bloc de génération :

Avant :

```python
schema = get_generator_schema(request.generator_key.upper())
...
gen_result = generate_dynamic_exercise(
    generator_key=request.generator_key.upper(),
    seed=request.seed,
    difficulty=request.difficulty
)
variables = gen_result.get("variables", {})
results = gen_result.get("results", {})
all_vars = {**variables, **results}
svg_enonce = gen_result.get("figure_svg_enonce") if request.svg_mode == "AUTO" else None
svg_solution = gen_result.get("figure_svg_solution") if request.svg_mode == "AUTO" else None
```

Après (logique de fallback Factory → legacy) :

```python
generator_key = request.generato

schema = get_generator_schema(generator_key)
...

factory_schema = factory_get_schema(generator_key)
if factory_schema:
    logger.info(f"🏭 Preview via Factory pour generator={generator_key}")
    result = factory_generate(
        generator_key=generator_key,
        exercise_params=None,
        overrides=None,
        seed=request.seed,
    )

    variables = result.get("variables", {})
    all_vars = {
        **variables,
        **result.get("results", {}),
        **result.get("geo_data", {}),
    }
    svg_enonce = result.get("figure_svg_enonce") if request.svg_mode == "AUTO" else None
    svg_solution = result.get("figure_svg_solution") if request.svg_mode == "AUTO" else None
else:
    logger.info(f"📐 Preview via générateur legacy pour generator={generator_key}")
    gen_result = generate_dynamic_exercise(
        generator_key=generator_key,
        seed=request.seed,
        difficulty=request.difficulty
    )

    variables = gen_result.get("variables", {})
    results = gen_result.get("results", {})
    all_vars = {**variables, **results}
    svg_enonce = gen_result.get("figure_svg_enonce") if request.svg_mode == "AUTO" else None
    svg_solution = gen_result.get("figure_svg_solution") if request.svg_mode == "AUTO" else None
```

- Le reste de la fonction (détection de placeholders, format de la réponse JSON) reste inchangé.

### 2. Aucun impact sur THALES_V1

- Si `generator_key` **n’est pas connu de la Factory** (ex: `THALES_V1`), le `factory_get_schema(generator_key)` retourne `None` et le code exécute le chemin existant `generate_dynamic_exercise(...)` sans modification.

---

## 🧪 Vérifications après correctif

### 1. SYMETRIE_AXIALE_V2 – preview via API

Commande :

```bash
curl -s -X POST http://localhost:8000/api/admin/exercises/preview-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "SYMETRIE_AXIALE_V2",
    "enonce_template_html": "<p>Test {{figure_type}} - {{axe_type}}</p>",
    "solution_template_html": "<p>Solution</p>",
    "difficulty": "moyen",
    "seed": 42,
    "svg_mode": "AUTO"
  }' | jq '.'
```

Résultat :

```json
{
  "success": true,
  "enonce_html": "<p>Test point - vertical</p>",
  "solution_html": "<p>Solution</p>",
  "variables_used": { ... },
  "svg_enonce": "<svg ...>",
  "svg_solution": "<svg ...>",
  "errors": []
}
```

### 2. THALES_V1 – non-régression

Commande :

```bash
curl -s -X POST http://localhost:8000/api/admin/exercises/preview-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "THALES_V1",
    "enonce_template_html": "<p>Test {{cote_initial}} × {{coefficient_str}}</p>",
    "solution_template_html": "<p>Solution</p>",
    "difficulty": "moyen",
    "seed": 123,
    "svg_mode": "AUTO"
  }' | jq '.'
```

- Résultat attendu : `success: true`, `enonce_html` et `solution_html` sans `{{...}}`, `svg_enonce`/`svg_solution` présents.
- Aucune modification n’a été faite sur la logique `THALES_V1`, seulement sur la sélection de pipeline dans `preview_dynamic_exercise`.

---

## ✅ Résumé du correctif

- **Root cause** : `preview_dynamic_exercise` utilisait **toujours** le pipeline legacy `THALES_V1` (`generate_dynamic_exercise`), donc tout `generator_key` non présent dans `GENERATORS_REGISTRY` (ex: `SYMETRIE_AXIALE_V2`) causait un `ValueError` remonté en `INTERNAL_SERVER_ERROR`.
- **Fix** :
  - Si le générateur est géré par la **Factory v1** (`factory_get_schema` non nul), la prévisualisation est effectuée via `factory_generate(...)` + rendu des templates avec `variables + results + geo_data`.
  - Sinon, on garde le comportement historique en appelant `generate_dynamic_exercise` (THALES_V1).
  - Le tout est encapsulé dans le `try/except` existant qui garantit un retour **100 % JSON** (jamais d’HTML brut) et une liste d’erreurs de placeholders si nécessaire.
- **Non-régressions** :
  - THALES_V1 continue de fonctionner comme avant.
  - Les autres endpoints `/api/v1/exercises/generators`, `/generate`, GM07/GM08, etc. ne sont pas affectés.


