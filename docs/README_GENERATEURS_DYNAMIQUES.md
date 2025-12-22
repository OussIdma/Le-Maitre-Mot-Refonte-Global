# Guide des Générateurs Dynamiques — Le Maître Mot
**Version :** 1.0.0  
**Date :** 2025-01-XX

---

## 📚 Documentation disponible

### 🎯 Pour créer un nouveau générateur

**👉 [PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md](PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md)**

Procédure complète et industrialisée pour créer un nouveau générateur dynamique sans erreur :
- Structure du fichier
- Imports obligatoires
- Métadonnées et schéma
- Méthode `generate()`
- Enregistrement dans `GeneratorFactory`
- Tests unitaires
- Validation et déploiement
- **Pièges courants et solutions** (8 pièges documentés)

**Utilisez cette procédure si** : Vous créez un nouveau générateur de zéro.

---

### 📝 Pour ajouter un template à un générateur existant

**👉 [PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md](PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md)**

Procédure pour créer un exercice dynamique via l'admin UI :
- Identifier le générateur
- Récupérer les templates de référence
- Extraire les placeholders
- Créer l'exercice via l'admin
- Valider les placeholders
- Tester la génération

**Utilisez cette procédure si** : Le générateur existe déjà et vous voulez créer un exercice dynamique.

---

### 📖 Spécifications complètes

**👉 [CAHIER_DES_CHARGES_GENERATEURS_DYNAMIQUES.md](CAHIER_DES_CHARGES_GENERATEURS_DYNAMIQUES.md)**

Cahier des charges complet avec :
- Architecture technique
- Structure d'un générateur
- Définition des paramètres
- Templates HTML
- Génération SVG
- Mapping multi-chapitres
- Presets pédagogiques
- Validation et tests
- Exemple complet

**Utilisez ce document si** : Vous voulez comprendre l'architecture complète.

---

## 🚀 Quick Start

### Créer un nouveau générateur

1. **Lire** : `PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md`
2. **Suivre** : La checklist complète étape par étape
3. **Valider** : Tests unitaires + rebuild Docker + test API

### Ajouter un exercice dynamique

1. **Lire** : `PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md`
2. **Vérifier** : Le générateur existe et est enregistré
3. **Créer** : L'exercice via l'admin UI avec les templates de référence

---

## ⚠️ Pièges courants (résumé)

1. **Import manquant dans factory.py** → Générateur non visible
2. **Imports manquants** (`time`, `safe_random_choice`, `safe_randrange`) → `NameError`
3. **Crash randrange** → Filtrage préventif des pools obligatoire
4. **Placeholders non résolus** → Tous les placeholders DOIVENT être dans `variables`
5. **Docker non rebuild** → Code modifié mais non pris en compte
6. **Décorateur manquant** → `@GeneratorFactory.register` obligatoire
7. **Templates copiés** → Toujours utiliser les templates du générateur lui-même
8. **Erreurs de syntaxe** → Vérifier avec `python3 -m py_compile`

**📚 Solutions détaillées** : Voir `PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` section "Pièges courants et solutions"

---

## 📊 Exemples de référence

### Générateurs existants

1. **SIMPLIFICATION_FRACTIONS_V1** (`backend/generators/simplification_fractions_v1.py`)
   - Exemple simple et complet
   - Filtrage préventif de pools
   - Logs structurés
   - Tests complets

2. **SIMPLIFICATION_FRACTIONS_V2** (`backend/generators/simplification_fractions_v2.py`)
   - Exemple avec variants pédagogiques
   - Templates multiples (A, B, C)
   - Non-régression V1

3. **THALES_V2** (`backend/generators/thales_v2.py`)
   - Exemple avec génération SVG complexe
   - Mapping multi-chapitres

---

## 🔗 Liens utiles

- **Incidents documentés** : `docs/incidents/`
- **Tests de référence** : `backend/tests/test_simplification_fractions_v1.py`
- **Factory** : `backend/generators/factory.py`
- **Base Generator** : `backend/generators/base_generator.py`

---

## ✅ Checklist rapide

### Création d'un générateur

- [ ] Fichier créé avec imports obligatoires
- [ ] Décorateur `@GeneratorFactory.register` présent
- [ ] Import ajouté dans `factory.py`
- [ ] Tests unitaires créés
- [ ] Compilation OK
- [ ] Rebuild Docker effectué
- [ ] Générateur visible dans l'API

### Ajout d'un template

- [ ] Générateur existe et est enregistré
- [ ] Templates de référence extraits du générateur
- [ ] Placeholders identifiés
- [ ] Exercice créé via admin avec templates corrects
- [ ] Validation des placeholders OK
- [ ] Test de génération OK

---

**Document créé le :** 2025-01-XX  
**Dernière mise à jour :** 2025-01-XX  
**Statut :** ✅ Validé


