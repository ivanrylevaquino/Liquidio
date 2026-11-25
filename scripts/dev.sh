#!/usr/bin/env bash
# Start Liquidio for manual testing: build frontend, migrate DB, serve on :8000
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8000}"

[ -d .venv ] || python -m venv .venv

REQ=$(ls backend/requirements.txt requirements.txt 2>/dev/null | head -1 || true)
[ -n "$REQ" ] && .venv/bin/pip install -q -r "$REQ"

[ -d frontend/node_modules ] || (cd frontend && npm ci)
(cd frontend && npm run build)

.venv/bin/alembic upgrade head

read -r -p "Create a user account now? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then .venv/bin/python scripts/create_user.py; fi

IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -1 || true)
echo
echo "  This computer:  http://localhost:$PORT"
[ -n "${IP:-}" ] && echo "  Phone (same Wi-Fi): http://$IP:$PORT"
echo "  API docs:       http://localhost:$PORT/docs"
echo "  Ctrl+C to stop"
echo
exec .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT"