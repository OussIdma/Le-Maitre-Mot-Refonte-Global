# 🎯 DIAGNOSTIC CTO COMPLET - LE MAÎTRE MOT

**Date**: 2 janvier 2026  
**Analyste**: Agent CTO/Architecte  
**Version analysée**: v16 - Refonte locale  
**Objectif**: Repartir sur de bons pieds pour une V1 monétisable rapidement

---

## 1. RÉSUMÉ EXÉCUTIF (10 lignes max)

Le projet "Le Maître Mot" est un générateur d'exercices scolaires (math V1) avec une architecture FastAPI + React + MongoDB. **État global : ~65% fonctionnel**. Les générateurs dynamiques Python fonctionnent (16 générateurs, 100% tests unitaires OK), mais l'intégration end-to-end présente des fragilités. **3 problèmes critiques identifiés** : (1) fallback silencieux frontend DB→catalogue non-traité, (2) wrapping HTML `<p>` sur contenu déjà block-level, (3) UI hardcodée pour 2 générateurs seulement. Le panier local fonctionne, l'export PDF existe mais n'est pas encore derrière un paywall. **Recommandation** : 2-3 jours de P0 pour stabiliser, puis 3-5 jours de P1 pour le MVP monétisable.

---

## 2. CARTE DU PROJET & FLUX

### 2.1 Structure des fichiers

```
/projet
├── backend/                      # FastAPI + Python (5.1MB)
│   ├── server.py                 # Point d'entrée (6915 lignes!)
│   ├── routes/                   # API endpoints
│   │   ├── exercises_routes.py   # 🔴 CRITIQUE (3024 lignes - génération élève)
│   │   ├── admin_exercises_routes.py  # CRUD admin
│   │   ├── mathalea_routes.py    # Export PDF/fiche
│   │   └── catalogue_routes.py   # Curriculum read-only
│   ├── generators/               # 🟢 Cœur métier - 16 générateurs
│   │   ├── factory.py            # Registry central
│   │   ├── base_generator.py     # Classe abstraite
│   │   ├── thales_v2.py          # Exemple: agrandissement/réduction
│   │   └── [14 autres]           # calcul, fractions, périmètre, etc.
│   ├── services/                 # Logique métier
│   │   ├── math_generation_service.py  # Calculs Python purs
│   │   ├── template_renderer.py  # Rendu Mustache {{var}}
│   │   └── exercise_persistence_service.py  # CRUD MongoDB
│   ├── models/                   # Pydantic schemas
│   └── tests/                    # 100+ fichiers de tests
│
├── frontend/                     # React + Tailwind (1.1MB src)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ExerciseGeneratorPage.js  # 🔴 Page principale (1639 lignes)
│   │   │   ├── SheetBuilderPage.js       # Panier/Export PDF
│   │   │   └── admin/                    # Interface admin
│   │   ├── hooks/
│   │   │   ├── useCurriculumChapters.js  # 🟡 Fallback silencieux ici
│   │   │   └── useAuth.js                # Authentification
│   │   └── contexts/
│   │       └── SelectionContext.js       # État panier local
│
├── docker-compose.yml            # Infra locale
├── scripts/healthcheck.sh        # Tests smoke de base
└── docs/                         # 150+ fichiers de documentation
```

### 2.2 Flux de données principal

