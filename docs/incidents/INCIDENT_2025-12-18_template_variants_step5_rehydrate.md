## INCIDENT – Variants d’énoncés dynamiques (Étape 5 : réhydratation admin & CRUD)

### 1. Métadonnées

- **ID incident** : `INCIDENT_2025-12-18_template_variants_step5_rehydrate`
- **Date** : 2025-12-18
- **Contexte** : UI admin – gestion des `template_variants` pour les exercices dynamiques (chapitres pilotes)
- **Gravité** : P3 (UX admin / cohérence données), sans impact direct sur la génération élève
- **Statut** : résolu

### 2. Symptôme

- **Depuis l’UI admin** (`ChapterExercisesAdminPage`) :
  - Création d’un exercice dynamique avec plusieurs `template_variants` (variants d’énoncé/correction).
  - Sauvegarde via le formulaire.
  - À la réouverture de l’exercice, l’éditeur affiche parfois uniquement un “variant virtuel” basé sur les champs legacy (`enonce_template_html` / `solution_template_html`), donnant l’impression que les `template_variants` ont disparu.
- **Complément** :
  - Les appels CRUD utilisaient encore des `fetch` directs, sans passer par `adminApi.apiCall`, ce qui compliquait la traçabilité des erreurs JSON côté admin.

### 3. Root cause

**Côté backend (vérification)** :

- Le service de persistance (`ExercisePersistenceService`) :
  - stocke bien `template_variants` lors de la création (`create_exercise`), et
  - renvoie l’intégralité du document (y compris `template_variants`) via `get_exercises` et `get_exercise_by_id` :

```520:572:backend/services/exercise_persistence_service.py
async def get_exercises(
    self,
    chapter_code: str,
    offer: Optional[str] = None,
    difficulty: Optional[str] = None
) -> List[Dict[str, Any]]:
    ...
    exercises = await self.collection.find(
        query,
        {"_id": 0}
    ).sort("id", 1).to_list(100)
    return exercises
```

**Côté frontend (cause principale UX)** :

- La réhydratation du formulaire d’édition dans `ChapterExercisesAdminPage` prenait bien en compte `exercise.template_variants`, mais :
  - le mode “variants” (`isVariantMode`) dépendait de `formData.is_dynamic` **et** de la présence de `template_variants` :

```237:245:frontend/src/components/admin/ChapterExercisesAdminPage.js
// Helpers variants dynamiques
const isVariantMode =
  formData.is_dynamic &&
  Array.isArray(formData.template_variants) &&
  formData.template_variants.length > 0;

const effectiveVariants = isVariantMode
  ? formData.template_variants
  : [
    { id: 'v1', ... enonce_template_html: formData.enonce_template_html, ... },
  ];
```

- En cas d’incohérence ou de désactivation accidentelle de `is_dynamic` (ex. modifications successives, migration, données anciennes), la présence de `template_variants` dans la réponse backend n’était plus suffisante : l’UI basculait en mode “legacy” et reconstruisait un variant virtuel à partir des templates racine, **masquant** les vrais variants pourtant stockés en DB.
- En parallèle, les appels `POST/PUT/DELETE` étaient encore effectués avec des `fetch` bruts, sans centralisation via `adminApi`, ce qui :
  - dupliquait la logique de timeout / parsing JSON,
  - rendait plus difficile le suivi de la présence effective de `template_variants` dans les payloads envoyés.

### 4. Correctif appliqué

#### 4.1. Réhydratation et source de vérité côté UI

- **Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js`
- **Changements** :
  - Introduction d’un flag `hasTemplateVariants` et simplification du mode variants :

```237:253:frontend/src/components/admin/ChapterExercisesAdminPage.js
// Helpers variants dynamiques
const hasTemplateVariants =
  Array.isArray(formData.template_variants) &&
  formData.template_variants.length > 0;

// Dès que des template_variants existent, ils sont la source de vérité pour l'UI
const isVariantMode = hasTemplateVariants;

const effectiveVariants = hasTemplateVariants
  ? formData.template_variants
  : [
      {
        id: 'v1',
        label: 'Variant 1',
        weight: 1,
        enonce_template_html: formData.enonce_template_html || '',
        solution_template_html: formData.solution_template_html || '',
      },
    ];
```

- **Effet** :
  - Dès qu’un exercice possède des `template_variants` non vides (issus de l’API admin), l’UI bascule **toujours** en mode variants et utilise ce tableau comme **source de vérité unique**.
  - Le “variant virtuel” basé sur les champs legacy n’est utilisé qu’en absence totale de `template_variants` (exercices legacy ou premiers brouillons sans variants).

#### 4.2. Centralisation CRUD via `adminApi`

- **Fichiers** :
  - `frontend/src/lib/adminApi.js`
  - `frontend/src/components/admin/ChapterExercisesAdminPage.js`

- **Ajouts dans `adminApi.js`** :

```159:182:frontend/src/lib/adminApi.js
export async function createChapterExercise(chapterCode, exercisePayload) {
  return apiCall(`/api/admin/chapters/${chapterCode}/exercises`, {
    method: 'POST',
    body: exercisePayload,
    timeout: DEFAULT_TIMEOUT,
  });
}

