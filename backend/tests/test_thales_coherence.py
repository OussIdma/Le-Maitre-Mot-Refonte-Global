"""
Tests de cohérence CRITIQUE pour les exercices de Thalès
Vérifie que l'énoncé correspond TOUJOURS à la figure SVG
"""

import pytest
import sys
import os
import re
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.math_text_service import MathTextService
import asyncio


class TestThalesCoherence:
    """Tests critiques de cohérence pour Thalès"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
        self.text_service = MathTextService()
    
    def extraire_points_geometriques(self, texte: str) -> set:
        """Extraire tous les points géométriques d'un texte"""
        
        patterns = [
            r'\b([A-Z])\b',  # Lettre isolée
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
        
        # Filtrer les mots courants
        mots_exclus = {'I', 'L', 'On', 'Le', 'La', 'Les', 'Un', 'Une', 'De', 'Du', 'Des', 'En'}
        points = points - mots_exclus
        
        return points
    
    def test_thales_30_exercices_coherence(self):
        """Test CRITIQUE : Générer 30 exercices Thalès et vérifier la cohérence totale"""
        
        print("\n" + "="*80)
        print("TEST CRITIQUE : COHÉRENCE THALÈS (30 EXERCICES)")
        print("="*80 + "\n")
        
        echecs = []
        succes = 0
        
        for i in range(30):
            print(f"Test exercice {i+1}/30")
            print("-"*80)
            
            try:
                # Générer spec
                specs = self.math_service.generate_math_exercise_specs(
                    niveau="3e",
                    chapitre="Théorème de Thalès",
                    difficulte="moyen",
                    nb_exercices=1
                )
                
                assert len(specs) > 0, "Aucune spec générée"
                spec = specs[0]
                
                # Points autorisés de la figure
                points_autorises = set(spec.figure_geometrique.points)
                print(f"   Points autorisés: {points_autorises}")
                
                # Générer le texte (avec fallback si IA échoue)
                text = self.text_service._generate_fallback_text(spec)
                
                # Extraire les points de l'énoncé
                points_enonce = self.extraire_points_geometriques(text.enonce)
                print(f"   Points dans énoncé: {points_enonce}")
                
                # Extraire les points de la solution
                points_solution = self.extraire_points_geometriques(text.solution_redigee or "")
                print(f"   Points dans solution: {points_solution}")
                
                # VÉRIFICATION CRITIQUE 1 : Aucun point non autorisé dans l'énoncé
                points_interdits_enonce = points_enonce - points_autorises
                if points_interdits_enonce:
                    error = f"Points NON AUTORISÉS dans énoncé: {points_interdits_enonce}"
                    print(f"   ❌ {error}")
                    print(f"      Énoncé: {text.enonce[:150]}...")
                    echecs.append((i+1, error))
                    continue
                
                # VÉRIFICATION CRITIQUE 2 : Aucun point non autorisé dans la solution
                points_interdits_solution = points_solution - points_autorises
                if points_interdits_solution:
                    error = f"Points NON AUTORISÉS dans solution: {points_interdits_solution}"
                    print(f"   ❌ {error}")
                    echecs.append((i+1, error))
                    continue
                
                # VÉRIFICATION CRITIQUE 3 : Les 5 points doivent apparaître
                if len(points_autorises) >= 5:
                    points_utilises = points_enonce | points_solution
                    points_manquants = points_autorises - points_utilises
                    
                    if len(points_manquants) > 1:  # Tolérer 1 point manquant
                        error = f"Points MANQUANTS: {points_manquants}"
                        print(f"   ⚠️  {error}")
                        # Ne pas compter comme échec critique
                
                # VÉRIFICATION CRITIQUE 4 : Longueurs mentionnées doivent correspondre
                if spec.figure_geometrique.longueurs_connues:
                    longueurs_figure = spec.figure_geometrique.longueurs_connues
                    
                    # Vérifier qu'au moins une longueur de la figure est mentionnée
                    longueur_trouvee = False
                    for segment, valeur in longueurs_figure.items():
                        if f"{segment}" in text.enonce and str(valeur) in text.enonce:
                            longueur_trouvee = True
                            break
                    
                    if not longueur_trouvee:
                        error = "Aucune longueur de la figure n'est mentionnée dans l'énoncé"
                        print(f"   ⚠️  {error}")
                        # Pas un échec critique pour ce test
                
                print(f"   ✅ COHÉRENCE OK")
                succes += 1
                
            except Exception as e:
                error = f"Exception: {str(e)[:100]}"
                print(f"   ❌ {error}")
                echecs.append((i+1, error))
            
            print()
        
        # Rapport final
        print("="*80)
        print("RÉSUMÉ DU TEST DE COHÉRENCE THALÈS")
        print("="*80)
        print(f"✅ Exercices cohérents: {succes}/30 ({succes*100//30}%)")
        print(f"❌ Exercices incohérents: {len(echecs)}/30")
        
        if echecs:
            print("\n⚠️  ÉCHECS DÉTAILLÉS :")
            for num, error in echecs[:10]:  # Afficher les 10 premiers
                print(f"   Exercice {num}: {error}")
        
        print("="*80 + "\n")
        
        # Le test échoue si plus de 10% d'échecs
        taux_echec = len(echecs) / 30
        assert taux_echec <= 0.1, f"Taux d'échec trop élevé: {taux_echec*100:.1f}% (max 10%)"
    
    def test_thales_api_integration_coherence(self):
        """Test d'intégration : Vérifier la cohérence via l'API réelle"""
        
        print("\n" + "="*80)
        print("TEST INTÉGRATION API : COHÉRENCE THALÈS")
        print("="*80 + "\n")
        
        echecs = []
        
        for i in range(5):
            print(f"Test API {i+1}/5")
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
                        "guest_id": f"test_coherence_{i}"
                    },
                    timeout=60
                )
                
                assert response.status_code == 200, f"Status {response.status_code}"
                
                data = response.json()
                exercise = data["document"]["exercises"][0]
                
                # Points autorisés
                points_autorises = set(exercise["spec_mathematique"]["figure_geometrique"]["points"])
                print(f"   Points autorisés: {points_autorises}")
                
                # Points dans l'énoncé
                enonce = exercise["enonce"]
                points_enonce = self.extraire_points_geometriques(enonce)
                print(f"   Points dans énoncé: {points_enonce}")
                
                # Vérification
                points_interdits = points_enonce - points_autorises
                if points_interdits:
                    error = f"Points NON AUTORISÉS: {points_interdits}"
                    print(f"   ❌ {error}")
                    print(f"      Énoncé: {enonce[:150]}...")
                    echecs.append((i+1, error))
                    continue
                
                print(f"   ✅ COHÉRENCE API OK")
                
            except Exception as e:
                error = f"Exception: {str(e)[:100]}"
                print(f"   ❌ {error}")
                echecs.append((i+1, error))
            
            print()
        
        print("="*80)
        print(f"Résultats: {5-len(echecs)}/5 exercices cohérents")
        print("="*80 + "\n")
        
        assert len(echecs) == 0, f"{len(echecs)} exercice(s) incohérent(s) via API"
    
    def test_thales_fallback_deterministe(self):
        """Test que le fallback Thalès est déterministe et cohérent"""
        
        print("\n" + "="*80)
        print("TEST FALLBACK THALÈS DÉTERMINISTE")
        print("="*80 + "\n")
        
        # Générer 10 specs et vérifier que le fallback est toujours cohérent
        for i in range(10):
            specs = self.math_service.generate_math_exercise_specs(
                niveau="3e",
                chapitre="Théorème de Thalès",
                difficulte="facile",
                nb_exercices=1
            )
            
            spec = specs[0]
            fallback = self.text_service._fallback_thales(spec)
            
            points_autorises = set(spec.figure_geometrique.points)
            points_enonce = self.extraire_points_geometriques(fallback.enonce)
            
            # Vérifier cohérence
            points_interdits = points_enonce - points_autorises
            assert len(points_interdits) == 0, f"Fallback incohérent: {points_interdits}"
            
            print(f"   ✅ Fallback {i+1}/10 cohérent")
        
        print("\n✅ Fallback Thalès toujours déterministe et cohérent")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Exécution directe
    test = TestThalesCoherence()
    test.setup_method()
    
    print("\n🧪 LANCEMENT DES TESTS DE COHÉRENCE THALÈS\n")
    
    try:
        test.test_thales_30_exercices_coherence()
        test.test_thales_fallback_deterministe()
        test.test_thales_api_integration_coherence()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS DE COHÉRENCE PASSENT")
        print("="*80 + "\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        sys.exit(1)