```
┌─────────────────┐     POST /api/v1/exercises/generate
│   FRONTEND      │────────────────────────────────────────────┐
│ ExerciseGenerator│                                           │
│     Page.js     │◄──────────────────────────────────────────┐│
└─────────────────┘     JSON {id, enonce_html, solution_html} ││
                                                              ││
                    ┌─────────────────────────────────────────┼┤
                    │           BACKEND (FastAPI)             ││
                    │                                         ││
                    │  ┌──────────────────────────────────┐   ││
                    │  │  exercises_routes.py             │   ││
                    │  │  1. Lookup chapitre en DB        │   ││
                    │  │  2. Sélection générateur         │   ││
                    │  │  3. GeneratorFactory.generate()  │───┼┘
                    │  │  4. Template rendering           │   │
                    │  │  5. Retour exercice complet      │   │
                    │  └──────────────────────────────────┘   │
                    │                                         │
                    │  ┌──────────────────────────────────┐   │
                    │  │  generators/factory.py           │   │
                    │  │  - Registry de 16 générateurs    │   │
                    │  │  - Fusion params (defaults+user) │   │
                    │  │  - Validation stricte            │   │
                    │  └──────────────────────────────────┘   │
                    │                                         │
                    │  ┌──────────────────────────────────┐   │
                    │  │       MongoDB                    │   │
                    │  │  - curriculum_chapters           │   │
                    │  │  - admin_exercises               │   │
                    │  │  - user_exercises (panier sync)  │   │
                    │  └──────────────────────────────────┘   │
                    └─────────────────────────────────────────┘
```

---

## 3. DIAGNOSTIC : OK / KO / ZONES GRISES

### 3.1 ✅ CE QUI MARCHE (OK)

| Composant | Fichier(s) | Preuve |
|-----------|-----------|--------|
| **16 générateurs Python** | `generators/*.py` | Tests unitaires 100% pass |
| **Factory centralisée** | `generators/factory.py` | Schema-driven, presets, validation stricte |
| **Rendu templates Mustache** | `services/template_renderer.py` | {{var}} → valeurs |
| **API génération exercice** | `/api/v1/exercises/generate` | healthcheck.sh valide |
| **Preview admin** | `/api/admin/exercises/preview-dynamic` | healthcheck.sh valide |
| **MongoDB comme source** | `admin_exercises`, `curriculum_chapters` | Collections utilisées |
| **Panier local (Composer)** | `SelectionContext.js` | localStorage fonctionne |
| **Export PDF basique** | `mathalea_routes.py` | PDF généré (WeasyPrint) |
| **Authentification magic link** | `secure_auth_service.py` | Fonctionnel |
| **SVG géométrie** | `geometry_svg_renderer.py` | Figures générées |

### 3.2 ❌ CE QUI CASSE (KO) - CONFIRMÉ PAR LECTURE DE CODE

| Problème | Fichier(s) + Ligne | Symptôme | Impact |
|----------|-------------------|----------|--------|
| **Fallback silencieux frontend** | `hooks/useCurriculumChapters.js:56-70` | Si `/api/admin/curriculum/{niveau}` échoue, fallback sur `/api/catalogue/...` dans un `catch` sans notification | Incohérences sources de vérité, debugging impossible |
| **HTML wrapping bug** | `routes/exercises_routes.py:860` | `html = f"<div class='exercise-enonce'><p>{enonce}</p>"` wrappe TOUJOURS dans `<p>`, même si l'énoncé contient `<table>` ou `<div>` | HTML invalide (`<p><table>` interdit), rendu cassé |
| **UI générateurs hardcodée** | `ExerciseGeneratorPage.js:1210-1244` | Sélecteur conditionnel `if (detectedGenerator === "CALCUL_NOMBRES_V1")` et `if (detectedGenerator === "RAISONNEMENT_MULTIPLICATIF_V1")` - SEULEMENT 2 générateurs sur 16 | 87% des générateurs inaccessibles à l'utilisateur |
| **Pas de paywall export** | `mathalea_routes.py` | Export PDF sans vérification quota/premium effective | Pas de monétisation V1 |

### 3.3 🟡 ZONES GRISES (à tester)

