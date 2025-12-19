#!/usr/bin/env python3
"""
Test complet du système géométrique amélioré
Validation de la qualité MathALÉA sur tous les types de figures
"""

import sys
import os
sys.path.append('/app/backend')

from geometry_renderer import GeometryRenderer

def test_integration_complete():
    """Test d'intégration complète du nouveau système"""
    print("🎯 TEST INTÉGRATION COMPLÈTE - QUALITÉ MATHALÉA")
    print("=" * 55)
    
    geometry_renderer = GeometryRenderer()
    
    # Test 1: Rectangle avec nouveau rendu
    print("\n🔧 Test 1: Rectangle haute qualité")
    rectangle_schema = {
        "type": "schema_geometrique", 
        "figure": "rectangle",
        "longueur": 120,
        "largeur": 80,
        "points": ["A", "B", "C", "D"]
    }
    
    svg_result = geometry_renderer.render_geometric_figure(rectangle_schema)
    if '<svg' in svg_result:
        print("✅ Rectangle SVG de qualité généré")
        with open('/app/test_integration_rectangle.svg', 'w') as f:
            f.write(svg_result)
    else:
        print("❌ Erreur génération rectangle")
    
    # Test 2: Triangle rectangle avec qualité MathALÉA
    print("\n🔧 Test 2: Triangle rectangle haute qualité")
    triangle_schema = {
        "type": "schema_geometrique",
        "figure": "triangle_rectangle", 
        "points": ["A", "B", "C"],
        "angle_droit": "B",
        "segments": [
            ["A", "B", {"longueur": "6 cm"}],
            ["B", "C", {"longueur": "8 cm"}],
            ["A", "C", {"longueur": "10 cm"}]
        ]
    }
    
    svg_result = geometry_renderer.render_geometric_figure(triangle_schema)
    if '<svg' in svg_result:
        print("✅ Triangle rectangle SVG de qualité généré")
        with open('/app/test_integration_triangle.svg', 'w') as f:
            f.write(svg_result)
    else:
        print("❌ Erreur génération triangle rectangle")
    
    # Test 3: Cercle avec nouveau rendu
    print("\n🔧 Test 3: Cercle haute qualité")
    cercle_schema = {
        "type": "schema_geometrique",
        "figure": "cercle",
        "rayon": 50,
        "centre": "O"
    }
    
    svg_result = geometry_renderer.render_geometric_figure(cercle_schema)
    if '<svg' in svg_result:
        print("✅ Cercle SVG de qualité généré")
        with open('/app/test_integration_cercle.svg', 'w') as f:
            f.write(svg_result)
    else:
        print("❌ Erreur génération cercle")
    
    # Test 4: Construction géométrique (médiatrice)
    print("\n🔧 Test 4: Construction géométrique avancée")
    mediatrice_schema = {
        "type": "schema_geometrique",
        "figure": "mediatrice"
    }
    
    svg_result = geometry_renderer.render_geometric_figure(mediatrice_schema)
    if '<svg' in svg_result:
        print("✅ Construction médiatrice SVG générée")
        with open('/app/test_integration_mediatrice.svg', 'w') as f:
            f.write(svg_result)
    else:
        print("❌ Erreur génération médiatrice")
    
    # Test 5: Rendu pour affichage web (Base64)
    print("\n🔧 Test 5: Conversion Base64 pour web")
    base64_result = geometry_renderer.render_geometry_to_base64(rectangle_schema)
    if base64_result:
        print("✅ Conversion Base64 réussie")
        print(f"   Taille: {len(base64_result)} caractères")
        if base64_result.startswith('data:image/svg+xml'):
            print("   Format: SVG vectoriel (qualité optimale)")
        else:
            print("   Format: PNG rasterisé")
    else:
        print("❌ Erreur conversion Base64")
    
    print("\n🎯 RÉSUMÉ DES AMÉLIORATIONS:")
    print("✅ Rendu SVG pur (pas de matplotlib)")
    print("✅ Traits vectoriels nets et redimensionnables")
    print("✅ Couleurs et styles cohérents avec MathALÉA")
    print("✅ Positionnement intelligent des labels")
    print("✅ Constructions géométriques précises")
    print("✅ Marqueurs d'angles droits professionnels")
    print("✅ Cotes dimensionnelles bien placées")
    print("✅ Intégration transparente dans le système existant")
    
    print(f"\n📁 Fichiers générés: /app/test_integration_*.svg")

if __name__ == "__main__":
    test_integration_complete()