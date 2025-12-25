# P0 - Auth Réactive + Bouton "Sauvegarder (Pro)" - Diff et Checklist

## Objectif
Rendre l'auth réactive (sans refresh) + afficher "Sauvegarder (Pro)" aux guests comme levier de conversion.

---

## Fichiers modifiés

### 1. `frontend/src/hooks/useAuth.js` (NOUVEAU)

**Création du hook réactif d'authentification**

```javascript
/**
 * useAuth - Hook réactif pour gérer l'authentification
 * 
 * Écoute les changements d'auth via:
 * - Événement custom "lmm:auth-changed"
 * - Événement "storage" (multi-tabs)
 * - Mise à jour automatique quand localStorage change
 */

import { useState, useEffect } from 'react';

const getAuthFromStorage = () => {
  const sessionToken = localStorage.getItem('lemaitremot_session_token');
  const userEmail = localStorage.getItem('lemaitremot_user_email');
  const loginMethod = localStorage.getItem('lemaitremot_login_method');
  
  const isPro = !!(sessionToken && userEmail && loginMethod === 'session');
  
  return {
    sessionToken: sessionToken || null,
    userEmail: userEmail || null,
    isPro
  };
};

export const useAuth = () => {
  const [authState, setAuthState] = useState(getAuthFromStorage);
  
  useEffect(() => {
    const updateAuthState = () => {
      const newState = getAuthFromStorage();
      setAuthState(newState);
    };
    
    const handleAuthChanged = () => {
      console.log('[useAuth] Événement lmm:auth-changed détecté');
      updateAuthState();
    };
    
    const handleStorageChange = (e) => {
      if (
        e.key === 'lemaitremot_session_token' ||
        e.key === 'lemaitremot_user_email' ||
        e.key === 'lemaitremot_login_method' ||
        e.key === null
      ) {
        console.log('[useAuth] Changement localStorage détecté:', e.key);
        updateAuthState();
      }
    };
    
    window.addEventListener('lmm:auth-changed', handleAuthChanged);
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('lmm:auth-changed', handleAuthChanged);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);
  
  return authState;
};
```

**Changements**:
- ✅ Hook réactif qui lit `localStorage` au mount
- ✅ Écoute `lmm:auth-changed` (événement custom)
- ✅ Écoute `storage` (multi-tabs)
- ✅ Retourne `{sessionToken, userEmail, isPro}`

---

### 2. `frontend/src/components/GlobalLoginModal.js`

**Diff** - Ajout du dispatch d'événement après login réussi

```diff
      // Store session token and user info
      const sessionToken = response.data.session_token;
      localStorage.setItem('lemaitremot_session_token', sessionToken);
      localStorage.setItem('lemaitremot_user_email', loginEmail);
      localStorage.setItem('lemaitremot_login_method', 'session');
      
+     // P0: Dispatcher l'événement pour notifier les composants utilisant useAuth()
+     window.dispatchEvent(new Event('lmm:auth-changed'));
+     
      closeLogin();
      
      // P0 UX: Rediriger vers returnTo si présent
      const returnTo = sessionStorage.getItem('postLoginRedirect');
      if (returnTo) {
        sessionStorage.removeItem('postLoginRedirect');
        setTimeout(() => {
          navigate(returnTo);
        }, 100);
      }
      
      toast({
        title: "Connexion réussie",
        description: "Vous êtes maintenant connecté.",
      });
      
      // Ne pas reload - React Router gère la navigation
-     // L'état auth sera mis à jour via LoginContext
+     // L'état auth sera mis à jour via useAuth() hook
```

**Changements**:
- ✅ Dispatch `lmm:auth-changed` après login réussi
- ✅ Commentaire mis à jour

---

### 3. `frontend/src/components/ExerciseGeneratorPage.js`

**Diff 1** - Imports ajoutés

```diff
import { useToast } from "../hooks/use-toast";
+ import { useAuth } from "../hooks/useAuth";
+ import { useLogin } from "../contexts/LoginContext";
+ import { useNavigate } from "react-router-dom";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";
- import { Trash2, RefreshCw, Save, Check } from "lucide-react";
+ import { Trash2, RefreshCw, Save, Check, Lock } from "lucide-react";
```

