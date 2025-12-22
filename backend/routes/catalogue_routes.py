"""
Routes pour le catalogue unifié d'exercices (Sprint F.2)

Endpoints:
- GET /api/catalogue/levels : Liste des niveaux
- GET /api/catalogue/levels/{niveau}/chapters : Chapitres d'un niveau
- GET /api/catalogue/exercise-types : Liste filtrée des ExerciseTypes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os
from collections import defaultdict

from backend.models.catalogue_models import ChapterWithStats, CatalogueExerciseType
from backend.models.mathalea_models import ExerciseType
from backend.services.chapter_service import ChapterService

# Configuration MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.mathalea_db

# Collections
exercise_types_collection = db.exercise_types

# Services
chapter_service = ChapterService(db)

router = APIRouter(prefix="/api/catalogue", tags=["Catalogue"])


# Mapping des chapitres par niveau/domaine
# Cette structure peut être étendue ou remplacée par une collection MongoDB dédiée
CHAPITRES_STRUCTURE = {
    "6e": {
        "Nombres et calculs": [
            {"id": "6_calc_decimaux", "titre": "Nombres décimaux", "code": "6N10", "ordre": 1},
            {"id": "6_fractions", "titre": "Fractions", "code": "6N20", "ordre": 2},
            {"id": "6_proportionnalite", "titre": "Proportionnalité", "code": "6N30", "ordre": 3},
            {"id": "6_pourcentages", "titre": "Pourcentages", "code": "6N31", "ordre": 4},
        ],
        "Espace et géométrie": [
            {"id": "6_symetrie_axiale", "titre": "Symétrie axiale", "code": "6G20", "ordre": 10},
            {"id": "6_triangles", "titre": "Triangles", "code": "6G10", "ordre": 11},
            {"id": "6_rectangles", "titre": "Quadrilatères", "code": "6G11", "ordre": 12},
            {"id": "6_cercle", "titre": "Cercle", "code": "6G15", "ordre": 13},
            {"id": "6_aires_perimetres", "titre": "Aires et périmètres", "code": "6G30", "ordre": 14},
            {"id": "6_volumes", "titre": "Volumes", "code": "6G40", "ordre": 15},
        ],
        "Organisation et gestion de données": [
            {"id": "6_statistiques", "titre": "Statistiques", "code": "6D10", "ordre": 20},
        ]
    },
    "5e": {
        "Nombres et calculs": [
            {"id": "5_relatifs", "titre": "Nombres relatifs", "code": "5N10", "ordre": 1},
            {"id": "5_fractions", "titre": "Fractions", "code": "5N20", "ordre": 2},
            {"id": "5_decimaux", "titre": "Nombres décimaux", "code": "5N11", "ordre": 3},
            {"id": "5_proportionnalite", "titre": "Proportionnalité", "code": "5N30", "ordre": 4},
            {"id": "5_pourcentages", "titre": "Pourcentages", "code": "5N31", "ordre": 5},
        ],
        "Espace et géométrie": [
            {"id": "5_symetrie_centrale", "titre": "Symétrie centrale", "code": "5G20", "ordre": 10},
            {"id": "5_triangles", "titre": "Triangles", "code": "5G10", "ordre": 11},
            {"id": "5_rectangles", "titre": "Parallélogrammes", "code": "5G11", "ordre": 12},
            {"id": "5_cercle", "titre": "Cercle", "code": "5G15", "ordre": 13},
            {"id": "5_aires_perimetres", "titre": "Aires et périmètres", "code": "5G30", "ordre": 14},
            {"id": "5_volumes", "titre": "Volumes", "code": "5G40", "ordre": 15},
        ],
        "Organisation et gestion de données": [
            {"id": "5_statistiques", "titre": "Statistiques", "code": "5D10", "ordre": 20},
        ]
    },
    "4e": {
        "Nombres et calculs": [
            {"id": "4_relatifs", "titre": "Nombres relatifs", "code": "4N10", "ordre": 1},
            {"id": "4_fractions", "titre": "Fractions", "code": "4N20", "ordre": 2},
            {"id": "4_puissances", "titre": "Puissances", "code": "4N25", "ordre": 3},
            {"id": "4_calcul_litteral", "titre": "Calcul littéral", "code": "4N40", "ordre": 4},
            {"id": "4_equations", "titre": "Équations", "code": "4N41", "ordre": 5},
            {"id": "4_proportionnalite", "titre": "Proportionnalité", "code": "4N30", "ordre": 6},
            {"id": "4_pourcentages", "titre": "Pourcentages", "code": "4N31", "ordre": 7},
        ],
        "Espace et géométrie": [
            {"id": "4_triangles", "titre": "Triangles", "code": "4G10", "ordre": 10},
            {"id": "4_pythagore", "titre": "Théorème de Pythagore", "code": "4G11", "ordre": 11},
            {"id": "4_aires_perimetres", "titre": "Aires et périmètres", "code": "4G30", "ordre": 14},
            {"id": "4_volumes", "titre": "Volumes", "code": "4G40", "ordre": 15},
        ],
        "Organisation et gestion de données": [
            {"id": "4_statistiques", "titre": "Statistiques", "code": "4D10", "ordre": 20},
            {"id": "4_probabilites", "titre": "Probabilités", "code": "4D20", "ordre": 21},
        ]
    },
    "3e": {
        "Nombres et calculs": [
            {"id": "3_relatifs", "titre": "Nombres relatifs", "code": "3N10", "ordre": 1},
            {"id": "3_fractions", "titre": "Fractions", "code": "3N20", "ordre": 2},
            {"id": "3_puissances", "titre": "Puissances", "code": "3N25", "ordre": 3},
            {"id": "3_calcul_litteral", "titre": "Calcul littéral", "code": "3N40", "ordre": 4},
            {"id": "3_equations", "titre": "Équations", "code": "3N41", "ordre": 5},
            {"id": "3_proportionnalite", "titre": "Proportionnalité", "code": "3N30", "ordre": 6},
            {"id": "3_pourcentages", "titre": "Pourcentages", "code": "3N31", "ordre": 7},
        ],
        "Espace et géométrie": [
            {"id": "3_triangles", "titre": "Triangles", "code": "3G10", "ordre": 10},
            {"id": "3_pythagore", "titre": "Théorème de Pythagore", "code": "3G11", "ordre": 11},
            {"id": "3_thales", "titre": "Théorème de Thalès", "code": "3G12", "ordre": 12},
            {"id": "3_trigonometrie", "titre": "Trigonométrie", "code": "3G15", "ordre": 13},
            {"id": "3_volumes", "titre": "Volumes", "code": "3G40", "ordre": 15},
        ],
        "Organisation et gestion de données": [
            {"id": "3_statistiques", "titre": "Statistiques", "code": "3D10", "ordre": 20},
            {"id": "3_probabilites", "titre": "Probabilités", "code": "3D20", "ordre": 21},
        ]
    }
}


def get_chapter_info(chapitre_id: str) -> Optional[dict]:
    """Récupère les infos d'un chapitre à partir de son ID"""
    for niveau, domaines in CHAPITRES_STRUCTURE.items():
        for domaine, chapitres in domaines.items():
            for chapitre in chapitres:
                if chapitre["id"] == chapitre_id:
                    return {
                        **chapitre,
                        "niveau": niveau,
                        "domaine": domaine
                    }
    return None


