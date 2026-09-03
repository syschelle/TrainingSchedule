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
    assert 'src="calendar.js?v=0.3.2"' in html
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
    assert '.map((block) => `${Number(block.week || 1)}::${block.day}::${String(block.trainer || "").trim()}`)' in overview
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


def test_planning_validation_page_is_removed_from_user_interface() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'id="validation-page"' not in html
    assert 'id="validationNavButton"' not in html
    assert 'id="validationCount"' not in html
    assert 'id="warnings"' not in html
    assert 'Planungsprüfung' not in html
    assert 'function renderWarnings()' not in javascript


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
    assert 'Seite 1 · Uebersicht' not in javascript
    overview_section = javascript.split('pdf-preview-overview-sheet', 1)[1].split('${projectOverviewMeta()}', 1)[0]
    assert 'Kunde: ${escapeHtml(customer)}' in overview_section
    assert 'Standort: ${escapeHtml(location)}' in overview_section
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


def test_trainer_editor_is_compact_and_keyboard_friendly() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert 'class="trainer-name-input"' in javascript
    assert 'class="trainer-add-button"' in javascript
    assert 'handleTrainerKeydown' in javascript
    assert 'addTrainer(true)' in javascript
    assert '.trainer-list {' in css
    assert 'flex-wrap: wrap;' in css
    assert '.trainer-row {' in css
    assert 'flex: 0 1 230px;' in css

def test_add_week_button_uses_correct_german_umlaut() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "Woche hinzufügen" in javascript
    assert "Woche hinzufuegen" not in javascript

def test_arrival_calendar_tile_uses_compact_display_title_only() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'block.type === "arrival" ? "Anreise" : String(block.title || "").trim()' in javascript
    assert 'monday_arrival_label: "Anreise / Eintreffen der Teilnehmer"' in javascript


def test_calendar_hides_participant_group_name_but_keeps_generated_split_group() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "function calendarDisplayParts(block)" in javascript
    display_helper = javascript.split("function calendarDisplayParts(block)", 1)[1].split("function calendarDisplayTitle", 1)[0]
    assert "participant_groups" in display_helper
    assert 'const marker = ` - ${groupName}`;' in display_helper
    assert 'suffix.startsWith("Gruppe ")' in display_helper
    assert 'groupLabel = suffix.startsWith("Gruppe ") ? suffix : "";' in display_helper
    assert '(project.topics || []).find((item) => item.id === (block.source_topic_id || block.topic_id))' in display_helper
    block_html = javascript.split("function blockHtml", 1)[1].split("function startBlockResize", 1)[0]
    assert "const displayParts = calendarDisplayParts(block);" in block_html


def test_training_calendar_tile_uses_three_line_title_group_and_time_structure() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    block_html = javascript.split("function blockHtml", 1)[1].split("function startBlockResize", 1)[0]
    assert 'class="block-title">${escapeHtml(displayTitle)}</strong>' in block_html
    assert 'class="block-group">${escapeHtml(displayParts.groupLabel)}</span>' in block_html
    assert 'class="block-meta">${block.start}-${block.end} · ${formatHours(blockDuration)}</span>' in block_html
    assert block_html.index('class="block-title"') < block_html.index('class="block-group"') < block_html.index('class="block-meta"')
    assert ".calendar-block .block-title" in css
    assert ".calendar-block .block-group" in css
    assert "white-space: nowrap;" in css



def test_empty_training_weeks_are_hidden_from_calendar_and_preview() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'function scheduledWeeks()' in javascript
    scheduled = javascript.split('function scheduledWeeks()', 1)[1].split('function plannedWeeks()', 1)[0]
    assert '.filter((block) => block.type === "training")' in scheduled
    planned = javascript.split('function plannedWeeks()', 1)[1].split('function hideEmptyTransientWeek', 1)[0]
    assert '...scheduledWeeks()' in planned
    assert '...transientManualWeeks' in planned
    assert 'project.manual_weeks' not in planned
    preview = javascript.split('function renderPreview()', 1)[1].split('function normalizeProjectState()', 1)[0]
    assert '${scheduledWeeks().map((week)' in preview
    assert 'Wochen ohne Schulungsblöcke werden automatisch ausgeblendet.' in javascript
    assert 'hideEmptyTransientWeek(previousWeek);' in javascript


