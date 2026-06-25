import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.db.session import get_db
from app.db import models
from app.schemas.schemas import DocumentOut
from app.core.config import settings
from app.agents.document_agent import ingest_pdf

router = APIRouter(tags=["documents"])

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/documents/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...), db: DBSession = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_MB}MB.")

    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
    filepath = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(contents)

    document = models.Document(
        filename=file.filename,
        filepath=filepath,
        size_bytes=len(contents),
        status="PROCESSING",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    document = ingest_pdf(db, document)

    db.add(models.AnalyticsEvent(event_type="document_upload", meta={"filename": file.filename}))
    db.commit()

    return document


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: DBSession = Depends(get_db)):
    return db.query(models.Document).order_by(models.Document.uploaded_at.desc()).all()


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: DBSession = Depends(get_db)):
    from app.services import vector_store
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    vector_store.delete_document(document_id)
    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)
    db.delete(doc)
    db.commit()
    return {"status": "deleted"}
