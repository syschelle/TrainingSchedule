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
    participant_group: "Radiologen, Radiologen Keyuser, MFA, Kliniker, Webviewer und Administratoren",
    start_date: "2026-09-07",
    end_date: null,
    settings: { ...defaultSettings },
    product_lines: [
      {
        id: "deepunity-pacs",
        name: "DeepUnity PACS",
        description: "PACS-Schulungen fuer Radiologie, Keyuser, MFA, Kliniker, Webviewer und Administration.",
        participant_groups: [
          participantGroup("radiologen", "Radiologen", 12),
          participantGroup("radiologen-keyuser", "Radiologen Keyuser", 4),
          participantGroup("mfa", "MFA", 8),
          participantGroup("kliniker", "Kliniker", 15),
          participantGroup("webviewer", "Webviewer", 20),
          participantGroup("administratoren", "Administratoren", 3)
        ]
      }
    ],
    topics: [
      topic("pacs-admin", "PACS-Administration", 360, 1, "Uebersicht, Installation, Rechte, Rollen und Webinterface."),
      topic("diagnost-basic", "DU Diagnost Basic", 90, 1, "Grundlagen im Umgang mit der DeepUnity DIAGNOST Anwendung."),
      topic("diagnost-erweitert", "DU Diagnost erweitert", 120, 2, "Erweiterte Funktionen der Befundungsworkstation.", "diagnost-basic"),
      topic("diagnost-keyuser", "DU Diagnost KeyUser", 180, 2, "Konfigurationsoberflaeche und Verteilung der Client Software.", "diagnost-erweitert"),
      topic("review-kliniker", "DU Review Kliniker", 60, 3, "Grundlagen der Review Betrachtungsworkstation."),
      topic("viewer", "DU Viewer", 45, 3, "Grundfunktionen des DeepUnity Viewers."),
      topic("xchange", "DU XChange", 60, 3, "Import und Export von Patientenstudien."),
      topic("review-mtra", "DU Review MTRA", 60, 3, "Review- und XChange-Funktionen fuer MTRA.")
    ],
    blocks: [],
    manual_weeks: [],
    unscheduled_topics: [],
    warnings: []
  };
}

function topic(id, title, duration_minutes, priority, description, depends_on = null, product_id = "deepunity-pacs", background_color = "#eaf8f2") {
  return { id, product_id, participant_group_id: null, participant_group_ids: [], title, description, duration_minutes, priority, preferred_day: null, preferred_order: null, depends_on, trainer: "", room: "", notes: "", background_color };
}

function participantGroup(id, name, participant_count, product_id = "deepunity-pacs") {
  return { id, product_id, name, participant_count, notes: "" };
}

const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", () => {
  $("#openMenu").addEventListener("click", openSideMenu);
  $("#autoPlan").addEventListener("click", createPlan);
  $("#resetDemo").addEventListener("click", () => {
    project = makeDefaultProject();
    transientManualWeeks = new Set();
    activeTab = "overview";
    currentPage = "input";
    render();
  });
  $("#backToInput").addEventListener("click", () => {
    currentPage = "input";
    renderPages();
  });
  $("#addTopic").addEventListener("click", addTopic);
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
  render();
  loadProducts();
  loadTrainingContents();
});

function setStatus(text) {
  $("#status-line").textContent = text;
}

function render() {
  renderHeader();
  renderBaseFields();
  renderSettingsFields();
  renderParticipantGroups();
  renderTopics();
  renderProductMenu();
  renderContentCatalog();
  renderWarnings();
  renderTabs();
  renderPages();
  renderNavigation();
}

function renderHeader() {
  const product = currentProduct();
  const headerProduct = $("#headerProduct");
  const headerContext = $("#headerContext");
  if (headerProduct) headerProduct.textContent = `Aktives Produkt: ${product.name}`;
  if (headerContext) headerContext.textContent = `${project.title || "Schulungsplan"} - Mehrtaegige Trainings planen, pruefen und exportieren.`;
}

function renderBaseFields() {
  const customerDisabled = project.project_mode === "service_calculation";
  $("#base-fields").innerHTML = [
    modeSelector(),
    field("title", "Schulungsbezeichnung", project.title, "text", true),
    customerDisabled ? "" : field("customer_name", "Kunde", project.customer_name),
    customerDisabled ? "" : field("location", "Standort", project.location),
    trainerEditor(),
    field("start_date", "Startdatum", project.start_date || "", "date")
  ].join("");
  $("#projectMode").addEventListener("change", updateProjectMode);
  $("#base-fields").querySelectorAll("input[data-field-name]").forEach((input) => input.addEventListener("input", updateProjectField));
  $("#base-fields").querySelectorAll("input[data-trainer-index]").forEach((input) => {
    input.addEventListener("change", updateTrainerField);
    input.addEventListener("keydown", handleTrainerKeydown);
  });
  const addTrainerButton = $("#addTrainer");
  if (addTrainerButton) addTrainerButton.addEventListener("click", () => addTrainer(true));
}

