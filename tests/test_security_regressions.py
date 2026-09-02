from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docx_untrusted_markdown_path_does_not_use_regular_expressions():
    source = (ROOT / "app/server/docx_content.py").read_text(encoding="utf-8")
    assert "import re" not in source
    assert "re." not in source


def test_security_dependency_pins_and_dev_requirements_are_not_duplicated():
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    development = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "python-multipart==0.0.32" in runtime
    assert "pypdf==6.16.2" in runtime
    assert "-r requirements.txt" not in development
