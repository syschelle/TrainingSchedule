const days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"];
const defaultSettings = {
  day_start: "08:30",
  day_end: "17:00",
  break_min_minutes: 20,
  break_max_minutes: 30,
  break_preferred_minutes: 25,
  lunch_minutes: 45,
  lunch_window_start: "12:00",
  lunch_window_end: "14:00",
  monday_arrival_enabled: true,
  monday_arrival_start: "08:30",
  monday_arrival_end: "10:00",
  monday_arrival_label: "Anreise / Eintreffen der Teilnehmer",
  thursday_departure_enabled: true,
  thursday_departure_start: "15:00",
  thursday_departure_end: "17:00",
  thursday_departure_label: "Abreise",
  friday_training_enabled: false
};

let activeTab = "overview";
let currentPage = "input";
let draggedBlockId = null;
let draggedBlockOffsetMinutes = 0;
let resizingBlock = null;
let cutBlockId = null;
const calendarHourHeight = 76;
const calendarSnapMinutes = 15;
let trainingContents = [];
let catalogProducts = [];
let selectedContentId = null;
let markdownEditorContentId = null;
let markdownPendingChangeType = "saved";
let blockEditorBlockId = null;
let transientManualWeeks = new Set();
let project = makeDefaultProject();
const workflowSteps = [
  { id: "product", label: "Produkt", number: 1 },
  { id: "project", label: "Projekt", number: 2 },
  { id: "people", label: "Personen", number: 3 },
  { id: "training", label: "Schulungen", number: 4 },
  { id: "time", label: "Zeiten", number: 5 },
  { id: "review", label: "Prüfen", number: 6 }
];
let currentWorkflowStep = "product";
let planInputsDirty = false;
let workflowErrors = {};

function makeDefaultProject() {
  return {
    title: "DeepUnity Schulungsplan",
    project_mode: "training_plan",
    customer_data_required: true,
    customer_name: "",
    location: "",
    product_id: "deepunity-pacs",
    trainer: "",
    trainers: [],
    participant_group: "",
    start_date: null,
    end_date: null,
    settings: { ...defaultSettings },
    product_lines: [
      {
        id: "deepunity-pacs",
        name: "DeepUnity PACS",
        description: "PACS-Schulungen fuer Radiologie, Keyuser, MFA, Kliniker, Webviewer und Administration.",
        participant_groups: [
          participantGroup("radiologen", "Radiologen", 0),
          participantGroup("radiologen-keyuser", "Radiologen Keyuser", 0),
          participantGroup("mfa", "MFA", 0),
          participantGroup("kliniker", "Kliniker", 0),
          participantGroup("webviewer", "Webviewer", 0),
          participantGroup("administratoren", "Administratoren", 0)
        ]
      }
    ],
    topics: [],
    blocks: [],
    manual_weeks: [],
    unscheduled_topics: [],
    warnings: []
  };
}

function topic(id, title, duration_minutes, priority, description, depends_on = null, product_id = "deepunity-pacs", background_color = "#eaf8f2") {
  return { id, product_id, participant_group_id: null, participant_group_ids: [], title, description, duration_minutes, catalog_duration_minutes: duration_minutes, duration_overridden: false, priority, preferred_day: null, preferred_order: null, depends_on, trainer: "", room: "", notes: "", split_enabled: false, background_color };
}

function participantGroup(id, name, participant_count, product_id = "deepunity-pacs") {
  return { id, product_id, name, participant_count, notes: "" };
}

const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", () => {
  $("#openMenu").addEventListener("click", openSideMenu);
  $("#autoPlan").addEventListener("click", createPlan);
  $("#backToInput").addEventListener("click", () => navigatePage("input"));
  $("#headerInputView").addEventListener("click", () => navigatePage("input"));
  $("#headerPlanView").addEventListener("click", () => {
    if (project.blocks.length) navigatePage("plan");
    else setWorkflowStep("review");
  });
  $("#reviewChangedInputs").addEventListener("click", () => setWorkflowStep("review"));
  $("#addTrainingContent").addEventListener("click", addTrainingContent);
  $("#closeMarkdownEditor").addEventListener("click", closeMarkdownEditor);
  $("#cancelMarkdownEditor").addEventListener("click", closeMarkdownEditor);
  $("#saveMarkdownEditor").addEventListener("click", saveMarkdownEditor);
  $("#exportMarkdownDocx").addEventListener("click", exportMarkdownDocx);
  $("#importMarkdownDocx").addEventListener("click", () => $("#markdownDocxInput").click());
  $("#markdownDocxInput").addEventListener("change", importMarkdownDocx);
  $("#markdownEditorInput").addEventListener("input", updateMarkdownPreview);
  document.querySelectorAll("[data-md-action]").forEach((button) => button.addEventListener("click", applyMarkdownAction));
  $("#markdownEditorModal").addEventListener("click", (event) => {
    if (event.target === $("#markdownEditorModal")) closeMarkdownEditor();
  });
  $("#closeBlockEditor").addEventListener("click", closeBlockEditor);
  $("#cancelBlockEditor").addEventListener("click", closeBlockEditor);
  $("#saveBlockEditor").addEventListener("click", saveBlockEditor);
  $("#blockEditorTopic").addEventListener("change", applyBlockEditorTopic);
  $("#blockEditorStart").addEventListener("change", syncBlockEditorEndFromDuration);
  $("#blockEditorDuration").addEventListener("change", syncBlockEditorEndFromDuration);
  $("#blockEditorEnd").addEventListener("change", syncBlockEditorDurationFromEnd);
  $("#blockEditorModal").addEventListener("click", (event) => {
    if (event.target === $("#blockEditorModal")) closeBlockEditor();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !$("#blockEditorModal").hidden) closeBlockEditor();
  });
  $("#exportProject").addEventListener("click", exportProjectState);
  $("#importProject").addEventListener("click", () => $("#projectImportInput").click());
  $("#projectImportInput").addEventListener("change", importProjectState);
  $("#exportPdf").addEventListener("click", () => downloadExport("pdf"));
  $("#exportXlsx").addEventListener("click", () => downloadExport("xlsx"));
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      activeTab = button.dataset.tab;
      renderTabs();
    });
  });
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.addEventListener("click", () => navigatePage(button.dataset.page));
  });
  document.querySelectorAll("[data-workflow-next]").forEach((button) => {
    button.addEventListener("click", () => advanceWorkflow(button.dataset.workflowNext));
  });
  document.querySelectorAll("[data-workflow-back]").forEach((button) => {
    button.addEventListener("click", () => setWorkflowStep(button.dataset.workflowBack));
  });
  render();
  loadProducts();
  loadTrainingContents();
});

function setStatus(text) {
  $("#status-line").textContent = text;
}

function render() {
  renderHeader();
  renderWorkflowProgress();
  renderProductWorkflow();
  renderBaseFields();
  renderPeopleWorkflow();
  renderTrainingWorkflow();
  renderSettingsFields();
  renderWorkflowReview();
  renderProductMenu();
  renderContentCatalog();
  renderTabs();
  renderPages();
  renderNavigation();
  renderWorkflowPanels();
  renderPlanDirtyState();
}

function renderHeader() {
  const product = currentProduct();
  const headerProduct = $("#headerProduct");
  const headerContext = $("#headerContext");
  if (headerProduct) headerProduct.textContent = product.name;
  const contextParts = [project.customer_name, project.location].filter(Boolean);
  if (headerContext) headerContext.textContent = contextParts.length ? contextParts.join(" · ") : "Neues Schulungsprojekt";
  const inputButton = $("#headerInputView");
  const planButton = $("#headerPlanView");
  if (inputButton) inputButton.classList.toggle("active", currentPage === "input");
  if (planButton) {
    planButton.classList.toggle("active", currentPage === "plan");
    planButton.disabled = !project.blocks.length;
    planButton.title = project.blocks.length ? "Vorhandenen Schulungsplan anzeigen" : "Noch kein Schulungsplan erstellt";
  }
  const existingPlanButton = $("#showExistingPlan");
  if (existingPlanButton) existingPlanButton.disabled = !project.blocks.length;
  const status = $("#planSyncStatus");
  if (status) {
    status.hidden = !project.blocks.length;
    status.textContent = planInputsDirty ? "● Eingaben geändert" : "✓ Plan aktuell";
    status.classList.toggle("is-dirty", planInputsDirty);
  }
}

function renderBaseFields() {
  const customerDisabled = project.project_mode === "service_calculation";
  const base = $("#base-fields");
  const advanced = $("#project-advanced-fields");
  if (!base || !advanced) return;
  base.innerHTML = [
    customerDisabled ? "" : field("customer_name", "Kunde", project.customer_name),
    customerDisabled ? "" : field("location", "Standort", project.location),
    field("start_date", "Startdatum", project.start_date || "", "date")
  ].join("");
  advanced.innerHTML = [
    field("title", "Schulungsbezeichnung", project.title, "text", true),
    modeSelector()
  ].join("");
  document.querySelectorAll("#base-fields input[data-field-name], #project-advanced-fields input[data-field-name]").forEach((input) => input.addEventListener("input", updateProjectField));
  const mode = $("#projectMode");
  if (mode) mode.addEventListener("change", updateProjectMode);
  applyWorkflowFieldErrors();
}

function trainerEditor() {
  const values = Array.isArray(project.trainers) && project.trainers.length ? project.trainers : [""];
  return `<div class="field field-wide trainer-editor">
    <div class="trainer-editor-heading">
      <span>Trainer</span>
    </div>
    <div class="trainer-list" role="group" aria-label="Trainer">
      ${values.map((name, index) => `<div class="trainer-row">
        <input class="trainer-name-input" data-trainer-index="${index}" data-original-trainer="${escapeHtml(name)}" value="${escapeHtml(name)}" placeholder="Trainername" autocomplete="off" spellcheck="false" aria-label="Trainer ${index + 1}">
        ${values.length > 1 || name ? `<button type="button" class="trainer-remove" onclick="deleteTrainer(${index})" title="Trainer entfernen" aria-label="Trainer ${index + 1} entfernen">×</button>` : ""}
      </div>`).join("")}
      <button type="button" id="addTrainer" class="trainer-add-button" title="Weiteren Trainer hinzufuegen"><span aria-hidden="true">＋</span> Trainer</button>
    </div>
  </div>`;
}

function renderPeopleWorkflow() {
  const trainerPanel = $("#trainer-workflow-panel");
  if (trainerPanel) {
    trainerPanel.innerHTML = trainerEditor();
    trainerPanel.querySelectorAll("input[data-trainer-index]").forEach((input) => {
      input.addEventListener("change", updateTrainerField);
      input.addEventListener("keydown", handleTrainerKeydown);
    });
    const addTrainerButton = $("#addTrainer");
    if (addTrainerButton) addTrainerButton.addEventListener("click", () => addTrainer(true));
  }
  renderParticipantGroups();
  renderPeopleSummary();
  applyWorkflowFieldErrors();
}

function renderPeopleSummary() {
  const summary = $("#people-summary");
  if (!summary) return;
  const trainers = activeTrainers();
  const groups = currentProduct().participant_groups || [];
  const participants = groups.reduce((sum, group) => sum + Math.max(0, Number(group.participant_count || 0)), 0);
  summary.innerHTML = `<strong>${trainers.length} ${trainers.length === 1 ? "Trainer" : "Trainer"}</strong><span>·</span><strong>${participants} Teilnehmer</strong><span>·</span><strong>${groups.length} ${groups.length === 1 ? "Gruppe" : "Gruppen"}</strong>`;
}

function activeTrainers() {
  return (project.trainers || []).map((name) => String(name || "").trim()).filter(Boolean);
}

function renderProductWorkflow() {
  const container = $("#workflow-product-options");
  if (!container) return;
  const products = project.product_lines || [];
  container.innerHTML = products.length ? products.map((item) => {
    const selected = item.id === project.product_id;
    return `<button type="button" class="product-choice ${selected ? "selected" : ""}" data-workflow-product="${escapeHtml(item.id)}" aria-pressed="${selected ? "true" : "false"}">
      <span class="product-choice-check" aria-hidden="true">${selected ? "✓" : ""}</span>
      <strong>${escapeHtml(item.name)}</strong>
      ${item.description ? `<span>${escapeHtml(item.description)}</span>` : ""}
    </button>`;
  }).join("") : `<div class="workflow-empty"><strong>Keine Produkte vorhanden.</strong><span>Lege zuerst ein Produkt unter Produktdaten an.</span></div>`;
  container.querySelectorAll("[data-workflow-product]").forEach((button) => {
    button.addEventListener("click", () => {
      const nextId = button.dataset.workflowProduct;
      if (nextId === project.product_id) return;
      selectProjectProduct(nextId);
      markPlanningInputsChanged();
      render();
    });
  });
}

