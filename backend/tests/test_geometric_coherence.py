"""
Tests de cohérence CRITIQUE pour TOUS les générateurs géométriques
Vérifie que énoncé/figure/solution sont toujours cohérents

Générateurs testés :
- Pythagore (triangle_rectangle)
- Trigonométrie
- Cercles  
- Rectangles/Carrés
- Périmètres et aires
- Triangles quelconques
"""

import pytest
import sys
import os
import re
from typing import Set, Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.math_text_service import MathTextService
import asyncio


class CoherenceChecker:
    """Utilitaire pour vérifier la cohérence des exercices géométriques"""
    
    @staticmethod
    def extraire_points_geometriques(texte: str) -> Set[str]:
        """Extraire tous les points géométriques d'un texte"""
        patterns = [
            r'\b([A-Z])\b',  # Lettre isolée
            r'point ([A-Z])',
            r'segment \[([A-Z])([A-Z])\]',
            r'triangle ([A-Z])([A-Z])([A-Z])',
            r'\(([A-Z])([A-Z])\)',
            r'droite[s]? \(([A-Z])([A-Z])\)',
            r'rectangle ([A-Z])([A-Z])([A-Z])([A-Z])',
            r'carré ([A-Z])([A-Z])([A-Z])([A-Z])',
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
        
        # Filtrer les mots courants (articles, prépositions, etc.)
        mots_exclus = {'I', 'L', 'On', 'Le', 'La', 'Les', 'Un', 'Une', 'De', 'Du', 'Des', 'En', 'Et', 'Au', 'A'}
        points = points - mots_exclus
        
        return points
    
    @staticmethod
    def extraire_valeurs_numeriques(texte: str) -> Set[float]:
        """Extraire toutes les valeurs numériques du texte"""
        # Pattern pour capturer nombres décimaux et entiers
        pattern = r'\b(\d+(?:\.\d+)?)\s*(?:cm|m|°)?'
        matches = re.findall(pattern, texte)
        valeurs = set()
        for match in matches:
            try:
                valeurs.add(float(match))
            except:
                pass
        return valeurs
    
    @staticmethod
    def verifier_coherence_points(
        points_autorises: Set[str],
        points_enonce: Set[str],
        points_solution: Set[str],
        exercice_id: str
    ) -> List[str]:
        """Vérifier que tous les points utilisés sont autorisés"""
        erreurs = []
        
        # Vérifier énoncé
        points_interdits_enonce = points_enonce - points_autorises
        if points_interdits_enonce:
            erreurs.append(
                f"[{exercice_id}] Points NON AUTORISÉS dans énoncé: {points_interdits_enonce}"
            )
        
        # Vérifier solution
        points_interdits_solution = points_solution - points_autorises
        if points_interdits_solution:
            erreurs.append(
                f"[{exercice_id}] Points NON AUTORISÉS dans solution: {points_interdits_solution}"
            )
        
        return erreurs
    
    @staticmethod
    def verifier_coherence_valeurs(
        valeurs_figure: Dict[str, Any],
        valeurs_enonce: Set[float],
        valeurs_solution: Set[float],
        exercice_id: str,
        spec=None
    ) -> List[str]:
        """Vérifier que les valeurs numériques sont cohérentes"""
        erreurs = []
        
        # Extraire les valeurs de la figure
        valeurs_attendues = set()
        for val in valeurs_figure.values():
            if isinstance(val, (int, float)):
                valeurs_attendues.add(float(val))
        
        # Pour les cercles, accepter aussi les valeurs dérivées (périmètre, aire)
        valeurs_derivees = set()
        if spec and hasattr(spec, 'parametres'):
            params = spec.parametres
            # Si c'est un exercice de type "rayon_depuis_perimetre", accepter le périmètre
            if params.get('type') == 'rayon_depuis_perimetre' and 'perimetre' in params:
                valeurs_derivees.add(float(params['perimetre']))
            # Pour les exercices sur cercles, accepter aussi périmètre/aire calculés
            if 'rayon' in valeurs_figure:
                rayon = valeurs_figure['rayon']
                import math
                perimetre_calcule = round(2 * math.pi * rayon, 2)
                aire_calculee = round(math.pi * rayon * rayon, 2)
                valeurs_derivees.add(perimetre_calcule)
                valeurs_derivees.add(aire_calculee)
        
        # Vérifier qu'au moins une valeur (directe ou dérivée) apparaît dans l'énoncé
        if valeurs_attendues and valeurs_enonce:
            toutes_valeurs_acceptables = valeurs_attendues | valeurs_derivees
            intersection = toutes_valeurs_acceptables & valeurs_enonce
            if not intersection:
                erreurs.append(
                    f"[{exercice_id}] Aucune valeur de la figure n'apparaît dans l'énoncé. "
                    f"Figure: {valeurs_attendues}, Énoncé: {valeurs_enonce}"
                )
        
        return erreurs


class TestGeometricCoherence:
    """Tests de cohérence pour tous les générateurs géométriques"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
        self.text_service = MathTextService()
        self.checker = CoherenceChecker()
    
    def test_pythagore_coherence(self):
        """Test cohérence : Théorème de Pythagore (triangle rectangle)"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE : PYTHAGORE (TRIANGLE RECTANGLE)")
        print("="*80 + "\n")
        
        nb_tests = 20
        echecs = self._test_generateur_coherence(
            niveau="4e",
            chapitre="Théorème de Pythagore",
            difficulte="moyen",
            nb_tests=nb_tests,
            nom_test="Pythagore"
        )
        
        taux_echec = len(echecs) / nb_tests
        print(f"\n✅ Succès: {nb_tests - len(echecs)}/{nb_tests}")
        print(f"❌ Échecs: {len(echecs)}/{nb_tests}")
        
        assert taux_echec <= 0.1, f"Taux d'échec trop élevé: {taux_echec*100:.1f}% (max 10%)"
    
    def test_trigonometrie_coherence(self):
        """Test cohérence : Trigonométrie"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE : TRIGONOMÉTRIE")
        print("="*80 + "\n")
        
        nb_tests = 20
        echecs = self._test_generateur_coherence(
            niveau="3e",
            chapitre="Trigonométrie",
            difficulte="moyen",
            nb_tests=nb_tests,
            nom_test="Trigonométrie"
        )
        
        taux_echec = len(echecs) / nb_tests
        print(f"\n✅ Succès: {nb_tests - len(echecs)}/{nb_tests}")
        print(f"❌ Échecs: {len(echecs)}/{nb_tests}")
        
        assert taux_echec <= 0.1, f"Taux d'échec trop élevé: {taux_echec*100:.1f}% (max 10%)"
    
    def test_cercles_coherence(self):
        """Test cohérence : Cercles"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE : CERCLES")
        print("="*80 + "\n")
        
        nb_tests = 20
        echecs = self._test_generateur_coherence(
            niveau="6e",
            chapitre="Aires",
            difficulte="facile",
            nb_tests=nb_tests,
            nom_test="Cercles",
            filtre_type="cercle"
        )
        
        # Pour les cercles, on accepte un peu plus d'échecs car on filtre
        taux_echec = len(echecs) / max(nb_tests, 1)
        print(f"\n✅ Succès: {max(0, nb_tests - len(echecs))}/{nb_tests}")
        print(f"❌ Échecs: {len(echecs)}/{nb_tests}")
        
        if nb_tests > 0:
            assert taux_echec <= 0.15, f"Taux d'échec trop élevé: {taux_echec*100:.1f}% (max 15%)"
    
    def test_rectangles_coherence(self):
        """Test cohérence : Rectangles et carrés"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE : RECTANGLES/CARRÉS")
        print("="*80 + "\n")
        
        nb_tests = 20
        echecs = self._test_generateur_coherence(
            niveau="5e",
            chapitre="Aires et périmètres",
            difficulte="facile",
            nb_tests=nb_tests,
            nom_test="Rectangles",
            filtre_type="rectangle"
        )
        
        taux_echec = len(echecs) / max(nb_tests, 1)
        print(f"\n✅ Succès: {max(0, nb_tests - len(echecs))}/{nb_tests}")
        print(f"❌ Échecs: {len(echecs)}/{nb_tests}")
        
        if nb_tests > 0:
            assert taux_echec <= 0.15, f"Taux d'échec trop élevé: {taux_echec*100:.1f}% (max 15%)"
    
    def test_perimetre_aire_coherence(self):
        """Test cohérence : Périmètres et aires (rectangle/carré/cercle)"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE : PÉRIMÈTRES ET AIRES")
        print("="*80 + "\n")
        
        nb_tests = 30  # Plus de tests car 3 types de figures
        echecs = self._test_generateur_coherence(
            niveau="6e",
            chapitre="Périmètres et aires",
            difficulte="facile",
            nb_tests=nb_tests,
            nom_test="Périmètres et aires"
        )
        
        taux_echec = len(echecs) / nb_tests
        print(f"\n✅ Succès: {nb_tests - len(echecs)}/{nb_tests}")
        print(f"❌ Échecs: {len(echecs)}/{nb_tests}")
        
        assert taux_echec <= 0.15, f"Taux d'échec trop élevé: {taux_echec*100:.1f}% (max 15%)"
    
    def test_triangles_coherence(self):
        """Test cohérence : Triangles quelconques"""
        print("\n" + "="*80)
        print("TEST COHÉRENCE : TRIANGLES")
        print("="*80 + "\n")
        
        nb_tests = 20
        echecs = self._test_generateur_coherence(
            niveau="5e",
            chapitre="Triangles",
            difficulte="facile",
            nb_tests=nb_tests,
            nom_test="Triangles"
        )
        
        taux_echec = len(echecs) / nb_tests
        print(f"\n✅ Succès: {nb_tests - len(echecs)}/{nb_tests}")
        print(f"❌ Échecs: {len(echecs)}/{nb_tests}")
        
        assert taux_echec <= 0.15, f"Taux d'échec trop élevé: {taux_echec*100:.1f}% (max 15%)"
    
    def _test_generateur_coherence(
        self,
        niveau: str,
        chapitre: str,
        difficulte: str,
        nb_tests: int,
        nom_test: str,
        filtre_type: str = None
    ) -> List[tuple]:
        """
        Méthode générique pour tester la cohérence d'un générateur
        
        Args:
            niveau: Niveau scolaire
            chapitre: Chapitre
            difficulte: Niveau de difficulté
            nb_tests: Nombre d'exercices à tester
            nom_test: Nom du test (pour affichage)
            filtre_type: Type de figure à filtrer (optionnel, ex: "cercle", "rectangle")
        
        Returns:
            Liste des échecs (tuples de numéro et message d'erreur)
        """
        echecs = []
        exercices_testes = 0
        tentatives = 0
        max_tentatives = nb_tests * 3  # Générer jusqu'à 3x plus pour le filtrage
        
        while exercices_testes < nb_tests and tentatives < max_tentatives:
            tentatives += 1
            i = exercices_testes + 1
            
            try:
                # Générer spec
                specs = self.math_service.generate_math_exercise_specs(
                    niveau=niveau,
                    chapitre=chapitre,
                    difficulte=difficulte,
                    nb_exercices=1
                )
                
                if not specs or len(specs) == 0:
                    continue
                
                spec = specs[0]
                
                # Filtrer par type si demandé
                if filtre_type:
                    if not spec.figure_geometrique or spec.figure_geometrique.type != filtre_type:
                        continue
                
                # Vérifier qu'il y a bien une figure géométrique
                if not spec.figure_geometrique:
                    print(f"   ⚠️  Test {i}: Pas de figure géométrique générée")
                    continue
                
                exercices_testes += 1
                print(f"Test {exercices_testes}/{nb_tests} - {nom_test}")
                print("-"*80)
                
                figure = spec.figure_geometrique
                
                # Points autorisés de la figure
                points_autorises = set(figure.points) if figure.points else set()
                print(f"   Points autorisés: {points_autorises}")
                
                # Longueurs/valeurs de la figure
                valeurs_figure = figure.longueurs_connues or {}
                if hasattr(figure, 'angles_connus') and figure.angles_connus:
                    valeurs_figure.update(figure.angles_connus)
                
                print(f"   Valeurs figure: {valeurs_figure}")
                
                # Générer le texte (avec fallback si IA échoue)
                text = self.text_service._generate_fallback_text(spec)
                
                enonce = text.enonce or ""
                solution = text.solution_redigee or ""
                
                # Extraire les points de l'énoncé et de la solution
                points_enonce = self.checker.extraire_points_geometriques(enonce)
                points_solution = self.checker.extraire_points_geometriques(solution)
                
                print(f"   Points dans énoncé: {points_enonce}")
                print(f"   Points dans solution: {points_solution}")
                
                # Extraire les valeurs numériques
                valeurs_enonce = self.checker.extraire_valeurs_numeriques(enonce)
                valeurs_solution = self.checker.extraire_valeurs_numeriques(solution)
                
                print(f"   Valeurs dans énoncé: {valeurs_enonce}")
                
                # VÉRIFICATIONS DE COHÉRENCE
                erreurs = []
                
                # 1. Vérifier cohérence des points
                erreurs_points = self.checker.verifier_coherence_points(
                    points_autorises,
                    points_enonce,
                    points_solution,
                    f"{nom_test}-{exercices_testes}"
                )
                erreurs.extend(erreurs_points)
                
                # 2. Vérifier cohérence des valeurs (si applicable)
                if valeurs_figure:
                    erreurs_valeurs = self.checker.verifier_coherence_valeurs(
                        valeurs_figure,
                        valeurs_enonce,
                        valeurs_solution,
                        f"{nom_test}-{exercices_testes}",
                        spec=spec
                    )
                    erreurs.extend(erreurs_valeurs)
                
                # 3. Vérifier qu'il y a bien un énoncé
                if not enonce or len(enonce.strip()) < 10:
                    erreurs.append(f"[{nom_test}-{exercices_testes}] Énoncé vide ou trop court")
                
                # Afficher les résultats
                if erreurs:
                    for erreur in erreurs:
                        print(f"   ❌ {erreur}")
                    echecs.append((exercices_testes, erreurs))
                else:
                    print(f"   ✅ COHÉRENCE OK")
                
            except Exception as e:
                error_msg = f"Exception: {str(e)[:150]}"
                print(f"   ❌ {error_msg}")
                echecs.append((exercices_testes, [error_msg]))
            
            print()
        
        # Afficher un avertissement si on n'a pas pu tester assez d'exercices
        if exercices_testes < nb_tests:
            print(f"⚠️  Attention: Seulement {exercices_testes}/{nb_tests} exercices testés après {tentatives} tentatives")
        
        return echecs
    
    def test_all_geometric_generators_summary(self):
        """Test résumé : Vérifier que tous les générateurs géométriques sont cohérents"""
        print("\n" + "="*80)
        print("TEST RÉSUMÉ : TOUS LES GÉNÉRATEURS GÉOMÉTRIQUES")
        print("="*80 + "\n")
        
        generateurs = [
            ("4e", "Théorème de Pythagore", "Pythagore"),
            ("3e", "Trigonométrie", "Trigonométrie"),
            ("6e", "Aires", "Cercles"),
            ("5e", "Aires et périmètres", "Rectangles"),
            ("6e", "Périmètres et aires", "Périmètres/Aires"),
            ("5e", "Triangles", "Triangles"),
        ]
        
        resultats = []
        
        for niveau, chapitre, nom in generateurs:
            print(f"\n🔍 Test rapide : {nom} ({niveau} - {chapitre})")
            print("-"*60)
            
            echecs = self._test_generateur_coherence(
                niveau=niveau,
                chapitre=chapitre,
                difficulte="facile",
                nb_tests=5,  # Test rapide avec 5 exercices
                nom_test=nom
            )
            
            taux_succes = (5 - len(echecs)) / 5 * 100
            resultats.append((nom, taux_succes, len(echecs)))
            
            if len(echecs) == 0:
                print(f"   ✅ {nom}: 100% cohérent")
            else:
                print(f"   ⚠️  {nom}: {taux_succes:.0f}% cohérent ({len(echecs)} échec(s))")
        
        # Afficher le résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ COHÉRENCE TOUS GÉNÉRATEURS GÉOMÉTRIQUES")
        print("="*80)
        
        for nom, taux_succes, nb_echecs in resultats:
            status = "✅" if nb_echecs == 0 else "⚠️"
            print(f"{status} {nom:25s} : {taux_succes:5.0f}% cohérent")
        
        # Calculer le taux global
        taux_global = sum(t for _, t, _ in resultats) / len(resultats)
        print(f"\n{'='*80}")
        print(f"📊 TAUX DE COHÉRENCE GLOBAL : {taux_global:.1f}%")
        print(f"{'='*80}\n")
        
        # Le test passe si le taux global est >= 85%
        assert taux_global >= 85, f"Taux de cohérence global trop faible: {taux_global:.1f}% (min 85%)"


if __name__ == "__main__":
    # Exécution directe
    test = TestGeometricCoherence()
    test.setup_method()
    
    print("\n" + "="*80)
    print("🧪 LANCEMENT DES TESTS DE COHÉRENCE GÉOMÉTRIQUE")
    print("="*80 + "\n")
    
    try:
        # Test résumé d'abord
        test.test_all_geometric_generators_summary()
        
        # Puis tests détaillés
        print("\n" + "="*80)
        print("TESTS DÉTAILLÉS PAR GÉNÉRATEUR")
        print("="*80)
        
        test.test_pythagore_coherence()
        test.test_trigonometrie_coherence()
        test.test_cercles_coherence()
        test.test_rectangles_coherence()
        test.test_perimetre_aire_coherence()
        test.test_triangles_coherence()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS DE COHÉRENCE PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        sys.exit(1)
