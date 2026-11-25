#!/usr/bin/env bash
# ==============================================================================
# Liquidio Test Runner (Linux / Arch Linux)
# Executes migrations, backend pytest suite, and frontend build validation
# against an isolated temporary SQLite database and throwaway credentials.
# ==============================================================================

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DB="$REPO_ROOT/liquidio_test_run_$$.db"

# Cleanup trap to ensure temporary database is removed upon script exit
cleanup() {
    EXIT_CODE=$?
    if [ -f "$TEMP_DB" ]; then
        rm -f "$TEMP_DB"
    fi
    if [ -f "${TEMP_DB}-wal" ]; then
        rm -f "${TEMP_DB}-wal"
    fi
    if [ -f "${TEMP_DB}-shm" ]; then
        rm -f "${TEMP_DB}-shm"
    fi
    if [ $EXIT_CODE -ne 0 ]; then
        echo ""
        echo "================================================================"
        echo " [FAIL] Test suite encountered errors. See log details above."
        echo "================================================================"
    fi
}
trap cleanup EXIT

echo "================================================================"
echo " Starting Liquidio Project Verification & Test Suite"
echo "================================================================"

# 1. Setup / Validate Python Virtual Environment
VENV_DIR="$REPO_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"
ALEMBIC_BIN="$VENV_DIR/bin/alembic"
PYTEST_BIN="$VENV_DIR/bin/pytest"

if [ ! -f "$ALEMBIC_BIN" ] || [ ! -f "$PYTEST_BIN" ]; then
    echo "==> Installing backend dependencies into virtual environment..."
    "$PIP_BIN" install -q -r "$REPO_ROOT/backend/requirements.txt"
fi

# 2. Configure Isolated Test Environment Variables
export DATABASE_URL="sqlite:///$TEMP_DB"
export JWT_SECRET="test-throwaway-jwt-secret-liquidio-2026"
export PYTHONPATH="$REPO_ROOT"

echo "==> Isolated test database: $DATABASE_URL"

# 3. Test Alembic Migrations
echo "==> Running Alembic migrations against isolated database..."
"$ALEMBIC_BIN" upgrade head

# 4. Run Backend Tests via Pytest
echo "==> Running backend test suite with pytest..."
"$PYTEST_BIN" "$REPO_ROOT/backend/tests" -v

# 5. Verify Frontend Compilation
echo "==> Checking frontend compilation..."
cd "$REPO_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    if [ -f "package-lock.json" ]; then
        npm ci --silent
    else
        npm install --silent
    fi
fi
npm run build

echo ""
echo "================================================================"
echo " [PASS] ALL CHECKS PASSED: Migrations, Pytest & Frontend Build!"
echo "================================================================"
