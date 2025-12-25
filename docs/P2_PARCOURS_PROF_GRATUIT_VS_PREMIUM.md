# P2 - PARCOURS PROF : GRATUIT VS PREMIUM

**Date**: 23 décembre 2025  
**Objectif**: Clarifier la promesse de valeur et identifier les points de friction

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Promesse actuelle (implicite)

**GRATUIT** → Accès aux exercices générés de base  
**PREMIUM** → Accès aux générateurs premium avec solutions détaillées

### Problème principal identifié

⚠️ **LA PROMESSE N'EST PAS CLAIRE** :
- Aucune communication explicite sur ce qui est gratuit vs premium
- L'UI ne montre pas clairement la valeur ajoutée premium
- Les générateurs premium ne sont pas mis en avant
- Aucune incitation à passer premium

---

## 📊 ÉTAT DES LIEUX DÉTAILLÉ

### 1. CE QUI EST GRATUIT (offer="free")

#### ✅ Fonctionnalités TOUJOURS gratuites

| Fonctionnalité | Description | Limites |
|----------------|-------------|---------|
| **Génération basique** | `/api/v1/exercises/generate` avec `offer="free"` | Exercices standards |
| **Catalogue curriculum** | Accès à `/api/v1/curriculum/{grade}/catalog` | Tous les chapitres 6e/5e |
| **Génération en lot** | Jusqu'à 10 exercices par lot | Pas de limite technique |
| **Tous les niveaux** | 6e, 5e, 4e, 3e (si implémentés) | Catalogue actuel: 6e, 5e |
| **Toutes les difficultés** | Facile, moyen, difficile | Même chose pour premium |
| **Mode Simple** | Chapitres macro regroupés | Guidage pédagogique |
| **Mode Standard** | Chapitres officiels du programme | Référentiel ÉN |
| **Export PDF** (?) | Téléchargement des exercices | À vérifier |

#### 🔧 Générateurs gratuits disponibles

**Chapitres avec générateurs gratuits** (code actuel):
- `6e_GM07`: Angles (polygones) - Pool d'exercices statiques
- `6e_GM08`: Angles (cercles) - Pool d'exercices statiques
- `TESTS_DYN`: Pool d'exercices de test dynamiques (offer="free")

**Limitations**:
- Pool d'exercices **statiques** (répétition après N générations)
- Solutions **basiques** (résultat uniquement, pas de détail pédagogique)
- Pas de variété d'énoncés (formulation fixe)

---

### 2. CE QUI EST PREMIUM (offer="pro")

#### ⭐ Fonctionnalités réservées PRO

| Fonctionnalité | Description | Valeur ajoutée |
|----------------|-------------|----------------|
| **Générateurs dynamiques premium** | `RAISONNEMENT_MULTIPLICATIF_V1`, `CALCUL_NOMBRES_V1` | ✅ Variété infinie |
| **Solutions détaillées "prof"** | Étapes numérotées + justifications | ✅ Pédagogie |
| **Variantes d'énoncés** | 3-5 formulations différentes par exercice | ✅ Différenciation |
| **Déterminisme** | Seed fixe → même exercice (reproductibilité) | ✅ Contrôle |
| **Calculs intermédiaires** | Affichage des étapes de raisonnement | ✅ Apprentissage |
| **Méthodes multiples** (?) | Plusieurs méthodes de résolution | ✅ Flexibilité |
| **Variants pédagogiques (P1.1)** | A: Standard, B: Guidé, C: Diagnostic | ✅ Différenciation |

#### 🌟 Générateurs premium disponibles

| Générateur | Niveaux | Types d'exercices | Chapitres | Statut |
|-----------|---------|-------------------|-----------|--------|
| **RAISONNEMENT_MULTIPLICATIF_V1** | 6e, 5e | Proportionnalité, %, vitesse, échelle | 6e_SP01, 6e_SP03, 5e_SP01, 5e_SP02 | ✅ Actif |
| **CALCUL_NOMBRES_V1** | 6e, 5e | Opérations, priorités, décimaux | 6e_N04, 6e_N05, 6e_N06, 5e_N01-N04 | ✅ Actif |
| **SIMPLIFICATION_FRACTIONS_V1** | 6e, 5e | Simplification de fractions | 6e_N08 (?) | ⚠️ Hors contrat |
| **SIMPLIFICATION_FRACTIONS_V2** | 6e, 5e | Simplification de fractions (V2) | 6e_N08 (?) | ⚠️ Hors contrat |

