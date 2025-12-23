# P2 - ACTIONS PRIORITAIRES : GRATUIT VS PREMIUM

**Date**: 23 décembre 2025  
**Référence**: `docs/P2_PARCOURS_PROF_GRATUIT_VS_PREMIUM.md`

---

## 🚨 PROBLÈME CRITIQUE IDENTIFIÉ

**Les générateurs premium sont accessibles en mode gratuit !**

### Détail technique

```python
# backend/routes/exercises_routes.py (ligne 1441)
premium_only_generators = ["DUREES_PREMIUM"]  # ❌ Liste obsolète
```

**Générateurs premium NON filtrés**:
- `RAISONNEMENT_MULTIPLICATIF_V1` ⚠️
- `CALCUL_NOMBRES_V1` ⚠️
- `SIMPLIFICATION_FRACTIONS_V2` ⚠️

**Conséquence**: Un utilisateur gratuit peut générer des exercices premium !

---

## 🎯 4 ACTIONS PRIORITAIRES

### P2.1 - 🔴 CRITIQUE : Sécuriser le filtrage gratuit/premium

**Temps estimé**: 1-2h  
**Complexité**: Faible  
**Impact**: Critique (protection du revenu)

#### Tâches

1. **Mettre à jour la liste des générateurs premium**

```python
# backend/routes/exercises_routes.py (ligne 1441)

# Liste des générateurs premium à exclure en mode gratuit
premium_only_generators = [
    "RAISONNEMENT_MULTIPLICATIF_V1",
    "CALCUL_NOMBRES_V1",
    "SIMPLIFICATION_FRACTIONS_V2",
    "DUREES_PREMIUM",  # Obsolète mais garder pour legacy
]
```

2. **Ajouter un test E2E**

```python
# backend/tests/test_premium_access.py (CRÉER)

def test_gratuit_ne_peut_pas_acceder_premium():
    """Vérifier que offer=free n'utilise pas les générateurs premium."""
    response = client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_SP03",  # Utilise RAISONNEMENT_MULTIPLICATIF_V1
            "offer": "free",
            "seed": 42
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier que ce n'est PAS un générateur premium
    assert data["metadata"]["is_premium"] is False
    assert data["metadata"]["generator_key"] not in [
        "RAISONNEMENT_MULTIPLICATIF_V1",
        "CALCUL_NOMBRES_V1"
    ]
```

3. **Tester manuellement**

```bash
# Test 1: Utilisateur gratuit sur chapitre premium
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_SP03",
    "offer": "free",
    "seed": 42
  }' | jq '.metadata.is_premium, .metadata.generator_key'

# Attendu: false, "STANDARD" ou fallback
# PAS "RAISONNEMENT_MULTIPLICATIF_V1"

# Test 2: Utilisateur premium sur même chapitre
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_SP03",
    "offer": "pro",
    "seed": 42
  }' | jq '.metadata.is_premium, .metadata.generator_key'

# Attendu: true, "RAISONNEMENT_MULTIPLICATIF_V1"
```

#### Validation

- [ ] Liste `premium_only_generators` mise à jour
- [ ] Test E2E créé et passant
- [ ] Test manuel gratuit → pas de générateur premium
- [ ] Test manuel premium → générateur premium actif
- [ ] Commit + Push

---

### P2.2 - 🟠 MAJEUR : Ajouter badges "PREMIUM" dans l'UI

**Temps estimé**: 4-6h  
**Complexité**: Moyenne  
**Impact**: Fort (visibilité de la valeur premium)

#### Tâches Frontend

1. **Badge sur les chapitres premium** (`ExerciseGeneratorPage.js`)

```javascript
// Dans la liste des chapitres, ajouter un indicateur premium
{chapter.is_premium && (
  <Badge className="ml-2 bg-purple-100 text-purple-800 hover:bg-purple-100 border border-purple-300">
    ✨ PREMIUM
  </Badge>
)}

// Tooltip explicatif
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger>
      <Crown className="h-4 w-4 text-purple-600 ml-1" />
    </TooltipTrigger>
    <TooltipContent>
      <p>Exercices premium : solutions détaillées + variété infinie</p>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

2. **Détecter les chapitres premium côté frontend**

```javascript
// Ajouter une propriété `is_premium` aux chapitres du catalog
const enrichCatalogWithPremium = (catalog) => {
  const premiumGenerators = [
    "RAISONNEMENT_MULTIPLICATIF_V1",
    "CALCUL_NOMBRES_V1",
    "SIMPLIFICATION_FRACTIONS_V2"
  ];
  
  return {
    ...catalog,
    domains: catalog.domains.map(domain => ({
      ...domain,
      chapters: domain.chapters.map(chapter => ({
        ...chapter,
        is_premium: chapter.exercise_types?.some(et => 
          premiumGenerators.includes(et)
        ) || false
      }))
    }))
  };
};
```

3. **Badge sur les exercices générés**

```javascript
// Dans le rendu de chaque exercice
{exercise.metadata?.is_premium && (
  <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100 border border-purple-300">
    ⭐ SOLUTION PREMIUM
  </Badge>
)}

