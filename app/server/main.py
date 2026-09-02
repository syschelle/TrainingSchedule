from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .content_db import create_product, create_training_content, db_session, init_database, list_products, list_training_contents, update_training_content
from .exporter import export_pdf, export_xlsx
from .importer import build_project_from_uploads
from .models import ExportRequest, ProductCreate, TrainingContentCreate, TrainingContentUpdate, TrainingProject
from .planner import plan_project, validate_project

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "25"))
APP_VERSION = os.environ.get("APP_VERSION", "0.2.23")
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

app = FastAPI(title="Schulungsplantool", version=APP_VERSION)


@app.middleware("http")
async def no_cache_for_app_assets(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in {"/", "/index.html", "/app.js", "/styles.css"}:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.on_event("startup")
def startup() -> None:
    init_database()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/products")
def products(session: Session = Depends(db_session)) -> dict:
    return {"items": list_products(session)}


@app.post("/api/products")
def add_product(payload: ProductCreate, session: Session = Depends(db_session)) -> dict:
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Produktname ist erforderlich.")
    return create_product(session, payload.name, payload.description)


@app.get("/api/training-contents")
def training_contents(product_id: str | None = None, session: Session = Depends(db_session)) -> dict:
    return {"items": list_training_contents(session, product_id)}


@app.post("/api/training-contents")
def add_training_content(payload: TrainingContentCreate, session: Session = Depends(db_session)) -> dict:
    if not payload.product_id.strip() or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Produkt und Titel sind erforderlich.")
    try:
        return create_training_content(session, payload.product_id, payload.title)
    except ValueError as error:
        if str(error) == "product_not_found":
            raise HTTPException(status_code=404, detail="Produkt wurde nicht gefunden.") from error
        raise


@app.put("/api/training-contents/{content_id}")
def save_training_content(content_id: str, payload: TrainingContentUpdate, session: Session = Depends(db_session)) -> dict:
    updated = update_training_content(session, content_id, payload.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="Schulungsinhalt wurde nicht gefunden.")
    return updated


async def _read_upload(upload: UploadFile) -> tuple[str, bytes]:
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"{upload.filename} ist groesser als {MAX_UPLOAD_MB} MB.")
    return upload.filename or "upload", data


@app.post("/api/import")
async def import_files(files: list[UploadFile] = File(...)) -> dict:
    excel_files: list[tuple[str, bytes]] = []
    pdf_files: list[tuple[str, bytes]] = []
    for upload in files:
        name, data = await _read_upload(upload)
        lower = name.lower()
        if lower.endswith((".xlsx", ".xlsm")):
            excel_files.append((name, data))
        elif lower.endswith(".pdf"):
            pdf_files.append((name, data))
        else:
            raise HTTPException(status_code=400, detail=f"Nicht erlaubter Dateityp: {name}")
    if not excel_files and not pdf_files:
        raise HTTPException(status_code=400, detail="Bitte mindestens eine Excel- oder PDF-Datei hochladen.")
    summary = build_project_from_uploads(excel_files, pdf_files)
    return summary.model_dump(mode="json")


@app.post("/api/plan")
def plan(project: TrainingProject) -> dict:
    return plan_project(project).model_dump(mode="json")


@app.post("/api/validate")
def validate(project: TrainingProject) -> dict:
    return {"warnings": validate_project(project)}


@app.post("/api/export")
def export(request: ExportRequest) -> Response:
    if request.format == "pdf":
        return Response(
            export_pdf(request.project),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="schulungsplan.pdf"'},
        )
    return Response(
        export_xlsx(request.project),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="schulungsplan.xlsx"'},
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
