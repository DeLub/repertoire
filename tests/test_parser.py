"""Tests for parser module."""
import pytest

from repertoire.parser import extract_text_from_html, clean_text


class TestExtractTextFromHtml:
    """Test HTML text extraction."""
    
    def test_extract_simple_html(self):
        """Test extracting text from simple HTML."""
        html = """
        <article>
            <p>This is paragraph one with enough content.</p>
            <p>This is paragraph two with enough content too.</p>
        </article>
        """
        paragraphs = extract_text_from_html(html)
        
        assert len(paragraphs) == 2
        assert "paragraph one" in paragraphs[0]
    
    def test_ignore_short_paragraphs(self):
        """Test that short paragraphs are ignored."""
        html = """
        <article>
            <p>X</p>
            <p>This is a paragraph with enough content to not be filtered.</p>
            <p>Ok</p>
        </article>
        """
        paragraphs = extract_text_from_html(html)
        
        assert len(paragraphs) == 1
        assert "enough content" in paragraphs[0]
    
    def test_ignore_script_and_style(self):
        """Test that script and style content is ignored."""
        html = """
        <article>
            <p>Real content here with enough text.</p>
            <script>var x = "This should be ignored";</script>
            <style>.class { content: "ignore"; }</style>
            <p>More real content with enough text too.</p>
        </article>
        """
        paragraphs = extract_text_from_html(html)
        
        assert len(paragraphs) == 2
        assert not any("javascript" in p.lower() for p in paragraphs)
        assert not any("class" in p.lower() for p in paragraphs)
    
    def test_empty_html(self):
        """Test with empty HTML."""
        paragraphs = extract_text_from_html("<html></html>")
        assert len(paragraphs) == 0
    
    def test_malformed_html(self):
        """Test with malformed HTML."""
        html = "<article><p>Unclosed paragraph"
        paragraphs = extract_text_from_html(html)
        
        # Should handle gracefully
        assert isinstance(paragraphs, list)


class TestCleanText:
    """Test text cleaning."""
    
    def test_remove_extra_spaces(self):
        """Test removing extra spaces."""
        text = "This   has    multiple   spaces"
        cleaned = clean_text(text)
        
        assert "   " not in cleaned
        assert cleaned == "This has multiple spaces"
    
    def test_remove_html_entities(self):
        """Test removing HTML entities."""
        text = "Name &amp; title &quot;text&quot;"
        cleaned = clean_text(text)
        
        assert "&" in cleaned
        assert '"' in cleaned
    
    def test_strip_whitespace(self):
        """Test stripping whitespace."""
        text = "   centered text   "
        cleaned = clean_text(text)
        
        assert cleaned == "centered text"