def test_short_calendar_blocks_use_compact_non_clipping_layout() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert 'interactive && blockDuration <= 30 ? " is-compact" : ""' in javascript
    assert 'title="${escapeHtml(blockTooltip)}"' in javascript
    assert ".calendar-block.is-compact .block-actions" in css
    assert "grid-template-columns: repeat(2, 17px);" in css
    assert ".calendar-block.is-compact .icon" in css
    assert "height: 17px;" in css
    assert ".calendar-block.is-compact .block-content > span" in css
    assert ".calendar-block.is-compact .block-title" in css
    assert "white-space: nowrap;" in css
    assert "text-overflow: ellipsis;" in css


def test_training_blocks_support_live_quarter_hour_resize_and_hour_duration_label() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert 'class="calendar-resize-handle resize-start"' in javascript
    assert 'class="calendar-resize-handle resize-end"' in javascript
    assert "function startBlockResize(event, id, edge)" in javascript
    assert "function resizeBlockPointerMove(event)" in javascript
    assert "function finishBlockResize(event)" in javascript
    assert "snapMinutes(rawMinutes)" in javascript
    assert "calendarSnapMinutes = 15" in javascript
    assert 'class="block-meta">${block.start}-${block.end} · ${formatHours(blockDuration)}' in javascript
    assert "function formatHours(minutes)" in javascript
    assert "· ${block.type}" not in javascript.split("function blockHtml", 1)[1].split("function addManualWeek", 1)[0]
    assert ".calendar-resize-handle {" in css
    assert "cursor: ns-resize;" in css
    assert "touch-action: none;" in css


def test_calendar_block_typography_scales_smoothly_with_live_height() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert "function calendarBlockTypography(height)" in javascript
    assert "function applyCalendarBlockTypography(element, height)" in javascript
    assert '--calendar-title-size:${typography.titleSize.toFixed(3)}rem' in javascript
    assert '--calendar-meta-size:${typography.metaSize.toFixed(3)}rem' in javascript
    resize_section = javascript.split("function updateResizedBlockElement", 1)[1].split("function finishBlockResize", 1)[0]
    assert "applyCalendarBlockTypography(element, cappedHeight);" in resize_section
    assert "font-size: var(--calendar-title-size" in css
    assert "font-size: var(--calendar-meta-size" in css
    assert "transition: font-size 90ms linear" in css


def test_training_content_editor_exposes_split_toggle_and_syncs_it_to_planning():
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert "Schulungsblock teilen" in javascript
    assert 'data-key="split_enabled" type="checkbox"' in javascript
    assert 'split_enabled: Boolean(item.split_enabled)' in javascript
    assert 'topic.split_enabled = Boolean(content.split_enabled);' in javascript
    assert 'event.target.type === "checkbox"' in javascript
    assert '.split-training-option {' in css


def test_header_shows_only_product_name_and_has_no_standard_data_reset() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert '<p id="headerProduct" class="eyebrow">DeepUnity PACS</p>' in html
    assert 'headerProduct.textContent = product.name;' in javascript
    assert 'Aktives Produkt: ${product.name}' not in javascript
    assert 'id="resetDemo"' not in html
    assert '>Standarddaten<' not in html
    assert '$("#resetDemo")' not in javascript


def test_v030_guided_workflow_has_six_header_steps_and_sticky_progress() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert 'id="workflowProgress"' in html
    assert 'const workflowSteps = [' in javascript
    for step in ['"product", label: "Produkt"', '"project", label: "Projekt"', '"people", label: "Personen"', '"training", label: "Schulungen"', '"time", label: "Zeiten"', '"review", label: "Prüfen"']:
        assert step in javascript
    assert ".topbar {" in css
    assert "position: sticky;" in css
    assert ".workflow-progress-step.current" in css


def test_v030_product_selection_is_first_and_catalog_editing_stays_separate() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    product_panel = html.split('data-workflow-panel="product"', 1)[1].split('data-workflow-panel="project"', 1)[0]
    assert "Produkt wählen" in product_panel
    assert 'id="workflow-product-options"' in product_panel
    assert 'data-workflow-product=' in javascript
    assert 'id="products-page"' in html
    assert "Produktdaten" in html


