"""Tests for dashboard router and layout."""

def test_layout_base_css():
    from fastmvc_dashboards.layout import BASE_CSS
    assert "--bg:" in BASE_CSS
    assert "var(--text)" in BASE_CSS


def test_render_dashboard_page():
    from fastmvc_dashboards.layout import render_dashboard_page
    html = render_dashboard_page(
        title="Test",
        subtitle="Sub",
        body_html="<p>Hi</p>",
        accent_color="#22c55e",
    )
    assert "Test" in html
    assert "Sub" in html
    assert "<p>Hi</p>" in html
