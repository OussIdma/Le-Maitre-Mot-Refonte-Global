"""
Tests unitaires pour les générateurs mathématiques
"""
import pytest
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from models.math_models import MathExerciseType
import math


class TestCercleGenerator:
    """Tests pour le générateur de cercles"""
    
    def setup_method(self):
        self.service = MathGenerationService()
    
    def test_generate_cercle_perimetre(self):
        """Test calcul périmètre cercle"""
        spec = self.service._gen_cercle("6e", "Aires", "facile")
        
        assert spec is not None
        assert spec.type_exercice == MathExerciseType.CERCLE
        
        params = spec.parametres
        if params.get('type') == 'perimetre':
            rayon = params['rayon']
            perimetre_attendu = round(2 * math.pi * rayon, 2)
            perimetre_calcule = spec.solution_calculee['perimetre']
            
            assert abs(perimetre_attendu - perimetre_calcule) < 0.01, \
                f"Périmètre incorrect: {perimetre_calcule} != {perimetre_attendu}"
    
    def test_generate_cercle_aire(self):
        """Test calcul aire cercle"""
        # Générer plusieurs fois pour avoir une aire
        for _ in range(10):
            spec = self.service._gen_cercle("6e", "Aires", "facile")
            params = spec.parametres
            
            if params.get('type') == 'aire':
                rayon = params['rayon']
                aire_attendue = round(math.pi * rayon * rayon, 2)
                aire_calculee = spec.solution_calculee['aire']
                
                assert abs(aire_attendue - aire_calculee) < 0.01, \
                    f"Aire incorrecte: {aire_calculee} != {aire_attendue}"
                break
    
    def test_cercle_structure_json(self):
        """Test structure JSON de l'exercice cercle"""
        spec = self.service._gen_cercle("6e", "Aires", "facile")
        
        # Vérifier champs obligatoires
        assert 'type' in spec.parametres
        assert 'rayon' in spec.parametres or 'perimetre' in spec.parametres
        assert 'unite' in spec.solution_calculee
        assert spec.resultat_final is not None
        assert len(spec.etapes_calculees) >= 3


class TestTrigonometrieGenerator:
    """Tests pour le générateur de trigonométrie"""
    
    def setup_method(self):
        self.service = MathGenerationService()
    
    def test_generate_trigonometrie_angle_30(self):
        """Test avec angle remarquable 30°"""
        # Forcer génération facile pour avoir 30°, 45° ou 60°
        spec = self.service._gen_trigonometrie("3e", "Trigonométrie", "facile")
        
        assert spec is not None
        assert spec.type_exercice == MathExerciseType.TRIGONOMETRIE
        
        params = spec.parametres
        angle = params['angle']
        
        # Vérifier que l'angle est bien un des angles remarquables ou valide
        assert 25 <= angle <= 70, f"Angle hors limites: {angle}"
    
    def test_trigonometrie_calculs_coherents(self):
        """Test cohérence des calculs trigonométriques"""
        spec = self.service._gen_trigonometrie("3e", "Trigonométrie", "facile")
        
        params = spec.parametres
        solution = spec.solution_calculee
        
        angle = params['angle']
        resultat = solution['resultat']
        
        # Vérifier que le résultat est positif et réaliste
        assert resultat > 0, "Résultat doit être positif"
        assert resultat < 1000, "Résultat trop grand"
    
    def test_trigonometrie_points_geometriques(self):
        """Test que les points géométriques sont bien définis"""
        spec = self.service._gen_trigonometrie("3e", "Trigonométrie", "facile")
        
        assert spec.figure_geometrique is not None
        assert len(spec.figure_geometrique.points) == 3
        
        # Vérifier que les points sont des lettres majuscules
        for point in spec.figure_geometrique.points:
            assert point.isupper()
            assert len(point) == 1


class TestThalesGenerator:
    """Tests pour le générateur de Thalès"""
    
    def setup_method(self):
        self.service = MathGenerationService()
    
    def test_generate_thales_rapports(self):
        """Test égalité des rapports de Thalès"""
        spec = self.service._gen_thales("3e", "Théorème de Thalès", "facile")
        
        assert spec is not None
        assert spec.type_exercice == MathExerciseType.THALES
        
        params = spec.parametres
        solution = spec.solution_calculee
        
        # Extraire les longueurs
        AD = params['AD']
        DB = params['DB']
        AE = params['AE']
        EC = params['EC']
        
        AB = solution['AB']
        AC = solution['AC']
        
        # Vérifier les sommes
        assert AB == AD + DB, f"AB incorrect: {AB} != {AD} + {DB}"
        assert AC == AE + EC, f"AC incorrect: {AC} != {AE} + {EC}"
        
        # Vérifier l'égalité des rapports
        rapport_AD_AB = round(AD / AB, 4) if AB > 0 else 0
        rapport_AE_AC = round(AE / AC, 4) if AC > 0 else 0
        
        assert abs(rapport_AD_AB - rapport_AE_AC) < 0.01, \
            f"Rapports Thalès non égaux: {rapport_AD_AB} != {rapport_AE_AC}"
    
    def test_thales_5_points(self):
        """Test que Thalès utilise bien 5 points"""
        spec = self.service._gen_thales("3e", "Théorème de Thalès", "facile")
        
        params = spec.parametres
        points = params['points']
        
        assert len(points) == 5, f"Devrait avoir 5 points, a {len(points)}"
        
        # Vérifier que tous sont différents
        assert len(set(points)) == 5, "Points dupliqués détectés"
    
    def test_thales_figure_geometrique(self):
        """Test structure de la figure géométrique"""
        spec = self.service._gen_thales("3e", "Théorème de Thalès", "facile")
        
        assert spec.figure_geometrique is not None
        assert spec.figure_geometrique.type == "thales"
        assert len(spec.figure_geometrique.points) == 5
        
        # Vérifier longueurs_connues
        longueurs = spec.figure_geometrique.longueurs_connues
        assert len(longueurs) == 4, "Devrait avoir 4 longueurs connues"


# Fonction pour exécuter les tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
