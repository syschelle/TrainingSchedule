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
