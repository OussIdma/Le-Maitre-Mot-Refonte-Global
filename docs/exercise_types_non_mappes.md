# ExerciseType non mappés vers chapter_code

**Date de création:** 2024-12-09  
**Sprint:** Migration douce des ExerciseType vers chapitres MathALÉA

---

## 📊 Contexte

Suite à la migration 002, **7 ExerciseType sur 47** (14.9%) n'ont pas pu être automatiquement mappés vers un `chapter_code` MathALÉA.

Ces exercices **restent fonctionnels** via leur `chapitre_id` (legacy) et ne posent aucun problème de régression.

Ce document liste ces exercices et propose des correspondances manuelles à valider.

---

## 🔍 Liste des ExerciseType non mappés

### 1. LEGACY_EQ_1DEG_4e

**Informations :**
- **Code:** `LEGACY_EQ_1DEG_4e`
- **Titre:** Équations du 1er degré (4e)
- **Niveau:** 4e
- **Domaine:** Nombres et calculs
- **chapitre_id (legacy):** `Calcul littéral`

**Analyse :**
Le chapitre_id "Calcul littéral" est trop générique. Ce type d'exercice traite spécifiquement des équations du premier degré.

**Chapitres possibles :**
1. ✅ **`4e_CL04`** - Équations du premier degré (ax + b = c)  
   👉 **RECOMMANDATION : Meilleur match** (correspondance exacte avec le titre)
2. `4e_CL01` - Expressions littérales : simplifier, réduire  
   (Moins spécifique)

**Action proposée :**
```python
chapter_code = "4e_CL04"
```

---

### 2. LEGACY_EQ_1DEG_3e

**Informations :**
- **Code:** `LEGACY_EQ_1DEG_3e`
- **Titre:** Équations du 1er degré (3e)
- **Niveau:** 3e
- **Domaine:** Nombres et calculs
- **chapitre_id (legacy):** `Calcul littéral`

**Analyse :**
Même problématique que pour 4e. Le matching automatique n'a pas trouvé de correspondance car les chapitres 3e n'ont pas de chapitre spécifique "Équations du 1er degré".

**Chapitres possibles :**
1. ✅ **`3e_CL03`** - Équations du premier degré et problèmes  
   👉 **RECOMMANDATION : Meilleur match** (correspondance exacte)

**Action proposée :**
```python
chapter_code = "3e_CL03"
```

---

### 3. LEGACY_RECT_6e

**Informations :**
- **Code:** `LEGACY_RECT_6e`
- **Titre:** Rectangle et quadrilatères (6e)
- **Niveau:** 6e
- **Domaine:** Espace et géométrie
- **chapitre_id (legacy):** `Géométrie - Triangles et quadrilatères`

**Analyse :**
Le chapitre_id mélange triangles et quadrilatères. Ce type d'exercice se concentre sur les quadrilatères.

**Chapitres possibles :**
1. ✅ **`6e_G05`** - Quadrilatères usuels (carré, rectangle, losange, parallélogramme)  
   👉 **RECOMMANDATION : Meilleur match** (traite spécifiquement des quadrilatères dont le rectangle)
2. `6e_G04` - Triangles (construction et classification)  
   (Ne traite que des triangles)

**Action proposée :**
```python
chapter_code = "6e_G05"
```

---

### 4. LEGACY_RECT_5e

**Informations :**
- **Code:** `LEGACY_RECT_5e`
- **Titre:** Rectangle et quadrilatères (5e)
- **Niveau:** 5e
- **Domaine:** Espace et géométrie
- **chapitre_id (legacy):** `Géométrie - Triangles et quadrilatères`

**Analyse :**
Même problématique que pour 6e.

**Chapitres possibles :**
1. ✅ **`5e_G04`** - Parallélogrammes (définition et propriétés)  
   👉 **RECOMMANDATION : Meilleur match** (les rectangles sont des parallélogrammes particuliers)
2. `5e_G03` - Triangles particuliers  
   (Ne traite que des triangles)

**Action proposée :**
```python
chapter_code = "5e_G04"
```

---

### 5. LEGACY_PERIM_AIRE_6e

**Informations :**
- **Code:** `LEGACY_PERIM_AIRE_6e`
- **Titre:** Périmètres et aires (6e)
- **Niveau:** 6e
- **Domaine:** Espace et géométrie
- **chapitre_id (legacy):** `Périmètres et aires`

**Analyse :**
Le matching automatique n'a pas trouvé de correspondance directe. Ce type d'exercice traite des grandeurs et mesures.

**Chapitres possibles :**
1. ✅ **`6e_GM02`** - Périmètre de figures usuelles  
   👉 **RECOMMANDATION : Meilleur match**