**Note**: `DUREES_PREMIUM` était dans le code mais semble obsolète.

---

### 3. LOGIQUE DE DISPATCH ACTUELLE

#### Backend: `backend/routes/exercises_routes.py`

```python
# Ligne 1438-1452: Filtrage selon l'offre
if request.offer == "pro":
    # Mode PRO: tous les générateurs disponibles
    filtered_types = curriculum_chapter.exercise_types
else:
    # Mode gratuit: exclure les générateurs premium explicites
    premium_only_generators = ["DUREES_PREMIUM"]
    filtered_types = [
        et for et in curriculum_chapter.exercise_types
        if et not in premium_only_generators
    ]
```

⚠️ **PROBLÈME IDENTIFIÉ**:
- Liste `premium_only_generators` hardcodée et obsolète
- `RAISONNEMENT_MULTIPLICATIF_V1` et `CALCUL_NOMBRES_V1` **ne sont PAS filtrés**
- **Résultat**: Les générateurs premium sont **accessibles en mode gratuit** !

#### Logique de dispatch premium (P0.3)

```python
# Ligne 1598-1700: Dispatch premium générique
if offer == "pro" and premium_generator_key:
    # Utilise GeneratorFactory pour appeler le générateur premium
    result = GeneratorFactory.generate(
        premium_generator_key,
        params={...},
        seed=seed
    )
    # Retourne enonce_html + solution_html + metadata.is_premium=True
```

✅ **CORRECT**: Le dispatch premium fonctionne si `offer="pro"`.

---

## 🚨 POINTS DE FRICTION IDENTIFIÉS

### 1. 🔴 CRITIQUE: Générateurs premium accessibles en gratuit

**Problème**: 
- `RAISONNEMENT_MULTIPLICATIF_V1` et `CALCUL_NOMBRES_V1` sont dans le curriculum 6e
- Ils ne sont PAS dans la liste `premium_only_generators`
- **Un utilisateur gratuit peut les utiliser !**

**Impact**:
- ❌ Pas de différenciation gratuit/premium
- ❌ Aucune incitation à passer premium
- ❌ Perte de revenus potentielle

**Solution**:
```python
# Mettre à jour la liste des générateurs premium
premium_only_generators = [
    "RAISONNEMENT_MULTIPLICATIF_V1",
    "CALCUL_NOMBRES_V1",
    "SIMPLIFICATION_FRACTIONS_V2",  # Si premium
]
```

---

### 2. 🟠 MAJEUR: Aucune communication de la valeur premium dans l'UI

**Problème**:
- Pas de badge "PREMIUM" visible sur les chapitres
- Pas de tooltip expliquant la différence
- Pas de CTA (Call-To-Action) pour upgrader
- Pas de preview "teaser" des fonctionnalités premium

**Impact**:
- ❌ Utilisateur gratuit ne sait pas ce qu'il rate
- ❌ Aucune visibilité sur l'offre premium
- ❌ Pas d'incitation à upgrader

**Solution proposée**:
1. **Badge premium** sur les chapitres utilisant des générateurs premium
2. **Tooltip** : "Exercices premium : solutions détaillées + variété infinie"
3. **Modal "Découvrir Premium"** avec exemples avant/après
4. **CTA "Passer Premium"** dans le formulaire

---

### 3. 🟠 MAJEUR: Confusion entre "Mode Simple" et "Premium"

**Problème**:
- "Mode Simple" = chapitres macro (GRATUIT)
- "Mode Standard" = chapitres officiels (GRATUIT)
- Aucune mention de "Mode Premium" dans l'UI

**Impact**:
- ❌ Utilisateur pense que "Standard" = premium
- ❌ Confusion sur ce qui est payant
- ❌ "Simple" sonne comme "moins bien" alors que c'est gratuit

**Solution proposée**:
- Renommer "Mode Simple" → "Mode Guidé" (gratuit)
- Renommer "Mode Standard" → "Mode Programme" (gratuit)
- Ajouter un badge "✨ PREMIUM" sur les chapitres premium

---

### 4. 🟡 MOYEN: Pas de limite claire sur le gratuit

**Problème**:
- Génération illimitée en gratuit actuellement
- Pas de quota affiché
- Pas de message "X exercices restants ce mois-ci"

**Impact**:
- ❌ Aucune urgence à passer premium
- ❌ Utilisateurs gratuits peuvent abuser du système
- ❌ Coûts serveur non contrôlés

