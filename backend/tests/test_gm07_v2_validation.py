#!/usr/bin/env python3
"""
Test GM07 v2 Validation - Validation des correctifs GM07 v2

Tests pour valider les deux bugs corrigés dans GM07:
1. HTML pur: Remplacement de Markdown (**texte**) et LaTeX ($...$) par HTML (<strong>, ×)
2. Pas de doublons: Seeds différents retournent des exercices différents grâce au hash de Knuth

Backend URL: https://math-exercise-sync.preview.emergentagent.com
"""

import requests
import json
import time
import hashlib
from typing import List, Dict, Any

class GM07V2Validator:
    def __init__(self, base_url="https://math-exercise-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
    def run_test(self, name: str, test_func) -> bool:
        """Run a single test and track results"""
        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print("=" * 60)
        
        try:
            success = test_func()
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED: {name}")
            else:
                print(f"❌ FAILED: {name}")
            return success
        except Exception as e:
            print(f"❌ ERROR in {name}: {str(e)}")
            return False
    
    def make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to generate exercise"""
        url = f"{self.api_url}/v1/exercises/generate"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"API returned {response.status_code}: {response.text}")
        
        return response.json()
    
    def test_html_pur_pas_de_markdown(self) -> bool:
        """Test 1: HTML pur - Pas de Markdown"""
        print("Vérification: solution_html ne contient PAS ** et contient <strong>")
        
        payload = {
            "code_officiel": "6e_GM07",
            "difficulte": "facile"
        }
        
        response = self.make_request(payload)
        solution_html = response.get('solution_html', '')
        
        # Vérifications
        has_markdown = '**' in solution_html
        has_strong_tag = '<strong>' in solution_html
        has_latex_times = '\\times' in solution_html
        has_latex_frac = '\\frac' in solution_html
        has_latex_text = '\\text' in solution_html
        
        print(f"   Solution HTML length: {len(solution_html)} chars")
        print(f"   Contains **: {has_markdown}")
        print(f"   Contains <strong>: {has_strong_tag}")
        print(f"   Contains \\times: {has_latex_times}")
        print(f"   Contains \\frac: {has_latex_frac}")
        print(f"   Contains \\text: {has_latex_text}")
        
        # Critères de succès
        success = (
            not has_markdown and  # Pas de **
            has_strong_tag and   # Contient <strong>
            not has_latex_times and  # Pas de \times
            not has_latex_frac and   # Pas de \frac
            not has_latex_text       # Pas de \text
        )
        
        if success:
            print("   ✅ HTML pur validé - Pas de Markdown ni LaTeX")
        else:
            print("   ❌ HTML contient encore du Markdown ou LaTeX")
            
        return success
    
    def test_html_pur_pas_de_latex(self) -> bool:
        """Test 2: HTML pur - Pas de LaTeX"""
        print("Vérification: solution_html ne contient PAS $ et utilise × au lieu de \\times")
        
        payload = {
            "code_officiel": "6e_GM07",
            "difficulte": "moyen"
        }
        
        response = self.make_request(payload)
        solution_html = response.get('solution_html', '')
        
        # Vérifications
        has_dollar_signs = '$' in solution_html
        has_times_symbol = '×' in solution_html
        has_div_symbol = '÷' in solution_html
        has_latex_times = '\\times' in solution_html
        has_latex_div = '\\div' in solution_html
        
        print(f"   Solution HTML length: {len(solution_html)} chars")
        print(f"   Contains $: {has_dollar_signs}")
        print(f"   Contains ×: {has_times_symbol}")
        print(f"   Contains ÷: {has_div_symbol}")
        print(f"   Contains \\times: {has_latex_times}")
        print(f"   Contains \\div: {has_latex_div}")
        
        # Critères de succès
        success = (
            not has_dollar_signs and  # Pas de $
            not has_latex_times and   # Pas de \times
            not has_latex_div         # Pas de \div
        )
        
        # Bonus si utilise × et ÷
        if has_times_symbol or has_div_symbol:
            print("   ✅ Utilise les symboles HTML × ou ÷")
        
        if success:
            print("   ✅ HTML pur validé - Pas de LaTeX")
        else:
            print("   ❌ HTML contient encore du LaTeX")
            
        return success
    
    def test_pas_de_doublons_free_moyen(self) -> bool:
        """Test 3: Pas de doublons - 5 exercices FREE moyen (stock=4)"""
        print("Vérification: Au moins 4 exercices uniques sur 5 avec seeds consécutifs")
        
        base_seed = 1734100000000
        exercises = []
        
        for i in range(5):
            payload = {
                "code_officiel": "6e_GM07",
                "difficulte": "moyen",
                "seed": base_seed + i
            }
            
            response = self.make_request(payload)
            exercise_content = response.get('enonce_html', '') + response.get('solution_html', '')
            
            # Créer un hash du contenu pour détecter les doublons
            content_hash = hashlib.md5(exercise_content.encode()).hexdigest()
            exercises.append({
                'seed': base_seed + i,
                'hash': content_hash,
                'content_preview': exercise_content[:100]
            })
            
            print(f"   Seed {base_seed + i}: Hash {content_hash[:8]}...")
            time.sleep(0.1)  # Éviter de surcharger l'API
        
        # Compter les exercices uniques
        unique_hashes = set(ex['hash'] for ex in exercises)
        unique_count = len(unique_hashes)
        
        print(f"   Exercices générés: 5")
        print(f"   Exercices uniques: {unique_count}")
        print(f"   Doublons détectés: {5 - unique_count}")
        
        # Critère de succès: au moins 4 uniques sur 5 (stock=4)
        success = unique_count >= 4
        
        if success:
            print("   ✅ Diversité suffisante - Au moins 4/5 exercices uniques")
        else:
            print("   ❌ Trop de doublons - Moins de 4/5 exercices uniques")
            
        return success
    
    def test_pas_de_doublons_pro_difficile(self) -> bool:
        """Test 4: Pas de doublons - 5 exercices PRO difficile (stock=6)"""
        print("Vérification: 5 exercices uniques sur 5 avec seeds consécutifs en mode PRO")
        
        base_seed = 1734200000000
        exercises = []
        
        for i in range(5):
            payload = {
                "code_officiel": "6e_GM07",
                "difficulte": "difficile",
                "offer": "pro",
                "seed": base_seed + i
            }
            
            response = self.make_request(payload)
            exercise_content = response.get('enonce_html', '') + response.get('solution_html', '')
            
            # Créer un hash du contenu pour détecter les doublons
            content_hash = hashlib.md5(exercise_content.encode()).hexdigest()
            exercises.append({
                'seed': base_seed + i,
                'hash': content_hash,
                'content_preview': exercise_content[:100]
            })
            
            print(f"   Seed {base_seed + i}: Hash {content_hash[:8]}...")
            time.sleep(0.1)  # Éviter de surcharger l'API
        
        # Compter les exercices uniques
        unique_hashes = set(ex['hash'] for ex in exercises)
        unique_count = len(unique_hashes)
        
        print(f"   Exercices générés: 5")
        print(f"   Exercices uniques: {unique_count}")
        print(f"   Doublons détectés: {5 - unique_count}")
        
        # Critère de succès: 5 uniques sur 5 (stock=6)
        success = unique_count == 5
        
        if success:
            print("   ✅ Diversité parfaite - 5/5 exercices uniques")
        else:
            print("   ❌ Doublons détectés - Moins de 5/5 exercices uniques")
            
        return success
    
    def test_non_regression_autres_chapitres(self) -> bool:
        """Test 5: Non-régression - Autres chapitres"""
        print("Vérification: 6e_N08 fonctionne toujours correctement")
        
        payload = {
            "code_officiel": "6e_N08",
            "difficulte": "facile"
        }
        
        response = self.make_request(payload)
        generator_code = response.get('metadata', {}).get('generator_code', '')
        
        print(f"   Generator code: {generator_code}")
        
        # Vérifications
        has_fraction_generator = 'FRACTION' in generator_code.upper()
        
        success = has_fraction_generator
        
        if success:
            print("   ✅ Chapitre 6e_N08 fonctionne - Generator FRACTION détecté")
        else:
            print("   ❌ Chapitre 6e_N08 ne fonctionne pas correctement")
            
        return success
    
    def test_non_regression_logique_free_pro(self) -> bool:
        """Test 6: Non-régression - Logique Free/Pro"""
        print("Vérification: Logique Free/Pro préservée")
        
        # Test 5 appels FREE
        free_results = []
        for i in range(5):
            payload = {
                "code_officiel": "6e_GM07",
                "difficulte": "facile",
                "seed": 1734300000000 + i
            }
            
            response = self.make_request(payload)
            is_premium = response.get('metadata', {}).get('is_premium', None)
            free_results.append(is_premium)
            time.sleep(0.1)
        
        # Test 5 appels PRO difficile
        pro_results = []
        for i in range(5):
            payload = {
                "code_officiel": "6e_GM07",
                "difficulte": "difficile",
                "offer": "pro",
                "seed": 1734400000000 + i
            }
            
            response = self.make_request(payload)
            is_premium = response.get('metadata', {}).get('is_premium', None)
            pro_results.append(is_premium)
            time.sleep(0.1)
        
        # Vérifications
        all_free_are_false = all(result is False for result in free_results)
        at_least_one_pro_is_true = any(result is True for result in pro_results)
        
        print(f"   FREE results: {free_results}")
        print(f"   PRO results: {pro_results}")
        print(f"   All FREE are false: {all_free_are_false}")
        print(f"   At least one PRO is true: {at_least_one_pro_is_true}")
        
        success = all_free_are_false and at_least_one_pro_is_true
        
        if success:
            print("   ✅ Logique Free/Pro préservée")
        else:
            print("   ❌ Logique Free/Pro compromise")
            
        return success
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all GM07 v2 validation tests"""
        print("🧪 VALIDATION DES CORRECTIFS GM07 V2")
        print("=" * 80)
        print("Context: Validation de deux bugs corrigés dans GM07:")
        print("1. HTML pur: Remplacement de Markdown et LaTeX par HTML")
        print("2. Pas de doublons: Seeds différents → exercices différents")
        print(f"Backend URL: {self.base_url}")
        
        # Run all tests
        test_results = {
            "test_1_html_pas_markdown": self.run_test("HTML pur - Pas de Markdown", self.test_html_pur_pas_de_markdown),
            "test_2_html_pas_latex": self.run_test("HTML pur - Pas de LaTeX", self.test_html_pur_pas_de_latex),
            "test_3_pas_doublons_free": self.run_test("Pas de doublons - FREE moyen (stock=4)", self.test_pas_de_doublons_free_moyen),
            "test_4_pas_doublons_pro": self.run_test("Pas de doublons - PRO difficile (stock=6)", self.test_pas_de_doublons_pro_difficile),
            "test_5_non_regression_chapitres": self.run_test("Non-régression - Autres chapitres", self.test_non_regression_autres_chapitres),
            "test_6_non_regression_free_pro": self.run_test("Non-régression - Logique Free/Pro", self.test_non_regression_logique_free_pro)
        }
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 RÉSULTATS DE VALIDATION GM07 V2")
        print("=" * 80)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100
        print(f"\nTaux de succès: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        
        # Critères de succès globaux
        all_html_tests = test_results["test_1_html_pas_markdown"] and test_results["test_2_html_pas_latex"]
        all_doublon_tests = test_results["test_3_pas_doublons_free"] and test_results["test_4_pas_doublons_pro"]
        all_regression_tests = test_results["test_5_non_regression_chapitres"] and test_results["test_6_non_regression_free_pro"]
        
        print(f"\n🎯 CRITÈRES DE SUCCÈS:")
        print(f"   ✅ Pas de Markdown ni LaTeX: {'✅' if all_html_tests else '❌'}")
        print(f"   ✅ Au moins 4/5 uniques (seeds): {'✅' if all_doublon_tests else '❌'}")
        print(f"   ✅ Autres chapitres non impactés: {'✅' if all_regression_tests else '❌'}")
        print(f"   ✅ Logique Free/Pro préservée: {'✅' if test_results['test_6_non_regression_free_pro'] else '❌'}")
        
        overall_success = all_html_tests and all_doublon_tests and all_regression_tests
        
        if overall_success:
            print(f"\n🎉 VALIDATION GM07 V2 RÉUSSIE - Tous les correctifs fonctionnent")
        else:
            print(f"\n⚠️  VALIDATION GM07 V2 PARTIELLE - Certains correctifs à revoir")
        
        return {
            "overall_success": overall_success,
            "tests_passed": self.tests_passed,
            "tests_total": self.tests_run,
            "success_rate": success_rate,
            "test_results": test_results,
            "criteria": {
                "html_pur": all_html_tests,
                "pas_doublons": all_doublon_tests,
                "non_regression": all_regression_tests
            }
        }

def main():
    """Main function to run GM07 v2 validation"""
    validator = GM07V2Validator()
    results = validator.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results["overall_success"] else 1
    return exit_code

if __name__ == "__main__":
    exit(main())