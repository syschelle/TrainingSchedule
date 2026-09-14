# Schulungsplantool – Internal Tests and Release Checks

Status: **v0.4.10**

This document describes the checks performed before a new version of Schulungsplantool is released. It distinguishes between automated regression tests in the repository, additional syntax/configuration checks, and checks that can only be fully completed in GitHub CI.

## 1. Automated Python / Regression Tests

The complete test suite is executed with Pytest:

```bash
python -m pytest -q
```

For **v0.4.10**, the result is:

```text
142 passed
```

### Test distribution in v0.4.10

| Test file | Count | Focus |
|---|---:|---|
| `tests/test_static_paths.py` | 64 | Frontend structure, UI rules, calendar, customer HTML, version regressions |
| `tests/test_planner.py` | 33 | Automatic planning, breaks, trainer availability, arrival/departure, remote/on-site |
| `tests/test_project_export.py` | 25 | Project files, PDF, customer HTML, return import, tamper protection |
| `tests/test_content_catalog.py` | 10 | Training content, products, history and persistence |
| `tests/test_docx_training_content.py` | 6 | DOCX import/export and protection against unsupported content |
| `tests/test_codeql_workflow.py` | 2 | CodeQL configuration and language matrix |
| `tests/test_security_regressions.py` | 2 | Security-related regressions |
| **Total** | **142** | |

## 2. Important Functional Regression Tests

The test suite covers, among other things, the following business rules:

- Arrival and departure are reserved correctly for **on-site training**.
- **Remote training** does not create arrival or departure blocks.
- Older projects without a delivery mode remain compatible and default to **On-site**.
- Training sessions are planned on a 15-minute grid.
- In the customer HTML, there must be at least **15 minutes of break time** between two training blocks assigned to the same trainer.
- Exactly 15 minutes of separation is accepted; less than 15 minutes is rejected during return import.
- Hidden break and lunch blocks must not prevent visible blocks from being moved in the customer HTML.
- Parked training blocks can be moved back to a valid training day.
- Training blocks placed on unavailable trainer days are recognized as parked.
- A customer return import must not allow manipulation of a block's duration.
- Manipulation of the signed source data is rejected.
- Visible blocks must not overlap.
- Automatically generated lunch breaks must not overlap training blocks.
- Trainer availability, including explicitly unavailable days, is respected.
- Multiple trainers can be planned in parallel without incorrectly blocking each other.
- Project files can be exported and imported again without losing planning state.

## 3. JavaScript Syntax Checks

All currently used JavaScript files are additionally checked for syntax errors with Node.js:

```bash
node --check app/static/app.js
node --check app/static/calendar.js
node --check app/customer_assets/app.js
```

This catches, among other things, syntax errors that might otherwise only become visible in the browser.

## 4. GitHub Workflow / YAML Validation

The GitHub workflow files are checked for valid YAML structure:

```text
.github/workflows/ci.yml
.github/workflows/codeql.yml
.github/workflows/release-image.yml
```

The Pytest suite also contains regression tests for the CodeQL workflow. In particular, it verifies that only the intended CodeQL languages are configured and that `actions` is not accidentally re-enabled as a separate analysis language.

## 5. CodeQL

CodeQL is configured for the following languages:

```text
python
javascript-typescript
```

The actual CodeQL analysis runs in GitHub Actions. The GitHub CodeQL infrastructure cannot be fully reproduced locally or in the internal test environment.

Before tagging a new version, the CodeQL jobs in GitHub should therefore be verified as successful.

## 6. Docker / Compose Checks

GitHub CI additionally runs the following checks:

```bash
docker compose -f docker-compose.yml config >/dev/null
docker compose -f docker-compose.images.yml config >/dev/null
docker build --build-arg APP_VERSION="$(cat VERSION)" -t schulungsplantool:ci .
```

These checks validate both Compose files and build the application image.

**Important:** If no Docker CLI is available in the internal execution environment, these checks cannot be run there. In that case, they are not reported as locally passed; the GitHub CI run is authoritative.

## 7. Release Checks Before Tagging

Before creating a release tag, at least the following should be true:

- `python -m pytest -q` is fully green.
- JavaScript syntax checks are green.
- GitHub workflow YAML is valid.
- GitHub CI is green.
- CodeQL is green.
- The version number in `VERSION` matches the intended release version.
- Only after that should the Git tag be created and pushed.

Recommended process:

```bash
git add .
git commit -m "Release vX.Y.Z: <description>"
git push origin main
```

Then verify CI and CodeQL. If both complete successfully:

```bash
git tag -a vX.Y.Z -m "Schulungsplantool vX.Y.Z"
git push origin vX.Y.Z
```

## 8. Additional Checks for Customer HTML Changes

When drag & drop, parking, remote/on-site behavior, or return import is changed, additional targeted regression tests are added. Typical scenarios include:

1. Move a block within the same day.
2. Move a block to another valid day.
3. Move a parked block back to a valid day.
4. Target position overlaps a hidden break.
5. Target position would create less than 15 minutes of separation from the previous training block.
6. Target position would create less than 15 minutes of separation from the following training block.
7. Exactly 15 minutes of separation must be accepted.
8. Overlaps between visible blocks must be rejected.
9. The duration of the moved block must remain unchanged.
10. Remote projects must not contain arrival or departure blocks.

## 9. Known Notes in v0.4.10

The current test suite reports two `DeprecationWarning` messages from FastAPI regarding `@app.on_event("startup")`. These warnings do not cause test failures, but the code should be migrated to FastAPI lifespan handlers in a later version.

```text
142 passed, 2 warnings
```

## 10. Principle for Future Releases

A version is not considered fully verified merely because individual tests passed. For a release, all available local checks are executed, followed by separate verification of GitHub CI and CodeQL. If a check cannot be performed because a required runtime tool is unavailable — for example Docker — this is stated explicitly.
