# ContextAI — Context-Aware Multi-Agent Conversational Platform

A production-grade, multi-agent AI platform built with **FastAPI + LangGraph** (backend)
and **Next.js 15 + TypeScript + Tailwind** (frontend). It does two things really well:

1. **Document Q&A** — upload a PDF, ask questions, get answers grounded only in the
   document, with page-level citations and a confidence score.
2. **Conversational appointment booking** — a stateful, multi-turn flow that collects
   name / email / phone / date, validates each field, parses natural-language dates,
   and remembers everything across the conversation (and across context switches back
   and forth between booking and document Q&A).

It is architected as a **Supervisor + specialist agents** system, orchestrated with
LangGraph, not a single monolithic prompt.

---

## 1. Architecture

```
Next.js Frontend  →  FastAPI Gateway  →  LangGraph Supervisor  →  Intent Router
                                                                      │
                                ┌─────────────────────────────────────┼─────────────────────┐
                                │                 │                   │                     │
                        Document Agent   Appointment Agent      Memory Agent        (Validation + Date
                          (RAG/Chroma)    (booking state          (profile/         Agents are invoked
                                            machine)              history)          synchronously by the
                                                                                     Appointment Agent)
                                │
                          PostgreSQL/SQLite + ChromaDB
```

Full Mermaid diagrams (system architecture, LangGraph workflow, ER diagram, RAG
pipeline, agent sequence) are in [`docs/diagrams.md`](docs/diagrams.md).

### Agents

| Agent | Responsibility |
|---|---|
| **Supervisor** | Intent classification, context routing, agent selection |
| **Document Agent** | PDF retrieval, hybrid semantic search, reranking, citation generation, confidence scoring |
| **Appointment Agent** | Drives the `WAITING_NAME → WAITING_EMAIL → WAITING_PHONE → WAITING_DATE → CONFIRMATION → BOOKED` state machine |
| **Validation Agent** | Name / email (RFC) / phone (international, via `phonenumbers`) validation with friendly error messages |
| **Date Agent** | Converts "tomorrow", "next Monday", "coming Friday", "in 2 days" → `YYYY-MM-DD`, with confidence |
| **Memory Agent** | Answers "what email did I provide earlier?", "what appointment did I book?", "when did we last talk?" from persisted profile/session/appointment history |

---

## 2. Tech Stack

**Backend:** FastAPI, LangGraph, SQLAlchemy + Alembic, SQLite (default) / PostgreSQL, ChromaDB, Pydantic v2, slowapi (rate limiting), loguru.

**Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS, lucide-react.

**AI / NLP:** Pluggable LLM client (`Ollama` qwen3:8b, any OpenAI-compatible API, or a deterministic **offline mode** so the whole platform is demoable with zero AI infra). PyMuPDF for PDF extraction, `dateparser` + a custom weekday resolver for date extraction, `phonenumbers` + `email-validator` for validation.

> **Why offline mode exists:** the original spec assumes a local Ollama install. To
> guarantee this runs out-of-the-box on *any* machine, the Document Agent falls back to
> extractive answers (best-matching chunk) when no LLM is configured, and all other
> agents (validation, date parsing, booking, memory) are already 100% deterministic —
> they never depended on an LLM in the first place.

---

## 3. Project Structure

```
ai-platform/
├── backend/
│   ├── app/
│   │   ├── agents/         # supervisor, document, appointment, validation, date, memory
│   │   ├── api/             # chat, documents, appointments, analytics routers
│   │   ├── core/            # config, logging
│   │   ├── db/               # SQLAlchemy models + session
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # llm_client, embeddings, vector_store
│   │   └── main.py
│   ├── alembic/              # migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                  # dashboard, chat, documents, appointments, analytics, settings
│   ├── components/
│   ├── lib/api.ts
│   ├── Dockerfile
│   └── .env.example
├── docs/
│   └── diagrams.md
└── docker-compose.yml
```

---

