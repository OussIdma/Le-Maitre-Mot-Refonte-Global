# GUIDE D'IMPLÉMENTATION - REFACTOR UI ADMIN EXERCICES

## Modifications clés à apporter

### 1. Fonctions de détection (✅ DÉJÀ AJOUTÉES)

Les fonctions suivantes ont été ajoutées dans `ChapterExercisesAdminPage.js` :
- `getExerciseType(exercise)` : Retourne 'GENERATOR' | 'STATIC_DB' | 'CATALOG_LEGACY'
- `isLegacySource(exercise)` : Vérifie si l'exercice provient d'une source legacy
- `filterByType(exercisesList, type)` : Filtre les exercices par type
- Variables calculées : `catalogExercises`, `generatorExercises`, `staticDBExercises`, `legacyExercises`

### 2. Modification des onglets (✅ DÉJÀ COMMENCÉE)

Les onglets ont été modifiés pour avoir 3 onglets au lieu de 2 :
- 📚 Catalogue
- 🧩 Générateurs  
- 📄 Statiques DB

### 3. À FAIRE : Remplacer le contenu des TabsContent

#### Onglet Catalogue (nouveau)

```javascript
<TabsContent value="catalogue" className="space-y-6">
  {/* Vue unifiée de TOUS les exercices avec badges */}
  <Card>
    <CardHeader>
      <CardTitle>📚 Catalogue - Tous les exercices consommables</CardTitle>
      <CardDescription>
        Vue unifiée : Générateurs 🧩 + Statiques DB 📄 + Legacy 📚
      </CardDescription>
    </CardHeader>
    <CardContent>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Type</TableHead>
            <TableHead>ID</TableHead>
            <TableHead>Énoncé</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {catalogExercises.map((exercise) => {
            const type = getExerciseType(exercise);
            const badge = type === 'GENERATOR' ? '🧩 Générateur' : 
                         type === 'STATIC_DB' ? '📄 Statique DB' : 
                         '📚 Legacy';
            return (
              <TableRow key={exercise.id}>
                <TableCell>
                  <Badge>{badge}</Badge>
                </TableCell>
                <TableCell>#{exercise.id}</TableCell>
                <TableCell>{getExercisePreview(exercise)}</TableCell>
                <TableCell>
                  {type === 'GENERATOR' && (
                    <Button onClick={() => handleOpenEdit(exercise)}>Modifier</Button>
                  )}
                  {type === 'STATIC_DB' && (
                    <Button onClick={() => handleEditStatic(exercise)}>Modifier</Button>
                  )}
                  {type === 'CATALOG_LEGACY' && (
                    <Button onClick={() => handleDuplicateLegacy(exercise)}>Dupliquer vers DB</Button>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </CardContent>
  </Card>
</TabsContent>
```

#### Onglet Générateurs (remplace "Dynamiques")

```javascript
<TabsContent value="generateurs" className="space-y-6">
  {/* UNIQUEMENT les exercices avec is_dynamic=true et generator_key */}
  {/* Utiliser generatorExercises au lieu de exercises */}
  {/* Le reste du code existant de l'onglet "dynamiques" */}
</TabsContent>
```

#### Onglet Statiques DB (existant, à adapter)

```javascript
<TabsContent value="statiques" className="space-y-6">
  {/* UNIQUEMENT les exercices STATIC_DB (is_dynamic=false ET pas legacy) */}
  {/* Utiliser staticDBExercises au lieu de staticExercises */}
  {/* Le reste du code existant */}
</TabsContent>
```

### 4. À FAIRE : Adapter les handlers de modification

#### handleOpenEdit (pour générateurs)

```javascript
const handleOpenEdit = (exercise) => {
  const type = getExerciseType(exercise);
  
  if (type === 'GENERATOR') {
    // Ouvrir le modal générateur (formulaire complet avec variables, templates)
    setEditingExercise(exercise);
    setFormData({
      ...exercise,
      is_dynamic: true,
      generator_key: exercise.generator_key,
      variables: exercise.variables || {},
      template_variants: exercise.template_variants || []
    });
    setModalMode('edit');
    setIsModalOpen(true);
  } else if (type === 'STATIC_DB') {
    // Rediriger vers le modal statique
    handleEditStatic(exercise);
  } else if (type === 'CATALOG_LEGACY') {
    // Afficher un message : "Cet exercice est legacy, dupliquez-le vers DB pour l'éditer"
    toast({
      title: "Exercice legacy",
      description: "Cet exercice provient d'un fichier Python. Dupliquez-le vers Statiques DB pour l'éditer.",
      variant: "info"
    });
  }
};
```

