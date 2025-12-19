# 🔧 Administration Curriculum 6e - Documentation V1

> **Version** : 1.0  
> **Date** : Décembre 2024  
> **Mode** : Lecture seule (READ-ONLY)

---

## 📋 Vue d'ensemble

La page d'administration du curriculum 6e permet de visualiser le référentiel
pédagogique sans modifier le code source.

### Fonctionnalités V1

- ✅ Visualisation des 27 chapitres 6e
- ✅ Affichage des générateurs associés
- ✅ Indication des schémas SVG
- ✅ Filtrage par recherche et domaine
- ✅ Statistiques globales
- ❌ Pas d'édition (prévu V2)
- ❌ Pas de création de chapitres (prévu V2)

---

## 🌐 Accès

### URL

```
/admin/curriculum
```

### Protection

L'accès est contrôlé par la variable d'environnement `ADMIN_ENABLED` :

```bash
# Activer l'admin (défaut en V1)
ADMIN_ENABLED=true

# Désactiver l'admin
ADMIN_ENABLED=false
```

Par défaut, l'admin est **activé** en V1 car c'est en lecture seule.

---

## 🔌 API Backend

### Endpoints disponibles

#### 1. Liste des chapitres 6e

```http
GET /api/admin/curriculum/6e
```

**Réponse :**
```json
{
  "niveau": "6e",
  "total_chapitres": 27,
  "chapitres": [
    {
      "code_officiel": "6e_N01",
      "domaine": "Nombres et calculs",
      "libelle": "Lire et écrire les nombres entiers",
      "generateurs": ["NOMBRES_LECTURE", "CALCUL_DECIMAUX"],
      "has_diagramme": false,
      "statut": "prod",
      "chapitre_backend": "Nombres entiers et décimaux",
      "tags": ["entiers", "lecture"],
      "difficulte_min": 1,
      "difficulte_max": 3
    }
  ],
  "stats": {
    "total": 27,
    "with_diagrams": 18,
    "by_domaine": {...},
    "by_status": {...}
  }
}
```

#### 2. Détail d'un chapitre

```http
GET /api/admin/curriculum/6e/{code_officiel}
```

**Exemple :**
```http
GET /api/admin/curriculum/6e/6e_N08
```

**Réponse :**
```json
{
  "code_officiel": "6e_N08",
  "domaine": "Nombres et calculs",
  "libelle": "Fractions comme partage et quotient",
  "generateurs": ["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"],
  "has_diagramme": true,
  "statut": "prod",
  "chapitre_backend": "Fractions"
}
```

#### 3. Validation du curriculum

```http
GET /api/admin/curriculum/6e/validate
```

**Réponse :**
```json
{
  "valid": true,
  "total_chapters": 27,
  "chapters_with_generators": 27,
  "chapters_without_generators": 0,
  "chapters_by_status": {"prod": 27},
  "chapters_by_domaine": {...},
  "warnings": []
}
```

#### 4. Statistiques globales

```http
GET /api/admin/curriculum/stats
```

---

## 🎨 Interface utilisateur

### Tableau des chapitres

| Colonne | Description |
|---------|-------------|
| **Code** | Code officiel (6e_N01, 6e_G01, etc.) |
| **Domaine** | Catégorie mathématique |
| **Libellé** | Intitulé officiel du programme |
| **Générateurs** | Types d'exercices associés |
| **Schéma** | ✓ si des SVG sont générés |
| **Statut** | prod / beta / hidden |

### Filtres

- **Recherche** : Par code ou libellé
- **Domaine** : Sélection parmi les 4 domaines

### Statistiques

- Total chapitres
- Chapitres avec schémas
- Nombre de domaines
- Chapitres en production

---

## 📁 Fichiers

### Backend

| Fichier | Rôle |
|---------|------|
| `backend/routes/admin_curriculum_routes.py` | Endpoints API admin |
| `backend/tests/test_admin_curriculum.py` | Tests unitaires |

### Frontend

| Fichier | Rôle |
|---------|------|
| `frontend/src/components/admin/Curriculum6eAdminPage.js` | Composant React |
| `frontend/src/App.js` | Route `/admin/curriculum` |

### Documentation

| Fichier | Rôle |
|---------|------|
| `docs/ADMIN_CURRICULUM_6E.md` | Cette documentation |

---

## 🔒 Sécurité

### V1 - Lecture seule

- Aucune modification possible via l'API
- Pas d'authentification requise (lecture seule)
- Protection par flag `ADMIN_ENABLED`

### V2 - Prévu

- Authentification requise pour l'édition
- Logs d'audit
- Historique des modifications

---

## 🔄 Non-régression

Les endpoints suivants restent inchangés :

- `POST /api/v1/exercises/generate` (mode legacy)
- `POST /api/v1/exercises/generate` (mode code_officiel)
- `/generate` (page frontend)

---

## 🔮 Évolutions V2

### Fonctionnalités prévues

1. **Édition des chapitres**
   - Modifier les générateurs associés
   - Changer le statut (prod/beta/hidden)
   - Ajouter des tags

2. **Gestion des contextes**
   - Ajouter des contextes thématiques (DBZ, foot...)
   - Prévisualisation avec contexte

3. **Import/Export**
   - Export CSV/JSON
   - Import de nouveaux chapitres

4. **Historique**
   - Logs des modifications
   - Rollback possible

---

## 🧪 Tests

### Lancer les tests

```bash
cd /app/backend
python3 -m pytest tests/test_admin_curriculum.py -v
```

### Tests couverts

- Chargement des 27 chapitres
- Structure des données
- Validation des codes
- Filtrage par domaine
- Non-régression des endpoints existants

---

*Documentation V1 - Décembre 2024*
