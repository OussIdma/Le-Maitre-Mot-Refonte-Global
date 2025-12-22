"""
Tests pour le référentiel curriculum 6e

Ces tests valident:
1. Le chargement du JSON curriculum
2. L'API avec code_officiel
3. La non-régression du mode legacy (niveau + chapitre)
"""

import pytest
import sys
import os

# Ajouter le chemin backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from curriculum.loader import (
    load_curriculum_6e,
    get_curriculum_index,
    get_chapter_by_official_code,
    get_chapters_by_backend_name,
    get_all_official_codes,
    get_exercise_types_for_official_code,
    validate_curriculum,
    CurriculumChapter,
    CurriculumIndex
)


class TestCurriculumLoader:
    """Tests pour le chargement du curriculum"""
    
    def test_load_curriculum_6e(self):
        """Test que le curriculum 6e se charge correctement"""
        index = load_curriculum_6e()
        
        assert index is not None
        assert isinstance(index, CurriculumIndex)
        assert len(index.by_official_code) > 0
    
    def test_all_csv_chapters_loaded(self):
        """Test que tous les 27 chapitres du CSV sont chargés"""
        index = get_curriculum_index()
        
        # 27 chapitres dans le CSV officiel
        expected_count = 27
        assert len(index.by_official_code) == expected_count, \
            f"Attendu {expected_count} chapitres, trouvé {len(index.by_official_code)}"
    
    def test_key_chapters_have_exercise_types(self):
        """Test que les chapitres clés ont des exercise_types non vides"""
        key_codes = [
            "6e_N08",  # Fractions
            "6e_SP03", # Proportionnalité
            "6e_G07",  # Symétrie axiale
            "6e_GM03", # Aire rectangle/carré
        ]
        
        for code in key_codes:
            chapter = get_chapter_by_official_code(code)
            assert chapter is not None, f"Chapitre {code} non trouvé"
            assert len(chapter.exercise_types) > 0, \
                f"Chapitre {code} ({chapter.libelle}) n'a pas d'exercise_types"
    
    def test_get_chapter_by_official_code(self):
        """Test la récupération par code officiel"""
        chapter = get_chapter_by_official_code("6e_N08")
        
        assert chapter is not None
        assert chapter.code_officiel == "6e_N08"
        assert chapter.niveau == "6e"
        assert "Fractions" in chapter.libelle
        assert chapter.chapitre_backend == "Fractions"
    
    def test_get_chapter_invalid_code(self):
        """Test qu'un code invalide retourne None"""
        chapter = get_chapter_by_official_code("INVALID_CODE")
        assert chapter is None
    
    def test_get_chapters_by_backend_name(self):
        """Test la récupération par nom de chapitre backend"""
        chapters = get_chapters_by_backend_name("Fractions")
        
        assert len(chapters) > 0
        for chapter in chapters:
            assert chapter.chapitre_backend == "Fractions"
    
    def test_get_all_official_codes(self):
        """Test la liste de tous les codes"""
        codes = get_all_official_codes()
        
        assert len(codes) == 27
        assert "6e_N01" in codes
        assert "6e_SP04" in codes
    
    def test_get_exercise_types_for_code(self):
        """Test la récupération des types d'exercices"""
        types = get_exercise_types_for_official_code("6e_SP03")
        
        assert len(types) > 0
        assert "PROPORTIONNALITE" in types or "PROP_TABLEAU" in types
    
    def test_curriculum_validation(self):
        """Test le rapport de validation"""
        report = validate_curriculum()
        
        assert report["total_chapters"] == 27
        assert report["chapters_with_generators"] > 0
        assert "prod" in report["chapters_by_status"]


