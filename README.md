# ContextAI — Context-Aware Conversational Agent

> A full-stack conversational AI that answers questions from your documents **and** books appointments — powered entirely by a local Ollama LLM (no internet required).

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi) ![LangGraph](https://img.shields.io/badge/LangGraph-0.1.x-orange) ![React](https://img.shields.io/badge/React-18-61DAFB?logo=react) ![Ollama](https://img.shields.io/badge/LLM-Ollama%20llama3.2%3A1b-black)

---

## Features

- **Document QA** — Upload `.txt` or `.pdf` files and ask questions; answers are grounded in your documents via RAG (FAISS + Ollama embeddings)
- **Appointment Booking** — Conversational multi-step form that collects name, phone, email, and preferred date (supports natural language like *"next Monday"* or *"in 3 days"*)
- **Context Switching** — Seamlessly switch between Document QA and Appointment Booking mid-conversation
- **Fully Offline** — All LLM inference runs locally via Ollama; no API keys, no internet required
- **Session Persistence** — Conversation state, booking progress, and document context are maintained throughout the session

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Axios, react-markdown |
| Backend | FastAPI, Uvicorn, Python 3.11+ |
| Agent Orchestration | LangGraph 0.1.x |
| LLM (chat) | Ollama · `llama3.2:1b` |
| LLM (embeddings) | Ollama · `nomic-embed-text` |
| Vector Store | FAISS (`faiss-cpu`) |
| Document Loading | LangChain (`TextLoader`, `PyPDFLoader`) |
| Validation | `python-dateutil`, custom regex |
| Database | SQLite (`app.db`) |

---

## Architecture

```
CLIENT LAYER  (React Frontend)
      │  HTTP JSON  POST /chat · POST /upload-document
      ▼
API LAYER  (FastAPI · port 8000)
      │
      ▼
AGENT LAYER  (LangGraph)
      │
      ├── route_intent
      │       ├── Document QA Node  →  FAISS retrieval → Ollama → answer
      │       └── Appointment Node  →  multi-step form → SQLite
      │
TOOLS LAYER
      ├── FAISS Vector Store + RAG Pipeline
      └── Validators: name · phone · email · parse_natural_date()
      │
INFRASTRUCTURE
      └── Ollama (localhost:11434) · SQLite (app.db) · ./uploads
```

See [`system_diagram.md`](./system_diagram.md) for the full architecture diagram.

---

## Prerequisites

- Python **3.11+**
- Node.js **18+**
- [Ollama](https://ollama.com) installed and running

---

## Quick Start

### 1. Pull Ollama Models

```bash
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

Verify Ollama is running:
```bash
ollama serve   # starts on http://localhost:11434
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (defaults work out of the box)

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

Backend will be live at **http://localhost:8000**  
Interactive API docs at **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the dev server
npm run dev
```

Frontend will be live at **http://localhost:3000**

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

```env
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

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/chat` | POST | Main agent entry point — handles both QA and booking |
| `/upload-document` | POST | Upload and re-index a `.txt` or `.pdf` document |
| `/documents` | GET | List all indexed documents |

**POST /chat — Request body:**
```json
{
  "message": "Book an appointment for next Monday",
  "history": [],
  "mode": "chat",
  "appt_step": null,
  "appt_data": {}
}
```

**POST /chat — Response:**
```json
{
  "response": "Sure! What's your name?",
  "mode": "appointment",
  "appt_step": "name",
  "appt_data": {}
}
```

---

## How It Works

### Document QA
1. Upload a `.txt` or `.pdf` via the UI
2. Document is chunked (size=500, overlap=50) and embedded with `nomic-embed-text`
3. Embeddings are stored in a FAISS vector store (`./vectorstore`)
4. On query, top-4 similar chunks are retrieved and passed to `llama3.2:1b` as context

### Appointment Booking
The agent walks through a validated multi-step form:

```
"book an appointment"
        │
        ▼
Name  →  Phone  →  Email  →  Date  →  Confirm  →  Saved to SQLite
```

Natural language dates are supported:
- *"next Monday"* → `2026-06-29`
- *"in 3 days"* → `2026-06-28`
- *"July 5"* → `2026-07-05`

### Context Switching
The `route_intent` node in LangGraph detects whether the user wants to query a document or book an appointment, and routes accordingly — mid-conversation switching is fully supported.

---

## Project Structure

```
ai-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + routes
│   │   ├── agent/               # LangGraph graph definition
│   │   ├── tools/               # Validators + RAG pipeline
│   │   └── uploads/             # Uploaded documents
│   ├── alembic/                 # DB migrations
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                     # Next.js app directory
│   ├── components/              # Chat UI components
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml
├── system_diagram.md
└── README.md
```

---

## Docker (Optional)

Run the full stack with Docker Compose:

```bash
docker-compose up --build
```

> **Note:** Ollama must still be running on the host machine. The containers connect to `host.docker.internal:11434`.

---

## Constraints & Limits

| Setting | Value |
|---|---|
| Max upload size | 25 MB |
| API rate limit | 60 requests / minute |
| CORS origins | `localhost:3000`, `127.0.0.1:3000` |
| Supported file types | `.txt`, `.pdf` |

---

## Built With

- [FastAPI](https://fastapi.tiangolo.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangChain](https://www.langchain.com/)
- [Ollama](https://ollama.com/)
- [FAISS](https://faiss.ai/)
- [Next.js](https://nextjs.org/)

---

## Author

**Narayan Bhandari**  
Data Scientist · ML Engineer  
[GitHub](https://github.com/Om700-create) · narayanbhandari498@gmail.com

---

## License

MIT License — feel free to use, modify, and distribute.