function renderTrainingWorkflow() {
  const container = $("#training-selection");
  const summary = $("#training-summary");
  if (!container || !summary) return;
  const product = currentProduct();
  const items = trainingContents.filter((item) => item.product_id === product.id);
  const selectedIds = selectedTrainingContentIds();
  container.innerHTML = items.length ? items.map((item) => {
    const selected = selectedIds.has(item.id);
    const selectedTopic = projectTopicForContent(item.id);
    const groupNames = (item.participant_group_ids || []).map((id) => product.participant_groups.find((group) => group.id === id)?.name).filter(Boolean);
    const details = [
      `Standard ${formatDuration(Number(item.duration_minutes || 0))}`,
      groupNames.length ? groupNames.join(", ") : "Keine feste Teilnehmergruppe",
      item.max_participants ? `max. ${Number(item.max_participants)} Teilnehmer` : ""
    ].filter(Boolean);
    const projectDuration = Number(selectedTopic?.duration_minutes || item.duration_minutes || 60);
    return `<article class="training-choice ${selected ? "selected" : ""}">
      <label class="training-choice-select">
        <input type="checkbox" data-training-choice="${escapeHtml(item.id)}" ${selected ? "checked" : ""}>
        <span class="training-choice-body">
          <strong>${escapeHtml(item.title)}</strong>
          <span>${escapeHtml(details.join(" · "))}</span>
          ${item.split_enabled ? `<em>Geteilter Schulungsblock</em>` : ""}
        </span>
      </label>
      ${selected ? `<label class="project-training-duration">
        <span>Dauer im Projekt</span>
        <span class="project-duration-input"><input data-project-training-duration="${escapeHtml(item.id)}" type="number" min="5" step="5" inputmode="numeric" value="${projectDuration}" aria-label="Dauer im Projekt für ${escapeHtml(item.title)}"><span>min</span></span>
      </label>` : ""}
    </article>`;
  }).join("") : `<div class="workflow-empty"><strong>Keine Schulungsinhalte für ${escapeHtml(product.name)}.</strong><span>Schulungsinhalte werden in der Verwaltung gepflegt.</span></div>`;
  container.querySelectorAll("[data-training-choice]").forEach((input) => input.addEventListener("change", toggleTrainingContent));
  container.querySelectorAll("[data-project-training-duration]").forEach((input) => input.addEventListener("input", updateProjectTrainingDuration));
  const selectedCount = items.filter((item) => selectedIds.has(item.id)).length;
  summary.innerHTML = `<strong>${selectedCount} ${selectedCount === 1 ? "Schulungsinhalt ausgewählt" : "Schulungsinhalte ausgewählt"}</strong>`;
  applyWorkflowFieldErrors();
}

function projectTopicForContent(contentId) {
  return (project.topics || []).find((item) => (item.catalog_content_id || item.id) === contentId) || null;
}

function updateProjectTrainingDuration(event) {
  const item = projectTopicForContent(event.target.dataset.projectTrainingDuration);
  if (!item) return;
  const value = Number(event.target.value);
  if (!Number.isFinite(value) || value <= 0) return;
  item.duration_minutes = Math.round(value);
  item.duration_overridden = true;
  markPlanningInputsChanged();
  renderWorkflowReview();
}

function selectedTrainingContentIds() {
  const productId = currentProduct().id;
  return new Set((project.topics || []).filter((item) => (item.product_id || productId) === productId).map((item) => item.catalog_content_id || item.id));
}

function topicFromTrainingContent(content) {
  const productId = content.product_id || currentProduct().id;
  return {
    ...topic(content.id, content.title, Number(content.duration_minutes || 60), 3, content.goals || "", content.dependency_content_id || null, productId, content.background_color || "#eaf8f2"),
    catalog_content_id: content.id,
    catalog_duration_minutes: Number(content.duration_minutes || 60),
    duration_overridden: false,
    participant_group_ids: content.participant_group_ids || [],
    participants_per_session: content.max_participants ? Number(content.max_participants) : null,
    split_enabled: Boolean(content.split_enabled)
  };
}

function toggleTrainingContent(event) {
  const contentId = event.target.dataset.trainingChoice;
  const content = trainingContents.find((item) => item.id === contentId);
  if (!content) return;
  const selectedIds = selectedTrainingContentIds();
  if (event.target.checked && !selectedIds.has(contentId)) {
    project.topics = [...(project.topics || []), topicFromTrainingContent(content)];
  } else if (!event.target.checked) {
    project.topics = (project.topics || []).filter((item) => (item.catalog_content_id || item.id) !== contentId);
  }
  markPlanningInputsChanged();
  renderTrainingWorkflow();
  renderWorkflowProgress();
  renderWorkflowReview();
}

function syncTrainerLegacy() {
  const cleaned = (project.trainers || []).map((name) => String(name || "").trim()).filter(Boolean);
  project.trainer = cleaned[0] || "";
}

function updateTrainerField(event) {
  const index = Number(event.target.dataset.trainerIndex);
  const previous = event.target.dataset.originalTrainer || "";
  project.trainers = Array.isArray(project.trainers) ? [...project.trainers] : [];
  while (project.trainers.length <= index) project.trainers.push("");
  const next = event.target.value.trim();
  project.trainers[index] = next;
  if (previous && previous !== next) {
    project.blocks.forEach((block) => {
      if (block.trainer === previous) block.trainer = next;
    });
  }
  project.trainers = project.trainers.filter((name, position, all) => name || position === index).filter((name, position, all) => !name || all.indexOf(name) === position);
  syncTrainerLegacy();
  markPlanningInputsChanged();
  render();
}

function focusTrainerInput(index) {
  requestAnimationFrame(() => {
    const input = $(`#trainer-workflow-panel input[data-trainer-index="${index}"]`);
    if (input) {
      input.focus();
      input.select();
    }
  });
}

function addTrainer(focusNew = false) {
  project.trainers = Array.isArray(project.trainers) ? [...project.trainers] : [];
  let index = project.trainers.length - 1;
  if (!project.trainers.length || project.trainers[index].trim()) {
    project.trainers.push("");
    index = project.trainers.length - 1;
  }
  markPlanningInputsChanged();
  renderPeopleWorkflow();
  renderWorkflowProgress();
  renderWorkflowReview();
  if (focusNew) focusTrainerInput(index);
}

function handleTrainerKeydown(event) {
  if (event.key !== "Enter") return;
  event.preventDefault();
  const input = event.currentTarget;
  const index = Number(input.dataset.trainerIndex);
  updateTrainerField({ target: input });
  const current = String((project.trainers || [])[index] || "").trim();
  if (current) addTrainer(true);
}

function deleteTrainer(index) {
  project.trainers = Array.isArray(project.trainers) ? [...project.trainers] : [];
  const removed = project.trainers[index] || "";
  project.trainers.splice(index, 1);
  const replacement = project.trainers.find((name) => String(name || "").trim()) || "";
  if (removed) {
    project.blocks.forEach((block) => {
      if (block.trainer === removed) block.trainer = replacement;
    });
  }
  syncTrainerLegacy();
  markPlanningInputsChanged();
  validateAndRender();
}

function modeSelector() {
  return `<label class="field field-wide" data-field="project_mode">
    <span>Verwendungszweck</span>
    <select id="projectMode">
      <option value="training_plan" ${project.project_mode === "training_plan" ? "selected" : ""}>Schulungsplanung mit Kundendaten</option>
      <option value="service_calculation" ${project.project_mode === "service_calculation" ? "selected" : ""}>Dienstleistungskalkulation ohne Kundendaten</option>
    </select>
  </label>`;
}

function productEditor() {
  const product = currentProduct();
  return `<div class="product-editor field-wide">
    <div class="subheading">
      <h3>Produktdaten</h3>
    </div>
    <div class="field-grid embedded-grid">
      <label class="field field-wide"><span>Aktives Produkt</span><select id="productSelect">${project.product_lines.map((item) => `<option value="${escapeHtml(item.id)}" ${item.id === product.id ? "selected" : ""}>${escapeHtml(item.name)}</option>`).join("")}</select></label>
      <label class="field"><span>Produkt</span><input data-product="name" value="${escapeHtml(product.name)}"></label>
      <label class="field"><span>Produkt-ID</span><input data-product="id" value="${escapeHtml(product.id)}"></label>
      <label class="field field-wide"><span>Beschreibung</span><input data-product="description" value="${escapeHtml(product.description || "")}"></label>
    </div>
    <div class="new-product-box">
      <h3>Neues Produkt</h3>
      <label class="field"><span>Name</span><input id="newProductName" value="" placeholder="Produktname"></label>
      <label class="field"><span>Beschreibung</span><textarea id="newProductDescription" placeholder="Kurzbeschreibung"></textarea></label>
      <button type="button" id="addProduct" class="button button-primary">Produkt anlegen</button>
    </div>
  </div>`;
}

function groupEditor(group) {
  return `<div class="participant-row">
    <label><span>Gruppe</span><input data-group="${group.id}" data-key="name" value="${escapeHtml(group.name)}" aria-label="Teilnehmergruppe"></label>
    <label><span>Teilnehmer</span><input data-group="${group.id}" data-key="participant_count" type="number" min="0" step="1" inputmode="numeric" value="${Number(group.participant_count)}" aria-label="Teilnehmerzahl"></label>
    <button type="button" class="icon danger participant-remove" title="Löschen" onclick="deleteParticipantGroup('${group.id}')">×</button>
  </div>`;
}

function renderSettingsFields() {
  const s = project.settings;
  const container = $("#settings-fields");
  const advanced = $("#advanced-settings-fields");
  if (!container || !advanced) return;
  container.innerHTML = `
    <div class="time-setting-card">
      <div class="time-setting-heading"><strong>Schulungstag</strong><span>Montag bis Donnerstag</span></div>
      <div class="time-pair">${setting("day_start", "Beginn", s.day_start, "time")}${setting("day_end", "Ende", s.day_end, "time")}</div>
    </div>
    <div class="time-setting-card">
      <div class="time-setting-heading"><strong>Montag · Anreise</strong>${inlineToggle("monday_arrival_enabled", s.monday_arrival_enabled, "Aktiv")}</div>
      <div class="time-pair ${s.monday_arrival_enabled ? "" : "is-disabled"}">${setting("monday_arrival_start", "Von", s.monday_arrival_start, "time")}${setting("monday_arrival_end", "Bis", s.monday_arrival_end, "time")}</div>
    </div>
    <div class="time-setting-card">
      <div class="time-setting-heading"><strong>Donnerstag · Abreise</strong>${inlineToggle("thursday_departure_enabled", s.thursday_departure_enabled, "Aktiv")}</div>
      <div class="time-pair ${s.thursday_departure_enabled ? "" : "is-disabled"}">${setting("thursday_departure_start", "Von", s.thursday_departure_start, "time")}${setting("thursday_departure_end", "Bis", s.thursday_departure_end, "time")}</div>
    </div>
    <div class="time-setting-card">
      <div class="time-setting-heading"><strong>Pausen</strong><span>Standardwerte</span></div>
      <div class="time-pair">${numberSetting("break_preferred_minutes", "Zwischen Schulungen", s.break_preferred_minutes)}${numberSetting("lunch_minutes", "Mittagspause", s.lunch_minutes)}</div>
    </div>`;
  advanced.innerHTML = [
    numberSetting("break_min_minutes", "Pause min.", s.break_min_minutes),
    numberSetting("break_max_minutes", "Pause max.", s.break_max_minutes),
    setting("lunch_window_start", "Mittagsfenster von", s.lunch_window_start, "time"),
    setting("lunch_window_end", "Mittagsfenster bis", s.lunch_window_end, "time"),
    checkboxSetting("friday_training_enabled", "Freitag für Schulung nutzen", s.friday_training_enabled)
  ].join("");
  document.querySelectorAll("#settings-fields input, #advanced-settings-fields input").forEach((input) => input.addEventListener("input", updateSettingField));
  applyWorkflowFieldErrors();
}

function inlineToggle(name, value, label) {
  return `<label class="inline-toggle"><input data-setting-name="${name}" type="checkbox" ${value ? "checked" : ""}><span>${label}</span></label>`;
}

function field(name, label, value, type = "text", wide = false) {
  return `<label class="field ${wide ? "field-wide" : ""}" data-field="${name}">
    <span>${label}</span>
    <input data-field-name="${name}" type="${type}" value="${escapeHtml(value || "")}" spellcheck="false" autocomplete="off">
  </label>`;
}

function setting(name, label, value, type = "text") {
  return `<label class="field" data-field="${name}">
    <span>${label}</span>
    <input data-setting-name="${name}" type="${type}" ${type === "time" ? 'step="900"' : ""} value="${escapeHtml(value || "")}">
  </label>`;
}

function numberSetting(name, label, value) {
  return `<label class="field" data-field="${name}">
    <span>${label}</span>
    <input data-setting-name="${name}" type="number" min="0" step="5" value="${Number(value)}">
  </label>`;
}

function checkboxSetting(name, label, value) {
  return `<label class="field checkbox-field" data-field="${name}">
    <span>${label}</span>
    <input data-setting-name="${name}" type="checkbox" ${value ? "checked" : ""}>
  </label>`;
}

function markPlanningInputsChanged() {
  if (project.blocks.length) planInputsDirty = true;
  renderHeader();
  renderPlanDirtyState();
}

function renderWorkflowProgress() {
  const progress = $("#workflowProgress");
  if (!progress) return;
  progress.hidden = !["input", "plan"].includes(currentPage);
  const currentIndex = workflowSteps.findIndex((step) => step.id === currentWorkflowStep);
  progress.innerHTML = workflowSteps.map((step, index) => {
    const complete = workflowStepIsComplete(step.id);
    const current = currentPage === "input" && step.id === currentWorkflowStep;
    const stateClass = current ? "current" : complete ? "complete" : index < currentIndex ? "visited" : "pending";
    const marker = complete && !current ? "✓" : String(step.number);
    return `<button type="button" class="workflow-progress-step ${stateClass}" data-workflow-step="${step.id}" aria-current="${current ? "step" : "false"}">
      <span class="workflow-progress-marker">${marker}</span>
      <span class="workflow-progress-label">${step.label}</span>
    </button>${index < workflowSteps.length - 1 ? `<span class="workflow-progress-line ${complete ? "complete" : ""}" aria-hidden="true"></span>` : ""}`;
  }).join("");
  progress.querySelectorAll("[data-workflow-step]").forEach((button) => button.addEventListener("click", () => setWorkflowStep(button.dataset.workflowStep)));
}

