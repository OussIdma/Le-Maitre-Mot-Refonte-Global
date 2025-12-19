#!/usr/bin/env python3
"""
Test V1 Exercises Generation API Endpoint
Testing the 3 bug fixes for /api/v1/exercises/generate
"""

import requests
import json
import sys
import time
from datetime import datetime

class V1ExercisesAPITester:
    def __init__(self):
        # Get backend URL from frontend .env
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip()
                        break
                else:
                    self.base_url = "https://math-exercise-sync.preview.emergentagent.com"
        except:
            self.base_url = "https://math-exercise-sync.preview.emergentagent.com"
        
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🔧 Testing V1 Exercises API at: {self.base_url}")
        print(f"📅 Test session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   URL: {url}")
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)
            
            response_time = time.time() - start_time
            
            print(f"   Status: {response.status_code} (Response time: {response_time:.2f}s)")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error text: {response.text[:200]}")
                    return False, {"error": response.text}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timeout after {timeout}s")
            return False, {"error": "timeout"}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {"error": str(e)}

    def test_html_tables_proportionnalite(self):
        """Test HTML Tables (Proportionnalité) - Priority 1"""
        print("\n" + "="*60)
        print("🧪 TEST 1: HTML Tables (Proportionnalité) - Priority 1")
        print("VERIFY: enonce_html contains actual HTML table tags <table NOT escaped &lt;table")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Proportionnalité",
            "difficulte": "moyen"
        }
        
        success, response = self.run_test(
            "HTML Tables Proportionnalité",
            "POST",
            "v1/exercises/generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):
            # Check if we have enonce_html field
            enonce_html = response.get('enonce_html', '')
            if not enonce_html:
                print("   ❌ No enonce_html field in response")
                self.test_results.append({
                    "test": "HTML Tables Proportionnalité",
                    "status": "FAILED",
                    "reason": "No enonce_html field"
                })
                return False, response
            
            # Check for HTML table tags (not escaped)
            has_html_table = '<table' in enonce_html
            has_escaped_table = '&lt;table' in enonce_html
            
            print(f"   📊 enonce_html length: {len(enonce_html)} characters")
            print(f"   🔍 Contains <table: {has_html_table}")
            print(f"   🔍 Contains &lt;table (escaped): {has_escaped_table}")
            
            if has_html_table and not has_escaped_table:
                print("   ✅ HTML table tags are properly rendered (not escaped)")
                # Show a sample of the HTML
                if 'style=' in enonce_html:
                    print("   ✅ HTML table has styling attributes")
                
                # Extract table sample
                table_start = enonce_html.find('<table')
                if table_start != -1:
                    table_sample = enonce_html[table_start:table_start+100]
                    print(f"   📋 Table sample: {table_sample}...")
                
                self.test_results.append({
                    "test": "HTML Tables Proportionnalité",
                    "status": "PASSED",
                    "details": "HTML tables properly rendered without escaping"
                })
                return True, response
            else:
                if has_escaped_table:
                    print("   ❌ HTML table tags are escaped (&lt;table found)")
                    reason = "HTML tables are escaped"
                else:
                    print("   ❌ No HTML table tags found")
                    reason = "No HTML table tags found"
                
                self.test_results.append({
                    "test": "HTML Tables Proportionnalité",
                    "status": "FAILED",
                    "reason": reason
                })
                return False, response
        else:
            self.test_results.append({
                "test": "HTML Tables Proportionnalité",
                "status": "FAILED",
                "reason": "API call failed"
            })
            return False, response

    def test_fractions_enonce(self):
        """Test Fractions enonce - Priority 2"""
        print("\n" + "="*60)
        print("🧪 TEST 2: Fractions enonce - Priority 2")
        print("VERIFY: enonce_html contains readable mathematical instruction like 'Calculer :' followed by fractions")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Fractions",
            "difficulte": "moyen"
        }
        
        success, response = self.run_test(
            "Fractions enonce content",
            "POST",
            "v1/exercises/generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):
            enonce_html = response.get('enonce_html', '')
            if not enonce_html:
                print("   ❌ No enonce_html field in response")
                self.test_results.append({
                    "test": "Fractions enonce",
                    "status": "FAILED",
                    "reason": "No enonce_html field"
                })
                return False, response
            
            print(f"   📊 enonce_html length: {len(enonce_html)} characters")
            print(f"   📋 Content preview: {enonce_html[:200]}...")
            
            # Check for mathematical instruction
            has_calculer = 'Calculer' in enonce_html or 'calculer' in enonce_html
            has_fractions = '\\frac{' in enonce_html or 'frac{' in enonce_html
            has_generic_only = enonce_html.strip() == "Exercice de Fractions"
            
            print(f"   🔍 Contains 'Calculer': {has_calculer}")
            print(f"   🔍 Contains fractions (\\frac): {has_fractions}")
            print(f"   🔍 Is generic only: {has_generic_only}")
            
            if has_generic_only:
                print("   ❌ Content is just generic 'Exercice de Fractions'")
                self.test_results.append({
                    "test": "Fractions enonce",
                    "status": "FAILED",
                    "reason": "Generic content only - no actual math"
                })
                return False, response
            elif has_calculer and has_fractions:
                print("   ✅ Contains mathematical instruction with fractions")
                self.test_results.append({
                    "test": "Fractions enonce",
                    "status": "PASSED",
                    "details": "Contains 'Calculer' instruction with fractions"
                })
                return True, response
            elif has_fractions:
                print("   ✅ Contains fractions (acceptable)")
                self.test_results.append({
                    "test": "Fractions enonce",
                    "status": "PASSED",
                    "details": "Contains fractions content"
                })
                return True, response
            else:
                print("   ❌ No mathematical content found")
                self.test_results.append({
                    "test": "Fractions enonce",
                    "status": "FAILED",
                    "reason": "No mathematical content found"
                })
                return False, response
        else:
            self.test_results.append({
                "test": "Fractions enonce",
                "status": "FAILED",
                "reason": "API call failed"
            })
            return False, response

    def test_newly_mapped_chapter(self):
        """Test newly mapped chapter - Priority 3"""
        print("\n" + "="*60)
        print("🧪 TEST 3: Newly mapped chapter - Priority 3")
        print("VERIFY: 'Nombres en écriture fractionnaire' returns 200 OK with valid exercise data")
        print("="*60)
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Nombres en écriture fractionnaire",
            "difficulte": "moyen"
        }
        
        success, response = self.run_test(
            "Newly mapped chapter",
            "POST",
            "v1/exercises/generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):
            # Check for valid exercise data
            enonce_html = response.get('enonce_html', '')
            has_content = len(enonce_html.strip()) > 10
            
            print(f"   📊 Response has content: {has_content}")
            if enonce_html:
                print(f"   📋 Content preview: {enonce_html[:150]}...")
            
            # Check for error about unmapped chapter
            error_msg = str(response).lower()
            has_unmapped_error = 'chapitre non mappé' in error_msg or 'non mappé' in error_msg
            
            print(f"   🔍 Has unmapped chapter error: {has_unmapped_error}")
            
            if has_unmapped_error:
                print("   ❌ Still getting 'CHAPITRE NON MAPPÉ' error")
                self.test_results.append({
                    "test": "Newly mapped chapter",
                    "status": "FAILED",
                    "reason": "Chapter still not mapped"
                })
                return False, response
            elif has_content:
                print("   ✅ Chapter is properly mapped and returns valid content")
                self.test_results.append({
                    "test": "Newly mapped chapter",
                    "status": "PASSED",
                    "details": "Chapter properly mapped, no unmapped error"
                })
                return True, response
            else:
                print("   ⚠️  No unmapped error but content is empty")
                self.test_results.append({
                    "test": "Newly mapped chapter",
                    "status": "PARTIAL",
                    "reason": "No error but empty content"
                })
                return False, response
        else:
            self.test_results.append({
                "test": "Newly mapped chapter",
                "status": "FAILED",
                "reason": "API call failed"
            })
            return False, response

    def test_tableaux_donnees_html(self):
        """Test Tableaux de données (another HTML table case)"""
        print("\n" + "="*60)
        print("🧪 TEST 4: Tableaux de données HTML tables")
        print("VERIFY: enonce_html contains HTML table tags for data tables")
        print("="*60)
        
        # Use a valid chapter that might contain tables
        test_data = {
            "niveau": "6e",
            "chapitre": "Périmètres et aires",
            "difficulte": "moyen"
        }
        
        success, response = self.run_test(
            "Tableaux de données HTML",
            "POST",
            "v1/exercises/generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):
            enonce_html = response.get('enonce_html', '')
            if not enonce_html:
                print("   ❌ No enonce_html field in response")
                self.test_results.append({
                    "test": "Tableaux de données HTML",
                    "status": "FAILED",
                    "reason": "No enonce_html field"
                })
                return False, response
            
            print(f"   📊 enonce_html length: {len(enonce_html)} characters")
            print(f"   📋 Content preview: {enonce_html[:200]}...")
            
            # Check for HTML table tags
            has_html_table = '<table' in enonce_html
            has_escaped_table = '&lt;table' in enonce_html
            
            print(f"   🔍 Contains <table: {has_html_table}")
            print(f"   🔍 Contains &lt;table (escaped): {has_escaped_table}")
            
            # For this test, we accept that not all exercises will have tables
            # The key is that IF there are tables, they should not be escaped
            if has_escaped_table:
                print("   ❌ HTML table tags are escaped")
                self.test_results.append({
                    "test": "Tableaux de données HTML",
                    "status": "FAILED",
                    "reason": "HTML tables are escaped"
                })
                return False, response
            elif has_html_table:
                print("   ✅ HTML table tags are properly rendered")
                self.test_results.append({
                    "test": "Tableaux de données HTML",
                    "status": "PASSED",
                    "details": "HTML tables properly rendered"
                })
                return True, response
            else:
                print("   ✅ No HTML tables found (acceptable - no escaping issues)")
                self.test_results.append({
                    "test": "Tableaux de données HTML",
                    "status": "PASSED",
                    "details": "No HTML tables but no escaping issues"
                })
                return True, response
        else:
            self.test_results.append({
                "test": "Tableaux de données HTML",
                "status": "FAILED",
                "reason": "API call failed"
            })
            return False, response

    def test_api_health_check(self):
        """Test General API health check"""
        print("\n" + "="*60)
        print("🧪 TEST 5: General API health check")
        print("VERIFY: GET /api/v1/exercises/health returns {\"status\": \"healthy\", ...}")
        print("="*60)
        
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "v1/exercises/health",
            200,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            status = response.get('status', '')
            print(f"   📊 Health status: {status}")
            
            if status == 'healthy':
                print("   ✅ API health check passed")
                self.test_results.append({
                    "test": "API Health Check",
                    "status": "PASSED",
                    "details": f"Status: {status}"
                })
                return True, response
            else:
                print(f"   ❌ Unexpected health status: {status}")
                self.test_results.append({
                    "test": "API Health Check",
                    "status": "FAILED",
                    "reason": f"Unexpected status: {status}"
                })
                return False, response
        else:
            self.test_results.append({
                "test": "API Health Check",
                "status": "FAILED",
                "reason": "API call failed or invalid response"
            })
            return False, response

    def run_all_tests(self):
        """Run all V1 exercises API tests"""
        print("\n" + "="*80)
        print("🚀 STARTING V1 EXERCISES API COMPREHENSIVE TESTING")
        print("Testing 3 bug fixes for /api/v1/exercises/generate")
        print("="*80)
        
        # Run all tests
        test_methods = [
            self.test_html_tables_proportionnalite,
            self.test_fractions_enonce,
            self.test_newly_mapped_chapter,
            self.test_tableaux_donnees_html,
            self.test_api_health_check
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
                self.test_results.append({
                    "test": test_method.__name__,
                    "status": "ERROR",
                    "reason": str(e)
                })
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 V1 EXERCISES API TEST SUMMARY")
        print("="*80)
        
        print(f"📈 Overall Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run*100):.1f}%)")
        
        # Categorize results
        passed_tests = [r for r in self.test_results if r['status'] == 'PASSED']
        failed_tests = [r for r in self.test_results if r['status'] == 'FAILED']
        partial_tests = [r for r in self.test_results if r['status'] == 'PARTIAL']
        error_tests = [r for r in self.test_results if r['status'] == 'ERROR']
        
        print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
        for test in passed_tests:
            details = test.get('details', '')
            print(f"   • {test['test']}: {details}")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                reason = test.get('reason', 'Unknown')
                print(f"   • {test['test']}: {reason}")
        
        if partial_tests:
            print(f"\n⚠️  PARTIAL TESTS ({len(partial_tests)}):")
            for test in partial_tests:
                reason = test.get('reason', 'Unknown')
                print(f"   • {test['test']}: {reason}")
        
        if error_tests:
            print(f"\n🚨 ERROR TESTS ({len(error_tests)}):")
            for test in error_tests:
                reason = test.get('reason', 'Unknown')
                print(f"   • {test['test']}: {reason}")
        
        # Bug fix assessment
        print(f"\n🔧 BUG FIX ASSESSMENT:")
        
        # Bug 1: HTML Tables
        html_tests = [r for r in self.test_results if 'HTML' in r['test']]
        html_passed = all(t['status'] == 'PASSED' for t in html_tests)
        print(f"   Bug 1 (HTML Tables): {'✅ FIXED' if html_passed else '❌ NOT FIXED'}")
        
        # Bug 2: Fractions enonce
        fractions_tests = [r for r in self.test_results if 'Fractions' in r['test']]
        fractions_passed = all(t['status'] == 'PASSED' for t in fractions_tests)
        print(f"   Bug 2 (Fractions enonce): {'✅ FIXED' if fractions_passed else '❌ NOT FIXED'}")
        
        # Bug 3: Chapter mapping
        mapping_tests = [r for r in self.test_results if 'mapped' in r['test']]
        mapping_passed = all(t['status'] == 'PASSED' for t in mapping_tests)
        print(f"   Bug 3 (Chapter mapping): {'✅ FIXED' if mapping_passed else '❌ NOT FIXED'}")
        
        # Overall assessment
        all_critical_passed = html_passed and fractions_passed and mapping_passed
        if all_critical_passed:
            print(f"\n🎉 ALL 3 BUG FIXES VERIFIED SUCCESSFULLY!")
            print(f"   ✅ HTML tables render properly without escaping")
            print(f"   ✅ Fractions generate actual mathematical content")
            print(f"   ✅ New chapter mapping works without errors")
        else:
            print(f"\n⚠️  SOME BUG FIXES NEED ATTENTION")
            if not html_passed:
                print(f"   ❌ HTML table escaping issue persists")
            if not fractions_passed:
                print(f"   ❌ Fractions content generation issue persists")
            if not mapping_passed:
                print(f"   ❌ Chapter mapping issue persists")
        
        print(f"\n📅 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

def main():
    """Main test execution"""
    tester = V1ExercisesAPITester()
    tester.run_all_tests()
    
    # Return exit code based on results
    if tester.tests_passed == tester.tests_run:
        sys.exit(0)  # All tests passed
    else:
        sys.exit(1)  # Some tests failed

if __name__ == "__main__":
    main()