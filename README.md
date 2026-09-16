# StudyGen AI — Full-Stack AI Study Assistant

> A modern, production-grade EdTech web application designed to turn raw study materials (lecture notes, textbook excerpts, syllabi) into structured summaries, prioritized exam topics, customizable question papers, and interactive quizzes with real-time feedback.

🚀 **Live Demo**: [https://studygen-ai-2x1i.onrender.com](https://studygen-ai-2x1i.onrender.com)  
📖 **API Docs**: [https://studygen-ai-2x1i.onrender.com/docs](https://studygen-ai-2x1i.onrender.com/docs)

---

## 📖 Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Architecture & System Design](#architecture--system-design)
4. [Tech Stack](#tech-stack)
5. [Database Schema](#database-schema)
6. [Prerequisites & Installation](#prerequisites--installation)
7. [Environment Variables](#environment-variables)
8. [Running the Application](#running-the-application)
9. [AI Provider Configuration (Ollama & OpenAI)](#ai-provider-configuration)
10. [REST API Documentation](#rest-api-documentation)
11. [Testing Suite](#testing-suite)
12. [Screenshots & UI Showcase](#screenshots--ui-showcase)
13. [Future Roadmap](#future-roadmap)

---

## 1. Project Overview

**StudyGen AI** bridges the gap between passive reading and active recall. University students and self-learners frequently struggle to transform lengthy lecture slides and unformatted text into targeted study sessions. StudyGen AI solves this by:
- Ingesting raw text notes, Markdown (`.md`), plain text (`.txt`), and PDF documents (`.pdf`).
- Generating comprehensive executive summaries with key concept badges and quick-revision flash points.
- Extracting prioritized exam topics ranked by relevance (`Critical`, `High`, `Medium`).
- Producing balanced question papers configured by marks, difficulty, and format (MCQs, Short Answer, Long Answer, Mixed).
- Offering a focused **Interactive Quiz Mode** with real-time feedback, grading, answer rationales, and historical attempt analytics.

---

## 2. Key Features

- 📊 **Interactive Dashboard**: Real-time project search, dynamic subject filter dropdown, multi-criteria sorting (newest, oldest, A-Z, most papers, most documents), and high-level study metrics.
- ⚡ **Instant Study Kit Generator**: 1-click study kit generation from sample presets (Computer Science OS, Biology Genetics, History World War II) or custom input.
- 📄 **Multi-Format Document Ingestion**: Support for pasted text notes and direct file uploads for `.pdf` (using `pypdf`), `.txt`, and `.md` with automatic text extraction and character counting.
- 📑 **AI-Powered Summaries**:
  - Structured Executive Overview
  - Key Concept Tag Cloud
  - Important Exam Highlights
  - ⚡ Quick Revision Cheat-Sheet
- 🎯 **Card-Based Important Topics**: Priority-rated topics with in-depth explanations and related concept pills.
- 📝 **Question Paper Generator**: Fully customizable test generator configured by question count, total marks, duration, difficulty, and question type.
- 🚀 **Interactive Quiz Mode**:
  - One-at-a-time focus viewport
  - Option selector with instant color-coded feedback
  - Detailed grounding explanations for every question
  - Final score report with percentage, marks earned, correct/incorrect ratios, and answer breakdown
- ⏱ **Generation Audit Trail**: Detailed audit log tracking AI models used, generation types, status, and timestamps.
- 🔒 **Security & Multi-Tenancy**: Password hashing using `bcrypt`, JWT bearer authentication, and isolated user data scoping.
- 🔄 **Smart Fallback Engine**: Pluggable provider system with built-in heuristic extraction so the platform is 100% testable even without an active LLM daemon.

---

## 3. Architecture & System Design

The application follows a clean layered architecture:

```
studygen-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint & static mounting
│   │   ├── config.py            # Pydantic & environment settings
│   │   ├── database.py          # SQLAlchemy 2.0 engine, SessionLocal & automatic fallback
│   │   ├── models/              # SQLAlchemy ORM entities (User, Project, Document, etc.)
│   │   ├── schemas/             # Pydantic v2 validation models
│   │   ├── routes/              # Modular REST API endpoints
│   │   ├── services/            # Core business logic (StudyService, QuizService, AuthService)
│   │   │   └── ai/              # AI Provider Abstraction (Ollama, OpenAI, Fallback)
│   │   └── utils/               # Security, bcrypt, text processing
│   ├── tests/                   # Pytest test suite with in-memory SQLite fixtures
│   ├── requirements.txt         # Frozen Python dependencies
│   └── .env.example             # Backend environment template
├── frontend/
│   ├── index.html               # Single-page application shell
│   ├── css/
│   │   ├── styles.css           # Modern SaaS design system (Slate & Indigo theme)
│   │   └── quiz.css             # Dedicated interactive quiz styling
│   └── js/
│       ├── api.js               # Centralized REST API client
│       ├── state.js             # Client-side reactive state store
│       ├── components.js        # Toasts, modals, and dynamic AI loading overlay
│       └── app.js               # View router, controllers, and event listeners
├── run.py                       # Unified one-command full-stack server
├── README.md                    # Project documentation
└── .env.example                 # Root environment template
```
## 4. Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2, Uvicorn, Pytest.
- **Database**: PostgreSQL with SQLAlchemy connection pooling (`psycopg2-binary`). Automatic fallback to SQLite (`studygen.db`) enables seamless zero-config local development and testing.
- **AI Inference**:
  - **Ollama**: Local private LLM execution (e.g. `llama3`, `mistral`, `qwen`).
  - **OpenAI**: Cloud LLM execution via official SDK (`gpt-4o-mini`).
  - **Internal Fallback**: Deterministic heuristic engine for zero-dependency test execution.
- **Frontend**: Vanilla HTML5, modern responsive CSS3 (CSS custom properties, glassmorphism, responsive grid), and modular Vanilla JavaScript ES6 (no React/Vue framework bloat).

---

## 5. Database Schema

The database schema is strictly normalized with explicit foreign keys, cascade deletes, and indexed query paths:

1. **`users`**: `id`, `name`, `email` (unique, indexed), `password_hash`, `created_at`.
2. **`projects`**: `id`, `user_id` (FK), `name`, `subject` (indexed), `description`, `created_at`, `updated_at`.
3. **`documents`**: `id`, `project_id` (FK), `filename`, `file_type`, `content`, `char_count`, `created_at`.
4. **`summaries`**: `id`, `document_id` (FK), `summary`, `key_concepts` (JSON), `important_topics` (JSON), `quick_revision` (JSON), `created_at`.
5. **`important_topics`**: `id`, `document_id` (FK), `topic`, `explanation`, `importance`, `related_concepts` (JSON), `created_at`.
6. **`question_papers`**: `id`, `project_id` (FK), `document_id` (FK nullable), `title`, `total_marks`, `duration`, `difficulty`, `question_type`, `created_at`.
7. **`questions`**: `id`, `question_paper_id` (FK), `question_number`, `question_text`, `question_type`, `marks`, `difficulty`, `options` (JSON), `correct_answer`, `explanation`.
8. **`quiz_attempts`**: `id`, `user_id` (FK), `question_paper_id` (FK), `score`, `total_questions`, `correct_count`, `incorrect_count`, `percentage`, `details` (JSON), `completed_at`.
9. **`generation_history`**: `id`, `project_id` (FK), `generation_type`, `model_used`, `status`, `error_message`, `created_at`.

---

## 6. Prerequisites & Installation

### Prerequisites
- Python 3.10+
- (Optional) PostgreSQL server installed and running
- (Optional) Ollama installed for local offline LLM inference

### Setup Steps
```bash
# 1. Clone or navigate to the repository
cd studygen-ai

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# 4. Install backend dependencies
pip install -r backend/requirements.txt

# 5. Copy environment file
cp .env.example .env
```

---

## 7. Environment Variables

Create a `.env` file in the root directory (or in `backend/`):

```env
# Application Settings
DEBUG=True
SECRET_KEY=your-secure-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database (PostgreSQL or SQLite)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/studygen_ai
USE_SQLITE_FALLBACK=True
SQLITE_URL=sqlite:///./studygen.db

# AI Provider Selection: 'gemini' (Default), 'ollama', 'openai', or 'fallback'
AI_PROVIDER=gemini

# Google Gemini API Settings (Recommended)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# Ollama Settings (Alternative)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# OpenAI Settings (Alternative)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

---

## 8. Running the Application

Start the unified server with a single command:

```bash
python run.py
```

The application will be accessible at:
- **Web Interface**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Redoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 9. AI Provider Configuration

### Option A: Google Gemini API (Recommended & Default)
1. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Set in your `.env`:
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_actual_gemini_api_key
   GEMINI_MODEL=gemini-2.5-flash
   ```

### Option B: Local Inference with Ollama (Alternative)
1. Install [Ollama](https://ollama.com).
2. Download a local model:
   ```bash
   ollama pull llama3
   ```
3. Set in your `.env`:
   ```env
   AI_PROVIDER=ollama
   OLLAMA_MODEL=llama3
   ```

### Option C: Cloud Inference with OpenAI (Alternative)
1. Obtain an API key from [platform.openai.com](https://platform.openai.com).
2. In your `.env`:
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini
   ```

---

## 10. REST API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user account |
| `POST` | `/api/auth/login` | Login and receive JWT bearer token |
| `GET` | `/api/auth/me` | Fetch authenticated user profile |
| `POST` | `/api/projects` | Create a new study project |
| `GET` | `/api/projects` | List projects for the user |
| `GET` | `/api/projects/{id}` | Get project details |
| `PUT` | `/api/projects/{id}` | Update project metadata |
| `DELETE` | `/api/projects/{id}` | Delete project and cascade documents |
| `POST` | `/api/documents` | Add study material as pasted text |
| `POST` | `/api/documents/upload` | Upload `.pdf`, `.txt`, or `.md` file with automatic text extraction |
| `GET` | `/api/documents/project/{id}` | List documents in a project |
| `DELETE` | `/api/documents/{id}` | Remove a study document |
| `POST` | `/api/summaries/generate` | Generate structured AI summary |
| `GET` | `/api/summaries/document/{id}` | Retrieve document summary |
| `POST` | `/api/topics/generate` | Extract prioritized exam topics |
| `GET` | `/api/topics/document/{id}` | Retrieve document topics |
| `POST` | `/api/question-papers/generate`| Generate custom question paper |
| `GET` | `/api/question-papers/project/{id}`| List question papers for project |
| `DELETE` | `/api/question-papers/{id}`| Delete a question paper |
| `POST` | `/api/quizzes/submit` | Submit answers for real-time grading |
| `GET` | `/api/quizzes/paper/{id}/attempts`| List previous attempts for paper |
| `GET` | `/api/generation/project/{id}` | Fetch AI generation audit logs |
| `GET` | `/api/generation/status` | Check active AI provider status |

---

## 11. Testing Suite

The project includes unit and integration tests covering authentication, database models, document validation, AI services, and quiz grading:

```bash
# Run pytest test suite
.venv\Scripts\pytest -v backend/tests
```

All tests execute against an isolated in-memory SQLite database.

---

## 12. Screenshots & UI Showcase

*Portfolio Highlights*:
- **Landing Page**: Modern hero section with feature highlights and quick-start CTAs.
- **Interactive Dashboard**: Search, filter by subject, multi-criteria sorting, and study metrics.
- **Project Workspace**: Unified workspace for notes, AI summaries, exam topics, and question papers.
- **Interactive Quiz View**: One-at-a-time viewport with option cards and instant answer feedback.
- **Score Report**: Final completion card with breakdown, metrics, and question-by-question review.

---

## 13. Future Roadmap

- [x] Support for native PDF document parsing via `pypdf`.
- [ ] Export question papers directly to PDF / Printable LaTeX formats.
- [ ] Flashcard generation mode with spaced repetition algorithms (SM-2).
- [ ] Audio transcription for lecture recordings using local Whisper models.