**Diff 2** - Remplacement de la logique mount-only par useAuth()

```diff
const ExerciseGeneratorPage = () => {
  const { toast } = useToast();
+ const { openLogin } = useLogin();
+ const navigate = useNavigate();
  
- // États PRO - Détection de l'utilisateur premium
- const [isPro, setIsPro] = useState(false);
- const [userEmail, setUserEmail] = useState("");
+ // P0: Utiliser le hook useAuth() pour un état réactif
+ const { sessionToken, userEmail, isPro } = useAuth();
  
  // État pour le seed de génération GM07 (pour reproductibilité des variations)
  const [gm07Seed, setGm07Seed] = useState(null);
  
  // État pour le warning batch (pool insuffisant)
  const [batchWarning, setBatchWarning] = useState(null);
  
  // P3.0: États pour la sauvegarde d'exercices
  const [savedExercises, setSavedExercises] = useState(new Set());
  const [savingExerciseId, setSavingExerciseId] = useState(null);
  
  // Track premium badges viewed (P2.2)
  useEffect(() => {
    exercises.forEach((exercise, index) => {
      if (exercise.metadata?.premium_available && 
          !exercise.metadata?.is_premium && 
          !isPro) {
        trackPremiumEvent('premium_badge_viewed', {
          exercise_id: exercise.id_exercice,
          generator_key: exercise.metadata?.generator_key,
          index: index
        });
      }
    });
  }, [exercises, isPro]);
  
- // Initialiser l'authentification PRO
- useEffect(() => {
-   const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
-   const storedEmail = localStorage.getItem('lemaitremot_user_email');
-   const loginMethod = localStorage.getItem('lemaitremot_login_method');
-   
-   if (storedSessionToken && storedEmail && loginMethod === 'session') {
-     setUserEmail(storedEmail);
-     setIsPro(true);
-     console.log('🌟 Mode PRO activé:', storedEmail);
-     
-     // P3.0: Charger les exercices sauvegardés pour marquer ceux déjà sauvegardés
-     loadSavedExercises(storedSessionToken);
-   }
- }, []);
+ // P0: Charger les exercices sauvegardés quand sessionToken devient disponible
+ useEffect(() => {
+   if (sessionToken && isPro) {
+     console.log('🌟 Mode PRO activé (réactif):', userEmail);
+     loadSavedExercises(sessionToken);
+   }
+ }, [sessionToken, isPro, userEmail]);
```

**Diff 3** - Modification de handleSaveExercise() pour gérer les guests

```diff
  // P3.0: Sauvegarder un exercice
  const handleSaveExercise = async (exercise) => {
-   const sessionToken = localStorage.getItem('lemaitremot_session_token');
-   
-   if (!sessionToken) {
-     toast({
-       title: "Authentification requise",
-       description: "Veuillez vous connecter pour sauvegarder un exercice",
-       variant: "destructive"
-     });
-     return;
-   }
+   // P0: Si pas Pro, ouvrir le modal de login avec message
+   if (!isPro || !sessionToken) {
+     const currentPath = window.location.pathname;
+     openLogin(currentPath);
+     toast({
+       title: "Sauvegarde réservée aux Pro",
+       description: "Connectez-vous avec un compte Pro pour sauvegarder vos exercices",
+       variant: "default"
+     });
+     return;
+   }
    
    // Vérifier si déjà sauvegardé
    if (savedExercises.has(exercise.id_exercice)) {
      // ... reste du code inchangé
```

**Diff 4** - Bouton "Sauvegarder" visible pour tous (avec lock si Guest)

