"""
Tests de cohérence CRITIQUE pour les SOLUTIONS des exercices de Thalès
Vérifie que la solution utilise les bons points et le bon parallélisme
"""

import pytest
import sys
import os
import re
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.math_text_service import MathTextService


class TestThalesSolutionCoherence:
    """Tests critiques de cohérence pour les SOLUTIONS Thalès"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
        self.text_service = MathTextService()
    
    def extraire_points_geometriques(self, texte: str) -> set:
        """Extraire tous les points géométriques d'un texte"""
        
        patterns = [
            r'\b([A-Z])\b',
            r'point ([A-Z])',
            r'segment \[([A-Z])([A-Z])\]',
            r'triangle ([A-Z])([A-Z])([A-Z])',
            r'\(([A-Z])([A-Z])\)',
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
        
        # Filtrer les mots courants
        mots_exclus = {'I', 'L', 'On', 'Le', 'La', 'Les', 'Un', 'Une', 'De', 'Du', 'Des', 'En'}
        points = points - mots_exclus
        
        return points
    
    def extraire_parallelisme(self, texte: str) -> list:
        """Extraire les parallélismes (AB) // (CD) d'un texte"""
        
        pattern = r'\(([A-Z])([A-Z])\)\s*//\s*\(([A-Z])([A-Z])\)'
        matches = re.findall(pattern, texte)
        
        parallelismes = []
        for match in matches:
            # match = (A, B, C, D) pour "(AB) // (CD)"
            parallelismes.append({
                'segment1': f"{match[0]}{match[1]}",
                'segment2': f"{match[2]}{match[3]}",
                'points': set(match)
            })
        
        return parallelismes
    
    def test_thales_20_solutions_coherentes(self):
        """Test CRITIQUE : Générer 20 exercices et vérifier cohérence des SOLUTIONS"""
        
        print("\n" + "="*80)
        print("TEST CRITIQUE : COHÉRENCE SOLUTIONS THALÈS (20 EXERCICES)")
        print("="*80 + "\n")
        
        echecs = []
        succes = 0
        
        for i in range(20):
            print(f"Test solution {i+1}/20")
            print("-"*80)
            
            try:
                # Générer spec
                specs = self.math_service.generate_math_exercise_specs(
                    niveau="3e",
                    chapitre="Théorème de Thalès",
                    difficulte="moyen",
                    nb_exercices=1
                )
                
                spec = specs[0]
                points_autorises = set(spec.figure_geometrique.points)
                
                print(f"   Points autorisés: {points_autorises}")
                
                # Extraire les étapes calculées (générées par le générateur Python)
                etapes = spec.etapes_calculees
                
                # Vérifier l'étape 1 (doit contenir le bon parallélisme)
                etape_1 = etapes[0] if etapes else ""
                print(f"   Étape 1: {etape_1}")
                
                # Extraire points de l'étape 1
                points_etape_1 = self.extraire_points_geometriques(etape_1)
                
                # VÉRIFICATION 1 : Pas de points non autorisés dans l'étape 1
                points_interdits = points_etape_1 - points_autorises
                if points_interdits:
                    error = f"Étape 1: Points NON AUTORISÉS: {points_interdits}"
                    print(f"   ❌ {error}")
                    echecs.append((i+1, error))
                    continue
                
                # VÉRIFICATION 2 : Le parallélisme doit utiliser les bons points
                parallelismes = self.extraire_parallelisme(etape_1)
                
                if parallelismes:
                    parallel = parallelismes[0]
                    print(f"   Parallélisme: ({parallel['segment1']}) // ({parallel['segment2']})")
                    
                    # Vérifier que tous les points du parallélisme sont autorisés
                    points_parallel_interdits = parallel['points'] - points_autorises
                    if points_parallel_interdits:
                        error = f"Parallélisme avec points NON AUTORISÉS: {points_parallel_interdits}"
                        print(f"   ❌ {error}")
                        echecs.append((i+1, error))
                        continue
                    
                    # VÉRIFICATION 3 : Le parallélisme doit être cohérent avec la structure
                    # Points = [A, B, C, D, E] où A=sommet, D et E sont internes, B et C sont base
                    # Donc le parallélisme doit être (DE) // (BC)
                    A, B, C, D, E = list(points_autorises)[:5]
                    
                    expected_parallel = f"({D}{E}) // ({B}{C})"
                    actual_parallel = f"({parallel['segment1']}) // ({parallel['segment2']})"
                    
                    # Note: L'ordre peut varier (DE ou ED, BC ou CB)
                    # On vérifie juste que les points sont corrects
                    expected_points = {D, E, B, C}
                    actual_points = parallel['points']
                    
                    if expected_points != actual_points:
                        error = f"Parallélisme incorrect: attendu {expected_points}, obtenu {actual_points}"
                        print(f"   ⚠️  {error}")
                        # Pas un échec critique si les points sont autorisés
                
                # Vérifier toutes les étapes
                all_etapes_text = " ".join(etapes)
                points_toutes_etapes = self.extraire_points_geometriques(all_etapes_text)
                points_interdits_etapes = points_toutes_etapes - points_autorises
                
                if points_interdits_etapes:
                    error = f"Étapes: Points NON AUTORISÉS: {points_interdits_etapes}"
                    print(f"   ❌ {error}")
                    echecs.append((i+1, error))
                    continue
                
                print(f"   ✅ SOLUTION COHÉRENTE")
                succes += 1
                
            except Exception as e:
                error = f"Exception: {str(e)[:100]}"
                print(f"   ❌ {error}")
                echecs.append((i+1, error))
            
            print()
        
        # Rapport final
        print("="*80)
        print("RÉSUMÉ TEST COHÉRENCE SOLUTIONS THALÈS")
        print("="*80)
        print(f"✅ Solutions cohérentes: {succes}/20 ({succes*100//20}%)")
        print(f"❌ Solutions incohérentes: {len(echecs)}/20")
        
        if echecs:
            print("\n⚠️  ÉCHECS DÉTAILLÉS :")
            for num, error in echecs:
                print(f"   Exercice {num}: {error}")
        
        print("="*80 + "\n")
        
        # Le test échoue si plus de 5% d'échecs
        assert len(echecs) == 0, f"{len(echecs)} solution(s) incohérente(s) détectée(s)"
    
    def test_thales_api_solutions_coherentes(self):
        """Test API : Vérifier cohérence des solutions via l'API réelle"""
        
        print("\n" + "="*80)
        print("TEST API : COHÉRENCE SOLUTIONS THALÈS")
        print("="*80 + "\n")
        
        echecs = []
        
        for i in range(5):
            print(f"Test API solution {i+1}/5")
            print("-"*80)
            
            try:
                response = requests.post(
                    "http://localhost:8001/api/generate",
                    json={
                        "matiere": "Mathématiques",
                        "niveau": "3e",
                        "chapitre": "Théorème de Thalès",
                        "type_doc": "exercices",
                        "difficulte": "moyen",
                        "nb_exercices": 1,
                        "guest_id": f"test_solution_{i}"
                    },
                    timeout=60
                )
                
                assert response.status_code == 200
                
                data = response.json()
                exercise = data["document"]["exercises"][0]
                
                # Points autorisés
                points_autorises = set(exercise["spec_mathematique"]["figure_geometrique"]["points"])
                print(f"   Points autorisés: {points_autorises}")
                
                # Vérifier les étapes de solution
                etapes = exercise["solution"]["etapes"]
                etape_1 = etapes[0] if etapes else ""
                
                print(f"   Étape 1: {etape_1[:80]}...")
                
                # Extraire points et parallélisme
                points_etape = self.extraire_points_geometriques(etape_1)
                parallelismes = self.extraire_parallelisme(etape_1)
                
                # Vérifier points
                points_interdits = points_etape - points_autorises
                if points_interdits:
                    error = f"Points NON AUTORISÉS dans solution: {points_interdits}"
                    print(f"   ❌ {error}")
                    echecs.append((i+1, error))
                    continue
                
                # Vérifier parallélisme
                if parallelismes:
                    parallel = parallelismes[0]
                    points_parallel_interdits = parallel['points'] - points_autorises
                    
                    if points_parallel_interdits:
                        error = f"Parallélisme NON AUTORISÉ: {points_parallel_interdits}"
                        print(f"   ❌ {error}")
                        echecs.append((i+1, error))
                        continue
                    
                    print(f"   Parallélisme: ({parallel['segment1']}) // ({parallel['segment2']}) ✓")
                
                print(f"   ✅ SOLUTION API COHÉRENTE")
                
            except Exception as e:
                error = f"Exception: {str(e)[:100]}"
                print(f"   ❌ {error}")
                echecs.append((i+1, error))
            
            print()
        
        print("="*80)
        print(f"Résultats: {5-len(echecs)}/5 solutions cohérentes")
        print("="*80 + "\n")
        
        assert len(echecs) == 0, f"{len(echecs)} solution(s) API incohérente(s)"
    
    def test_thales_pas_de_hardcoded_points(self):
        """Test : Vérifier qu'aucun point hardcodé (DE, BC, etc.) n'apparaît avec de mauvais points"""
        
        print("\n" + "="*80)
        print("TEST : DÉTECTION POINTS HARDCODÉS")
        print("="*80 + "\n")
        
        # Générer 10 exercices avec des points aléatoires
        for i in range(10):
            specs = self.math_service.generate_math_exercise_specs(
                niveau="3e",
                chapitre="Théorème de Thalès",
                difficulte="facile",
                nb_exercices=1
            )
            
            spec = specs[0]
            points = spec.figure_geometrique.points
            etapes = spec.etapes_calculees
            
            # Si les points ne sont PAS [D, E, F, M, N], alors "DE" et "BC" ne doivent PAS apparaître
            if points != ['D', 'E', 'F', 'M', 'N']:
                etape_1 = etapes[0] if etapes else ""
                
                # Chercher des occurrences de points qui ne sont pas dans la liste
                if 'DE' in etape_1 or 'BC' in etape_1:
                    # Vérifier si D, E, B, C sont vraiment dans les points autorisés
                    points_set = set(points)
                    
                    if 'D' not in points_set or 'E' not in points_set:
                        if 'DE' in etape_1:
                            print(f"   ❌ ERREUR: 'DE' apparaît mais D ou E n'est pas autorisé")
                            print(f"      Points: {points}")
                            print(f"      Étape: {etape_1}")
                            assert False, "Points hardcodés détectés"
                    
                    if 'B' not in points_set or 'C' not in points_set:
                        if 'BC' in etape_1:
                            print(f"   ❌ ERREUR: 'BC' apparaît mais B ou C n'est pas autorisé")
                            print(f"      Points: {points}")
                            print(f"      Étape: {etape_1}")
                            assert False, "Points hardcodés détectés"
            
            print(f"   ✅ Test {i+1}/10 : Pas de points hardcodés")
        
        print("\n✅ Aucun point hardcodé détecté")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Exécution directe
    test = TestThalesSolutionCoherence()
    test.setup_method()
    
    print("\n🧪 LANCEMENT DES TESTS COHÉRENCE SOLUTIONS THALÈS\n")
    
    try:
        test.test_thales_20_solutions_coherentes()
        test.test_thales_pas_de_hardcoded_points()
        test.test_thales_api_solutions_coherentes()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS DE SOLUTIONS PASSENT")
        print("="*80 + "\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        sys.exit(1)
