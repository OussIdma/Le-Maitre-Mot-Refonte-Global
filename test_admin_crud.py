#!/usr/bin/env python3
"""
Simple test script for Admin Page V2 CRUD APIs
"""

import requests
import json
import sys

def test_admin_crud_apis():
    """Test Admin Page V2 CRUD APIs for curriculum management"""
    base_url = "https://math-exercise-sync.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔧 TESTING ADMIN PAGE V2 CRUD APIs")
    print("="*60)
    print("CONTEXT: Testing /api/admin/curriculum/* endpoints for V2 CRUD functionality")
    
    # Test data for CRUD operations
    test_chapter_code = "6e_TEST_CRUD"
    test_chapter_data = {
        "code_officiel": test_chapter_code,
        "libelle": "Test CRUD Chapitre",
        "domaine": "Nombres et calculs",
        "chapitre_backend": "Test Backend",
        "exercise_types": ["CALCUL_FRACTIONS", "CALCUL_DECIMAUX"],
        "schema_requis": True,
        "difficulte_min": 1,
        "difficulte_max": 3,
        "statut": "beta"
    }
    
    results = {
        "options_test": False,
        "create_test": False,
        "read_test": False,
        "update_test": False,
        "delete_test": False,
        "error_handling": False,
        "count_verification": False
    }
    
    def run_test(name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
    
    # 1. Test GET /api/admin/curriculum/options
    print("\n1️⃣ Testing GET /api/admin/curriculum/options")
    success, response = run_test(
        "Admin Curriculum Options",
        "GET",
        "admin/curriculum/options",
        200,
        timeout=30
    )
    
    if success and isinstance(response, dict):
        generators = response.get('generators', [])
        domaines = response.get('domaines', [])
        statuts = response.get('statuts', [])
        
        print(f"   ✅ Found {len(generators)} generators")
        print(f"   ✅ Found {len(domaines)} domaines")
        print(f"   ✅ Found {len(statuts)} statuts")
        
        # Verify expected structure
        if generators and domaines and statuts:
            results["options_test"] = True
            print("   ✅ Options endpoint working correctly")
        else:
            print("   ❌ Missing required options data")
    else:
        print("   ❌ Options endpoint failed")
    
    # 2. Get initial count for verification later
    print("\n2️⃣ Getting initial curriculum count")
    success, response = run_test(
        "Initial Curriculum Count",
        "GET", 
        "admin/curriculum/6e",
        200,
        timeout=30
    )
    
    initial_count = 0
    if success and isinstance(response, dict):
        initial_count = response.get('total_chapitres', 0)
        print(f"   ✅ Initial count: {initial_count} chapitres")
    
    # 3. Test POST /api/admin/curriculum/6e/chapters (Create)
    print(f"\n3️⃣ Testing POST /api/admin/curriculum/6e/chapters (Create)")
    print(f"   Creating chapter: {test_chapter_code}")
    
    success, response = run_test(
        "Create Chapter",
        "POST",
        "admin/curriculum/6e/chapters",
        200,
        data=test_chapter_data,
        timeout=30
    )
    
    if success and isinstance(response, dict):
        if response.get('success') and response.get('chapter'):
            results["create_test"] = True
            chapter = response['chapter']
            print(f"   ✅ Chapter created successfully")
            print(f"   ✅ Code: {chapter.get('code_officiel')}")
            print(f"   ✅ Libelle: {chapter.get('libelle')}")
            print(f"   ✅ Statut: {chapter.get('statut')}")
        else:
            print(f"   ❌ Create failed: {response}")
    else:
        print("   ❌ Create chapter failed")
    
    # 4. Test GET /api/admin/curriculum/6e/{code_officiel} (Read)
    print(f"\n4️⃣ Testing GET /api/admin/curriculum/6e/{test_chapter_code} (Read)")
    
    success, response = run_test(
        "Read Chapter",
        "GET",
        f"admin/curriculum/6e/{test_chapter_code}",
        200,
        timeout=30
    )
    
    if success and isinstance(response, dict):
        # Verify all fields are correctly saved
        if (response.get('code_officiel') == test_chapter_code and
            response.get('libelle') == test_chapter_data['libelle'] and
            response.get('domaine') == test_chapter_data['domaine']):
            results["read_test"] = True
            print("   ✅ Chapter read successfully with correct data")
            print(f"   ✅ Verified: code_officiel, libelle, domaine")
        else:
            print(f"   ❌ Data mismatch in read: {response}")
    else:
        print("   ❌ Read chapter failed")
    
    # 5. Test PUT /api/admin/curriculum/6e/chapters/{code_officiel} (Update)
    print(f"\n5️⃣ Testing PUT /api/admin/curriculum/6e/chapters/{test_chapter_code} (Update)")
    
    update_data = {
        "libelle": "Test CRUD Chapitre Modifié",
        "statut": "prod",
        "difficulte_max": 2
    }
    
    success, response = run_test(
        "Update Chapter",
        "PUT",
        f"admin/curriculum/6e/chapters/{test_chapter_code}",
        200,
        data=update_data,
        timeout=30
    )
    
    if success and isinstance(response, dict):
        if response.get('success') and response.get('chapter'):
            chapter = response['chapter']
            # Verify changes are persisted
            if (chapter.get('libelle') == update_data['libelle'] and
                chapter.get('statut') == update_data['statut'] and
                chapter.get('difficulte_max') == update_data['difficulte_max']):
                results["update_test"] = True
                print("   ✅ Chapter updated successfully")
                print(f"   ✅ New libelle: {chapter.get('libelle')}")
                print(f"   ✅ New statut: {chapter.get('statut')}")
                print(f"   ✅ New difficulte_max: {chapter.get('difficulte_max')}")
            else:
                print(f"   ❌ Update data not persisted correctly")
        else:
            print(f"   ❌ Update failed: {response}")
    else:
        print("   ❌ Update chapter failed")
    
    # 6. Test Error Handling
    print(f"\n6️⃣ Testing Error Handling")
    
    error_tests_passed = 0
    total_error_tests = 3
    
    # Test duplicate code_officiel (should return 400)
    print("   Testing duplicate code_officiel...")
    success, response = run_test(
        "Duplicate Create",
        "POST",
        "admin/curriculum/6e/chapters",
        400,
        data=test_chapter_data,  # Same data as before
        timeout=30
    )
    if success:
        error_tests_passed += 1
        print("   ✅ Duplicate code_officiel correctly rejected (400)")
    
    # Test PUT on non-existent chapter (should return 404)
    print("   Testing update non-existent chapter...")
    success, response = run_test(
        "Update Non-existent",
        "PUT",
        "admin/curriculum/6e/chapters/NONEXISTENT_CODE",
        404,
        data={"libelle": "Test"},
        timeout=30
    )
    if success:
        error_tests_passed += 1
        print("   ✅ Update non-existent chapter correctly returns 404")
    
    # Test DELETE on non-existent chapter (should return 404)
    print("   Testing delete non-existent chapter...")
    success, response = run_test(
        "Delete Non-existent",
        "DELETE",
        "admin/curriculum/6e/chapters/NONEXISTENT_CODE",
        404,
        timeout=30
    )
    if success:
        error_tests_passed += 1
        print("   ✅ Delete non-existent chapter correctly returns 404")
    
    if error_tests_passed == total_error_tests:
        results["error_handling"] = True
        print(f"   ✅ All error handling tests passed ({error_tests_passed}/{total_error_tests})")
    else:
        print(f"   ⚠️  Error handling tests: {error_tests_passed}/{total_error_tests} passed")
    
    # 7. Test DELETE /api/admin/curriculum/6e/chapters/{code_officiel} (Delete)
    print(f"\n7️⃣ Testing DELETE /api/admin/curriculum/6e/chapters/{test_chapter_code} (Delete)")
    
    success, response = run_test(
        "Delete Chapter",
        "DELETE",
        f"admin/curriculum/6e/chapters/{test_chapter_code}",
        200,
        timeout=30
    )
    
    if success and isinstance(response, dict):
        if response.get('success'):
            results["delete_test"] = True
            print("   ✅ Chapter deleted successfully")
            
            # Verify it no longer exists (GET should return 404)
            print("   Verifying deletion...")
            success, response = run_test(
                "Verify Deletion",
                "GET",
                f"admin/curriculum/6e/{test_chapter_code}",
                404,
                timeout=30
            )
            if success:
                print("   ✅ Verified: Chapter no longer exists (404)")
            else:
                print("   ❌ Chapter still exists after deletion")
        else:
            print(f"   ❌ Delete failed: {response}")
    else:
        print("   ❌ Delete chapter failed")
    
    # 8. Verify total count returns to original
    print(f"\n8️⃣ Verifying total count returns to original")
    
    success, response = run_test(
        "Final Count Verification",
        "GET",
        "admin/curriculum/6e",
        200,
        timeout=30
    )
    
    if success and isinstance(response, dict):
        final_count = response.get('total_chapitres', 0)
        if final_count == initial_count:
            results["count_verification"] = True
            print(f"   ✅ Count returned to original: {final_count} chapitres")
        else:
            print(f"   ❌ Count mismatch: initial={initial_count}, final={final_count}")
    
    # Summary
    print(f"\n📊 ADMIN CRUD API TEST SUMMARY:")
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("   🎉 ALL ADMIN CRUD API TESTS PASSED")
        print("   ✅ Admin Page V2 CRUD functionality is fully operational")
        return True
    else:
        print(f"   ⚠️  {total_tests - passed_tests} tests failed")
        print("   ❌ Admin Page V2 CRUD functionality has issues")
        return False

if __name__ == "__main__":
    success = test_admin_crud_apis()
    sys.exit(0 if success else 1)