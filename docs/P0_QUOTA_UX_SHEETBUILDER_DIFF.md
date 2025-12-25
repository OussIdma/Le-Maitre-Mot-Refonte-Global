# P0 - UX Quota Clair + Upgrade Immédiat dans SheetBuilderPage

## Objectif
Afficher le quota clairement et proposer upgrade immédiat quand quota dépassé dans SheetBuilderPage.js

---

## Fichiers modifiés

### `frontend/src/components/SheetBuilderPage.js`

**Diff 1** - Imports ajoutés

```diff
import ProExportModal from "./ProExportModal";
+ import UpgradeProModal from "./UpgradeProModal";
+ import { useToast } from "../hooks/use-toast";
```

**Diff 2** - États ajoutés

```diff
  // États pour filtres
  const [selectedDomain, setSelectedDomain] = useState("");
  const [selectedGeneratorKind, setSelectedGeneratorKind] = useState("");
  const [availableDomains, setAvailableDomains] = useState([]);
+ 
+ // P0: États pour le quota guest
+ const [quotaStatus, setQuotaStatus] = useState(null);
+ const [quotaLoading, setQuotaLoading] = useState(false);
+ const [showUpgradeModal, setShowUpgradeModal] = useState(false);
+ 
+ const { toast } = useToast();
```

**Diff 3** - useEffect pour charger le quota

```diff
  // Initialiser l'authentification
  useEffect(() => {
    // ... code existant ...
  }, []);
+ 
+ // P0: Charger le quota guest si !isPro
+ useEffect(() => {
+   if (!isPro) {
+     loadQuotaStatus();
+   } else {
+     // Si Pro, pas de quota
+     setQuotaStatus(null);
+   }
+ }, [isPro]);
+ 
+ // P0: Fonction pour charger le quota
+ const loadQuotaStatus = async () => {
+   try {
+     setQuotaLoading(true);
+     const guestId = localStorage.getItem('lemaitremot_guest_id');
+     
+     if (!guestId) {
+       // Créer un guest_id si absent
+       const newGuestId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
+       localStorage.setItem('lemaitremot_guest_id', newGuestId);
+       
+       // Charger avec le nouveau guest_id
+       const response = await axios.get(`${API}/quota/check?guest_id=${newGuestId}`);
+       setQuotaStatus(response.data);
+       return;
+     }
+     
+     const response = await axios.get(`${API}/quota/check?guest_id=${guestId}`);
+     setQuotaStatus(response.data);
+     console.log('📊 Quota chargé:', response.data);
+   } catch (error) {
+     console.error('Erreur chargement quota:', error);
+     // En cas d'erreur, on continue quand même (pas bloquant)
+   } finally {
+     setQuotaLoading(false);
+   }
+ };
```

**Diff 4** - Vérification quota avant export dans handleGeneratePDF()

