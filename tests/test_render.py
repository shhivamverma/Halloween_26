"""Self-contained HTML ofrenda altar page rendering tests."""

from app.render import render_ofrenda


def test_render_contains_all_content(sample_ofrenda):
    """Rendered HTML contains name, offerings, songs, and objects."""
    html = render_ofrenda(sample_ofrenda)
    for s in ("Rosa", "tamales", "Cielito Lindo", "cafe de olla", "her rosary"):
        assert s in html


def test_html_escapes_user_input(sample_ofrenda):
    """User input must be strictly escaped by Jinja2 to prevent XSS."""
    sample_ofrenda.story_text = "<script>alert(1)</script>"
    html = render_ofrenda(sample_ofrenda)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_no_external_urls(sample_ofrenda):
    """Rendered page must have no http:// or https:// external links or resources."""
    html = render_ofrenda(sample_ofrenda)
    assert "http://" not in html and "https://" not in html
    assert "<link " not in html and 'src="http' not in html


def test_photo_embedded_as_data_uri(sample_ofrenda_with_photo):
    """Portrait photo is embedded as a self-contained base64 data URI."""
    html = render_ofrenda(sample_ofrenda_with_photo)
    assert "data:image/" in html


def test_lang_attribute(sample_ofrenda):
    """HTML lang attribute matches configured ofrenda language."""
    html = render_ofrenda(sample_ofrenda)
    assert 'lang="es"' in html


def test_renders_without_optional_fields(minimal_ofrenda):
    """Render works gracefully with only required fields (e.g. name only)."""
    html = render_ofrenda(minimal_ofrenda)
    assert "Rosa" in html
    assert 'lang="en"' in html


def test_page_and_download_endpoints(client, created_id):
    """Verify /api/ofrendas/{id}/page and /download endpoints return valid HTML."""
    r_page = client.get(f"/api/ofrendas/{created_id}/page")
    assert r_page.status_code == 200
    assert "text/html" in r_page.headers["content-type"]
    assert "Rosa Hernandez" in r_page.text

    r_down = client.get(f"/api/ofrendas/{created_id}/download")
    assert r_down.status_code == 200
    assert "attachment;" in r_down.headers.get("content-disposition", "")
    assert "Rosa_Hernandez_ofrenda.html" in r_down.headers.get("content-disposition", "")
