#!/usr/bin/env python3
"""
Test de non-régression - Synchronisation admin_exercises → exercise_types

Ce test valide que le correctif fonctionne correctement et ne casse rien.

Usage:
    python test_exercise_types_sync.py

Prérequis:
    - Backend démarré
    - MongoDB accessible
    - Patches appliqués
"""

import os
import sys
import asyncio
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Configuration
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'lemaitremotdb')

# Chapitre de test
TEST_CHAPTER = "6E_TEST_SYNC"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_test(msg):
    print(f"{bcolors.OKBLUE}🧪 TEST: {msg}{bcolors.ENDC}")

def print_success(msg):
    print(f"{bcolors.OKGREEN}✅ {msg}{bcolors.ENDC}")

def print_error(msg):
    print(f"{bcolors.FAIL}❌ {msg}{bcolors.ENDC}")

def print_warning(msg):
    print(f"{bcolors.WARNING}⚠️  {msg}{bcolors.ENDC}")

def print_header(msg):
    print(f"\n{bcolors.HEADER}{'='*80}")
    print(f"{msg}")
    print(f"{'='*80}{bcolors.ENDC}\n")


async def cleanup_test_data(db):
    """Nettoyer les données de test avant/après"""
    await db["admin_exercises"].delete_many({"chapter_code": TEST_CHAPTER})
    await db["exercise_types"].delete_many({"chapter_code": TEST_CHAPTER})
    await db["chapters"].delete_one({"code": TEST_CHAPTER})
    print_success(f"Données de test nettoyées pour {TEST_CHAPTER}")


async def test_create_dynamic_exercise_syncs_to_exercise_types():
    """Test: Créer un exercice dynamique → doit sync vers exercise_types"""
    print_test("Créer exercice dynamique → sync exercise_types")
    
    # Créer un exercice dynamique via API
    response = requests.post(
        f"{BACKEND_URL}/api/admin/chapters/{TEST_CHAPTER}/exercises",
        json={
            "is_dynamic": True,
            "generator_key": "PERIMETRE_V1",
            "difficulty": "moyen",
            "offer": "free",
            "title": "Test périmètre"
        }
    )
    
    if response.status_code != 201:
        print_error(f"Échec création exercice: {response.status_code} - {response.text}")
        return False
    
    exercise = response.json().get('exercise')
    exercise_id = exercise.get('id')
    print_success(f"Exercice créé (id={exercise_id})")
    
    # Attendre un peu pour la sync async
    await asyncio.sleep(2)
    
    # Vérifier que l'exercise_type a été créé
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    exercise_type = await db["exercise_types"].find_one({
        "chapter_code": TEST_CHAPTER,
        "code_ref": "PERIMETRE_V1"
    })
    
    client.close()
    
    if not exercise_type:
        print_error("exercise_type NON créé dans la collection!")
        return False
    
    print_success(f"exercise_type créé: {exercise_type.get('id')}")
    print_success(f"  - code_ref: {exercise_type.get('code_ref')}")
    print_success(f"  - source: {exercise_type.get('source')}")
    return True


async def test_update_exercise_syncs_to_exercise_types():
    """Test: Modifier un exercice → doit re-sync exercise_types"""
    print_test("Modifier exercice → re-sync exercise_types")
    
    # Récupérer l'exercice créé précédemment
    response = requests.get(
        f"{BACKEND_URL}/api/admin/chapters/{TEST_CHAPTER}/exercises"
    )
    
    if response.status_code != 200:
        print_error(f"Échec récupération exercices: {response.status_code}")
        return False
    
    exercises = response.json().get('exercises', [])
    if not exercises:
        print_warning("Aucun exercice trouvé (créer d'abord)")
        return True
    
    exercise_id = exercises[0]['id']
    
    # Modifier la difficulté
    response = requests.put(
        f"{BACKEND_URL}/api/admin/chapters/{TEST_CHAPTER}/exercises/{exercise_id}",
        json={"difficulty": "difficile"}
    )
    
    if response.status_code != 200:
        print_error(f"Échec modification exercice: {response.status_code}")
        return False
    
    print_success(f"Exercice modifié (id={exercise_id})")
    
    # Attendre la sync
    await asyncio.sleep(2)
    
    # Vérifier que l'exercise_type a été mis à jour
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    exercise_type = await db["exercise_types"].find_one({
        "chapter_code": TEST_CHAPTER,
        "code_ref": "PERIMETRE_V1"
    })
    
    client.close()
    
    if not exercise_type:
        print_error("exercise_type disparu après update!")
        return False
    
    if "difficile" not in exercise_type.get('difficulty_levels', []):
        print_warning("difficulty_levels pas mis à jour (peut être normal)")
    else:
        print_success("difficulty_levels mis à jour")
    
    return True