```diff
  const handleGeneratePDF = async () => {
    if (sheetItems.length === 0) {
      alert('Veuillez ajouter au moins un exercice à la fiche');
      return;
    }
    
+   // P0: Vérifier le quota avant export (si !isPro)
+   if (!isPro) {
+     const guestId = localStorage.getItem('lemaitremot_guest_id');
+     
+     if (!guestId) {
+       // Créer un guest_id si absent
+       const newGuestId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
+       localStorage.setItem('lemaitremot_guest_id', newGuestId);
+     }
+     
+     // Vérifier le quota
+     try {
+       const quotaResponse = await axios.get(`${API}/quota/check?guest_id=${guestId || localStorage.getItem('lemaitremot_guest_id')}`);
+       const quota = quotaResponse.data;
+       
+       if (quota.quota_exceeded) {
+         // Quota dépassé - ouvrir modal upgrade
+         setShowUpgradeModal(true);
+         toast({
+           title: "Quota d'exports atteint",
+           description: `Vous avez utilisé vos ${quota.max_exports} exports gratuits. Passez à Pro pour continuer.`,
+           variant: "destructive"
+         });
+         return;
+       }
+       
+       // Mettre à jour le quota affiché
+       setQuotaStatus(quota);
+     } catch (error) {
+       console.error('Erreur vérification quota:', error);
+       // Continuer quand même si erreur (pas bloquant)
+     }
+   }
+   
    setIsGeneratingPDF(true);
    
    try {
      // ... sauvegarde fiche ...
      
      const config = {};
      if (sessionToken) {
        config.headers = {
          'X-Session-Token': sessionToken
        };
+     } else {
+       // P0: Ajouter guest_id si pas Pro
+       const guestId = localStorage.getItem('lemaitremot_guest_id');
+       if (guestId) {
+         config.headers = {
+           'X-Guest-ID': guestId
+         };
+       }
      }
      
      // ... appel export-standard ...
      
      // Stocker les résultats et ouvrir la modale
      setPdfResult({...});
      setShowPdfModal(true);
      
+     // P0: Recharger le quota après export réussi (si guest)
+     if (!isPro) {
+       await loadQuotaStatus();
+     }
+     
      console.log('✅ 2 PDFs générés et prêts à télécharger');
      
    } catch (error) {
      console.error('Erreur génération PDF:', error);
      
+     // P0: Gérer erreur 402 (quota dépassé)
+     if (error.response?.status === 402 && error.response?.data?.detail?.error === 'quota_exceeded') {
+       const quotaDetail = error.response.data.detail;
+       setShowUpgradeModal(true);
+       toast({
+         title: "Quota d'exports atteint",
+         description: quotaDetail.message || `Vous avez utilisé vos ${quotaDetail.max_exports} exports gratuits. Passez à Pro pour continuer.`,
+         variant: "destructive"
+       });
+       // Recharger le quota
+       await loadQuotaStatus();
+       return;
+     }
+     
      // Improved error handling
      let errorMessage = 'Erreur lors de la génération du PDF. ';
      
      if (error.response) {
        if (error.response.status >= 400 && error.response.status < 500) {
-         errorMessage += error.response.data?.detail || 'Merci de vérifier la configuration des exercices.';
+         errorMessage += error.response.data?.detail?.message || error.response.data?.detail || 'Merci de vérifier la configuration des exercices.';
        } else if (error.response.status >= 500) {
          errorMessage += 'Erreur serveur. Merci de réessayer plus tard.';
        }
      } else if (error.request) {
        errorMessage += 'Impossible de contacter le serveur. Vérifiez votre connexion.';
      } else {
        errorMessage += error.message || 'Une erreur inattendue s\'est produite.';
      }
      
-     alert(errorMessage);
+     toast({
+       title: "Erreur",
+       description: errorMessage,
+       variant: "destructive"
+     });
    } finally {
      setIsGeneratingPDF(false);
    }
  };
```

**Diff 5** - Affichage du quota près du bouton

```diff
-                     <Button
-                       onClick={handleGeneratePDF}
-                       disabled={isGeneratingPDF}
-                       className="w-full bg-green-600 hover:bg-green-700"
-                     >
-                       {isGeneratingPDF ? (
-                         <Loader2 className="h-4 w-4 mr-2 animate-spin" />
-                       ) : (
-                         <Download className="h-4 w-4 mr-2" />
-                       )}
-                       Générer PDF
-                     </Button>
+                     <div className="space-y-2">
+                       <Button
+                         onClick={handleGeneratePDF}
+                         disabled={isGeneratingPDF}
+                         className="w-full bg-green-600 hover:bg-green-700"
+                       >
+                         {isGeneratingPDF ? (
+                           <Loader2 className="h-4 w-4 mr-2 animate-spin" />
+                         ) : (
+                           <Download className="h-4 w-4 mr-2" />
+                         )}
+                         Générer PDF
+                       </Button>
+                       
+                       {/* P0: Afficher le quota restant (si guest) */}
+                       {!isPro && quotaStatus && (
+                         <div className="text-center text-xs text-gray-600">
+                           {quotaStatus.quota_exceeded ? (
+                             <span className="text-red-600 font-medium">
+                               ⚠️ Quota atteint ({quotaStatus.exports_used}/{quotaStatus.max_exports})
+                             </span>
+                           ) : (
+                             <span className="text-gray-600">
+                               {quotaStatus.exports_remaining} export{quotaStatus.exports_remaining > 1 ? 's' : ''} gratuit{quotaStatus.exports_remaining > 1 ? 's' : ''} restant{quotaStatus.exports_remaining > 1 ? 's' : ''}
+                             </span>
+                           )}
+                         </div>
+                       )}
+                     </div>
```