```diff
-                   {/* P3.0: Bouton Sauvegarder */}
-                   {isPro && (
-                     <Button
-                       onClick={() => handleSaveExercise(exercise)}
-                       disabled={savingExerciseId === exercise.id_exercice || savedExercises.has(exercise.id_exercice)}
-                       variant={savedExercises.has(exercise.id_exercice) ? "outline" : "default"}
-                       size="sm"
-                       className={savedExercises.has(exercise.id_exercice) ? "border-green-300 text-green-700" : ""}
-                     >
-                       {savingExerciseId === exercise.id_exercice ? (
-                         <>
-                           <Loader2 className="mr-2 h-4 w-4 animate-spin" />
-                           Sauvegarde...
-                         </>
-                       ) : savedExercises.has(exercise.id_exercice) ? (
-                         <>
-                           <Check className="mr-2 h-4 w-4" />
-                           Sauvegardé ✅
-                         </>
-                       ) : (
-                         <>
-                           <Save className="mr-2 h-4 w-4" />
-                           Sauvegarder
-                         </>
-                       )}
-                     </Button>
-                   )}
+                   {/* P0: Bouton Sauvegarder - Visible pour tous (avec lock si Guest) */}
+                   <Button
+                     onClick={() => handleSaveExercise(exercise)}
+                     disabled={savingExerciseId === exercise.id_exercice || savedExercises.has(exercise.id_exercice)}
+                     variant={savedExercises.has(exercise.id_exercice) ? "outline" : isPro ? "default" : "outline"}
+                     size="sm"
+                     className={
+                       savedExercises.has(exercise.id_exercice) 
+                         ? "border-green-300 text-green-700" 
+                         : !isPro 
+                           ? "border-gray-300 text-gray-600 hover:bg-gray-50" 
+                           : ""
+                     }
+                   >
+                     {savingExerciseId === exercise.id_exercice ? (
+                       <>
+                         <Loader2 className="mr-2 h-4 w-4 animate-spin" />
+                         Sauvegarde...
+                       </>
+                     ) : savedExercises.has(exercise.id_exercice) ? (
+                       <>
+                         <Check className="mr-2 h-4 w-4" />
+                         Sauvegardé ✅
+                       </>
+                     ) : isPro ? (
+                       <>
+                         <Save className="mr-2 h-4 w-4" />
+                         Sauvegarder
+                       </>
+                     ) : (
+                       <>
+                         <Lock className="mr-2 h-4 w-4" />
+                         Sauvegarder (Pro)
+                       </>
+                     )}
+                   </Button>
```

**Changements**:
- ✅ Remplacement de `useState` pour `isPro/userEmail` par `useAuth()`
- ✅ `useEffect` réactif qui charge les exercices quand `sessionToken` devient disponible
- ✅ Bouton "Sauvegarder" visible pour tous
- ✅ Bouton affiche "Sauvegarder (Pro)" avec icône Lock si Guest
- ✅ Au clic Guest → ouvre le modal de login + toast explicatif

---

## Checklist de tests manuels

### Test 1: Auth réactive après login (sans refresh)
**Prérequis**: Être déconnecté

1. ✅ Ouvrir `/generer` dans un onglet
2. ✅ Vérifier que le bouton affiche "Sauvegarder (Pro)" avec icône Lock
3. ✅ Générer un exercice
4. ✅ Cliquer sur "Se connecter" dans le header
5. ✅ Se connecter avec un compte Pro
6. ✅ **VÉRIFIER**: Sans refresh, le bouton change automatiquement en "Sauvegarder" (sans Lock)
7. ✅ **VÉRIFIER**: Les exercices sauvegardés se chargent automatiquement (badge "Sauvegardé ✅" si déjà sauvegardé)

**Résultat attendu**: ✅ Auth réactive, pas besoin de refresh

---

### Test 2: Bouton "Sauvegarder (Pro)" visible pour Guest
**Prérequis**: Être déconnecté

1. ✅ Ouvrir `/generer`
2. ✅ Générer un exercice
3. ✅ **VÉRIFIER**: Le bouton "Sauvegarder (Pro)" est visible avec icône Lock
4. ✅ **VÉRIFIER**: Le style est `outline` (bordure grise, texte gris)
5. ✅ Cliquer sur le bouton
6. ✅ **VÉRIFIER**: Le modal de login s'ouvre
7. ✅ **VÉRIFIER**: Un toast s'affiche: "Sauvegarde réservée aux Pro"