| Zone | Fichier(s) | Question | Test simple |
|------|-----------|----------|-------------|
| **Sync panier cross-device** | `user_exercises` collection | Le panier local se sync-t-il après login ? | `curl POST /api/mathalea/user/exercises` puis vérifier DB |
| **Quota exports free** | `access_control.py` | Les quotas sont-ils appliqués ? | Créer user free, exporter 4 PDF |
| **Pipeline par chapitre** | `curriculum_chapters.pipeline` | Tous les chapitres ont-ils un pipeline défini ? | Query DB : `db.curriculum_chapters.find({pipeline: null})` |
| **Templates dynamiques admin** | `admin_template_routes.py` | L'édition de template se persist-elle ? | PUT puis GET et comparer |
| **Difficultés mapping** | `difficulty_utils.py` | "moyen" frontend = "moyen" générateur ? | Générer avec chaque niveau, vérifier |

---

## 4. MVP V1 : SCOPE IN/OUT + DEFINITION OF DONE

### 4.1 SCOPE IN (livrable V1)

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| ✅ Génération exercices | Visiteur choisit niveau/chapitre → génère exercices | P0 |
| ✅ Bouton "Régénérer données" | Même template, nouveau seed | P0 |
| ✅ Bouton "Nouvel exercice" | Autre template/variant | P0 |
| ✅ Panier local | Stockage navigateur, pas de sync | P0 |
| ✅ Export PDF | Sujet + corrigé depuis panier | P1 |
| ✅ Paywall export | Compte gratuit = quotas, Premium = illimité | P1 |
| ✅ Création compte | Email + magic link (déjà implémenté) | P1 |
| 🆕 UI dynamique générateurs | Afficher tous les générateurs disponibles pour un chapitre | P1 |

### 4.2 SCOPE OUT (post-V1)

| Fonctionnalité | Raison |
|----------------|--------|
| Sync panier cross-device | Complexité, localStorage suffit pour V1 |
| Variantes de fiches (même exos, seeds différents) | Feature premium avancée |
| IA pour enrichissement texte | Déjà en place mais optionnel |
| Export sans branding (premium) | Post-lancement |
| Multi-matières (Physique, SVT...) | Math d'abord |

### 4.3 DEFINITION OF DONE V1

```
□ Smoke tests passent (healthcheck.sh étendu)
□ Génération 6e fonctionne pour 5 chapitres pilotes
□ Export PDF sujet+corrigé fonctionne
□ Paywall bloque export après 3 PDF/jour pour free
□ Pas de placeholders {{...}} visibles dans les exercices
□ Pas d'erreurs 500 dans les logs pendant 30 min de test manuel
□ Aucun fallback silencieux activé (logs vérifiés)
□ Frontend affiche dynamiquement les générateurs par chapitre
```

---

## 5. PLAN P0/P1/P2 (IMPACT/EFFORT/RISQUE/FICHIERS/TESTS)

### 5.1 P0 - Aujourd'hui/1 journée : STABILISER

| Tâche | Impact | Effort | Risque | Fichiers | Validation |
|-------|--------|--------|--------|----------|------------|
| **P0.1** Supprimer fallback silencieux frontend | 🔴 Critique | 30min | Faible | `useCurriculumChapters.js` | Error explicite si API fail |
| **P0.2** Fix HTML wrapping bug | 🔴 Critique | 1h | Moyen | `exercises_routes.py`, `template_renderer.py` | Pas de `<p><table>` dans output |
| **P0.3** Vérifier tous les chapitres ont `pipeline` | 🟡 Important | 30min | Faible | Script + Migration | Query DB retourne 0 |
| **P0.4** Activer logs explicites pour diagnostics | 🟢 Nice | 30min | Faible | `observability/logger.py` | Logs structurés JSON |
| **P0.5** Étendre healthcheck.sh | 🟡 Important | 1h | Faible | `scripts/healthcheck.sh` | 10+ tests automatisés |

### 5.2 P1 - 2-5 jours : V1 MONÉTISABLE

