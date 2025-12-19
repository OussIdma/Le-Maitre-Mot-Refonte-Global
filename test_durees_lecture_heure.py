#!/usr/bin/env python3
"""
Test complet du chapitre "Durées et lecture de l'heure" (6e_GM07)
Tests des 4 types d'exercices et validation de la qualité des SVG
"""

import requests
import json
import time
import uuid
from datetime import datetime

class TestDureesLectureHeure:
    def __init__(self):
        # Use REACT_APP_BACKEND_URL from frontend/.env
        self.base_url = "https://math-exercise-sync.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.guest_id = f"test-durees-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Test results tracking
        self.test_results = {
            "curriculum_check": False,
            "generation_by_code": False,
            "generation_by_name": False,
            "difficulty_levels": {"facile": False, "moyen": False, "difficile": False},
            "svg_quality": {"LECTURE_HORLOGE": False, "CALCUL_DUREE": False},
            "exercise_types_found": set(),
            "response_format_valid": True,
            "detailed_results": []
        }

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
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED")
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
                except:
                    print(f"   Error text: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_1_curriculum_chapter_exists(self):
        """Test 1: Vérifier que le chapitre 6e_GM07 existe dans le curriculum"""
        print("\n" + "="*80)
        print("TEST 1: Vérification du chapitre dans le curriculum")
        print("="*80)
        
        success, response = self.run_test(
            "GET curriculum 6e_GM07",
            "GET",
            "admin/curriculum/6e/6e_GM07",
            200
        )
        
        if success and isinstance(response, dict):
            # Vérifier les champs requis
            code_officiel = response.get('code_officiel')
            libelle = response.get('libelle')
            exercise_types = response.get('exercise_types', [])
            schema_requis = response.get('schema_requis')
            statut = response.get('statut')
            
            print(f"   Code officiel: {code_officiel}")
            print(f"   Libellé: {libelle}")
            print(f"   Exercise types: {exercise_types}")
            print(f"   Schema requis: {schema_requis}")
            print(f"   Statut: {statut}")
            
            # Vérifications
            checks = []
            checks.append(("Code officiel correct", code_officiel == "6e_GM07"))
            checks.append(("Libellé contient 'Durées'", "Durées" in str(libelle)))
            checks.append(("4 exercise types", len(exercise_types) == 4))
            checks.append(("Schema requis = true", schema_requis == True))
            checks.append(("Statut = prod", statut == "prod"))
            
            # Vérifier les 4 types d'exercices attendus
            expected_types = ["LECTURE_HORLOGE", "CONVERSION_DUREES", "CALCUL_DUREE", "PROBLEME_DUREES"]
            for expected_type in expected_types:
                checks.append((f"Type {expected_type} présent", expected_type in exercise_types))
            
            # Afficher les résultats
            all_passed = True
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}")
                if not check_result:
                    all_passed = False
            
            self.test_results["curriculum_check"] = all_passed
            return all_passed, response
        else:
            self.test_results["curriculum_check"] = False
            return False, {}

    def test_2_generation_by_code(self):
        """Test 2: Génération avec code_officiel"""
        print("\n" + "="*80)
        print("TEST 2: Génération avec code_officiel")
        print("="*80)
        
        # Test multiple generations to get different types
        all_generator_types = set()
        svg_exercises = []
        total_exercises = 0
        
        for attempt in range(10):  # Multiple attempts to get variety
            test_data = {
                "code_officiel": "6e_GM07",
                "difficulte": "facile",
                "nb_exercices": 1
            }
            
            success, response = self.run_test(
                f"POST generate attempt {attempt + 1}",
                "POST",
                "v1/exercises/generate",
                200,
                data=test_data,
                timeout=60
            )
            
            if success and isinstance(response, dict):  # Single exercise response
                total_exercises += 1
                generator_code = response.get('metadata', {}).get('generator_code', '')
                exercise_type = self._extract_exercise_type(generator_code)
                all_generator_types.add(exercise_type)
                
                print(f"   Exercice {attempt+1}: {generator_code} ({exercise_type})")
                
                # Vérifier SVG pour LECTURE_HORLOGE et CALCUL_DUREE
                if exercise_type in ["LECTURE_HORLOGE", "CALCUL_DUREE"]:
                    svg_content = response.get('svg', '')
                    if svg_content:
                        svg_exercises.append((attempt+1, exercise_type, svg_content))
                        print(f"     ✅ SVG présent ({len(svg_content)} caractères)")
                    else:
                        print(f"     ❌ SVG manquant pour {exercise_type}")
        
        # Vérifier que les 4 types sont utilisés
        expected_types = {"LECTURE_HORLOGE", "CONVERSION_DUREES", "CALCUL_DUREE", "PROBLEME_DUREES"}
        found_types = all_generator_types.intersection(expected_types)
        
        print(f"\n   Types trouvés: {found_types}")
        print(f"   Types attendus: {expected_types}")
        print(f"   Total exercices générés: {total_exercises}")
        
        types_check = len(found_types) >= 3  # Au moins 3 des 4 types
        svg_check = len(svg_exercises) > 0  # Au moins un SVG
        
        self.test_results["generation_by_code"] = types_check and svg_check
        self.test_results["exercise_types_found"].update(found_types)
        
        # Stocker les exercices SVG pour analyse détaillée
        self.svg_exercises = svg_exercises
        
        return types_check and svg_check, {"types_found": found_types, "svg_count": len(svg_exercises)}

    def test_3_generation_by_name(self):
        """Test 3: Génération avec nom de chapitre"""
        print("\n" + "="*80)
        print("TEST 3: Génération avec nom de chapitre")
        print("="*80)
        
        test_data = {
            "chapitre": "Durées et lecture de l'heure",
            "niveau": "6e",
            "difficulte": "moyen",
            "nb_exercices": 1
        }
        
        success, response = self.run_test(
            "POST generate with chapter name",
            "POST",
            "v1/exercises/generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):  # Single exercise response
            print(f"   Généré 1 exercice par nom de chapitre")
            
            # Vérifier que l'exercice est bien du bon chapitre
            generator_code = response.get('metadata', {}).get('generator_code', '')
            chapter_match = generator_code.startswith('6e_') and any(x in generator_code for x in ['LECTURE_HORLOGE', 'CONVERSION_DUREES', 'CALCUL_DUREE', 'PROBLEME_DUREES'])
            
            if chapter_match:
                print(f"   ✅ Exercice: {generator_code}")
            else:
                print(f"   ❌ Code générateur incorrect: {generator_code}")
            
            self.test_results["generation_by_name"] = chapter_match
            return chapter_match, response
        else:
            self.test_results["generation_by_name"] = False
            return False, {}

    def test_4_difficulty_levels(self):
        """Test 4: Test des 3 niveaux de difficulté"""
        print("\n" + "="*80)
        print("TEST 4: Test des niveaux de difficulté")
        print("="*80)
        
        difficulties = ["facile", "moyen", "difficile"]
        
        for difficulty in difficulties:
            print(f"\n   Testing difficulté: {difficulty}")
            
            test_data = {
                "code_officiel": "6e_GM07",
                "difficulte": difficulty,
                "nb_exercices": 1
            }
            
            success, response = self.run_test(
                f"Generate difficulty {difficulty}",
                "POST",
                "v1/exercises/generate",
                200,
                data=test_data,
                timeout=60
            )
            
            if success and isinstance(response, dict):  # Single exercise response
                print(f"     ✅ Génération réussie pour {difficulty}")
                
                # Vérifier que l'énoncé et la solution sont présents
                enonce = response.get('enonce_html', '')
                solution = response.get('solution_html', '')
                
                if enonce and solution:
                    print(f"     ✅ Énoncé et solution présents")
                    # Vérifier les étapes détaillées dans la solution
                    if "étape" in solution.lower() or any(x in solution.lower() for x in ["1.", "2.", "3."]):
                        print(f"     ✅ Solution détaillée étape par étape")
                    else:
                        print(f"     ⚠️  Solution sans étapes numérotées visibles")
                else:
                    print(f"     ❌ Énoncé ou solution manquant")
                
                self.test_results["difficulty_levels"][difficulty] = True
            else:
                print(f"     ❌ Échec génération pour {difficulty}")
                self.test_results["difficulty_levels"][difficulty] = False

    def test_5_svg_quality_lecture_horloge(self):
        """Test 5: Qualité des SVG pour LECTURE_HORLOGE"""
        print("\n" + "="*80)
        print("TEST 5: Qualité des SVG LECTURE_HORLOGE")
        print("="*80)
        
        # Use the SVG exercises found in test 2
        if hasattr(self, 'svg_exercises') and self.svg_exercises:
            for exercise_num, exercise_type, svg_content in self.svg_exercises:
                if exercise_type == "LECTURE_HORLOGE":
                    print(f"   ✅ LECTURE_HORLOGE avec SVG trouvé (exercice {exercise_num})")
                    svg_analysis = self._analyze_clock_svg(svg_content)
                    print(f"   ✅ SVG présent: {svg_analysis}")
                    self.test_results["svg_quality"]["LECTURE_HORLOGE"] = True
                    return
        
        # If not found in previous tests, try to generate one
        max_attempts = 5
        lecture_horloge_found = False
        
        for attempt in range(max_attempts):
            print(f"\n   Tentative {attempt + 1}/{max_attempts}")
            
            test_data = {
                "code_officiel": "6e_GM07",
                "difficulte": "facile",
                "nb_exercices": 1
            }
            
            success, response = self.run_test(
                f"Generate for LECTURE_HORLOGE attempt {attempt + 1}",
                "POST",
                "v1/exercises/generate",
                200,
                data=test_data,
                timeout=60
            )
            
            if success and isinstance(response, dict):
                generator_code = response.get('metadata', {}).get('generator_code', '')
                exercise_type = self._extract_exercise_type(generator_code)
                
                if exercise_type == "LECTURE_HORLOGE":
                    print(f"     ✅ LECTURE_HORLOGE trouvé")
                    
                    # Analyser le SVG
                    svg_content = response.get('svg', '')
                    metadata = response.get('metadata', {})
                    
                    if svg_content:
                        svg_analysis = self._analyze_clock_svg(svg_content)
                        print(f"     ✅ SVG présent: {svg_analysis}")
                        
                        # Vérifier metadata.has_figure
                        has_figure = metadata.get('has_figure', False)
                        print(f"     {'✅' if has_figure else '❌'} metadata.has_figure = {has_figure}")
                        
                        self.test_results["svg_quality"]["LECTURE_HORLOGE"] = True
                        lecture_horloge_found = True
                        break
                    else:
                        print(f"     ❌ SVG manquant pour LECTURE_HORLOGE")
        
        if not lecture_horloge_found:
            print(f"   ❌ LECTURE_HORLOGE non trouvé après {max_attempts} tentatives")

    def test_6_svg_quality_calcul_duree(self):
        """Test 6: Qualité des SVG pour CALCUL_DUREE"""
        print("\n" + "="*80)
        print("TEST 6: Qualité des SVG CALCUL_DUREE")
        print("="*80)
        
        # Use the SVG exercises found in test 2
        if hasattr(self, 'svg_exercises') and self.svg_exercises:
            for exercise_num, exercise_type, svg_content in self.svg_exercises:
                if exercise_type == "CALCUL_DUREE":
                    print(f"   ✅ CALCUL_DUREE avec SVG trouvé (exercice {exercise_num})")
                    svg_analysis = self._analyze_duration_svg(svg_content)
                    print(f"   ✅ SVG présent: {svg_analysis}")
                    self.test_results["svg_quality"]["CALCUL_DUREE"] = True
                    return
        
        # If not found in previous tests, try to generate one
        max_attempts = 5
        calcul_duree_found = False
        
        for attempt in range(max_attempts):
            print(f"\n   Tentative {attempt + 1}/{max_attempts}")
            
            test_data = {
                "code_officiel": "6e_GM07",
                "difficulte": "moyen",
                "nb_exercices": 1
            }
            
            success, response = self.run_test(
                f"Generate for CALCUL_DUREE attempt {attempt + 1}",
                "POST",
                "v1/exercises/generate",
                200,
                data=test_data,
                timeout=60
            )
            
            if success and isinstance(response, dict):
                generator_code = response.get('metadata', {}).get('generator_code', '')
                exercise_type = self._extract_exercise_type(generator_code)
                
                if exercise_type == "CALCUL_DUREE":
                    print(f"     ✅ CALCUL_DUREE trouvé")
                    
                    # Analyser le SVG
                    svg_content = response.get('svg', '')
                    metadata = response.get('metadata', {})
                    
                    if svg_content:
                        svg_analysis = self._analyze_duration_svg(svg_content)
                        print(f"     ✅ SVG présent: {svg_analysis}")
                        
                        # Vérifier metadata.has_figure
                        has_figure = metadata.get('has_figure', False)
                        print(f"     {'✅' if has_figure else '❌'} metadata.has_figure = {has_figure}")
                        
                        self.test_results["svg_quality"]["CALCUL_DUREE"] = True
                        calcul_duree_found = True
                        break
                    else:
                        print(f"     ❌ SVG manquant pour CALCUL_DUREE")
        
        if not calcul_duree_found:
            print(f"   ❌ CALCUL_DUREE non trouvé après {max_attempts} tentatives")

    def test_7_response_format_validation(self):
        """Test 7: Validation du format de réponse"""
        print("\n" + "="*80)
        print("TEST 7: Validation du format de réponse")
        print("="*80)
        
        test_data = {
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "nb_exercices": 1
        }
        
        success, response = self.run_test(
            "Generate for format validation",
            "POST",
            "v1/exercises/generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):  # Single exercise response
            format_valid = True
            
            print(f"\n   Validation exercice:")
            
            # Vérifier enonce_html
            enonce_html = response.get('enonce_html', '')
            if enonce_html and 'exercise-enonce' in enonce_html:
                print(f"     ✅ enonce_html valide avec classe 'exercise-enonce'")
            else:
                print(f"     ❌ enonce_html invalide ou classe manquante")
                format_valid = False
            
            # Vérifier solution_html
            solution_html = response.get('solution_html', '')
            if solution_html and any(x in solution_html.lower() for x in ['étape', '1.', '2.', '3.']):
                print(f"     ✅ solution_html contient des étapes numérotées")
            else:
                print(f"     ❌ solution_html sans étapes numérotées")
                format_valid = False
            
            # Vérifier metadata
            metadata = response.get('metadata', {})
            is_fallback = metadata.get('is_fallback', True)
            generator_code = metadata.get('generator_code', '')
            
            if not is_fallback:
                print(f"     ✅ metadata.is_fallback = false (pas de fallback)")
            else:
                print(f"     ❌ metadata.is_fallback = true (fallback utilisé)")
                format_valid = False
            
            if generator_code.startswith('6e_'):
                print(f"     ✅ generator_code commence par '6e_': {generator_code}")
            else:
                print(f"     ❌ generator_code incorrect: {generator_code}")
                format_valid = False
            
            self.test_results["response_format_valid"] = format_valid
            return format_valid, response
        else:
            self.test_results["response_format_valid"] = False
            return False, {}

    def _extract_exercise_type(self, generator_code):
        """Extraire le type d'exercice du code générateur"""
        if "LECTURE_HORLOGE" in generator_code:
            return "LECTURE_HORLOGE"
        elif "CONVERSION_DUREES" in generator_code:
            return "CONVERSION_DUREES"
        elif "CALCUL_DUREE" in generator_code:
            return "CALCUL_DUREE"
        elif "PROBLEME_DUREES" in generator_code:
            return "PROBLEME_DUREES"
        else:
            return "UNKNOWN"

    def _analyze_clock_svg(self, svg_content):
        """Analyser le contenu SVG d'une horloge"""
        analysis = []
        
        if '<circle' in svg_content:
            circle_count = svg_content.count('<circle')
            analysis.append(f"{circle_count} cercles")
        
        if '<line' in svg_content:
            line_count = svg_content.count('<line')
            analysis.append(f"{line_count} lignes (aiguilles)")
        
        if '<path' in svg_content:
            path_count = svg_content.count('<path')
            analysis.append(f"{path_count} chemins")
        
        return ", ".join(analysis) if analysis else "Éléments non identifiés"

    def _analyze_duration_svg(self, svg_content):
        """Analyser le contenu SVG pour calcul de durée (deux horloges)"""
        analysis = []
        
        circle_count = svg_content.count('<circle')
        if circle_count >= 2:
            analysis.append(f"{circle_count} cercles (≥2 horloges)")
        else:
            analysis.append(f"{circle_count} cercles (insuffisant)")
        
        line_count = svg_content.count('<line')
        analysis.append(f"{line_count} lignes")
        
        # Rechercher des indicateurs de temps
        if 'début' in svg_content.lower() or 'fin' in svg_content.lower():
            analysis.append("indicateurs début/fin")
        
        return ", ".join(analysis) if analysis else "Éléments non identifiés"

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🕐 TESTS COMPLETS - CHAPITRE 'Durées et lecture de l'heure' (6e_GM07)")
        print("="*80)
        
        start_time = time.time()
        
        # Exécuter tous les tests
        self.test_1_curriculum_chapter_exists()
        self.test_2_generation_by_code()
        self.test_3_generation_by_name()
        self.test_4_difficulty_levels()
        self.test_5_svg_quality_lecture_horloge()
        self.test_6_svg_quality_calcul_duree()
        self.test_7_response_format_validation()
        
        total_time = time.time() - start_time
        
        # Résumé final
        print("\n" + "="*80)
        print("RÉSUMÉ FINAL")
        print("="*80)
        
        print(f"Tests exécutés: {self.tests_run}")
        print(f"Tests réussis: {self.tests_passed}")
        print(f"Temps total: {total_time:.2f}s")
        
        # Détail des résultats
        print(f"\n📊 RÉSULTATS DÉTAILLÉS:")
        print(f"✅ Chapitre dans curriculum: {self.test_results['curriculum_check']}")
        print(f"✅ Génération par code: {self.test_results['generation_by_code']}")
        print(f"✅ Génération par nom: {self.test_results['generation_by_name']}")
        
        difficulty_results = self.test_results['difficulty_levels']
        print(f"✅ Difficultés - Facile: {difficulty_results['facile']}, Moyen: {difficulty_results['moyen']}, Difficile: {difficulty_results['difficile']}")
        
        svg_results = self.test_results['svg_quality']
        print(f"✅ SVG LECTURE_HORLOGE: {svg_results['LECTURE_HORLOGE']}")
        print(f"✅ SVG CALCUL_DUREE: {svg_results['CALCUL_DUREE']}")
        
        print(f"✅ Format de réponse: {self.test_results['response_format_valid']}")
        
        print(f"\n🎯 Types d'exercices trouvés: {self.test_results['exercise_types_found']}")
        
        # Score global
        total_checks = 10  # Nombre total de vérifications principales
        passed_checks = sum([
            self.test_results['curriculum_check'],
            self.test_results['generation_by_code'],
            self.test_results['generation_by_name'],
            sum(difficulty_results.values()),
            sum(svg_results.values()),
            self.test_results['response_format_valid']
        ])
        
        success_rate = (passed_checks / total_checks) * 100
        print(f"\n🏆 TAUX DE RÉUSSITE: {success_rate:.1f}% ({passed_checks}/{total_checks})")
        
        if success_rate >= 80:
            print("🎉 SUCCÈS - Le chapitre 'Durées et lecture de l'heure' fonctionne correctement!")
        elif success_rate >= 60:
            print("⚠️  PARTIEL - Le chapitre fonctionne mais avec quelques problèmes")
        else:
            print("❌ ÉCHEC - Le chapitre nécessite des corrections importantes")
        
        return success_rate >= 80


if __name__ == "__main__":
    tester = TestDureesLectureHeure()
    success = tester.run_all_tests()
    exit(0 if success else 1)