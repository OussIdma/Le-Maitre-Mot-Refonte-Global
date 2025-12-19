"""
Tests pour le catalogue unifié (Sprint F.2)

Couvre:
- GET /api/catalogue/levels
- GET /api/catalogue/levels/{niveau}/chapters
- GET /api/catalogue/exercise-types (avec filtres)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
import sys
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app


@pytest_asyncio.fixture
async def client():
    """Client HTTP async pour les tests"""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# TESTS GET /api/catalogue/levels
# ============================================================================

@pytest.mark.asyncio
async def test_get_levels(client):
    """
    TEST 1: GET /api/catalogue/levels
    Retourne au moins les niveaux de collège existants dans ExerciseType
    """
    response = await client.get("/api/catalogue/levels")
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier que c'est une liste
    assert isinstance(data, list)
    
    # Vérifier que les niveaux de collège sont présents
    # (au moins un niveau doit être présent après la migration F.1)
    assert len(data) > 0
    
    # Vérifier que les niveaux sont triés dans l'ordre
    niveaux_college = ["6e", "5e", "4e", "3e"]
    niveaux_presents = [n for n in data if n in niveaux_college]
    
    assert len(niveaux_presents) >= 1
    
    # Vérifier l'ordre
    for i in range(len(niveaux_presents) - 1):
        assert niveaux_college.index(niveaux_presents[i]) < niveaux_college.index(niveaux_presents[i+1])
    
    print(f"✓ Niveaux disponibles: {data}")


# ============================================================================
# TESTS GET /api/catalogue/levels/{niveau}/chapters
# ============================================================================

@pytest.mark.asyncio
async def test_get_chapters_for_6e(client):
    """
    TEST 2: GET /api/catalogue/levels/6e/chapters
    Pour le niveau 6e, retourne une liste de chapitres avec nb_exercises
    """
    response = await client.get("/api/catalogue/levels/6e/chapters")
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier que c'est une liste
    assert isinstance(data, list)
    
    # Chaque chapitre doit avoir une structure complète
    for chapter in data:
        assert "id" in chapter
        assert "titre" in chapter
        assert "niveau" in chapter
        assert chapter["niveau"] == "6e"
        assert "domaine" in chapter
        assert "nb_exercises" in chapter
        assert isinstance(chapter["nb_exercises"], int)
    
    # Vérifier que les chapitres sont triés par ordre
    ordres = [ch["ordre"] for ch in data]
    assert ordres == sorted(ordres)
    
    print(f"✓ {len(data)} chapitres pour 6e")


@pytest.mark.asyncio
async def test_get_chapters_invalid_niveau(client):
    """
    TEST 3: GET /api/catalogue/levels/{niveau}/chapters avec niveau invalide
    Doit retourner une erreur 404
    """
    response = await client.get("/api/catalogue/levels/CE2/chapters")
    
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]
    
    print("✓ Erreur 404 pour niveau invalide")


# ============================================================================
# TESTS GET /api/catalogue/exercise-types
# ============================================================================

@pytest.mark.asyncio
async def test_get_all_exercise_types(client):
    """
    TEST 4: GET /api/catalogue/exercise-types sans filtre
    Retourne tous les ExerciseType (TEMPLATE + LEGACY)
    """
    response = await client.get("/api/catalogue/exercise-types")
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier que c'est une liste
    assert isinstance(data, list)
    
    # Doit avoir au moins les ExerciseTypes legacy créés en F.1
    assert len(data) >= 10
    
    # Vérifier la structure de chaque item
    for item in data[:5]:  # Vérifier les 5 premiers
        assert "id" in item
        assert "code_ref" in item
        assert "titre" in item
        assert "niveau" in item
        assert "domaine" in item
        assert "generator_kind" in item
        assert "difficulty_levels" in item
        assert "is_legacy" in item
        assert isinstance(item["is_legacy"], bool)
    
    # Compter LEGACY vs autres
    legacy_count = sum(1 for item in data if item["is_legacy"])
    template_count = sum(1 for item in data if not item["is_legacy"])
    
    print(f"✓ Total: {len(data)} ExerciseTypes (Legacy: {legacy_count}, Template: {template_count})")


@pytest.mark.asyncio
async def test_filter_by_niveau(client):
    """
    TEST 5: GET /api/catalogue/exercise-types?niveau=5e
    Ne retourne que les ExerciseType de niveau 5e
    """
    response = await client.get("/api/catalogue/exercise-types?niveau=5e")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Vérifier que tous les items sont de niveau 5e
    for item in data:
        assert item["niveau"] == "5e"
    
    print(f"✓ {len(data)} ExerciseTypes pour 5e")


@pytest.mark.asyncio
async def test_filter_by_niveau_and_domaine(client):
    """
    TEST 6: GET /api/catalogue/exercise-types?niveau=5e&domaine=Espace et géométrie
    Filtre bien par domaine
    """
    response = await client.get(
        "/api/catalogue/exercise-types",
        params={"niveau": "5e", "domaine": "Espace et géométrie"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    
    # Vérifier que tous les items correspondent aux filtres
    for item in data:
        assert item["niveau"] == "5e"
        assert item["domaine"] == "Espace et géométrie"
    
    print(f"✓ {len(data)} ExerciseTypes pour 5e / Géométrie")


@pytest.mark.asyncio
async def test_filter_by_generator_kind_legacy(client):
    """
    TEST 7: GET /api/catalogue/exercise-types?generator_kind=LEGACY
    Ne retourne que les ExerciseType LEGACY
    """
    response = await client.get("/api/catalogue/exercise-types?generator_kind=legacy")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Vérifier que tous les items sont LEGACY
    for item in data:
        assert item["generator_kind"] == "legacy"
        assert item["is_legacy"] == True
    
    print(f"✓ {len(data)} ExerciseTypes LEGACY")


@pytest.mark.asyncio
async def test_filter_by_generator_kind_template(client):
    """
    TEST 8: GET /api/catalogue/exercise-types?generator_kind=TEMPLATE
    Ne retourne que les ExerciseType TEMPLATE
    """
    response = await client.get("/api/catalogue/exercise-types?generator_kind=template")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    
    # Vérifier que tous les items sont TEMPLATE
    for item in data:
        assert item["generator_kind"] == "template"
        assert item["is_legacy"] == False
    
    print(f"✓ {len(data)} ExerciseTypes TEMPLATE")


@pytest.mark.asyncio
async def test_chapitre_info_populated(client):
    """
    TEST 9: Vérifier que les infos de chapitre sont bien remplies
    """
    response = await client.get("/api/catalogue/exercise-types?niveau=3e&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    
    # Au moins un item doit avoir les infos de chapitre
    items_with_chapter = [item for item in data if item.get("chapitre")]
    
    assert len(items_with_chapter) > 0
    
    # Vérifier la structure du chapitre
    for item in items_with_chapter:
        chapter = item["chapitre"]
        assert "id" in chapter
        assert "titre" in chapter
        # code est optionnel
    
    print(f"✓ {len(items_with_chapter)}/{len(data)} items avec infos chapitre")


@pytest.mark.asyncio
async def test_pagination(client):
    """
    TEST 10: Vérifier que la pagination fonctionne
    """
    # Premier appel avec limit=5
    response1 = await client.get("/api/catalogue/exercise-types?limit=5")
    
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) <= 5
    
    # Deuxième appel avec skip=5, limit=5
    response2 = await client.get("/api/catalogue/exercise-types?skip=5&limit=5")
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) <= 5
    
    # Les deux pages doivent être différentes
    if len(data1) > 0 and len(data2) > 0:
        assert data1[0]["id"] != data2[0]["id"]
    
    print("✓ Pagination fonctionne")


# ============================================================================
# TESTS DE NON-RÉGRESSION
# ============================================================================

@pytest.mark.asyncio
async def test_mathalea_endpoints_still_work(client):
    """
    TEST 11: Vérifier que les endpoints MathALÉA existants fonctionnent toujours
    """
    # Test endpoint exercise-types original
    response = await client.get("/api/mathalea/exercise-types?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    
    print("✓ Endpoints MathALÉA existants fonctionnent")