#### handleEditStatic (pour statiques DB)

```javascript
// Vérifier que l'exercice est bien STATIC_DB avant d'éditer
const handleEditStatic = (exercise) => {
  const type = getExerciseType(exercise);
  
  if (type !== 'STATIC_DB') {
    toast({
      title: "Erreur",
      description: "Cet exercice ne peut pas être édité comme statique DB.",
      variant: "destructive"
    });
    return;
  }
  
  // Code existant...
};
```

### 5. À FAIRE : Ajouter la fonction de duplication legacy

```javascript
const handleDuplicateLegacy = async (exercise) => {
  if (!window.confirm(`Dupliquer l'exercice legacy #${exercise.id} vers Statiques DB ?`)) {
    return;
  }
  
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/admin/chapters/${chapterCode}/static-exercises`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: exercise.title || `Copie de #${exercise.id}`,
          difficulty: exercise.difficulty || 'moyen',
          enonce_html: exercise.enonce_html,
          solution_html: exercise.solution_html,
          tags: exercise.tags || [],
          order: exercise.order || null,
          offer: exercise.offer || 'free'
        })
      }
    );
    
    if (!response.ok) {
      throw new Error('Erreur duplication');
    }
    
    toast({
      title: "Exercice dupliqué",
      description: "L'exercice legacy a été dupliqué vers Statiques DB. Vous pouvez maintenant l'éditer.",
    });
    
    fetchStaticExercises();
    fetchExercises();
  } catch (err) {
    toast({
      title: "Erreur",
      description: err.message,
      variant: "destructive"
    });
  }
};
```

### 6. À FAIRE : Ajouter la section Debug (dev only)

```javascript
{process.env.NODE_ENV === 'development' && (
  <Card className="mt-6 border-yellow-300">
    <CardHeader>
      <CardTitle className="text-sm">🔧 Debug (dev only)</CardTitle>
    </CardHeader>
    <CardContent>
      <details>
        <summary className="cursor-pointer text-sm text-gray-600">
          Afficher les détails techniques
        </summary>
        <div className="mt-4 space-y-2 text-xs font-mono">
          <div>Total exercices: {exercises.length}</div>
          <div>Générateurs: {generatorExercises.length}</div>
          <div>Statiques DB: {staticDBExercises.length}</div>
          <div>Legacy: {legacyExercises.length}</div>
          <div>Pipeline: {chapterPipeline}</div>
        </div>
      </details>
    </CardContent>
  </Card>
)}
```

### 7. À FAIRE : Mettre à jour le chargement des statiques

Modifier `fetchStaticExercises` pour charger uniquement les statiques DB (pas les legacy) :

```javascript
const fetchStaticExercises = useCallback(async () => {
  // ... code existant ...
  
  // Après récupération, filtrer pour ne garder que STATIC_DB
  const data = await response.json();
  const staticDBOnly = data.filter(ex => getExerciseType(ex) === 'STATIC_DB');
  setStaticExercises(staticDBOnly);
}, [chapterCode]);
```

### 8. À FAIRE : Mettre à jour le useEffect pour charger les statiques

```javascript
useEffect(() => {
  if (activeTab === 'statiques' || activeTab === 'catalogue') {
    fetchStaticExercises();
  }
}, [activeTab, fetchStaticExercises]);
```

## Checklist de validation

- [ ] Les 3 onglets sont visibles et fonctionnels
- [ ] Catalogue affiche tous les exercices avec badges
- [ ] Générateurs affiche uniquement les exercices avec `is_dynamic=true`
- [ ] Statiques DB affiche uniquement les exercices STATIC_DB (pas legacy)
- [ ] Le modal "Modifier" ouvre le bon formulaire selon le type
- [ ] Les exercices legacy ne peuvent pas être modifiés directement
- [ ] La fonction "Dupliquer vers DB" fonctionne pour les legacy
- [ ] La section Debug est visible uniquement en dev
- [ ] Aucune régression : les fonctionnalités existantes fonctionnent toujours

## Notes importantes

1. **Pas de régression backend** : Toutes les routes API existantes restent inchangées
2. **Filtrage frontend** : Le filtrage par type se fait côté frontend pour éviter de modifier les APIs
3. **Compatibilité** : Le code doit fonctionner avec les exercices existants (migration P3.2)




