"""
Tests pour build_enonce_html() dans backend/routes/exercises_routes.py

Run with: pytest -q backend/tests/test_build_enonce_html.py
"""
import pytest
from backend.routes.exercises_routes import build_enonce_html


class TestBuildEnonceHtml:
    """Tests pour la fonction build_enonce_html()"""

    def test_simple_text_wrapped_in_p(self):
        """
        Cas 1: enonce="Texte simple" => doit contenir "<p>Texte simple</p>"
        """
        enonce = "Texte simple"
        result = build_enonce_html(enonce)
        
        # Doit contenir <p>Texte simple</p>
        assert "<p>Texte simple</p>" in result
        # Doit être dans le wrapper exercise-enonce
        assert result.startswith("<div class='exercise-enonce'>")
        assert result.endswith("</div>")

    def test_table_not_wrapped_in_p(self):
        """
        Cas 2: enonce="<table>...</table>" => ne doit PAS contenir "<p><table", 
        et doit contenir la table telle quelle
        """
        enonce = "<table><tr><td>Cellule 1</td><td>Cellule 2</td></tr></table>"
        result = build_enonce_html(enonce)
        
        # Ne doit PAS contenir "<p><table"
        assert "<p><table" not in result
        # Doit contenir la table telle quelle
        assert "<table><tr><td>Cellule 1</td><td>Cellule 2</td></tr></table>" in result
        # Doit être dans le wrapper exercise-enonce
        assert result.startswith("<div class='exercise-enonce'>")
        assert result.endswith("</div>")

    def test_existing_p_not_doubled(self):
        """
        Cas 3: enonce="<p>Déjà en paragraphe</p>" => ne doit pas doubler inutilement 
        les <p> (au minimum: pas de "<p><p>")
        """
        enonce = "<p>Déjà en paragraphe</p>"
        result = build_enonce_html(enonce)
        
        # Ne doit PAS contenir "<p><p>"
        assert "<p><p>" not in result
        # Doit contenir le paragraphe original
        assert "<p>Déjà en paragraphe</p>" in result
        # Doit être dans le wrapper exercise-enonce
        assert result.startswith("<div class='exercise-enonce'>")
        assert result.endswith("</div>")

    def test_div_not_wrapped_in_p(self):
        """Test supplémentaire: div ne doit pas être enveloppé dans <p>"""
        enonce = "<div>Contenu dans une div</div>"
        result = build_enonce_html(enonce)
        
        assert "<p><div" not in result
        assert "<div>Contenu dans une div</div>" in result

    def test_ul_not_wrapped_in_p(self):
        """Test supplémentaire: liste ul ne doit pas être enveloppée dans <p>"""
        enonce = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = build_enonce_html(enonce)
        
        assert "<p><ul" not in result
        assert "<ul><li>Item 1</li><li>Item 2</li></ul>" in result

    def test_svg_with_figure(self):
        """Test avec SVG: doit toujours avoir le wrapper exercise-figure"""
        enonce = "Texte simple"
        svg = "<svg><circle r='10'/></svg>"
        result = build_enonce_html(enonce, svg)
        
        assert "<p>Texte simple</p>" in result
        assert "<div class='exercise-figure'><svg><circle r='10'/></svg></div>" in result

    def test_table_with_svg(self):
        """Test table avec SVG: table non enveloppée, SVG dans exercise-figure"""
        enonce = "<table><tr><td>Test</td></tr></table>"
        svg = "<svg><rect width='10' height='10'/></svg>"
        result = build_enonce_html(enonce, svg)
        
        assert "<p><table" not in result
        assert "<table><tr><td>Test</td></tr></table>" in result
        assert "<div class='exercise-figure'><svg><rect width='10' height='10'/></svg></div>" in result

