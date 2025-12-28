"""
P0-B: Tests for HTML Safety Module

Run with: python -m pytest backend/tests/test_html_safety.py -v
"""

import pytest
from backend.utils.html_safety import (
    sanitize_text_html,
    is_html_safe,
    sanitize_template_html,
    trust_generator_svg
)


class TestSanitizeTextHtml:
    """Tests for sanitize_text_html function"""

    def test_script_tag_removed(self):
        """<script>alert(1)</script> => script absent"""
        html = "<p>Hello</p><script>alert(1)</script><p>World</p>"
        result = sanitize_text_html(html)
        assert "<script" not in result
        assert "alert(1)" not in result
        assert "<p>Hello</p>" in result
        assert "<p>World</p>" in result

    def test_img_onerror_removed(self):
        """<img src=x onerror=alert(1)> => onerror absent"""
        html = '<p>Test</p><img src=x onerror=alert(1)>'
        result = sanitize_text_html(html)
        assert "onerror" not in result
        assert "alert(1)" not in result
        # img is not in allowed tags, so it should be stripped
        assert "<img" not in result
        assert "<p>Test</p>" in result

    def test_javascript_href_removed(self):
        """<a href='javascript:alert(1)'>x</a> => javascript: absent"""
        html = "<a href='javascript:alert(1)'>Click me</a>"
        result = sanitize_text_html(html)
        assert "javascript:" not in result
        # <a> is not in allowed tags, so content should be preserved but tag stripped
        assert "Click me" in result

    def test_safe_content_preserved(self):
        """contenu safe (<p><strong>...</strong></p>) préservé"""
        html = "<p><strong>Important:</strong> This is <em>emphasized</em> text.</p>"
        result = sanitize_text_html(html)
        assert result == html

    def test_table_preserved(self):
        """Tables should be preserved"""
        html = "<table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>"
        result = sanitize_text_html(html)
        assert "<table>" in result
        assert "<tr>" in result
        assert "<td>" in result
        assert "Cell 1" in result

    def test_lists_preserved(self):
        """Lists should be preserved"""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = sanitize_text_html(html)
        assert "<ul>" in result
        assert "<li>" in result
        assert "Item 1" in result

    def test_class_attribute_preserved(self):
        """class attribute should be allowed"""
        html = '<p class="important">Text</p>'
        result = sanitize_text_html(html)
        assert 'class="important"' in result

    def test_style_attribute_removed(self):
        """style attribute should be removed (not in whitelist)"""
        html = '<p style="color:red">Text</p>'
        result = sanitize_text_html(html)
        assert 'style=' not in result
        assert '<p>Text</p>' in result or '<p >Text</p>' in result

    def test_onclick_removed(self):
        """onclick should be removed"""
        html = '<p onclick="alert(1)">Click</p>'
        result = sanitize_text_html(html)
        assert "onclick" not in result
        assert "alert(1)" not in result
        assert "<p>Click</p>" in result or "<p >Click</p>" in result

    def test_iframe_removed(self):
        """iframe should be removed"""
        html = '<p>Before</p><iframe src="evil.com"></iframe><p>After</p>'
        result = sanitize_text_html(html)
        assert "<iframe" not in result
        assert "evil.com" not in result
        assert "<p>Before</p>" in result
        assert "<p>After</p>" in result

    def test_empty_string(self):
        """Empty string should return empty string"""
        assert sanitize_text_html("") == ""
        assert sanitize_text_html(None) == ""

    def test_max_length_exceeded(self):
        """Should raise error for too-large input"""
        huge_html = "x" * 500_000
        with pytest.raises(ValueError, match="HTML too large"):
            sanitize_text_html(huge_html)


