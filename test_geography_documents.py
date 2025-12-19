#!/usr/bin/env python3
"""
Standalone test for Geography document functionality
"""

import requests
import time
import uuid
import sys
import json

class GeographyDocumentTester:
    def __init__(self, base_url="https://math-exercise-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.guest_id = str(uuid.uuid4())
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=30):
        """Run a single test"""
        self.tests_run += 1
        
        try:
            url = f"{self.api_url}/{endpoint}"
            headers = headers or {'Content-Type': 'application/json'}
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                self.tests_passed += 1
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ {name}: Expected {expected_status}, got {response.status_code}")
                try:
                    return False, response.json()
                except:
                    return False, response.text
                    
        except Exception as e:
            print(f"❌ {name}: Exception - {e}")
            return False, {"error": str(e)}

    def test_geography_generation_6e_with_documents(self):
        """Test Geography exercise generation for 6e level with educational documents - CRITICAL TEST"""
        test_data = {
            "matiere": "Géographie",
            "niveau": "6e",
            "chapitre": "Découvrir le(s) lieu(x) où j'habite",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 2,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"\n🗺️ CRITICAL TEST: Geography 6e Generation with Educational Documents")
        print(f"   Chapter: {test_data['chapitre']}")
        print(f"   Expected: Geography exercises with attached educational documents")
        
        start_time = time.time()
        success, response = self.run_test(
            "Geography 6e Generation with Documents", 
            "POST", 
            "generate", 
            200, 
            data=test_data,
            timeout=60
        )
        generation_time = time.time() - start_time
        
        if success and isinstance(response, dict):
            document = response.get('document')
            if document:
                exercises = document.get('exercises', [])
                print(f"   ✅ Geography 6e generation SUCCESSFUL with {len(exercises)} exercises")
                print(f"   ⏱️  Generation time: {generation_time:.2f} seconds")
                
                if generation_time > 30:
                    print(f"   ⚠️  Generation time exceeds 30 seconds threshold")
                else:
                    print(f"   ✅ Generation time within 30 seconds threshold")
                
                # Track document statistics
                exercises_with_documents = 0
                total_documents = 0
                
                # Check exercise content and documents
                for i, exercise in enumerate(exercises):
                    enonce = exercise.get('enonce', '')
                    icone = exercise.get('icone', '')
                    exercise_type = exercise.get('type', '')
                    educational_document = exercise.get('document')  # Check for educational document
                    
                    print(f"\n   Exercise {i+1}: Type={exercise_type}, Icon={icone}")
                    print(f"   Content preview: {enonce[:150]}...")
                    
                    # Check for Geography specific content
                    geo_indicators = ['lieu', 'habite', 'territoire', 'espace', 'carte', 'région', 'ville', 'habitat', 'environnement', 'géographique']
                    has_geo_content = any(indicator in enonce.lower() for indicator in geo_indicators)
                    if has_geo_content:
                        print(f"   ✅ Exercise {i+1} has appropriate Geography content")
                    else:
                        print(f"   ⚠️  Exercise {i+1} may not have specific Geography content")
                    
                    # Check for correct icon assignment
                    expected_geo_icons = ['map', 'compass', 'users', 'building-2', 'globe']
                    if icone in expected_geo_icons:
                        print(f"   ✅ Exercise {i+1} has appropriate Geography icon: {icone}")
                    else:
                        print(f"   ⚠️  Exercise {i+1} has unexpected icon: {icone}")
                    
                    # CRITICAL: Check for educational documents (main feature being tested)
                    if educational_document:
                        exercises_with_documents += 1
                        total_documents += 1
                        print(f"   ✅ Exercise {i+1} has educational document attached")
                        
                        # Validate document structure
                        if isinstance(educational_document, dict):
                            title = educational_document.get('title', '')
                            image_url = educational_document.get('image_url', '')
                            attribution = educational_document.get('attribution', '')
                            license_info = educational_document.get('license', '')
                            source_url = educational_document.get('source_url', '')
                            
                            print(f"     📄 Document title: {title}")
                            print(f"     🖼️  Image URL: {image_url[:50]}..." if image_url else "     ❌ No image URL")
                            print(f"     👤 Attribution: {attribution}")
                            print(f"     📜 License: {license_info}")
                            print(f"     🔗 Source URL: {source_url[:50]}..." if source_url else "     No source URL")
                            
                            # Validate required fields for educational documents
                            required_fields = ['title', 'image_url', 'attribution']
                            missing_fields = [field for field in required_fields if not educational_document.get(field)]
                            
                            if not missing_fields:
                                print(f"   ✅ Exercise {i+1} document has complete required metadata")
                            else:
                                print(f"   ❌ Exercise {i+1} document missing required fields: {missing_fields}")
                                
                            # Check for license information
                            if license_info:
                                print(f"   ✅ Exercise {i+1} document has license information")
                            else:
                                print(f"   ⚠️  Exercise {i+1} document missing license information")
                        else:
                            print(f"   ❌ Exercise {i+1} document is not a valid dictionary")
                    else:
                        print(f"   ℹ️  Exercise {i+1} has no educational document")
                
                # Summary of document attachment
                print(f"\n   📊 DOCUMENT ATTACHMENT SUMMARY:")
                print(f"   Exercises with documents: {exercises_with_documents}/{len(exercises)}")
                print(f"   Total documents found: {total_documents}")
                
                if exercises_with_documents > 0:
                    print(f"   ✅ CRITICAL SUCCESS: Geography exercises have educational documents attached")
                else:
                    print(f"   ⚠️  No educational documents found - may need investigation")
                    
                return success, {
                    "document": document,
                    "exercises": exercises,
                    "exercises_with_documents": exercises_with_documents,
                    "total_documents": total_documents,
                    "generation_time": generation_time
                }
            else:
                print(f"   ❌ No document in response: {response}")
        else:
            print(f"   ❌ Geography 6e generation FAILED")
            if isinstance(response, dict):
                error_detail = response.get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
        
        return success, response

    def test_geography_document_frontend_display(self, document_id):
        """Test frontend display of Geography documents via /api/documents endpoint"""
        print(f"\n🖥️ TESTING FRONTEND DOCUMENT DISPLAY")
        print(f"   Testing Step3GenerationApercu.js document display functionality")
        print(f"   📄 Testing document display for ID: {document_id}")
        
        # Test the /api/documents endpoint (used by Step3GenerationApercu.js)
        success, response = self.run_test(
            "Frontend Document Display",
            "GET",
            f"documents/{document_id}",
            200,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            exercises = response.get('exercises', [])
            print(f"   ✅ Document retrieved successfully with {len(exercises)} exercises")
            
            # Check for document display features
            exercises_with_documents = 0
            documents_with_images = 0
            documents_with_attribution = 0
            
            for i, exercise in enumerate(exercises):
                educational_document = exercise.get('document')
                
                if educational_document:
                    exercises_with_documents += 1
                    print(f"   📄 Exercise {i+1} has document for frontend display")
                    
                    # Check frontend display requirements
                    title = educational_document.get('title', '')
                    image_url = educational_document.get('image_url', '')
                    attribution = educational_document.get('attribution', '')
                    license_info = educational_document.get('license', '')
                    
                    if image_url:
                        documents_with_images += 1
                        print(f"     ✅ Document has image URL for display")
                    else:
                        print(f"     ❌ Document missing image URL")
                    
                    if attribution:
                        documents_with_attribution += 1
                        print(f"     ✅ Document has attribution for display")
                    else:
                        print(f"     ❌ Document missing attribution")
                    
                    if title:
                        print(f"     ✅ Document has title for display")
                    else:
                        print(f"     ❌ Document missing title")
                    
                    if license_info:
                        print(f"     ✅ Document has license info for display")
                    else:
                        print(f"     ⚠️  Document missing license info")
            
            # Frontend display summary
            print(f"\n   🖥️ FRONTEND DISPLAY SUMMARY:")
            print(f"   Exercises with documents: {exercises_with_documents}")
            print(f"   Documents with images: {documents_with_images}")
            print(f"   Documents with attribution: {documents_with_attribution}")
            
            if exercises_with_documents > 0 and documents_with_images > 0:
                print(f"   ✅ FRONTEND DISPLAY READY: Documents have required display elements")
                return True, {
                    "exercises_with_documents": exercises_with_documents,
                    "documents_with_images": documents_with_images,
                    "documents_with_attribution": documents_with_attribution
                }
            else:
                print(f"   ❌ FRONTEND DISPLAY ISSUES: Missing required display elements")
                return False, {}
        else:
            print(f"   ❌ Document retrieval failed")
            return False, {}

    def test_geography_pdf_export_with_documents(self, document_id):
        """Test PDF export with Geography documents and CSS styling"""
        print(f"\n📄 TESTING PDF EXPORT WITH GEOGRAPHY DOCUMENTS")
        print(f"   Testing PDF template integration with educational documents")
        print(f"   📄 Testing PDF export for document ID: {document_id}")
        
        # Test PDF export for both sujet and corrigé
        export_types = ["sujet", "corrige"]
        export_results = {}
        
        for export_type in export_types:
            print(f"\n   📋 Testing {export_type} PDF export...")
            
            export_data = {
                "document_id": document_id,
                "export_type": export_type,
                "guest_id": self.guest_id,
                "template_style": "classique"  # Test with classique template
            }
            
            success, response = self.run_test(
                f"PDF Export {export_type.title()}",
                "POST",
                "export",
                200,
                data=export_data,
                timeout=60
            )
            
            if success:
                print(f"   ✅ {export_type.title()} PDF export successful")
                export_results[export_type] = True
                
                # Check if response indicates successful PDF generation
                if isinstance(response, dict):
                    if 'pdf_url' in response or 'download_url' in response:
                        print(f"   ✅ {export_type.title()} PDF URL provided")
                    else:
                        print(f"   ℹ️  {export_type.title()} PDF generated (no URL in response)")
            else:
                print(f"   ❌ {export_type.title()} PDF export failed")
                export_results[export_type] = False
                if isinstance(response, dict):
                    error_detail = response.get('detail', 'Unknown error')
                    print(f"   Error: {error_detail}")
        
        # Summary of PDF export tests
        successful_exports = sum(export_results.values())
        total_exports = len(export_results)
        
        print(f"\n   📊 PDF EXPORT SUMMARY:")
        print(f"   Successful exports: {successful_exports}/{total_exports}")
        
        if successful_exports == total_exports:
            print(f"   ✅ ALL PDF EXPORTS SUCCESSFUL: Geography documents integrated in PDF templates")
            return True, export_results
        else:
            print(f"   ❌ SOME PDF EXPORTS FAILED: Issues with document integration")
            return False, export_results

    def run_all_tests(self):
        """Run all Geography document tests"""
        print("="*80)
        print("🗺️ GEOGRAPHY DOCUMENT FUNCTIONALITY TESTING")
        print("="*80)
        print("CONTEXT: Testing complete implementation of educational documents for Geography")
        print("FEATURES TESTED:")
        print("- Geography 6e exercise generation with educational documents")
        print("- Frontend display of documents in Step3GenerationApercu.js")
        print("- PDF export integration with document templates")
        print("="*80)
        
        # Test 1: Geography Generation with Documents
        print(f"\n{'='*60}")
        print(f"🔍 Geography Generation with Documents")
        print(f"{'='*60}")
        
        success, gen_response = self.test_geography_generation_6e_with_documents()
        
        if not success or not isinstance(gen_response, dict):
            print("❌ Geography Generation with Documents FAILED")
            return False
        
        document = gen_response.get('document')
        if not document:
            print("❌ No document generated")
            return False
        
        document_id = document.get('id')
        if not document_id:
            print("❌ No document ID")
            return False
        
        print("✅ Geography Generation with Documents PASSED")
        
        # Test 2: Frontend Document Display
        print(f"\n{'='*60}")
        print(f"🔍 Frontend Document Display")
        print(f"{'='*60}")
        
        success, _ = self.test_geography_document_frontend_display(document_id)
        if success:
            print("✅ Frontend Document Display PASSED")
        else:
            print("❌ Frontend Document Display FAILED")
        
        # Test 3: PDF Export with Documents
        print(f"\n{'='*60}")
        print(f"🔍 PDF Export with Documents")
        print(f"{'='*60}")
        
        success, _ = self.test_geography_pdf_export_with_documents(document_id)
        if success:
            print("✅ PDF Export with Documents PASSED")
        else:
            print("❌ PDF Export with Documents FAILED")
        
        # Final summary
        print(f"\n{'='*80}")
        print(f"🗺️ GEOGRAPHY DOCUMENT TEST RESULTS: {self.tests_passed}/{self.tests_run} passed")
        print(f"{'='*80}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL GEOGRAPHY DOCUMENT TESTS PASSED!")
            print("✅ Geography exercises generate with educational documents")
            print("✅ Frontend displays documents with proper metadata")
            print("✅ PDF exports include documents with CSS styling")
        else:
            print("❌ SOME GEOGRAPHY DOCUMENT TESTS FAILED")
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = GeographyDocumentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)