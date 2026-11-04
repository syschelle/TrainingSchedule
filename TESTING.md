# Schulungsplantool – Internal Tests and Release Checks

Status: **v0.5.0-beta.5 (Pre-Release)**

This document describes the checks performed before a Schulungsplantool release or pre-release. It is updated together with the current application version.

## 1. Automated Python / Regression Tests

Run the complete suite with:

```bash
python -m pytest -q
```

For **v0.5.0-beta.5**, the current local result is:

```text
156 passed, 2 warnings
```

The two warnings are the known FastAPI deprecation warnings for `@app.on_event("startup")`; they are not test failures.

### Test distribution

| Test file | Count | Focus |
|---|---:|---|
| `tests/test_static_paths.py` | 70 | Frontend structure, UI rules, calendar, customer HTML, version regressions, master-data UI wiring |
| `tests/test_planner.py` | 33 | Automatic planning, breaks, availability, arrival/departure, remote/on-site |
| `tests/test_project_export.py` | 25 | Project files, PDF, customer HTML, return import and tamper protection |
| `tests/test_content_catalog.py` | 10 | Training contents, products, history and persistence |
| `tests/test_docx_training_content.py` | 6 | DOCX import/export and unsupported-content protection |
| `tests/test_master_data_collection.py` | 6 | Master-data template seed, extension, ordering, deletion and project compatibility |
| `tests/test_release_docs.py` | 2 | Root TESTING/SECURITY documentation and version consistency |
| `tests/test_codeql_workflow.py` | 2 | CodeQL configuration and language matrix |
| `tests/test_security_regressions.py` | 2 | Security-related regressions |
| **Total** | **156** | |

## 2. Master Data Collection Regression Coverage

The pre-release includes dedicated regression coverage for the customer master-data collection appointment:

- opening the Master Data Collection page refreshes its project context from the current project model;
- customer name and project number entered in Project master data are shown in the collection appointment;

- the DeepUnity PACS default template contains exactly 17 numbered blocks;
- the initial order is `1..17`;
- blocks are product-bound, extendable, reorderable and deletable;
- reordering normalizes the complete template to a gap-free sequence;
- manually edited template content survives another database seed;
- old project files without master-data fields remain valid;
- project snapshots serialize completion state and project-specific notes;
- the collection is an optional customer appointment inside a normal `training_plan` project, not a replacement project mode;
- legacy beta.1/beta.2 files using `project_mode=master_data_collection` are normalized to `training_plan` with the collection enabled;
- project number, collection date, start time, duration, Dedalus participants, customer participants and appointment-completed state serialize correctly;
- the guided flow inserts Master Data Collection between Project and People when enabled;
- the collection page explicitly continues with **Training Planning** afterward;
- the page documents that Training Planning itself remains one topic of the collection;
- the frontend remains wired to the `/api/master-data-blocks` template endpoints.


## 3. Beta.4 Layout Regression Coverage

The beta.4 pre-release adds a focused frontend regression check for the Master Data Collection workspace:

- the project Master Data Collection page spans the full available workspace width;
- the Master Data Template configuration also spans the full workspace width;
- the template editor uses a responsive left navigation / flexible right editor grid on desktop;
- the Markdown editor receives a larger desktop editing area;
- the template manager collapses back to a single column on narrow screens.

No application data model or master-data business rules are changed by beta.4.

## 4. Existing Functional Regression Coverage

The suite continues to cover, among other rules:

- remote projects create no arrival/departure blocks;
- on-site projects preserve travel planning;
- old projects default to on-site;
- training sessions use the 15-minute grid;
- customer HTML enforces at least 15 minutes between training blocks for the same trainer;
- hidden break/lunch reservations do not prevent valid customer moves;
- parked blocks can return to valid trainer days;
- customer return files cannot change block duration or signed baseline data;
- visible blocks cannot overlap;
- trainer availability and unavailable days are enforced;
- project files round-trip without losing planning state.

## 5. JavaScript Syntax Checks

Run:

```bash
node --check app/static/app.js
node --check app/static/calendar.js
node --check app/customer_assets/app.js
```

All three files must pass before release.

## 6. Python Syntax Checks

Key server modules are additionally compiled before packaging:

```bash
python -m py_compile app/server/models.py app/server/content_db.py app/server/main.py
```

## 7. GitHub Workflow / YAML Validation

The repository contains:

```text
.github/workflows/ci.yml
.github/workflows/codeql.yml
.github/workflows/release-image.yml
```

The CodeQL regression tests ensure the explicit language matrix remains limited to:

```text
python
javascript-typescript
```

GitHub Actions must not be reintroduced as a separate CodeQL language.


## 8. API CRUD Smoke Check

The new master-data API was additionally exercised against a temporary file-backed SQLite database through FastAPI `TestClient`:

```text
GET    /api/master-data-blocks?product_id=deepunity-pacs -> 200 / 17 seed blocks
POST   /api/master-data-blocks                            -> 200 / block 18 created
PUT    /api/master-data-blocks/{id}                       -> 200 / moved to position 2
DELETE /api/master-data-blocks/{id}                       -> 204
```

This is a supplemental smoke check in addition to the repository regression tests.

## 9. CodeQL

The actual CodeQL analysis runs on GitHub. Before tagging a release or pre-release, both configured CodeQL analysis jobs must be green.

The repository uses Advanced Setup. GitHub Default Setup must remain disabled to avoid conflicting SARIF uploads.

## 10. Docker / Compose Checks

GitHub CI additionally validates:

```bash
docker compose -f docker-compose.yml config >/dev/null
docker compose -f docker-compose.images.yml config >/dev/null
docker build --build-arg APP_VERSION="$(cat VERSION)" -t schulungsplantool:ci .
```

If Docker is unavailable in the local/internal execution environment, these checks are not claimed as locally passed; GitHub CI is authoritative.

## 11. Release Checklist

Before creating a tag:

- full Pytest suite is green;
- JavaScript syntax checks are green;
- Python syntax checks are green;
- workflow YAML is valid;
- GitHub CI is green;
- CodeQL is green;
- `VERSION`, frontend asset versions, Docker image version and `APP_VERSION` match;
- `README.md`, `CHANGELOG.md`, `TESTING.md` and `SECURITY.md` describe the same version.

For a pre-release, create a pre-release tag and mark the GitHub release as a pre-release.

The Docker release workflow is also regression-tested so a pre-release version (for example `0.5.0-beta.5`) does **not** publish or move the `latest` image tag.

## 12. Current Known Notes

FastAPI currently emits two deprecation warnings for `@app.on_event("startup")`. A later refactor should migrate startup handling to a lifespan context.

No failure is currently associated with these warnings.