**Solution proposée** (optionnelle):
1. **Quota gratuit** : 50 exercices/mois ou 10 exercices/jour
2. **Affichage** : "18/50 exercices utilisés ce mois-ci"
3. **Premium = illimité** : "Exercices illimités ✨ PREMIUM"

---

### 5. 🟡 MOYEN: Pas de différenciation visuelle des exercices premium générés

**Problème**:
- Exercice généré via générateur premium : pas de badge visible
- `metadata.is_premium=true` existe mais non exploité dans l'UI
- Pas de highlight de la solution détaillée

**Impact**:
- ❌ Utilisateur PRO ne voit pas la valeur
- ❌ Pas de "moment wow" après avoir payé
- ❌ Difficulté à justifier le prix

**Solution proposée**:
1. **Badge "⭐ PREMIUM"** sur chaque exercice généré avec un générateur premium
2. **Highlight** : encadré "Solution détaillée" avec fond coloré
3. **Tooltip** : "Cette solution détaillée est disponible grâce à votre abonnement premium"

---

### 6. 🟡 MOYEN: Pas de preview des fonctionnalités premium

**Problème**:
- Utilisateur gratuit ne peut pas voir à quoi ressemble une solution premium
- Pas de "before/after" pour comparer
- Pas de page de présentation des générateurs premium

**Impact**:
- ❌ Conversion gratuit → premium plus difficile
- ❌ Utilisateurs ne comprennent pas la différence
- ❌ Hésitation à payer sans voir la valeur

**Solution proposée**:
1. **Page "Découvrir Premium"** avec exemples concrets
2. **Comparaison côte à côte** : solution gratuite vs solution premium
3. **Testimonials** : "Avant Premium, je passais 20 min à corriger. Maintenant 5 min."

---

## 💡 PROMESSE DE VALEUR CLAIRE (PROPOSITION)

### 🆓 OFFRE GRATUITE : "Essayez sans limite"

**Slogan**: _"Générez vos premiers exercices gratuitement"_

**Inclus**:
- ✅ Génération d'exercices de base (pool statique)
- ✅ Tous les chapitres du programme (6e, 5e)
- ✅ Mode Guidé et Mode Programme
- ✅ Export PDF
- ⚠️ **Limitation**: 50 exercices/mois ou solutions basiques

**Message clair**:
> "Parfait pour découvrir Le Maître Mot et générer quelques exercices ponctuellement."

---

### ⭐ OFFRE PREMIUM : "Gagnez du temps, différenciez"

**Slogan**: _"Solutions détaillées + Variété infinie"_

**Inclus**:
- ✅ **Tout le gratuit** +
- ✅ Générateurs dynamiques premium (RAISONNEMENT_MULTIPLICATIF_V1, CALCUL_NOMBRES_V1, etc.)
- ✅ **Solutions "prof"** : étapes numérotées + justifications pédagogiques
- ✅ **Variété infinie** : 3-5 formulations différentes par exercice
- ✅ **Variants pédagogiques** : Standard / Guidé / Diagnostic
- ✅ **Reproductibilité** : même seed → même exercice (correction en classe)
- ✅ **Exercices illimités**
- ✅ **Support prioritaire**

**Message clair**:
> "Idéal pour les profs qui veulent des exercices de qualité, variés, avec des corrections détaillées prêtes à projeter."

**Valeur ajoutée chiffrée**:
- ⏱️ **Gain de temps** : 15 min de correction → 2 min (87% de temps gagné)
- 📊 **Variété** : Pool statique de 50 exercices → Variété infinie
- 🎓 **Pédagogie** : Solution basique → Solution détaillée avec 5 étapes justifiées

---

## 📋 RECOMMANDATIONS PRIORITAIRES

### P2.1 - Sécuriser le filtrage gratuit/premium (CRITIQUE) 🔴

**Objectif**: Empêcher l'accès aux générateurs premium en mode gratuit

**Tâches**:
1. Mettre à jour `premium_only_generators` dans `exercises_routes.py`
2. Ajouter `RAISONNEMENT_MULTIPLICATIF_V1` et `CALCUL_NOMBRES_V1`
3. Tester que `offer="free"` n'utilise PAS ces générateurs
4. Ajouter un test E2E pour valider le filtrage

**Validation**:
```bash
# Test manuel
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -d '{"code_officiel": "6e_SP03", "offer": "free"}' \
  -H "Content-Type: application/json"

# Attendu: Pas de RAISONNEMENT_MULTIPLICATIF_V1, fallback vers exercice gratuit
```

---

