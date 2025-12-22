#!/usr/bin/env python3
"""
P0/P1/P2 Admin Dynamic Exercise UX Improvements Tests
====================================================

Tests for the new admin UX improvements for dynamic exercises:
1. P0.2: Generator schema endpoint and variables display in admin UI
2. P1: SVG AUTO mode for dynamic exercises  
3. P2: Dynamic preview endpoint and modal
4. Non-regression: GM07, GM08, TESTS_DYN batch generation

Backend URL is in /app/frontend/.env as REACT_APP_BACKEND_URL.
"""

import requests
import sys
import json
import time
import uuid
from datetime import datetime

class P0P1P2DynamicExercisesTester:
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
        if headers:
            print(f"   Headers: {list(headers.keys())}")
        
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

    def test_p0_generator_schema_endpoint(self):
        """Test P0.2 - Generator Schema Endpoint"""
        print("\n🔧 TESTING P0.2 - Generator Schema Endpoint")
        print("="*60)
        
        # Test GET /api/v1/exercises/generators/THALES_V1/schema
        success, response = self.run_test(
            "P0.2 Generator Schema THALES_V1",
            "GET",
            "v1/exercises/generators/THALES_V1/schema",
            200,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            # Verify required fields
            required_fields = ['generator_key', 'label', 'variables', 'svg_modes', 'template_example_enonce', 'template_example_solution']
            missing_fields = []
            
            for field in required_fields:
                if field not in response:
                    missing_fields.append(field)
                else:
                    print(f"   ✅ Found required field: {field}")
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False, {"missing_fields": missing_fields}
            
            # Check variables count (should be 22 according to spec)
            variables = response.get('variables', [])
            print(f"   📊 Variables count: {len(variables)}")
            if len(variables) >= 20:  # Allow some flexibility
                print(f"   ✅ Variables count looks good ({len(variables)})")
            else:
                print(f"   ⚠️  Expected around 22 variables, got {len(variables)}")
            
            # Check SVG modes
            svg_modes = response.get('svg_modes', [])
            print(f"   🎨 SVG modes: {svg_modes}")
            
            # Check template examples
            template_enonce = response.get('template_example_enonce', '')
            template_solution = response.get('template_example_solution', '')
            
            if template_enonce and template_solution:
                print(f"   ✅ Template examples provided")
                print(f"   Enonce preview: {template_enonce[:100]}...")
                print(f"   Solution preview: {template_solution[:100]}...")
            else:
                print(f"   ❌ Missing template examples")
                return False, {"error": "missing_templates"}
            
            return True, response
        else:
            print(f"   ❌ Generator schema endpoint failed")
            return False, response

    def test_p2_dynamic_preview_endpoint(self):
        """Test P2 - Dynamic Preview Endpoint"""
        print("\n🔍 TESTING P2 - Dynamic Preview Endpoint")
        print("="*60)
        
        # Test POST /api/admin/exercises/preview-dynamic
        preview_data = {
            "generator_key": "THALES_V1",
            "enonce_template_html": "<p>Test {{coefficient}}</p>",
            "solution_template_html": "<p>Réponse</p>",
            "difficulty": "moyen",
            "seed": 42,
            "svg_mode": "AUTO"
        }
        
        success, response = self.run_test(
            "P2 Dynamic Preview",
            "POST",
            "admin/exercises/preview-dynamic",
            200,
            data=preview_data,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            # Verify required response fields
            required_fields = ['success', 'enonce_html', 'variables_used']
            missing_fields = []
            
            for field in required_fields:
                if field not in response:
                    missing_fields.append(field)
                else:
                    print(f"   ✅ Found required field: {field}")
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False, {"missing_fields": missing_fields}
            
            # Check if success is true
            success_flag = response.get('success', False)
            print(f"   🎯 Preview success: {success_flag}")
            
            # Check if variable was replaced
            enonce_html = response.get('enonce_html', '')
            if '{{coefficient}}' not in enonce_html and 'coefficient' in str(response.get('variables_used', {})):
                print(f"   ✅ Variable replacement working")
                print(f"   Rendered enonce: {enonce_html}")
            else:
                print(f"   ❌ Variable replacement may not be working")
                print(f"   Enonce: {enonce_html}")
            
            # Check for SVG if AUTO mode
            svg_enonce = response.get('svg_enonce')
            if svg_enonce:
                print(f"   ✅ SVG enonce generated (length: {len(svg_enonce)})")
            else:
                print(f"   ℹ️  No SVG enonce (may be normal)")
            
            variables_used = response.get('variables_used', {})
            print(f"   📊 Variables used: {len(variables_used)} variables")
            
            return True, response
        else:
            print(f"   ❌ Dynamic preview endpoint failed")
            return False, response

    def test_p0_generators_list_endpoint(self):
        """Test P0.2 - Generators List Endpoint"""
        print("\n📋 TESTING P0.2 - Generators List Endpoint")
        print("="*60)
        
        # Test GET /api/v1/exercises/generators/list
        success, response = self.run_test(
            "P0.2 Generators List",
            "GET",
            "v1/exercises/generators/list",
            200,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            # Verify required fields
            if 'generators' not in response or 'count' not in response:
                print(f"   ❌ Missing required fields (generators, count)")
                return False, {"error": "missing_fields"}
            
            generators = response.get('generators', [])
            count = response.get('count', 0)
            
            print(f"   📊 Generators count: {count}")
            print(f"   📋 Generators array length: {len(generators)}")
            
            if count != len(generators):
                print(f"   ⚠️  Count mismatch: count={count}, array_length={len(generators)}")
            else:
                print(f"   ✅ Count matches array length")
            
            # Check if THALES_V1 is in the list
            thales_found = False
            for gen in generators:
                if isinstance(gen, dict) and gen.get('generator_key') == 'THALES_V1':
                    thales_found = True
                    print(f"   ✅ THALES_V1 generator found in list")
                    print(f"   Label: {gen.get('label', 'N/A')}")
                    break
            
            if not thales_found:
                print(f"   ❌ THALES_V1 generator not found in list")
                return False, {"error": "thales_not_found"}
            
            return True, response
        else:
            print(f"   ❌ Generators list endpoint failed")
            return False, response

    def test_gm07_batch_non_regression(self):
        """Test GM07 Batch Non-regression"""
        print("\n🔄 TESTING GM07 Batch Non-regression")
        print("="*60)
        
        # Test POST /api/v1/exercises/generate/batch/gm07
        batch_data = {
            "nb_exercices": 5,
            "offer": "pro"
        }
        
        success, response = self.run_test(
            "GM07 Batch Non-regression",
            "POST",
            "v1/exercises/generate/batch/gm07",
            200,
            data=batch_data,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            exercises = response.get('exercises', [])
            batch_metadata = response.get('batch_metadata', {})
            
            print(f"   📊 Exercises generated: {len(exercises)}")
            print(f"   🎯 Requested: {batch_data['nb_exercices']}")
            
            if len(exercises) == batch_data['nb_exercices']:
                print(f"   ✅ Correct number of exercises returned")
            else:
                print(f"   ⚠️  Expected {batch_data['nb_exercices']}, got {len(exercises)}")
                warning = batch_metadata.get('warning', '')
                if warning:
                    print(f"   ℹ️  Warning: {warning}")
            
            # Check exercise structure (GM07 uses different field names)
            if exercises:
                first_ex = exercises[0]
                # Check for either format
                has_id = 'id' in first_ex or 'id_exercice' in first_ex
                has_enonce = 'enonce' in first_ex or 'enonce_html' in first_ex
                has_solution = 'solution' in first_ex or 'solution_html' in first_ex
                
                if has_id:
                    print(f"   ✅ Exercise has ID field")
                else:
                    print(f"   ❌ Exercise missing ID field")
                    
                if has_enonce:
                    print(f"   ✅ Exercise has enonce field")
                else:
                    print(f"   ❌ Exercise missing enonce field")
                    
                if has_solution:
                    print(f"   ✅ Exercise has solution field")
                else:
                    print(f"   ❌ Exercise missing solution field")
            
            return True, response
        else:
            print(f"   ❌ GM07 batch generation failed")
            return False, response

    def test_gm08_batch_non_regression(self):
        """Test GM08 Batch Non-regression"""
        print("\n🔄 TESTING GM08 Batch Non-regression")
        print("="*60)
        
        # Test POST /api/v1/exercises/generate/batch/gm08
        batch_data = {
            "nb_exercices": 5,
            "offer": "free"
        }
        
        success, response = self.run_test(
            "GM08 Batch Non-regression",
            "POST",
            "v1/exercises/generate/batch/gm08",
            200,
            data=batch_data,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            exercises = response.get('exercises', [])
            batch_metadata = response.get('batch_metadata', {})
            
            print(f"   📊 Exercises generated: {len(exercises)}")
            print(f"   🎯 Requested: {batch_data['nb_exercices']}")
            
            if len(exercises) == batch_data['nb_exercices']:
                print(f"   ✅ Correct number of exercises returned")
            else:
                print(f"   ⚠️  Expected {batch_data['nb_exercices']}, got {len(exercises)}")
                warning = batch_metadata.get('warning', '')
                if warning:
                    print(f"   ℹ️  Warning: {warning}")
            
            # Check exercise structure (GM08 uses different field names)
            if exercises:
                first_ex = exercises[0]
                # Check for either format
                has_id = 'id' in first_ex or 'id_exercice' in first_ex
                has_enonce = 'enonce' in first_ex or 'enonce_html' in first_ex
                has_solution = 'solution' in first_ex or 'solution_html' in first_ex
                
                if has_id:
                    print(f"   ✅ Exercise has ID field")
                else:
                    print(f"   ❌ Exercise missing ID field")
                    
                if has_enonce:
                    print(f"   ✅ Exercise has enonce field")
                else:
                    print(f"   ❌ Exercise missing enonce field")
                    
                if has_solution:
                    print(f"   ✅ Exercise has solution field")
                else:
                    print(f"   ❌ Exercise missing solution field")
            
            return True, response
        else:
            print(f"   ❌ GM08 batch generation failed")
            return False, response

    def test_tests_dyn_batch_dynamic_exercises(self):
        """Test TESTS_DYN Batch Dynamic Exercises"""
        print("\n🎲 TESTING TESTS_DYN Batch Dynamic Exercises")
        print("="*60)
        
        # Test POST /api/v1/exercises/generate/batch/tests_dyn
        batch_data = {
            "nb_exercices": 3,
            "offer": "free"
        }
        
        success, response = self.run_test(
            "TESTS_DYN Batch Dynamic",
            "POST",
            "v1/exercises/generate/batch/tests_dyn",
            200,
            data=batch_data,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            exercises = response.get('exercises', [])
            batch_metadata = response.get('batch_metadata', {})
            
            print(f"   📊 Exercises generated: {len(exercises)}")
            print(f"   🎯 Requested: {batch_data['nb_exercices']}")
            
            if len(exercises) == batch_data['nb_exercices']:
                print(f"   ✅ Correct number of exercises returned")
            else:
                print(f"   ⚠️  Expected {batch_data['nb_exercices']}, got {len(exercises)}")
                warning = batch_metadata.get('warning', '')
                if warning:
                    print(f"   ℹ️  Warning: {warning}")
            
            # Check for dynamic exercise properties
            dynamic_exercises_found = 0
            thales_exercises_found = 0
            
            for i, exercise in enumerate(exercises):
                # Check if exercise is marked as dynamic (in metadata)
                metadata = exercise.get('metadata', {})
                is_dynamic = metadata.get('is_dynamic', False)
                generator_key = metadata.get('generator_key', '')
                
                if is_dynamic:
                    dynamic_exercises_found += 1
                    print(f"   ✅ Exercise {i+1} is marked as dynamic")
                
                if generator_key == 'THALES_V1':
                    thales_exercises_found += 1
                    print(f"   ✅ Exercise {i+1} uses THALES_V1 generator")
                
                # Check for required fields (different field names for dynamic exercises)
                required_fields = ['id_exercice', 'enonce_html', 'solution_html']
                for field in required_fields:
                    if field in exercise:
                        print(f"   ✅ Exercise {i+1} has {field}")
                    else:
                        print(f"   ❌ Exercise {i+1} missing {field}")
            
            print(f"   🎲 Dynamic exercises: {dynamic_exercises_found}/{len(exercises)}")
            print(f"   🔧 THALES_V1 exercises: {thales_exercises_found}/{len(exercises)}")
            
            # Verify all exercises are dynamic and use THALES_V1
            if dynamic_exercises_found == len(exercises) and thales_exercises_found == len(exercises):
                print(f"   ✅ All exercises are dynamic with THALES_V1 generator")
                return True, response
            else:
                print(f"   ⚠️  Not all exercises are properly dynamic")
                return False, response
        else:
            print(f"   ❌ TESTS_DYN batch generation failed")
            return False, response

    def run_all_tests(self):
        """Run all P0/P1/P2 Admin Dynamic Exercise UX Improvement tests"""
        print("\n🚀 TESTING P0/P1/P2 ADMIN DYNAMIC EXERCISE UX IMPROVEMENTS")
        print("="*80)
        
        test_results = {}
        
        # P0.2 Tests
        print("\n📋 P0.2 TESTS")
        test_results['p0_generator_schema'] = self.test_p0_generator_schema_endpoint()
        test_results['p0_generators_list'] = self.test_p0_generators_list_endpoint()
        
        # P2 Tests  
        print("\n🔍 P2 TESTS")
        test_results['p2_dynamic_preview'] = self.test_p2_dynamic_preview_endpoint()
        
        # Non-regression Tests
        print("\n🔄 NON-REGRESSION TESTS")
        test_results['gm07_batch'] = self.test_gm07_batch_non_regression()
        test_results['gm08_batch'] = self.test_gm08_batch_non_regression()
        test_results['tests_dyn_batch'] = self.test_tests_dyn_batch_dynamic_exercises()
        
        # Summary
        passed_tests = sum(1 for success, _ in test_results.values() if success)
        total_tests = len(test_results)
        
        print(f"\n📊 P0/P1/P2 ADMIN DYNAMIC UX IMPROVEMENTS SUMMARY:")
        print(f"   Overall: {passed_tests}/{total_tests} tests passed")
        
        for test_name, (success, _) in test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        return passed_tests == total_tests, test_results


if __name__ == "__main__":
    print("🚀 Starting P0/P1/P2 Admin Dynamic Exercise UX Improvements Tests")
    print("="*80)
    
    tester = P0P1P2DynamicExercisesTester()
    
    try:
        success, results = tester.run_all_tests()
        
        print(f"\n🏁 FINAL RESULTS:")
        print(f"   Tests run: {tester.tests_run}")
        print(f"   Tests passed: {tester.tests_passed}")
        print(f"   Success rate: {tester.tests_passed/tester.tests_run*100:.1f}%")
        
        if success:
            print("\n🎉 ALL P0/P1/P2 ADMIN DYNAMIC UX IMPROVEMENT TESTS PASSED!")
        else:
            print("\n⚠️  SOME P0/P1/P2 TESTS FAILED - See details above")
            
            # Show failed tests
            failed_tests = [name for name, (test_success, _) in results.items() if not test_success]
            if failed_tests:
                print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Testing completed!")