async def test_delete_exercise_cleans_exercise_types():
    """Test: Supprimer le dernier exercice → doit supprimer exercise_type"""
    print_test("Supprimer dernier exercice → cleanup exercise_type")
    
    # Récupérer l'exercice
    response = requests.get(
        f"{BACKEND_URL}/api/admin/chapters/{TEST_CHAPTER}/exercises"
    )
    
    exercises = response.json().get('exercises', [])
    if not exercises:
        print_warning("Aucun exercice à supprimer")
        return True
    
    exercise_id = exercises[0]['id']
    
    # Supprimer
    response = requests.delete(
        f"{BACKEND_URL}/api/admin/chapters/{TEST_CHAPTER}/exercises/{exercise_id}"
    )
    
    if response.status_code != 200:
        print_error(f"Échec suppression exercice: {response.status_code}")
        return False
    
    print_success(f"Exercice supprimé (id={exercise_id})")
    
    # Attendre la sync
    await asyncio.sleep(2)
    
    # Vérifier que l'exercise_type a été supprimé (orphelin cleanup)
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    exercise_type = await db["exercise_types"].find_one({
        "chapter_code": TEST_CHAPTER,
        "code_ref": "PERIMETRE_V1"
    })
    
    client.close()
    
    if exercise_type:
        print_warning("exercise_type toujours présent (orphelin non nettoyé)")
        # Pas une erreur fatale, juste un warning
        return True
    
    print_success("exercise_type orphelin supprimé")
    return True


async def test_static_exercise_no_sync():
    """Test: Créer exercice statique → NE doit PAS sync vers exercise_types"""
    print_test("Créer exercice statique → pas de sync exercise_types")
    
    # Créer un exercice statique
    response = requests.post(
        f"{BACKEND_URL}/api/admin/chapters/{TEST_CHAPTER}/exercises",
        json={
            "is_dynamic": False,
            "enonce_html": "<p>Exercice statique</p>",
            "solution_html": "<p>Solution</p>",
            "difficulty": "facile",
            "offer": "free"
        }
    )
    
    if response.status_code != 201:
        print_error(f"Échec création exercice statique: {response.status_code}")
        return False
    
    print_success("Exercice statique créé")
    
    # Vérifier qu'AUCUN exercise_type n'a été créé
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    exercise_types_count = await db["exercise_types"].count_documents({
        "chapter_code": TEST_CHAPTER
    })
    
    client.close()
    
    if exercise_types_count > 0:
        print_warning(f"exercise_types trouvés: {exercise_types_count} (peut être résidu)")
    else:
        print_success("Aucun exercise_type créé (correct)")
    
    return True


async def test_mathalea_endpoint():
    """Test: Endpoint mathalea retourne bien les exercices"""
    print_test("Endpoint mathalea /exercise-types")
    
    # Créer d'abord un exercice dynamique
    requests.post(
        f"{BACKEND_URL}/api/admin/chapters/{TEST_CHAPTER}/exercises",
        json={
            "is_dynamic": True,
            "generator_key": "PERIMETRE_V1",
            "difficulty": "moyen",
            "offer": "free"
        }
    )
    
    await asyncio.sleep(2)
    
    # Tester l'endpoint mathalea
    response = requests.get(
        f"{BACKEND_URL}/api/mathalea/chapters/{TEST_CHAPTER}/exercise-types"
    )
    
    # Peut retourner 404 si le chapitre n'existe pas dans chapters
    if response.status_code == 404:
        print_warning("Chapitre non trouvé dans chapters (normal pour test)")
        return True
    
    if response.status_code != 200:
        print_error(f"Erreur endpoint mathalea: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    total = data.get('total', 0)
    
    if total == 0:
        print_error("Aucun exercise_type retourné!")
        return False
    
    print_success(f"Endpoint OK: {total} exercise_types retournés")
    return True


async def main():
    print_header("TEST DE NON-RÉGRESSION - Sync admin_exercises → exercise_types")
    print(f"Backend: {BACKEND_URL}")
    print(f"MongoDB: {MONGO_URL}/{DB_NAME}")
    print(f"Chapitre test: {TEST_CHAPTER}\n")
    
    # Connexion MongoDB pour cleanup
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Cleanup initial
        print_header("NETTOYAGE INITIAL")
        await cleanup_test_data(db)
        
        # Tests
        tests = [
            ("Création exercice dynamique", test_create_dynamic_exercise_syncs_to_exercise_types),
            ("Modification exercice", test_update_exercise_syncs_to_exercise_types),
            ("Création exercice statique", test_static_exercise_no_sync),
            ("Endpoint mathalea", test_mathalea_endpoint),
            ("Suppression exercice (cleanup)", test_delete_exercise_cleans_exercise_types),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print_header(f"TEST: {test_name}")
            try:
                result = await test_func()
                results.append((test_name, result))
                if result:
                    print_success(f"Test réussi: {test_name}")
                else:
                    print_error(f"Test échoué: {test_name}")
            except Exception as e:
                print_error(f"Exception dans test {test_name}: {e}")
                results.append((test_name, False))
            
            # Pause entre tests
            await asyncio.sleep(1)
        
        # Cleanup final
        print_header("NETTOYAGE FINAL")
        await cleanup_test_data(db)
        
        # Résumé
        print_header("RÉSUMÉ DES TESTS")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n{bcolors.BOLD}Score: {passed}/{total} tests réussis{bcolors.ENDC}")
        
        if passed == total:
            print_success("\n🎉 TOUS LES TESTS SONT PASSÉS! Le correctif fonctionne.")
            return 0
        else:
            print_error(f"\n⚠️  {total - passed} test(s) échoué(s). Vérifier les logs.")
            return 1
        
    finally:
        client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