// Highlight de la solution détaillée
<div className={`solution-container ${
  exercise.metadata?.is_premium 
    ? 'bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200' 
    : 'bg-gray-50'
} p-4 rounded-lg border`}>
  {exercise.metadata?.is_premium && (
    <div className="flex items-center gap-2 mb-3 text-purple-700">
      <Crown className="h-4 w-4" />
      <span className="text-sm font-medium">Solution détaillée Premium</span>
    </div>
  )}
  
  <MathHtmlRenderer html={exercise.solution_html} />
</div>
```

4. **Modal "Découvrir Premium" pour utilisateurs gratuits**

```javascript
// Afficher un modal la première fois qu'un utilisateur gratuit
// clique sur un chapitre premium

const [showPremiumModal, setShowPremiumModal] = useState(false);

// Dans le handler de sélection de chapitre
const handleChapterSelect = (chapter) => {
  if (chapter.is_premium && !isPro) {
    // Première fois seulement (localStorage)
    if (!localStorage.getItem('premiumModalShown')) {
      setShowPremiumModal(true);
      localStorage.setItem('premiumModalShown', 'true');
    } else {
      // Sinon, juste un toast
      toast({
        title: "Chapitre premium",
        description: "Passez Premium pour accéder aux solutions détaillées",
        action: <Button variant="link" onClick={() => navigate('/premium')}>
          Découvrir
        </Button>
      });
    }
    return; // Bloquer l'accès
  }
  
  setSelectedItem(chapter.code_officiel);
};

// Modal component
<Dialog open={showPremiumModal} onOpenChange={setShowPremiumModal}>
  <DialogContent className="max-w-2xl">
    <DialogHeader>
      <DialogTitle className="flex items-center gap-2">
        <Crown className="h-6 w-6 text-purple-600" />
        Découvrez les exercices Premium
      </DialogTitle>
    </DialogHeader>
    
    <div className="space-y-4">
      <p>Les exercices premium offrent :</p>
      <ul className="space-y-2">
        <li className="flex items-start gap-2">
          <Check className="h-5 w-5 text-green-600 mt-0.5" />
          <span><strong>Solutions détaillées</strong> : étapes justifiées prêtes à projeter</span>
        </li>
        <li className="flex items-start gap-2">
          <Check className="h-5 w-5 text-green-600 mt-0.5" />
          <span><strong>Variété infinie</strong> : 3-5 formulations différentes</span>
        </li>
        <li className="flex items-start gap-2">
          <Check className="h-5 w-5 text-green-600 mt-0.5" />
          <span><strong>Gain de temps</strong> : 15 min de correction → 2 min</span>
        </li>
      </ul>
      
      <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
        <p className="text-sm text-purple-900">
          <strong>Offre de lancement :</strong> Essayez Premium 7 jours gratuit
        </p>
      </div>
    </div>
    
    <DialogFooter>
      <Button variant="outline" onClick={() => setShowPremiumModal(false)}>
        Rester en gratuit
      </Button>
      <Button onClick={() => navigate('/premium')} className="bg-purple-600">
        Essayer Premium 7 jours
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

#### Validation

- [ ] Badge "✨ PREMIUM" visible sur chapitres premium
- [ ] Tooltip explicatif au survol
- [ ] Badge "⭐ SOLUTION PREMIUM" sur exercices générés
- [ ] Highlight visuel des solutions premium
- [ ] Modal "Découvrir Premium" fonctionnel
- [ ] Blocage soft des chapitres premium en mode gratuit
- [ ] Toast de rappel si utilisateur gratuit tente d'accéder

---

### P2.3 - 🟡 MOYEN : Créer page "Découvrir Premium"

**Temps estimé**: 1 jour (dev + copywriting)  
**Complexité**: Moyenne  
**Impact**: Moyen (conversion gratuit → premium)

#### Structure de la page `/premium`