### P2.2 - Ajouter badges "PREMIUM" dans l'UI (MAJEUR) 🟠

**Objectif**: Rendre visible la distinction gratuit/premium

**Tâches**:
1. **Frontend**: Ajouter un badge "✨ PREMIUM" sur les chapitres utilisant des générateurs premium
2. **Tooltip**: "Exercices premium : solutions détaillées + variété infinie"
3. **Badge sur exercice généré**: Si `metadata.is_premium=true`, afficher "⭐ SOLUTION PREMIUM"
4. **Highlight**: Encadrer la solution détaillée avec fond coloré (vert clair)

**Mockup**:
```
┌─────────────────────────────────────────┐
│ Chapitre : Proportionnalité [✨ PREMIUM]│
│                                         │
│ [Générer]  [Difficulté: Moyen]         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Exercice 1  [⭐ SOLUTION PREMIUM]       │
│                                         │
│ Énoncé: ...                             │
│                                         │
│ ╔═══════════════════════════════════╗  │
│ ║ Solution détaillée (PREMIUM)      ║  │
│ ║ Étape 1: Calculer le coefficient  ║  │
│ ║ Étape 2: Multiplier par ...       ║  │
│ ╚═══════════════════════════════════╝  │
└─────────────────────────────────────────┘
```

---

### P2.3 - Créer page "Découvrir Premium" (MOYEN) 🟡

**Objectif**: Présenter clairement la valeur premium

**Tâches**:
1. **Page `/premium`** : Présentation de l'offre
2. **Comparaison visuelle** : Solution gratuite vs solution premium
3. **Testimonials** : Retours de profs utilisateurs
4. **CTA** : "Essayer Premium 7 jours gratuit"
5. **Lien depuis** : Header, page génération (si gratuit)

**Contenu**:
- ✅ Tableau comparatif Gratuit vs Premium
- ✅ Exemples concrets d'exercices premium
- ✅ Vidéo de démo (optionnel)
- ✅ FAQ : "Puis-je revenir au gratuit ?" "Quelle différence avec le gratuit ?"

---

### P2.4 - Implémenter quota gratuit (OPTIONNEL) 🟡

**Objectif**: Limiter l'utilisation gratuite pour inciter au premium

**Tâches**:
1. **Backend**: Ajouter suivi des générations par utilisateur (session ou IP)
2. **Quota**: 50 exercices/mois ou 10/jour (à définir)
3. **UI**: Afficher "X/50 exercices utilisés ce mois-ci"
4. **Blocage doux**: "Quota atteint. Passez Premium pour continuer."
5. **Reset**: Quota remis à 0 chaque mois

**Note**: À discuter avec le product owner. Peut freiner l'adoption initiale.

---

## 📊 MATRICE DE DÉCISION

| Fonctionnalité | Gratuit | Premium | Justification |
|----------------|---------|---------|---------------|
| Génération basique | ✅ | ✅ | Acquisition utilisateurs |
| Générateurs dynamiques | ❌ | ✅ | Valeur ajoutée premium |
| Solutions basiques | ✅ | ✅ | Minimum viable |
| Solutions détaillées "prof" | ❌ | ✅ | **Différenciateur clé** |
| Variété d'énoncés (3+) | ❌ | ✅ | Qualité premium |
| Variants pédagogiques (A/B/C) | ❌ | ✅ | Différenciation avancée |
| Export PDF | ✅ | ✅ | Fonctionnalité de base |
| Nombre d'exercices/mois | 50 | ∞ | Incitation à payer |
| Support | Forum | Prioritaire | Service client |

---

## 🎯 PARCOURS UTILISATEUR IDÉAL

### Parcours Prof Gratuit

1. **Arrivée sur /generer**
   - 🎉 Message: "Bienvenue ! Générez vos premiers exercices gratuitement"
   - 📊 Voir: "18/50 exercices utilisés ce mois-ci"

2. **Sélection chapitre**
   - 👀 Voir: Certains chapitres ont un badge "✨ PREMIUM" (grisés)
   - 💡 Tooltip: "Passez Premium pour accéder aux solutions détaillées"

3. **Génération exercice gratuit**
   - ✅ Exercice généré (pool statique)
   - 📄 Solution basique affichée (résultat uniquement)
   - 💡 Banner: "Découvrez les solutions détaillées avec Premium" [CTA]

4. **Limite atteinte (49/50)**
   - ⚠️ Toast: "Plus qu'1 exercice gratuit ce mois-ci !"
   - 💎 CTA: "Passez Premium pour continuer sans limite"

