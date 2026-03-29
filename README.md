# 📝 Content Ops — AI-Powered Content Operations Platform

An autonomous, multi-agent content operations system that orchestrates the entire content lifecycle — from brief intake to compliance-checked, localized, and published content — powered by LLMs, vector search, and a human-in-the-loop review gate.

---

## ✨ Features

- **Multi-Agent Pipeline** — Specialized AI agents handle strategy, knowledge retrieval, drafting, governance, localization, and publishing.
- **Self-Correcting Compliance** — A governance agent checks drafts against brand policies and auto-corrects violations (up to 3 attempts).
- **Multilingual Localization** — Automatic translation into Indian languages (Tamil, Hindi, Bengali, Telugu, Malayalam).
- **Google Sheets Archival** — Approved content is published to Google Sheets via a service account for Zapier/LinkedIn automation.
- **Human Review Gate** — All AI-generated content pauses for human approval before publishing.
- **Analytics Dashboard** — Track content metrics, violation counts, and pipeline performance.
- **Document Indexing** — Upload product specs/PDFs that are chunked, embedded, and used as RAG context for drafting.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)               │
│              Dashboard · Job Management · Analytics      │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────┐
│                  Backend (FastAPI)                        │
│         /api/jobs · /api/documents · /api/analytics       │
└──────┬──────────────────────────────────────┬───────────┘
       │                                      │
┌──────▼──────┐                        ┌──────▼──────┐
│  Celery +   │                        │  PostgreSQL  │
│   Redis     │                        │  (Database)  │
│  (Workers)  │                        └──────────────┘
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│                   Agent Pipeline                         │
│                                                          │
│  1. Intelligence Agent  → Strategy & brief refinement    │
│  2. Knowledge Agent     → RAG retrieval & doc indexing   │
│  3. LLM Client (Groq)  → Content drafting               │
│  4. Governance Agent    → Brand policy compliance        │
│  5. Localization Agent  → Multilingual translation       │
│  6. Distribution Agent  → Channel publishing             │
│  7. Publishing Agent    → Google Sheets archival         │
│  8. Analytics Agent     → Content metrics tracking       │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer      | Technology                              |
| ---------- | --------------------------------------- |
| Frontend   | React 18, TypeScript, Vite, TailwindCSS |
| Backend    | FastAPI, SQLAlchemy, Alembic            |
| LLM        | Groq (LLaMA)                            |
| Task Queue | Celery + Redis                          |
| Database   | PostgreSQL                              |
| Embeddings | Sentence Transformers                   |
| Archival   | Google Sheets API (service account)     |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL
- Redis
- A [Groq API key](https://console.groq.com/)
- Google Cloud service account JSON (for Sheets archival)

### 1. Clone the Repository

```bash
git clone https://github.com/Akshayaa1010/content-ops-.git
cd content-ops-
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   DATABASE_URL, REDIS_URL, GROQ_API_KEY, GOOGLE_SHEETS_CREDENTIALS, etc.

# Run database migrations
alembic upgrade head
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Start All Services

Open **three terminals**:

```bash
# Terminal 1 — Backend API
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery Worker
cd backend
celery -A app.pipeline.celery_app worker --loglevel=info --pool=solo

# Terminal 3 — Frontend Dev Server
cd frontend
npm run dev
```

The dashboard will be available at **http://localhost:5173**.

---

## 📡 API Endpoints

| Method | Endpoint                      | Description                      |
| ------ | ----------------------------- | -------------------------------- |
| GET    | `/health`                     | Health check                     |
| POST   | `/api/jobs/`                  | Create a new content job         |
| GET    | `/api/jobs/`                  | List all jobs                    |
| GET    | `/api/jobs/{id}`              | Get job details                  |
| POST   | `/api/jobs/{id}/approve`      | Approve & publish a reviewed job |
| POST   | `/api/documents/upload`       | Upload a document for indexing   |
| GET    | `/api/documents/`             | List indexed documents           |
| GET    | `/api/analytics/`             | Get content analytics & metrics  |

---

## 📂 Project Structure

```
content-ops-/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── agents/           # AI agents (knowledge, governance, LLM, etc.)
│   │   ├── api/routes/       # FastAPI route handlers
│   │   ├── config/           # App configuration
│   │   ├── db/               # SQLAlchemy models & database setup
│   │   ├── pipeline/         # Celery tasks, state machine, embeddings
│   │   ├── policies/         # Brand policy documents
│   │   └── tests/            # Backend tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main dashboard application
│   │   ├── main.tsx          # React entry point
│   │   └── index.css         # Global styles
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

---

## 🔄 Pipeline Flow

1. **Brief Submission** — User creates a content job with topic, audience, and target channels.
2. **Strategy Refinement** — Intelligence agent analyzes the brief and suggests optimizations.
3. **Knowledge Retrieval** — RAG-based retrieval pulls relevant context from indexed documents.
4. **Content Drafting** — Groq LLM generates a blog post and LinkedIn post from the brief + context.
5. **Compliance Check** — Governance agent validates against brand policies; auto-corrects violations.
6. **Localization** — Content is translated into configured target languages.
7. **Human Review** — Pipeline pauses; content is presented on the dashboard for approval.
8. **Publishing** — On approval, content is distributed to channels and archived to Google Sheets.

---

## 📄 License

This project is for educational and demonstration purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
