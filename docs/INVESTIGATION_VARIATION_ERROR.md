# 🔍 INVESTIGATION ROOT CAUSE - "Erreur lors de la génération de la variation"

## Symptôme
**Côté élève** : Clic sur "Variation" → message générique "Erreur lors de la génération de la variation"
- Pas de crash frontend visible
- Réponse backend parfois en 422 ou None
- La variation ne génère aucun nouvel exercice
- Le bug peut apparaître même quand la génération initiale fonctionne

---

## 📍 CHAÎNE D'APPEL COMPLÈTE

### 1. **FRONTEND - Bouton Variation**

**Fichier** : `frontend/src/components/ExerciseGeneratorPage.js`
- **Ligne 442-572** : Fonction `generateVariation(index)`
- **Ligne 533** : Génération du seed : `const seed = Date.now() + Math.random() * 1000`
- **Ligne 537-538** : Récupération de l'exercice courant :
  ```javascript
  const currentExerciseForVariation = exercises[index];
  const isCurrentPremium = currentExerciseForVariation?.metadata?.is_premium === true;
  ```
- **Ligne 541-545** : Construction du payload :
  ```javascript
  const payload = {
    code_officiel: codeOfficiel,
    difficulte: difficulte,
    seed: seed
  };
  ```
- **Ligne 549-550** : **PROBLÈME POTENTIEL** - Si exercice courant est PREMIUM :
  ```javascript
  if (isCurrentPremium) {
    payload.offer = "pro";
  }
  ```
- **Ligne 552-556** : Si exercice n'est pas premium mais utilisateur est PRO :
  ```javascript
  else if (isPro) {
    // On NE MET PAS offer: "pro" pour garder la cohérence
  }
  ```
- **Ligne 558** : Appel API : `axios.post(`${API_V1}/generate`, payload)`
- **Ligne 566-568** : Gestion d'erreur générique :
  ```javascript
  catch (error) {
    console.error("Erreur lors de la génération de variation:", error);
    setError("Erreur lors de la génération de la variation");  // ❌ Message générique
  }
  ```

**Résultat** : Le frontend peut envoyer `offer: "pro"` si l'exercice courant est premium, mais **tous les exercices TESTS_DYN sont "free"**.

---

### 2. **BACKEND - Route /generate**

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 688** : Vérification `is_tests_dyn_request(request.code_officiel)`
- **Ligne 694-698** : Appel à `generate_tests_dyn_exercise()` :
  ```python
  dyn_exercise = generate_tests_dyn_exercise(
      offer=request.offer,
      difficulty=request.difficulte,
      seed=request.seed
  )
  ```
- **Ligne 700-708** : Si `dyn_exercise` est `None`, lève HTTPException 422 :
  ```python
  if not dyn_exercise:
      raise HTTPException(
          status_code=422,
          detail={
              "error": "no_tests_dyn_exercise_found",
              "message": f"Aucun exercice dynamique trouvé pour offer='{request.offer}' et difficulty='{request.difficulte}'",
              "hint": "Vérifiez les filtres ou utilisez /generate/batch/tests_dyn pour les lots"
          }
      )
  ```

**Résultat** : Si `generate_tests_dyn_exercise()` retourne `None`, une exception 422 est levée.

---

### 3. **BACKEND - Handler TESTS_DYN**

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Ligne 135-178** : Fonction `generate_tests_dyn_exercise()`
- **Ligne 151** : Normalisation : `offer = (offer or "free").lower()`
- **Ligne 156-160** : Sélection du template :
  ```python
  exercise_template = get_random_tests_dyn_exercise(
      offer=offer,
      difficulty=difficulty,
      seed=seed
  )
  ```
- **Ligne 163-168** : **FALLBACK** - Si aucun exercice trouvé avec `offer="pro"` :
  ```python
  if not exercise_template and offer == "pro":
      exercise_template = get_random_tests_dyn_exercise(
          offer="free",
          difficulty=difficulty,
          seed=seed  # ⚠️ MÊME SEED utilisé pour le fallback
      )
  ```