@router.get("/levels", response_model=List[str])
async def get_levels():
    """
    Récupère la liste des niveaux disponibles
    
    Returns:
        Liste des niveaux (6e, 5e, 4e, 3e)
    """
    # Récupérer les niveaux distincts depuis la DB
    levels = await exercise_types_collection.distinct("niveau")
    
    # Trier dans l'ordre du collège
    ordre_college = ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"]
    levels_sorted = sorted(
        [l for l in levels if l in ordre_college],
        key=lambda x: ordre_college.index(x)
    )
    
    return levels_sorted


@router.get("/levels/{niveau}/chapters", response_model=List[ChapterWithStats])
async def get_chapters_for_level(niveau: str):
    """
    Récupère la liste des chapitres pour un niveau donné
    
    Args:
        niveau: Niveau scolaire (6e, 5e, 4e, 3e, 2nde, 1re, Tale)
        
    Returns:
        Liste des chapitres avec nombre d'exercices
    """
    # Récupérer les chapitres depuis MongoDB
    chapters = await chapter_service.get_chapters_by_niveau(niveau)
    
    if not chapters:
        # Fallback sur CHAPITRES_STRUCTURE si aucun chapitre trouvé dans MongoDB
        if niveau not in CHAPITRES_STRUCTURE:
            raise HTTPException(status_code=404, detail=f"Niveau '{niveau}' non trouvé")
        
        # Utiliser l'ancienne logique comme fallback
        chapitres_avec_stats = []
        for domaine, chapitres_list in CHAPITRES_STRUCTURE[niveau].items():
            for chapitre_def in chapitres_list:
                count = await exercise_types_collection.count_documents({
                    "niveau": niveau,
                    "domaine": domaine,
                    "$or": [
                        {"chapitre_id": chapitre_def["titre"]},
                        {"chapitre_id": {"$in": [chapitre_def["titre"], chapitre_def["id"]]}}
                    ]
                })
                
                chapitre_with_stats = ChapterWithStats(
                    id=chapitre_def["id"],
                    titre=chapitre_def["titre"],
                    niveau=niveau,
                    domaine=domaine,
                    code=chapitre_def.get("code"),
                    ordre=chapitre_def.get("ordre", 0),
                    nb_exercises=count
                )
                
                chapitres_avec_stats.append(chapitre_with_stats)
        
        # Trier par ordre
        chapitres_avec_stats.sort(key=lambda x: x.ordre)
        
        return chapitres_avec_stats
    
    # Nouvelle logique : utiliser les chapitres depuis MongoDB
    chapitres_avec_stats = []
    
    for chapter in chapters:
        # Compter le nombre d'ExerciseTypes pour ce chapitre
        # Chercher par code, legacy_code ou chapitre_id
        count = await exercise_types_collection.count_documents({
            "niveau": niveau,
            "$or": [
                {"chapitre_id": chapter["code"]},
                {"chapitre_id": chapter.get("legacy_code")},
                {"chapter_code": chapter["code"]}
            ]
        })
        
        chapitre_with_stats = ChapterWithStats(
            id=chapter["code"],
            titre=chapter["titre"],
            niveau=chapter["niveau"],
            domaine=chapter.get("domaine_legacy", chapter["domaine"]),  # Utiliser domaine_legacy pour compatibilité
            code=chapter["code"],
            ordre=chapter.get("ordre", 0),
            nb_exercises=count
        )
        
        chapitres_avec_stats.append(chapitre_with_stats)
    
    # Trier par domaine puis ordre
    chapitres_avec_stats.sort(key=lambda x: (x.domaine, x.ordre))
    
    return chapitres_avec_stats



