#!/usr/bin/env python3
"""
Script de vérification de l'environnement PDF/SVG

Vérifie que toutes les dépendances nécessaires pour la génération
de PDF avec WeasyPrint sont correctement installées et fonctionnelles.

Usage:
    python check_pdf_env.py

Exit codes:
    0 - Environnement OK
    1 - Problèmes détectés
"""

import sys
import os
import tempfile
from pathlib import Path


def check_system_libs():
    """Vérifie la présence des bibliothèques système critiques."""
    print("🔍 Vérification des bibliothèques système...")
    
    try:
        import ctypes.util
        
        required_libs = {
            'pangoft2-1.0': 'libpangoft2-1.0-0',
            'pango-1.0': 'libpango-1.0-0',
            'cairo': 'libcairo2',
            'gdk_pixbuf-2.0': 'libgdk-pixbuf2.0-0'
        }
        
        all_ok = True
        for lib_name, package_name in required_libs.items():
            lib_path = ctypes.util.find_library(lib_name)
            if lib_path:
                print(f"  ✅ {lib_name} trouvée : {lib_path}")
            else:
                print(f"  ❌ {lib_name} introuvable (package: {package_name})")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"  ❌ Erreur lors de la vérification : {e}")
        return False


def check_python_packages():
    """Vérifie l'importation des packages Python critiques."""
    print("\n🐍 Vérification des packages Python...")
    
    # Packages critiques (doivent être présents)
    critical_packages = {
        'weasyprint': 'WeasyPrint',
        'PIL': 'Pillow',
        'jinja2': 'Jinja2'
    }
    
    # Packages optionnels (non bloquants)
    optional_packages = {
        'cairo': 'cairocffi (optionnel)'
    }
    
    all_ok = True
    
    # Vérifier les packages critiques
    for module_name, display_name in critical_packages.items():
        try:
            __import__(module_name)
            print(f"  ✅ {display_name} importé avec succès")
        except ImportError as e:
            print(f"  ❌ {display_name} : erreur d'import - {e}")
            all_ok = False
    
    # Vérifier les packages optionnels (ne pas échouer si absents)
    for module_name, display_name in optional_packages.items():
        try:
            __import__(module_name)
            print(f"  ✅ {display_name} importé avec succès")
        except ImportError:
            print(f"  ℹ️  {display_name} non disponible (pas critique)")
    
    return all_ok


def test_weasyprint_basic():
    """Test de génération PDF basique avec WeasyPrint."""
    print("\n🧪 Test de génération PDF avec WeasyPrint...")
    
    try:
        import weasyprint
        
        # HTML minimal
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #2563eb; }
            </style>
        </head>
        <body>
            <h1>Test WeasyPrint</h1>
            <p>Ce PDF a été généré avec succès pour vérifier l'environnement.</p>
            <p>Date : <strong>2025-01-XX</strong></p>
        </body>
        </html>
        """
        
        # Générer le PDF en mémoire
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        
        # Vérifier que le PDF n'est pas vide
        if len(pdf_bytes) > 0:
            print(f"  ✅ PDF généré avec succès ({len(pdf_bytes)} octets)")
            
            # Optionnel : sauvegarder dans /tmp pour inspection
            test_pdf_path = Path("/tmp/test_weasyprint.pdf")
            with open(test_pdf_path, "wb") as f:
                f.write(pdf_bytes)
            print(f"  📄 PDF de test sauvegardé : {test_pdf_path}")
            
            return True
        else:
            print("  ❌ PDF généré est vide")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur lors de la génération PDF : {e}")
        import traceback
        traceback.print_exc()
        return False


def test_svg_support():
    """Test du support SVG (utilisé pour les figures géométriques)."""
    print("\n🎨 Test du support SVG...")
    
    try:
        import weasyprint
        
        # HTML avec SVG inline
        html_with_svg = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body>
            <h2>Test SVG</h2>
            <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="40" stroke="black" stroke-width="2" fill="blue" />
            </svg>
        </body>
        </html>
        """
        
        pdf_bytes = weasyprint.HTML(string=html_with_svg).write_pdf()
        
        if len(pdf_bytes) > 0:
            print(f"  ✅ SVG rendu avec succès dans le PDF")
            return True
        else:
            print("  ❌ Échec du rendu SVG")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur lors du test SVG : {e}")
        return False


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("🔍 VÉRIFICATION ENVIRONNEMENT PDF/SVG")
    print("=" * 60)
    print()
    
    results = {
        "system_libs": check_system_libs(),
        "python_packages": check_python_packages(),
        "weasyprint_basic": test_weasyprint_basic(),
        "svg_support": test_svg_support()
    }
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ OK" if result else "❌ ÉCHEC"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        print("🎉 PDF_ENV_OK - Environnement entièrement fonctionnel !")
        return 0
    else:
        print("⚠️  PDF_ENV_PARTIAL - Certains tests ont échoué")
        print("\n💡 Actions recommandées :")
        print("   1. Exécuter : python3 /app/scripts/ensure_system_dependencies.py")
        print("   2. Redémarrer le backend : sudo supervisorctl restart backend")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Vérification interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