function renderWorkflowPanels() {
  document.querySelectorAll("[data-workflow-panel]").forEach((panel) => {
    const active = panel.dataset.workflowPanel === currentWorkflowStep;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
    panel.querySelectorAll(".workflow-step-error").forEach((node) => node.remove());
    const message = workflowErrors[panel.dataset.workflowPanel];
    if (message && active) {
      const heading = panel.querySelector(".workflow-panel-heading");
      const error = document.createElement("div");
      error.className = "workflow-step-error";
      error.textContent = message;
      heading?.insertAdjacentElement("afterend", error);
    }
  });
}

function setWorkflowStep(step) {
  if (!workflowSteps.some((item) => item.id === step)) return;
  currentWorkflowStep = step;
  currentPage = "input";
  delete workflowErrors[step];
  renderHeader();
  renderPages();
  renderWorkflowProgress();
  renderWorkflowPanels();
  if (step === "review") renderWorkflowReview();
  requestAnimationFrame(() => document.querySelector(`[data-workflow-panel="${step}"]`)?.scrollIntoView({ block: "start", behavior: "smooth" }));
}

function advanceWorkflow(nextStep) {
  if (!validateWorkflowStep(currentWorkflowStep, true)) return;
  setWorkflowStep(nextStep);
}

function workflowStepIsComplete(step) {
  if (step === "product") return Boolean(project.product_id && (project.product_lines || []).some((item) => item.id === project.product_id));
  if (step === "project") {
    if (!project.start_date) return false;
    if (project.project_mode === "service_calculation") return true;
    return Boolean(String(project.customer_name || "").trim() && String(project.location || "").trim());
  }
  if (step === "people") {
    const participants = (currentProduct().participant_groups || []).reduce((sum, group) => sum + Math.max(0, Number(group.participant_count || 0)), 0);
    return activeTrainers().length > 0 && participants > 0;
  }
  if (step === "training") return selectedTrainingContentIds().size > 0;
  if (step === "time") {
    const start = toMinutes(project.settings.day_start || "00:00");
    const end = toMinutes(project.settings.day_end || "00:00");
    return Number.isFinite(start) && Number.isFinite(end) && start < end;
  }
  if (step === "review") return ["product", "project", "people", "training", "time"].every(workflowStepIsComplete);
  return false;
}

function validateWorkflowStep(step, focus = false) {
  let message = "";
  let focusSelector = "";
  if (step === "product" && !workflowStepIsComplete("product")) {
    message = "Bitte ein Produkt auswählen.";
    focusSelector = "[data-workflow-product]";
  } else if (step === "project" && !workflowStepIsComplete("project")) {
    if (!project.start_date) { message = "Bitte ein Startdatum auswählen."; focusSelector = '[data-field="start_date"] input'; }
    else if (project.project_mode !== "service_calculation" && !String(project.customer_name || "").trim()) { message = "Bitte den Kunden eintragen."; focusSelector = '[data-field="customer_name"] input'; }
    else { message = "Bitte den Standort eintragen."; focusSelector = '[data-field="location"] input'; }
  } else if (step === "people" && !workflowStepIsComplete("people")) {
    if (!activeTrainers().length) { message = "Bitte mindestens einen Trainer eintragen."; focusSelector = ".trainer-name-input"; }
    else { message = "Bitte Teilnehmerzahlen eintragen."; focusSelector = "#participant-group-panel input[type=number]"; }
  } else if (step === "training" && !workflowStepIsComplete("training")) {
    message = "Bitte mindestens einen Schulungsinhalt auswählen.";
    focusSelector = "#training-selection input";
  } else if (step === "time" && !workflowStepIsComplete("time")) {
    message = "Der Tagesbeginn muss vor dem Tagesende liegen.";
    focusSelector = '[data-setting-name="day_start"]';
  }
  if (message) {
    workflowErrors[step] = message;
    renderWorkflowPanels();
    if (focus) requestAnimationFrame(() => document.querySelector(focusSelector)?.focus());
    return false;
  }
  delete workflowErrors[step];
  return true;
}

function applyWorkflowFieldErrors() {
  document.querySelectorAll(".workflow-input-error").forEach((node) => node.classList.remove("workflow-input-error"));
}

function renderWorkflowReview() {
  const container = $("#workflow-review");
  if (!container) return;
  const product = currentProduct();
  const trainers = activeTrainers();
  const groups = product.participant_groups || [];
  const participants = groups.reduce((sum, group) => sum + Math.max(0, Number(group.participant_count || 0)), 0);
  const trainingCount = (project.topics || []).length;
  const ready = workflowStepIsComplete("review");
  const missing = workflowSteps.slice(0, 5).filter((step) => !workflowStepIsComplete(step.id));
  const dateLabel = project.start_date ? TrainingCalendar.formatGermanDate(TrainingCalendar.parseIsoDate(project.start_date)) : "—";
  container.innerHTML = `
    <div class="review-hero ${ready ? "ready" : "incomplete"}">
      <div><span>${ready ? "Bereit für die Planung" : "Noch nicht vollständig"}</span><strong>${escapeHtml(project.customer_name || product.name || "Schulungsprojekt")}</strong><small>${escapeHtml([project.location, product.name].filter(Boolean).join(" · "))}</small></div>
      <span class="review-status-icon" aria-hidden="true">${ready ? "✓" : "!"}</span>
    </div>
    <div class="review-grid">
      ${reviewCard("Projekt", [["Produkt", product.name], ["Start", dateLabel], ["Standort", project.location || "—"]], "project")}
      ${reviewCard("Personen", [["Trainer", trainers.length ? trainers.join(", ") : "—"], ["Teilnehmer", String(participants)], ["Gruppen", String(groups.length)]], "people")}
      ${reviewCard("Schulungen", [["Ausgewählt", `${trainingCount} ${trainingCount === 1 ? "Schulungsinhalt" : "Schulungsinhalte"}`]], "training")}
      ${reviewCard("Zeiten", [["Schulungstag", `${project.settings.day_start}–${project.settings.day_end}`], ["Anreise", project.settings.monday_arrival_enabled ? `${project.settings.monday_arrival_start}–${project.settings.monday_arrival_end}` : "Aus"], ["Abreise", project.settings.thursday_departure_enabled ? `${project.settings.thursday_departure_start}–${project.settings.thursday_departure_end}` : "Aus"]], "time")}
    </div>
    ${missing.length ? `<div class="review-missing">${missing.map((step) => `<button type="button" data-review-step="${step.id}">${step.label} ergänzen</button>`).join("")}</div>` : ""}
    ${planInputsDirty && project.blocks.length ? `<div class="review-replan-note"><strong>Vorhandener Kalender wird beim Neuerstellen ersetzt.</strong><span>Deine bisherigen Kalenderblöcke bleiben bis zum Klick auf „Plan erstellen“ unverändert.</span></div>` : ""}`;
  container.querySelectorAll("[data-review-step]").forEach((button) => button.addEventListener("click", () => setWorkflowStep(button.dataset.reviewStep)));
  const planButton = $("#autoPlan");
  if (planButton) {
    planButton.disabled = !ready;
    planButton.textContent = project.blocks.length ? "Plan neu erstellen" : "Plan erstellen";
  }
}

function reviewCard(title, rows, step) {
  return `<section class="review-card"><div class="review-card-heading"><h3>${escapeHtml(title)}</h3><button type="button" data-review-step="${step}">Bearbeiten</button></div>${rows.map(([label, value]) => `<div class="review-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}</section>`;
}

function renderPlanDirtyState() {
  const banner = $("#planDirtyBanner");
  if (banner) banner.hidden = !(project.blocks.length && planInputsDirty);
}

function updateProjectField(event) {
  project[event.target.dataset.fieldName] = event.target.value;
  delete workflowErrors[event.target.dataset.fieldName];
  markPlanningInputsChanged();
  renderHeader();
  renderWorkflowProgress();
  renderWorkflowReview();
  renderTabs();
}

function updateProjectMode(event) {
  project.project_mode = event.target.value;
  project.customer_data_required = project.project_mode !== "service_calculation";
  if (!project.customer_data_required) {
    project.customer_name = "";
    project.location = "";
  }
  markPlanningInputsChanged();
  render();
}

function updateProductField(event) {
  const product = currentProduct();
  const oldId = product.id;
  product[event.target.dataset.product] = event.target.value;
  if (event.target.dataset.product === "id") {
    project.product_id = product.id;
    product.participant_groups.forEach((group) => {
      group.product_id = product.id;
    });
    project.topics.forEach((item) => {
      if (item.product_id === oldId) item.product_id = product.id;
    });
  }
  renderTabs();
}

function updateProductSelection(event) {
  selectProjectProduct(event.target.value);
  markPlanningInputsChanged();
  render();
}

function selectProjectProduct(productId) {
  project.product_id = productId;
  ensureSelectedProductExists();
  const selectedProductId = currentProduct().id;
  project.topics = (project.topics || []).filter((item) => (item.product_id || selectedProductId) === selectedProductId);
  selectedContentId = firstContentForCurrentProduct()?.id || null;
}

function updateParticipantGroupField(event) {
  const group = currentProduct().participant_groups.find((candidate) => candidate.id === event.target.dataset.group);
  if (!group) return;
  const key = event.target.dataset.key;
  group[key] = key === "participant_count" ? Number(event.target.value) : event.target.value;
  project.participant_group = currentProduct().participant_groups.map((item) => item.name).join(", ");
  markPlanningInputsChanged();
  // Keep the active input node untouched while typing. Re-rendering the whole
  // people panel on every input event used to replace the number field and
  // therefore steal focus after each digit. Only dependent summaries/views
  // are refreshed here.
  renderPeopleSummary();
  renderTrainingWorkflow();
  renderWorkflowProgress();
  renderWorkflowReview();
  renderTabs();
}

function currentProduct() {
  if (!project.product_lines || !project.product_lines.length) {
    project.product_lines = [{ id: "deepunity-pacs", name: "DeepUnity PACS", description: "", participant_groups: [] }];
  }
  return project.product_lines.find((item) => item.id === project.product_id) || project.product_lines[0];
}

function addProductLine() {
  createProductLine();
}

function addParticipantGroup() {
  const product = currentProduct();
  product.participant_groups.push(participantGroup(crypto.randomUUID(), "Neue Gruppe", 0, product.id));
  project.participant_group = product.participant_groups.map((item) => item.name).join(", ");
  markPlanningInputsChanged();
  render();
}

function deleteParticipantGroup(id) {
  const product = currentProduct();
  product.participant_groups = product.participant_groups.filter((item) => item.id !== id);
  project.participant_group = product.participant_groups.map((item) => item.name).join(", ");
  markPlanningInputsChanged();
  render();
}

function updateSettingField(event) {
  const key = event.target.dataset.settingName;
  let value = event.target.type === "number" ? Number(event.target.value) : event.target.type === "checkbox" ? event.target.checked : event.target.value;
  if (event.target.type === "time" && (key === "day_start" || key.endsWith("_start"))) {
    value = snapTimeValue(value);
    event.target.value = value;
  }
  project.settings[key] = value;
  markPlanningInputsChanged();
  if (["monday_arrival_enabled", "thursday_departure_enabled"].includes(key)) renderSettingsFields();
  renderWorkflowProgress();
  renderWorkflowReview();
  renderTabs();
}

function renderTopics() {
  $("#topic-list").innerHTML = project.topics.map((item) => `
    <article class="topic">
      <input data-topic="${item.id}" data-key="title" value="${escapeHtml(item.title)}" aria-label="Titel">
      <input data-topic="${item.id}" data-key="participants_per_session" type="number" min="1" step="1" value="${item.participants_per_session || ""}" aria-label="Maximale Teilnehmer">
      <input data-topic="${item.id}" data-key="duration_minutes" type="number" min="5" step="5" value="${item.duration_minutes}" aria-label="Dauer">
      <select data-topic="${item.id}" data-key="priority" aria-label="Prioritaet">
        ${[1, 2, 3, 4, 5].map((n) => `<option value="${n}" ${Number(item.priority) === n ? "selected" : ""}>Prio ${n}</option>`).join("")}
      </select>
      <textarea data-topic="${item.id}" data-key="description" aria-label="Beschreibung">${escapeHtml(item.description || "")}</textarea>
      <button type="button" class="icon" title="Duplizieren" onclick="duplicateTopic('${item.id}')">⧉</button>
      <button type="button" class="icon danger" title="Loeschen" onclick="deleteTopic('${item.id}')">×</button>
    </article>
  `).join("");
  $("#topic-list").querySelectorAll("input, textarea, select").forEach((input) => input.addEventListener("change", updateTopic));
}

async function loadTrainingContents() {
  try {
    const response = await fetch("api/training-contents");
    if (!response.ok) throw new Error("catalog");
    trainingContents = (await response.json()).items || [];
    syncTopicsFromCatalog();
    selectedContentId = firstContentForCurrentProduct()?.id || selectedContentId;
    render();
  } catch (error) {
    trainingContents = [];
    const status = $("#catalog-status");
    if (status) status.textContent = "Katalog nicht erreichbar.";
  }
}

