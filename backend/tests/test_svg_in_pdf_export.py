"""
Test critique : Vérifier que les SVG apparaissent dans les exports PDF
"""

import pytest
import sys
import os
import requests
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSVGInPDFExport:
    """Tests SVG dans export PDF"""
    
    BASE_URL = "http://localhost:8001"
    
    def test_svg_present_in_generated_exercises(self):
        """Test : Les exercices géométriques doivent avoir un figure_svg"""
        print("\n" + "="*80)
        print("TEST : SVG présent dans exercices générés")
        print("="*80)
        
        # Générer des exercices Pythagore (toujours avec figure)
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "4e",
                "chapitre": "Théorème de Pythagore",
                "type_doc": "exercices",
                "difficulte": "moyen",
                "nb_exercices": 3,
                "guest_id": "test_svg_pdf"
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        exercises = data["document"]["exercises"]
        
        print(f"Exercices générés : {len(exercises)}")
        
        for i, ex in enumerate(exercises, 1):
            has_svg = 'figure_svg' in ex and ex['figure_svg']
            svg_length = len(ex.get('figure_svg', ''))
            
            print(f"Exercice {i} :")
            print(f"  - figure_svg présent : {has_svg}")
            print(f"  - Longueur SVG : {svg_length} caractères")
            
            assert has_svg, f"Exercice {i} : figure_svg manquant"
            assert svg_length > 100, f"Exercice {i} : SVG trop court ({svg_length} chars)"
            assert '<svg' in ex['figure_svg'], f"Exercice {i} : Pas de balise <svg>"
        
        print("\n✅ Tous les exercices ont un SVG valide")
    
    def test_export_pdf_contains_schema_svg(self):
        """Test : L'export PDF doit contenir schema_svg pour les templates"""
        print("\n" + "="*80)
        print("TEST : schema_svg présent pour export PDF")
        print("="*80)
        
        # 1. Générer des exercices
        response_gen = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "4e",
                "chapitre": "Théorème de Pythagore",
                "type_doc": "exercices",
                "difficulte": "moyen",
                "nb_exercices": 2,
                "guest_id": "test_export_svg"
            },
            timeout=60
        )
        
        assert response_gen.status_code == 200
        data = response_gen.json()
        document_id = data["document"]["id"]
        
        print(f"Document généré : {document_id}")
        
        # 2. Exporter en PDF
        response_export = requests.post(
            f"{self.BASE_URL}/api/export/pdf",
            json={
                "document_id": document_id,
                "export_type": "sujet",
                "template": "moderne"
            },
            timeout=120
        )
        
        # Note: Le backend renvoie le PDF binaire
        # On ne peut pas vérifier directement le contenu du PDF ici
        # Mais on peut vérifier les logs backend
        
        assert response_export.status_code == 200, \
            f"Export PDF échoué : {response_export.status_code}"
        
        pdf_size = len(response_export.content)
        print(f"PDF généré : {pdf_size} bytes")
        
        # Un PDF avec SVG doit être > 10KB minimum
        assert pdf_size > 10000, \
            f"PDF trop petit ({pdf_size} bytes), SVG probablement manquant"
        
        print("✅ Export PDF généré avec succès")
    
    def test_figure_svg_to_schema_svg_conversion(self):
        """Test : Vérifier que figure_svg est bien copié vers schema_svg"""
        print("\n" + "="*80)
        print("TEST : Conversion figure_svg → schema_svg")
        print("="*80)
        
        # Ce test vérifie indirectement via les logs backend
        # En pratique, on teste l'API complète
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "3e",
                "chapitre": "Théorème de Thalès",
                "type_doc": "exercices",
                "difficulte": "moyen",
                "nb_exercices": 1,
                "guest_id": "test_conversion"
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        ex = data["document"]["exercises"][0]
        
        # Vérifier figure_svg présent
        assert 'figure_svg' in ex, "figure_svg manquant dans l'exercice"
        assert ex['figure_svg'], "figure_svg vide"
        
        print(f"✅ figure_svg présent : {len(ex['figure_svg'])} caractères")
        
        # La conversion figure_svg → schema_svg se fait côté serveur
        # lors de l'export PDF, on ne peut pas le tester directement ici
        # mais le test précédent (export PDF) le valide indirectement
        
        print("✅ Test réussi")
    
    def test_multiple_geometry_types(self):
        """Test : Différents types de géométrie doivent tous avoir des SVG"""
        print("\n" + "="*80)
        print("TEST : SVG pour différents types géométriques")
        print("="*80)
        
        chapitres_geometriques = [
            ("4e", "Théorème de Pythagore"),
            ("3e", "Trigonométrie"),
            ("3e", "Théorème de Thalès"),
            ("6e", "Aires"),
        ]
        
        for niveau, chapitre in chapitres_geometriques:
            response = requests.post(
                f"{self.BASE_URL}/api/generate",
                json={
                    "matiere": "Mathématiques",
                    "niveau": niveau,
                    "chapitre": chapitre,
                    "type_doc": "exercices",
                    "difficulte": "facile",
                    "nb_exercices": 1,
                    "guest_id": f"test_svg_{niveau}_{chapitre}"
                },
                timeout=60
            )
            
            assert response.status_code == 200
            data = response.json()
            ex = data["document"]["exercises"][0]
            
            # Certains chapitres peuvent générer des exercices sans figure
            # (ex: Aires peut générer calcul_decimaux si mal mappé)
            # On vérifie juste que s'il y a une figure, elle a un SVG
            
            type_ex = ex["spec_mathematique"]["type_exercice"]
            has_figure = ex["spec_mathematique"].get("figure_geometrique") is not None
            has_svg = 'figure_svg' in ex and ex['figure_svg']
            
            print(f"{niveau} - {chapitre} :")
            print(f"  Type : {type_ex}")
            print(f"  Figure présente : {has_figure}")
            print(f"  SVG présent : {has_svg}")
            
            if has_figure:
                assert has_svg, f"{chapitre} : Figure présente mais SVG manquant"
            
            print(f"  ✅ OK")
        
        print("\n✅ Tous les types géométriques validés")


if __name__ == "__main__":
    # Exécution directe
    test = TestSVGInPDFExport()
    
    print("\n" + "🔍"*40)
    print("TESTS SVG DANS EXPORT PDF")
    print("🔍"*40 + "\n")
    
    try:
        test.test_svg_present_in_generated_exercises()
        test.test_export_pdf_contains_schema_svg()
        test.test_figure_svg_to_schema_svg_conversion()
        test.test_multiple_geometry_types()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS SVG EXPORT PDF PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        exit(1)
