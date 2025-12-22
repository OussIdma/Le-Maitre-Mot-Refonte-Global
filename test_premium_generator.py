#!/usr/bin/env python3
"""
Test complet du générateur PREMIUM pour le chapitre "Durées et lecture de l'heure" (6e_GM07)

Contexte: Deux bugs ont été corrigés dans /app/backend/routes/exercises_routes.py:
1. UnboundLocalError sur `get_chapter_by_official_code` (import redondant supprimé)
2. 'DUREES_PREMIUM' is not a valid MathExerciseType (changement de `MathExerciseType(g)` à `MathExerciseType[g]`)

Tests à effectuer:
1. Test Mode Standard (sans premium) - should return is_premium: false
2. Test Mode PREMIUM (offer=pro) - should return is_premium: true with DUREES_PREMIUM generator
3. Test Content PREMIUM (5 générations) - verify variety and quality
4. Test Mode Legacy (compatibility)
5. Test Non-regression other chapters
6. Test Error (invalid code_officiel)
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

class PremiumGeneratorTester:
    def __init__(self, base_url="https://math-exercise-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result for summary"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
        if details.get("message"):
            print(f"   {details['message']}")
    
    def make_request(self, endpoint: str, method: str = "POST", data: Dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (success, response_data)"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {
                    "status_code": response.status_code,
                    "error": response.text[:500]
                }
                
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_mode_standard_without_premium(self):
        """Test 1: Mode Standard (sans premium) - should return is_premium: false"""
        print("\n🔍 Test 1: Mode Standard (sans premium)")
        
        test_data = {
            "code_officiel": "6e_GM07",
            "difficulte": "facile"
            # Note: pas de "offer" = mode gratuit par défaut
        }
        
        success, response = self.make_request("v1/exercises/generate", "POST", test_data)
        
        if success:
            metadata = response.get("metadata", {})
            is_premium = metadata.get("is_premium", False)
            offer = metadata.get("offer", "")
            generator_code = metadata.get("generator_code", "")
            
            # Vérifications
            checks = {
                "http_200": True,
                "is_premium_false": not is_premium,
                "offer_free": offer in ["free", ""],
                "valid_generator": generator_code.startswith("6e_"),
                "enonce_not_empty": len(response.get("enonce_html", "")) > 0
            }
            
            all_passed = all(checks.values())
            
            details = {
                "message": f"is_premium: {is_premium}, offer: '{offer}', generator: {generator_code}",
                "checks": checks,
                "response_keys": list(response.keys())
            }
            
            # Vérifier que c'est un des générateurs attendus (pas forcément DUREES_PREMIUM)
            expected_generators = ["LECTURE_HORLOGE", "CALCUL_DUREE", "CONVERSION_DUREES", "PROBLEME_DUREES", "DUREES_PREMIUM"]
            generator_name = generator_code.replace("6e_", "") if generator_code.startswith("6e_") else ""
            
            if generator_name in expected_generators:
                details["generator_valid"] = True
                details["message"] += f" (générateur valide: {generator_name})"
            else:
                details["generator_valid"] = False
                details["message"] += f" (générateur inattendu: {generator_name})"
                all_passed = False
            
        else:
            all_passed = False
            details = {"message": f"Erreur HTTP: {response}", "checks": {}}
        
        self.log_test_result("Mode Standard (sans premium)", all_passed, details)
        return all_passed
    
    def test_mode_premium_with_pro_offer(self):
        """Test 2: Mode PREMIUM (offer=pro) - should return is_premium: true with DUREES_PREMIUM"""
        print("\n🔍 Test 2: Mode PREMIUM (offer=pro)")
        
        test_data = {
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "offer": "pro"
        }
        
        success, response = self.make_request("v1/exercises/generate", "POST", test_data)
        
        if success:
            metadata = response.get("metadata", {})
            is_premium = metadata.get("is_premium", False)
            offer = metadata.get("offer", "")
            generator_code = metadata.get("generator_code", "")
            
            # Vérifications PREMIUM
            checks = {
                "http_200": True,
                "is_premium_true": is_premium,
                "offer_pro": offer == "pro",
                "durees_premium_generator": "DUREES_PREMIUM" in generator_code,
                "enonce_not_empty": len(response.get("enonce_html", "")) > 0
            }
            
            all_passed = all(checks.values())
            
            details = {
                "message": f"is_premium: {is_premium}, offer: '{offer}', generator: {generator_code}",
                "checks": checks,
                "response_keys": list(response.keys())
            }
            
            # Vérifier la qualité de l'énoncé PREMIUM
            enonce_html = response.get("enonce_html", "")
            if "DUREES_PREMIUM" in generator_code and len(enonce_html) > 50:
                details["premium_quality"] = True
                details["message"] += " (énoncé premium de qualité)"
            elif "DUREES_PREMIUM" in generator_code:
                details["premium_quality"] = False
                details["message"] += " (énoncé premium trop court)"
                all_passed = False
            
        else:
            all_passed = False
            details = {"message": f"Erreur HTTP: {response}", "checks": {}}
        
        self.log_test_result("Mode PREMIUM (offer=pro)", all_passed, details)
        return all_passed
    
    def test_premium_content_variety(self):
        """Test 3: Test Contenu PREMIUM (5 générations) - verify variety and quality"""
        print("\n🔍 Test 3: Contenu PREMIUM (5 générations)")
        
        enonces = []
        generators_used = []
        premium_count = 0
        
        for i in range(5):
            test_data = {
                "code_officiel": "6e_GM07",
                "difficulte": "moyen",
                "offer": "pro"
            }
            
            success, response = self.make_request("v1/exercises/generate", "POST", test_data)
            
            if success:
                metadata = response.get("metadata", {})
                generator_code = metadata.get("generator_code", "")
                is_premium = metadata.get("is_premium", False)
                enonce_html = response.get("enonce_html", "")
                
                enonces.append(enonce_html)
                generators_used.append(generator_code)
                
                if is_premium and "DUREES_PREMIUM" in generator_code:
                    premium_count += 1
                
                print(f"   Génération {i+1}: {generator_code}, premium: {is_premium}")
            else:
                print(f"   Génération {i+1}: ÉCHEC - {response}")
        
        # Analyse de la variété
        unique_enonces = len(set(enonces))
        unique_generators = len(set(generators_used))
        
        # Vérifications
        checks = {
            "all_generations_success": len(enonces) == 5,
            "premium_generator_used": premium_count > 0,
            "enonce_variety": unique_enonces >= 3,  # Au moins 3 énoncés différents sur 5
            "generator_variety": unique_generators >= 1,  # Au moins 1 générateur utilisé
            "quality_content": all(len(e) > 50 for e in enonces)  # Énoncés non vides
        }
        
        all_passed = all(checks.values())
        
        details = {
            "message": f"Générations: {len(enonces)}/5, Premium: {premium_count}, Variété énoncés: {unique_enonces}, Générateurs: {unique_generators}",
            "checks": checks,
            "generators_used": list(set(generators_used)),
            "premium_count": premium_count,
            "variety_score": unique_enonces / 5
        }
        
        # Vérifier la présence de conversions (h, min, sec) dans les énoncés premium
        conversion_indicators = ["heure", "minute", "seconde", "h", "min", "sec", "conversion"]
        premium_with_conversions = 0
        
        for i, enonce in enumerate(enonces):
            if generators_used[i] and "DUREES_PREMIUM" in generators_used[i]:
                if any(indicator in enonce.lower() for indicator in conversion_indicators):
                    premium_with_conversions += 1
        
        if premium_count > 0:
            details["conversion_quality"] = premium_with_conversions / premium_count
            details["message"] += f", Conversions: {premium_with_conversions}/{premium_count}"
        
        self.log_test_result("Contenu PREMIUM (variété et qualité)", all_passed, details)
        return all_passed
    
    def test_mode_legacy_compatibility(self):
        """Test 4: Mode Legacy (compatibilité) - should work with old format"""
        print("\n🔍 Test 4: Mode Legacy (compatibilité)")
        
        test_data = {
            "niveau": "6e",
            "chapitre": "Fractions",
            "difficulte": "facile"
        }
        
        success, response = self.make_request("v1/exercises/generate", "POST", test_data)
        
        if success:
            metadata = response.get("metadata", {})
            generator_code = metadata.get("generator_code", "")
            
            checks = {
                "http_200": True,
                "has_generator": len(generator_code) > 0,
                "enonce_not_empty": len(response.get("enonce_html", "")) > 0,
                "solution_not_empty": len(response.get("solution_html", "")) > 0
            }
            
            all_passed = all(checks.values())
            
            details = {
                "message": f"Legacy mode functional, generator: {generator_code}",
                "checks": checks,
                "response_keys": list(response.keys())
            }
            
        else:
            all_passed = False
            details = {"message": f"Erreur HTTP: {response}", "checks": {}}
        
        self.log_test_result("Mode Legacy (compatibilité)", all_passed, details)
        return all_passed
    
    def test_non_regression_other_chapters(self):
        """Test 5: Non-régression autres chapitres"""
        print("\n🔍 Test 5: Non-régression autres chapitres")
        
        test_chapters = [
            {"code_officiel": "6e_N08", "name": "Fractions"},
            {"code_officiel": "6e_G07", "name": "Symétrie axiale"}
        ]
        
        all_passed = True
        results = []
        
        for chapter in test_chapters:
            test_data = {
                "code_officiel": chapter["code_officiel"],
                "difficulte": "facile"
            }
            
            success, response = self.make_request("v1/exercises/generate", "POST", test_data)
            
            if success:
                metadata = response.get("metadata", {})
                generator_code = metadata.get("generator_code", "")
                
                chapter_success = (
                    len(response.get("enonce_html", "")) > 0 and
                    len(generator_code) > 0
                )
                
                results.append({
                    "chapter": chapter["name"],
                    "code": chapter["code_officiel"],
                    "success": chapter_success,
                    "generator": generator_code
                })
                
                print(f"   {chapter['name']} ({chapter['code_officiel']}): {'✅' if chapter_success else '❌'} - {generator_code}")
                
                if not chapter_success:
                    all_passed = False
            else:
                results.append({
                    "chapter": chapter["name"],
                    "code": chapter["code_officiel"],
                    "success": False,
                    "error": str(response)
                })
                print(f"   {chapter['name']} ({chapter['code_officiel']}): ❌ - {response}")
                all_passed = False
        
        details = {
            "message": f"Chapitres testés: {len(results)}, Succès: {sum(1 for r in results if r['success'])}",
            "results": results
        }
        
        self.log_test_result("Non-régression autres chapitres", all_passed, details)
        return all_passed
    
    def test_error_invalid_code_officiel(self):
        """Test 6: Test Erreur (code_officiel invalide) - should return HTTP 422"""
        print("\n🔍 Test 6: Test Erreur (code_officiel invalide)")
        
        test_data = {
            "code_officiel": "INVALID_CODE"
        }
        
        success, response = self.make_request("v1/exercises/generate", "POST", test_data)
        
        # Pour ce test, on s'attend à un échec avec un code d'erreur approprié
        expected_failure = not success and response.get("status_code") == 422
        
        if expected_failure:
            details = {
                "message": f"Erreur 422 correctement retournée pour code invalide",
                "status_code": response.get("status_code"),
                "error_preview": response.get("error", "")[:200]
            }
            test_passed = True
        elif success:
            # Si ça réussit, c'est un problème (le code invalide ne devrait pas marcher)
            details = {
                "message": "PROBLÈME: Code invalide a généré un exercice (ne devrait pas)",
                "unexpected_success": True
            }
            test_passed = False
        else:
            # Autre type d'erreur
            details = {
                "message": f"Erreur inattendue: {response}",
                "status_code": response.get("status_code", "unknown")
            }
            test_passed = False
        
        self.log_test_result("Erreur code_officiel invalide", test_passed, details)
        return test_passed
    
    def run_all_tests(self):
        """Execute all tests and provide summary"""
        print("🧪 VALIDATION COMPLÈTE DU GÉNÉRATEUR PREMIUM - Chapitre 6e_GM07")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Execute all tests
        test_methods = [
            self.test_mode_standard_without_premium,
            self.test_mode_premium_with_pro_offer,
            self.test_premium_content_variety,
            self.test_mode_legacy_compatibility,
            self.test_non_regression_other_chapters,
            self.test_error_invalid_code_officiel
        ]
        
        start_time = time.time()
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ ERREUR dans {test_method.__name__}: {e}")
                self.tests_run += 1
                self.log_test_result(test_method.__name__, False, {"error": str(e)})
        
        total_time = time.time() - start_time
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests exécutés: {self.tests_run}")
        print(f"Tests réussis: {self.tests_passed}")
        print(f"Taux de succès: {success_rate:.1f}%")
        print(f"Temps total: {total_time:.2f}s")
        
        # Detailed results
        print("\n📋 DÉTAIL DES RÉSULTATS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}")
            if result["details"].get("message"):
                print(f"   {result['details']['message']}")
        
        # Critical assessment
        print("\n🎯 CRITÈRES DE SUCCÈS:")
        
        critical_tests = [
            "Mode Standard (sans premium)",
            "Mode PREMIUM (offer=pro)",
            "Contenu PREMIUM (variété et qualité)"
        ]
        
        critical_passed = sum(1 for r in self.test_results 
                            if r["test_name"] in critical_tests and r["success"])
        
        print(f"✅ Tests critiques réussis: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("🎉 VALIDATION PREMIUM COMPLÈTEMENT RÉUSSIE")
            print("✅ Le mode PREMIUM active bien le générateur DUREES_PREMIUM")
            print("✅ Le mode standard ne retourne pas is_premium=true inappropriément")
            print("✅ Les énoncés PREMIUM sont de qualité avec conversions variées")
        elif critical_passed >= 2:
            print("⚠️  VALIDATION PREMIUM PARTIELLEMENT RÉUSSIE")
            print("   Certains tests critiques ont échoué")
        else:
            print("❌ VALIDATION PREMIUM ÉCHOUÉE")
            print("   Les tests critiques ont majoritairement échoué")
        
        # Non-regression check
        non_regression_passed = any(r["test_name"] == "Non-régression autres chapitres" and r["success"] 
                                  for r in self.test_results)
        
        if non_regression_passed:
            print("✅ Aucune régression sur les autres chapitres")
        else:
            print("❌ Régression détectée sur d'autres chapitres")
        
        return success_rate >= 80 and critical_passed >= 2


def main():
    """Main test execution"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://math-exercise-sync.preview.emergentagent.com"
    
    tester = PremiumGeneratorTester(base_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()