```
┌─────────────────────────────────────────────────────────┐
│  [HEADER avec lien "Essayer 7 jours gratuit"]          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  HERO                                                   │
│  ┌─────────────────────────────────────────┐           │
│  │ Le Maître Mot Premium                   │           │
│  │ Solutions détaillées + Variété infinie  │           │
│  │                                         │           │
│  │ [Essayer 7 jours gratuit] [Voir tarifs]│           │
│  └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  COMPARAISON                                            │
│  ┌──────────────┬──────────────┬──────────────┐        │
│  │              │   Gratuit    │   Premium    │        │
│  ├──────────────┼──────────────┼──────────────┤        │
│  │ Génération   │      ✅      │      ✅      │        │
│  │ Solutions    │  Basiques    │  Détaillées  │        │
│  │ Variété      │  Limitée     │   Infinie    │        │
│  │ Exercices    │  50/mois     │   Illimité   │        │
│  │ Support      │    Forum     │ Prioritaire  │        │
│  └──────────────┴──────────────┴──────────────┘        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  EXEMPLES AVANT/APRÈS                                   │
│  ┌─────────────────────────┬─────────────────────────┐ │
│  │ Solution gratuite       │ Solution premium        │ │
│  │ "Réponse : 36"          │ "Étape 1: Calculer..." │ │
│  │                         │ "Étape 2: Multiplier..."│ │
│  │                         │ "Réponse finale : 36"  │ │
│  └─────────────────────────┴─────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  TESTIMONIALS                                           │
│  "Avant Premium, je passais 20 min à corriger.         │
│   Maintenant 5 min." - Marie, prof de 6e               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PRICING                                                │
│  ┌─────────────────────────────────────────┐           │
│  │ Premium : 9€/mois ou 79€/an (-26%)     │           │
│  │ Essai gratuit 7 jours, sans engagement │           │
│  │                                         │           │
│  │ [Essayer 7 jours gratuit]              │           │
│  └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  FAQ                                                    │
│  Q: Puis-je revenir au gratuit ?                       │
│  R: Oui, à tout moment, sans frais.                    │
│                                                         │
│  Q: Quelle différence avec le gratuit ?                │
│  R: Solutions détaillées + variété infinie             │
└─────────────────────────────────────────────────────────┘
```

#### Fichier à créer

`frontend/src/components/PremiumPage.js`

#### Validation

- [ ] Page `/premium` accessible
- [ ] Tableau comparatif visible
- [ ] Exemples avant/après convaincants
- [ ] CTA "Essayer 7 jours" bien visible
- [ ] FAQ complète
- [ ] Liens depuis Header et page génération

---

### P2.4 - 🟡 OPTIONNEL : Implémenter quota gratuit

**Temps estimé**: 1 jour  
**Complexité**: Moyenne-Haute  
**Impact**: Moyen (incitation à payer vs friction initiale)

#### ⚠️ ATTENTION

Cette fonctionnalité peut **freiner l'adoption initiale**. À discuter avec le product owner.

**Alternatives**:
- Pas de quota, juste les générateurs premium réservés
- Quota soft : afficher "X exercices utilisés" sans bloquer
- Quota très large : 200 exercices/mois (peu restrictif)

#### Tâches (si validé)

1. **Backend: Tracking des générations**

```python
# backend/services/quota_service.py (CRÉER)

from datetime import datetime, timedelta
from typing import Optional

class QuotaService:
    """Service de gestion des quotas utilisateurs gratuits."""
    
    # En production: utiliser Redis ou MongoDB
    # En dev: dict en mémoire (simplifié)
    _usage = {}  # {user_id: {month: count}}
    
    QUOTA_FREE_MONTHLY = 50
    
    @classmethod
    def get_usage(cls, user_id: str, month: str = None) -> int:
        """Récupère le nombre d'exercices générés ce mois."""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        
        return cls._usage.get(user_id, {}).get(month, 0)
    
    @classmethod
    def increment_usage(cls, user_id: str) -> int:
        """Incrémente le compteur et retourne la nouvelle valeur."""
        month = datetime.now().strftime("%Y-%m")
        
        if user_id not in cls._usage:
            cls._usage[user_id] = {}
        if month not in cls._usage[user_id]:
            cls._usage[user_id][month] = 0
        
        cls._usage[user_id][month] += 1
        return cls._usage[user_id][month]
    
    @classmethod
    def has_quota(cls, user_id: str, is_pro: bool) -> bool:
        """Vérifie si l'utilisateur a encore du quota."""
        if is_pro:
            return True  # Premium = illimité
        
        usage = cls.get_usage(user_id)
        return usage < cls.QUOTA_FREE_MONTHLY
```

2. **Backend: Middleware de vérification**