class TestCurriculumStructure:
    """Tests pour la structure des données"""
    
    def test_all_chapters_have_required_fields(self):
        """Test que tous les chapitres ont les champs requis"""
        index = get_curriculum_index()
        
        required_fields = [
            "niveau", "code_officiel", "domaine", "libelle", 
            "chapitre_backend", "exercise_types"
        ]
        
        for code, chapter in index.by_official_code.items():
            for field in required_fields:
                assert hasattr(chapter, field), \
                    f"Chapitre {code} manque le champ {field}"
    
    def test_all_codes_follow_pattern(self):
        """Test que tous les codes suivent le pattern 6e_XXX"""
        index = get_curriculum_index()
        
        import re
        pattern = r"^6e_(N|G|GM|SP)\d{2}$"
        
        for code in index.by_official_code.keys():
            assert re.match(pattern, code), \
                f"Code {code} ne suit pas le pattern attendu"
    
    def test_domaines_are_valid(self):
        """Test que les domaines sont dans les valeurs attendues"""
        index = get_curriculum_index()
        
        valid_domaines = [
            "Nombres et calculs",
            "Géométrie",
            "Grandeurs et mesures",
            "Organisation et gestion de données"
        ]
        
        for chapter in index.by_official_code.values():
            assert chapter.domaine in valid_domaines, \
                f"Domaine invalide: {chapter.domaine}"
    
    def test_difficulte_ranges_are_valid(self):
        """Test que les ranges de difficulté sont valides"""
        index = get_curriculum_index()
        
        for code, chapter in index.by_official_code.items():
            assert 1 <= chapter.difficulte_min <= 3, \
                f"difficulte_min invalide pour {code}"
            assert 1 <= chapter.difficulte_max <= 3, \
                f"difficulte_max invalide pour {code}"
            assert chapter.difficulte_min <= chapter.difficulte_max, \
                f"difficulte_min > difficulte_max pour {code}"


class TestCurriculumIntegration:
    """Tests d'intégration avec les générateurs"""
    
    def test_exercise_types_exist_in_enum(self):
        """Test que tous les exercise_types correspondent à des MathExerciseType valides"""
        from models.math_models import MathExerciseType
        
        index = get_curriculum_index()
        invalid_types = []
        
        for code, chapter in index.by_official_code.items():
            for et in chapter.exercise_types:
                if not hasattr(MathExerciseType, et):
                    invalid_types.append((code, et))
        
        assert len(invalid_types) == 0, \
            f"Types d'exercices invalides: {invalid_types}"
    
    def test_backend_chapters_are_mappable(self):
        """Test que les chapitre_backend correspondent à des chapitres réels"""
        from services.math_generation_service import MathGenerationService
        
        service = MathGenerationService()
        index = get_curriculum_index()
        
        unmappable = []
        for code, chapter in index.by_official_code.items():
            try:
                types = service._map_chapter_to_types(
                    chapter.chapitre_backend, chapter.niveau
                )
                if not types:
                    unmappable.append((code, chapter.chapitre_backend))
            except Exception as e:
                unmappable.append((code, chapter.chapitre_backend, str(e)))
        
        # Note: certains chapitres peuvent ne pas avoir de mapping direct
        # On vérifie juste qu'il n'y a pas trop d'erreurs
        assert len(unmappable) < 10, \
            f"Trop de chapitres non mappables: {unmappable}"


# Tests API (à exécuter avec pytest-asyncio)
class TestAPIWithCodeOfficiel:
    """Tests de l'API avec code_officiel"""
    
    @pytest.mark.asyncio
    async def test_api_with_code_officiel_fractions(self):
        """Test l'API avec code_officiel pour les fractions"""
        from routes.exercises_routes import generate_exercise
        from models.exercise_models import ExerciseGenerateRequest
        
        request = ExerciseGenerateRequest(
            code_officiel="6e_N08",
            difficulte="moyen"
        )
        
        response = await generate_exercise(request)
        
        assert response is not None
        assert response.niveau == "6e"
        # Le chapitre backend pour 6e_N08 est "Fractions"
        assert "Fractions" in response.chapitre or response.chapitre == "Fractions"
        assert response.enonce_html is not None
        # metadata est un dict, pas un objet
        assert response.metadata.get("is_fallback") == False
    
    @pytest.mark.asyncio
    async def test_api_with_code_officiel_proportionnalite(self):
        """Test l'API avec code_officiel pour la proportionnalité"""
        from routes.exercises_routes import generate_exercise
        from models.exercise_models import ExerciseGenerateRequest
        
        request = ExerciseGenerateRequest(
            code_officiel="6e_SP03",
            difficulte="moyen"
        )
        
        response = await generate_exercise(request)
        
        assert response is not None
        assert response.niveau == "6e"
        assert response.enonce_html is not None
    
    @pytest.mark.asyncio
    async def test_api_legacy_mode_unchanged(self):
        """Test que le mode legacy fonctionne toujours"""
        from routes.exercises_routes import generate_exercise
        from models.exercise_models import ExerciseGenerateRequest
        
        request = ExerciseGenerateRequest(
            niveau="6e",
            chapitre="Fractions",
            difficulte="moyen"
        )
        
        response = await generate_exercise(request)
        
        assert response is not None
        assert response.niveau == "6e"
        assert response.chapitre == "Fractions"
        assert response.enonce_html is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
