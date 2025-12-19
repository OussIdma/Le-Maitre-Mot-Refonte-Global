#!/usr/bin/env python3
"""
GM08 Testing Script - Grandeurs et mesures (Longueurs, Périmètres)
================================================================

Tests the new GM08 chapter implementation according to the review request:
1. Batch Endpoint `/api/v1/exercises/generate/batch/gm08`
2. Single Endpoint `/api/v1/exercises/generate` 
3. Content Validation (HTML purity, solution structure, families)
4. Non-regression GM07

API Base URL: https://math-exercise-sync.preview.emergentagent.com/api/v1/exercises
"""

import requests
import sys
import json
import time
import uuid
from datetime import datetime

class GM08Tester:
    def __init__(self, base_url="https://math-exercise-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1/exercises"
        self.tests_run = 0
        self.tests_passed = 0
        self.guest_id = f"test-gm08-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Test results tracking
        self.results = {
            "batch_tests": {"passed": 0, "total": 0, "details": []},
            "single_tests": {"passed": 0, "total": 0, "details": []},
            "content_tests": {"passed": 0, "total": 0, "details": []},
            "regression_tests": {"passed": 0, "total": 0, "details": []}
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=timeout)

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
                    return False, {"error": response.text}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            return False, {"error": "timeout"}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {"error": str(e)}

    def test_gm08_batch_scenarios(self):
        """Test GM08 batch endpoint with various scenarios from review request"""
        print("\n🎯 TESTING GM08 BATCH ENDPOINT")
        print("="*50)
        
        test_scenarios = [
            {
                "name": "Free offer, 3 exercises",
                "data": {
                    "code_officiel": "6e_GM08",
                    "nb_exercices": 3,
                    "offer": "free"
                },
                "expected_count": 3,
                "should_succeed": True
            },
            {
                "name": "Free offer, facile difficulty, 5 exercises (should warn - pool=4)",
                "data": {
                    "code_officiel": "6e_GM08", 
                    "nb_exercices": 5,
                    "offer": "free",
                    "difficulte": "facile"
                },
                "expected_count": 4,  # Only 4 facile exercises in free pool
                "should_succeed": True,
                "should_warn": True
            },
            {
                "name": "Pro offer, 10 exercises (from pool of 20)",
                "data": {
                    "code_officiel": "6e_GM08",
                    "nb_exercices": 10, 
                    "offer": "pro"
                },
                "expected_count": 10,
                "should_succeed": True
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n   Testing: {scenario['name']}")
            
            success, response = self.run_test(
                f"GM08 Batch - {scenario['name']}",
                "POST",
                "generate/batch/gm08",
                200 if scenario['should_succeed'] else 400,
                data=scenario['data'],
                timeout=30
            )
            
            test_result = {
                "scenario": scenario['name'],
                "success": success,
                "data": scenario['data']
            }
            
            if success and isinstance(response, dict):
                exercises = response.get('exercises', [])
                batch_metadata = response.get('batch_metadata', {})
                
                test_result.update({
                    "exercise_count": len(exercises),
                    "batch_metadata": batch_metadata
                })
                
                # Check exercise count
                if len(exercises) == scenario['expected_count']:
                    print(f"   ✅ Correct number of exercises: {len(exercises)}")
                    self.results["batch_tests"]["passed"] += 1
                else:
                    print(f"   ❌ Wrong exercise count: got {len(exercises)}, expected {scenario['expected_count']}")
                
                # Check for warning if expected
                if scenario.get('should_warn'):
                    if 'warning' in batch_metadata:
                        print(f"   ✅ Warning present as expected: {batch_metadata['warning']}")
                    else:
                        print(f"   ⚠️  Warning expected but not found")
                
                # Validate exercise uniqueness (no duplicates)
                exercise_ids = [ex.get('metadata', {}).get('exercise_id') for ex in exercises]
                unique_ids = set(exercise_ids)
                if len(unique_ids) == len(exercise_ids):
                    print(f"   ✅ All exercises are unique (no duplicates)")
                else:
                    print(f"   ❌ Duplicate exercises found: {len(exercise_ids)} total, {len(unique_ids)} unique")
                
                # Check first exercise metadata
                if exercises:
                    first_ex = exercises[0]
                    metadata = first_ex.get('metadata', {})
                    
                    # Verify GM08 metadata
                    if metadata.get('code_officiel') == '6e_GM08':
                        print(f"   ✅ Correct code_officiel in metadata")
                    else:
                        print(f"   ❌ Wrong code_officiel: {metadata.get('code_officiel')}")
                    
                    # Check family
                    family = metadata.get('family')
                    expected_families = ['CONVERSION', 'COMPARAISON', 'PERIMETRE', 'PROBLEME']
                    if family in expected_families:
                        print(f"   ✅ Valid family: {family}")
                    else:
                        print(f"   ❌ Invalid family: {family}")
            else:
                print(f"   ❌ Test failed")
                test_result["error"] = response if isinstance(response, dict) else "Unknown error"
            
            self.results["batch_tests"]["details"].append(test_result)
            self.results["batch_tests"]["total"] += 1
        
        print(f"\n   GM08 Batch Tests: {self.results['batch_tests']['passed']}/{self.results['batch_tests']['total']} passed")

    def test_gm08_single_endpoint(self):
        """Test GM08 single exercise endpoint"""
        print("\n🎯 TESTING GM08 SINGLE ENDPOINT")
        print("="*50)
        
        test_scenarios = [
            {
                "name": "Free offer",
                "data": {
                    "code_officiel": "6e_GM08",
                    "offer": "free"
                },
                "should_succeed": True
            },
            {
                "name": "Pro offer with difficile difficulty",
                "data": {
                    "code_officiel": "6e_GM08",
                    "offer": "pro",
                    "difficulte": "difficile"
                },
                "should_succeed": True
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n   Testing: {scenario['name']}")
            
            success, response = self.run_test(
                f"GM08 Single - {scenario['name']}",
                "POST",
                "generate",
                200 if scenario['should_succeed'] else 400,
                data=scenario['data'],
                timeout=30
            )
            
            test_result = {
                "scenario": scenario['name'],
                "success": success,
                "data": scenario['data']
            }
            
            if success and isinstance(response, dict):
                # Verify required fields
                required_fields = ['id_exercice', 'enonce_html', 'solution_html', 'metadata']
                missing_fields = [field for field in required_fields if field not in response]
                
                if not missing_fields:
                    print(f"   ✅ All required fields present: {required_fields}")
                    self.results["single_tests"]["passed"] += 1
                else:
                    print(f"   ❌ Missing fields: {missing_fields}")
                
                # Check metadata
                metadata = response.get('metadata', {})
                if metadata.get('code_officiel') == '6e_GM08':
                    print(f"   ✅ Correct code_officiel: {metadata.get('code_officiel')}")
                else:
                    print(f"   ❌ Wrong code_officiel: {metadata.get('code_officiel')}")
                
                test_result.update({
                    "has_required_fields": len(missing_fields) == 0,
                    "metadata": metadata
                })
            else:
                print(f"   ❌ Test failed")
                test_result["error"] = response if isinstance(response, dict) else "Unknown error"
            
            self.results["single_tests"]["details"].append(test_result)
            self.results["single_tests"]["total"] += 1
        
        print(f"\n   GM08 Single Tests: {self.results['single_tests']['passed']}/{self.results['single_tests']['total']} passed")

    def test_gm08_content_validation(self):
        """Test GM08 content validation requirements"""
        print("\n🎯 TESTING GM08 CONTENT VALIDATION")
        print("="*50)
        
        # Get a sample of exercises to validate content
        success, response = self.run_test(
            "GM08 Content Sample",
            "POST",
            "generate/batch/gm08",
            200,
            data={
                "code_officiel": "6e_GM08",
                "nb_exercices": 5,
                "offer": "pro"
            },
            timeout=30
        )
        
        content_results = {
            "html_pure": 0,
            "solution_structure": 0,
            "valid_families": 0,
            "total_checked": 0
        }
        
        if success and isinstance(response, dict):
            exercises = response.get('exercises', [])
            content_results['total_checked'] = len(exercises)
            
            for i, exercise in enumerate(exercises):
                print(f"\n   Validating Exercise {i+1}:")
                
                # Check HTML purity (no LaTeX delimiters)
                enonce_html = exercise.get('enonce_html', '')
                solution_html = exercise.get('solution_html', '')
                
                has_latex = '$' in enonce_html or '$' in solution_html
                if not has_latex:
                    print(f"   ✅ Pure HTML (no LaTeX delimiters)")
                    content_results['html_pure'] += 1
                else:
                    print(f"   ❌ LaTeX delimiters found")
                
                # Check solution structure (4 steps with <ol>)
                if '<ol>' in solution_html and '</ol>' in solution_html:
                    print(f"   ✅ Solution has ordered list structure")
                    content_results['solution_structure'] += 1
                else:
                    print(f"   ❌ Solution missing proper <ol> structure")
                
                # Check family
                metadata = exercise.get('metadata', {})
                family = metadata.get('family')
                expected_families = ['CONVERSION', 'COMPARAISON', 'PERIMETRE', 'PROBLEME']
                
                if family in expected_families:
                    print(f"   ✅ Valid family: {family}")
                    content_results['valid_families'] += 1
                else:
                    print(f"   ❌ Invalid family: {family}")
                
                # Show content preview
                print(f"   Content preview: {enonce_html[:100]}...")
        
        # Summary
        total = content_results['total_checked']
        if total > 0:
            html_rate = (content_results['html_pure'] / total) * 100
            structure_rate = (content_results['solution_structure'] / total) * 100
            family_rate = (content_results['valid_families'] / total) * 100
            
            print(f"\n   Content Validation Summary:")
            print(f"   HTML Purity: {content_results['html_pure']}/{total} ({html_rate:.1f}%)")
            print(f"   Solution Structure: {content_results['solution_structure']}/{total} ({structure_rate:.1f}%)")
            print(f"   Valid Families: {content_results['valid_families']}/{total} ({family_rate:.1f}%)")
            
            if html_rate == 100 and structure_rate == 100 and family_rate == 100:
                self.results["content_tests"]["passed"] = 1
                print(f"   ✅ All content validation tests passed")
            else:
                print(f"   ❌ Some content validation tests failed")
        else:
            print(f"   ❌ No exercises to validate")
        
        self.results["content_tests"]["total"] = 1
        self.results["content_tests"]["details"].append({
            "content_results": content_results,
            "success": content_results['html_pure'] == content_results['solution_structure'] == content_results['valid_families'] == total and total > 0
        })

    def test_gm07_non_regression(self):
        """Test that GM07 still works (non-regression)"""
        print("\n🎯 TESTING GM07 NON-REGRESSION")
        print("="*50)
        print("CONTEXT: Ensure GM07 batch endpoint still works after GM08 implementation")
        
        success, response = self.run_test(
            "GM07 Batch Non-Regression",
            "POST",
            "generate/batch/gm07",
            200,
            data={
                "code_officiel": "6e_GM07",
                "nb_exercices": 3,
                "offer": "free"
            },
            timeout=30
        )
        
        test_result = {
            "success": success,
            "gm07_working": False
        }
        
        if success and isinstance(response, dict):
            exercises = response.get('exercises', [])
            batch_metadata = response.get('batch_metadata', {})
            
            if len(exercises) == 3:
                print(f"   ✅ GM07 batch still works: {len(exercises)} exercises generated")
                
                # Check first exercise metadata
                if exercises:
                    metadata = exercises[0].get('metadata', {})
                    if metadata.get('code_officiel') == '6e_GM07':
                        print(f"   ✅ GM07 metadata correct")
                        test_result["gm07_working"] = True
                        self.results["regression_tests"]["passed"] = 1
                    else:
                        print(f"   ❌ GM07 metadata incorrect: {metadata.get('code_officiel')}")
            else:
                print(f"   ❌ GM07 batch failed: got {len(exercises)} exercises, expected 3")
        else:
            print(f"   ❌ GM07 batch endpoint failed")
        
        self.results["regression_tests"]["total"] = 1
        self.results["regression_tests"]["details"].append(test_result)

    def run_all_tests(self):
        """Run all GM08 tests"""
        print("🚀 Starting GM08 Testing Suite...")
        print("="*60)
        print(f"API Base URL: {self.api_url}")
        print(f"Guest ID: {self.guest_id}")
        print("="*60)
        
        # Run all test suites
        self.test_gm08_batch_scenarios()
        self.test_gm08_single_endpoint()
        self.test_gm08_content_validation()
        self.test_gm07_non_regression()
        
        # Display final summary
        print("\n" + "="*60)
        print("📊 GM08 TEST SUMMARY")
        print("="*60)
        
        total_passed = 0
        total_tests = 0
        
        for test_type, results in self.results.items():
            passed = results["passed"]
            total = results["total"]
            total_passed += passed
            total_tests += total
            
            status = "✅" if passed == total else "❌"
            print(f"{status} {test_type.replace('_', ' ').title()}: {passed}/{total}")
        
        print(f"\nOverall: {total_passed}/{total_tests} test suites passed")
        print(f"Individual tests: {self.tests_passed}/{self.tests_run} passed")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if total_passed == total_tests:
            print("\n🎉 ALL GM08 TESTS PASSED!")
            print("✅ GM08 batch endpoint working correctly")
            print("✅ GM08 single endpoint working correctly") 
            print("✅ Content validation requirements met")
            print("✅ GM07 non-regression confirmed")
        else:
            print("\n❌ Some GM08 tests failed. Check the logs above.")
            
            # Show detailed failures
            for test_type, results in self.results.items():
                if results["passed"] < results["total"]:
                    print(f"\n❌ {test_type.replace('_', ' ').title()} failures:")
                    for detail in results["details"]:
                        if not detail.get("success", True):
                            print(f"   - {detail.get('scenario', 'Unknown')}: {detail.get('error', 'Failed')}")
        
        return total_passed == total_tests

def main():
    """Main function to run GM08 tests"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://math-exercise-sync.preview.emergentagent.com"
    
    tester = GM08Tester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()