**Diff 6** - Ajout du modal UpgradeProModal

```diff
      {/* Pro Export Modal */}
      <ProExportModal
        isOpen={showProExportModal}
        onClose={() => setShowProExportModal(false)}
        sheetId={sheetId}
        sheetTitle={sheetTitle}
        sessionToken={sessionToken}
      />
+     
+     {/* P0: Upgrade Pro Modal */}
+     <UpgradeProModal
+       isOpen={showUpgradeModal}
+       onClose={() => setShowUpgradeModal(false)}
+       context="export"
+     />
    </div>
  );
}
```

---

## Checklist de tests manuels

### Test 1: Affichage quota restant (Guest)
**Prérequis**: Être déconnecté (guest)

1. ✅ Ouvrir `/mes-fiches` ou créer une nouvelle fiche
2. ✅ Ajouter au moins un exercice à la fiche
3. ✅ **VÉRIFIER**: Sous le bouton "Générer PDF", affichage: "X exports gratuits restants" (ex: "3 exports gratuits restants")
4. ✅ **VÉRIFIER**: Le texte est en gris, centré, petite taille

**Résultat attendu**: ✅ Quota affiché clairement

---

### Test 2: Quota atteint - Affichage + Modal
**Prérequis**: Guest avec 3 exports déjà utilisés (dans les 30 derniers jours)

1. ✅ Ouvrir `/mes-fiches`
2. ✅ Créer une fiche avec exercices
3. ✅ **VÉRIFIER**: Sous le bouton "Générer PDF", affichage: "⚠️ Quota atteint (3/3)" en rouge
4. ✅ Cliquer sur "Générer PDF"
5. ✅ **VÉRIFIER**: Le modal UpgradeProModal s'ouvre
6. ✅ **VÉRIFIER**: Un toast s'affiche: "Quota d'exports atteint - Vous avez utilisé vos 3 exports gratuits. Passez à Pro pour continuer."
7. ✅ **VÉRIFIER**: L'export ne démarre pas (pas de loader)

**Résultat attendu**: ✅ Quota atteint → Modal upgrade + Toast + Export bloqué

---

### Test 3: Vérification quota avant export (Guest avec quota OK)
**Prérequis**: Guest avec quota disponible (ex: 2 exports restants)

1. ✅ Ouvrir `/mes-fiches`
2. ✅ Créer une fiche avec exercices
3. ✅ **VÉRIFIER**: Affichage "2 exports gratuits restants"
4. ✅ Cliquer sur "Générer PDF"
5. ✅ **VÉRIFIER**: L'export démarre (loader visible)
6. ✅ **VÉRIFIER**: Après export réussi, le quota se met à jour (affiche "1 export gratuit restant")
7. ✅ **VÉRIFIER**: Les 2 PDFs sont générés (élève + corrigé)

**Résultat attendu**: ✅ Export réussi + Quota mis à jour automatiquement

---

### Test 4: Erreur 402 backend (quota dépassé pendant export)
**Prérequis**: Guest avec quota OK au moment du clic, mais quota dépassé côté backend

1. ✅ Ouvrir `/mes-fiches`
2. ✅ Créer une fiche
3. ✅ Cliquer "Générer PDF"
4. ✅ Simuler une erreur 402 du backend (ou utiliser un guest_id avec quota déjà dépassé)
5. ✅ **VÉRIFIER**: Le modal UpgradeProModal s'ouvre
6. ✅ **VÉRIFIER**: Toast avec message: "Quota d'exports atteint"
7. ✅ **VÉRIFIER**: Le quota est rechargé et affiche "Quota atteint"

**Résultat attendu**: ✅ Gestion propre de l'erreur 402 + Modal upgrade

---

### Test 5: Pro user (pas de quota affiché)
**Prérequis**: Être connecté en Pro

1. ✅ Se connecter avec un compte Pro
2. ✅ Ouvrir `/mes-fiches`
3. ✅ Créer une fiche
4. ✅ **VÉRIFIER**: Aucun affichage de quota sous le bouton "Générer PDF"
5. ✅ Cliquer "Générer PDF"
6. ✅ **VÉRIFIER**: Export réussit sans vérification de quota
7. ✅ **VÉRIFIER**: Les 2 PDFs sont générés

**Résultat attendu**: ✅ Pro user → Pas de quota, export illimité

