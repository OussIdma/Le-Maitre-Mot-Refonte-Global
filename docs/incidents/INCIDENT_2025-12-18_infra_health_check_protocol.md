# INCIDENT — Amélioration protocole : Infrastructure Health Check

**ID**: INCIDENT_2025-12-18_infra_health_check_protocol  
**Date**: 2025-12-18  
**Type**: 🔧 Amélioration protocole (prévention faux positifs)

---

## 📋 SYMPTÔME OBSERVÉ

- **Contexte**: Validation de fixes backend alors que l'infrastructure Docker/Mongo était down
- **Problème**: L'agent a validé des changements code alors que la cause racine était une panne infrastructure
- **Impact**: Faux positifs, perte de temps, confusion entre bug code vs bug infra

### Cas observé

- `docker compose build / down / up` ne retournait pas le contrôle (hang)
- Conteneur Mongo non accessible (`mongo:27017 Temporary failure in name resolution`)
- Backend retournait HTTP 500
- **Agent a assumé un bug application** et a procédé avec validation

---

## 🔍 ROOT CAUSE

**Gap systémique** : L'agent ne distinguait pas les erreurs infrastructure (Docker down, Mongo unreachable) des erreurs application (bug code).

**Manque de garde-fou** :
- Aucune vérification de l'état Docker avant validation
- Aucune inspection des logs infra en cas de HTTP 500
- Validation automatique sans preuve que l'infrastructure est saine

---

## ✅ FIX APPLIQUÉ

### Ajout d'une section "INFRASTRUCTURE HEALTH CHECK" dans `.cursorrules`

**Emplacement** : Phase 2 — Analyse d'Impact & Garde-fous (AVANT Pre-Flight Check)

**Règles strictes ajoutées** :

1. **Vérification Docker obligatoire** :
   ```bash
   docker compose ps
   ```
   - Tous les services doivent être `Up`
   - Si `Exit` ou `Restarting` → **BLOQUER la validation**

2. **Vérification MongoDB obligatoire** :
   ```bash
   docker compose exec -T mongo mongosh --eval "db.adminCommand('ping')"
   ```
   - Si `Mongo unreachable` ou timeout → **BLOQUER la validation**

3. **Inspection logs en cas d'erreur HTTP 500** :
   ```bash
   docker compose logs --tail=50 backend | grep -i error
   docker compose logs --tail=50 mongo | grep -i error
   ```
   - Si erreurs DNS/connexion → **INFRASTRUCTURE DOWN, pas un bug code**

4. **Gestion des timeouts Docker** :
   - Si commande Docker hang > 30s → **ARRÊTER immédiatement**
   - Signaler : "Infrastructure Docker non disponible, impossible de valider"

### Modifications dans "NO GREEN WITHOUT PROOF"

**Ajout du point 0 (OBLIGATOIRE EN PREMIER)** :
- **INFRASTRUCTURE CHECK** avant toute validation
- Si infra down → **BLOQUER** (voir section Infrastructure Health Check)

### Modifications dans "Definition of Done"

**Ajout du point 0 (OBLIGATOIRE EN PREMIER)** :
- **Infrastructure** : `docker compose ps` → tous les services `Up`
- MongoDB accessible (pas d'erreur DNS/connexion)
- Si infra down → **BLOQUER** (pas de faux positif)

---

## 🧪 TESTS / PREUVE

### Scénario de test

1. **Simuler une panne infra** :
   ```bash
   docker compose stop mongo
   ```

2. **Tenter une validation backend** :
   - L'agent DOIT exécuter `docker compose ps` en premier
   - Détecter que `mongo` est `Exit`
   - **BLOQUER** avec message : "NON VALIDÉ — Infrastructure Docker/Mongo non disponible"

3. **Vérifier les logs** :
   - Si HTTP 500, l'agent DOIT inspecter `docker compose logs mongo`
   - Détecter erreur DNS/connexion
   - **Ne PAS** interpréter comme un bug code

---

## 🔧 COMMANDES DE REBUILD / RESTART

**Aucun rebuild nécessaire** (modification protocole uniquement).

**Validation** :
- Relire `.cursorrules` pour confirmer la section "INFRASTRUCTURE HEALTH CHECK"
- Tester avec une panne infra simulée

---

## 📝 RECOMMANDATIONS

1. **Automatisation future** :
   - Script de health check réutilisable : `scripts/healthcheck_infra.sh`
   - Intégration dans le Proof Pack automatique

2. **Monitoring proactif** :
   - Détecter les pannes infra AVANT de tenter des validations
   - Afficher un warning si Docker daemon non accessible

3. **Documentation** :
   - Ajouter une section "Troubleshooting Infrastructure" dans la doc
   - Lister les erreurs DNS/Mongo courantes et leurs solutions

---

## 🔗 FICHIERS IMPACTÉS

- `.cursorrules` : Ajout section "INFRASTRUCTURE HEALTH CHECK"
- `docs/incidents/INCIDENT_2025-12-18_infra_health_check_protocol.md` : Ce document

---

## ✅ VALIDATION

- [x] Section "INFRASTRUCTURE HEALTH CHECK" ajoutée dans `.cursorrules`
- [x] Point 0 ajouté dans "NO GREEN WITHOUT PROOF"
- [x] Point 0 ajouté dans "Definition of Done"
- [x] Règles strictes documentées (jamais valider si infra down)
- [x] Document d'incident créé

---

## 🎯 EFFET ATTENDU

**Prévention des faux positifs** :
- L'agent ne validera plus un fix code si l'infrastructure est down
- Distinction claire entre erreur infra vs erreur application
- Gain de temps (pas de debug code inutile sur un problème infra)

**Amélioration de la fiabilité** :
- Validation uniquement si l'infrastructure est saine
- Messages explicites : "NON VALIDÉ — Infrastructure Docker/Mongo non disponible"
- Diagnostic infra fourni avant toute tentative de fix code