@router.get("/chapters", response_model=List[ChapterWithStats])
async def get_chapters(
    niveau: Optional[str] = Query(None, description="Filtrer par niveau (ex: '6e', '2nde')"),
    domaine: Optional[str] = Query(None, description="Filtrer par domaine")
):
    """
    Récupère la liste des chapitres avec filtres optionnels
    
    Args:
        niveau: Niveau scolaire (optionnel)
        domaine: Domaine mathématique (optionnel)
        
    Returns:
        Liste des chapitres avec nombre d'exercices
    """
    if niveau:
        chapters = await chapter_service.get_chapters_by_niveau_and_domaine(niveau, domaine)
    else:
        # Récupérer tous les chapitres
        chapters = await chapter_service.collection.find({}, {"_id": 0}).sort([("niveau", 1), ("domaine", 1), ("ordre", 1)]).to_list(None)
    
    if not chapters:
        return []
    
    chapitres_avec_stats = []
    
    for chapter in chapters:
        # Compter le nombre d'ExerciseTypes pour ce chapitre
        count = await exercise_types_collection.count_documents({
            "$or": [
                {"chapitre_id": chapter["code"]},
                {"chapitre_id": chapter.get("legacy_code")},
                {"chapter_code": chapter["code"]}
            ]
        })
        
        chapitre_with_stats = ChapterWithStats(
            id=chapter["code"],
            titre=chapter["titre"],
            niveau=chapter["niveau"],
            domaine=chapter.get("domaine_legacy", chapter["domaine"]),
            code=chapter["code"],
            ordre=chapter.get("ordre", 0),
            nb_exercises=count
        )
        
        chapitres_avec_stats.append(chapitre_with_stats)
    
    return chapitres_avec_stats