```python
# backend/routes/exercises_routes.py

from backend.services.quota_service import QuotaService

@router.post("/generate", ...)
async def generate_exercise(request: ExerciseGenerateRequest):
    # Déterminer user_id (session token, IP, ou anonyme)
    user_id = request.session_token or request.client_ip or "anonymous"
    is_pro = request.offer == "pro"
    
    # Vérifier quota
    if not QuotaService.has_quota(user_id, is_pro):
        raise HTTPException(
            status_code=429,  # Too Many Requests
            detail={
                "error_code": "QUOTA_EXCEEDED",
                "message": "Quota mensuel atteint (50 exercices/mois)",
                "hint": "Passez Premium pour continuer sans limite",
                "context": {
                    "quota_limit": QuotaService.QUOTA_FREE_MONTHLY,
                    "quota_used": QuotaService.get_usage(user_id),
                    "reset_date": "2025-01-01"  # Calculer dynamiquement
                }
            }
        )
    
    # Générer exercice
    result = ...
    
    # Incrémenter compteur
    if not is_pro:
        new_usage = QuotaService.increment_usage(user_id)
        result["metadata"]["quota_remaining"] = (
            QuotaService.QUOTA_FREE_MONTHLY - new_usage
        )
    
    return result
```

3. **Frontend: Affichage du quota**

```javascript
// ExerciseGeneratorPage.js

const [quota, setQuota] = useState({ used: 0, limit: 50 });

// Après chaque génération, mettre à jour depuis metadata
useEffect(() => {
  if (exercises.length > 0 && !isPro) {
    const lastExercise = exercises[exercises.length - 1];
    if (lastExercise.metadata?.quota_remaining !== undefined) {
      setQuota({
        used: 50 - lastExercise.metadata.quota_remaining,
        limit: 50
      });
    }
  }
}, [exercises, isPro]);

// Afficher en haut de page
{!isPro && (
  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
    <div className="flex items-center gap-2">
      <Info className="h-4 w-4 text-blue-600" />
      <span className="text-sm text-blue-900">
        {quota.used}/{quota.limit} exercices utilisés ce mois-ci
      </span>
    </div>
    
    {quota.used >= quota.limit * 0.8 && (
      <Button variant="link" onClick={() => navigate('/premium')}>
        Passer Premium
      </Button>
    )}
  </div>
)}
```

#### Validation

- [ ] Tracking backend fonctionnel
- [ ] Quota affiché côté frontend
- [ ] Blocage à 50 exercices/mois
- [ ] Message d'erreur clair (HTTP 429)
- [ ] CTA "Passer Premium" visible
- [ ] Premium = quota illimité

---

## 📝 RÉSUMÉ DES PRIORITÉS

| Action | Priorité | Temps | Impact | Complexité |
|--------|----------|-------|--------|------------|
| P2.1 - Filtrage premium | 🔴 CRITIQUE | 1-2h | Critique | Faible |
| P2.2 - Badges UI | 🟠 MAJEUR | 4-6h | Fort | Moyenne |
| P2.3 - Page Premium | 🟡 MOYEN | 1j | Moyen | Moyenne |
| P2.4 - Quota | 🟡 OPTIONNEL | 1j | Moyen | Moyenne-Haute |

**Ordre recommandé**:
1. ✅ **P2.1** (urgent, rapide, critique)
2. ✅ **P2.2** (fort impact, visible)
3. ⏸️ **P2.3** (peut attendre copywriting)
4. ❓ **P2.4** (à valider avec product owner)

---

## 🎯 COMMANDES DE VALIDATION

```bash
# P2.1 - Tester filtrage premium
docker compose up -d --build backend
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_SP03", "offer": "free", "seed": 42}' \
  | jq '.metadata.is_premium, .metadata.generator_key'

# Attendu: false, pas "RAISONNEMENT_MULTIPLICATIF_V1"

# P2.2 - Tester badges UI
docker compose up -d --build frontend
# Ouvrir http://localhost:3000/generer
# Vérifier présence badges "✨ PREMIUM"

# P2.3 - Tester page Premium
# Ouvrir http://localhost:3000/premium
# Vérifier contenu et CTA

# P2.4 - Tester quota
# Générer 51 exercices en mode gratuit
# Vérifier blocage au 51e
```

---

## ✅ CHECKLIST FINALE

### Avant le merge

- [ ] P2.1 - Code mis à jour + test passant
- [ ] P2.2 - Badges visibles + modal fonctionnel
- [ ] Documentation utilisateur mise à jour
- [ ] Tests manuels complets
- [ ] Pas de régression sur le gratuit existant

### Avant le lancement premium

- [ ] P2.3 - Page Premium créée et validée
- [ ] P2.4 - Quota implémenté (si validé)
- [ ] Pricing défini
- [ ] Tunnel de paiement Stripe fonctionnel
- [ ] Emails transactionnels configurés
- [ ] Support client préparé

---

**Statut P2**: 📋 **ANALYSE COMPLÉTÉE**

**Prochaine étape**: Valider P2.1 et P2.2 avec l'équipe, puis développer.

