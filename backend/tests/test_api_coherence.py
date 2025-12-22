"""
Test E2E - Cohérence API
Objectif : Mesurer le taux de cohérence réel de l'API /api/generate
Seuil : >= 90% (objectif : 95-100%)

Ce test est le RADAR de qualité du projet.
"""

import pytest
import requests
import re
from typing import Set, List, Tuple
import time


class TestAPICoherence:
    """Tests de cohérence end-to-end via API"""
    
    BASE_URL = "http://localhost:8001"
    
    @staticmethod
    def extraire_points_geometriques(texte: str) -> Set[str]:
        """Extraire tous les points géométriques d'un texte"""
        patterns = [
            r'\b([A-Z])\b',
            r'point ([A-Z])',
            r'segment \[([A-Z])([A-Z])\]',
            r'triangle ([A-Z])([A-Z])([A-Z])',
            r'\(([A-Z])([A-Z])\)',
            r'droite[s]? \(([A-Z])([A-Z])\)',
        ]
        
        points = set()
        for pattern in patterns:
            matches = re.findall(pattern, texte)
            for match in matches:
                if isinstance(match, tuple):
                    points.update(m for m in match if m and m.isupper())
                else:
                    if match and match.isupper():
                        points.add(match)
        
        # Filtrer mots courants
        mots_exclus = {'I', 'L', 'On', 'Le', 'La', 'Les', 'Un', 'Une', 'De', 'Du', 'Des', 'En', 'Et', 'Au', 'A'}
        points = points - mots_exclus
        
        return points
    
    @staticmethod
    def verifier_coherence_exercice(exercice: dict) -> Tuple[bool, List[str]]:
        """Vérifier la cohérence d'un exercice"""
        erreurs = []
        
        # 1. Extraire données
        spec = exercice.get("spec_mathematique", {})
        figure = spec.get("figure_geometrique", {})
        points_autorises = set(figure.get("points", []))
        
        enonce = exercice.get("enonce", "")
        solution = exercice.get("solution", {})
        solution_text = solution.get("solution_redigee", "") if isinstance(solution, dict) else str(solution)
        
        # 2. Extraire points de l'énoncé et solution
        points_enonce = TestAPICoherence.extraire_points_geometriques(enonce)
        points_solution = TestAPICoherence.extraire_points_geometriques(solution_text)
        
        # 3. VÉRIFICATION CRITIQUE : Points non autorisés
        points_interdits_enonce = points_enonce - points_autorises
        points_interdits_solution = points_solution - points_autorises
        
        if points_interdits_enonce:
            erreurs.append(f"Points NON AUTORISÉS dans énoncé: {points_interdits_enonce}")
        
        if points_interdits_solution:
            erreurs.append(f"Points NON AUTORISÉS dans solution: {points_interdits_solution}")
        
        # 4. Vérifier énoncé présent
        if not enonce or len(enonce.strip()) < 10:
            erreurs.append("Énoncé vide ou trop court")
        
        # 5. Vérifier figure SVG si applicable
        if figure and not exercice.get("figure_svg"):
            erreurs.append("Figure géométrique présente mais SVG manquant")
        
        return len(erreurs) == 0, erreurs
    
    def _generer_exercices(self, niveau: str, chapitre: str, nb: int = 5) -> List[dict]:
        """Générer des exercices via API"""
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": niveau,
                "chapitre": chapitre,
                "type_doc": "exercices",
                "difficulte": "moyen",
                "nb_exercices": nb,
                "guest_id": f"test_coherence_{int(time.time())}"
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Erreur API: {response.status_code}"
        data = response.json()
        return data["document"]["exercises"]
    
    def test_coherence_pythagore(self):
        """Test cohérence : Théorème de Pythagore"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE API : PYTHAGORE")
        print("="*80)
        
        exercices = self._generer_exercices("4e", "Théorème de Pythagore", nb=5)
        
        coherents = 0
        incoherents = 0
        
        for i, ex in enumerate(exercices, 1):
            est_coherent, erreurs = self.verifier_coherence_exercice(ex)
            
            if est_coherent:
                coherents += 1
                print(f"✅ Exercice {i}/5 : COHÉRENT")
            else:
                incoherents += 1
                print(f"❌ Exercice {i}/5 : INCOHÉRENT")
                for err in erreurs:
                    print(f"   - {err}")
        
        taux = coherents / len(exercices)
        print(f"\n📊 Taux de cohérence : {taux*100:.1f}% ({coherents}/{len(exercices)})")
        
        assert taux >= 0.9, f"Taux de cohérence trop faible : {taux*100:.1f}% (min 90%)"
    
    def test_coherence_cercles(self):
        """Test cohérence : Cercles"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE API : CERCLES")
        print("="*80)
        
        exercices = self._generer_exercices("6e", "Aires", nb=5)
        
        coherents = 0
        incoherents = 0
        
        for i, ex in enumerate(exercices, 1):
            est_coherent, erreurs = self.verifier_coherence_exercice(ex)
            
            if est_coherent:
                coherents += 1
                print(f"✅ Exercice {i}/5 : COHÉRENT")
            else:
                incoherents += 1
                print(f"❌ Exercice {i}/5 : INCOHÉRENT")
                for err in erreurs:
                    print(f"   - {err}")
        
        taux = coherents / len(exercices)
        print(f"\n📊 Taux de cohérence : {taux*100:.1f}% ({coherents}/{len(exercices)})")
        
        assert taux >= 0.9, f"Taux de cohérence trop faible : {taux*100:.1f}% (min 90%)"
    
    def test_coherence_rectangles(self):
        """Test cohérence : Rectangles"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE API : RECTANGLES")
        print("="*80)
        
        exercices = self._generer_exercices("5e", "Aires et périmètres", nb=5)
        
        coherents = 0
        incoherents = 0
        
        for i, ex in enumerate(exercices, 1):
            est_coherent, erreurs = self.verifier_coherence_exercice(ex)
            
            if est_coherent:
                coherents += 1
                print(f"✅ Exercice {i}/5 : COHÉRENT")
            else:
                incoherents += 1
                print(f"❌ Exercice {i}/5 : INCOHÉRENT")
                for err in erreurs:
                    print(f"   - {err}")
        
        taux = coherents / len(exercices)
        print(f"\n📊 Taux de cohérence : {taux*100:.1f}% ({coherents}/{len(exercices)})")
        
        assert taux >= 0.9, f"Taux de cohérence trop faible : {taux*100:.1f}% (min 90%)"
    
    def test_coherence_trigonometrie(self):
        """Test cohérence : Trigonométrie"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE API : TRIGONOMÉTRIE")
        print("="*80)
        
        exercices = self._generer_exercices("3e", "Trigonométrie", nb=5)
        
        coherents = 0
        incoherents = 0
        
        for i, ex in enumerate(exercices, 1):
            est_coherent, erreurs = self.verifier_coherence_exercice(ex)
            
            if est_coherent:
                coherents += 1
                print(f"✅ Exercice {i}/5 : COHÉRENT")
            else:
                incoherents += 1
                print(f"❌ Exercice {i}/5 : INCOHÉRENT")
                for err in erreurs:
                    print(f"   - {err}")
        
        taux = coherents / len(exercices)
        print(f"\n📊 Taux de cohérence : {taux*100:.1f}% ({coherents}/{len(exercices)})")
        
        assert taux >= 0.9, f"Taux de cohérence trop faible : {taux*100:.1f}% (min 90%)"
    
    def test_coherence_thales(self):
        """Test cohérence : Théorème de Thalès (non-régression)"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE API : THALÈS (non-régression)")
        print("="*80)
        
        exercices = self._generer_exercices("3e", "Théorème de Thalès", nb=5)
        
        coherents = 0
        incoherents = 0
        
        for i, ex in enumerate(exercices, 1):
            est_coherent, erreurs = self.verifier_coherence_exercice(ex)
            
            if est_coherent:
                coherents += 1
                print(f"✅ Exercice {i}/5 : COHÉRENT")
            else:
                incoherents += 1
                print(f"❌ Exercice {i}/5 : INCOHÉRENT")
                for err in erreurs:
                    print(f"   - {err}")
        
        taux = coherents / len(exercices)
        print(f"\n📊 Taux de cohérence : {taux*100:.1f}% ({coherents}/{len(exercices)})")
        
        # Thalès doit être parfait (déjà validé à 100%)
        assert taux >= 0.95, f"Taux de cohérence trop faible : {taux*100:.1f}% (min 95%)"
    
    def test_coherence_globale(self):
        """Test cohérence globale (tous types confondus)"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE API : GLOBAL (échantillon représentatif)")
        print("="*80)
        
        types_tests = [
            ("4e", "Théorème de Pythagore", 3),
            ("3e", "Trigonométrie", 3),
            ("6e", "Aires", 3),
            ("5e", "Aires et périmètres", 3),
            ("3e", "Théorème de Thalès", 3),
        ]
        
        total_coherents = 0
        total_exercices = 0
        
        for niveau, chapitre, nb in types_tests:
            print(f"\n🔍 {niveau} - {chapitre} ({nb} exercices)")
            exercices = self._generer_exercices(niveau, chapitre, nb=nb)
            
            for i, ex in enumerate(exercices, 1):
                est_coherent, erreurs = self.verifier_coherence_exercice(ex)
                total_exercices += 1
                
                if est_coherent:
                    total_coherents += 1
                    print(f"   ✅ Ex {i} : OK")
                else:
                    print(f"   ❌ Ex {i} : {'; '.join(erreurs[:2])}")
        
        taux_global = total_coherents / total_exercices
        
        print(f"\n" + "="*80)
        print(f"📊 TAUX DE COHÉRENCE GLOBAL : {taux_global*100:.1f}%")
        print(f"   Exercices cohérents : {total_coherents}/{total_exercices}")
        print("="*80)
        
        # Objectif : >= 90% (production sécurisée)
        assert taux_global >= 0.9, f"Taux de cohérence global trop faible : {taux_global*100:.1f}% (min 90%)"


if __name__ == "__main__":
    # Exécution directe
    test = TestAPICoherence()
    
    print("\n" + "🚀"*40)
    print("LANCEMENT DES TESTS DE COHÉRENCE API")
    print("🚀"*40 + "\n")
    
    try:
        test.test_coherence_pythagore()
        test.test_coherence_cercles()
        test.test_coherence_rectangles()
        test.test_coherence_trigonometrie()
        test.test_coherence_thales()
        test.test_coherence_globale()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS DE COHÉRENCE API PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        exit(1)