@router.get("/exercise-types", response_model=List[CatalogueExerciseType])
async def get_catalogue_exercise_types(
    niveau: Optional[str] = Query(None, description="Filtrer par niveau"),
    chapitre_id: Optional[str] = Query(None, description="Filtrer par chapitre"),
    domaine: Optional[str] = Query(None, description="Filtrer par domaine"),
    generator_kind: Optional[str] = Query(None, description="Filtrer par type (legacy, template)"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """
    Récupère la liste des ExerciseTypes avec filtres
    
    Catalogue unifié legacy + template
    
    Args:
        niveau: Niveau scolaire
        chapitre_id: ID du chapitre
        domaine: Domaine mathématique
        generator_kind: Type de générateur
        limit: Nombre max de résultats
        skip: Nombre à ignorer (pagination)
        
    Returns:
        Liste des ExerciseTypes enrichis
    """
    # Construire la query MongoDB
    query = {}
    
    if niveau:
        query["niveau"] = niveau
    
    if domaine:
        query["domaine"] = domaine
    
    if generator_kind:
        query["generator_kind"] = generator_kind.lower()
    
    if chapitre_id:
        # Chercher par ID de chapitre ou par titre de chapitre
        chapitre_info = get_chapter_info(chapitre_id)
        if chapitre_info:
            query["chapitre_id"] = {"$in": [chapitre_info["titre"], chapitre_id]}
        else:
            query["chapitre_id"] = chapitre_id
    
    # Récupérer les ExerciseTypes
    cursor = exercise_types_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
    exercise_types = await cursor.to_list(length=limit)
    
    # Enrichir avec les infos du catalogue
    catalogue_items = []
    for et_dict in exercise_types:
        try:
            et = ExerciseType(**et_dict)
            
            # Récupérer les infos du chapitre
            chapitre_dict = None
            if et.chapitre_id:
                # Essayer de trouver le chapitre dans la structure
                for niv, domaines in CHAPITRES_STRUCTURE.items():
                    if niv == et.niveau:
                        for dom, chaps in domaines.items():
                            for ch in chaps:
                                if ch["titre"] == et.chapitre_id or ch["id"] == et.chapitre_id:
                                    chapitre_dict = {
                                        "id": ch["id"],
                                        "titre": ch["titre"],
                                        "code": ch.get("code")
                                    }
                                    break
                            if chapitre_dict:
                                break
            
            catalogue_item = CatalogueExerciseType(
                id=et.id,
                code_ref=et.code_ref,
                titre=et.titre,
                niveau=et.niveau,
                domaine=et.domaine,
                chapitre=chapitre_dict,
                generator_kind=et.generator_kind.value,
                difficulty_levels=et.difficulty_levels or [],
                min_questions=et.min_questions,
                max_questions=et.max_questions,
                default_questions=et.default_questions,
                supports_ai_enonce=et.supports_ai_enonce,
                supports_ai_correction=et.supports_ai_correction,
                is_legacy=(et.generator_kind.value == "legacy")
            )
            
            catalogue_items.append(catalogue_item)
            
        except Exception as e:
            # Log l'erreur mais continue
            print(f"Erreur parsing ExerciseType {et_dict.get('id')}: {e}")
            continue
    
    return catalogue_items


# Export du router
__all__ = ["router"]
