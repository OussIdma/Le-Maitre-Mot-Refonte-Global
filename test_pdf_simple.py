#!/usr/bin/env python3
"""
Test simple de génération PDF avec weasyprint
Vérifie qu'il n'y a pas d'erreur OSError libpangoft2
"""

import sys
import tempfile
import os
from pathlib import Path

def test_simple_pdf_generation():
    """Test simple de génération PDF"""
    print("🔍 Test de génération PDF simple avec weasyprint...")
    
    try:
        # Import lazy de weasyprint (comme dans server.py)
        from weasyprint import HTML, CSS
        print("✅ Import weasyprint réussi")
        
        # HTML simple pour test
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Test PDF</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 2cm; }
                h1 { color: #2c3e50; }
                .test-box { 
                    border: 2px solid #3498db; 
                    padding: 20px; 
                    margin: 20px 0;
                    background-color: #ecf0f1;
                }
            </style>
        </head>
        <body>
            <h1>Test de génération PDF</h1>
            <div class="test-box">
                <p>Ce PDF a été généré avec WeasyPrint pour tester l'environnement.</p>
                <p>Si vous voyez ce texte, la génération PDF fonctionne correctement.</p>
                <p><strong>Date du test:</strong> $(date)</p>
            </div>
            <p>✅ Test libpangoft2-1.0-0 : SUCCÈS</p>
        </body>
        </html>
        """
        
        # Génération du PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
            
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(pdf_path)
        
        # Vérification du fichier généré
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF généré avec succès: {pdf_path}")
            print(f"✅ Taille du fichier: {file_size} octets")
            
            # Vérification que c'est un vrai PDF
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                if header == b'%PDF':
                    print("✅ Format PDF valide détecté")
                else:
                    print("❌ Format PDF invalide")
                    return False
            
            # Nettoyage
            os.unlink(pdf_path)
            print("✅ Fichier temporaire nettoyé")
            
            return True
        else:
            print("❌ Fichier PDF non créé")
            return False
            
    except OSError as e:
        if 'libpangoft2' in str(e):
            print(f"❌ ERREUR libpangoft2 détectée: {e}")
            return False
        else:
            print(f"❌ Erreur OSError autre: {e}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la génération PDF: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST SIMPLE GÉNÉRATION PDF")
    print("=" * 60)
    
    success = test_simple_pdf_generation()
    
    if success:
        print("\n🎉 TEST RÉUSSI - Aucune erreur libpangoft2 détectée")
        sys.exit(0)
    else:
        print("\n❌ TEST ÉCHOUÉ - Problème de génération PDF")
        sys.exit(1)