- **Ligne 170-171** : Si toujours aucun template :
  ```python
  if not exercise_template:
      return None  # ❌ Retourne None → déclenche HTTPException 422
  ```
- **Ligne 176** : **PROBLÈME IDENTIFIÉ** - Seed dérivé :
  ```python
  gen_seed = (seed or timestamp) + exercise_template["id"]
  ```
  - Le seed utilisé pour le générateur est **dérivé** du seed original
  - Si le fallback "pro" → "free" se produit, le même seed est utilisé, mais avec un template différent (ID différent)
  - **Impact** : Le déterminisme est perdu si le fallback se produit

**Résultat** : Si aucun exercice n'est trouvé après le fallback, la fonction retourne `None`.

---

### 4. **BACKEND - Sélection du template**

**Fichier** : `backend/data/tests_dyn_exercises.py`
- **Ligne 150-164** : Fonction `get_random_tests_dyn_exercise()`
- **Ligne 156** : Appel à `get_tests_dyn_exercises(offer, difficulty)`
- **Ligne 158-159** : Si aucun exercice disponible :
  ```python
  if not available:
      return None  # ❌ Retourne None
  ```
- **Ligne 161-162** : Si seed fourni :
  ```python
  if seed is not None:
      random.seed(seed)
  ```
- **Ligne 164** : Sélection aléatoire : `return random.choice(available)`

**Fichier** : `backend/data/tests_dyn_exercises.py`
- **Ligne 124-147** : Fonction `get_tests_dyn_exercises()`
- **Ligne 131** : Base : `exercises = TESTS_DYN_EXERCISES`
- **Ligne 133-141** : Filtrage par `offer` :
  ```python
  if offer:
      offer = offer.lower()
      if offer == "free":
          exercises = [ex for ex in exercises if ex["offer"] == "free"]
      elif offer == "pro":
          exercises = [ex for ex in exercises if ex["offer"] == "pro"]  # ❌ PROBLÈME
  else:
      exercises = [ex for ex in exercises if ex["offer"] == "free"]
  ```
- **Ligne 143-145** : Filtrage par `difficulty` :
  ```python
  if difficulty:
      difficulty = difficulty.lower()
      exercises = [ex for ex in exercises if ex["difficulty"] == difficulty]
  ```

**PROBLÈME CRITIQUE IDENTIFIÉ** :
- **Ligne 20-117** : Tous les exercices dans `TESTS_DYN_EXERCISES` ont `offer: "free"` :
  - ID 1 : `"offer": "free"` (ligne 25)
  - ID 2 : `"offer": "free"` (ligne 54)
  - ID 3 : `"offer": "free"` (ligne 88)
- **Aucun exercice avec `offer: "pro"` n'existe dans le pool**
- **Résultat** : Si `offer="pro"` est envoyé, le filtre ligne 137-138 retourne une liste vide
- **Fallback ligne 163-168** : Essaie "free", mais si le seed ou la difficulty ne matchent pas, peut toujours retourner None

---

## 🎯 VÉRIFICATION DES HYPOTHÈSES

### Hypothèse 1 : Gestion du paramètre `offer` (free / pro)

**✅ CONFIRMÉE - PROBLÈME IDENTIFIÉ**

**Frontend** :
- **Ligne 549-550** : Si `isCurrentPremium === true`, envoie `offer: "pro"`
- **Ligne 552-556** : Si exercice n'est pas premium mais utilisateur est PRO, **n'envoie PAS** `offer: "pro"`

**Backend** :
- **Ligne 137-138** (`tests_dyn_exercises.py`) : Filtre strict `ex["offer"] == "pro"`
- **Ligne 20-117** (`tests_dyn_exercises.py`) : **TOUS les exercices ont `offer: "free"`**
- **Résultat** : Si `offer="pro"` est envoyé, le pool est vide → `get_random_tests_dyn_exercise()` retourne `None`

**Fallback** :
- **Ligne 163-168** (`tests_dyn_handler.py`) : Si `offer="pro"` et aucun exercice, essaie `offer="free"`
- **PROBLÈME** : Le fallback utilise le **même seed**, mais si la difficulty ne matche pas, peut toujours retourner `None`