function trainerEditor() {
  const values = Array.isArray(project.trainers) && project.trainers.length ? project.trainers : [""];
  return `<div class="field field-wide trainer-editor">
    <div class="trainer-editor-heading">
      <span>Trainer</span>
      <small>Enter speichert und fuegt den naechsten Trainer hinzu.</small>
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
  render();
}

function focusTrainerInput(index) {
  requestAnimationFrame(() => {
    const input = $(`#base-fields input[data-trainer-index="${index}"]`);
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
  renderBaseFields();
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
    <input data-group="${group.id}" data-key="name" value="${escapeHtml(group.name)}" aria-label="Teilnehmergruppe">
    <input data-group="${group.id}" data-key="participant_count" type="number" min="0" value="${Number(group.participant_count)}" aria-label="Teilnehmerzahl">
    <button type="button" class="icon danger" title="Loeschen" onclick="deleteParticipantGroup('${group.id}')">×</button>
  </div>`;
}

function renderSettingsFields() {
  const s = project.settings;
  $("#settings-fields").innerHTML = [
    setting("day_start", "Tagesbeginn", s.day_start, "time"),
    setting("day_end", "Tagesende", s.day_end, "time"),
    numberSetting("break_min_minutes", "Pause min.", s.break_min_minutes),
    numberSetting("break_max_minutes", "Pause max.", s.break_max_minutes),
    numberSetting("break_preferred_minutes", "Pause bevorzugt", s.break_preferred_minutes),
    numberSetting("lunch_minutes", "Mittag", s.lunch_minutes),
    setting("monday_arrival_start", "Anreise Beginn", s.monday_arrival_start, "time"),
    setting("monday_arrival_end", "Anreise Ende", s.monday_arrival_end, "time"),
    setting("thursday_departure_start", "Abreise Beginn", s.thursday_departure_start, "time"),
    setting("thursday_departure_end", "Abreise Ende", s.thursday_departure_end, "time"),
    checkboxSetting("friday_training_enabled", "Freitag fuer Schulung nutzen", s.friday_training_enabled)
  ].join("");
  $("#settings-fields").querySelectorAll("input").forEach((input) => input.addEventListener("input", updateSettingField));
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

function updateProjectField(event) {
  project[event.target.dataset.fieldName] = event.target.value;
  renderTabs();
}

function updateProjectMode(event) {
  project.project_mode = event.target.value;
  project.customer_data_required = project.project_mode !== "service_calculation";
  if (!project.customer_data_required) {
    project.customer_name = "";
    project.location = "";
  }
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
  project.product_id = event.target.value;
  ensureSelectedProductExists();
  selectedContentId = firstContentForCurrentProduct()?.id || null;
  render();
}

function updateParticipantGroupField(event) {
  const group = currentProduct().participant_groups.find((candidate) => candidate.id === event.target.dataset.group);
  if (!group) return;
  const key = event.target.dataset.key;
  group[key] = key === "participant_count" ? Number(event.target.value) : event.target.value;
  project.participant_group = currentProduct().participant_groups.map((item) => item.name).join(", ");
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
  render();
}

function deleteParticipantGroup(id) {
  const product = currentProduct();
  product.participant_groups = product.participant_groups.filter((item) => item.id !== id);
  project.participant_group = product.participant_groups.map((item) => item.name).join(", ");
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
    renderContentCatalog();
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
    topic.duration_minutes = Number(content.duration_minutes || topic.duration_minutes || 60);
    if (content.max_participants) topic.participants_per_session = Number(content.max_participants);
    topic.participant_group_ids = content.participant_group_ids || [];
    topic.participant_group_id = null;
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
  currentPage = page;
  renderPages();
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
      .filter((block) => block.topic_id === id)
      .map((block) => Number(block.week || 1))
  );
  project.topics = project.topics.filter((item) => item.id !== id);
  project.blocks = project.blocks.filter((block) => block.topic_id !== id);
  affectedWeeks.forEach((week) => hideEmptyTransientWeek(week));
  render();
}

async function createPlan() {
  setStatus("Planung wird berechnet...");
  const response = await fetch("api/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(project)
  });
  if (!response.ok) {
    setStatus("Planung konnte nicht erstellt werden.");
    return;
  }
  project = await response.json();
  normalizeProjectState();
  transientManualWeeks = new Set();
  setStatus("Plan erstellt und validiert.");
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
      .map((block) => `${Number(block.week || 1)}::${block.day}`)
  ).size;
}

function formatServiceDays(count) {
  return `${count} ${count === 1 ? "Tag" : "Tage"}`;
}

function topicSummary() {
  if (!project.topics.length) return "Noch keine Themen.";
  return project.topics.map((item) => {
    const planned = project.blocks.some((block) => block.topic_id === item.id) ? item.duration_minutes : 0;
    return `<div class="summary-row"><span>${escapeHtml(item.title)}</span><b>${planned} / ${item.duration_minutes} min</b></div>`;
  }).join("");
}

function productSummary() {
  return (project.product_lines || []).map((product) => `
    <section class="product-summary-card">
      <strong>${escapeHtml(product.name)}</strong>
      <span>${escapeHtml(product.description || "")}</span>
      <div>${product.participant_groups.map((group) => `<b>${escapeHtml(group.name)}: ${Number(group.participant_count)}</b>`).join("")}</div>
    </section>
  `).join("");
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
      <div class="calendar-help">Bloecke koennen zwischen Tagen, Wochen und Trainern verschoben werden. Jeder Trainer besitzt pro Kalenderwoche eine eigene Wochenansicht.</div>
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

function blockHtml(block, dayStart, calendarHeight, interactive = true) {
  const displayTitle = block.type === "arrival" ? "Anreise" : block.title;
  const start = toMinutes(block.start);
  const blockDuration = Math.max(calendarSnapMinutes, duration(block.start, block.end));
  const top = Math.max(0, ((start - dayStart) / 60) * calendarHourHeight);
  const height = Math.max(44, (blockDuration / 60) * calendarHourHeight);
  const cappedHeight = Math.min(height, Math.max(44, calendarHeight - top));
  return `<article class="block calendar-block ${block.type} ${block.id === cutBlockId ? "is-cut" : ""}" ${interactive ? `draggable="true" ondragstart="dragBlock(event, '${block.id}')"` : ""} style="top:${top}px;height:${cappedHeight}px;--block-bg:${escapeHtml(block.background_color || "#ffffff")}">
    <div>
      <strong>${escapeHtml(displayTitle)}</strong>
      <span>${block.start}-${block.end} · ${block.type}</span>
    </div>
    ${interactive ? `<div class="block-actions">
      <button type="button" class="icon" onclick="cutBlock('${block.id}')" title="Ausschneiden">✂</button>
      <button type="button" class="icon" onclick="editBlock('${block.id}')" title="Bearbeiten">✎</button>
      <button type="button" class="icon" onclick="copyBlock('${block.id}')" title="Duplizieren">⧉</button>
      <button type="button" class="icon danger" onclick="removeBlock('${block.id}')" title="Loeschen">×</button>
    </div>` : ""}
  </article>`;
}

function addManualWeek() {
  const nextWeek = Math.max(0, ...plannedWeeks()) + 1;
  project.manual_weeks = [...new Set([...(project.manual_weeks || []), nextWeek])].sort((a, b) => a - b);
  transientManualWeeks.add(nextWeek);
  currentPage = "plan";
  activeTab = "week";
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
  project.blocks.push({ id: crypto.randomUUID(), type: "training", week, day, title: "Neuer Block", start: "10:00", end: "11:00", topic_id: null, description: "", trainer, room: "", notes: "", background_color: "#ffffff" });
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
  topicSelect.value = block.topic_id || "";

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

  block.topic_id = $("#blockEditorTopic").value || null;
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
  render();
  setStatus(`Planungsstand geladen (${payload.app_version || "unbekannte Version"}).`);
}

function renderWarnings() {
  const warnings = project.warnings || [];
  const warningContainer = $("#warnings");
  if (warningContainer) {
    warningContainer.innerHTML = warnings.length
      ? warnings.map((warning) => `<p>${escapeHtml(warning)}</p>`).join("")
      : `<div class="validation-empty"><strong>Keine Konflikte.</strong><span>Die aktuelle Planung enthaelt keine Validierungshinweise.</span></div>`;
  }
  const count = $("#validationCount");
  if (count) count.textContent = `${warnings.length} ${warnings.length === 1 ? "Hinweis" : "Hinweise"}`;
  const nav = $("#validationNavButton");
  if (nav) {
    nav.textContent = warnings.length ? `Planungspruefung (${warnings.length})` : "Planungspruefung";
    nav.classList.toggle("has-warnings", warnings.length > 0);
  }
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

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}