| Tâche | Impact | Effort | Risque | Fichiers | Validation |
|-------|--------|--------|--------|----------|------------|
| **P1.1** Paywall export PDF | 🔴 Critique | 4h | Moyen | `mathalea_routes.py`, `access_control.py` | Free bloqué après 3 exports |
| **P1.2** UI dynamique générateurs | 🔴 Critique | 4h | Moyen | `ExerciseGeneratorPage.js` | Affiche N générateurs, pas 2 |
| **P1.3** Endpoint /chapters/{code}/generators | 🟡 Important | 2h | Faible | `generators_routes.py` | Retourne liste générateurs actifs |
| **P1.4** Tests E2E Playwright | 🟡 Important | 6h | Moyen | `tests/e2e/` | Flow complet visiteur → export |
| **P1.5** Page pricing + checkout | 🟡 Important | 4h | Faible | `PricingPage.js`, `CheckoutPage.js` | Stripe fonctionnel |

### 5.3 P2 - 1-2 semaines : DURCIR

| Tâche | Impact | Effort | Risque | Fichiers | Validation |
|-------|--------|--------|--------|----------|------------|
| **P2.1** Monitoring production | 🟡 Important | 1j | Faible | Sentry, logs | Alertes sur erreurs |
| **P2.2** Backup MongoDB automatique | 🟡 Important | 2h | Faible | Script cron | Dump quotidien |
| **P2.3** Rate limiting API | 🟢 Nice | 2h | Faible | `server.py` (slowapi) | Déjà présent, vérifier config |
| **P2.4** Documentation API OpenAPI | 🟢 Nice | 4h | Faible | Annotations routes | /docs complet |
| **P2.5** CI/CD GitHub Actions | 🟡 Important | 1j | Moyen | `.github/workflows/` | Tests auto sur PR |

---

## 6. SMOKE TESTS COPIABLES

### 6.1 Commandes de base (utilise healthcheck.sh existant)

```bash
# 1. Démarrer l'environnement
docker compose up --build -d

# 2. Attendre que les services soient prêts (30s)
sleep 30

# 3. Exécuter le healthcheck existant
./scripts/healthcheck.sh http://localhost:8000
```

### 6.2 Tests étendus (à ajouter)

```bash
#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://localhost:8000}"

echo "=== SMOKE TESTS ÉTENDUS V1 ==="

# Test 1: API health
echo "1) GET /docs (OpenAPI)"
curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs" | grep -q "200" && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Catalogue chapitres 6e
echo "2) GET /api/admin/curriculum/6e"
curl -s "${BASE_URL}/api/admin/curriculum/6e" | jq -e '.chapitres | length > 0' && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Génération exercice simple
echo "3) POST /api/v1/exercises/generate (6e_GM07)"
RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_GM07","difficulte":"facile","offer":"free","seed":42}' \
  "${BASE_URL}/api/v1/exercises/generate")
echo "$RESULT" | jq -e '.enonce_html | length > 10' && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: Pas de placeholders non résolus
echo "4) Check no {{placeholders}} in output"
echo "$RESULT" | grep -q '{{' && echo "❌ FAIL - Placeholders trouvés!" || echo "✅ PASS"

# Test 5: SVG présent si géométrie
echo "5) Check SVG for geometry exercises"
GEOM_RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_GM08","difficulte":"facile","offer":"free","seed":42}' \
  "${BASE_URL}/api/v1/exercises/generate")
echo "$GEOM_RESULT" | jq -e '.figure_svg_enonce != null or .needs_svg == false' && echo "✅ PASS" || echo "⚠️ CHECK"

# Test 6: Preview admin
echo "6) POST /api/admin/exercises/preview-dynamic"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"generator_key":"THALES_V2","difficulty":"facile","seed":1}' \
  "${BASE_URL}/api/admin/exercises/preview-dynamic" | jq -e '.enonce_html' && echo "✅ PASS" || echo "❌ FAIL"

# Test 7: Liste des générateurs
echo "7) GET /api/v1/exercises/generators"
curl -s "${BASE_URL}/api/v1/exercises/generators" | jq -e 'length >= 10' && echo "✅ PASS" || echo "❌ FAIL"

# Test 8: Export PDF (sans auth = devrait échouer ou limiter)
echo "8) POST /api/mathalea/sheets/export (no auth)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" \
  -d '{"items":[],"title":"Test","layout":"academique"}' \
  "${BASE_URL}/api/mathalea/sheets/export")
[ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ] && echo "✅ PASS (auth required)" || echo "⚠️ CHECK ($HTTP_CODE)"

# Test 9: MongoDB connecté
echo "9) Check MongoDB connection"
curl -s "${BASE_URL}/api/debug/build" | jq -e '.database == "connected"' && echo "✅ PASS" || echo "❌ FAIL"

# Test 10: Pas d'erreurs 500 dans les tests précédents
echo "10) No 500 errors logged"
docker logs le-maitre-mot-backend 2>&1 | tail -50 | grep -q "500 Internal Server Error" && echo "❌ FAIL" || echo "✅ PASS"

echo "=== FIN DES TESTS ==="
```