function syncTopicsFromCatalog() {
  const topicByTitle = new Map(project.topics.map((item) => [normalizeKey(item.title), item]));
  const topicByCatalogId = new Map(project.topics.map((item) => [item.catalog_content_id || item.id, item]));
  const topicByContentId = new Map();
  trainingContents.forEach((content) => {
    const topic = topicByCatalogId.get(content.id) || topicByTitle.get(normalizeKey(content.title));
    if (topic) topicByContentId.set(content.id, topic.id);
  });
  trainingContents.forEach((content) => {
    const topic = topicByCatalogId.get(content.id) || topicByTitle.get(normalizeKey(content.title));
    if (!topic) return;
    topic.catalog_content_id = content.id;
    topic.title = content.title;
    topic.catalog_duration_minutes = Number(content.duration_minutes || topic.catalog_duration_minutes || topic.duration_minutes || 60);
    if (!topic.duration_overridden) topic.duration_minutes = topic.catalog_duration_minutes;
    if (content.max_participants) topic.participants_per_session = Number(content.max_participants);
    topic.participant_group_ids = content.participant_group_ids || [];
    topic.participant_group_id = null;
    topic.split_enabled = Boolean(content.split_enabled);
    topic.background_color = content.background_color || "#eaf8f2";
    if (content.dependency_content_id && topicByContentId.has(content.dependency_content_id)) {
      topic.depends_on = topicByContentId.get(content.dependency_content_id);
    }
  });
}

function normalizeKey(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
}

async function loadProducts() {
  try {
    const response = await fetch("api/products");
    if (!response.ok) throw new Error("products");
    catalogProducts = (await response.json()).items || [];
    mergeCatalogProducts();
    render();
  } catch (error) {
    catalogProducts = project.product_lines || [];
  }
}

function mergeCatalogProducts() {
  catalogProducts.forEach((product) => {
    const existing = project.product_lines.find((item) => item.id === product.id);
    if (existing) {
      existing.name = product.name;
      existing.description = product.description || "";
    } else {
      project.product_lines.push({ id: product.id, name: product.name, description: product.description || "", participant_groups: [] });
    }
  });
  ensureSelectedProductExists();
}

function ensureSelectedProductExists() {
  if (!project.product_lines.some((item) => item.id === project.product_id)) {
    project.product_id = project.product_lines[0]?.id || "deepunity-pacs";
  }
}

function renderProductMenu() {
  const container = $("#product-menu-panel");
  if (!container) return;
  container.innerHTML = productEditor();
  container.querySelectorAll("[data-product]").forEach((input) => input.addEventListener("input", updateProductField));
  $("#productSelect").addEventListener("change", updateProductSelection);
  $("#addProduct").addEventListener("click", addProductLine);
}

function renderParticipantGroups() {
  const container = $("#participant-group-panel");
  const addButton = $("#addGroup");
  if (!container || !addButton) return;
  const product = currentProduct();
  container.innerHTML = product.participant_groups.length
    ? product.participant_groups.map(groupEditor).join("")
    : `<p class="muted">Noch keine Teilnehmergruppen fuer ${escapeHtml(product.name)}.</p>`;
  container.querySelectorAll("[data-group]").forEach((input) => input.addEventListener("input", updateParticipantGroupField));
  addButton.onclick = addParticipantGroup;
}

async function createProductLine() {
  const nameInput = $("#newProductName");
  const descriptionInput = $("#newProductDescription");
  const name = nameInput.value.trim();
  if (!name) {
    nameInput.focus();
    return;
  }
  const button = $("#addProduct");
  button.disabled = true;
  button.textContent = "Anlegen...";
  try {
    const response = await fetch("api/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: descriptionInput.value.trim() })
    });
    if (!response.ok) throw new Error("product");
    const product = await response.json();
    catalogProducts.push(product);
    project.product_lines.push({ ...product, participant_groups: [] });
    project.product_id = product.id;
    render();
  } catch (error) {
    button.disabled = false;
    button.textContent = "Fehler";
  }
}

function renderContentCatalog() {
  let linkList = $("#content-link-list");
  let detail = $("#content-detail");
  const status = $("#catalog-status");
  if (!linkList || !detail) {
    const legacyContainer = $("#content-catalog");
    if (!legacyContainer) return;
    legacyContainer.innerHTML = `<div class="content-manager"><nav id="content-link-list" class="content-link-list" aria-label="Schulungsinhalte"></nav><div id="content-detail" class="content-detail"></div></div>`;
    linkList = $("#content-link-list");
    detail = $("#content-detail");
  }
  const product = currentProduct();
  const items = trainingContents.filter((item) => item.product_id === product.id);
  if (!items.some((item) => item.id === selectedContentId)) {
    selectedContentId = items[0]?.id || null;
  }
  if (status) {
    status.textContent = items.length ? `${items.length} Inhalte fuer ${product.name}` : "Noch keine Inhalte fuer dieses Produkt.";
  }
  linkList.innerHTML = items.length ? items.map(contentLink).join("") : `<p class="muted">Keine Inhalte.</p>`;
  linkList.querySelectorAll("[data-content-link]").forEach((button) => button.addEventListener("click", selectTrainingContent));
  const item = items.find((candidate) => candidate.id === selectedContentId);
  detail.innerHTML = item ? contentCard(item) : `<p class="muted">Fuer ${escapeHtml(product.name)} sind noch keine Schulungsinhalte hinterlegt.</p>`;
  detail.querySelectorAll("input[data-content], textarea[data-content]").forEach((input) => input.addEventListener("input", updateTrainingContentDraft));
  detail.querySelectorAll("select[data-content]").forEach((input) => input.addEventListener("change", updateTrainingContentDraft));
  detail.querySelectorAll("button[data-save-content]").forEach((button) => button.addEventListener("click", saveTrainingContent));
  detail.querySelectorAll("button[data-open-markdown]").forEach((button) => button.addEventListener("click", openMarkdownEditor));
}

async function addTrainingContent() {
  const product = currentProduct();
  const title = prompt("Titel des neuen Schulungsinhalts", "Neuer Schulungsinhalt");
  if (!title || !title.trim()) return;
  const button = $("#addTrainingContent");
  button.disabled = true;
  button.textContent = "Anlegen...";
  try {
    const response = await fetch("api/training-contents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: product.id, title: title.trim() })
    });
    if (!response.ok) throw new Error("content");
    const content = await response.json();
    trainingContents.push(content);
    project.topics.push({ ...topic(content.id, content.title, content.duration_minutes || 60, 3, "", null, product.id, content.background_color || "#eaf8f2"), catalog_content_id: content.id });
    selectedContentId = content.id;
    currentPage = "contents";
    render();
  } catch (error) {
    button.disabled = false;
    button.textContent = "Fehler";
    window.setTimeout(() => {
      button.textContent = "Inhalt anlegen";
    }, 1200);
  }
}

function firstContentForCurrentProduct() {
  return trainingContents.find((item) => item.product_id === currentProduct().id);
}

function contentLink(item) {
  return `<button type="button" class="content-link ${item.id === selectedContentId ? "active" : ""}" data-content-link="${item.id}">
    <strong>${escapeHtml(item.title)}</strong>
    <span>${formatDuration(Number(item.duration_minutes || 0))}</span>
  </button>`;
}

function selectTrainingContent(event) {
  selectedContentId = event.currentTarget.dataset.contentLink;
  renderContentCatalog();
}

function openSideMenu() {
  $("#sideMenu").classList.toggle("open");
}

function closeSideMenu() {
  $("#sideMenu").classList.remove("open");
}

function navigatePage(page) {
  if (page === "plan" && !project.blocks.length) {
    closeSideMenu();
    setWorkflowStep("review");
    return;
  }
  currentPage = page;
  renderHeader();
  renderPages();
  renderWorkflowProgress();
  renderPlanDirtyState();
  closeSideMenu();
}

function contentCard(item) {
  const groups = currentProduct().participant_groups || [];
  return `<article class="content-card">
    <div class="content-card-title">
      <label class="field"><span>Titel</span><input data-content="${item.id}" data-key="title" value="${escapeHtml(item.title)}"></label>
      <label class="field color-field"><span>Farbe</span><input data-content="${item.id}" data-key="background_color" type="color" value="${escapeHtml(item.background_color || "#eaf8f2")}"></label>
      <label class="field duration-field"><span>Max. Teilnehmer</span><input data-content="${item.id}" data-key="max_participants" type="number" min="1" step="1" value="${Number(item.max_participants || 0) || ""}"></label>
      <label class="field duration-field"><span>Dauer</span><input data-content="${item.id}" data-key="duration_minutes" type="number" min="5" step="5" value="${Number(item.duration_minutes || 0)}"></label>
    </div>
    <label class="field checkbox-field split-training-field"><span>Schulungsblock teilen</span><span class="split-training-option"><input data-content="${item.id}" data-key="split_enabled" type="checkbox" ${item.split_enabled ? "checked" : ""}><span>Bei der Planung automatisch in zwei Hälften aufteilen</span></span></label>
    <label class="field"><span>Abhaengigkeit</span><select data-content="${item.id}" data-key="dependency_content_id">${dependencyOptions(item)}</select></label>
    <label class="field field-wide"><span>Teilnehmergruppen</span><select data-content="${item.id}" data-key="participant_group_ids" multiple size="${Math.min(Math.max(groups.length, 3), 7)}">${participantGroupOptions(item, groups)}</select></label>
    ${contentTextarea(item, "target_group", "Zielgruppe")}
    ${contentTextarea(item, "goals", "Ziele")}
    ${contentTextarea(item, "requirements", "Voraussetzungen")}
    ${contentTextarea(item, "preparation", "Vorbereitung")}
    ${contentTextarea(item, "special_notes", "Hinweise")}
    <div class="content-actions">
      <button type="button" class="button button-ghost" data-open-markdown="${item.id}">Schulungspunkte bearbeiten</button>
      <button type="button" class="button button-secondary" data-save-content="${item.id}">Speichern</button>
    </div>
  </article>`;
}

function participantGroupOptions(item, groups) {
  const selected = new Set(item.participant_group_ids || []);
  return groups.map((group) => `<option value="${escapeHtml(group.id)}" ${selected.has(group.id) ? "selected" : ""}>${escapeHtml(group.name)} (${Number(group.participant_count)})</option>`).join("");
}

function dependencyOptions(item) {
  const productItems = trainingContents.filter((candidate) => candidate.product_id === item.product_id && candidate.id !== item.id);
  return [
    `<option value="" ${item.dependency_content_id ? "" : "selected"}>Keine Abhaengigkeit</option>`,
    ...productItems.map((candidate) => `<option value="${escapeHtml(candidate.id)}" ${candidate.id === item.dependency_content_id ? "selected" : ""}>${escapeHtml(candidate.title)}</option>`)
  ].join("");
}

function contentTextarea(item, key, label) {
  return `<label class="field"><span>${label}</span><textarea data-content="${item.id}" data-key="${key}">${escapeHtml(item[key] || "")}</textarea></label>`;
}

function updateTrainingContentDraft(event) {
  const item = trainingContents.find((candidate) => candidate.id === event.target.dataset.content);
  if (!item) return;
  const key = event.target.dataset.key;
  if (key === "participant_group_ids") {
    item[key] = Array.from(event.target.selectedOptions).map((option) => option.value);
  } else if (event.target.type === "checkbox") {
    item[key] = event.target.checked;
  } else {
    item[key] = ["duration_minutes", "max_participants"].includes(key) ? Number(event.target.value || 0) || null : event.target.value || null;
  }
}