export async function updateChapterExercise(chapterCode, exerciseId, exercisePayload) {
  return apiCall(`/api/admin/chapters/${chapterCode}/exercises/${exerciseId}`, {
    method: 'PUT',
    body: exercisePayload,
    timeout: DEFAULT_TIMEOUT,
  });
}

export async function deleteChapterExercise(chapterCode, exerciseId) {
  return apiCall(`/api/admin/chapters/${chapterCode}/exercises/${exerciseId}`, {
    method: 'DELETE',
    timeout: DEFAULT_TIMEOUT,
  });
}
```

- **Refactor dans `ChapterExercisesAdminPage.js`** :
  - Import des nouvelles fonctions :

```58:63:frontend/src/components/admin/ChapterExercisesAdminPage.js
import {
  createChapterExercise,
  updateChapterExercise,
  deleteChapterExercise,
} from '../../lib/adminApi';
```

  - Remplacement du `fetch` direct dans `handleSubmit` par `createChapterExercise` / `updateChapterExercise` :

```520:588:frontend/src/components/admin/ChapterExercisesAdminPage.js
const result =
  modalMode === 'create'
    ? await createChapterExercise(chapterCode, payload)
    : await updateChapterExercise(chapterCode, editingExercise.id, payload);

if (!result.success) {
  const details = result.error_details || {};
  const message =
    result.error ||
    details.message ||
    'Erreur lors de la sauvegarde';
  throw new Error(message);
}

const data = result.data || {};
setOperationMessage({
  type: 'success',
  text: data.message || `Exercice ${modalMode === 'create' ? 'créé' : 'modifié'} avec succès`
});
```

  - Remplacement du `fetch` direct dans `handleConfirmDelete` par `deleteChapterExercise` :

```597:632:frontend/src/components/admin/ChapterExercisesAdminPage.js
const result = await deleteChapterExercise(chapterCode, exerciseToDelete.id);

if (!result.success) {
  const details = result.error_details || {};
  const message =
    result.error ||
    details.message ||
    'Erreur lors de la suppression';
  throw new Error(message);
}

const data = result.data || {};
setOperationMessage({
  type: 'success',
  text: data.message || 'Exercice supprimé avec succès'
});
```

- **Effet** :
  - Tous les CRUD admin (create/update/delete) bénéficient désormais du parsing JSON défensif et des codes d’erreurs structurés d’`adminApi.apiCall`.
  - Le payload envoyé reste strictement identique (pas de transformation métier supplémentaire), y compris pour `template_variants`.

### 5. Tests et validation

#### 5.1. Tests UI (manuels)

1. **Création avec variants, puis réouverture**
   - Créer un exercice dynamique (`is_dynamic = true`) avec au moins 2 `template_variants`.
   - Sauvegarder.
   - Revenir à la liste des exercices, cliquer sur “Modifier” :
     - le bloc “Variants d’énoncés dynamiques” affiche la liste complète des variants (id, label, weight, templates),
     - les textareas “Template énoncé/solution” reflètent le variant sélectionné.

2. **Modification d’un variant, sauvegarde, réouverture**
   - Modifier le texte d’un variant (par ex. ajouter un marqueur `(V2 TEST)`).
   - Sauvegarder.
   - Revenir à la liste, réouvrir l’exercice :
     - le variant modifié apparaît avec le texte mis à jour.

3. **Suppression d’un exercice dynamique**
   - Supprimer un exercice dynamique via le bouton “Supprimer”.
   - Vérifier que :
     - l’entrée disparaît du tableau,
     - aucun message d’erreur réseau/JSON n’apparaît,
     - l’API renvoie un JSON `success: true` avec un message explicite.

#### 5.2. Tests API / réseau

- Via l’onglet Network du navigateur (ou un proxy) :
  - Vérifier que les requêtes `POST /api/admin/chapters/{chapterCode}/exercises` et `PUT /api/admin/chapters/{chapterCode}/exercises/{id}` contiennent bien le champ `template_variants` lorsque l’UI est en mode variants.
  - Vérifier que les réponses d’erreur (4xx/5xx) sont JSON et passent par le format structuré d’`adminApi` (`error_code`, `message`, `error_details`).

### 6. Risques résiduels et contraintes

- **Aucun impact** sur les pipelines de génération élève (GM07/GM08, TESTS_DYN) : les changements sont strictement côté UI admin + client HTTP admin.
- **Risque résiduel** :
  - Des données anciennes pourraient contenir des incohérences entre `is_dynamic` et `template_variants`, mais le nouvel algorithme (`hasTemplateVariants` → source de vérité pour l’UI) minimise le risque de “variants invisibles”.
- **Rappel règles CTO** :
  - `template_variants` non vide = source de vérité unique pour le rendu dynamique.
  - Les champs legacy restent un miroir/compat, jamais source de vérité en présence de variants.


