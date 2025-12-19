#!/usr/bin/env python3
"""
Test du nouvel endpoint créé dans SPRINT 4 : GET /api/chapters/{chapter_code}/exercise-types

Contexte :
- Nouvel endpoint dédié pour récupérer les ExerciseType d'un chapitre MathALÉA
- Base URL backend : https://math-exercise-sync.preview.emergentagent.com
- Collection MongoDB : exercise_types avec champ `chapter_code`

Tests à effectuer :
1. Test succès avec chapter_code valide
2. Test HTTP 404 avec chapter_code inexistant  
3. Test pagination
4. Test compatibilité backward
5. Test avec chapter_code ayant 0 exercices
"""

import requests
import sys
import json
import time
from datetime import datetime

class Sprint4ChaptersEndpointTester:
    def __init__(self, base_url="https://math-exercise-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error text: {response.text[:200]}")
                    return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_sprint4_chapters_endpoint(self):
        """Test le nouvel endpoint créé dans SPRINT 4 : GET /api/chapters/{chapter_code}/exercise-types"""
        print("\n📚 TESTING SPRINT 4 - NEW CHAPTERS ENDPOINT")
        print("="*60)
        print("CONTEXT: Test du nouvel endpoint GET /api/mathalea/chapters/{chapter_code}/exercise-types")
        
        # Test 1: Test succès avec chapter_code valide
        print("\n🔍 Test 1: Succès avec chapter_code valide (6e_G07)")
        success1, response1 = self.run_test(
            "Chapter 6e_G07 Exercise Types",
            "GET",
            "mathalea/chapters/6e_G07/exercise-types",
            200,
            timeout=30
        )
        
        if success1 and isinstance(response1, dict):
            total = response1.get('total', 0)
            items = response1.get('items', [])
            print(f"   ✅ Response structure correct: total={total}, items count={len(items)}")
            
            if total >= 1:
                print(f"   ✅ Found {total} exercise types for chapter 6e_G07")
                
                # Vérifier que tous les items ont chapter_code == "6e_G07"
                all_correct_chapter = all(item.get('chapter_code') == '6e_G07' for item in items)
                if all_correct_chapter:
                    print(f"   ✅ All items have correct chapter_code: 6e_G07")
                else:
                    print(f"   ❌ Some items have incorrect chapter_code")
                    for item in items:
                        if item.get('chapter_code') != '6e_G07':
                            print(f"     - Item {item.get('id', 'unknown')} has chapter_code: {item.get('chapter_code')}")
                
                # Vérifier présence des champs requis
                required_fields = ['id', 'code_ref', 'titre', 'niveau', 'domaine', 'chapter_code']
                if items:
                    first_item = items[0]
                    missing_fields = [field for field in required_fields if field not in first_item]
                    if not missing_fields:
                        print(f"   ✅ All required fields present: {required_fields}")
                        print(f"   Sample item: {json.dumps(first_item, indent=2, ensure_ascii=False)}")
                    else:
                        print(f"   ❌ Missing fields: {missing_fields}")
                        print(f"   Available fields: {list(first_item.keys())}")
            else:
                print(f"   ⚠️  No exercise types found for chapter 6e_G07 (total={total})")
        else:
            print(f"   ❌ Test 1 failed or invalid response structure")
        
        # Test 2: Test HTTP 404 avec chapter_code inexistant
        print("\n🔍 Test 2: HTTP 404 avec chapter_code inexistant")
        success2, response2 = self.run_test(
            "Invalid Chapter Code",
            "GET", 
            "mathalea/chapters/INVALID_CODE_123/exercise-types",
            404,
            timeout=30
        )
        
        if success2 and isinstance(response2, dict):
            detail = response2.get('detail', '')
            expected_message = "Chapter with code 'INVALID_CODE_123' not found"
            if expected_message in detail:
                print(f"   ✅ Correct 404 error message: {detail}")
            else:
                print(f"   ⚠️  Unexpected error message: {detail}")
                print(f"   Expected: {expected_message}")
        else:
            print(f"   ❌ Test 2 failed - expected 404 response")
        
        # Test 3: Test pagination
        print("\n🔍 Test 3: Test pagination (limit=1&skip=0)")
        success3, response3 = self.run_test(
            "Pagination Test",
            "GET",
            "mathalea/chapters/6e_G07/exercise-types?limit=1&skip=0",
            200,
            timeout=30
        )
        
        if success3 and isinstance(response3, dict):
            total = response3.get('total', 0)
            items = response3.get('items', [])
            if len(items) <= 1:
                print(f"   ✅ Pagination working: returned {len(items)} item(s), total={total}")
                if total > 1 and len(items) == 1:
                    print(f"   ✅ Correct pagination: total > 1 but only 1 item returned")
                elif total == 1 and len(items) == 1:
                    print(f"   ✅ Correct pagination: total = 1 and 1 item returned")
                elif total == 0:
                    print(f"   ℹ️  No items to paginate (total=0)")
            else:
                print(f"   ❌ Pagination failed: returned {len(items)} items with limit=1")
        else:
            print(f"   ❌ Test 3 failed")
        
        # Test 4: Test compatibilité backward
        print("\n🔍 Test 4: Test compatibilité backward")
        # Ancien endpoint
        success4a, response4a = self.run_test(
            "Old Endpoint",
            "GET",
            "mathalea/exercise-types?chapter_code=6e_G07",
            200,
            timeout=30
        )
        
        # Nouveau endpoint
        success4b, response4b = self.run_test(
            "New Endpoint",
            "GET", 
            "mathalea/chapters/6e_G07/exercise-types",
            200,
            timeout=30
        )
        
        if success4a and success4b and isinstance(response4a, dict) and isinstance(response4b, dict):
            old_total = response4a.get('total', 0)
            new_total = response4b.get('total', 0)
            if old_total == new_total:
                print(f"   ✅ Backward compatibility: both endpoints return same total ({old_total})")
            else:
                print(f"   ❌ Backward compatibility issue: old={old_total}, new={new_total}")
                print(f"   Old endpoint response keys: {list(response4a.keys())}")
                print(f"   New endpoint response keys: {list(response4b.keys())}")
        else:
            print(f"   ❌ Test 4 failed - one or both endpoints failed")
            if not success4a:
                print(f"     Old endpoint failed")
            if not success4b:
                print(f"     New endpoint failed")
        
        # Test 5: Test avec chapter_code ayant 0 exercices
        print("\n🔍 Test 5: Test avec chapter_code ayant 0 exercices")
        # Essayer quelques codes qui pourraient ne pas avoir d'exercices
        test_codes = ["6e_G99", "5e_Z99", "EMPTY_CHAPTER", "TEST_EMPTY"]
        found_empty_chapter = False
        
        for test_code in test_codes:
            success5, response5 = self.run_test(
                f"Empty Chapter Test ({test_code})",
                "GET",
                f"mathalea/chapters/{test_code}/exercise-types",
                200,
                timeout=30
            )
            
            if success5 and isinstance(response5, dict):
                total = response5.get('total', -1)
                items = response5.get('items', None)
                if total == 0 and items == []:
                    print(f"   ✅ Found empty chapter {test_code}: total=0, items=[]")
                    found_empty_chapter = True
                    break
                elif total > 0:
                    print(f"   ℹ️  Chapter {test_code} has {total} exercises (not empty)")
                else:
                    print(f"   ⚠️  Chapter {test_code} returned unexpected structure: total={total}, items={items}")
            else:
                print(f"   ℹ️  Chapter {test_code} returned non-200 status (chapter may not exist)")
        
        if not found_empty_chapter:
            print(f"   ⚠️  Could not find a chapter with 0 exercises to test")
            print(f"   Note: This is expected if all test chapter codes have exercises or don't exist")
        
        # Résumé des tests SPRINT 4
        tests_passed = sum([success1, success2, success3, success4a and success4b])
        total_tests = 4
        
        print(f"\n📊 SPRINT 4 ENDPOINT TESTS SUMMARY:")
        print(f"   Tests passed: {tests_passed}/{total_tests}")
        print(f"   Test 1 (Valid chapter): {'✅ PASSED' if success1 else '❌ FAILED'}")
        print(f"   Test 2 (Invalid chapter 404): {'✅ PASSED' if success2 else '❌ FAILED'}")
        print(f"   Test 3 (Pagination): {'✅ PASSED' if success3 else '❌ FAILED'}")
        print(f"   Test 4 (Backward compatibility): {'✅ PASSED' if (success4a and success4b) else '❌ FAILED'}")
        print(f"   Test 5 (Empty chapter): {'✅ TESTED' if found_empty_chapter else '⚠️ NOT FOUND'}")
        
        if tests_passed == total_tests:
            print(f"   🎉 SPRINT 4 ENDPOINT FULLY FUNCTIONAL")
        else:
            print(f"   ⚠️  SPRINT 4 ENDPOINT HAS ISSUES")
        
        return tests_passed == total_tests, {
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "test1_valid_chapter": success1,
            "test2_invalid_404": success2,
            "test3_pagination": success3,
            "test4_backward_compat": success4a and success4b,
            "test5_empty_chapter": found_empty_chapter
        }

if __name__ == "__main__":
    print("🚀 Starting SPRINT 4 Chapters Endpoint Testing...")
    print(f"   Backend URL: https://math-exercise-sync.preview.emergentagent.com")
    print(f"   Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = Sprint4ChaptersEndpointTester()
    success, results = tester.test_sprint4_chapters_endpoint()
    
    print(f"\n📊 Final Summary:")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if success:
        print("🎉 ALL SPRINT 4 TESTS PASSED! New endpoint is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  SOME SPRINT 4 TESTS FAILED. Check the issues above.")
        sys.exit(1)