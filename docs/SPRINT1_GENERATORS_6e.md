# 📚 SPRINT 1 : Générateurs 6e - Premiers chapitres

## 📋 Vue d'ensemble

Ce document récapitule l'implémentation du **SPRINT 1** : création de générateurs Python pour 3 chapitres prioritaires de 6e.

**Date** : 2025-01-XX  
**Status** : ✅ TERMINÉ ET VALIDÉ

---

## 🎯 Chapitres implémentés

### 1. G03 - Perpendiculaires et parallèles à la règle et à l'équerre

**Titre exact** : `"Perpendiculaires et parallèles à la règle et à l'équerre"`  
**Code** : `6e_G03`  
**Type exercice** : `MathExerciseType.RECTANGLE`  
**Schéma** : OUI (grille + droites)  

**Types d'exercices** :
- Tracer une perpendiculaire à une droite passant par un point
- Tracer une parallèle à une droite passant par un point
- Identifier si deux droites sont perpendiculaires/parallèles/quelconques

**Exemple d'énoncé** :
```
Tracer la perpendiculaire à la droite (DE) passant par le point F. Utiliser l'équerre.
```

**Générateur** : `_gen_perpendiculaires_paralleles()`  
**Ligne** : 2190-2387

---

### 2. N03 - Droite numérique et repérage

**Titre exact** : `"Droite numérique et repérage"`  
**Code** : `6e_N03`  
**Type exercice** : `MathExerciseType.CALCUL_DECIMAUX`  
**Schéma** : NON (pourrait être ajouté plus tard)

**Types d'exercices** :
- Placer un nombre sur la droite graduée
- Lire l'abscisse d'un point
- Calculer la distance entre deux points

**Exemples d'énoncés** :
```
Sur une droite graduée allant de 0 à 10 (graduations tous les 1), le point A est placé. Lire son abscisse.

Sur une droite graduée, le point A a pour abscisse 5 et le point B a pour abscisse 15. Calculer la distance AB.
```

**Générateur** : `_gen_droite_numerique()`  
**Ligne** : 2389-2530

---

### 3. SP01 - Lire et compléter des tableaux de données

**Titre exact** : `"Lire et compléter des tableaux de données"`  
**Code** : `6e_SP01`  
**Type exercice** : `MathExerciseType.STATISTIQUES`  
**Schéma** : NON (données sous forme de tableaux dans les paramètres)

**Types d'exercices** :
- Lire une valeur dans un tableau
- Compléter une valeur manquante (avec total donné)
- Calculer le total d'une ligne ou colonne

**Exemples d'énoncés** :
```
Dans un tableau de notes, quelle est la valeur pour Français dans la colonne Trimestre 3 ?

Dans un tableau de ventes, calculer le total de la ligne Lundi. Les valeurs sont : 12, 15, 18.
```

**Générateur** : `_gen_tableaux_donnees()`  
**Ligne** : 2532-2709

---

## 🔧 Modifications techniques

### Fichier : `backend/services/math_generation_service.py`

**1. Mapping des chapitres** (ligne 70-74)
```python
# ========== 6e - Nombres et calculs (SPRINT 1) ==========
"Droite numérique et repérage": [MathExerciseType.CALCUL_DECIMAUX],

# ========== 6e - Organisation et gestion de données (SPRINT 1) ==========
"Lire et compléter des tableaux de données": [MathExerciseType.STATISTIQUES],
```

**2. Générateurs spécifiques par chapitre** (ligne 147-157)
```python
# SPRINT 1 : Générateurs spécifiques par chapitre (priorité sur les types)
chapter_specific_generators = {
    "Perpendiculaires et parallèles à la règle et à l'équerre": self._gen_perpendiculaires_paralleles,
    "Droite numérique et repérage": self._gen_droite_numerique,
    "Lire et compléter des tableaux de données": self._gen_tableaux_donnees
}

# Vérifier si un générateur spécifique existe pour ce chapitre
if chapitre in chapter_specific_generators:
    return chapter_specific_generators[chapitre](niveau, chapitre, difficulte)
```

**3. Nouveaux générateurs** (ligne 2190-2709)
- `_gen_perpendiculaires_paralleles()` : 197 lignes
- `_gen_droite_numerique()` : 141 lignes
- `_gen_tableaux_donnees()` : 177 lignes

**Total** : 515 lignes de code ajoutées

---

## ✅ Tests de validation

### Test 1 : Génération réussie pour chaque chapitre

```bash
python3 /tmp/test_sprint1_v4.py
```

