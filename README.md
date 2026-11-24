# Liquidio — Expense Classification and Liquidation Reporting System (DOST &times; CIT-U)

Module 1: Budget Foundation & Core Expense Recording for DOST-funded research projects at Cebu Institute of Technology – University (CIT-U).

---

## 1. Architecture & Layering

The system enforces a strict 3-tier decoupled architecture:
```
Controller (FastAPI Router)
       ↓
Service (Business Rules & Validations)
       ↓
Repository (SQLAlchemy 2.x Database Access)
```
- **No SQL queries inside services or routers**.
- **No HTTP handling or business logic inside repositories**.
- **FastAPI `Depends`** injects database sessions (`get_db`) and authenticated RBAC contexts.

---

## 2. Technology Stack

- **Backend**: Python 3.14+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, bcrypt, PyJWT.
- **Frontend**: Vue 3 (Composition API `<script setup>`), Pinia, Vue Router, Vite.
- **Database**: SQLite (local development / demo) via SQLAlchemy `Numeric(12, 2)` and Python `Decimal` (no floating-point rounding errors). Switchable to PostgreSQL via `DATABASE_URL`.
- **Cloud Storage**: Zero-cost adapter interface (`StorageAdapter`) supporting `LocalStorageAdapter` and `GoogleDriveStorageAdapter` stub.

---

## 3. Directory Structure

```text
Liquidio/
├── .env                  # Local runtime environment variables
├── .env.example          # Template environment file
├── alembic.ini           # Alembic migration configuration
├── backend/
│   ├── alembic/          # Database migration revisions and env.py
│   ├── app/
│   │   ├── adapters/     # StorageAdapter (Local vs Google Drive)
│   │   ├── core/         # Config, Database engine, Security
│   │   ├── models/       # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/      # Pydantic v2 validation schemas
│   │   ├── repositories/ # Isolated database query logic
│   │   ├── services/     # Business rules & validations
│   │   ├── controllers/  # FastAPI REST route controllers
│   │   └── main.py       # FastAPI application entrypoint & static mounting
│   ├── requirements.txt  # Python backend dependencies
│   └── uploads/receipts/ # Local storage receipt uploads directory
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable UI widgets & forms
│   │   ├── views/        # Page views
│   │   ├── router/       # Vue Router configuration
│   │   ├── stores/       # Pinia state stores
│   │   ├── App.vue       # Root layout component
│   │   └── main.js       # Vue application entrypoint
│   ├── package.json      # Frontend npm dependencies
│   └── vite.config.js    # Vite configuration & backend proxy
└── README.md
```

---

## 4. Setup & Installation

### Prerequisites
- Python 3.10+ (with `venv`)
- Node.js 18+ and npm

### Step 1: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` settings:
```ini
DATABASE_URL=sqlite:///./liquidio.db
JWT_SECRET=supersecret-liquidio-dost-jwt-key-2026-citu
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
STORAGE_MODE=local
LOCAL_STORAGE_DIR=backend/uploads/receipts
```

### Step 2: Backend Dependencies & Database Migration
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run initial database migration to create all tables
alembic upgrade head
```

### Step 3: Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 5. Running the System

### Option A: Demo Mode (Single Process)
Run both backend and frontend as a single server on port 8000:
```bash
# 1. Build the Vue SPA bundle:
cd frontend && npm run build && cd ..

# 2. Start the unified FastAPI server:
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- Open `http://localhost:8000` in any web browser or phone on the same local network.
- Interactive API docs available at `http://localhost:8000/docs`.

### Option B: Development Mode (Hot Reloading)
Run backend and frontend independently with auto-reload:

1. **Terminal 1 (Backend)**:
   ```bash
   .venv/bin/uvicorn backend.app.main:app --reload --port 8000
   ```
2. **Terminal 2 (Frontend)**:
   ```bash
   cd frontend
   npm run dev
   ```
   Access Vite dev server at `http://localhost:5173`. API calls are automatically proxied to `:8000`.

---

## 6. Running Tests

Automated test runner scripts are provided for both Arch Linux and Windows PowerShell. These scripts:
1. Initialize `.venv` and install backend requirements if missing.
2. Spin up an **isolated temporary SQLite database** via `DATABASE_URL` and a throwaway `JWT_SECRET` (never touching `liquidio.db` or `.env` data).
3. Execute **Alembic migrations** against the temporary database to verify schema evolution.
4. Execute the **pytest** test suite.
5. Validate **frontend compilation** (`npm run build`).
6. Print a clear PASS/FAIL summary and automatically clean up the temporary database upon exit.

### On Arch Linux / Linux (Bash)
```bash
bash scripts/test.sh
```

### On Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

### Manual Pytest Run
You can also run pytest directly inside the virtual environment:
- **Linux**: `.venv/bin/pytest backend/tests -v`
- **Windows**: `.venv\Scripts\pytest backend\tests -v`
*(When run directly, test fixtures automatically isolate execution to a temporary test database).*
