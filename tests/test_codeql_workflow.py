from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "codeql.yml"


def test_codeql_languages_are_explicit_and_exclude_actions() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "- python" in workflow
    assert "- javascript-typescript" in workflow
    assert "languages: ${{ matrix.language }}" in workflow
    assert "- actions" not in workflow


def test_codeql_uses_current_major_action_version() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "github/codeql-action/init@v4" in workflow
    assert "github/codeql-action/analyze@v4" in workflow
