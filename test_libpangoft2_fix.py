#!/usr/bin/env python3
"""
Test complet de validation du fix libpangoft2-1.0-0
Validation SPRINT P0 : Correction libpangoft2-1.0-0
"""

import sys
import subprocess
import requests
import tempfile
import os
from datetime import datetime

class LibPangoFT2FixTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.backend_url = "https://math-exercise-sync.preview.emergentagent.com"
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
        
        if details:
            print(f"   {details}")
        print()
    
    def test_system_dependencies(self):
        """Test 1: Exécuter ensure_system_dependencies.py"""
        print("🔍 TEST 1: Vérification des dépendances système")
        print("-" * 50)
        
        try:
            result = subprocess.run(
                [sys.executable, "/app/scripts/ensure_system_dependencies.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            output_lines = result.stdout.split('\n')
            
            # Vérifier que toutes les dépendances sont installées (5/5)
            dependencies_ok = "5/5 packages installés" in result.stdout
            all_deps_ready = "Toutes les dépendances système sont prêtes" in result.stdout
            
            if success and dependencies_ok and all_deps_ready:
                self.log_test("System Dependencies Check", True, 
                             "5/5 packages installés, toutes dépendances prêtes")
                return True
            else:
                self.log_test("System Dependencies Check", False, 
                             f"Exit code: {result.returncode}, Output: {result.stdout[:200]}")
                return False
                
        except Exception as e:
            self.log_test("System Dependencies Check", False, f"Exception: {e}")
            return False
    
    def test_pdf_environment_check(self):
        """Test 2: Exécuter check_pdf_env.py"""
        print("🔍 TEST 2: Vérification environnement PDF")
        print("-" * 50)
        
        try:
            result = subprocess.run(
                [sys.executable, "/app/backend/scripts/check_pdf_env.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            pdf_env_ok = "PDF_ENV_OK" in result.stdout
            
            if success and pdf_env_ok:
                self.log_test("PDF Environment Check", True, 
                             "PDF_ENV_OK retourné, exit code 0")
                return True
            else:
                self.log_test("PDF Environment Check", False, 
                             f"Exit code: {result.returncode}, PDF_ENV_OK: {pdf_env_ok}")
                return False
                
        except Exception as e:
            self.log_test("PDF Environment Check", False, f"Exception: {e}")
            return False
    
    def test_simple_pdf_generation(self):
        """Test 3: Test génération PDF simple"""
        print("🔍 TEST 3: Génération PDF simple avec weasyprint")
        print("-" * 50)
        
        try:
            # Import lazy de weasyprint
            from weasyprint import HTML
            
            html_content = """
            <!DOCTYPE html>
            <html>
            <head><title>Test libpangoft2 Fix</title></head>
            <body>
                <h1>Test de validation libpangoft2-1.0-0</h1>
                <p>Ce PDF teste la correction du problème libpangoft2.</p>
            </body>
            </html>
            """
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                pdf_path = tmp_file.name
            
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(pdf_path)
            
            # Vérification
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                
                # Vérifier que c'est un vrai PDF
                with open(pdf_path, 'rb') as f:
                    header = f.read(4)
                    is_valid_pdf = header == b'%PDF'
                
                os.unlink(pdf_path)  # Nettoyage
                
                if is_valid_pdf and file_size > 1000:
                    self.log_test("Simple PDF Generation", True, 
                                 f"PDF valide généré ({file_size} octets)")
                    return True
                else:
                    self.log_test("Simple PDF Generation", False, 
                                 f"PDF invalide ou trop petit ({file_size} octets)")
                    return False
            else:
                self.log_test("Simple PDF Generation", False, "Fichier PDF non créé")
                return False
                
        except OSError as e:
            if 'libpangoft2' in str(e):
                self.log_test("Simple PDF Generation", False, f"ERREUR libpangoft2: {e}")
                return False
            else:
                self.log_test("Simple PDF Generation", False, f"OSError: {e}")
                return False
        except Exception as e:
            self.log_test("Simple PDF Generation", False, f"Exception: {e}")
            return False
    
    def test_backend_api(self):
        """Test 4: Test API backend"""
        print("🔍 TEST 4: Test API backend")
        print("-" * 50)
        
        try:
            # Test endpoint exercise-types
            response = requests.get(
                f"{self.backend_url}/api/mathalea/exercise-types",
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Backend API", True, 
                             f"GET /api/mathalea/exercise-types retourne HTTP 200")
                return True
            else:
                self.log_test("Backend API", False, 
                             f"HTTP {response.status_code} au lieu de 200")
                return False
                
        except Exception as e:
            self.log_test("Backend API", False, f"Exception: {e}")
            return False
    
    def test_backend_logs(self):
        """Test 5: Vérification logs backend"""
        print("🔍 TEST 5: Vérification logs backend")
        print("-" * 50)
        
        try:
            # Vérifier les logs récents pour erreurs libpangoft2
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                recent_logs = result.stdout
                
                # Chercher les erreurs libpangoft2 récentes (ignorer les anciennes)
                lines = recent_logs.split('\n')
                recent_libpangoft2_errors = []
                
                # Considérer seulement les 20 dernières lignes comme "récentes"
                for line in lines[-20:]:
                    if 'libpangoft2' in line.lower() and 'error' in line.lower():
                        recent_libpangoft2_errors.append(line)
                
                if not recent_libpangoft2_errors:
                    self.log_test("Backend Logs Check", True, 
                                 "Aucune erreur libpangoft2 récente dans les logs")
                    return True
                else:
                    self.log_test("Backend Logs Check", False, 
                                 f"{len(recent_libpangoft2_errors)} erreurs libpangoft2 récentes")
                    return False
            else:
                self.log_test("Backend Logs Check", False, 
                             f"Impossible de lire les logs (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            self.log_test("Backend Logs Check", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("=" * 70)
        print("🧪 VALIDATION SPRINT P0 : Correction libpangoft2-1.0-0")
        print("=" * 70)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Exécuter tous les tests
        test_results = []
        test_results.append(self.test_system_dependencies())
        test_results.append(self.test_pdf_environment_check())
        test_results.append(self.test_simple_pdf_generation())
        test_results.append(self.test_backend_api())
        test_results.append(self.test_backend_logs())
        
        # Résumé
        print("=" * 70)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 70)
        print(f"Tests exécutés: {self.tests_run}")
        print(f"Tests réussis: {self.tests_passed}")
        print(f"Taux de réussite: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print()
        
        all_passed = all(test_results)
        
        if all_passed:
            print("🎉 SUCCÈS COMPLET - Correction libpangoft2-1.0-0 VALIDÉE")
            print("✅ Tous les scripts retournent exit code 0")
            print("✅ Aucune erreur libpangoft2 dans les logs récents")
            print("✅ Backend fonctionne normalement")
            print("✅ Génération PDF opérationnelle")
        else:
            print("❌ ÉCHEC - Problèmes détectés dans la correction")
            failed_tests = [i for i, result in enumerate(test_results) if not result]
            print(f"Tests échoués: {failed_tests}")
        
        return all_passed

if __name__ == "__main__":
    tester = LibPangoFT2FixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)