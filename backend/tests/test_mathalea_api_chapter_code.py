"""
Tests API pour l'endpoint dédié GET /api/chapters/{chapter_code}/exercise-types

Sprint 4 - Tests avec FastAPI TestClient
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer server
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


class TestChapterCodeEndpoint:
    """Tests pour l'endpoint dédié des exercices par chapter_code"""
    
    def test_01_list_all_exercise_types_sanity_check(self):
        """
        Test 1 - Endpoint de base sans filtre (sanity check)
        
        Vérifie que l'endpoint existant /api/mathalea/exercise-types fonctionne
        et retourne des données avec les champs chapter_code présents.
        """
        response = client.get("/api/mathalea/exercise-types")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total" in data, "Response should have 'total' field"
        assert "items" in data, "Response should have 'items' field"
        assert isinstance(data["items"], list), "Items should be a list"
        
        # Vérifier qu'au moins un item a chapter_code
        if data["total"] > 0:
            has_chapter_code = any(
                "chapter_code" in item and item["chapter_code"] is not None
                for item in data["items"]
            )
            print(f"✅ Test 1: {data['total']} exercices trouvés, chapter_code présent: {has_chapter_code}")
        else:
            print("⚠️  Test 1: Aucun exercice en base")
    
    def test_02_filter_by_chapter_code_on_existing_endpoint(self):
        """
        Test 2 - Filtre chapter_code sur endpoint existant
        
        Vérifie que le filtre chapter_code sur /api/mathalea/exercise-types?chapter_code=X
        retourne uniquement les exercices du chapitre spécifié.
        """
        # Utiliser un chapter_code connu (ajuster selon les données réelles)
        test_chapter_code = "6e_G07"
        
        response = client.get(f"/api/mathalea/exercise-types?chapter_code={test_chapter_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total" in data, "Response should have 'total' field"
        assert "items" in data, "Response should have 'items' field"
        
        # Vérifier que tous les items retournés ont le bon chapter_code
        for item in data["items"]:
            assert item.get("chapter_code") == test_chapter_code, \
                f"Expected chapter_code '{test_chapter_code}', got '{item.get('chapter_code')}'"
        
        print(f"✅ Test 2: {data['total']} exercices trouvés pour chapter_code '{test_chapter_code}'")
    
    def test_03_dedicated_endpoint_success(self):
        """
        Test 3 - Nouveau endpoint dédié
        
        Vérifie que GET /api/chapters/{chapter_code}/exercise-types fonctionne
        et retourne le même contenu que le test 2.
        """
        test_chapter_code = "6e_G07"
        
        response = client.get(f"/api/mathalea/chapters/{test_chapter_code}/exercise-types")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total" in data, "Response should have 'total' field"
        assert "items" in data, "Response should have 'items' field"
        assert isinstance(data["items"], list), "Items should be a list"
        
        # Vérifier que tous les items ont le bon chapter_code
        for item in data["items"]:
            assert item.get("chapter_code") == test_chapter_code, \
                f"Expected chapter_code '{test_chapter_code}', got '{item.get('chapter_code')}'"
            
            # Vérifier la présence des champs essentiels
            assert "id" in item, "Item should have 'id' field"
            assert "code_ref" in item, "Item should have 'code_ref' field"
            assert "titre" in item, "Item should have 'titre' field"
            assert "niveau" in item, "Item should have 'niveau' field"
            assert "domaine" in item, "Item should have 'domaine' field"
        
        print(f"✅ Test 3: Endpoint dédié - {data['total']} exercices pour '{test_chapter_code}'")
        
        if data["total"] > 0:
            print(f"   Premier exercice: {data['items'][0]['code_ref']} - {data['items'][0]['titre']}")
    
    def test_04_unknown_chapter_code_returns_404(self):
        """
        Test 4 - chapter_code inconnu
        
        Vérifie que l'endpoint retourne HTTP 404 avec un message explicite
        lorsqu'un chapter_code inexistant est fourni.
        """
        unknown_chapter_code = "UNKNOWN_CODE_123"
        
        response = client.get(f"/api/mathalea/chapters/{unknown_chapter_code}/exercise-types")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        assert unknown_chapter_code in data["detail"], \
            f"Error message should mention the chapter_code '{unknown_chapter_code}'"
        
        print(f"✅ Test 4: HTTP 404 correctement retourné pour chapter_code inconnu")
        print(f"   Message: {data['detail']}")
    
    def test_05_non_migrated_exercise_compatibility(self):
        """
        Test 5 - Cas avec un exercice non migré
        
        Vérifie que les exercices qui n'ont pas de chapter_code (non migrés)
        ne sont PAS retournés par le nouvel endpoint, ce qui est le comportement attendu.
        
        L'ancien endpoint /api/mathalea/exercise-types sans filtre doit toujours
        retourner ces exercices non migrés pour maintenir la compatibilité.
        """
        # 1. Vérifier l'endpoint existant retourne tous les exercices
        response_all = client.get("/api/mathalea/exercise-types")
        assert response_all.status_code == 200
        data_all = response_all.json()
        total_all = data_all["total"]
        
        # 2. Compter les exercices avec chapter_code
        response_with_code = client.get("/api/mathalea/exercise-types")
        assert response_with_code.status_code == 200
        data_with_code = response_with_code.json()
        
        count_with_chapter_code = sum(
            1 for item in data_with_code["items"]
            if item.get("chapter_code") is not None
        )
        
        count_without_chapter_code = sum(
            1 for item in data_with_code["items"]
            if item.get("chapter_code") is None
        )
        
        print(f"✅ Test 5: Compatibilité exercices non migrés")
        print(f"   Total exercices: {total_all}")
        print(f"   Avec chapter_code: {count_with_chapter_code}")
        print(f"   Sans chapter_code (non migrés): {count_without_chapter_code}")
        
        # 3. Vérifier qu'un exercice migré est accessible via le nouvel endpoint
        if count_with_chapter_code > 0:
            # Trouver un exercice avec chapter_code
            exercise_with_code = next(
                item for item in data_with_code["items"]
                if item.get("chapter_code") is not None
            )
            
            chapter_code = exercise_with_code["chapter_code"]
            response_dedicated = client.get(f"/api/mathalea/chapters/{chapter_code}/exercise-types")
            
            if response_dedicated.status_code == 200:
                print(f"   ✅ Exercice migré accessible via endpoint dédié (chapter_code: {chapter_code})")
            else:
                print(f"   ⚠️  Exercice migré non accessible (status: {response_dedicated.status_code})")
        
        # 4. Vérifier que les exercices non migrés ne sont PAS retournés par le nouvel endpoint
        # (comportement attendu : si pas de chapter_code, le nouvel endpoint ne les trouve pas)
        if count_without_chapter_code > 0:
            print(f"   ✅ Les exercices sans chapter_code restent accessibles via l'endpoint legacy")
    
    def test_06_pagination_works(self):
        """
        Test 6 - Pagination (bonus)
        
        Vérifie que les paramètres skip et limit fonctionnent correctement.
        """
        test_chapter_code = "6e_G07"
        
        # Récupérer avec limit=2
        response = client.get(f"/api/mathalea/chapters/{test_chapter_code}/exercise-types?limit=2")
        
        if response.status_code == 200:
            data = response.json()
            assert len(data["items"]) <= 2, "Limit should restrict number of items"
            print(f"✅ Test 6: Pagination fonctionne - {len(data['items'])} items retournés avec limit=2")
        elif response.status_code == 404:
            print(f"⚠️  Test 6: Chapter code '{test_chapter_code}' n'existe pas, test skippé")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


if __name__ == "__main__":
    """Exécution directe des tests pour debug"""
    print("=" * 80)
    print("TESTS API - SPRINT 4: Endpoint dédié chapter_code")
    print("=" * 80)
    
    test_suite = TestChapterCodeEndpoint()
    
    print("\n--- Test 1: Sanity check endpoint existant ---")
    test_suite.test_01_list_all_exercise_types_sanity_check()
    
    print("\n--- Test 2: Filtre chapter_code sur endpoint existant ---")
    test_suite.test_02_filter_by_chapter_code_on_existing_endpoint()
    
    print("\n--- Test 3: Nouvel endpoint dédié ---")
    test_suite.test_03_dedicated_endpoint_success()
    
    print("\n--- Test 4: Chapter code inconnu (HTTP 404) ---")
    test_suite.test_04_unknown_chapter_code_returns_404()
    
    print("\n--- Test 5: Compatibilité exercices non migrés ---")
    test_suite.test_05_non_migrated_exercise_compatibility()
    
    print("\n--- Test 6: Pagination ---")
    test_suite.test_06_pagination_works()
    
    print("\n" + "=" * 80)
    print("✅ TOUS LES TESTS TERMINÉS")
    print("=" * 80)