class TestIsHtmlSafe:
    """Tests for is_html_safe function"""

    def test_safe_html(self):
        """Safe HTML should return safe=True"""
        result = is_html_safe("<p>Hello World</p>")
        assert result["safe"] is True
        assert len(result["issues"]) == 0

    def test_script_detected(self):
        """Script tags should be detected"""
        result = is_html_safe("<script>alert(1)</script>")
        assert result["safe"] is False
        assert any("script" in issue.lower() for issue in result["issues"])

    def test_onclick_detected(self):
        """Event handlers should be detected"""
        result = is_html_safe('<p onclick="alert(1)">Test</p>')
        assert result["safe"] is False
        assert any("event" in issue.lower() or "onclick" in issue.lower()
                   for issue in result["issues"])

    def test_javascript_url_detected(self):
        """javascript: URLs should be detected"""
        result = is_html_safe('<a href="javascript:alert(1)">Link</a>')
        assert result["safe"] is False
        assert any("javascript" in issue.lower() for issue in result["issues"])

    def test_iframe_detected(self):
        """iframe should be detected as dangerous"""
        result = is_html_safe('<iframe src="evil.com"></iframe>')
        assert result["safe"] is False
        assert any("iframe" in issue.lower() or "dangerous" in issue.lower()
                   for issue in result["issues"])

    def test_sanitized_output_provided(self):
        """Should provide sanitized version"""
        result = is_html_safe("<p>Safe</p><script>bad</script>")
        assert "sanitized" in result
        assert "<script" not in result["sanitized"]


class TestSanitizeTemplateHtml:
    """Tests for sanitize_template_html function"""

    def test_both_templates_sanitized(self):
        """Both enonce and solution should be sanitized"""
        result = sanitize_template_html(
            enonce_html="<p>Enonce</p><script>bad</script>",
            solution_html="<p>Solution</p><script>evil</script>"
        )
        assert "<script" not in result["enonce_html"]
        assert "<script" not in result["solution_html"]
        assert "<p>Enonce</p>" in result["enonce_html"]
        assert "<p>Solution</p>" in result["solution_html"]


class TestTrustGeneratorSvg:
    """Tests for trust_generator_svg function"""

    def test_svg_passed_through(self):
        """SVG should be passed through unmodified"""
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg>'
        result = trust_generator_svg(svg)
        assert result == svg

    def test_svg_with_script_not_sanitized(self):
        """
        SVG from generator is trusted - even if it contains script-like content
        (This is intentional - generator SVG is trusted source)
        """
        # Note: In practice, generators don't produce script tags
        # This test documents the trust relationship
        svg = '<svg><script>alert(1)</script></svg>'
        result = trust_generator_svg(svg)
        assert result == svg  # Intentionally NOT sanitized


class TestComplexXssPayloads:
    """Tests for various XSS payloads"""

    def test_svg_onerror(self):
        """SVG onerror should be sanitized in text HTML"""
        html = '<svg onload="alert(1)"><circle cx="50" cy="50" r="40"/></svg>'
        result = sanitize_text_html(html)
        assert "onload" not in result
        # svg is not in allowed tags for text HTML
        assert "<svg" not in result

    def test_data_url(self):
        """data: URLs should not execute"""
        html = '<a href="data:text/html,<script>alert(1)</script>">Link</a>'
        result = sanitize_text_html(html)
        # <a> is not in allowed tags
        assert "data:" not in result or "<a" not in result

    def test_vbscript(self):
        """vbscript: should be neutralized"""
        html = '<a href="vbscript:msgbox(1)">Link</a>'
        result = sanitize_text_html(html)
        assert "vbscript:" not in result

    def test_nested_script(self):
        """Nested/obfuscated script should be removed"""
        html = '<p><sc<script>ript>alert(1)</sc</script>ript></p>'
        result = sanitize_text_html(html)
        # After sanitization, no script should remain
        assert "script" not in result.lower() or result == "<p>ript&gt;alert(1)ript&gt;</p>"

    def test_uppercase_tags(self):
        """Uppercase tags should also be handled"""
        html = '<SCRIPT>alert(1)</SCRIPT>'
        result = sanitize_text_html(html)
        assert "script" not in result.lower()
        assert "SCRIPT" not in result

    def test_mixed_case_onclick(self):
        """Mixed case event handlers should be handled"""
        html = '<p OnClick="alert(1)">Test</p>'
        result = sanitize_text_html(html)
        assert "onclick" not in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