async function saveTrainingContent(event) {
  const item = trainingContents.find((candidate) => candidate.id === event.target.dataset.saveContent);
  if (!item) return;
  const payload = {
    title: item.title,
    target_group: item.target_group || "",
    duration_minutes: Number(item.duration_minutes || 5),
    max_participants: item.max_participants ? Number(item.max_participants) : null,
    split_enabled: Boolean(item.split_enabled),
    dependency_content_id: item.dependency_content_id || null,
    participant_group_ids: item.participant_group_ids || [],
    background_color: item.background_color || "#eaf8f2",
    goals: item.goals || "",
    requirements: item.requirements || "",
    preparation: item.preparation || "",
    special_notes: item.special_notes || ""
  };
  event.target.disabled = true;
  event.target.textContent = "Speichern...";
  try {
    const response = await fetch(`api/training-contents/${encodeURIComponent(item.id)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error("save");
    const updated = await response.json();
    trainingContents = trainingContents.map((candidate) => candidate.id === updated.id ? updated : candidate);
    syncTopicsFromCatalog();
    event.target.textContent = "Gespeichert";
    window.setTimeout(renderContentCatalog, 700);
  } catch (error) {
    event.target.disabled = false;
    event.target.textContent = "Fehler";
  }
}

function openMarkdownEditor(event) {
  const item = trainingContents.find((candidate) => candidate.id === event.currentTarget.dataset.openMarkdown);
  if (!item) return;
  markdownEditorContentId = item.id;
  markdownPendingChangeType = "saved";
  $("#markdownEditorTitle").textContent = `Schulungspunkte: ${item.title}`;
  $("#markdownEditorInput").value = item.markdown_content || "";
  $("#markdownEditorStatus").textContent = "";
  $("#markdownEditorModal").hidden = false;
  document.body.classList.add("modal-open");
  updateMarkdownPreview();
  loadMarkdownHistory(item.id);
  window.setTimeout(() => $("#markdownEditorInput").focus(), 0);
}

function closeMarkdownEditor() {
  $("#markdownEditorModal").hidden = true;
  document.body.classList.remove("modal-open");
  markdownEditorContentId = null;
  markdownPendingChangeType = "saved";
  $("#markdownDocxInput").value = "";
}

function updateMarkdownPreview() {
  $("#markdownPreview").innerHTML = renderMarkdown($("#markdownEditorInput").value);
}

function renderMarkdown(markdown) {
  const lines = String(markdown || "").replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  let listType = null;
  const closeList = () => {
    if (listType) html.push(`</${listType}>`);
    listType = null;
  };
  lines.forEach((rawLine) => {
    const line = rawLine.trimEnd();
    if (!line.trim()) {
      closeList();
      return;
    }
    let match = line.match(/^###\s+(.+)$/);
    if (match) {
      closeList();
      html.push(`<h3>${renderMarkdownInline(match[1])}</h3>`);
      return;
    }
    match = line.match(/^##\s+(.+)$/);
    if (match) {
      closeList();
      html.push(`<h2>${renderMarkdownInline(match[1])}</h2>`);
      return;
    }
    match = line.match(/^#\s+(.+)$/);
    if (match) {
      closeList();
      html.push(`<h1>${renderMarkdownInline(match[1])}</h1>`);
      return;
    }
    match = line.match(/^[-*]\s+(.+)$/);
    if (match) {
      if (listType !== "ul") {
        closeList();
        html.push("<ul>");
        listType = "ul";
      }
      html.push(`<li>${renderMarkdownInline(match[1])}</li>`);
      return;
    }
    match = line.match(/^\d+\.\s+(.+)$/);
    if (match) {
      if (listType !== "ol") {
        closeList();
        html.push("<ol>");
        listType = "ol";
      }
      html.push(`<li>${renderMarkdownInline(match[1])}</li>`);
      return;
    }
    closeList();
    html.push(`<p>${renderMarkdownInline(line)}</p>`);
  });
  closeList();
  return html.join("") || '<p class="muted">Noch keine Schulungspunkte hinterlegt.</p>';
}

function renderMarkdownInline(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function applyMarkdownAction(event) {
  const textarea = $("#markdownEditorInput");
  const action = event.currentTarget.dataset.mdAction;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = textarea.value.slice(start, end);
  let replacement = selected;
  if (action === "bold") replacement = `**${selected || "Text"}**`;
  if (action === "italic") replacement = `*${selected || "Text"}*`;
  if (action === "heading") replacement = selected ? selected.split("\n").map((line) => `## ${line}`).join("\n") : "## Ueberschrift";
  if (action === "bullet") replacement = selected ? selected.split("\n").map((line) => `- ${line.replace(/^[-*]\s+/, "")}`).join("\n") : "- Schulungspunkt";
  if (action === "number") replacement = selected ? selected.split("\n").map((line, index) => `${index + 1}. ${line.replace(/^\d+\.\s+/, "")}`).join("\n") : "1. Schulungspunkt";
  textarea.setRangeText(replacement, start, end, "end");
  textarea.focus();
  updateMarkdownPreview();
}

async function saveMarkdownEditor() {
  const item = trainingContents.find((candidate) => candidate.id === markdownEditorContentId);
  if (!item) return;
  const button = $("#saveMarkdownEditor");
  button.disabled = true;
  button.textContent = "Speichern...";
  $("#markdownEditorStatus").textContent = "";
  try {
    const response = await fetch(`api/training-contents/${encodeURIComponent(item.id)}/markdown`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ markdown_content: $("#markdownEditorInput").value, change_type: markdownPendingChangeType })
    });
    if (!response.ok) throw new Error("save-markdown");
    const updated = await response.json();
    trainingContents = trainingContents.map((candidate) => candidate.id === updated.id ? updated : candidate);
    $("#markdownEditorStatus").textContent = markdownPendingChangeType === "docx_imported" ? "DOCX-Inhalt gespeichert." : "Gespeichert.";
    markdownPendingChangeType = "saved";
    await loadMarkdownHistory(item.id);
  } catch (error) {
    $("#markdownEditorStatus").textContent = "Speichern fehlgeschlagen.";
  } finally {
    button.disabled = false;
    button.textContent = "Schulungspunkte speichern";
  }
}

async function exportMarkdownDocx() {
  const item = trainingContents.find((candidate) => candidate.id === markdownEditorContentId);
  if (!item) return;
  const button = $("#exportMarkdownDocx");
  button.disabled = true;
  $("#markdownEditorStatus").textContent = "DOCX wird erstellt...";
  try {
    const response = await fetch(`api/training-contents/${encodeURIComponent(item.id)}/docx/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ markdown_content: $("#markdownEditorInput").value, change_type: "saved" })
    });
    if (!response.ok) throw new Error(await apiErrorMessage(response, "DOCX-Export fehlgeschlagen."));
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `schulungsinhalt-${safeFilenamePart(item.title)}.docx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    $("#markdownEditorStatus").textContent = "DOCX exportiert.";
  } catch (error) {
    $("#markdownEditorStatus").textContent = error.message || "DOCX-Export fehlgeschlagen.";
  } finally {
    button.disabled = false;
  }
}

async function importMarkdownDocx(event) {
  const item = trainingContents.find((candidate) => candidate.id === markdownEditorContentId);
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!item || !file) return;
  if (!file.name.toLowerCase().endsWith(".docx")) {
    $("#markdownEditorStatus").textContent = "Bitte eine DOCX-Datei auswaehlen.";
    return;
  }

  const button = $("#importMarkdownDocx");
  button.disabled = true;
  $("#markdownEditorStatus").textContent = "DOCX wird geprueft...";
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await fetch(`api/training-contents/${encodeURIComponent(item.id)}/docx/import`, {
      method: "POST",
      body: formData
    });
    if (!response.ok) throw new Error(await apiErrorMessage(response, "DOCX-Import fehlgeschlagen."));
    const imported = await response.json();
    $("#markdownEditorInput").value = imported.markdown_content || "";
    markdownPendingChangeType = "docx_imported";
    updateMarkdownPreview();
    $("#markdownEditorStatus").textContent = "DOCX geprueft und geladen. Bitte Inhalt pruefen und anschliessend speichern.";
  } catch (error) {
    $("#markdownEditorStatus").textContent = error.message || "DOCX-Import fehlgeschlagen.";
  } finally {
    button.disabled = false;
  }
}

async function apiErrorMessage(response, fallback) {
  try {
    const payload = await response.json();
    return payload.detail || fallback;
  } catch (error) {
    return fallback;
  }
}

function safeFilenamePart(value) {
  return String(value || "schulungsinhalt")
    .normalize("NFKD")
    .replace(/[^a-zA-Z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "schulungsinhalt";
}

async function loadMarkdownHistory(contentId) {
  const history = $("#markdownHistory");
  const status = $("#markdownHistoryStatus");
  status.textContent = "Wird geladen...";
  try {
    const response = await fetch(`api/training-contents/${encodeURIComponent(contentId)}/history`);
    if (!response.ok) throw new Error("history");
    const items = (await response.json()).items || [];
    status.textContent = items.length ? `${items.length} von max. 5 gespeichert` : "Noch keine Versionen";
    history.innerHTML = items.length ? items.map(markdownHistoryItem).join("") : '<p class="muted">Nach dem ersten Speichern erscheint hier die Aenderungshistorie.</p>';
    history.querySelectorAll("[data-restore-markdown]").forEach((button) => button.addEventListener("click", restoreMarkdownVersion));
  } catch (error) {
    status.textContent = "Historie nicht erreichbar";
    history.innerHTML = '<p class="muted">Die Aenderungshistorie konnte nicht geladen werden.</p>';
  }
}

function markdownHistoryItem(item) {
  const timestamp = new Date(item.created_at).toLocaleString("de-DE");
  const label = item.change_type === "restored" ? "Wiederhergestellt" : item.change_type === "docx_imported" ? "DOCX importiert" : "Gespeichert";
  const preview = String(item.markdown_content || "").replace(/\s+/g, " ").trim().slice(0, 140) || "Leerer Inhalt";
  return `<article class="markdown-history-item">
    <div>
      <strong>${label}</strong>
      <span>${escapeHtml(timestamp)}</span>
      <p>${escapeHtml(preview)}${preview.length >= 140 ? "…" : ""}</p>
    </div>
    <button type="button" class="button button-ghost" data-restore-markdown="${item.id}">Wiederherstellen</button>
  </article>`;
}

async function restoreMarkdownVersion(event) {
  const item = trainingContents.find((candidate) => candidate.id === markdownEditorContentId);
  if (!item) return;
  if (!window.confirm("Diesen gespeicherten Stand wiederherstellen? Der aktuelle Stand bleibt als neue Historienversion nachvollziehbar.")) return;
  const revisionId = event.currentTarget.dataset.restoreMarkdown;
  event.currentTarget.disabled = true;
  try {
    const response = await fetch(`api/training-contents/${encodeURIComponent(item.id)}/history/${encodeURIComponent(revisionId)}/restore`, { method: "POST" });
    if (!response.ok) throw new Error("restore");
    const updated = await response.json();
    trainingContents = trainingContents.map((candidate) => candidate.id === updated.id ? updated : candidate);
    $("#markdownEditorInput").value = updated.markdown_content || "";
    updateMarkdownPreview();
    $("#markdownEditorStatus").textContent = "Version wiederhergestellt.";
    await loadMarkdownHistory(item.id);
  } catch (error) {
    $("#markdownEditorStatus").textContent = "Wiederherstellen fehlgeschlagen.";
    event.currentTarget.disabled = false;
  }
}

function addTopic() {
  project.topics.push(topic(crypto.randomUUID(), "Neues Thema", 60, 3, "", null, currentProduct().id));
  render();
}

function updateTopic(event) {
  const item = project.topics.find((candidate) => candidate.id === event.target.dataset.topic);
  if (!item) return;
  const key = event.target.dataset.key;
  item[key] = ["duration_minutes", "priority", "participants_per_session"].includes(key) ? Number(event.target.value || 0) || null : event.target.value || null;
}

function duplicateTopic(id) {
  const item = project.topics.find((candidate) => candidate.id === id);
  if (!item) return;
  project.topics.push({ ...item, id: crypto.randomUUID(), title: `${item.title} Kopie` });
  render();
}

function deleteTopic(id) {
  const affectedWeeks = new Set(
    project.blocks
      .filter((block) => (block.source_topic_id || block.topic_id) === id)
      .map((block) => Number(block.week || 1))
  );
  project.topics = project.topics.filter((item) => item.id !== id);
  project.blocks = project.blocks.filter((block) => (block.source_topic_id || block.topic_id) !== id);
  affectedWeeks.forEach((week) => hideEmptyTransientWeek(week));
  render();
}

async function createPlan() {
  if (!["product", "project", "people", "training", "time"].every((step) => validateWorkflowStep(step, false))) {
    const firstMissing = workflowSteps.slice(0, 5).find((step) => !workflowStepIsComplete(step.id));
    if (firstMissing) setWorkflowStep(firstMissing.id);
    return;
  }
  setStatus("Planung wird berechnet...");
  const button = $("#autoPlan");
  if (button) button.disabled = true;
  const response = await fetch("api/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(project)
  });
  if (!response.ok) {
    setStatus("Planung konnte nicht erstellt werden.");
    if (button) button.disabled = false;
    return;
  }
  project = await response.json();
  normalizeProjectState();
  transientManualWeeks = new Set();
  planInputsDirty = false;
  workflowErrors = {};
  setStatus("Plan erstellt.");
  activeTab = "week";
  currentPage = "plan";
  render();
}

function renderPages() {
  document.querySelectorAll(".app-page").forEach((page) => {
    page.classList.toggle("active", page.id === `${currentPage}-page`);
  });
  renderNavigation();
}

function renderNavigation() {
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === currentPage);
  });
}

function renderTabs() {
  document.querySelectorAll("[data-tab]").forEach((button) => button.classList.toggle("active", button.dataset.tab === activeTab));
  document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${activeTab}`));
  renderOverview();
  renderTopicSchedule();
  renderWeek();
  renderPreview();
}

function renderOverview() {
  const totals = totalMinutesByType();
  const serviceDays = serviceDayCount();
  $("#tab-overview").innerHTML = `
    ${projectOverviewMeta()}
    <div class="metric-grid">
      ${metric("Schulung", totals.training || 0)}
      ${metricValue("Dienstleistungstage", formatServiceDays(serviceDays))}
      ${metric("Nicht eingeplant", project.unscheduled_topics.reduce((sum, item) => sum + item.duration_minutes, 0))}
    </div>
    <div class="product-summary">${productSummary()}</div>
    <div class="output-wrap">
      <div class="output-content">${topicSummary()}</div>
    </div>`;
}

function projectOverviewMeta() {
  const product = currentProduct();
  const startDate = TrainingCalendar.formatGermanDate(TrainingCalendar.parseIsoDate(project.start_date));
  const trainers = calendarTrainers().map((trainer) => trainerLabel(trainer)).join(", ");
  const customer = project.customer_data_required ? (project.customer_name || "—") : "Nicht erforderlich";
  const location = project.customer_data_required ? (project.location || "—") : "Nicht erforderlich";
  return `<div class="overview-meta-grid">
    ${overviewMeta("Kunde", customer)}
    ${overviewMeta("Standort", location)}
    ${overviewMeta("Produkt", product.name || project.product_id || "—")}
    ${overviewMeta("Startdatum", startDate || "—")}
    ${overviewMeta("Trainer", trainers || "—", true)}
  </div>`;
}

function overviewMeta(label, value, wide = false) {
  return `<div class="overview-meta ${wide ? "overview-meta-wide" : ""}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function metric(label, minutes) {
  return metricValue(label, formatDuration(minutes));
}

