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


def test_markdown_editor_is_present_and_calendar_empty_hint_is_removed() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'id="markdownEditorModal"' in html
    assert 'data-open-markdown' in javascript
    assert 'Schulungspunkte bearbeiten' in javascript
    assert 'Keine sichtbaren Bloecke.' not in javascript
    assert 'api/training-contents/${encodeURIComponent(item.id)}/markdown' in javascript


def test_markdown_preview_distinguishes_heading_levels_two_and_three() -> None:
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert ".markdown-preview h2 {" in css
    assert "color: var(--primary);" in css
    assert ".markdown-preview h3 {" in css
    assert "color: var(--success);" in css
    assert "maximal 5 gespeicherte Staende" in html


def test_default_customer_location_and_trainer_are_empty() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'customer_name: "",' in javascript
    assert 'location: "",' in javascript
    assert 'trainer: "",' in javascript
    assert "MHG Gelsenkirchen" not in javascript
    assert 'trainer: "S. Schelle"' not in javascript


def test_calendar_uses_start_date_and_dach_holiday_helper() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    calendar_js = (STATIC_DIR / "calendar.js").read_text(encoding="utf-8")
    assert 'src="calendar.js?v=0.2.29"' in html
    assert "TrainingCalendar.dateForCalendarDay(project.start_date, week, day)" in javascript
    assert 'class="calendar-date"' in javascript
    assert 'class="calendar-holiday"' in javascript
    assert 'add("DE", "Tag der Deutschen Einheit"' in calendar_js
    assert 'add("AT", "Nationalfeiertag"' in calendar_js
    assert 'add("CH", "Bundesfeier"' in calendar_js
    assert "Regionale Feiertage" in javascript