### 6.3 Test rapide fallback (à exécuter manuellement)

```javascript
// Dans la console du navigateur sur http://localhost:3000
// Vérifier que le hook ne fait pas de fallback silencieux

// 1. Ouvrir Network tab
// 2. Sélectionner niveau "6e"
// 3. Vérifier qu'UN SEUL appel API est fait (pas de retry sur /catalogue)
// 4. Si deux appels : le bug du fallback silencieux est présent
```

---

## 7. TABLEAU FONCTIONNALITÉ → ÉTAT → TEST → FIX

| Fonctionnalité | État | Comment tester | Fix recommandé |
|----------------|------|----------------|----------------|
| **Génération exercice élève** | ✅ OK | `curl POST /api/v1/exercises/generate` | - |
| **Preview admin** | ✅ OK | `curl POST /api/admin/exercises/preview-dynamic` | - |
| **Panier local** | ✅ OK | Ajouter exercice, reload page, vérifier présent | - |
| **Export PDF** | 🟡 Partiel | `curl POST /api/mathalea/sheets/export` avec auth | Ajouter paywall P1.1 |
| **Paywall/Quotas** | ❌ KO | Exporter 10 PDF en free, devrait bloquer | Implémenter `access_control.py` |
| **UI liste générateurs** | ❌ KO | Ouvrir page, compter générateurs affichés | Rendre dynamique depuis `/generators` |
| **Fallback DB→catalogue** | ❌ KO | Couper `/api/admin/curriculum`, voir comportement | Supprimer fallback, afficher erreur |
| **HTML wrapping** | ❌ KO | Générer exercice avec `<table>`, inspecter HTML | Ne pas wrapper si déjà block |
| **Sync panier après login** | 🟡 Incertain | Login, vérifier `user_exercises` en DB | Tester manuellement |
| **Difficultés mapping** | 🟡 Incertain | Générer avec `facile/moyen/difficile`, vérifier output | Audit `difficulty_utils.py` |
| **SVG dans PDF** | ✅ OK | Exporter PDF avec figure, ouvrir et vérifier | - |
| **Auth magic link** | ✅ OK | Demander lien, cliquer, vérifier session | - |
| **CRUD admin exercices** | ✅ OK | `GET/POST/PUT/DELETE /api/admin/chapters/{code}/exercises` | - |
| **Import/Export package** | 🟡 Incertain | `POST /api/admin/package/export` | Tester manuellement |

---

## 8. QUESTIONS RESTANTES (MAX 5)

1. **Stripe est-il configuré en production ?**  
   → Vérifier `STRIPE_SECRET_KEY` et `STRIPE_WEBHOOK_SECRET` dans les env vars.

2. **Les migrations DB sont-elles toutes appliquées ?**  
   → Exécuter `ls backend/migrations/` et vérifier chaque `00X_` a été run.

3. **Quel est le domaine de déploiement prévu ?**  
   → Impacte CORS, cookies, et redirections auth.

