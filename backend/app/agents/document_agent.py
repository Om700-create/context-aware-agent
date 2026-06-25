"""
Document Intelligence Agent.

Implements the enterprise RAG pipeline:
  PDF Upload -> Text Extraction (PyMuPDF) -> Metadata Extraction ->
  Semantic Chunking -> Embedding Generation -> ChromaDB ->
  Hybrid Retrieval (vector + keyword overlap rerank) -> Context Builder ->
  LLM -> Answer + Citations + Confidence
"""
import os
import re
import fitz  # PyMuPDF
from sqlalchemy.orm import Session as DBSession
from app.db import models
from app.services import vector_store
from app.services.llm_client import llm_client
from app.core.logging import logger

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def ingest_pdf(db: DBSession, document: models.Document) -> models.Document:
    """Extracts text page-by-page, chunks it, embeds it, and stores in Chroma."""
    try:
        doc = fitz.open(document.filepath)
        all_chunks = []  # (page_number, text)
        for page_index in range(len(doc)):
            page = doc[page_index]
            page_text = page.get_text()
            for chunk in _chunk_text(page_text):
                if chunk.strip():
                    all_chunks.append((page_index + 1, chunk))

        document.num_pages = len(doc)
        ids, texts, metadatas = [], [], []
        for i, (page_num, chunk_text) in enumerate(all_chunks):
            db_chunk = models.DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                page_number=page_num,
                text=chunk_text,
            )
            db.add(db_chunk)
            db.flush()
            db_chunk.vector_id = db_chunk.id
            ids.append(db_chunk.id)
            texts.append(chunk_text)
            metadatas.append({
                "document_id": document.id,
                "filename": document.filename,
                "page": page_num,
                "chunk_index": i,
            })

        if ids:
            vector_store.add_chunks(ids, texts, metadatas)

        document.num_chunks = len(ids)
        document.status = "READY"
        db.commit()
        logger.info(f"Ingested document {document.filename}: {document.num_pages} pages, {len(ids)} chunks")
    except Exception as e:
        logger.exception(f"Failed to ingest document {document.filename}: {e}")
        document.status = "FAILED"
        db.commit()
    return document


def _rerank(query: str, docs: list[str], metadatas: list[dict], distances: list[float]):
    """Simple hybrid rerank: blend vector distance with keyword overlap score."""
    query_terms = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
    scored = []
    for text, meta, dist in zip(docs, metadatas, distances):
        terms = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
        overlap = len(query_terms & terms) / (len(query_terms) or 1)
        vector_score = max(0.0, 1.0 - dist)  # cosine distance -> similarity
        final_score = 0.6 * vector_score + 0.4 * overlap
        scored.append((final_score, text, meta))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def run_document_agent(db: DBSession, question: str, top_k: int = 5) -> dict:
    """Answers a question using only retrieved document content; returns
    answer text, confidence score, and source citations."""
    has_docs = db.query(models.Document).filter(models.Document.status == "READY").count() > 0
    if not has_docs:
        return {
            "answer": "No documents have been uploaded yet. Please upload a PDF before asking document questions.",
            "confidence": 0.0,
            "citations": [],
        }

    result = vector_store.query(question, n_results=top_k)
    docs = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    if not docs:
        return {
            "answer": "I couldn't find relevant content in the uploaded documents to answer that.",
            "confidence": 0.0,
            "citations": [],
        }

    reranked = _rerank(question, docs, metadatas, distances)
    top = reranked[:3]
    context = "\n\n".join([f"[{m['filename']} p.{m['page']}] {t}" for _, t, m in top])

    system = (
        "You are a precise document Q&A assistant. Answer ONLY using the provided context. "
        "If the answer is not in the context, say you don't know. Be concise."
    )
    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    from app.core.config import settings
    if settings.LLM_PROVIDER == "offline":
        # Deterministic extractive fallback: surface the most relevant chunk directly.
        best_text = top[0][1].strip()
        answer = best_text[:400] + ("..." if len(best_text) > 400 else "")
    else:
        answer = llm_client.complete(system, prompt)

    avg_score = sum(s for s, _, _ in top) / len(top)
    confidence = round(min(0.99, max(0.05, avg_score)), 2)

    citations = [
        {"document": m["filename"], "page": m["page"], "snippet": t[:160].strip() + "..."}
        for _, t, m in top
    ]

    return {"answer": answer, "confidence": confidence, "citations": citations}
