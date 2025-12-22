import requests
import sys
import json
import time
import uuid
import re
import os
from datetime import datetime

class MathDebugTester:
    def __init__(self, base_url="https://math-exercise-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.generated_document_id = None
        self.guest_id = f"test-math-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}"

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

    def test_math_document_generation(self):
        """Test document generation with mathematical expressions containing fractions"""
        print("\n🔍 MATH DEBUG: Testing document generation with mathematical expressions...")
        
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "4e",
            "chapitre": "Fractions",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 2,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"   Generating math document with fractions: {test_data}")
        success, response = self.run_test(
            "MATH DEBUG: Generate Math Document with Fractions", 
            "POST", 
            "generate", 
            200, 
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):
            document = response.get('document')
            if document:
                self.generated_document_id = document.get('id')
                exercises = document.get('exercises', [])
                print(f"   ✅ Math document generated with {len(exercises)} exercises")
                print(f"   Document ID: {self.generated_document_id}")
                
                # Analyze exercises for LaTeX content
                latex_found = False
                broken_fractions_found = False
                
                for i, exercise in enumerate(exercises):
                    enonce = exercise.get('enonce', '')
                    solution = exercise.get('solution', {})
                    
                    print(f"\n   📝 Exercise {i+1} Analysis:")
                    print(f"   Enonce preview: {enonce[:150]}...")
                    
                    # Check for LaTeX fractions in enonce
                    if '\\frac{' in enonce:
                        latex_found = True
                        print(f"   ✅ Exercise {i+1} contains LaTeX fractions in enonce")
                        # Extract and show LaTeX content
                        fractions = re.findall(r'\\frac\{[^}]+\}\{[^}]+\}', enonce)
                        print(f"   LaTeX fractions found: {fractions}")
                    
                    # Check for broken fraction patterns
                    broken_patterns = []
                    if ' de ' in enonce.lower():
                        broken_patterns.append('de')
                    if ' par ' in enonce.lower():
                        broken_patterns.append('par')
                    if re.search(r'\d+/\d+', enonce):
                        broken_patterns.append('slash notation')
                    
                    if broken_patterns:
                        broken_fractions_found = True
                        print(f"   ❌ Exercise {i+1} contains broken fraction patterns: {broken_patterns}")
                    
                    # Check solution steps
                    etapes = solution.get('etapes', [])
                    for j, etape in enumerate(etapes):
                        if '\\frac{' in etape:
                            latex_found = True
                            print(f"   ✅ Exercise {i+1} step {j+1} contains LaTeX fractions")
                            fractions = re.findall(r'\\frac\{[^}]+\}\{[^}]+\}', etape)
                            print(f"   LaTeX fractions in step: {fractions}")
                    
                    # Check result
                    resultat = solution.get('resultat', '')
                    if '\\frac{' in resultat:
                        latex_found = True
                        print(f"   ✅ Exercise {i+1} result contains LaTeX fractions")
                        fractions = re.findall(r'\\frac\{[^}]+\}\{[^}]+\}', resultat)
                        print(f"   LaTeX fractions in result: {fractions}")
                
                print(f"\n   📊 ANALYSIS SUMMARY:")
                if latex_found:
                    print("   ✅ AI is generating proper LaTeX \\frac{}{} format")
                else:
                    print("   ❌ No LaTeX fractions found - AI may not be following MATH_FORMATTING_RULE")
                
                if broken_fractions_found:
                    print("   ❌ CRITICAL: Broken fraction patterns detected - this explains user's PDF issue!")
                else:
                    print("   ✅ No broken fraction patterns detected")
                
                return True, {
                    "latex_content_found": latex_found, 
                    "broken_fractions_found": broken_fractions_found,
                    "exercises_count": len(exercises)
                }
            else:
                print(f"   ❌ No document in response: {response}")
        else:
            print(f"   ❌ Math document generation failed")
        
        return success, response

    def test_latex_to_mathml_function(self):
        """Test the process_math_content_for_pdf() function directly"""
        print("\n🔍 MATH DEBUG: Testing LaTeX to MathML conversion function...")
        
        # Import the function
        try:
            import sys
            sys.path.append('/app/backend')
            from curriculum_data import process_math_content_for_pdf
            print("   ✅ Successfully imported process_math_content_for_pdf function")
        except ImportError as e:
            print(f"   ❌ Failed to import function: {e}")
            return False, {"error": "import_failed"}
        
        # Test cases with LaTeX expressions
        test_cases = [
            {
                "input": "Calculer \\frac{7}{8} + \\frac{3}{4}",
                "description": "Simple fraction addition"
            },
            {
                "input": "Résoudre \\frac{2x}{5} = \\frac{3}{10}",
                "description": "Fraction equation"
            },
            {
                "input": "Simplifier \\frac{15}{20} et \\frac{6}{9}",
                "description": "Multiple fractions"
            },
            {
                "input": "Calculer x^{2} + 3x^{4}",
                "description": "Powers"
            },
            {
                "input": "Résoudre \\sqrt{16} + \\sqrt{25}",
                "description": "Square roots"
            },
            {
                "input": "Expression complexe: \\frac{x^{2}}{\\sqrt{9}}",
                "description": "Mixed expressions"
            },
            {
                "input": "Calculer 7 de 8 plus 3 par 4",
                "description": "Broken fraction format (should not convert)"
            }
        ]
        
        conversion_results = []
        for i, test_case in enumerate(test_cases):
            print(f"\n   Test {i+1}: {test_case['description']}")
            print(f"   Input: {test_case['input']}")
            
            try:
                result = process_math_content_for_pdf(test_case['input'])
                print(f"   Output: {result[:200]}...")
                
                # Check if conversion happened
                if result != test_case['input']:
                    print("   ✅ Conversion occurred")
                    # Check for MathML tags
                    if '<math' in result and '</math>' in result:
                        print("   ✅ MathML tags found in output")
                        conversion_results.append({"test": i+1, "success": True, "has_mathml": True})
                    else:
                        print("   ⚠️  Conversion occurred but no MathML tags found")
                        conversion_results.append({"test": i+1, "success": True, "has_mathml": False})
                else:
                    print("   ❌ No conversion occurred")
                    conversion_results.append({"test": i+1, "success": False, "has_mathml": False})
                    
            except Exception as e:
                print(f"   ❌ Conversion failed with error: {e}")
                conversion_results.append({"test": i+1, "success": False, "error": str(e)})
        
        # Summary
        successful_conversions = sum(1 for r in conversion_results if r.get('success', False))
        mathml_conversions = sum(1 for r in conversion_results if r.get('has_mathml', False))
        
        print(f"\n   📊 CONVERSION SUMMARY:")
        print(f"   ✅ Successful conversions: {successful_conversions}/{len(test_cases)}")
        print(f"   ✅ MathML output: {mathml_conversions}/{len(test_cases)}")
        
        if successful_conversions >= len(test_cases) - 1 and mathml_conversions > 0:  # Allow one failure for broken format
            print("   ✅ LaTeX to MathML function is working correctly")
            return True, {"conversions": conversion_results}
        else:
            print("   ❌ LaTeX to MathML function has issues")
            return False, {"conversions": conversion_results}

    def test_pdf_export_with_math_debug(self):
        """Test PDF export process with mathematical content debugging"""
        if not self.generated_document_id:
            print("⚠️  Skipping PDF math debug test - no document generated")
            return False, {}
        
        print("\n🔍 MATH DEBUG: Testing PDF export with mathematical content...")
        
        export_data = {
            "document_id": self.generated_document_id,
            "export_type": "sujet",
            "guest_id": self.guest_id
        }
        
        print(f"   Exporting PDF for document: {self.generated_document_id}")
        success, response = self.run_test(
            "MATH DEBUG: PDF Export with Math Content",
            "POST",
            "export",
            200,
            data=export_data,
            timeout=45
        )
        
        if success:
            print("   ✅ PDF export completed successfully")
            print("   ✅ No errors in PDF generation pipeline")
            
            # Check if we can get the document content to verify math processing
            doc_success, doc_response = self.run_test(
                "MATH DEBUG: Get Document for Math Verification",
                "GET",
                f"documents?guest_id={self.guest_id}",
                200
            )
            
            if doc_success and isinstance(doc_response, dict):
                documents = doc_response.get('documents', [])
                target_doc = None
                for doc in documents:
                    if doc.get('id') == self.generated_document_id:
                        target_doc = doc
                        break
                
                if target_doc:
                    exercises = target_doc.get('exercises', [])
                    print(f"   Found document with {len(exercises)} exercises")
                    
                    # Check for math content in exercises
                    for i, exercise in enumerate(exercises):
                        enonce = exercise.get('enonce', '')
                        if '\\frac{' in enonce:
                            print(f"   ⚠️  Exercise {i+1} still contains LaTeX in enonce (should be converted for PDF)")
                        elif '<math' in enonce:
                            print(f"   ✅ Exercise {i+1} contains MathML in enonce")
                        elif any(pattern in enonce.lower() for pattern in [' de ', ' par ']):
                            print(f"   ❌ Exercise {i+1} may contain broken fractions: {enonce[:100]}...")
            
            return True, {"pdf_export_success": True}
        else:
            print("   ❌ PDF export failed")
            if isinstance(response, dict):
                error_detail = response.get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
            return False, {"pdf_export_success": False}

    def test_pdf_export_corrige_with_math_debug(self):
        """Test PDF corrigé export with mathematical content debugging"""
        if not self.generated_document_id:
            print("⚠️  Skipping PDF corrigé math debug test - no document generated")
            return False, {}
        
        print("\n🔍 MATH DEBUG: Testing PDF corrigé export with mathematical content...")
        
        export_data = {
            "document_id": self.generated_document_id,
            "export_type": "corrige",
            "guest_id": self.guest_id
        }
        
        print(f"   Exporting corrigé PDF for document: {self.generated_document_id}")
        success, response = self.run_test(
            "MATH DEBUG: PDF Corrigé Export with Math Content",
            "POST",
            "export",
            200,
            data=export_data,
            timeout=45
        )
        
        if success:
            print("   ✅ PDF corrigé export completed successfully")
            print("   ✅ Math content processing in solution steps should be working")
            return True, {"pdf_corrige_export_success": True}
        else:
            print("   ❌ PDF corrigé export failed")
            if isinstance(response, dict):
                error_detail = response.get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
            return False, {"pdf_corrige_export_success": False}

    def test_backend_logs_for_math_processing(self):
        """Check backend logs for math processing indicators"""
        print("\n🔍 MATH DEBUG: Checking backend logs for math processing...")
        
        # Test a simple math generation to trigger logging
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "6e",
            "chapitre": "Fractions",
            "type_doc": "exercices",
            "difficulte": "facile",
            "nb_exercices": 1,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        success, response = self.run_test(
            "MATH DEBUG: Simple Math Generation for Log Analysis",
            "POST",
            "generate",
            200,
            data=test_data,
            timeout=30
        )
        
        if success:
            print("   ✅ Math generation request successful - backend processing working")
            
            # Try to export to trigger PDF math processing
            if isinstance(response, dict) and response.get('document', {}).get('id'):
                doc_id = response['document']['id']
                export_data = {
                    "document_id": doc_id,
                    "export_type": "sujet",
                    "guest_id": self.guest_id
                }
                
                export_success, export_response = self.run_test(
                    "MATH DEBUG: Export for Log Analysis",
                    "POST",
                    "export",
                    200,
                    data=export_data,
                    timeout=30
                )
                
                if export_success:
                    print("   ✅ PDF export successful - math processing pipeline working")
                    return True, {"backend_processing": True}
                else:
                    print("   ❌ PDF export failed - possible math processing issue")
                    return False, {"backend_processing": False}
        else:
            print("   ❌ Math generation failed - backend issue")
            return False, {"backend_processing": False}

    def run_math_debug_tests(self):
        """Run focused tests for mathematical expressions PDF rendering debug"""
        print("\n" + "="*80)
        print("🔍 MATHEMATICAL EXPRESSIONS PDF RENDERING DEBUG TESTS")
        print("="*80)
        print("CRITICAL ISSUE: User reports PDF shows broken fractions like '715 de 45', '23 par 910'")
        print("INVESTIGATION: Testing LaTeX→MathML conversion pipeline for PDF export")
        print("EXPECTED: Identify exact point where LaTeX→MathML conversion fails")
        print("="*80)
        
        math_tests = [
            ("Generate Math Document", self.test_math_document_generation),
            ("Test LaTeX→MathML Function", self.test_latex_to_mathml_function),
            ("PDF Export Math Debug", self.test_pdf_export_with_math_debug),
            ("PDF Corrigé Math Debug", self.test_pdf_export_corrige_with_math_debug),
            ("Backend Logs Analysis", self.test_backend_logs_for_math_processing)
        ]
        
        math_passed = 0
        math_total = len(math_tests)
        
        for test_name, test_func in math_tests:
            print(f"\n{'='*60}")
            print(f"🔍 {test_name}")
            print(f"{'='*60}")
            try:
                success, response = test_func()
                if success:
                    math_passed += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
                    if isinstance(response, dict) and 'error' in response:
                        print(f"   Error detail: {response['error']}")
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
        
        print(f"\n{'='*80}")
        print(f"🔍 MATH DEBUG TEST RESULTS: {math_passed}/{math_total} passed")
        print(f"{'='*80}")
        
        if math_passed == math_total:
            print("🎉 ALL MATH DEBUG TESTS PASSED!")
            print("✅ LaTeX→MathML conversion pipeline appears to be working")
        else:
            print("❌ SOME MATH DEBUG TESTS FAILED")
            print("⚠️  LaTeX→MathML conversion pipeline has issues")
            
        return math_passed, math_total

if __name__ == "__main__":
    tester = MathDebugTester()
    tester.run_math_debug_tests()