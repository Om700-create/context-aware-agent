# System Architecture — Context-Aware Conversational Agent

> **LLM Provider:** Ollama (local, offline) · Model: `llama3.2:1b` · Embeddings: `nomic-embed-text`

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │                    React Frontend                            │   │
│   │   Chat UI  ·  Document Upload  ·  Mode Badge (QA / Booking) │   │
│   └────────────────────────┬─────────────────────────────────────┘   │
└───────────────────────────│──────────────────────────────────────────┘
                             │  HTTP JSON  (POST /chat, POST /upload-document)
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                  │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │               FastAPI Backend  (port 8000)                   │   │
│   │   POST /chat · POST /upload-document · GET /documents        │   │
│   │   SECRET_KEY · CORS (localhost:3000, 127.0.0.1:3000)        │   │
│   │   RATE_LIMIT: 60/min · MAX_UPLOAD: 25 MB                    │   │
│   └────────────────────────┬─────────────────────────────────────┘   │
└───────────────────────────│──────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         AGENT LAYER                                  │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │               LangGraph Agent Graph                          │   │
│   │                                                              │   │
│   │   route_intent                                               │   │
│   │       │                                                      │   │
│   │       ├──────────────────────┬──────────────────────────┐   │   │
│   │       ▼                      ▼                          │   │   │
│   │  ┌─────────────┐    ┌─────────────────────┐            │   │   │
│   │  │ Document QA │    │  Appointment Node   │            │   │   │
│   │  │    Node     │    │  (multi-step form)  │            │   │   │
│   │  └──────┬──────┘    └──────────┬──────────┘            │   │   │
│   │         │                      │                        │   │   │
│   │   retrieve + answer     validate fields                 │   │   │
│   │                                                         │   │   │
│   │   Session state: { mode, appt_step, appt_data }        │   │   │
│   └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                    │                        │
          ┌─────────┘                        └──────────┐
          ▼                                             ▼
┌──────────────────────────┐           ┌──────────────────────────────┐
│       TOOLS LAYER        │           │         TOOLS LAYER           │
│                          │           │                              │
│  ┌──────────────────┐    │           │  ┌────────────────────────┐  │
│  │   FAISS Vector   │    │           │  │  Validators            │  │
│  │   Store          │    │           │  │  - validate_name()     │  │
│  │  (./vectorstore) │    │           │  │  - validate_phone()    │  │
│  └──────────────────┘    │           │  │  - validate_email()    │  │
│                          │           │  │  - parse_natural_date()│  │
│  ┌──────────────────┐    │           │  └────────────────────────┘  │
│  │  RAG Pipeline    │    │           └──────────────────────────────┘
│  │  chunk → embed   │    │
│  │  → similarity    │    │
│  │  search          │    │
│  └──────────────────┘    │
└──────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                          │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │              Ollama  (localhost:11434)  — LOCAL              │   │
│   │                                                              │   │
│   │   LLM:        llama3.2:1b     (chat completions)            │   │
│   │   Embeddings: nomic-embed-text  (document indexing)         │   │
│   │   Mode:       offline / no internet required                │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   ┌─────────────────────────┐   ┌────────────────────────────────┐   │
│   │  SQLite DB (app.db)     │   │  ./uploads  /  ./documents     │   │
│   │  Appointments table     │   │  PDF + TXT files (25 MB max)   │   │
│   └─────────────────────────┘   └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. React Frontend
- Chat window with message history
- Mode badge showing current context: `Document QA` or `Appointment Booking`
- Document upload button (`.txt`, `.pdf`)
- Quick-action buttons for common queries
- Persists session state: `mode`, `appt_step`, `appt_data`

### 2. FastAPI Backend
| Endpoint | Method | Purpose |
|---|---|---|
| `/chat` | POST | Main agent entry point |
| `/upload-document` | POST | Upload & re-index a document |
| `/documents` | GET | List indexed documents |

Config from `.env`:
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
DATABASE_URL=sqlite:///./app.db
UPLOAD_DIR=./app/uploads
MAX_UPLOAD_MB=25
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SECRET_KEY=change-me-in-production-please
RATE_LIMIT=60/minute
```

### 3. LangGraph Agent Graph
```
[entry] → route_intent
              │
     ┌────────┴────────┐
     ▼                 ▼
document_qa      appt_input_router
     │                 │
     │           appointment_node
     │           (name → phone → email → date → confirm)
     │
     └──→ [END]
```

**State shape:**
```python
{
  "messages": [...],       # full conversation history
  "mode": "chat|document_qa|appointment",
  "appt_step": "name|phone|email|date|confirm|done",
  "appt_data": { "name": "", "phone": "", "email": "", "date": "" },
  "last_user_input": "...",
  "response": "..."
}
```

### 4. RAG Pipeline
```
Document upload (.txt / .pdf)
        │
        ▼
  TextLoader / PyPDFLoader
        │
        ▼
  RecursiveCharacterTextSplitter
  (chunk_size=500, overlap=50)
        │
        ▼
  OllamaEmbeddings (nomic-embed-text)
        │
        ▼
  FAISS vector store (persisted to ./vectorstore)
        │
   [at query time]
        │
        ▼
  similarity_search(k=4) → context string
        │
        ▼
  ChatOllama (llama3.2:1b) → answer
```

### 5. Appointment Booking Flow
```
User: "book an appointment"
        │
        ▼
  route_intent → mode = appointment
        │
        ▼
  Collect name      → validate_name()
        │
        ▼
  Collect phone     → validate_phone()
        │
        ▼
  Collect email     → validate_email()
        │
        ▼
  Collect date      → parse_natural_date()  (supports "next Monday", "in 3 days", "July 5")
        │              is_future_date()
        ▼
  Show summary → "confirm" / "cancel"
        │
        ▼
  Confirmed → persist to SQLite
```

### 6. Ollama (Local LLM)
| Setting | Value |
|---|---|
| Base URL | `http://localhost:11434` |
| Chat model | `llama3.2:1b` |
| Embedding model | `nomic-embed-text` |
| Internet required | No (fully offline) |

Pull models before running:
```bash
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

---

## Data Flow Summary

```
User types message
      │
      ▼
React (sends { message, history, mode, appt_step, appt_data })
      │
      ▼
FastAPI /chat
      │
      ▼
LangGraph graph.invoke(state)
      │
      ├─── [document_qa] → FAISS retrieval → Ollama llama3.2 → response
      │
      └─── [appointment] → validators → collect fields → confirm → SQLite
      │
      ▼
FastAPI returns { response, mode, appt_step, appt_data }
      │
      ▼
React updates chat + session state
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Axios, react-markdown |
| Backend | FastAPI, Uvicorn, Python 3.11+ |
| Agent orchestration | LangGraph 0.1.x |
| LLM (chat) | Ollama · llama3.2:1b |
| LLM (embeddings) | Ollama · nomic-embed-text |
| Vector store | FAISS (faiss-cpu) |
| Document loading | LangChain (TextLoader, PyPDFLoader) |
| Validation | python-dateutil, custom regex |
| Database | SQLite (via DATABASE_URL) |
| Config | `.env` file |