4. **Y a-t-il des exercices "cassés" en DB à nettoyer ?**  
   → Query : `db.admin_exercises.find({enonce_html: {$regex: "{{"}})`.

5. **Faut-il supporter IE11 ou navigateurs anciens ?**  
   → Impacte les polyfills et la taille du bundle React.

---

## ANNEXE A : CORRECTIFS DÉTAILLÉS

### A.1 Fix Fallback Silencieux (P0.1)

**Fichier**: `frontend/src/hooks/useCurriculumChapters.js`

```javascript
// AVANT (lignes 56-70) - MAUVAIS
} catch (err) {
  // Fallback sur l'API catalogue
  const response = await axios.get(`${API}/catalogue/levels/${niveauToLoad}/chapters`);
  // ...
}

// APRÈS - CORRECT
} catch (err) {
  console.error('❌ API curriculum indisponible:', err);
  setError(err.response?.data?.detail || 'Impossible de charger les chapitres - Vérifiez votre connexion');
  setChapters([]);
  // PAS DE FALLBACK - L'erreur doit être visible
  return;
}
```

### A.2 Fix HTML Wrapping (P0.2)

**Fichier**: `backend/routes/exercises_routes.py` - Ligne 842-868

**Code actuel (bugué):**
```python
# Ligne 860 - MAUVAIS
html = f"<div class='exercise-enonce'><p>{enonce}</p>"
```

**Correctif:**
```python
import re

def is_block_level_html(html: str) -> bool:
    """Détecte si le HTML contient déjà des éléments block-level."""
    block_tags = r'<(div|table|ul|ol|h[1-6]|p|blockquote|pre|figure|section|article)[^>]*>'
    return bool(re.search(block_tags, html, re.IGNORECASE))

def build_enonce_html(enonce: str, svg: Optional[str] = None) -> str:
    """
    Construit l'énoncé HTML à partir de l'énoncé texte et du SVG.
    NE wrappe PAS dans <p> si le contenu est déjà block-level.
    """
    html = "<div class='exercise-enonce'>"
    
    # Wrapper dans <p> SEULEMENT si le contenu n'est pas déjà block-level
    if is_block_level_html(enonce):
        html += enonce  # Déjà formaté, pas de wrapper
    else:
        html += f"<p>{enonce}</p>"  # Texte simple, wrapper OK
    
    if svg:
        html += f"<div class='exercise-figure'>{svg}</div>"
    
    html += "</div>"
    return html
```

**Test de validation:**
```python
# Test 1: texte simple -> doit être wrappé
assert "<p>Calculer" in build_enonce_html("Calculer 2+2")

# Test 2: table -> NE doit PAS être wrappé dans <p>
table_html = "<table><tr><td>1</td></tr></table>"
result = build_enonce_html(table_html)
assert "<p><table>" not in result  # Invalide
assert "<div class='exercise-enonce'><table>" in result  # Correct
```

### A.3 UI Dynamique Générateurs (P1.2)

**Fichier**: `frontend/src/components/ExerciseGeneratorPage.js`

**Code actuel (hardcodé) - Lignes 1210-1245:**
```javascript
// MAUVAIS - seulement 2 générateurs hardcodés
{detectedGenerator === "CALCUL_NOMBRES_V1" && (
  <Select ...>
    <SelectItem value="operations_simples">...</SelectItem>
    // ...
  </Select>
)}
{detectedGenerator === "RAISONNEMENT_MULTIPLICATIF_V1" && (
  <Select ...>
    // ...
  </Select>
)}
```

**Correctif - Approche schema-driven:**

1. **Ajouter un état pour les générateurs disponibles:**
```javascript
// Après ligne 154
const [availableGenerators, setAvailableGenerators] = useState([]);
const [selectedGenerator, setSelectedGenerator] = useState(null);
```