2. ✅ **`6e_GM03`** - Aire du rectangle et du carré  
   👉 **Alternative valide** (dépend si l'exercice traite plutôt périmètres ou aires)

**Action proposée :**
```python
chapter_code = "6e_GM02"  # ou "6e_GM03" selon le contenu exact
```

---

### 6. LEGACY_PERIM_AIRE_5e

**Informations :**
- **Code:** `LEGACY_PERIM_AIRE_5e`
- **Titre:** Périmètres et aires (5e)
- **Niveau:** 5e
- **Domaine:** Espace et géométrie
- **chapitre_id (legacy):** `Périmètres et aires`

**Analyse :**
Même problématique que pour 6e.

**Chapitres possibles :**
1. ✅ **`5e_GM01`** - Aire de figures composées simples  
   👉 **RECOMMANDATION : Meilleur match**
2. ✅ **`5e_GM02`** - Périmètre et aire du cercle (intuition)  
   👉 **Alternative** (dépend si le cercle est traité)

**Action proposée :**
```python
chapter_code = "5e_GM01"  # ou "5e_GM02" selon le contenu
```

---

### 7. LEGACY_PERIM_AIRE_4e

**Informations :**
- **Code:** `LEGACY_PERIM_AIRE_4e`
- **Titre:** Périmètres et aires (4e)
- **Niveau:** 4e
- **Domaine:** Espace et géométrie
- **chapitre_id (legacy):** `Périmètres et aires`

**Analyse :**
Même problématique.

**Chapitres possibles :**
1. ✅ **`4e_GM01`** - Aire du disque  
   👉 **RECOMMANDATION : Meilleur match** (traite des aires)

**Action proposée :**
```python
chapter_code = "4e_GM01"
```

---

## 📋 Résumé des actions proposées

| Code ExerciseType | chapter_code proposé | Confiance |
|-------------------|---------------------|-----------|
| `LEGACY_EQ_1DEG_4e` | `4e_CL04` | ✅ Haute |
| `LEGACY_EQ_1DEG_3e` | `3e_CL03` | ✅ Haute |
| `LEGACY_RECT_6e` | `6e_G05` | ✅ Haute |
| `LEGACY_RECT_5e` | `5e_G04` | ✅ Haute |
| `LEGACY_PERIM_AIRE_6e` | `6e_GM02` ou `6e_GM03` | ⚠️ À valider |
| `LEGACY_PERIM_AIRE_5e` | `5e_GM01` ou `5e_GM02` | ⚠️ À valider |
| `LEGACY_PERIM_AIRE_4e` | `4e_GM01` | ✅ Haute |

---

## 🔧 Script de mise à jour manuelle

Une fois les correspondances validées, exécuter ce script pour mettre à jour la base :

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def update_unmapped_exercises():
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client.mathalea_db
    
    # Mapping validé manuellement
    manual_mapping = {
        "LEGACY_EQ_1DEG_4e": "4e_CL04",
        "LEGACY_EQ_1DEG_3e": "3e_CL03",
        "LEGACY_RECT_6e": "6e_G05",
        "LEGACY_RECT_5e": "5e_G04",
        "LEGACY_PERIM_AIRE_6e": "6e_GM02",  # À ajuster si besoin
        "LEGACY_PERIM_AIRE_5e": "5e_GM01",  # À ajuster si besoin
        "LEGACY_PERIM_AIRE_4e": "4e_GM01"
    }
    
    for code_ref, chapter_code in manual_mapping.items():
        result = await db.exercise_types.update_one(
            {"code_ref": code_ref},
            {"$set": {"chapter_code": chapter_code}}
        )
        
        if result.modified_count > 0:
            print(f"✅ {code_ref} → {chapter_code}")
        else:
            print(f"⚠️  {code_ref} : Aucune mise à jour")
    
    client.close()

# asyncio.run(update_unmapped_exercises())
```

**⚠️ IMPORTANT :** Ne pas exécuter ce script sans validation manuelle des correspondances.

---

## 📊 Statistiques finales (après mise à jour manuelle)

- Total ExerciseType : 47
- Avec chapter_code (automatique) : 40 (85.1%)
- À mapper manuellement : 7 (14.9%)
- **Objectif après validation : 100% mappés**

---

## 📝 Notes

- Ces exercices **fonctionnent toujours** avec leur `chapitre_id` legacy
- La migration est **non bloquante** et **non régressive**
- Les correspondances proposées sont des **suggestions** basées sur l'analyse des titres et du contenu
- Une validation manuelle par un expert pédagogique est **recommandée** avant mise à jour en production
