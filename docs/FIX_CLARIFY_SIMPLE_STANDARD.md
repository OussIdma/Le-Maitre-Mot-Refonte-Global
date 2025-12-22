# Fix Clarification Simple vs Standard - Documentation

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Enlever l'ambiguïté "Officiel", clarifier Simple vs Standard, et afficher le niveau clairement dans l'UI.

---

## Modifications Frontend

### Fichier modifié : `frontend/src/components/ExerciseGeneratorPage.js`

### 1. Remplacement "Mode Officiel" → "Mode Standard (programme)"

**Avant** :
```javascript
<Label htmlFor="view-mode" className={`text-sm ${!isPro ? 'text-gray-400' : 'text-gray-600'}`}>
  Officiel
  {!isPro && <Crown className="h-3 w-3 inline ml-1 text-amber-500" />}
</Label>
```

**Après** :
```javascript
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Label htmlFor="view-mode" className={`text-sm ${!isPro ? 'text-gray-400' : 'text-gray-600'} cursor-help`}>
        Standard (programme)
        {!isPro && <Crown className="h-3 w-3 inline ml-1 text-amber-500" />}
      </Label>
    </TooltipTrigger>
    {isPro && (
      <TooltipContent>
        <p>Aligné sur les attendus du programme. (Sources à documenter)</p>
      </TooltipContent>
    )}
  </Tooltip>
</TooltipProvider>
```

**Changements** :
- Libellé "Officiel" → "Standard (programme)"
- Tooltip sur le label avec message "Aligné sur les attendus du programme. (Sources à documenter)"
- Tooltip sur le switch si mode Standard activé (Pro uniquement)
- Icône Crown conservée si non Pro

### 2. Affichage du niveau en header

**Avant** :
```javascript
<p className="text-lg text-gray-600">
  Programme officiel de 6e • {catalog?.total_chapters || 0} chapitres disponibles
  {isPro && <span className="text-purple-600 ml-2">• Générateurs premium activés</span>}
</p>
```

**Après** :
```javascript
{/* Niveau affiché clairement */}
<div className="mb-3">
  <Badge variant="outline" className="text-base px-4 py-1.5 border-blue-300 text-blue-700 bg-blue-50">
    Niveau : 6e
  </Badge>
</div>
<p className="text-lg text-gray-600">
  {catalog?.total_chapters || 0} chapitres disponibles
  {isPro && <span className="text-purple-600 ml-2">• Générateurs premium activés</span>}
</p>
```

**Changements** :
- Badge "Niveau : 6e" affiché clairement en header
- Suppression de "Programme officiel de 6e" (redondant)

### 3. Clarification Simple vs Standard

**Avant** :
```javascript
<div className="flex items-center gap-3 bg-gray-100 px-4 py-2 rounded-lg">
  {/* Toggle sans texte explicatif */}
</div>
```

**Après** :
```javascript
<div className="flex flex-col items-end gap-2">
  <div className="flex items-center gap-3 bg-gray-100 px-4 py-2 rounded-lg">
    {/* Toggle */}
  </div>
  {/* Textes explicatifs sous le toggle */}
  <div className="flex items-center gap-4 text-xs text-gray-500">
    <span>Simple : exercices guidés</span>
    <span className="text-gray-300">|</span>
    <span>Standard : difficulté normale</span>
  </div>
</div>
```

**Changements** :
- Ajout de textes explicatifs sous le toggle
- "Simple : exercices guidés"
- "Standard : difficulté normale"
- Layout en colonne pour inclure les textes

### 4. Mise à jour des messages informatifs

**Info sur le mode sélectionné** :
- "Mode simple" → "Mode Simple : Un chapitre sera sélectionné automatiquement parmi le groupe (exercices guidés)"
- "Code officiel" → "Mode Standard : Code officiel {code} (difficulté normale)"

**Message si aucun exercice** :
- "Le mode simple regroupe les chapitres par thème" → "Le mode Simple regroupe les chapitres par thème (exercices guidés)"
- "Le mode officiel affiche les 28 chapitres du programme" → "Le mode Standard affiche les chapitres du programme (difficulté normale)"

### 5. Vérification paramètres API

**État actuel** :
- Le frontend envoie `code_officiel` dans le payload
- Le backend déduit le mode depuis le `code_officiel` (macro group ou chapitre direct)
- **Pas de paramètre `preset` nécessaire** : Le backend peut déduire le mode depuis le `code_officiel`

**Conclusion** : Aucune modification backend nécessaire. Le backend reçoit déjà un paramètre déterministe (`code_officiel`) qui permet de déterminer le mode.

---

## Checklist manuelle (5 points)

### 1. Test affichage niveau
- Ouvrir `/generer`
- **Attendu** : Badge "Niveau : 6e" visible en header, clairement affiché

### 2. Test libellé "Standard (programme)"
- Vérifier le toggle
- **Attendu** : Libellé "Standard (programme)" au lieu de "Officiel"
- Si Pro : Tooltip au survol avec "Aligné sur les attendus du programme. (Sources à documenter)"
- Si non Pro : Icône Crown visible

### 3. Test textes explicatifs
- Vérifier sous le toggle
- **Attendu** : "Simple : exercices guidés | Standard : difficulté normale" visible

### 4. Test messages informatifs
- Sélectionner un chapitre en mode Simple
- **Attendu** : Message "Mode Simple : Un chapitre sera sélectionné automatiquement parmi le groupe (exercices guidés)"
- Sélectionner un chapitre en mode Standard
- **Attendu** : Message "Mode Standard : Code officiel {code} (difficulté normale)"

### 5. Test génération API
- Générer un exercice en mode Simple puis Standard
- Vérifier la console navigateur
- **Attendu** : Logs "Mode Simple" et "Mode Standard" (pas "Mode officiel")
- **Attendu** : Payload API contient `code_officiel` (déterministe)

---

## Fichiers modifiés

1. **frontend/src/components/ExerciseGeneratorPage.js**
   - Remplacement "Officiel" → "Standard (programme)"
   - Ajout tooltip avec message explicatif
   - Affichage niveau en header
   - Ajout textes explicatifs sous le toggle
   - Mise à jour messages informatifs

---

## Validation

- ✅ Compilation : Pas d'erreurs de syntaxe
- ✅ Libellé : "Standard (programme)" au lieu de "Officiel"
- ✅ Tooltip : Message explicatif pour mode Standard
- ✅ Niveau : Badge "Niveau : 6e" affiché clairement
- ✅ Textes explicatifs : "Simple : exercices guidés | Standard : difficulté normale"
- ✅ Messages informatifs : Mis à jour avec clarifications
- ✅ API : Paramètres déterministes (code_officiel) conservés

---

## Notes

- **Pas de modification backend** : Le backend reçoit déjà `code_officiel` qui est déterministe
- **Icône Crown** : Conservée pour mode Standard si non Pro
- **Tooltip** : Visible uniquement si Pro et mode Standard activé, ou si non Pro (pour expliquer la restriction)

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