function metricValue(label, value) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
}

function serviceDayCount() {
  return new Set(
    project.blocks
      .filter((block) => block.type === "training")
      .map((block) => `${Number(block.week || 1)}::${block.day}::${String(block.trainer || "").trim()}`)
  ).size;
}

function formatServiceDays(count) {
  return `${count} ${count === 1 ? "Tag" : "Tage"}`;
}

function topicSummary() {
  const productId = currentProduct().id;
  const topics = (project.topics || []).filter((item) => !item.product_id || item.product_id === productId);
  if (!topics.length) return `<div class="empty-compact">Keine Schulungen ausgewählt.</div>`;
  return `<div class="topic-summary-compact">${topics.map((item) => `
    <div class="topic-summary-item">
      <span>${escapeHtml(item.title)}</span>
      <b>${Number(item.duration_minutes || 0)} min</b>
    </div>`).join("")}</div>`;
}

function productSummary() {
  const product = currentProduct();
  if (!product) return "";
  const participantGroups = (product.participant_groups || []).filter((group) => Number(group.participant_count || 0) > 0);
  return `
    <section class="product-summary-card">
      <strong>${escapeHtml(product.name)}</strong>
      ${product.description ? `<span>${escapeHtml(product.description)}</span>` : ""}
      ${participantGroups.length ? `<div>${participantGroups.map((group) => `<b>${escapeHtml(group.name)}: ${Number(group.participant_count)}</b>`).join("")}</div>` : ""}
    </section>`;
}

function renderTopicSchedule() {
  const target = $("#tab-topics");
  if (!target) return;
  const productId = currentProduct().id;
  const topics = (project.topics || []).filter((item) => !item.product_id || item.product_id === productId);
  if (!topics.length) {
    target.innerHTML = `<div class="calendar-empty-state"><strong>Keine Schulungsthemen ausgewählt.</strong></div>`;
    return;
  }

  target.innerHTML = `
    <div class="topic-schedule-page">
      <div class="topic-schedule-head">
        <span>Schulungsinhalt</span>
        <span>Termine</span>
        <span>Zeitraum</span>
      </div>
      <div class="topic-schedule-list">
        ${topics.map((topic) => {
          const blocks = topicScheduleBlocks(topic.id);
          return `<article class="topic-schedule-row">
            <strong>${escapeHtml(topic.title)}</strong>
            <span class="topic-schedule-count">${blocks.length ? `${blocks.length} ${blocks.length === 1 ? "Termin" : "Termine"}` : "—"}</span>
            <span class="topic-schedule-period ${blocks.length ? "" : "is-empty"}">${escapeHtml(topicSchedulePeriod(blocks))}</span>
          </article>`;
        }).join("")}
      </div>
    </div>`;
}

function topicScheduleBlocks(topicId) {
  return (project.blocks || [])
    .filter((block) => block.type === "training" && (block.source_topic_id || block.topic_id) === topicId)
    .slice()
    .sort(compareScheduleBlocks);
}

function compareScheduleBlocks(left, right) {
  const leftDate = TrainingCalendar.dateForCalendarDay(project.start_date, Number(left.week || 1), left.day);
  const rightDate = TrainingCalendar.dateForCalendarDay(project.start_date, Number(right.week || 1), right.day);
  const leftKey = leftDate ? leftDate.getTime() : Number(left.week || 1) * 7 * 86400000 + days.indexOf(left.day) * 86400000;
  const rightKey = rightDate ? rightDate.getTime() : Number(right.week || 1) * 7 * 86400000 + days.indexOf(right.day) * 86400000;
  return (leftKey + toMinutes(left.start) * 60000) - (rightKey + toMinutes(right.start) * 60000);
}

function topicSchedulePeriod(blocks) {
  if (!blocks.length) return "Nicht eingeplant";
  const first = blocks[0];
  const last = blocks[blocks.length - 1];
  const firstDate = TrainingCalendar.dateForCalendarDay(project.start_date, Number(first.week || 1), first.day);
  const lastDate = TrainingCalendar.dateForCalendarDay(project.start_date, Number(last.week || 1), last.day);
  const firstLabel = TrainingCalendar.formatGermanDate(firstDate);
  const lastLabel = TrainingCalendar.formatGermanDate(lastDate);
  if (firstLabel && firstLabel === lastLabel) return `${firstLabel} · ${first.start}–${last.end}`;
  if (firstLabel && lastLabel) return `${firstLabel} ${first.start} – ${lastLabel} ${last.end}`;
  return `Woche ${first.week}, ${first.day} ${first.start} – Woche ${last.week}, ${last.day} ${last.end}`;
}

function calendarTrainers() {
  const values = [];
  (project.trainers || []).forEach((name) => {
    const cleaned = String(name || "").trim();
    if (cleaned && !values.includes(cleaned)) values.push(cleaned);
  });
  if (!values.length && String(project.trainer || "").trim()) values.push(String(project.trainer).trim());
  (project.blocks || []).forEach((block) => {
    const cleaned = String(block.trainer || "").trim();
    if (cleaned && !values.includes(cleaned)) values.push(cleaned);
  });
  return values.length ? values : [""];
}

function trainerLabel(trainer) {
  return trainer || "Nicht zugewiesen";
}

function renderWeek() {
  const start = toMinutes(project.settings.day_start);
  const end = toMinutes(project.settings.day_end);
  const totalMinutes = Math.max(60, end - start);
  const height = (totalMinutes / 60) * calendarHourHeight;
  const weeks = plannedWeeks();
  const trainers = calendarTrainers();
  $("#tab-week").innerHTML = `
    <div class="calendar-toolbar">
      <div class="calendar-help">Schulungsblöcke können verschoben werden. Mit den Griffen an Ober- und Unterkante lassen sich Start- und Endzeit live im 15-Minuten-Raster anpassen. Jeder Trainer besitzt pro Kalenderwoche eine eigene Wochenansicht.</div>
      <button type="button" class="button button-secondary" onclick="addManualWeek()">Woche hinzufügen</button>
    </div>
    ${cutBlockId ? `<div class="cut-notice">Ausgeschnitten: ${escapeHtml(cutBlockTitle())}. Zieltag und Zieltrainer waehlen und Einfuegen klicken.</div>` : ""}
    <div class="calendar-weeks">
      ${weeks.length ? weeks.map((week) => `
      <div class="calendar-week-wrap">
        <h3>${weekHeading(week)}</h3>
        <div class="trainer-weeks">
          ${trainers.map((trainer, trainerIndex) => `
            <section class="trainer-week">
              <div class="trainer-week-title"><span>Trainer</span><strong>${escapeHtml(trainerLabel(trainer))}</strong></div>
              <div class="calendar-week" style="--calendar-height:${height}px">
                ${days.map((day) => dayHtml(day, start, height, week, trainer, trainerIndex)).join("")}
              </div>
            </section>
          `).join("")}
        </div>
      </div>
      `).join("") : `<div class="calendar-empty-state"><strong>Keine Schulungswochen vorhanden.</strong><span>Wochen ohne Schulungsblöcke werden automatisch ausgeblendet. Bei Bedarf kann eine neue Woche manuell hinzugefügt werden.</span></div>`}
    </div>`;
}

function weekHeading(week) {
  const first = TrainingCalendar.dateForCalendarDay(project.start_date, week, "Montag");
  const last = TrainingCalendar.dateForCalendarDay(project.start_date, week, "Freitag");
  if (!first || !last) return `Woche ${week}`;
  return `Woche ${week} · ${TrainingCalendar.formatGermanDate(first)}–${TrainingCalendar.formatGermanDate(last)}`;
}

function scheduledWeeks() {
  return [...new Set(
    (project.blocks || [])
      .filter((block) => block.type === "training")
      .map((block) => Number(block.week || 1))
      .filter((week) => Number.isFinite(week) && week > 0)
  )].sort((a, b) => a - b);
}

function plannedWeeks() {
  const weekSet = new Set([
    ...scheduledWeeks(),
    ...transientManualWeeks
  ]);
  return [...weekSet].filter((week) => Number.isFinite(week) && week > 0).sort((a, b) => a - b);
}

function hideEmptyTransientWeek(week) {
  const weekNumber = Number(week);
  if (!Number.isFinite(weekNumber) || weekNumber <= 0) return;
  const hasTraining = (project.blocks || []).some(
    (block) => block.type === "training" && Number(block.week || 1) === weekNumber
  );
  if (!hasTraining) transientManualWeeks.delete(weekNumber);
}

function dayHtml(day, dayStart, calendarHeight, week, trainer, trainerIndex, interactive = true) {
  const blocks = project.blocks.filter((block) => Number(block.week || 1) === week && block.day === day && String(block.trainer || "") === String(trainer || "")).sort((a, b) => a.start.localeCompare(b.start));
  const visibleBlocks = blocks.filter((block) => !["break", "lunch"].includes(block.type));
  const calendarDate = TrainingCalendar.dateForCalendarDay(project.start_date, week, day);
  const dateLabel = TrainingCalendar.formatGermanDate(calendarDate);
  const holidayHints = TrainingCalendar.holidayHints(calendarDate);
  return `<section class="calendar-day">
    <div class="calendar-day-title">
      <div class="calendar-day-heading">
        <h3>${day}</h3>
        ${dateLabel ? `<span class="calendar-date">${dateLabel}</span>` : ""}
        ${holidayHints.length ? `<span class="calendar-holiday" title="Landesweiter Feiertag in Deutschland/Oesterreich bzw. Schweizer Bundesfeier. Regionale Feiertage sind ohne Bundesland/Kanton nicht beruecksichtigt.">${holidayHints.map((item) => escapeHtml(item)).join(" · ")}</span>` : ""}
      </div>
      ${interactive ? `<div class="calendar-day-actions">
        ${cutBlockId ? `<button type="button" class="button button-secondary" onclick="pasteCutBlock('${day}', ${week}, ${trainerIndex})">Einfuegen</button>` : ""}
        <button type="button" class="button button-ghost" onclick="addBlock('${day}', ${week}, ${trainerIndex})">Block</button>
      </div>` : ""}
    </div>
    <div class="calendar-day-body" ${interactive ? `ondragover="event.preventDefault()" ondrop="dropBlock(event, '${day}', ${week}, ${trainerIndex})"` : ""}>
      ${quarterGridLines(dayStart, project.settings.day_end).join("")}
      <div class="day-time-labels" aria-hidden="true">${timeAxisLabels(dayStart, toMinutes(project.settings.day_end)).join("")}</div>
      ${visibleBlocks.map((block) => blockHtml(block, dayStart, calendarHeight, interactive)).join("")}
    </div>
  </section>`;
}

function calendarBlockTypography(height) {
  const minHeight = 44;
  const fullSizeHeight = 114;
  const progress = Math.max(0, Math.min(1, (height - minHeight) / (fullSizeHeight - minHeight)));
  return {
    titleSize: 0.70 + (0.18 * progress),
    groupSize: 0.58 + (0.16 * progress),
    metaSize: 0.56 + (0.22 * progress),
    titleLineHeight: 1.02 + (0.10 * progress),
  };
}

function applyCalendarBlockTypography(element, height) {
  const typography = calendarBlockTypography(height);
  element.style.setProperty("--calendar-title-size", `${typography.titleSize.toFixed(3)}rem`);
  element.style.setProperty("--calendar-group-size", `${typography.groupSize.toFixed(3)}rem`);
  element.style.setProperty("--calendar-meta-size", `${typography.metaSize.toFixed(3)}rem`);
  element.style.setProperty("--calendar-title-line-height", typography.titleLineHeight.toFixed(3));
}

function calendarDisplayParts(block) {
  const displayTitle = block.type === "arrival" ? "Anreise" : String(block.title || "").trim();
  if (block.type !== "training") return { title: displayTitle, groupLabel: "" };

  const topic = (project.topics || []).find((item) => item.id === (block.source_topic_id || block.topic_id));
  let title = String(topic?.title || displayTitle).trim();
  let groupLabel = "";
  const groupNames = (project.product_lines || [])
    .flatMap((product) => product.participant_groups || [])
    .map((group) => String(group.name || "").trim())
    .filter(Boolean)
    .sort((left, right) => right.length - left.length);

  for (const groupName of groupNames) {
    const marker = ` - ${groupName}`;
    const markerIndex = displayTitle.lastIndexOf(marker);
    if (markerIndex < 0) continue;
    const suffix = displayTitle.slice(markerIndex + marker.length).trimStart();
    if (suffix && !suffix.startsWith("Gruppe ")) continue;
    if (!topic?.title) title = displayTitle.slice(0, markerIndex).trim();
    groupLabel = suffix.startsWith("Gruppe ") ? suffix : "";
    break;
  }
  return { title, groupLabel };
}

function calendarDisplayTitle(block) {
  const parts = calendarDisplayParts(block);
  return parts.groupLabel ? `${parts.title} - ${parts.groupLabel}` : parts.title;
}

