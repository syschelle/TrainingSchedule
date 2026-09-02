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
    assert 'src="calendar.js?v=0.2.37"' in html
    assert "TrainingCalendar.dateForCalendarDay(project.start_date, week, day)" in javascript
    assert 'class="calendar-date"' in javascript
    assert 'class="calendar-holiday"' in javascript
    assert 'add("DE", "Tag der Deutschen Einheit"' in calendar_js
    assert 'add("AT", "Nationalfeiertag"' in calendar_js
    assert 'add("CH", "Bundesfeier"' in calendar_js
    assert "Regionale Feiertage" in javascript


def test_plan_overview_uses_service_days_instead_of_break_metrics() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    overview = javascript.split("function renderOverview()", 1)[1].split("function topicSummary()", 1)[0]
    assert 'metricValue("Dienstleistungstage", formatServiceDays(serviceDays))' in overview
    assert 'metric("Pausen"' not in overview
    assert 'metric("Mittag"' not in overview
    assert 'metric("Anreise"' not in overview
    assert 'metric("Abreise"' not in overview
    assert '.filter((block) => block.type === "training")' in overview
    assert '.map((block) => `${Number(block.week || 1)}::${block.day}`)' in overview
    assert 'count === 1 ? "Tag" : "Tage"' in overview



def test_multi_trainer_calendar_and_project_state_controls_are_present() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'id="exportProject"' in html
    assert 'id="importProject"' in html
    assert 'id="projectImportInput"' in html
    assert "function calendarTrainers()" in javascript
    assert "function trainerEditor()" in javascript
    assert "block.trainer = calendarTrainers()[trainerIndex]" in javascript
    assert 'fetch("api/project/export"' in javascript
    assert 'fetch("api/project/import"' in javascript
    assert "Jeder Trainer besitzt pro Kalenderwoche eine eigene Wochenansicht" in javascript


def test_preview_documents_landscape_calendar_export() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "PDF-Vorschau" in javascript
    assert "Querformat" in javascript
    assert "dayHtml(day, start, height, week, trainer, trainerIndex, false)" in javascript


def test_project_import_is_on_input_page_not_plan_header() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    input_page = html.split('id="input-page"', 1)[1].split('id="products-page"', 1)[0]
    plan_page = html.split('id="plan-page"', 1)[1].split('id="markdownEditorModal"', 1)[0]
    assert 'id="importProject"' in input_page
    assert 'id="projectImportInput"' in input_page
    assert 'id="importProject"' not in plan_page
    assert 'id="exportProject"' in plan_page


def test_frontend_normalizes_manual_and_imported_block_starts_to_quarter_hours() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "const calendarSnapMinutes = 15;" in javascript
    assert "function snapTimeValue(value)" in javascript
    assert "function normalizeBlockStart(block)" in javascript
    assert "const startValue = snapTimeValue($(\"#blockEditorStart\").value);" in javascript
    assert "block.start = startValue;" in javascript
    assert "normalizeBlockStart(block);" in javascript


def test_validation_warnings_are_separate_from_calendar_page() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    plan_page = html.split('id="plan-page"', 1)[1].split('id="validation-page"', 1)[0]
    validation_page = html.split('id="validation-page"', 1)[1].split('id="markdownEditorModal"', 1)[0]
    assert 'id="warnings"' not in plan_page
    assert 'id="warnings"' in validation_page
    assert 'id="validationNavButton"' in html
    assert 'id="validationCount"' in validation_page
    assert 'Planungspruefung' in html
    assert 'nav.textContent = warnings.length ? `Planungspruefung (${warnings.length})`' in javascript


def test_calendar_block_editor_is_embedded_and_replaces_prompt_editing() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert 'id="blockEditorModal"' in html
    assert 'id="blockEditorTopic"' in html
    assert 'id="blockEditorBlockTitle"' in html
    assert 'id="blockEditorTrainer"' in html
    assert 'id="blockEditorStart"' in html
    assert 'id="blockEditorEnd"' in html
    assert 'id="blockEditorDuration"' in html
    assert 'id="blockEditorRoom"' in html
    assert 'id="blockEditorDescription"' in html
    assert 'id="blockEditorNotes"' in html
    edit_section = javascript.split("function editBlock(id)", 1)[1].split("function copyBlock(id)", 1)[0]
    assert "openBlockEditor(id);" in edit_section
    assert "prompt(" not in edit_section
    assert "function saveBlockEditor()" in javascript
    assert "block.start = startValue;" in javascript
    assert 'class="block-editor-modal"' in html
    assert ".block-editor-modal {" in css


def test_overview_and_preview_show_customer_location_and_overview_first_page() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'overviewMeta("Kunde", customer)' in javascript
    assert 'overviewMeta("Standort", location)' in javascript
    assert 'pdf-preview-overview-sheet' in javascript
    assert 'Seite 1 · Uebersicht' in javascript
    assert 'Kunde: ${escapeHtml(customer)}' in javascript
    assert 'Standort: ${escapeHtml(location)}' in javascript


def test_project_export_filename_contains_customer_location_product_date_and_time() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "function projectExportFilename(now = new Date())" in javascript
    assert 'safeFilenamePart(customer, "kunde")' in javascript
    assert 'safeFilenamePart(location, "standort")' in javascript
    assert 'safeFilenamePart(productName, "produkt")' in javascript
    assert '${date}_${time}.json' in javascript
    assert 'link.download = projectExportFilename();' in javascript


def test_input_and_plan_can_switch_without_creating_a_new_plan() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'id="showExistingPlan"' in html
    assert 'data-page="plan"' in html
    assert 'id="backToInput"' in html
    navigation = javascript.split("function navigatePage(page)", 1)[1].split("function contentCard", 1)[0]
    assert "createPlan(" not in navigation
    assert javascript.count('fetch("api/plan"') == 1
    assert 'fetch("api/plan"' in javascript.split("async function createPlan()", 1)[1].split("function renderPages()", 1)[0]
