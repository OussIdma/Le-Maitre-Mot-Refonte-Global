#!/usr/bin/env python3
"""
Comprehensive Testing of 6e Generators (Waves 1, 2 & 3) - FINAL VERSION
Test comprehensive coverage of the new 6e generators as requested.
"""

import requests
import json
import time
import uuid
from datetime import datetime
from collections import Counter
import os

class SixeGeneratorsTester:
    def __init__(self):
        # Use REACT_APP_BACKEND_URL from frontend/.env
        self.base_url = "https://math-exercise-sync.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.guest_id = f"test-6e-generators-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Test results tracking
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        
        # Generator tracking
        self.generator_stats = {}
        
    def log_test_result(self, test_name, success, details=None):
        """Log test result with details"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            status = "✅ PASSED"
        else:
            self.test_results["failed_tests"] += 1
            status = "❌ FAILED"
            
        result = {
            "test_name": test_name,
            "status": status,
            "success": success,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["test_details"].append(result)
        print(f"{status} - {test_name}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def make_api_call(self, data, timeout=30):
        """Make API call to generate exercises"""
        url = f"{self.api_url}/v1/exercises/generate"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
            return response.status_code, response.json() if response.status_code == 200 else response.text
        except requests.exceptions.Timeout:
            return 408, "Request timeout"
        except Exception as e:
            return 500, str(e)
    
    def test_perimetres_aires_4_types(self):
        """Test 1: Périmètres et aires (4 types) - 20 runs"""
        print("\n🔍 TEST 1: Périmètres et aires (4 types) - 20 runs")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Périmètres et aires", 
            "difficulte": "moyen"
        }
        
        generator_counts = Counter()
        fallback_count = 0
        successful_calls = 0
        
        for i in range(20):
            print(f"Run {i+1}/20...", end=" ")
            status_code, response = self.make_api_call(test_data)
            
            if status_code == 200 and isinstance(response, dict):
                metadata = response.get('metadata', {})
                generator_code = metadata.get('generator_code', 'UNKNOWN')
                is_fallback = metadata.get('is_fallback', True)
                
                generator_counts[generator_code] += 1
                if is_fallback:
                    fallback_count += 1
                successful_calls += 1
                print(f"✅ {generator_code} (fallback: {is_fallback})")
            else:
                print(f"❌ Error: {response}")
        
        # Verify expected generator types (with 6e_ prefix)
        expected_generators = ['6e_PERIMETRE_AIRE', '6e_RECTANGLE', '6e_AIRE_TRIANGLE', '6e_AIRE_FIGURES_COMPOSEES']
        found_generators = list(generator_counts.keys())
        
        # Check if we have a mix of the expected types
        expected_found = [gen for gen in expected_generators if gen in found_generators]
        has_mix = len(expected_found) >= 3  # At least 3 different types for good coverage
        all_non_fallback = fallback_count == 0
        
        details = {
            "successful_calls": successful_calls,
            "generator_counts": dict(generator_counts),
            "fallback_count": fallback_count,
            "expected_generators": expected_generators,
            "found_generators": found_generators,
            "expected_found": expected_found,
            "has_mix": has_mix,
            "all_non_fallback": all_non_fallback
        }
        
        # Success criteria: good coverage and mix of generators
        success = successful_calls >= 15 and len(expected_found) >= 3
        self.log_test_result("Périmètres et aires (4 types)", success, details)
        return success
    
    def test_angles_3_types(self):
        """Test 2: Angles (3 types) - 15 runs"""
        print("\n🔍 TEST 2: Angles (3 types) - 15 runs")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Angles",
            "difficulte": "moyen"
        }
        
        generator_counts = Counter()
        fallback_count = 0
        successful_calls = 0
        
        for i in range(15):
            print(f"Run {i+1}/15...", end=" ")
            status_code, response = self.make_api_call(test_data)
            
            if status_code == 200 and isinstance(response, dict):
                metadata = response.get('metadata', {})
                generator_code = metadata.get('generator_code', 'UNKNOWN')
                is_fallback = metadata.get('is_fallback', True)
                
                generator_counts[generator_code] += 1
                if is_fallback:
                    fallback_count += 1
                successful_calls += 1
                print(f"✅ {generator_code} (fallback: {is_fallback})")
            else:
                print(f"❌ Error: {response}")
        
        # Verify expected generator types (with 6e_ prefix)
        expected_generators = ['6e_ANGLE_MESURE', '6e_ANGLE_VOCABULAIRE', '6e_ANGLE_PROPRIETES']
        found_generators = list(generator_counts.keys())
        expected_found = [gen for gen in expected_generators if gen in found_generators]
        has_all_three = len(expected_found) == 3
        
        details = {
            "successful_calls": successful_calls,
            "generator_counts": dict(generator_counts),
            "fallback_count": fallback_count,
            "expected_generators": expected_generators,
            "found_generators": found_generators,
            "expected_found": expected_found,
            "has_all_three": has_all_three
        }
        
        success = successful_calls >= 12 and has_all_three
        self.log_test_result("Angles (3 types)", success, details)
        return success
    
    def test_fractions_2_types(self):
        """Test 3: Fractions (2 types) - 10 runs"""
        print("\n🔍 TEST 3: Fractions (2 types) - 10 runs")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Fractions",
            "difficulte": "moyen"
        }
        
        generator_counts = Counter()
        fallback_count = 0
        successful_calls = 0
        
        for i in range(10):
            print(f"Run {i+1}/10...", end=" ")
            status_code, response = self.make_api_call(test_data)
            
            if status_code == 200 and isinstance(response, dict):
                metadata = response.get('metadata', {})
                generator_code = metadata.get('generator_code', 'UNKNOWN')
                is_fallback = metadata.get('is_fallback', True)
                
                generator_counts[generator_code] += 1
                if is_fallback:
                    fallback_count += 1
                successful_calls += 1
                print(f"✅ {generator_code} (fallback: {is_fallback})")
            else:
                print(f"❌ Error: {response}")
        
        # Verify expected generator types (with 6e_ prefix)
        expected_generators = ['6e_CALCUL_FRACTIONS', '6e_FRACTION_REPRESENTATION']
        found_generators = list(generator_counts.keys())
        expected_found = [gen for gen in expected_generators if gen in found_generators]
        has_both = len(expected_found) == 2
        
        details = {
            "successful_calls": successful_calls,
            "generator_counts": dict(generator_counts),
            "fallback_count": fallback_count,
            "expected_generators": expected_generators,
            "found_generators": found_generators,
            "expected_found": expected_found,
            "has_both": has_both
        }
        
        success = successful_calls >= 8 and has_both
        self.log_test_result("Fractions (2 types)", success, details)
        return success
    
    def test_proportionnalite_3_types(self):
        """Test 4: Proportionnalité (3 types) - 15 runs"""
        print("\n🔍 TEST 4: Proportionnalité (3 types) - 15 runs")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Proportionnalité",
            "difficulte": "moyen"
        }
        
        generator_counts = Counter()
        fallback_count = 0
        successful_calls = 0
        
        for i in range(15):
            print(f"Run {i+1}/15...", end=" ")
            status_code, response = self.make_api_call(test_data)
            
            if status_code == 200 and isinstance(response, dict):
                metadata = response.get('metadata', {})
                generator_code = metadata.get('generator_code', 'UNKNOWN')
                is_fallback = metadata.get('is_fallback', True)
                
                generator_counts[generator_code] += 1
                if is_fallback:
                    fallback_count += 1
                successful_calls += 1
                print(f"✅ {generator_code} (fallback: {is_fallback})")
            else:
                print(f"❌ Error: {response}")
        
        # Verify expected generator types (with 6e_ prefix)
        expected_generators = ['6e_PROPORTIONNALITE', '6e_PROP_TABLEAU', '6e_PROP_ACHAT']
        found_generators = list(generator_counts.keys())
        expected_found = [gen for gen in expected_generators if gen in found_generators]
        has_all_three = len(expected_found) == 3
        
        details = {
            "successful_calls": successful_calls,
            "generator_counts": dict(generator_counts),
            "fallback_count": fallback_count,
            "expected_generators": expected_generators,
            "found_generators": found_generators,
            "expected_found": expected_found,
            "has_all_three": has_all_three
        }
        
        success = successful_calls >= 12 and has_all_three
        self.log_test_result("Proportionnalité (3 types)", success, details)
        return success
    
    def test_nombres_entiers_3_types(self):
        """Test 5: Nombres entiers (3 types) - 15 runs"""
        print("\n🔍 TEST 5: Nombres entiers (3 types) - 15 runs")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Nombres entiers et décimaux",
            "difficulte": "moyen"
        }
        
        generator_counts = Counter()
        fallback_count = 0
        successful_calls = 0
        
        for i in range(15):
            print(f"Run {i+1}/15...", end=" ")
            status_code, response = self.make_api_call(test_data)
            
            if status_code == 200 and isinstance(response, dict):
                metadata = response.get('metadata', {})
                generator_code = metadata.get('generator_code', 'UNKNOWN')
                is_fallback = metadata.get('is_fallback', True)
                
                generator_counts[generator_code] += 1
                if is_fallback:
                    fallback_count += 1
                successful_calls += 1
                print(f"✅ {generator_code} (fallback: {is_fallback})")
            else:
                print(f"❌ Error: {response}")
        
        # Verify expected generator types (with 6e_ prefix)
        expected_generators = ['6e_CALCUL_DECIMAUX', '6e_NOMBRES_LECTURE', '6e_NOMBRES_COMPARAISON']
        found_generators = list(generator_counts.keys())
        expected_found = [gen for gen in expected_generators if gen in found_generators]
        has_good_mix = len(expected_found) >= 2  # At least 2 out of 3 types
        
        details = {
            "successful_calls": successful_calls,
            "generator_counts": dict(generator_counts),
            "fallback_count": fallback_count,
            "expected_generators": expected_generators,
            "found_generators": found_generators,
            "expected_found": expected_found,
            "has_good_mix": has_good_mix
        }
        
        success = successful_calls >= 12 and has_good_mix
        self.log_test_result("Nombres entiers (3 types)", success, details)
        return success
    
    def test_geometrie_plan_5_types(self):
        """Test 6: Géométrie dans le plan (5 types) - 20 runs"""
        print("\n🔍 TEST 6: Géométrie dans le plan (5 types) - 20 runs")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Géométrie dans le plan",
            "difficulte": "moyen"
        }
        
        generator_counts = Counter()
        fallback_count = 0
        successful_calls = 0
        
        for i in range(20):
            print(f"Run {i+1}/20...", end=" ")
            status_code, response = self.make_api_call(test_data)
            
            if status_code == 200 and isinstance(response, dict):
                metadata = response.get('metadata', {})
                generator_code = metadata.get('generator_code', 'UNKNOWN')
                is_fallback = metadata.get('is_fallback', True)
                
                generator_counts[generator_code] += 1
                if is_fallback:
                    fallback_count += 1
                successful_calls += 1
                print(f"✅ {generator_code} (fallback: {is_fallback})")
            else:
                print(f"❌ Error: {response}")
        
        # Verify expected generator types (including TRIANGLE_CONSTRUCTION, QUADRILATERES, PROBLEME_2_ETAPES)
        expected_generators = ['6e_TRIANGLE_CONSTRUCTION', '6e_QUADRILATERES', '6e_PROBLEME_2_ETAPES']
        found_generators = list(generator_counts.keys())
        expected_found = [gen for gen in expected_generators if gen in found_generators]
        has_key_generators = len(expected_found) >= 2  # At least 2 key generators
        
        details = {
            "successful_calls": successful_calls,
            "generator_counts": dict(generator_counts),
            "fallback_count": fallback_count,
            "expected_generators": expected_generators,
            "found_generators": found_generators,
            "expected_found": expected_found,
            "has_key_generators": has_key_generators
        }
        
        success = successful_calls >= 15 and has_key_generators
        self.log_test_result("Géométrie dans le plan (5 types)", success, details)
        return success
    
    def test_enonce_quality_new_generators(self):
        """Test 7: Test enonce quality for new generators"""
        print("\n🔍 TEST 7: Enonce quality for new generators")
        print("="*60)
        
        quality_tests = [
            {
                "name": "PROP_TABLEAU HTML tables",
                "data": {"niveau": "6e", "chapitre": "Proportionnalité", "difficulte": "moyen"},
                "check_func": self._check_html_tables
            },
            {
                "name": "NOMBRES_LECTURE writing instructions", 
                "data": {"niveau": "6e", "chapitre": "Nombres entiers et décimaux", "difficulte": "moyen"},
                "check_func": self._check_writing_instructions
            },
            {
                "name": "FRACTION_REPRESENTATION SVG visualization",
                "data": {"niveau": "6e", "chapitre": "Fractions", "difficulte": "moyen"},
                "check_func": self._check_svg_visualization
            }
        ]
        
        quality_results = []
        
        for test in quality_tests:
            print(f"\n   Testing {test['name']}...")
            
            # Try multiple times to get the specific generator
            found_target = False
            attempts = 0
            max_attempts = 10
            
            while not found_target and attempts < max_attempts:
                attempts += 1
                status_code, response = self.make_api_call(test['data'])
                
                if status_code == 200 and isinstance(response, dict):
                    metadata = response.get('metadata', {})
                    generator_code = metadata.get('generator_code', '')
                    enonce_html = response.get('enonce_html', '')
                    
                    # Check if we got the target generator and test quality
                    quality_result = test['check_func'](generator_code, enonce_html, response)
                    if quality_result['target_found']:
                        found_target = True
                        quality_results.append({
                            "test_name": test['name'],
                            "success": quality_result['quality_passed'],
                            "details": quality_result,
                            "attempts": attempts
                        })
                        print(f"   ✅ Found target generator on attempt {attempts}")
                        if quality_result['quality_passed']:
                            print(f"   ✅ Quality check passed")
                        else:
                            print(f"   ❌ Quality check failed: {quality_result.get('reason', 'Unknown')}")
                        break
            
            if not found_target:
                quality_results.append({
                    "test_name": test['name'],
                    "success": False,
                    "details": {"target_found": False, "attempts": attempts},
                    "attempts": attempts
                })
                print(f"   ❌ Target generator not found after {attempts} attempts")
        
        # Overall quality assessment
        passed_quality_tests = sum(1 for result in quality_results if result['success'])
        total_quality_tests = len(quality_results)
        
        details = {
            "quality_results": quality_results,
            "passed_quality_tests": passed_quality_tests,
            "total_quality_tests": total_quality_tests
        }
        
        success = passed_quality_tests >= 2  # At least 2 out of 3 quality tests should pass
        self.log_test_result("Enonce quality for new generators", success, details)
        return success
    
    def _check_html_tables(self, generator_code, enonce_html, response):
        """Check for properly formatted HTML tables"""
        target_generators = ['6e_PROP_TABLEAU']
        target_found = any(gen in generator_code for gen in target_generators)
        
        if not target_found:
            return {"target_found": False, "quality_passed": False}
        
        # Check for HTML table elements
        has_table = '<table' in enonce_html
        has_proper_style = 'border-collapse' in enonce_html
        has_headers = '<th' in enonce_html or '<td' in enonce_html
        
        quality_passed = has_table and has_proper_style and has_headers
        
        return {
            "target_found": True,
            "quality_passed": quality_passed,
            "has_table": has_table,
            "has_proper_style": has_proper_style,
            "has_headers": has_headers,
            "generator_code": generator_code,
            "reason": "Missing table elements" if not quality_passed else "All table elements present"
        }
    
    def _check_writing_instructions(self, generator_code, enonce_html, response):
        """Check for writing instructions in number exercises"""
        target_generators = ['6e_NOMBRES_LECTURE']
        target_found = any(gen in generator_code for gen in target_generators)
        
        if not target_found:
            return {"target_found": False, "quality_passed": False}
        
        # Check for writing instruction keywords
        writing_keywords = ['écrire en lettres', 'écrire', 'lettres', 'écriture']
        has_writing_instruction = any(keyword in enonce_html.lower() for keyword in writing_keywords)
        
        # Check for numbers to convert
        import re
        has_numbers = bool(re.search(r'\d+', enonce_html))
        
        quality_passed = has_writing_instruction and has_numbers
        
        return {
            "target_found": True,
            "quality_passed": quality_passed,
            "has_writing_instruction": has_writing_instruction,
            "has_numbers": has_numbers,
            "generator_code": generator_code,
            "reason": "Missing writing instructions or numbers" if not quality_passed else "Writing instructions and numbers present"
        }
    
    def _check_svg_visualization(self, generator_code, enonce_html, response):
        """Check for SVG visualization in fraction exercises"""
        target_generators = ['6e_FRACTION_REPRESENTATION']
        target_found = any(gen in generator_code for gen in target_generators)
        
        if not target_found:
            return {"target_found": False, "quality_passed": False}
        
        # Check for SVG elements
        has_svg = '<svg' in enonce_html
        has_geometric_shapes = any(shape in enonce_html for shape in ['<rect', '<circle', '<path'])
        
        quality_passed = has_svg and has_geometric_shapes
        
        return {
            "target_found": True,
            "quality_passed": quality_passed,
            "has_svg": has_svg,
            "has_geometric_shapes": has_geometric_shapes,
            "generator_code": generator_code,
            "reason": "Missing SVG or geometric shapes" if not quality_passed else "SVG with geometric shapes present"
        }
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 STARTING COMPREHENSIVE 6e GENERATORS TESTING")
        print("="*80)
        print(f"Backend URL: {self.base_url}")
        print(f"API Endpoint: {self.api_url}/v1/exercises/generate")
        print(f"Test Session ID: {self.guest_id}")
        print("="*80)
        
        start_time = time.time()
        
        # Run all tests
        test_functions = [
            self.test_perimetres_aires_4_types,
            self.test_angles_3_types,
            self.test_fractions_2_types,
            self.test_proportionnalite_3_types,
            self.test_nombres_entiers_3_types,
            self.test_geometrie_plan_5_types,
            self.test_enonce_quality_new_generators
        ]
        
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                print(f"❌ ERROR in {test_func.__name__}: {e}")
                self.log_test_result(test_func.__name__, False, {"error": str(e)})
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print comprehensive summary
        self.print_final_summary(total_time)
        
        return self.test_results
    
    def print_final_summary(self, total_time):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE 6e GENERATORS TEST SUMMARY")
        print("="*80)
        
        print(f"⏱️  Total Test Time: {total_time:.2f} seconds")
        print(f"📈 Overall Results: {self.test_results['passed_tests']}/{self.test_results['total_tests']} tests passed")
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100 if self.test_results['total_tests'] > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results['test_details']:
            print(f"   {result['status']} - {result['test_name']}")
            if 'generator_counts' in result['details']:
                print(f"      Generator counts: {result['details']['generator_counts']}")
            if 'successful_calls' in result['details']:
                print(f"      Successful calls: {result['details']['successful_calls']}")
            if 'expected_found' in result['details']:
                print(f"      Expected generators found: {result['details']['expected_found']}")
        
        print("\n🎯 WAVE 1, 2 & 3 GENERATORS ASSESSMENT:")
        
        # Collect all generator codes found
        all_generators = set()
        for result in self.test_results['test_details']:
            if 'generator_counts' in result['details']:
                all_generators.update(result['details']['generator_counts'].keys())
        
        print(f"   📦 Total unique generators found: {len(all_generators)}")
        print(f"   🔧 Generators: {sorted(all_generators)}")
        
        # Count non-fallback generators
        non_fallback_generators = []
        for result in self.test_results['test_details']:
            if 'generator_counts' in result['details'] and 'fallback_count' in result['details']:
                total_calls = result['details']['successful_calls']
                fallback_calls = result['details']['fallback_count']
                non_fallback_calls = total_calls - fallback_calls
                if non_fallback_calls > 0:
                    non_fallback_generators.extend(result['details']['generator_counts'].keys())
        
        unique_non_fallback = set(non_fallback_generators)
        print(f"   ✨ Non-fallback generators: {len(unique_non_fallback)}")
        
        # Overall assessment
        if success_rate >= 85:
            print("\n🎉 EXCELLENT: 6e generators (Waves 1, 2 & 3) are working excellently!")
        elif success_rate >= 70:
            print("\n✅ GOOD: 6e generators are working well with minor issues")
        elif success_rate >= 50:
            print("\n⚠️  MODERATE: 6e generators have some issues that need attention")
        else:
            print("\n❌ CRITICAL: 6e generators have significant issues requiring immediate attention")
        
        print("="*80)

def main():
    """Main test execution"""
    tester = SixeGeneratorsTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    success_rate = (results['passed_tests'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
    return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    exit(main())