**Conclusion** : Le problème principal est que **tous les exercices TESTS_DYN sont "free"**, mais le frontend peut envoyer `offer: "pro"` si l'exercice courant est premium.

---

### Hypothèse 2 : Fonction get_random_tests_dyn_exercise()

**✅ CONFIRMÉE - PEUT RETOURNER None**

**Conditions de retour None** :
1. **Ligne 158-159** : Si `available` est vide (après filtrage par offer/difficulty)
2. **Ligne 164** : `random.choice(available)` ne peut pas lever IndexError car vérifié ligne 158

**Filtres appliqués** :
1. **Offer** : Filtre strict `ex["offer"] == offer` (ligne 137-138)
2. **Difficulty** : Filtre strict `ex["difficulty"] == difficulty` (ligne 145)
3. **Seed** : Utilisé pour `random.seed(seed)` (ligne 161-162), puis `random.choice(available)` (ligne 164)

**Scénarios où None est retourné** :
- `offer="pro"` + aucun exercice "pro" → pool vide → None
- `difficulty="difficile"` + aucun exercice "difficile" → pool vide → None
- Combinaison offer+difficulty qui ne matche aucun exercice → pool vide → None

**Conclusion** : La fonction peut retourner `None` si le pool filtré est vide.

---

### Hypothèse 3 : Chaîne d'appel complète

**✅ CONFIRMÉE - CHAÎNE IDENTIFIÉE**

```
Frontend: generateVariation(index)
  └─> Ligne 533: seed = Date.now() + Math.random() * 1000
  └─> Ligne 549-550: Si isCurrentPremium → payload.offer = "pro"
  └─> Ligne 558: axios.post(`${API_V1}/generate`, payload)
      └─> Backend: exercises_routes.py:688
          └─> is_tests_dyn_request(request.code_officiel)
          └─> exercises_routes.py:694
              └─> generate_tests_dyn_exercise(offer, difficulty, seed)
                  └─> tests_dyn_handler.py:156
                      └─> get_random_tests_dyn_exercise(offer, difficulty, seed)
                          └─> tests_dyn_exercises.py:156
                              └─> get_tests_dyn_exercises(offer, difficulty)
                                  └─> Filtre par offer (ligne 137-138)
                                  └─> Filtre par difficulty (ligne 145)
                                  └─> Si pool vide → retourne []
                          └─> tests_dyn_exercises.py:158
                              └─> Si available vide → retourne None
                  └─> tests_dyn_handler.py:163-168
                      └─> Fallback: Si offer="pro" et None, essaie offer="free"
                  └─> tests_dyn_handler.py:170-171
                      └─> Si toujours None → retourne None
          └─> exercises_routes.py:700-708
              └─> Si dyn_exercise est None → HTTPException 422
      └─> Frontend: ExerciseGeneratorPage.js:566-568
          └─> catch (error) → setError("Erreur lors de la génération de la variation")
```

**Conclusion** : La chaîne est complète et identifiée. Le point de rupture est `get_random_tests_dyn_exercise()` qui retourne `None` si le pool filtré est vide.

---

### Hypothèse 4 : Gestion du seed

**✅ CONFIRMÉE - PROBLÈME DE DÉTERMINISME**

**Frontend** :
- **Ligne 533** : `const seed = Date.now() + Math.random() * 1000`
- **Problème** : Le seed est **non déterministe** (dépend de `Date.now()` et `Math.random()`)
- **Impact** : Chaque variation génère un seed différent, même pour le même exercice

**Backend** :
- **Ligne 161-162** (`tests_dyn_exercises.py`) : Si seed fourni, `random.seed(seed)`
- **Ligne 164** : `random.choice(available)` - sélection déterministe si seed fixe
- **Ligne 176** (`tests_dyn_handler.py`) : **PROBLÈME** - Seed dérivé :
  ```python
  gen_seed = (seed or timestamp) + exercise_template["id"]
  ```
  - Le seed utilisé pour le générateur est **dérivé** du seed original
  - Si le fallback "pro" → "free" se produit, le même seed est utilisé, mais avec un template différent (ID différent)
  - **Impact** : Le déterminisme est perdu si le fallback se produit