function blockHtml(block, dayStart, calendarHeight, interactive = true) {
  const displayParts = calendarDisplayParts(block);
  const displayTitle = displayParts.title;
  const start = toMinutes(block.start);
  const blockDuration = Math.max(calendarSnapMinutes, duration(block.start, block.end));
  const top = Math.max(0, ((start - dayStart) / 60) * calendarHourHeight);
  const height = Math.max(44, (blockDuration / 60) * calendarHourHeight);
  const cappedHeight = Math.min(height, Math.max(44, calendarHeight - top));
  const compactClass = interactive && blockDuration <= 30 ? " is-compact" : "";
  const typography = calendarBlockTypography(cappedHeight);
  const blockTooltip = [displayTitle, displayParts.groupLabel, `${block.start}-${block.end} · ${formatHours(blockDuration)}`].filter(Boolean).join(" · ");
  const resizeHandles = interactive && block.type === "training" ? `
    <button type="button" class="calendar-resize-handle resize-start" draggable="false" aria-label="Startzeit ziehen" title="Startzeit in 15-Minuten-Schritten ziehen" onpointerdown="startBlockResize(event, '${block.id}', 'start')" ondragstart="event.preventDefault(); event.stopPropagation()"></button>
    <button type="button" class="calendar-resize-handle resize-end" draggable="false" aria-label="Endzeit ziehen" title="Endzeit in 15-Minuten-Schritten ziehen" onpointerdown="startBlockResize(event, '${block.id}', 'end')" ondragstart="event.preventDefault(); event.stopPropagation()"></button>` : "";
  return `<article class="block calendar-block${compactClass} ${block.type} ${block.id === cutBlockId ? "is-cut" : ""}" data-block-id="${escapeHtml(block.id)}" title="${escapeHtml(blockTooltip)}" ${interactive ? `draggable="true" ondragstart="dragBlock(event, '${block.id}')"` : ""} style="top:${top}px;height:${cappedHeight}px;--block-bg:${escapeHtml(block.background_color || "#ffffff")};--calendar-title-size:${typography.titleSize.toFixed(3)}rem;--calendar-group-size:${typography.groupSize.toFixed(3)}rem;--calendar-meta-size:${typography.metaSize.toFixed(3)}rem;--calendar-title-line-height:${typography.titleLineHeight.toFixed(3)}">
    ${resizeHandles}
    <div class="block-content">
      <strong class="block-title">${escapeHtml(displayTitle)}</strong>
      ${displayParts.groupLabel ? `<span class="block-group">${escapeHtml(displayParts.groupLabel)}</span>` : ""}
      <span class="block-meta">${block.start}-${block.end} · ${formatHours(blockDuration)}</span>
    </div>
    ${interactive ? `<div class="block-actions">
      <button type="button" class="icon" onclick="cutBlock('${block.id}')" title="Ausschneiden">✂</button>
      <button type="button" class="icon" onclick="editBlock('${block.id}')" title="Bearbeiten">✎</button>
      <button type="button" class="icon" onclick="copyBlock('${block.id}')" title="Duplizieren">⧉</button>
      <button type="button" class="icon danger" onclick="removeBlock('${block.id}')" title="Loeschen">×</button>
    </div>` : ""}
  </article>`;
}

function startBlockResize(event, id, edge) {
  if (event.button !== undefined && event.button !== 0) return;
  const block = project.blocks.find((item) => item.id === id);
  const element = event.currentTarget.closest(".calendar-block");
  const dayBody = element?.closest(".calendar-day-body");
  if (!block || block.type !== "training" || !element || !dayBody) return;

  event.preventDefault();
  event.stopPropagation();
  resizingBlock = { id, edge, element, dayBody, pointerId: event.pointerId };
  element.classList.add("is-resizing");
  element.setAttribute("draggable", "false");
  document.body.classList.add("calendar-resizing");
  if (event.currentTarget.setPointerCapture && event.pointerId !== undefined) {
    try { event.currentTarget.setPointerCapture(event.pointerId); } catch (_) { /* no-op */ }
  }
  document.addEventListener("pointermove", resizeBlockPointerMove, { passive: false });
  document.addEventListener("pointerup", finishBlockResize);
  document.addEventListener("pointercancel", finishBlockResize);
}

function resizeBlockPointerMove(event) {
  if (!resizingBlock || (resizingBlock.pointerId !== undefined && event.pointerId !== resizingBlock.pointerId)) return;
  const block = project.blocks.find((item) => item.id === resizingBlock.id);
  if (!block) return;

  event.preventDefault();
  const rect = resizingBlock.dayBody.getBoundingClientRect();
  const dayStart = toMinutes(project.settings.day_start);
  const dayEnd = toMinutes(project.settings.day_end);
  const rawMinutes = dayStart + ((event.clientY - rect.top) / calendarHourHeight) * 60;
  const pointerMinutes = Math.min(dayEnd, Math.max(dayStart, snapMinutes(rawMinutes)));
  const currentStart = toMinutes(block.start);
  const currentEnd = toMinutes(block.end);

  if (resizingBlock.edge === "start") {
    block.start = formatTime(Math.min(pointerMinutes, currentEnd - calendarSnapMinutes));
  } else {
    block.end = formatTime(Math.max(pointerMinutes, currentStart + calendarSnapMinutes));
  }
  updateResizedBlockElement(block, resizingBlock.element, rect.height);
}

function updateResizedBlockElement(block, element, calendarHeight) {
  const dayStart = toMinutes(project.settings.day_start);
  const blockDuration = Math.max(calendarSnapMinutes, duration(block.start, block.end));
  const top = Math.max(0, ((toMinutes(block.start) - dayStart) / 60) * calendarHourHeight);
  const height = Math.max(44, (blockDuration / 60) * calendarHourHeight);
  const cappedHeight = Math.min(height, Math.max(44, calendarHeight - top));
  const displayParts = calendarDisplayParts(block);
  const displayTitle = displayParts.title;
  element.style.top = `${top}px`;
  element.style.height = `${cappedHeight}px`;
  applyCalendarBlockTypography(element, cappedHeight);
  element.classList.toggle("is-compact", blockDuration <= 30);
  element.title = [displayTitle, displayParts.groupLabel, `${block.start}-${block.end} · ${formatHours(blockDuration)}`].filter(Boolean).join(" · ");
  const meta = element.querySelector(".block-meta");
  if (meta) meta.textContent = `${block.start}-${block.end} · ${formatHours(blockDuration)}`;
}

function finishBlockResize(event) {
  if (!resizingBlock || (event?.pointerId !== undefined && resizingBlock.pointerId !== undefined && event.pointerId !== resizingBlock.pointerId)) return;
  const element = resizingBlock.element;
  element.classList.remove("is-resizing");
  element.setAttribute("draggable", "true");
  document.body.classList.remove("calendar-resizing");
  resizingBlock = null;
  document.removeEventListener("pointermove", resizeBlockPointerMove);
  document.removeEventListener("pointerup", finishBlockResize);
  document.removeEventListener("pointercancel", finishBlockResize);
  validateAndRender();
}

function addManualWeek() {
  const nextWeek = Math.max(0, ...plannedWeeks()) + 1;
  project.manual_weeks = [...new Set([...(project.manual_weeks || []), nextWeek])].sort((a, b) => a - b);
  transientManualWeeks.add(nextWeek);
  currentPage = "plan";
  activeTab = "week";
  planInputsDirty = false;
  currentWorkflowStep = "review";
  workflowErrors = {};
  render();
}

function cutBlockTitle() {
  const block = project.blocks.find((item) => item.id === cutBlockId);
  return block ? block.title : "Block";
}

function timeAxisLabels(start, end) {
  const labels = [];
  for (let minute = start; minute <= end; minute += calendarSnapMinutes) {
    const isHour = minute % 60 === 0;
    labels.push(`<span class="${isHour ? "full-hour" : "quarter-hour"}" style="top:${calendarOffset(minute, start)}px">${formatTime(minute)}</span>`);
  }
  return labels;
}

function quarterGridLines(start, endValue) {
  const end = toMinutes(endValue);
  const lines = [];
  for (let minute = start + calendarSnapMinutes; minute < end; minute += calendarSnapMinutes) {
    const isHour = minute % 60 === 0;
    lines.push(`<span class="calendar-grid-line ${isHour ? "full-hour" : "quarter-hour"}" style="top:${calendarOffset(minute, start)}px"></span>`);
  }
  return lines;
}

function dragBlock(event, id) {
  if (resizingBlock) {
    event.preventDefault();
    return;
  }
  draggedBlockId = id;
  const rect = event.currentTarget.getBoundingClientRect();
  draggedBlockOffsetMinutes = ((event.clientY - rect.top) / calendarHourHeight) * 60;
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", id);
}

function dropBlock(event, day, week = 1, trainerIndex = 0) {
  event.preventDefault();
  const id = draggedBlockId || event.dataTransfer.getData("text/plain");
  const block = project.blocks.find((item) => item.id === id);
  if (block) {
    const previousWeek = Number(block.week || 1);
    const blockDuration = Math.max(calendarSnapMinutes, duration(block.start, block.end));
    const dayBody = event.currentTarget;
    const rect = dayBody.getBoundingClientRect();
    const rawMinutes = project.settings.day_start
      ? toMinutes(project.settings.day_start) + ((event.clientY - rect.top) / calendarHourHeight) * 60 - draggedBlockOffsetMinutes
      : toMinutes(block.start);
    const start = clampToDay(snapMinutes(rawMinutes), blockDuration);
    block.day = day;
    block.week = week;
    block.trainer = calendarTrainers()[trainerIndex] || "";
    block.start = formatTime(start);
    block.end = formatTime(start + blockDuration);
    hideEmptyTransientWeek(previousWeek);
  }
  draggedBlockId = null;
  draggedBlockOffsetMinutes = 0;
  validateAndRender();
}

function snapMinutes(value) {
  return Math.round(value / calendarSnapMinutes) * calendarSnapMinutes;
}

function snapTimeValue(value) {
  if (!/^\d{1,2}:\d{2}$/.test(String(value || ""))) return value;
  const minutes = toMinutes(value);
  if (!Number.isFinite(minutes)) return value;
  return formatTime(snapMinutes(minutes));
}

function normalizeBlockStart(block) {
  if (!block || !block.start || !block.end) return;
  const originalDuration = duration(block.start, block.end);
  const snapped = snapTimeValue(block.start);
  if (snapped === block.start || !/^\d{2}:\d{2}$/.test(snapped)) return;
  block.start = snapped;
  block.end = formatTime(toMinutes(snapped) + Math.max(0, originalDuration));
}

function clampToDay(start, blockDuration) {
  const dayStart = toMinutes(project.settings.day_start);
  const dayEnd = toMinutes(project.settings.day_end);
  return Math.min(Math.max(start, dayStart), Math.max(dayStart, dayEnd - blockDuration));
}

function calendarOffset(minute, start) {
  return ((minute - start) / 60) * calendarHourHeight;
}

function addBlock(day, week = 1, trainerIndex = 0) {
  const trainer = calendarTrainers()[trainerIndex] || "";
  project.blocks.push({ id: crypto.randomUUID(), type: "training", week, day, title: "Neuer Block", start: "10:00", end: "11:00", topic_id: null, source_topic_id: null, split_part: null, split_parts: null, description: "", trainer, room: "", notes: "", background_color: "#ffffff" });
  validateAndRender();
}

function cutBlock(id) {
  cutBlockId = cutBlockId === id ? null : id;
  renderWeek();
}

function pasteCutBlock(day, week = 1, trainerIndex = 0) {
  const block = project.blocks.find((item) => item.id === cutBlockId);
  if (!block) {
    cutBlockId = null;
    renderWeek();
    return;
  }
  const previousWeek = Number(block.week || 1);
  const blockDuration = Math.max(calendarSnapMinutes, duration(block.start, block.end));
  const trainer = calendarTrainers()[trainerIndex] || "";
  const start = findAvailableStart(day, week, blockDuration, block.id, trainer);
  block.day = day;
  block.week = week;
  block.trainer = trainer;
  block.start = formatTime(start);
  block.end = formatTime(start + blockDuration);
  hideEmptyTransientWeek(previousWeek);
  cutBlockId = null;
  validateAndRender();
}

function findAvailableStart(day, week, blockDuration, movingBlockId, trainer = "") {
  const dayStart = toMinutes(project.settings.day_start);
  const dayEnd = toMinutes(project.settings.day_end);
  const occupied = project.blocks
    .filter((block) => block.id !== movingBlockId && Number(block.week || 1) === Number(week) && block.day === day && String(block.trainer || "") === String(trainer || ""))
    .map((block) => ({ start: toMinutes(block.start), end: toMinutes(block.end) }));
  for (let start = dayStart; start + blockDuration <= dayEnd; start += calendarSnapMinutes) {
    const end = start + blockDuration;
    if (!occupied.some((block) => start < block.end && block.start < end)) {
      return start;
    }
  }
  return clampToDay(dayStart, blockDuration);
}

function editBlock(id) {
  openBlockEditor(id);
}