---

### Test 6: Création automatique guest_id
**Prérequis**: Guest sans guest_id dans localStorage

1. ✅ Supprimer `lemaitremot_guest_id` du localStorage
2. ✅ Ouvrir `/mes-fiches`
3. ✅ Créer une fiche
4. ✅ **VÉRIFIER**: Un `guest_id` est créé automatiquement dans localStorage
5. ✅ **VÉRIFIER**: Le quota s'affiche (3 exports restants)
6. ✅ Cliquer "Générer PDF"
7. ✅ **VÉRIFIER**: L'export réussit avec le nouveau `guest_id`

**Résultat attendu**: ✅ Création automatique de guest_id si absent

---

### Test 7: Rechargement quota après export
**Prérequis**: Guest avec quota disponible

1. ✅ Ouvrir `/mes-fiches`
2. ✅ Créer une fiche
3. ✅ **VÉRIFIER**: Affichage initial: "3 exports gratuits restants"
4. ✅ Cliquer "Générer PDF"
5. ✅ **VÉRIFIER**: Export réussit
6. ✅ **VÉRIFIER**: Après export, affichage mis à jour: "2 exports gratuits restants"
7. ✅ **VÉRIFIER**: Le quota est rechargé automatiquement

**Résultat attendu**: ✅ Quota mis à jour automatiquement après export

---

### Test 8: Passage Guest → Pro (quota disparaît)
**Prérequis**: Guest avec quota affiché

1. ✅ Ouvrir `/mes-fiches` en Guest
2. ✅ **VÉRIFIER**: Quota affiché (ex: "2 exports gratuits restants")
3. ✅ Se connecter avec un compte Pro (dans un autre onglet ou via header)
4. ✅ Revenir sur `/mes-fiches`
5. ✅ **VÉRIFIER**: Le quota disparaît (pas d'affichage)
6. ✅ **VÉRIFIER**: Export fonctionne sans quota

**Résultat attendu**: ✅ Transition Guest → Pro → Quota disparaît

---

### Test 9: guest_id transmis au backend
**Prérequis**: Guest

1. ✅ Ouvrir `/mes-fiches`
2. ✅ Créer une fiche
3. ✅ Ouvrir DevTools → Network
4. ✅ Cliquer "Générer PDF"
5. ✅ **VÉRIFIER**: La requête POST `/api/mathalea/sheets/{id}/export-standard` contient:
   - Header `X-Guest-ID: <guest_id>` OU query `?guest_id=<guest_id>`
6. ✅ **VÉRIFIER**: L'export réussit

**Résultat attendu**: ✅ guest_id correctement transmis au backend

---

### Test 10: Modal upgrade - Navigation vers pricing
**Prérequis**: Guest avec quota atteint

1. ✅ Ouvrir `/mes-fiches`
2. ✅ Créer une fiche
3. ✅ Cliquer "Générer PDF" (quota atteint)
4. ✅ **VÉRIFIER**: Modal UpgradeProModal s'ouvre
5. ✅ Cliquer "Essayer Pro" ou "Voir les tarifs"
6. ✅ **VÉRIFIER**: Navigation vers `/pricing`

**Résultat attendu**: ✅ Modal upgrade fonctionnel avec navigation

---

## Résumé des changements

### Fonctionnalités ajoutées
- ✅ Vérification quota avant export (si !isPro)
- ✅ Affichage quota restant sous le bouton "Générer PDF"
- ✅ Modal UpgradeProModal quand quota dépassé
- ✅ Toast explicatif quand quota atteint
- ✅ Rechargement automatique du quota après export
- ✅ Création automatique de guest_id si absent
- ✅ Transmission guest_id au backend (header X-Guest-ID)
- ✅ Gestion erreur 402 (quota dépassé côté backend)

### UX améliorée
- ✅ **Quota visible**: L'utilisateur voit toujours combien d'exports il lui reste
- ✅ **Upgrade immédiat**: Modal s'ouvre automatiquement quand quota atteint
- ✅ **Messages clairs**: Toast explicatif avec action suggérée
- ✅ **Pas de surprise**: Vérification avant export, pas après

### Tests
- ✅ 10 tests manuels définis
- ✅ Couverture: Guest, Pro, Quota OK, Quota atteint, Transition, Erreurs