def test_v030_plan_is_created_only_from_review_and_navigation_preserves_calendar() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    review_panel = html.split('data-workflow-panel="review"', 1)[1].split('</section>', 1)[0]
    assert 'id="autoPlan"' in review_panel
    assert javascript.count('fetch("api/plan"') == 1
    assert "function markPlanningInputsChanged()" in javascript
    assert "if (project.blocks.length) planInputsDirty = true;" in javascript
    assert 'id="planDirtyBanner"' in html
    navigation = javascript.split("function navigatePage(page)", 1)[1].split("function contentCard", 1)[0]
    assert "createPlan(" not in navigation


def test_v030_workflow_uses_selection_not_topic_editing_for_project_schools() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    training_panel = html.split('data-workflow-panel="training"', 1)[1].split('data-workflow-panel="time"', 1)[0]
    assert 'id="training-selection"' in training_panel
    assert 'id="topic-list"' not in training_panel
    assert 'data-training-choice=' in javascript
    assert "function toggleTrainingContent(event)" in javascript
    assert 'id="contents-page"' in html


def test_v030_common_time_settings_are_visible_and_advanced_rules_are_disclosed() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    time_panel = html.split('data-workflow-panel="time"', 1)[1].split('data-workflow-panel="review"', 1)[0]
    assert 'id="settings-fields"' in time_panel
    assert "Weitere Planungsregeln" in time_panel
    assert 'id="advanced-settings-fields"' in time_panel
    assert "Montag · Anreise" in javascript
    assert "Donnerstag · Abreise" in javascript
    assert "Pause min." in javascript
    assert "Freitag für Schulung nutzen" in javascript


def test_v030_project_menu_separates_project_workflow_from_administration() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert '<p class="menu-section-label">Projekt</p>' in html
    assert '<p class="menu-section-label menu-section-spaced">Verwaltung</p>' in html
    project_part = html.split('<p class="menu-section-label">Projekt</p>', 1)[1].split('<p class="menu-section-label menu-section-spaced">Verwaltung</p>', 1)[0]
    admin_part = html.split('<p class="menu-section-label menu-section-spaced">Verwaltung</p>', 1)[1].split('</aside>', 1)[0]
    assert 'data-page="input"' in project_part
    assert 'data-page="plan"' in project_part
    assert 'data-page="validation"' not in project_part
    assert 'data-page="products"' in admin_part
    assert 'data-page="contents"' in admin_part


def test_v031_participant_count_typing_keeps_input_node_and_focus_stable() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    handler = javascript.split("function updateParticipantGroupField(event)", 1)[1].split("function currentProduct()", 1)[0]
    assert "renderPeopleWorkflow();" not in handler
    assert "renderPeopleSummary();" in handler
    assert "renderTrainingWorkflow();" in handler
    assert "function renderPeopleSummary()" in javascript


def test_v031_participant_count_input_supports_multi_digit_entry() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    editor = javascript.split("function groupEditor(group)", 1)[1].split("function productEditor()", 1)[0]
    assert 'data-key="participant_count" type="number" min="0" step="1" inputmode="numeric"' in editor


def test_v032_selection_duration_summary_is_removed() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "Basisdauer" not in javascript
    assert "Dauer der Auswahl" not in javascript
    assert 'Schulungsinhalte ausgewählt' in javascript


def test_v032_training_selection_supports_project_specific_duration_without_catalog_overwrite() -> None:
    javascript = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert 'Dauer im Projekt' in javascript
    assert 'data-project-training-duration=' in javascript
    assert 'function updateProjectTrainingDuration(event)' in javascript
    duration_handler = javascript.split('function updateProjectTrainingDuration(event)', 1)[1].split('function selectedTrainingContentIds()', 1)[0]
    assert 'renderTrainingWorkflow();' not in duration_handler
    assert 'item.duration_overridden = true;' in javascript
    assert 'topic.catalog_duration_minutes = Number(content.duration_minutes' in javascript
    assert 'if (!topic.duration_overridden) topic.duration_minutes = topic.catalog_duration_minutes;' in javascript


def test_v032_project_menu_has_no_planning_validation_entry() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert 'Planungsprüfung' not in html
    assert 'data-page="validation"' not in html
