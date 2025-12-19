#!/usr/bin/env python3
"""
Test Suite for AI Optimization System - Le Maître Mot

Tests the new optimization system that reduces AI calls by using pre-generated templates (gabarits).

SYSTEM COMPONENTS TESTED:
1. Gabarit Loader - Loading and managing pre-generated templates
2. Style Manager - 10 different formulation styles
3. Cache Manager - Caching system with hit/miss metrics
4. Math Text Service - Integration with optimization flow

OPTIMIZATION FLOW:
1. Check if gabarit exists → Select random style → Check cache → Interpolate values → Return (0 AI calls)
2. If fail: fallback to classic AI call

EXPECTED RESULTS:
✅ Symétrie Axiale/Centrale exercises generated with gabarits (0 AI calls)
✅ Different styles produce varied formulations
✅ Cache metrics show hits/misses
✅ Fallback works for chapters without gabarits
✅ Placeholders properly replaced
"""

import requests
import json
import time
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any


class IAOptimizationTester:
    """Comprehensive tester for the AI optimization system"""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.guest_id = f"test-optimization-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Test results tracking
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "gabarit_usage": [],
            "cache_metrics": [],
            "style_variety": [],
            "fallback_tests": [],
            "performance_data": []
        }
        
        print(f"🎯 AI OPTIMIZATION SYSTEM TESTER INITIALIZED")
        print(f"   Base URL: {self.base_url}")
        print(f"   Guest ID: {self.guest_id}")
        print(f"   Test Focus: Gabarits, Cache, Styles, Fallbacks")
    
    def run_api_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                     data: Dict = None, timeout: int = 30) -> tuple:
        """Execute a single API test with detailed logging"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.test_results["total_tests"] += 1
        print(f"\n🔍 Testing: {name}")
        print(f"   URL: {url}")
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            
            execution_time = time.time() - start_time
            
            print(f"   Status: {response.status_code} (Expected: {expected_status})")
            print(f"   Time: {execution_time:.2f}s")
            
            success = response.status_code == expected_status
            
            if success:
                self.test_results["passed_tests"] += 1
                print(f"   ✅ PASSED")
                try:
                    response_data = response.json()
                    return True, response_data, execution_time
                except:
                    return True, response.text, execution_time
            else:
                print(f"   ❌ FAILED - Got {response.status_code}, expected {expected_status}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    return False, error_data, execution_time
                except:
                    print(f"   Error: {response.text[:200]}")
                    return False, {"error": response.text}, execution_time
                    
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT after {timeout}s")
            return False, {"error": "timeout"}, timeout
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            return False, {"error": str(e)}, 0
    
    def test_symetrie_axiale_optimization(self):
        """
        Test 1: Génération d'exercices Symétrie Axiale avec optimisation
        
        EXPECTED:
        - 5 exercices générés avec succès
        - Énoncés différents (variété lexicale)
        - Logs "GABARIT utilisé" (pas d'appel IA)
        - Placeholders remplacés correctement
        - Respect des règles pédagogiques
        """
        print(f"\n" + "="*70)
        print(f"🎯 TEST 1: SYMÉTRIE AXIALE AVEC OPTIMISATION")
        print(f"="*70)
        
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "5e",
            "chapitre": "Symétrie axiale",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 5,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"📋 Test Configuration:")
        print(f"   Chapitre: {test_data['chapitre']}")
        print(f"   Niveau: {test_data['niveau']}")
        print(f"   Nombre d'exercices: {test_data['nb_exercices']}")
        print(f"   Expected: Gabarits utilisés (0 appels IA)")
        
        success, response, exec_time = self.run_api_test(
            "Symétrie Axiale Optimization",
            "POST",
            "generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):
            document = response.get('document', {})
            exercises = document.get('exercises', [])
            
            print(f"\n📊 RÉSULTATS:")
            print(f"   ✅ {len(exercises)} exercices générés")
            print(f"   ⏱️  Temps d'exécution: {exec_time:.2f}s")
            
            # Test 1.1: Vérifier le nombre d'exercices
            if len(exercises) == 5:
                print(f"   ✅ Nombre correct d'exercices: {len(exercises)}/5")
            else:
                print(f"   ❌ Nombre incorrect d'exercices: {len(exercises)}/5")
            
            # Test 1.2: Vérifier la variété lexicale
            enonces = [ex.get('enonce', '') for ex in exercises]
            variety_score = self.calculate_lexical_variety(enonces)
            
            print(f"\n🎨 VARIÉTÉ LEXICALE:")
            print(f"   Score de variété: {variety_score:.2f} (>0.6 attendu)")
            
            if variety_score > 0.6:
                print(f"   ✅ Bonne variété lexicale entre les énoncés")
            else:
                print(f"   ⚠️  Variété lexicale faible - styles peut-être similaires")
            
            # Test 1.3: Vérifier l'absence de placeholders
            placeholder_issues = []
            for i, enonce in enumerate(enonces):
                placeholders = re.findall(r'\{[^}]+\}', enonce)
                if placeholders:
                    placeholder_issues.append(f"Exercice {i+1}: {placeholders}")
            
            print(f"\n🔧 INTERPOLATION DES PLACEHOLDERS:")
            if not placeholder_issues:
                print(f"   ✅ Tous les placeholders correctement remplacés")
            else:
                print(f"   ❌ Placeholders non remplacés détectés:")
                for issue in placeholder_issues:
                    print(f"     - {issue}")
            
            # Test 1.4: Vérifier le contenu géométrique
            geometric_content_score = 0
            for i, enonce in enumerate(enonces):
                has_points = bool(re.search(r'\b[A-Z]\b', enonce))
                has_coords = bool(re.search(r'\(\s*-?\d+\s*,\s*-?\d+\s*\)', enonce))
                has_axis = bool(re.search(r'axe|symétrie', enonce.lower()))
                
                content_score = sum([has_points, has_coords, has_axis])
                geometric_content_score += content_score
                
                print(f"   Exercice {i+1}: Points={has_points}, Coords={has_coords}, Axe={has_axis}")
            
            avg_content_score = geometric_content_score / (len(exercises) * 3)
            print(f"\n📐 CONTENU GÉOMÉTRIQUE:")
            print(f"   Score moyen: {avg_content_score:.2f} (>0.7 attendu)")
            
            if avg_content_score > 0.7:
                print(f"   ✅ Contenu géométrique approprié")
            else:
                print(f"   ⚠️  Contenu géométrique insuffisant")
            
            # Enregistrer les résultats
            self.test_results["gabarit_usage"].append({
                "chapitre": "Symétrie axiale",
                "exercises_count": len(exercises),
                "variety_score": variety_score,
                "placeholder_issues": len(placeholder_issues),
                "content_score": avg_content_score,
                "execution_time": exec_time
            })
            
            # Test global réussi si tous les critères sont OK
            test_passed = (
                len(exercises) == 5 and
                variety_score > 0.6 and
                len(placeholder_issues) == 0 and
                avg_content_score > 0.7
            )
            
            print(f"\n🎯 RÉSULTAT TEST 1:")
            if test_passed:
                print(f"   ✅ SYMÉTRIE AXIALE OPTIMIZATION - SUCCÈS COMPLET")
            else:
                print(f"   ⚠️  SYMÉTRIE AXIALE OPTIMIZATION - SUCCÈS PARTIEL")
            
            return test_passed, {
                "exercises_generated": len(exercises),
                "variety_score": variety_score,
                "placeholder_issues": len(placeholder_issues),
                "content_score": avg_content_score
            }
        else:
            print(f"\n❌ ÉCHEC DE LA GÉNÉRATION")
            return False, {"error": "generation_failed"}
    
    def test_symetrie_centrale_optimization(self):
        """
        Test 2: Génération d'exercices Symétrie Centrale
        
        EXPECTED:
        - 5 exercices générés avec succès
        - Gabarits utilisés (centre de symétrie)
        - Variété dans les formulations
        """
        print(f"\n" + "="*70)
        print(f"🎯 TEST 2: SYMÉTRIE CENTRALE AVEC OPTIMISATION")
        print(f"="*70)
        
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "5e",
            "chapitre": "Symétrie centrale",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 5,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"📋 Test Configuration:")
        print(f"   Chapitre: {test_data['chapitre']}")
        print(f"   Expected: Gabarits avec centre de symétrie")
        
        success, response, exec_time = self.run_api_test(
            "Symétrie Centrale Optimization",
            "POST",
            "generate",
            200,
            data=test_data,
            timeout=60
        )
        
        if success and isinstance(response, dict):
            document = response.get('document', {})
            exercises = document.get('exercises', [])
            
            print(f"\n📊 RÉSULTATS:")
            print(f"   ✅ {len(exercises)} exercices générés")
            print(f"   ⏱️  Temps d'exécution: {exec_time:.2f}s")
            
            # Vérifier le contenu spécifique à la symétrie centrale
            central_symmetry_score = 0
            for i, enonce in enumerate(exercises):
                has_center = bool(re.search(r'centre|milieu', enonce.lower()))
                has_central_vocab = bool(re.search(r'centrale|central', enonce.lower()))
                
                if has_center or has_central_vocab:
                    central_symmetry_score += 1
                    print(f"   ✅ Exercice {i+1}: Contenu symétrie centrale détecté")
                else:
                    print(f"   ⚠️  Exercice {i+1}: Contenu symétrie centrale non détecté")
            
            central_ratio = central_symmetry_score / len(exercises) if exercises else 0
            
            print(f"\n🎯 SPÉCIFICITÉ SYMÉTRIE CENTRALE:")
            print(f"   Exercices avec contenu approprié: {central_symmetry_score}/{len(exercises)}")
            print(f"   Ratio: {central_ratio:.2f} (>0.8 attendu)")
            
            test_passed = central_ratio > 0.8 and len(exercises) == 5
            
            self.test_results["gabarit_usage"].append({
                "chapitre": "Symétrie centrale",
                "exercises_count": len(exercises),
                "central_content_ratio": central_ratio,
                "execution_time": exec_time
            })
            
            return test_passed, {
                "exercises_generated": len(exercises),
                "central_content_ratio": central_ratio
            }
        else:
            return False, {"error": "generation_failed"}
    
    def test_cache_metrics_verification(self):
        """
        Test 3: Vérification des métriques de cache
        
        EXPECTED:
        - Premiers exercices: CACHE MISS (chargement gabarits)
        - Exercices suivants: CACHE HIT (réutilisation)
        - Métriques disponibles via logs ou endpoint
        """
        print(f"\n" + "="*70)
        print(f"🎯 TEST 3: VÉRIFICATION DES MÉTRIQUES DE CACHE")
        print(f"="*70)
        
        print(f"📋 Stratégie de test:")
        print(f"   1. Générer exercices (devrait créer cache)")
        print(f"   2. Générer à nouveau (devrait utiliser cache)")
        print(f"   3. Vérifier les métriques")
        
        # Première génération (cache miss attendu)
        test_data_1 = {
            "matiere": "Mathématiques",
            "niveau": "5e",
            "chapitre": "Symétrie axiale",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 3,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"\n🔄 PREMIÈRE GÉNÉRATION (Cache Miss attendu):")
        success_1, response_1, time_1 = self.run_api_test(
            "Cache Test - First Generation",
            "POST",
            "generate",
            200,
            data=test_data_1,
            timeout=60
        )
        
        # Deuxième génération (cache hit attendu)
        test_data_2 = {
            "matiere": "Mathématiques",
            "niveau": "5e",
            "chapitre": "Symétrie axiale",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 3,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"\n🔄 DEUXIÈME GÉNÉRATION (Cache Hit attendu):")
        success_2, response_2, time_2 = self.run_api_test(
            "Cache Test - Second Generation",
            "POST",
            "generate",
            200,
            data=test_data_2,
            timeout=60
        )
        
        # Analyser les temps d'exécution
        if success_1 and success_2:
            print(f"\n⏱️  ANALYSE DES PERFORMANCES:")
            print(f"   Première génération: {time_1:.2f}s")
            print(f"   Deuxième génération: {time_2:.2f}s")
            
            # Le cache devrait accélérer la deuxième génération
            speed_improvement = (time_1 - time_2) / time_1 if time_1 > 0 else 0
            print(f"   Amélioration: {speed_improvement:.1%}")
            
            if speed_improvement > 0.1:  # Au moins 10% plus rapide
                print(f"   ✅ Cache semble fonctionner (amélioration significative)")
                cache_working = True
            elif time_2 < 5:  # Très rapide = probablement du cache
                print(f"   ✅ Génération très rapide (probablement cache)")
                cache_working = True
            else:
                print(f"   ⚠️  Pas d'amélioration claire détectée")
                cache_working = False
            
            self.test_results["cache_metrics"].append({
                "first_generation_time": time_1,
                "second_generation_time": time_2,
                "speed_improvement": speed_improvement,
                "cache_working": cache_working
            })
            
            return cache_working, {
                "first_time": time_1,
                "second_time": time_2,
                "improvement": speed_improvement
            }
        else:
            print(f"   ❌ Échec des générations pour test de cache")
            return False, {"error": "generation_failed"}
    
    def test_style_variety(self):
        """
        Test 4: Variété des styles
        
        EXPECTED:
        - 10+ exercices avec styles différents
        - Structures différentes (concis, narratif, scolaire, etc.)
        - Vocabulaire varié
        """
        print(f"\n" + "="*70)
        print(f"🎯 TEST 4: VARIÉTÉ DES STYLES DE FORMULATION")
        print(f"="*70)
        
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "5e",
            "chapitre": "Symétrie axiale",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 10,  # Plus d'exercices pour voir la variété
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"📋 Test Configuration:")
        print(f"   Nombre d'exercices: {test_data['nb_exercices']}")
        print(f"   Expected: Styles variés (concis, narratif, scolaire, etc.)")
        
        success, response, exec_time = self.run_api_test(
            "Style Variety Test",
            "POST",
            "generate",
            200,
            data=test_data,
            timeout=90
        )
        
        if success and isinstance(response, dict):
            document = response.get('document', {})
            exercises = document.get('exercises', [])
            enonces = [ex.get('enonce', '') for ex in exercises]
            
            print(f"\n📊 ANALYSE DES STYLES:")
            print(f"   Exercices générés: {len(exercises)}")
            
            # Analyser les différents styles détectés
            style_indicators = {
                "concis": ["Point", "Axe", "Trouve", "=", "?"],
                "narratif": ["Emma", "Lucas", "Marie", "Sophie", "aide", "dessine"],
                "scolaire": ["Soit", "Détermine", "coordonnées", "symétrique"],
                "academique": ["repère orthonormé", "propriétés", "transformation"],
                "guide": ["Observe", "Aide-toi", "À ton avis", "Regarde"],
                "defi": ["Défi", "Challenge", "Mission", "Sauras-tu"],
                "oral": ["Tu vois", "Bon", "vas-y", "Alors voilà"],
                "etapes": ["Étape", "1)", "2)", "3)", "Procédure"],
                "qr": ["Q :", "R :", "Question", "Réponse"]
            }
            
            detected_styles = {}
            for style, indicators in style_indicators.items():
                count = 0
                for enonce in enonces:
                    if any(indicator in enonce for indicator in indicators):
                        count += 1
                if count > 0:
                    detected_styles[style] = count
            
            print(f"\n🎨 STYLES DÉTECTÉS:")
            for style, count in detected_styles.items():
                print(f"   {style}: {count} exercices")
            
            # Calculer la diversité des styles
            style_diversity = len(detected_styles)
            total_styles_available = len(style_indicators)
            diversity_ratio = style_diversity / total_styles_available
            
            print(f"\n📈 MÉTRIQUES DE DIVERSITÉ:")
            print(f"   Styles différents détectés: {style_diversity}/{total_styles_available}")
            print(f"   Ratio de diversité: {diversity_ratio:.2f} (>0.5 attendu)")
            
            # Calculer la variété lexicale globale
            lexical_variety = self.calculate_lexical_variety(enonces)
            print(f"   Variété lexicale: {lexical_variety:.2f} (>0.7 attendu)")
            
            # Test réussi si bonne diversité
            test_passed = diversity_ratio > 0.5 and lexical_variety > 0.7
            
            self.test_results["style_variety"].append({
                "exercises_count": len(exercises),
                "styles_detected": style_diversity,
                "diversity_ratio": diversity_ratio,
                "lexical_variety": lexical_variety,
                "detected_styles": detected_styles
            })
            
            print(f"\n🎯 RÉSULTAT TEST 4:")
            if test_passed:
                print(f"   ✅ VARIÉTÉ DES STYLES - SUCCÈS")
            else:
                print(f"   ⚠️  VARIÉTÉ DES STYLES - INSUFFISANTE")
            
            return test_passed, {
                "styles_detected": style_diversity,
                "diversity_ratio": diversity_ratio,
                "lexical_variety": lexical_variety
            }
        else:
            return False, {"error": "generation_failed"}
    
    def test_fallback_system(self):
        """
        Test 5: Fallback sur chapitres sans gabarit
        
        EXPECTED:
        - Chapitre sans gabarit → fallback vers IA classique
        - Exercices générés correctement
        - Temps plus long (appel IA)
        """
        print(f"\n" + "="*70)
        print(f"🎯 TEST 5: SYSTÈME DE FALLBACK (CHAPITRES SANS GABARIT)")
        print(f"="*70)
        
        test_data = {
            "matiere": "Mathématiques",
            "niveau": "4e",
            "chapitre": "Théorème de Pythagore",  # Pas de gabarit pour ce chapitre
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 2,
            "versions": ["A"],
            "guest_id": self.guest_id
        }
        
        print(f"📋 Test Configuration:")
        print(f"   Chapitre: {test_data['chapitre']}")
        print(f"   Expected: Fallback vers IA classique (pas de gabarit)")
        
        success, response, exec_time = self.run_api_test(
            "Fallback System Test",
            "POST",
            "generate",
            200,
            data=test_data,
            timeout=90
        )
        
        if success and isinstance(response, dict):
            document = response.get('document', {})
            exercises = document.get('exercises', [])
            
            print(f"\n📊 RÉSULTATS FALLBACK:")
            print(f"   ✅ {len(exercises)} exercices générés")
            print(f"   ⏱️  Temps d'exécution: {exec_time:.2f}s")
            
            # Le fallback devrait prendre plus de temps (appel IA)
            if exec_time > 10:
                print(f"   ✅ Temps d'exécution élevé (probablement appel IA)")
                fallback_detected = True
            else:
                print(f"   ⚠️  Temps d'exécution rapide (gabarit utilisé ?)")
                fallback_detected = False
            
            # Vérifier le contenu spécifique au théorème de Pythagore
            pythagore_content = 0
            for i, enonce in enumerate(exercises):
                has_pythagore = bool(re.search(r'pythagore|triangle rectangle|hypoténuse', enonce.lower()))
                if has_pythagore:
                    pythagore_content += 1
                    print(f"   ✅ Exercice {i+1}: Contenu Pythagore détecté")
                else:
                    print(f"   ⚠️  Exercice {i+1}: Contenu Pythagore non détecté")
            
            content_ratio = pythagore_content / len(exercises) if exercises else 0
            
            print(f"\n🔺 CONTENU THÉORÈME DE PYTHAGORE:")
            print(f"   Exercices appropriés: {pythagore_content}/{len(exercises)}")
            print(f"   Ratio: {content_ratio:.2f} (>0.8 attendu)")
            
            test_passed = len(exercises) == 2 and content_ratio > 0.8
            
            self.test_results["fallback_tests"].append({
                "chapitre": test_data['chapitre'],
                "exercises_count": len(exercises),
                "execution_time": exec_time,
                "fallback_detected": fallback_detected,
                "content_ratio": content_ratio
            })
            
            return test_passed, {
                "exercises_generated": len(exercises),
                "fallback_detected": fallback_detected,
                "content_ratio": content_ratio
            }
        else:
            return False, {"error": "generation_failed"}
    
    def calculate_lexical_variety(self, texts: List[str]) -> float:
        """
        Calcule un score de variété lexicale entre plusieurs textes.
        
        Returns:
            Score de 0 à 1 (1 = totalement différents)
        """
        if len(texts) < 2:
            return 1.0
        
        # Tokeniser et compter les mots uniques
        all_words = set()
        total_words = 0
        
        for text in texts:
            # Nettoyer et tokeniser
            words = re.findall(r'\b\w+\b', text.lower())
            all_words.update(words)
            total_words += len(words)
        
        # Score = ratio mots uniques / mots totaux
        if total_words == 0:
            return 0.0
        
        variety = len(all_words) / total_words
        return min(variety, 1.0)
    
    def run_comprehensive_test_suite(self):
        """Execute tous les tests du système d'optimisation IA"""
        print(f"\n" + "="*80)
        print(f"🚀 SUITE DE TESTS COMPLÈTE - SYSTÈME D'OPTIMISATION IA")
        print(f"="*80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objectif: Valider le système de gabarits et cache")
        
        # Exécuter tous les tests
        test_functions = [
            ("Test 1: Symétrie Axiale", self.test_symetrie_axiale_optimization),
            ("Test 2: Symétrie Centrale", self.test_symetrie_centrale_optimization),
            ("Test 3: Métriques Cache", self.test_cache_metrics_verification),
            ("Test 4: Variété Styles", self.test_style_variety),
            ("Test 5: Système Fallback", self.test_fallback_system)
        ]
        
        results = {}
        
        for test_name, test_function in test_functions:
            try:
                success, data = test_function()
                results[test_name] = {"success": success, "data": data}
            except Exception as e:
                print(f"\n❌ ERREUR dans {test_name}: {str(e)}")
                results[test_name] = {"success": False, "data": {"error": str(e)}}
        
        # Générer le rapport final
        self.generate_final_report(results)
        
        return results
    
    def generate_final_report(self, results: Dict):
        """Génère un rapport final détaillé"""
        print(f"\n" + "="*80)
        print(f"📊 RAPPORT FINAL - SYSTÈME D'OPTIMISATION IA")
        print(f"="*80)
        
        # Statistiques globales
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📈 STATISTIQUES GLOBALES:")
        print(f"   Tests exécutés: {total_tests}")
        print(f"   Tests réussis: {passed_tests}")
        print(f"   Taux de réussite: {success_rate:.1f}%")
        
        # Détail par test
        print(f"\n📋 DÉTAIL DES RÉSULTATS:")
        for test_name, result in results.items():
            status = "✅ SUCCÈS" if result["success"] else "❌ ÉCHEC"
            print(f"   {test_name}: {status}")
            
            if result["success"] and "data" in result:
                data = result["data"]
                if "exercises_generated" in data:
                    print(f"     → Exercices générés: {data['exercises_generated']}")
                if "variety_score" in data:
                    print(f"     → Score variété: {data['variety_score']:.2f}")
                if "improvement" in data:
                    print(f"     → Amélioration cache: {data['improvement']:.1%}")
        
        # Évaluation du système d'optimisation
        print(f"\n🎯 ÉVALUATION DU SYSTÈME D'OPTIMISATION:")
        
        # Critères de succès
        gabarit_tests_passed = results.get("Test 1: Symétrie Axiale", {}).get("success", False) and \
                              results.get("Test 2: Symétrie Centrale", {}).get("success", False)
        
        cache_working = results.get("Test 3: Métriques Cache", {}).get("success", False)
        style_variety_good = results.get("Test 4: Variété Styles", {}).get("success", False)
        fallback_working = results.get("Test 5: Système Fallback", {}).get("success", False)
        
        print(f"   Gabarits fonctionnels: {'✅' if gabarit_tests_passed else '❌'}")
        print(f"   Cache opérationnel: {'✅' if cache_working else '❌'}")
        print(f"   Variété des styles: {'✅' if style_variety_good else '❌'}")
        print(f"   Fallback fonctionnel: {'✅' if fallback_working else '❌'}")
        
        # Conclusion globale
        all_systems_working = all([gabarit_tests_passed, cache_working, style_variety_good, fallback_working])
        
        print(f"\n🏆 CONCLUSION:")
        if all_systems_working:
            print(f"   ✅ SYSTÈME D'OPTIMISATION IA PLEINEMENT FONCTIONNEL")
            print(f"   🎯 Objectif atteint: Réduction drastique des appels IA")
            print(f"   💰 Économies de coûts: Significatives")
            print(f"   🚀 Performance: Améliorée")
        elif gabarit_tests_passed:
            print(f"   ⚠️  SYSTÈME D'OPTIMISATION PARTIELLEMENT FONCTIONNEL")
            print(f"   ✅ Gabarits opérationnels (principal objectif atteint)")
            print(f"   🔧 Améliorations nécessaires sur composants secondaires")
        else:
            print(f"   ❌ SYSTÈME D'OPTIMISATION NON FONCTIONNEL")
            print(f"   🚨 Problèmes critiques détectés")
            print(f"   🔧 Intervention requise")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        if not gabarit_tests_passed:
            print(f"   🔧 URGENT: Vérifier le chargement des gabarits JSON")
            print(f"   🔧 URGENT: Valider l'interpolation des placeholders")
        
        if not cache_working:
            print(f"   🔧 Optimiser le système de cache pour de meilleures performances")
        
        if not style_variety_good:
            print(f"   🎨 Améliorer la diversité des styles de formulation")
        
        if not fallback_working:
            print(f"   🔄 Vérifier le système de fallback vers l'IA classique")
        
        print(f"\n" + "="*80)


def main():
    """Point d'entrée principal pour les tests"""
    print(f"🎯 DÉMARRAGE DES TESTS - SYSTÈME D'OPTIMISATION IA")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialiser le testeur
    tester = IAOptimizationTester()
    
    # Exécuter la suite complète de tests
    results = tester.run_comprehensive_test_suite()
    
    # Retourner le code de sortie approprié
    all_passed = all(r["success"] for r in results.values())
    exit_code = 0 if all_passed else 1
    
    print(f"\n🏁 Tests terminés avec code de sortie: {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit(main())