function openBlockEditor(id) {
  const block = project.blocks.find((item) => item.id === id);
  if (!block) return;
  blockEditorBlockId = id;
  const modal = $("#blockEditorModal");
  const topicSelect = $("#blockEditorTopic");
  const topicOptions = (project.topics || []).map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)}</option>`).join("");
  topicSelect.innerHTML = `<option value="">Freier Kalenderblock</option>${topicOptions}`;
  topicSelect.value = block.source_topic_id || block.topic_id || "";

  $("#blockEditorBlockTitle").value = block.title || "";
  $("#blockEditorType").value = block.type || "training";
  $("#blockEditorWeek").value = Number(block.week || 1);
  $("#blockEditorDay").innerHTML = days.map((day) => `<option value="${escapeHtml(day)}">${escapeHtml(day)}</option>`).join("");
  $("#blockEditorDay").value = block.day || days[0];

  const trainers = calendarTrainers();
  const currentTrainer = String(block.trainer || "");
  const trainerValues = currentTrainer && !trainers.includes(currentTrainer) ? [...trainers, currentTrainer] : trainers;
  $("#blockEditorTrainer").innerHTML = trainerValues.length
    ? trainerValues.map((trainer) => `<option value="${escapeHtml(trainer)}">${escapeHtml(trainerLabel(trainer))}</option>`).join("")
    : '<option value="">Kein Trainer</option>';
  $("#blockEditorTrainer").value = currentTrainer;

  $("#blockEditorStart").value = snapTimeValue(block.start || project.settings.day_start);
  $("#blockEditorEnd").value = block.end || "";
  $("#blockEditorDuration").value = Math.max(calendarSnapMinutes, duration(block.start, block.end));
  $("#blockEditorColor").value = /^#[0-9a-fA-F]{6}$/.test(block.background_color || "") ? block.background_color : "#ffffff";
  $("#blockEditorRoom").value = block.room || "";
  $("#blockEditorDescription").value = block.description || "";
  $("#blockEditorNotes").value = block.notes || "";
  $("#blockEditorStatus").textContent = "";
  modal.hidden = false;
  document.body.classList.add("modal-open");
  $("#blockEditorBlockTitle").focus();
}

function closeBlockEditor() {
  $("#blockEditorModal").hidden = true;
  blockEditorBlockId = null;
  document.body.classList.remove("modal-open");
  $("#blockEditorStatus").textContent = "";
}

function applyBlockEditorTopic() {
  const topicId = $("#blockEditorTopic").value;
  if (!topicId) return;
  const item = (project.topics || []).find((topic) => topic.id === topicId);
  if (!item) return;
  $("#blockEditorBlockTitle").value = item.title || "";
  $("#blockEditorDescription").value = item.description || "";
  $("#blockEditorRoom").value = item.room || "";
  $("#blockEditorNotes").value = item.notes || "";
  $("#blockEditorColor").value = /^#[0-9a-fA-F]{6}$/.test(item.background_color || "") ? item.background_color : "#ffffff";
  $("#blockEditorType").value = "training";
  if (Number(item.duration_minutes) > 0) {
    $("#blockEditorDuration").value = Number(item.duration_minutes);
    syncBlockEditorEndFromDuration();
  }
}

function syncBlockEditorEndFromDuration() {
  const startValue = snapTimeValue($("#blockEditorStart").value);
  const durationMinutes = Number($("#blockEditorDuration").value);
  if (!/^\d{2}:\d{2}$/.test(startValue) || !Number.isFinite(durationMinutes) || durationMinutes <= 0) return;
  $("#blockEditorStart").value = startValue;
  $("#blockEditorEnd").value = formatTime(toMinutes(startValue) + durationMinutes);
}

function syncBlockEditorDurationFromEnd() {
  const startValue = snapTimeValue($("#blockEditorStart").value);
  const endValue = $("#blockEditorEnd").value;
  if (!/^\d{2}:\d{2}$/.test(startValue) || !/^\d{2}:\d{2}$/.test(endValue)) return;
  const minutes = toMinutes(endValue) - toMinutes(startValue);
  if (minutes > 0) $("#blockEditorDuration").value = minutes;
}

async function saveBlockEditor() {
  const block = project.blocks.find((item) => item.id === blockEditorBlockId);
  if (!block) return;
  const status = $("#blockEditorStatus");
  const previousWeek = Number(block.week || 1);
  const title = $("#blockEditorBlockTitle").value.trim();
  const startValue = snapTimeValue($("#blockEditorStart").value);
  const endValue = $("#blockEditorEnd").value;
  const week = Math.max(1, Number.parseInt($("#blockEditorWeek").value, 10) || 1);

  if (!title) {
    status.textContent = "Bitte einen Titel eingeben.";
    return;
  }
  if (!/^\d{2}:\d{2}$/.test(startValue) || !/^\d{2}:\d{2}$/.test(endValue)) {
    status.textContent = "Bitte gueltige Start- und Endzeiten eingeben.";
    return;
  }
  if (toMinutes(endValue) <= toMinutes(startValue)) {
    status.textContent = "Die Endzeit muss nach der Startzeit liegen.";
    return;
  }

  const selectedTopicId = $("#blockEditorTopic").value || null;
  const previousSourceTopicId = block.source_topic_id || block.topic_id || null;
  if (block.split_part && selectedTopicId && selectedTopicId === previousSourceTopicId) {
    block.source_topic_id = selectedTopicId;
  } else {
    block.topic_id = selectedTopicId;
    block.source_topic_id = selectedTopicId;
    block.split_part = null;
    block.split_parts = null;
  }
  block.title = title;
  block.type = $("#blockEditorType").value;
  block.week = week;
  block.day = $("#blockEditorDay").value;
  block.trainer = $("#blockEditorTrainer").value || "";
  block.start = startValue;
  block.end = endValue;
  block.room = $("#blockEditorRoom").value.trim();
  block.description = $("#blockEditorDescription").value.trim();
  block.notes = $("#blockEditorNotes").value.trim();
  block.background_color = $("#blockEditorColor").value || "#ffffff";

  if (block.trainer && !(project.trainers || []).includes(block.trainer)) project.trainers = [...(project.trainers || []), block.trainer];
  if (!(project.manual_weeks || []).includes(week) && !project.blocks.some((item) => item !== block && Number(item.week || 1) === week)) {
    project.manual_weeks = [...(project.manual_weeks || []), week].sort((a, b) => a - b);
  }
  hideEmptyTransientWeek(previousWeek);
  hideEmptyTransientWeek(week);
  syncTrainerLegacy();
  $("#blockEditorModal").hidden = true;
  blockEditorBlockId = null;
  document.body.classList.remove("modal-open");
  await validateAndRender();
}

function copyBlock(id) {
  const block = project.blocks.find((item) => item.id === id);
  if (!block) return;
  project.blocks.push({ ...block, id: crypto.randomUUID(), title: `${block.title} Kopie` });
  validateAndRender();
}

function removeBlock(id) {
  const removed = project.blocks.find((block) => block.id === id);
  project.blocks = project.blocks.filter((block) => block.id !== id);
  if (removed) hideEmptyTransientWeek(Number(removed.week || 1));
  if (cutBlockId === id) cutBlockId = null;
  validateAndRender();
}

async function validateAndRender() {
  const response = await fetch("api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(project)
  });
  if (response.ok) {
    project.warnings = (await response.json()).warnings;
  }
  render();
}

function renderPreview() {
  const start = toMinutes(project.settings.day_start);
  const end = toMinutes(project.settings.day_end);
  const totalMinutes = Math.max(60, end - start);
  const height = (totalMinutes / 60) * calendarHourHeight;
  const trainers = calendarTrainers();
  const productName = currentProduct().name;
  const customer = project.customer_data_required ? (project.customer_name || "—") : "Nicht erforderlich";
  const location = project.customer_data_required ? (project.location || "—") : "Nicht erforderlich";
  const totals = totalMinutesByType();
  const serviceDays = serviceDayCount();
  const unscheduled = project.unscheduled_topics.reduce((sum, item) => sum + item.duration_minutes, 0);
  $("#tab-preview").innerHTML = `<div class="calendar-preview">
    <p class="muted">PDF-Vorschau: Seite 1 ist die Uebersicht. Danach folgen die Kalenderseiten im A4-Querformat chronologisch nach Kalenderwoche und Trainer.</p>
    <div class="pdf-preview-pages">
      <section class="pdf-preview-sheet pdf-preview-overview-sheet">
        <div class="pdf-preview-header">
          <div>
            <h2>${escapeHtml(project.title || "Schulungsplan")}</h2>
            <p>Planuebersicht</p>
          </div>
          <div class="pdf-preview-customer"><strong>Kunde: ${escapeHtml(customer)}</strong><strong>Standort: ${escapeHtml(location)}</strong></div>
        </div>
        <div class="pdf-preview-overview-body">
          ${projectOverviewMeta()}
          <div class="metric-grid">
            ${metric("Schulung", totals.training || 0)}
            ${metricValue("Dienstleistungstage", formatServiceDays(serviceDays))}
            ${metric("Nicht eingeplant", unscheduled)}
          </div>
          <div class="product-summary">${productSummary()}</div>
          <div class="output-wrap"><div class="output-content">${topicSummary()}</div></div>
        </div>
      </section>
      ${scheduledWeeks().map((week) => trainers.map((trainer, trainerIndex) => `
        <section class="pdf-preview-sheet">
          <div class="pdf-preview-header">
            <div>
              <h2>${escapeHtml(project.title || "Schulungsplan")}</h2>
              <p>Produkt: ${escapeHtml(productName)} &nbsp;|&nbsp; Trainer: ${escapeHtml(trainerLabel(trainer))} &nbsp;|&nbsp; Woche ${week}</p>
            </div>
            <div class="pdf-preview-customer"><strong>Kunde: ${escapeHtml(customer)}</strong><strong>Standort: ${escapeHtml(location)}</strong></div>
          </div>
          <h3 class="pdf-preview-week-heading">${weekHeading(week)}</h3>
          <div class="calendar-week" style="--calendar-height:${height}px">
            ${days.map((day) => dayHtml(day, start, height, week, trainer, trainerIndex, false)).join("")}
          </div>
        </section>
      `).join("")).join("")}
    </div>
  </div>`;
}

function normalizeProjectState() {
  project.blocks = Array.isArray(project.blocks) ? project.blocks : [];
  project.manual_weeks = Array.isArray(project.manual_weeks) ? project.manual_weeks : [];
  project.settings = project.settings || { ...defaultSettings };
  ["day_start", "lunch_window_start", "monday_arrival_start", "thursday_departure_start"].forEach((key) => {
    if (project.settings[key]) project.settings[key] = snapTimeValue(project.settings[key]);
  });
  project.trainers = Array.isArray(project.trainers) ? project.trainers.map((name) => String(name || "").trim()).filter(Boolean) : [];
  if (!project.trainers.length && String(project.trainer || "").trim()) project.trainers = [String(project.trainer).trim()];
  project.blocks.forEach((block) => {
    const name = String(block.trainer || "").trim();
    if (name && !project.trainers.includes(name)) project.trainers.push(name);
    normalizeBlockStart(block);
  });
  if (project.trainers.length) {
    project.blocks.forEach((block) => {
      if (!String(block.trainer || "").trim()) block.trainer = project.trainers[0];
    });
  }
  syncTrainerLegacy();
}

async function exportProjectState() {
  setStatus("Planungsstand wird exportiert...");
  const response = await fetch("api/project/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(project)
  });
  if (!response.ok) {
    setStatus("Planungsstand konnte nicht exportiert werden.");
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = projectExportFilename();
  link.click();
  URL.revokeObjectURL(url);
  setStatus("Planungsstand exportiert.");
}

function safeFilenamePart(value, fallback) {
  const source = String(value || fallback || "").trim().normalize("NFKD");
  let result = "";
  let separatorPending = false;
  for (const char of source) {
    const code = char.charCodeAt(0);
    const asciiLetter = (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
    const digit = code >= 48 && code <= 57;
    if (asciiLetter || digit) {
      if (separatorPending && result) result += "-";
      result += char;
      separatorPending = false;
    } else if (char === "-") {
      separatorPending = Boolean(result);
    } else if (code < 0x0300 || code > 0x036f) {
      separatorPending = Boolean(result);
    }
  }
  return result || String(fallback || "wert");
}

function projectExportFilename(now = new Date()) {
  const productName = currentProduct()?.name || project.product_id || "produkt";
  const customer = project.customer_data_required ? project.customer_name : "ohne-kunde";
  const location = project.customer_data_required ? project.location : "ohne-standort";
  const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const time = `${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}`;
  return `${safeFilenamePart(customer, "kunde")}_${safeFilenamePart(location, "standort")}_${safeFilenamePart(productName, "produkt")}_${date}_${time}.json`;
}

async function importProjectState(event) {
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!file) return;
  setStatus("Planungsstand wird importiert...");
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("api/project/import", { method: "POST", body: formData });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    setStatus(payload.detail || "Planungsstand konnte nicht importiert werden.");
    return;
  }
  project = payload.project;
  normalizeProjectState();
  transientManualWeeks = new Set();
  cutBlockId = null;
  draggedBlockId = null;
  currentPage = "plan";
  activeTab = "week";
  planInputsDirty = false;
  currentWorkflowStep = "review";
  workflowErrors = {};
  render();
  setStatus("Planungsstand geladen.");
}

async function downloadExport(format) {
  setStatus(`${format.toUpperCase()} wird erstellt...`);
  const response = await fetch("api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project, format })
  });
  if (!response.ok) {
    setStatus("Export konnte nicht erstellt werden.");
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `schulungsplan.${format}`;
  link.click();
  URL.revokeObjectURL(url);
  setStatus("Export erstellt.");
}

function totalMinutesByType() {
  return project.blocks.reduce((acc, block) => {
    acc[block.type] = (acc[block.type] || 0) + duration(block.start, block.end);
    return acc;
  }, {});
}

function duration(start, end) {
  return toMinutes(end) - toMinutes(start);
}

function toMinutes(value) {
  const [hour, minute] = value.split(":").map(Number);
  return hour * 60 + minute;
}

function formatTime(minutes) {
  const hour = Math.floor(minutes / 60);
  const minute = minutes % 60;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return hours ? `${hours} h ${rest} min` : `${rest} min`;
}

function formatHours(minutes) {
  const hours = Math.max(0, Number(minutes) || 0) / 60;
  const value = Number.isInteger(hours) ? hours.toFixed(1) : String(Math.round(hours * 100) / 100);
  return `${value.replace(".", ",")} h`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}