2. **Charger les générateurs quand le chapitre change:**
```javascript
// Ajouter un useEffect après la ligne 371
useEffect(() => {
  const loadGenerators = async () => {
    if (!selectedItem || selectedItem.startsWith("macro:")) {
      setAvailableGenerators([]);
      return;
    }
    
    try {
      // Trouver le chapitre dans le catalogue
      const chapter = catalog?.domains
        ?.flatMap(d => d.chapters)
        ?.find(ch => ch.code_officiel === selectedItem);
      
      if (chapter?.generators?.length > 0) {
        // Charger les schemas des générateurs
        const genDetails = await Promise.all(
          chapter.generators.map(async (genKey) => {
            try {
              const res = await axios.get(`${API_V1}/generators/${genKey}/schema`);
              return { key: genKey, ...res.data };
            } catch {
              return { key: genKey, label: genKey, presets: [] };
            }
          })
        );
        setAvailableGenerators(genDetails);
        
        // Sélectionner le premier par défaut
        if (genDetails.length > 0 && !selectedGenerator) {
          setSelectedGenerator(genDetails[0].key);
        }
      } else {
        setAvailableGenerators([]);
      }
    } catch (err) {
      console.error("Erreur chargement générateurs:", err);
      setAvailableGenerators([]);
    }
  };
  
  loadGenerators();
}, [selectedItem, catalog]);
```

3. **Remplacer le sélecteur hardcodé (lignes 1210-1245) par:**
```javascript
{/* Sélecteur de générateur dynamique */}
{availableGenerators.length > 1 && (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      Type de générateur
    </label>
    <Select 
      value={selectedGenerator || ""} 
      onValueChange={setSelectedGenerator}
    >
      <SelectTrigger>
        <SelectValue placeholder="Sélectionner un type" />
      </SelectTrigger>
      <SelectContent>
        {availableGenerators.map(gen => (
          <SelectItem key={gen.key} value={gen.key}>
            {gen.label || gen.key}
            {gen.niveaux && (
              <span className="text-xs text-gray-500 ml-2">
                ({gen.niveaux.join(', ')})
              </span>
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  </div>
)}

{/* Afficher les presets du générateur sélectionné */}
{selectedGenerator && availableGenerators.find(g => g.key === selectedGenerator)?.presets?.length > 0 && (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      Configuration
    </label>
    <Select value={exerciseType} onValueChange={setExerciseType}>
      <SelectTrigger>
        <SelectValue placeholder="Configuration par défaut" />
      </SelectTrigger>
      <SelectContent>
        {availableGenerators
          .find(g => g.key === selectedGenerator)
          ?.presets?.map(preset => (
            <SelectItem key={preset.key} value={preset.key}>
              {preset.label}
            </SelectItem>
          ))}
      </SelectContent>
    </Select>
  </div>
)}
```

4. **Modifier le payload de génération (ligne 644-647) pour utiliser selectedGenerator:**
```javascript
// Remplacer detectedGenerator par selectedGenerator
if (selectedGenerator) {
  payload.generator_key = selectedGenerator;
  payload.ui_params = {
    ...payload.ui_params,
    generator_key: selectedGenerator,
    preset: exerciseType || undefined
  };
}
```

---

## ANNEXE B : DÉCISIONS TRANCHÉES

| Question | Décision | Justification |
|----------|----------|---------------|
| DB vs fichiers JSON comme source de vérité ? | **MongoDB uniquement** | Supprimer tout fallback vers fichiers statiques |
| UI générateurs hardcodée ou schema-driven ? | **Schema-driven** | Endpoint `/generators` retourne la liste dynamique |
| Pipeline par chapitre : explicite ou implicité ? | **Explicite en DB** | Champ `pipeline` obligatoire sur `curriculum_chapters` |
| Quotas free : côté frontend ou backend ? | **Backend only** | Le frontend ne peut pas être trusted |
| Auth : session ou JWT ? | **Session (magic link)** | Déjà implémenté, simple pour V1 |

---

*Document généré le 2 janvier 2026 - À mettre à jour après chaque sprint*