**Scénario problématique** :
1. Variation 1 : `offer="pro"` → fallback `offer="free"` → template ID 2 → `gen_seed = seed + 2`
2. Variation 2 : `offer="pro"` → fallback `offer="free"` → template ID 1 → `gen_seed = seed + 1`
3. **Résultat** : Même seed original, mais générateurs différents → non déterministe

**Conclusion** : Le seed est bien transmis, mais :
1. Le frontend génère un seed non déterministe (`Date.now() + Math.random()`)
2. Le backend dérive le seed (`seed + template["id"]`), ce qui casse le déterminisme si le fallback se produit

---

### Hypothèse 5 : Gestion des erreurs

**✅ CONFIRMÉE - ERREUR GÉNÉRIQUE**

**Backend** :
- **Ligne 700-708** (`exercises_routes.py`) : Si `dyn_exercise` est `None`, lève HTTPException 422 avec détail structuré :
  ```python
  {
      "error": "no_tests_dyn_exercise_found",
      "message": f"Aucun exercice dynamique trouvé pour offer='{request.offer}' et difficulty='{request.difficulte}'",
      "hint": "Vérifiez les filtres ou utilisez /generate/batch/tests_dyn pour les lots"
  }
  ```
- **Résultat** : Le backend retourne toujours un JSON valide (même en erreur)

**Frontend** :
- **Ligne 566-568** (`ExerciseGeneratorPage.js`) : Gestion d'erreur générique :
  ```javascript
  catch (error) {
    console.error("Erreur lors de la génération de variation:", error);
    setError("Erreur lors de la génération de la variation");  // ❌ Message générique
  }
  ```
- **Problème** : Le message d'erreur backend structuré n'est **pas utilisé**
- **Résultat** : L'utilisateur voit un message générique au lieu du message détaillé du backend

**Conclusion** : Le backend retourne toujours un JSON valide, mais le frontend n'utilise pas le message structuré.

---

## 🎯 ROOT CAUSE IDENTIFIÉE

### Scénario 1 : Offer "pro" avec pool vide (LE PLUS PROBABLE)

1. **Frontend ligne 549-550** : Si `isCurrentPremium === true`, envoie `offer: "pro"`
2. **Backend ligne 137-138** (`tests_dyn_exercises.py`) : Filtre `ex["offer"] == "pro"`
3. **Backend ligne 20-117** (`tests_dyn_exercises.py`) : **TOUS les exercices ont `offer: "free"`**
4. **Résultat** : Pool vide → `get_random_tests_dyn_exercise()` retourne `None`
5. **Backend ligne 163-168** : Fallback essaie `offer="free"` avec le même seed
6. **Si la difficulty ne matche pas** : Pool toujours vide → retourne `None`
7. **Backend ligne 700-708** : HTTPException 422 levée
8. **Frontend ligne 568** : Message générique affiché

**Conditions de reproduction** :
- Exercice courant avec `metadata.is_premium === true`
- OU utilisateur PRO qui envoie `offer: "pro"` (mais ligne 552-556 ne l'envoie pas si exercice n'est pas premium)
- Difficulty qui ne matche aucun exercice disponible

### Scénario 2 : Difficulty qui ne matche pas

1. **Frontend ligne 543** : Envoie `difficulte: difficulte` (valeur du state)
2. **Backend ligne 145** (`tests_dyn_exercises.py`) : Filtre strict `ex["difficulty"] == difficulty`
3. **Si la difficulty ne matche aucun exercice** : Pool vide → `None`
4. **Même chaîne d'erreur que Scénario 1**

**Conditions de reproduction** :
- Difficulty "difficile" avec seulement des exercices "facile" et "moyen" disponibles
- OU difficulty "facile" avec seulement des exercices "moyen" et "difficile" disponibles

