#!/usr/bin/env python3

import requests
import sys
import json
import time
import uuid
from datetime import datetime

class DynamicFactoryTester:
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

    def test_dynamic_factory_v1_complete(self):
        """Test Dynamic Factory v1 - Complete Implementation"""
        print("\n🏭 TESTING DYNAMIC FACTORY V1 - COMPLETE IMPLEMENTATION")
        print("="*70)
        
        results = {
            "p0_non_regression": {"passed": 0, "total": 3},
            "p1_registry_central": {"passed": 0, "total": 3},
            "p3_params_fusion": {"passed": 0, "total": 1},
            "all_tests": {"passed": 0, "total": 7},
            "critical_failures": []
        }
        
        # P0 - Non-regression tests
        print("\n📋 P0 - NON-REGRESSION TESTS")
        print("-" * 40)
        
        # Test GM07 batch
        print("Testing GM07 batch generation...")
        gm07_success, gm07_response = self.run_test(
            "P0 GM07 Non-regression",
            "POST",
            "v1/exercises/generate/batch/gm07",
            200,
            data={"nb_exercices": 5, "offer": "pro"},
            timeout=60
        )
        
        if gm07_success and isinstance(gm07_response, dict):
            exercises = gm07_response.get('exercises', [])
            if len(exercises) == 5:
                print(f"   ✅ GM07 generated {len(exercises)} exercises")
                results["p0_non_regression"]["passed"] += 1
                
                # Check SVG generation
                svg_count = sum(1 for ex in exercises if ex.get('figure_svg_enonce') or ex.get('figure_svg_solution'))
                if svg_count > 0:
                    print(f"   ✅ SVG generation working ({svg_count} exercises with SVG)")
                    results["p0_non_regression"]["passed"] += 1
                else:
                    print(f"   ❌ No SVG found in GM07 exercises")
            else:
                print(f"   ❌ GM07 expected 5 exercises, got {len(exercises)}")
        else:
            print(f"   ❌ GM07 batch generation failed")
            results["critical_failures"].append("P0 GM07 batch generation failed")
        
        # Test GM08 batch
        print("Testing GM08 batch generation...")
        gm08_success, gm08_response = self.run_test(
            "P0 GM08 Non-regression",
            "POST",
            "v1/exercises/generate/batch/gm08",
            200,
            data={"nb_exercices": 5, "offer": "free"},
            timeout=60
        )
        
        if gm08_success and isinstance(gm08_response, dict):
            exercises = gm08_response.get('exercises', [])
            if len(exercises) == 5:
                print(f"   ✅ GM08 generated {len(exercises)} exercises")
                results["p0_non_regression"]["passed"] += 1
            else:
                print(f"   ❌ GM08 expected 5 exercises, got {len(exercises)}")
        else:
            print(f"   ❌ GM08 batch generation failed")
            results["critical_failures"].append("P0 GM08 batch generation failed")
        
        # P1 - Registry Central
        print("\n📚 P1 - REGISTRY CENTRAL")
        print("-" * 40)
        
        # Test generators list
        print("Testing generators list...")
        list_success, list_response = self.run_test(
            "P1 Generators List",
            "GET",
            "v1/exercises/generators",
            200,
            timeout=30
        )
        
        if list_success and isinstance(list_response, dict):
            generators = list_response.get('generators', [])
            count = list_response.get('count', 0)
            print(f"   ✅ Found {count} generators")
            print(f"   Response structure: {list_response}")
            
            # Handle different response formats
            if generators and isinstance(generators, list):
                if isinstance(generators[0], dict):
                    generator_keys = [g.get('key') for g in generators]
                else:
                    generator_keys = generators  # If it's a list of strings
                print(f"   Generator keys: {generator_keys}")
                results["p1_registry_central"]["passed"] += 1
                
                # Check for expected generators
                expected_keys = ['SYMETRIE_AXIALE_V2', 'THALES_V2']
                found_keys = [k for k in expected_keys if k in generator_keys]
                print(f"   Expected generators found: {found_keys}")
            else:
                print(f"   ❌ Unexpected generators format: {type(generators)}")
        else:
            print(f"   ❌ Generators list failed")
            results["critical_failures"].append("P1 Generators list failed")
        
        # Test SYMETRIE_AXIALE_V2 schema
        print("Testing SYMETRIE_AXIALE_V2 full schema...")
        symetrie_success, symetrie_response = self.run_test(
            "P1 SYMETRIE_AXIALE_V2 Schema",
            "GET",
            "v1/exercises/generators/SYMETRIE_AXIALE_V2/full-schema",
            200,
            timeout=30
        )
        
        if symetrie_success and isinstance(symetrie_response, dict):
            generator_key = symetrie_response.get('generator_key')
            meta = symetrie_response.get('meta', {})
            defaults = symetrie_response.get('defaults', {})
            schema = symetrie_response.get('schema', [])
            presets = symetrie_response.get('presets', [])
            
            print(f"   ✅ Generator key: {generator_key}")
            print(f"   ✅ Schema params: {len(schema)} (expected: 6)")
            print(f"   ✅ Presets: {len(presets)} (expected: 4)")
            
            if len(schema) == 6 and len(presets) == 4:
                results["p1_registry_central"]["passed"] += 1
            else:
                print(f"   ❌ Schema structure incorrect: {len(schema)} params, {len(presets)} presets")
        else:
            print(f"   ❌ SYMETRIE_AXIALE_V2 schema failed")
            results["critical_failures"].append("P1 SYMETRIE_AXIALE_V2 schema failed")
        
        # Test THALES_V2 schema
        print("Testing THALES_V2 full schema...")
        thales_success, thales_response = self.run_test(
            "P1 THALES_V2 Schema",
            "GET",
            "v1/exercises/generators/THALES_V2/full-schema",
            200,
            timeout=30
        )
        
        if thales_success and isinstance(thales_response, dict):
            generator_key = thales_response.get('generator_key')
            schema = thales_response.get('schema', [])
            presets = thales_response.get('presets', [])
            
            print(f"   ✅ THALES_V2 Generator key: {generator_key}")
            print(f"   ✅ THALES_V2 Schema params: {len(schema)}")
            print(f"   ✅ THALES_V2 Presets: {len(presets)}")
            results["p1_registry_central"]["passed"] += 1
        else:
            print(f"   ❌ THALES_V2 schema failed")
        
        # P3 - Params Fusion
        print("\n🔧 P3 - PARAMS FUSION (defaults + exercise_params + overrides)")
        print("-" * 40)
        
        print("Testing params fusion with SYMETRIE_AXIALE_V2...")
        fusion_data = {
            "generator_key": "SYMETRIE_AXIALE_V2",
            "exercise_params": {"figure_type": "triangle"},
            "seed": 42
        }
        
        fusion_success, fusion_response = self.run_test(
            "P3 Params Fusion",
            "POST",
            "v1/exercises/generate-from-factory",
            200,
            data=fusion_data,
            timeout=60
        )
        
        if fusion_success and isinstance(fusion_response, dict):
            success = fusion_response.get('success', False)
            variables = fusion_response.get('variables', {})
            svg_enonce = fusion_response.get('figure_svg_enonce')
            
            if success and variables.get('figure_type') == 'triangle' and svg_enonce:
                print(f"   ✅ Params fusion successful")
                print(f"   ✅ figure_type = {variables.get('figure_type')}")
                print(f"   ✅ SVG generated ({len(svg_enonce)} chars)")
                results["p3_params_fusion"]["passed"] += 1
            else:
                print(f"   ❌ Params fusion failed: success={success}, figure_type={variables.get('figure_type')}, svg={bool(svg_enonce)}")
        else:
            print(f"   ❌ Params fusion request failed")
            results["critical_failures"].append("P3 Params fusion failed")
        
        # Calculate totals
        results["all_tests"]["passed"] = sum(cat["passed"] for cat in results.values() if "passed" in cat)
        
        # Summary
        print(f"\n📊 DYNAMIC FACTORY V1 TEST SUMMARY:")
        print(f"   P0 Non-regression: {results['p0_non_regression']['passed']}/{results['p0_non_regression']['total']}")
        print(f"   P1 Registry Central: {results['p1_registry_central']['passed']}/{results['p1_registry_central']['total']}")
        print(f"   P3 Params Fusion: {results['p3_params_fusion']['passed']}/{results['p3_params_fusion']['total']}")
        print(f"   OVERALL: {results['all_tests']['passed']}/{results['all_tests']['total']}")
        
        if results['critical_failures']:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in results['critical_failures']:
                print(f"   - {failure}")
        
        # Success criteria: All P0 + P1 + P3 must pass
        p0_success = results['p0_non_regression']['passed'] == results['p0_non_regression']['total']
        p1_success = results['p1_registry_central']['passed'] == results['p1_registry_central']['total']
        p3_success = results['p3_params_fusion']['passed'] == results['p3_params_fusion']['total']
        
        overall_success = p0_success and p1_success and p3_success
        
        if overall_success:
            print(f"\n   🎉 DYNAMIC FACTORY V1 IMPLEMENTATION SUCCESSFUL")
        else:
            print(f"\n   ❌ DYNAMIC FACTORY V1 IMPLEMENTATION HAS ISSUES")
        
        return overall_success, results

def main():
    tester = DynamicFactoryTester()
    success, results = tester.test_dynamic_factory_v1_complete()
    
    print(f"\n🏁 Testing completed!")
    print(f"Final result: {'PASSED' if success else 'FAILED'}")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)