**Résultat attendu**: ✅ Levier de conversion visible et fonctionnel

---

### Test 3: Sauvegarde après login (Guest → Pro)
**Prérequis**: Être déconnecté

1. ✅ Ouvrir `/generer`
2. ✅ Générer un exercice
3. ✅ Cliquer sur "Sauvegarder (Pro)"
4. ✅ Se connecter dans le modal
5. ✅ **VÉRIFIER**: Après connexion, le bouton devient "Sauvegarder" (sans Lock)
6. ✅ Cliquer sur "Sauvegarder"
7. ✅ **VÉRIFIER**: L'exercice est sauvegardé (toast de confirmation)
8. ✅ **VÉRIFIER**: Le bouton change en "Sauvegardé ✅"

**Résultat attendu**: ✅ Parcours complet Guest → Login → Sauvegarde fonctionne

---

### Test 4: Multi-tabs (synchronisation auth)
**Prérequis**: Être déconnecté

1. ✅ Ouvrir `/generer` dans l'onglet 1
2. ✅ Ouvrir `/generer` dans l'onglet 2
3. ✅ Dans l'onglet 1, se connecter
4. ✅ **VÉRIFIER**: Dans l'onglet 2, le bouton change automatiquement en "Sauvegarder" (sans refresh)

**Résultat attendu**: ✅ Synchronisation multi-tabs fonctionne

---

### Test 5: Déconnexion (Pro → Guest)
**Prérequis**: Être connecté en Pro

1. ✅ Ouvrir `/generer`
2. ✅ Générer un exercice
3. ✅ **VÉRIFIER**: Le bouton affiche "Sauvegarder" (sans Lock)
4. ✅ Se déconnecter (via header)
5. ✅ **VÉRIFIER**: Sans refresh, le bouton change en "Sauvegarder (Pro)" avec Lock

**Résultat attendu**: ✅ Déconnexion réactive

---

### Test 6: Exercices déjà sauvegardés
**Prérequis**: Être connecté en Pro avec des exercices sauvegardés

1. ✅ Ouvrir `/generer`
2. ✅ Générer un exercice déjà sauvegardé
3. ✅ **VÉRIFIER**: Le bouton affiche "Sauvegardé ✅" (désactivé, style vert)
4. ✅ **VÉRIFIER**: Le bouton est désactivé (pas cliquable)

**Résultat attendu**: ✅ État "déjà sauvegardé" correctement affiché

---

### Test 7: Comportement Pro (sauvegarde normale)
**Prérequis**: Être connecté en Pro

1. ✅ Ouvrir `/generer`
2. ✅ Générer un exercice non sauvegardé
3. ✅ **VÉRIFIER**: Le bouton affiche "Sauvegarder" (sans Lock, style default)
4. ✅ Cliquer sur "Sauvegarder"
5. ✅ **VÉRIFIER**: Pendant la sauvegarde, le bouton affiche "Sauvegarde..." avec loader
6. ✅ **VÉRIFIER**: Après sauvegarde, le bouton change en "Sauvegardé ✅"

**Résultat attendu**: ✅ Comportement Pro inchangé et fonctionnel

---

## Résumé des changements

### Fichiers créés
- ✅ `frontend/src/hooks/useAuth.js` - Hook réactif d'authentification

### Fichiers modifiés
- ✅ `frontend/src/components/GlobalLoginModal.js` - Dispatch événement après login
- ✅ `frontend/src/components/ExerciseGeneratorPage.js` - Utilisation de useAuth() + bouton visible pour tous

### Fonctionnalités
- ✅ Auth réactive (sans refresh) via événements custom + storage
- ✅ Bouton "Sauvegarder (Pro)" visible pour Guest comme levier de conversion
- ✅ Synchronisation multi-tabs
- ✅ Rechargement automatique des exercices sauvegardés après login

### Tests
- ✅ 7 tests manuels définis
- ✅ Couverture: Guest, Pro, Login, Déconnexion, Multi-tabs, États



