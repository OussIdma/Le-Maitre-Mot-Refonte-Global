#!/usr/bin/env python3
"""
Test spécifique pour vérifier la correction du bug geometric_schema
Bug: Le code divisait "rayon" en "ra" et "yon" pour les cercles
Fix: Ajout d'une logique spéciale pour traiter correctement le rayon des cercles
"""

import requests
import json
import sys
from datetime import datetime

class GeometricSchemaFixTester:
    def __init__(self):
        self.base_url = "https://math-exercise-sync.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_passed = 0
        self.tests_total = 0
        
    def test_circle_radius_fix(self):
        """Test que le rayon des cercles n'est plus divisé en 'ra' et 'yon'"""
        print("🔍 TEST: Correction du bug geometric_schema pour les cercles")
        print("="*60)
        
        test_scenarios = [
            {
                "name": "Aires - Cercles (6e)",
                "data": {
                    "matiere": "Mathématiques",
                    "niveau": "6e",
                    "chapitre": "Aires",
                    "type_doc": "exercices",
                    "difficulte": "facile",
                    "nb_exercices": 5,
                    "versions": ["A"],
                    "guest_id": f"test_circle_fix_{datetime.now().strftime('%H%M%S')}"
                }
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            
            response = requests.post(f"{self.api_url}/generate", json=scenario['data'], timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                document = data.get('document', {})
                exercises = document.get('exercises', [])
                
                print(f"   ✅ Generated {len(exercises)} exercises")
                
                circle_exercises = 0
                fixed_exercises = 0
                coherent_exercises = 0
                
                for i, exercise in enumerate(exercises):
                    exercise_num = i + 1
                    enonce = exercise.get('enonce', '').lower()
                    
                    # Check if this is a circle exercise
                    if any(term in enonce for term in ['cercle', 'rayon', 'diamètre']):
                        circle_exercises += 1
                        print(f"\n   📋 Circle Exercise {exercise_num}:")
                        print(f"      Enonce: {exercise.get('enonce', '')[:100]}...")
                        
                        # Check spec_mathematique
                        spec_math = exercise.get('spec_mathematique', {})
                        figure_geo = spec_math.get('figure_geometrique', {}) if spec_math else {}
                        
                        # Check geometric_schema
                        geo_schema = exercise.get('geometric_schema', {})
                        
                        # Verify the fix
                        segments = geo_schema.get('segments', [])
                        rayon_segment_found = False
                        broken_rayon_found = False
                        
                        for segment in segments:
                            if isinstance(segment, list) and len(segment) >= 2:
                                if segment[0] == 'rayon':
                                    rayon_segment_found = True
                                    print(f"      ✅ Correct rayon segment: {segment}")
                                elif segment[0] == 'ra' and len(segment) > 2 and segment[1] == 'yon':
                                    broken_rayon_found = True
                                    print(f"      ❌ Broken rayon segment found: {segment}")
                        
                        # Check spec_mathematique coherence
                        longueurs_connues = figure_geo.get('longueurs_connues', {})
                        rayon_in_spec = 'rayon' in longueurs_connues
                        
                        if rayon_in_spec:
                            rayon_value = longueurs_connues['rayon']
                            print(f"      ✅ Rayon in spec_mathematique: {rayon_value}")
                        else:
                            print(f"      ❌ Rayon missing from spec_mathematique")
                        
                        # Determine if this exercise is fixed and coherent
                        is_fixed = rayon_segment_found and not broken_rayon_found
                        is_coherent = is_fixed and rayon_in_spec
                        
                        if is_fixed:
                            fixed_exercises += 1
                            print(f"      ✅ Exercise {exercise_num}: BUG FIX APPLIED")
                        else:
                            print(f"      ❌ Exercise {exercise_num}: BUG STILL PRESENT")
                            
                        if is_coherent:
                            coherent_exercises += 1
                            print(f"      ✅ Exercise {exercise_num}: FULLY COHERENT")
                        else:
                            print(f"      ⚠️  Exercise {exercise_num}: NEEDS ATTENTION")
                
                # Summary for this scenario
                print(f"\n   📊 SUMMARY for {scenario['name']}:")
                print(f"      Circle exercises found: {circle_exercises}")
                print(f"      Bug fix applied: {fixed_exercises}/{circle_exercises}")
                print(f"      Fully coherent: {coherent_exercises}/{circle_exercises}")
                
                fix_rate = (fixed_exercises / circle_exercises * 100) if circle_exercises > 0 else 0
                coherence_rate = (coherent_exercises / circle_exercises * 100) if circle_exercises > 0 else 0
                
                print(f"      Fix rate: {fix_rate:.1f}%")
                print(f"      Coherence rate: {coherence_rate:.1f}%")
                
                # Test success criteria
                self.tests_total += 2
                if fix_rate == 100:
                    self.tests_passed += 1
                    print(f"      ✅ BUG FIX TEST: PASSED")
                else:
                    print(f"      ❌ BUG FIX TEST: FAILED")
                    
                if coherence_rate >= 80:
                    self.tests_passed += 1
                    print(f"      ✅ COHERENCE TEST: PASSED")
                else:
                    print(f"      ❌ COHERENCE TEST: FAILED")
                    
            else:
                print(f"   ❌ Generation failed: {response.status_code}")
                print(f"   Error: {response.text}")
    
    def test_rectangle_points_fix(self):
        """Test que les rectangles ont bien 4 points définis"""
        print("\n🔍 TEST: Vérification des points des rectangles")
        print("="*50)
        
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "5e",
            "chapitre": "Aires et périmètres",
            "type_doc": "exercices",
            "difficulte": "facile",
            "nb_exercices": 5,
            "versions": ["A"],
            "guest_id": f"test_rectangle_fix_{datetime.now().strftime('%H%M%S')}"
        }
        
        response = requests.post(f"{self.api_url}/generate", json=test_data, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            exercises = data.get('document', {}).get('exercises', [])
            
            rectangle_exercises = 0
            correct_point_count = 0
            
            for i, exercise in enumerate(exercises):
                enonce = exercise.get('enonce', '').lower()
                
                if any(term in enonce for term in ['rectangle', 'carré']):
                    rectangle_exercises += 1
                    print(f"\n   📋 Rectangle Exercise {i+1}:")
                    print(f"      Enonce: {exercise.get('enonce', '')[:100]}...")
                    
                    spec_math = exercise.get('spec_mathematique', {})
                    figure_geo = spec_math.get('figure_geometrique', {}) if spec_math else {}
                    points = figure_geo.get('points', [])
                    
                    print(f"      Points: {points} (count: {len(points)})")
                    
                    if len(points) == 4:
                        correct_point_count += 1
                        print(f"      ✅ Correct: 4 points defined")
                    else:
                        print(f"      ❌ Incorrect: {len(points)} points instead of 4")
            
            print(f"\n   📊 RECTANGLE POINTS SUMMARY:")
            print(f"      Rectangle exercises: {rectangle_exercises}")
            print(f"      Correct point count: {correct_point_count}/{rectangle_exercises}")
            
            if rectangle_exercises > 0:
                success_rate = (correct_point_count / rectangle_exercises * 100)
                print(f"      Success rate: {success_rate:.1f}%")
                
                self.tests_total += 1
                if success_rate >= 80:
                    self.tests_passed += 1
                    print(f"      ✅ RECTANGLE POINTS TEST: PASSED")
                else:
                    print(f"      ❌ RECTANGLE POINTS TEST: FAILED")
        else:
            print(f"   ❌ Generation failed: {response.status_code}")
    
    def test_trigonometry_phantom_points(self):
        """Test pour identifier le point fantôme 'L' en trigonométrie"""
        print("\n🔍 TEST: Identification du point fantôme en trigonométrie")
        print("="*55)
        
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "3e",
            "chapitre": "Trigonométrie",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 3,
            "versions": ["A"],
            "guest_id": f"test_trigono_fix_{datetime.now().strftime('%H%M%S')}"
        }
        
        response = requests.post(f"{self.api_url}/generate", json=test_data, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            exercises = data.get('document', {}).get('exercises', [])
            
            phantom_points_found = 0
            
            for i, exercise in enumerate(exercises):
                enonce = exercise.get('enonce', '')
                
                print(f"\n   📋 Trigonometry Exercise {i+1}:")
                print(f"      Enonce: {enonce[:150]}...")
                
                # Extract points from enonce
                import re
                enonce_points = set(re.findall(r'\b[A-Z]\b', enonce))
                
                # Get points from figure
                spec_math = exercise.get('spec_mathematique', {})
                figure_geo = spec_math.get('figure_geometrique', {}) if spec_math else {}
                figure_points = set(figure_geo.get('points', []))
                
                print(f"      Points in enonce: {sorted(enonce_points)}")
                print(f"      Points in figure: {sorted(figure_points)}")
                
                # Check for phantom points
                phantom_points = enonce_points - figure_points
                if phantom_points:
                    phantom_points_found += len(phantom_points)
                    print(f"      ❌ Phantom points detected: {sorted(phantom_points)}")
                    if 'L' in phantom_points:
                        print(f"      🎯 SPECIFIC ISSUE: Point 'L' phantom detected!")
                else:
                    print(f"      ✅ No phantom points")
            
            print(f"\n   📊 TRIGONOMETRY PHANTOM POINTS SUMMARY:")
            print(f"      Total phantom points found: {phantom_points_found}")
            
            self.tests_total += 1
            if phantom_points_found == 0:
                self.tests_passed += 1
                print(f"      ✅ PHANTOM POINTS TEST: PASSED")
            else:
                print(f"      ❌ PHANTOM POINTS TEST: FAILED")
        else:
            print(f"   ❌ Generation failed: {response.status_code}")
    
    def run_all_tests(self):
        """Run all geometric schema fix tests"""
        print("🎯 GEOMETRIC SCHEMA BUG FIX VALIDATION")
        print("="*70)
        print("CONTEXT: Re-test complet de la cohérence géométrique après correction du bug")
        print("BUG FIXED: Le code divisait 'rayon' en 'ra' et 'yon' pour les cercles")
        print("EXPECTED: geometric_schema.segments contient ['rayon', {...}] au lieu de ['ra', 'yon', {...}]")
        
        # Run all tests
        self.test_circle_radius_fix()
        self.test_rectangle_points_fix()
        self.test_trigonometry_phantom_points()
        
        # Final summary
        print(f"\n🎯 FINAL SUMMARY:")
        print(f"="*50)
        print(f"Tests passed: {self.tests_passed}/{self.tests_total}")
        success_rate = (self.tests_passed / self.tests_total * 100) if self.tests_total > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate >= 85:
            print(f"\n🎉 GEOMETRIC SCHEMA BUG FIX: SUCCESS")
            print(f"✅ Bug fix applied correctly")
            print(f"✅ Coherence rate meets expectations")
            return True
        else:
            print(f"\n⚠️  GEOMETRIC SCHEMA BUG FIX: NEEDS ATTENTION")
            print(f"❌ Some issues still present")
            return False

if __name__ == "__main__":
    tester = GeometricSchemaFixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)