**Résultats** :
- ✅ G03 : Perpendiculaires et parallèles → Énoncé contextuel généré
- ✅ N03 : Droite numérique → Énoncé contextuel généré
- ✅ SP01 : Tableaux de données → Énoncé contextuel généré

### Test 2 : Vérification des 3 niveaux de difficulté

| Chapitre | Facile | Moyen | Difficile |
|----------|--------|-------|-----------|
| G03      | ✅     | ✅    | ✅        |
| N03      | ✅     | ✅    | ✅        |
| SP01     | ✅     | ✅    | ✅        |

### Test 3 : Vérification des champs obligatoires

Pour chaque générateur :
- ✅ `parametres["enonce"]` : Énoncé contextuel présent
- ✅ `etapes_calculees` : Étapes de résolution détaillées
- ✅ `solution_calculee` : Solution calculée automatiquement
- ✅ `resultat_final` : Résultat final formaté
- ✅ `points_bareme` : Points de barème définis
- ✅ `figure_geometrique` : Schéma créé (G03 uniquement)

---

## 📊 Conformité avec le prompt

### Règle 1 : Titres de chapitres EXACTS ✅
- ✅ Titres copiés exactement depuis `001_migrate_chapters.py`
- ✅ Aucune variation ou abréviation

### Règle 2 : Types d'exercices existants ✅
- ✅ Utilisation de `RECTANGLE`, `CALCUL_DECIMAUX`, `STATISTIQUES`
- ✅ Aucun nouveau type créé

### Règle 3 : Énoncé contextuel OBLIGATOIRE ✅
- ✅ Tous les générateurs incluent `parametres["enonce"]`
- ✅ Aucun énoncé générique "Question 1"

**Exemples d'énoncés contextuels** :
- G03 : "Tracer la perpendiculaire à la droite (DE) passant par le point F. Utiliser l'équerre."
- N03 : "Sur une droite graduée allant de 0 à 10 (graduations tous les 1), le point A est placé. Lire son abscisse."
- SP01 : "Dans un tableau de notes, quelle est la valeur pour Français dans la colonne Trimestre 3 ?"

### Règle 4 : Cohérence énoncé/correction ✅
- ✅ Les mêmes valeurs sont utilisées dans l'énoncé et les étapes de résolution

---

## 🎯 Prochaines étapes (SPRINT 2)

### Chapitres prioritaires pour SPRINT 2 (5 chapitres)

1. **6e_G01** - Points, segments, droites, demi-droites
2. **6e_G02** - Alignement, milieu d'un segment
3. **6e_N01** - Lire et écrire les nombres entiers
4. **6e_N02** - Comparer et ranger des nombres entiers
5. **6e_N04** - Addition et soustraction de nombres entiers

**Approche** : Même stratégie que SPRINT 1
- Créer les générateurs spécifiques
- Ajouter au mapping `chapter_specific_generators`
- Tester avec les 3 niveaux de difficulté

---

## 📝 Notes techniques

### Architecture utilisée

**Système de mapping à 2 niveaux** :
1. `_map_chapter_to_types()` : Mappage chapitre → type d'exercice (conservé pour compatibilité)
2. `chapter_specific_generators` : Mappage chapitre → générateur spécifique (nouvelle logique)

**Avantages** :
- ✅ Rétrocompatibilité totale avec les générateurs existants
- ✅ Flexibilité pour créer des générateurs sur-mesure
- ✅ Pas besoin de créer de nouveaux types d'exercices
- ✅ Facilite l'ajout de nouveaux chapitres

**Inconvénient** :
- Les chapitres spécifiques ne bénéficient pas de la variation automatique des types d'exercices

**Solution future** : Créer des variantes dans chaque générateur spécifique (déjà fait pour G03, N03, SP01).

---

## 📋 Checklist de validation SPRINT 1

- [x] Fonction `_gen_perpendiculaires_paralleles()` créée
- [x] Fonction `_gen_droite_numerique()` créée
- [x] Fonction `_gen_tableaux_donnees()` créée
- [x] Mappings ajoutés dans `_map_chapter_to_types` avec titres EXACTS
- [x] Générateurs enregistrés dans `chapter_specific_generators`
- [x] Énoncés contextuels dans `parametres["enonce"]`
- [x] Schémas créés (G03 uniquement, conforme au prompt)
- [x] 3 niveaux de difficulté gérés
- [x] Étapes de résolution détaillées
- [x] Points de barème définis
- [x] Testé avec toutes les difficultés

---

**Auteur** : Emergent AI  
**Date** : 2025-01-XX  
**Projet** : Le-Maitre-Mot-v16-Refonte  
**Sprint** : 1 - Premiers générateurs 6e (G03, N03, SP01)