### Scénario 3 : Seed qui produit un pool vide (peu probable)

1. **Frontend ligne 533** : `seed = Date.now() + Math.random() * 1000`
2. **Backend ligne 161-162** : `random.seed(seed)`
3. **Backend ligne 164** : `random.choice(available)` - ne peut pas échouer si `available` n'est pas vide
4. **Résultat** : Le seed ne peut pas produire un pool vide directement

**Conclusion** : Le seed ne peut pas produire un pool vide, mais peut affecter la sélection si le pool est non vide.

---

## 📊 PREMIER POINT DE RUPTURE

**Fichier** : `backend/data/tests_dyn_exercises.py`
- **Ligne 137-138** : Filtre strict `ex["offer"] == "pro"`
- **Ligne 20-117** : **TOUS les exercices ont `offer: "free"`**
- **Résultat** : Si `offer="pro"` est envoyé, le pool filtré est vide

**Fichier** : `backend/data/tests_dyn_exercises.py`
- **Ligne 158-159** : Si `available` est vide, retourne `None`
- **Résultat** : `get_random_tests_dyn_exercise()` retourne `None` si le pool est vide

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Ligne 163-168** : Fallback essaie `offer="free"` si `offer="pro"` et aucun exercice
- **PROBLÈME** : Si la difficulty ne matche toujours pas, retourne `None`

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 700-708** : Si `dyn_exercise` est `None`, lève HTTPException 422
- **Résultat** : Le backend retourne une erreur structurée

**Fichier** : `frontend/src/components/ExerciseGeneratorPage.js`
- **Ligne 568** : Message générique au lieu d'utiliser le message backend
- **Résultat** : L'utilisateur voit "Erreur lors de la génération de la variation" au lieu du message détaillé

---

## ✅ CONDITIONS PRÉCISES POUR REPRODUIRE LE BUG

1. **Exercice courant avec `metadata.is_premium === true`**
   - OU utilisateur PRO (mais ligne 552-556 ne force pas `offer: "pro"` si exercice n'est pas premium)
2. **Frontend envoie `offer: "pro"`** (ligne 549-550)
3. **Backend filtre par `offer="pro"`** → pool vide (tous les exercices sont "free")
4. **Fallback essaie `offer="free"`** (ligne 163-168)
5. **Si la difficulty ne matche toujours pas** → pool vide → `None`
6. **HTTPException 422 levée** (ligne 700-708)
7. **Frontend affiche message générique** (ligne 568)

**OU**

1. **Difficulty qui ne matche aucun exercice disponible**
2. **Pool filtré vide** → `None`
3. **Même chaîne d'erreur**

---

## 📝 IMPACT SUR LE DÉTERMINISME (SEED)

**Problème identifié** :
- **Frontend ligne 533** : Seed non déterministe (`Date.now() + Math.random()`)
- **Backend ligne 176** : Seed dérivé (`seed + template["id"]`)
- **Impact** : Si le fallback "pro" → "free" se produit, le même seed original peut produire des templates différents (ID différent) → générateurs différents → non déterministe

**Conclusion** : Le déterminisme est cassé si le fallback se produit, car le seed dérivé dépend de l'ID du template sélectionné.

---

## 🎯 CONCLUSION

**Root cause principale** : Tous les exercices TESTS_DYN ont `offer: "free"`, mais le frontend peut envoyer `offer: "pro"` si l'exercice courant est premium. Le filtre strict retourne un pool vide, et si le fallback ne trouve toujours pas d'exercice (difficulty non matchée), la fonction retourne `None` → HTTPException 422 → message générique frontend.

**Premier point de rupture** : `backend/data/tests_dyn_exercises.py:137-138` - Filtre strict `ex["offer"] == "pro"` avec un pool contenant uniquement des exercices "free".

**Conditions de reproduction** :
1. Exercice courant avec `metadata.is_premium === true` → frontend envoie `offer: "pro"`
2. OU difficulty qui ne matche aucun exercice disponible
3. Pool filtré vide → `None` → HTTPException 422 → message générique

