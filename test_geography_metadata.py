#!/usr/bin/env python3
"""
Focused test for Geography document metadata structure verification
Based on user's review request for rapid verification of document metadata
"""

import requests
import json
import time
import uuid
from datetime import datetime

class GeographyMetadataTest:
    def __init__(self, base_url="https://math-exercise-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.guest_id = f"test-geo-metadata-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}"

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
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

    def test_geography_document_metadata_structure(self):
        """SPECIFIC TEST: Geography document metadata structure verification"""
        print("\n🗺️ TESTING GEOGRAPHY DOCUMENT METADATA STRUCTURE")
        print("="*60)
        print("CONTEXT: Vérification rapide des métadonnées de documents géographiques")
        print("PROBLÈME IDENTIFIÉ: Les logs montrent documents trouvés mais métadonnées vides")
        print("TEST UNIQUE: Génération Géographie 6e - 'Découvrir le(s) lieu(x) où j'habite'")
        print("FOCUS: Structure exacte des données de document dans exercise.document")
        
        test_data = {
            "matiere": "Géographie",
            "niveau": "6e",
            "chapitre": "Découvrir le(s) lieu(x) où j'habite",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 1,  # 1 exercice seulement pour simplifier
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"   🔍 Generating Geography exercise with data: {test_data}")
        
        start_time = time.time()
        success, response = self.run_test(
            "Geography Document Metadata Test",
            "POST",
            "generate",
            200,
            data=test_data,
            timeout=60
        )
        generation_time = time.time() - start_time
        
        metadata_issues = []
        document_found = False
        
        if success and isinstance(response, dict):
            document = response.get('document')
            if document:
                exercises = document.get('exercises', [])
                print(f"   ✅ Document generated with {len(exercises)} exercises in {generation_time:.2f}s")
                
                if exercises:
                    exercise = exercises[0]
                    print(f"\n   🔍 ANALYZING EXERCISE DOCUMENT STRUCTURE:")
                    
                    # Check if exercise has document field
                    exercise_document = exercise.get('document')
                    if exercise_document:
                        document_found = True
                        print(f"   ✅ exercise.document field present")
                        print(f"   📋 Document structure: {type(exercise_document)}")
                        
                        if isinstance(exercise_document, dict):
                            print(f"   📋 Document keys: {list(exercise_document.keys())}")
                            
                            # Check for expected metadata fields
                            expected_fields = ['titre', 'url_fichier_direct', 'licence']
                            for field in expected_fields:
                                if field in exercise_document:
                                    value = exercise_document[field]
                                    if value and str(value).strip():
                                        print(f"   ✅ {field}: '{str(value)[:100]}...' (populated)")
                                    else:
                                        print(f"   ❌ {field}: empty or None")
                                        metadata_issues.append(f"{field} is empty")
                                else:
                                    print(f"   ❌ {field}: missing from document")
                                    metadata_issues.append(f"{field} is missing")
                            
                            # Check for additional metadata
                            additional_fields = ['description', 'source', 'type_document', 'niveau_scolaire', 'title', 'image_url', 'attribution', 'license', 'source_url']
                            for field in additional_fields:
                                if field in exercise_document:
                                    value = exercise_document[field]
                                    print(f"   ℹ️  {field}: '{str(value)[:50]}...'")
                            
                            # Full document structure for debugging
                            print(f"\n   🔍 COMPLETE DOCUMENT STRUCTURE:")
                            for key, value in exercise_document.items():
                                value_preview = str(value)[:100] if value else "None/Empty"
                                print(f"     {key}: {value_preview}")
                                
                        else:
                            print(f"   ❌ Document is not a dictionary: {exercise_document}")
                            metadata_issues.append("Document is not a dictionary structure")
                    else:
                        print(f"   ❌ exercise.document field is missing or None")
                        metadata_issues.append("exercise.document field missing")
                    
                    # Check exercise content for geography context
                    enonce = exercise.get('enonce', '')
                    if enonce:
                        print(f"\n   📝 Exercise content preview: {enonce[:200]}...")
                        geo_terms = ['lieu', 'habite', 'territoire', 'espace', 'géographique', 'carte']
                        has_geo_content = any(term in enonce.lower() for term in geo_terms)
                        if has_geo_content:
                            print(f"   ✅ Exercise contains appropriate geography content")
                        else:
                            print(f"   ⚠️  Exercise may lack specific geography content")
                else:
                    print(f"   ❌ No exercises in generated document")
                    metadata_issues.append("No exercises generated")
            else:
                print(f"   ❌ No document in response")
                metadata_issues.append("No document in response")
        else:
            print(f"   ❌ Geography generation failed")
            if isinstance(response, dict):
                error_detail = response.get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
                metadata_issues.append(f"Generation failed: {error_detail}")
        
        # Summary of findings
        print(f"\n   📊 GEOGRAPHY DOCUMENT METADATA ANALYSIS:")
        print(f"   Document attached: {'✅ YES' if document_found else '❌ NO'}")
        print(f"   Metadata issues found: {len(metadata_issues)}")
        
        if metadata_issues:
            print(f"   🚨 ISSUES IDENTIFIED:")
            for issue in metadata_issues:
                print(f"     - {issue}")
        else:
            print(f"   ✅ All expected metadata fields present and populated")
        
        # Determine success criteria
        success_criteria = {
            "document_attached": document_found,
            "metadata_complete": len(metadata_issues) == 0,
            "generation_successful": success
        }
        
        all_criteria_met = all(success_criteria.values())
        
        print(f"\n   🎯 SUCCESS CRITERIA:")
        for criterion, met in success_criteria.items():
            status = "✅" if met else "❌"
            print(f"     {status} {criterion.replace('_', ' ').title()}")
        
        if all_criteria_met:
            print(f"   🎉 GEOGRAPHY DOCUMENT METADATA TEST PASSED")
        else:
            print(f"   🚨 GEOGRAPHY DOCUMENT METADATA TEST FAILED")
            print(f"   🔍 DIAGNOSTIC: Compare with document_search logs to identify serialization issue")
        
        return all_criteria_met, {
            "document_found": document_found,
            "metadata_issues": metadata_issues,
            "success_criteria": success_criteria,
            "generation_time": generation_time
        }

if __name__ == "__main__":
    print("🗺️ GEOGRAPHY DOCUMENT METADATA VERIFICATION")
    print("="*60)
    print("FOCUS: Rapid verification of document metadata structure")
    print("ISSUE: Logs show documents found but metadata appears empty")
    print("="*60)
    
    tester = GeographyMetadataTest()
    success, results = tester.test_geography_document_metadata_structure()
    
    print(f"\n🏁 TEST COMPLETED")
    print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if not success:
        print(f"\n🔍 NEXT STEPS:")
        print(f"1. Check backend logs for document_search activity")
        print(f"2. Verify document attachment in generate_exercises_with_ai()")
        print(f"3. Check serialization in /api/documents endpoint")
        print(f"4. Compare with document_search logs that show correct data")