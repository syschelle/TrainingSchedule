from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parents[1] / "app" / "static"


def test_frontend_assets_are_subpath_safe() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css?' in html
    assert 'src="app.js?' in html
    assert 'href="/styles.css' not in html
    assert 'src="/app.js' not in html


def test_frontend_api_calls_are_subpath_safe() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'fetch("/api/' not in javascript
    assert 'fetch(`/api/' not in javascript
    assert 'fetch("api/' in javascript or 'fetch(`api/' in javascript
