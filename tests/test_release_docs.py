from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_root_testing_and_security_docs_track_current_version():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    testing = (ROOT / "TESTING.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"v{version}" in testing
    assert f"v{version}" in security
    assert f"v{version}" in readme


def test_readme_links_release_quality_documents_from_repository_root():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "[Testing and release checks](TESTING.md)" in readme
    assert "[Security policy](SECURITY.md)" in readme
    assert not (ROOT / "docs" / "TESTING.md").exists()


def test_runtime_and_container_version_references_track_version_file():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
    server = (ROOT / "app" / "server" / "main.py").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    compose_images = (ROOT / "docker-compose.images.yml").read_text(encoding="utf-8")
    assert f'href="styles.css?v={version}"' in html
    assert f'src="calendar.js?v={version}"' in html
    assert f'src="app.js?v={version}"' in html
    assert f'v{version}' in html
    assert f'APP_VERSION", "{version}"' in server
    assert f'ARG APP_VERSION={version}' in dockerfile
    assert f'APP_VERSION: {version}' in compose
    assert f'schulungsplantool:{version}' in compose
    assert f'APP_VERSION: {version}' in compose_images