## 4. Setup — Local (no Docker)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
Backend is now live at `http://localhost:8000` (interactive docs at `/docs`).

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Frontend is now live at `http://localhost:3000`.

---

## 5. Setup — Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

---

## 6. Environment Variables

### `backend/.env`
| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./app.db` | swap for `postgresql+psycopg2://user:pass@host/db` |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | local, file-based vector store |
| `LLM_PROVIDER` | `offline` | `offline` \| `ollama` \| `openai` |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `qwen3:8b` | used if `LLM_PROVIDER=ollama` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | — | used if `LLM_PROVIDER=openai` |
| `MAX_UPLOAD_MB` | `25` | PDF upload size limit |
| `CORS_ORIGINS` | `http://localhost:3000` | comma-separated |

### `frontend/.env.local`
| Variable | Default |
|---|---|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000/api` |

---

## 7. API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Main conversational endpoint — handles document Q&A, booking, and memory turns |
| `POST` | `/api/documents/upload` | Upload + ingest a PDF (multipart/form-data, field `file`) |
| `GET` | `/api/documents` | List uploaded documents |
| `DELETE` | `/api/documents/{id}` | Delete a document and its vectors |
| `POST` | `/api/appointments/create` | Direct (non-conversational) appointment creation, fully validated |
| `GET` | `/api/appointments` | List all appointments |
| `GET` | `/api/analytics` | Usage metrics (chats, appointments, users, documents, agent utilization, avg response time) |
| `GET` | `/api/health` | Health check |

Full OpenAPI docs are auto-generated at `http://localhost:8000/docs`.

---

## 8. Demo Script

1. Open `http://localhost:3000/documents`, upload a PDF (e.g. an employee handbook).
2. Go to `/chat`, ask: **"What is the cancellation policy?"** → see the answer with page citation + confidence.
3. Say: **"Book an appointment"** → Appointment Agent starts the state machine.
4. Enter a name, then an **invalid email** → Validation Agent rejects it with a friendly message; enter a valid one.
5. Enter a phone number, then say **"next Monday"** → Date Agent converts it to `YYYY-MM-DD`.
6. Confirm with **"yes"** → appointment is persisted.
7. Ask: **"What email did I provide earlier?"** → Memory Agent answers from profile.
8. Ask: **"What appointment did I book?"** → Memory Agent answers from appointment history.
9. Open `/analytics` to see live agent utilization and response-time metrics.

---

## 9. Troubleshooting

- **`alembic upgrade head` fails with "table already exists"** — delete `app.db` and re-run, or just run the app once (it calls `Base.metadata.create_all` on startup as a safety net).
- **Chroma telemetry warnings in logs** (`Failed to send telemetry event...`) — harmless; ChromaDB's anonymous telemetry call signature mismatch in this version. Does not affect functionality.
- **Frontend can't reach backend** — check `NEXT_PUBLIC_API_BASE` and `CORS_ORIGINS` match your ports.
- **Want real LLM answers instead of extractive offline mode** — install [Ollama](https://ollama.com), `ollama pull qwen3:8b`, set `LLM_PROVIDER=ollama` in `backend/.env`. Or set `LLM_PROVIDER=openai` + `OPENAI_API_KEY`.
- **Date phrases not parsing** — the Date Agent has a built-in resolver for `tomorrow`, `today`, `in N days`, and `next/coming/this <weekday>` that runs before falling back to `dateparser`, since some `dateparser` versions mishandle "next Monday"-style phrasing.

---

## 10. Security Notes

- Uploads are restricted to PDF, size-capped, and written under a UUID-prefixed filename (no path traversal).
- All chat/appointment input is validated via Pydantic schemas before reaching agents.
- SQLAlchemy ORM (no raw SQL string interpolation) — no SQL injection surface.
- Rate limiting is wired via `slowapi` (`RATE_LIMIT` env var).
- CORS is explicitly allow-listed via `CORS_ORIGINS`.
- Change `SECRET_KEY` before any real deployment.