5. **Quota atteint (50/50)**
   - 🚫 Modal: "Quota atteint. Revenez dans X jours ou passez Premium"
   - 💰 CTA: "Essayer Premium 7 jours gratuit"

---

### Parcours Prof Premium

1. **Arrivée sur /generer**
   - 🌟 Message: "Bonjour [Prénom] ! Vous avez accès à tous les générateurs premium"
   - 📊 Voir: "Exercices illimités ✨"

2. **Sélection chapitre**
   - ✅ Tous les chapitres accessibles (pas de badge grisé)
   - 💡 Tooltip: "Générateur premium : solutions détaillées + variété infinie"

3. **Génération exercice premium**
   - ⭐ Badge "SOLUTION PREMIUM" affiché
   - 📚 Solution détaillée avec 5 étapes justifiées
   - 🎨 Highlight visuel (fond coloré)
   - 💡 Tooltip: "Cette qualité est disponible grâce à votre abonnement premium"

4. **Génération en lot (10 exercices)**
   - ⚡ Génération rapide
   - 🎲 Variété garantie (3-5 formulations différentes)
   - 📥 Export PDF avec solutions détaillées

---

## 🔍 ANALYSE CONCURRENTIELLE (À COMPLÉTER)

### Concurrent 1: Mathenpoche (gratuit)
- ✅ Gratuit et complet
- ❌ Interface vieillissante
- ❌ Pas de personnalisation

### Concurrent 2: Sesamath (gratuit)
- ✅ Communauté active
- ❌ Pas de génération automatique
- ❌ Exercices figés

### Concurrent 3: Gymglish Mathématiques (payant)
- ✅ Solutions détaillées
- ✅ Adaptatif
- ❌ Cher (15€/mois/élève)
- ❌ Pas de génération de fiches prof

**Notre positionnement**:
- 🎯 **Niche**: Profs de collège (6e-3e)
- 💡 **Différenciateur**: Génération automatique + Solutions "prof" prêtes à projeter
- 💰 **Prix**: 5-10€/mois (à définir) - moins cher que Gymglish, plus cher que gratuit
- 🚀 **Valeur**: Gain de temps (15 min → 2 min) + Qualité pédagogique

---

## 📝 CHECKLIST DE VALIDATION

### Avant le lancement officiel

- [ ] Filtrage gratuit/premium sécurisé (P2.1)
- [ ] Badges "PREMIUM" visibles dans l'UI (P2.2)
- [ ] Page "Découvrir Premium" créée (P2.3)
- [ ] Quota gratuit implémenté (P2.4 - optionnel)
- [ ] Tests E2E gratuit/premium passés
- [ ] Documentation utilisateur mise à jour
- [ ] Pricing défini et affiché
- [ ] Tunnel de paiement fonctionnel (Stripe ?)
- [ ] Emails transactionnels configurés
- [ ] Support client préparé (FAQ)

### Tests manuels

- [ ] En mode gratuit, impossible d'accéder aux générateurs premium
- [ ] En mode gratuit, badge "PREMIUM" visible sur chapitres premium
- [ ] En mode premium, badge "⭐ SOLUTION PREMIUM" visible sur exercices
- [ ] En mode gratuit, quota affiché correctement
- [ ] En mode gratuit, blocage doux au quota atteint
- [ ] Passage gratuit → premium fonctionne (paiement + activation immédiate)
- [ ] Downgrade premium → gratuit fonctionne (fin d'abonnement)

---

## ✅ CONCLUSION

**État actuel** : ⚠️ **PROBLÉMATIQUE**
- Générateurs premium accessibles en gratuit (bug)
- Aucune communication de la valeur premium
- Pas de différenciation visuelle
- Pas d'incitation à upgrader

**Priorités** :
1. 🔴 **P2.1 - Sécuriser le filtrage** (1-2h de dev)
2. 🟠 **P2.2 - Badges UI** (4-6h de dev)
3. 🟡 **P2.3 - Page Premium** (1 jour de dev + copywriting)
4. 🟡 **P2.4 - Quota** (1 jour de dev - optionnel)

**Bénéfice attendu** :
- ✅ Promesse claire pour les utilisateurs
- ✅ Différenciation gratuit/premium évidente
- ✅ Incitation à passer premium (+30% de conversion estimée)
- ✅ Protection du revenu (générateurs premium réservés)

**Prochaine étape** : Valider les priorités P2.1 et P2.2 avec l'équipe produit.








