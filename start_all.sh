#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_DIR="$ROOT_DIR/scientific-copilot-ui"
BACKEND_PID=""
FRONTEND_PID=""

info() {
  printf '\n> %s\n' "$1"
}

ok() {
  printf '  [OK] %s\n' "$1"
}

warn() {
  printf '  [!!] %s\n' "$1"
}

die() {
  printf '  [ERR] %s\n' "$1" >&2
  exit 1
}

cleanup() {
  trap - EXIT INT TERM
  printf '\nShutting down...\n'

  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

wait_for_http() {
  local name="$1"
  local url="$2"
  local attempts="${3:-60}"
  local delay="${4:-2}"

  for ((i=1; i<=attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      ok "$name is ready"
      return 0
    fi
    sleep "$delay"
  done

  die "$name did not become ready at $url"
}

trap cleanup EXIT INT TERM

require_cmd docker
require_cmd curl
require_cmd uv
require_cmd npm

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  if [[ -f "$ROOT_DIR/.env.example" ]]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    ok "Created .env from .env.example"
  else
    die "Missing .env and .env.example"
  fi
fi

info "Starting Docker services"
(
  cd "$ROOT_DIR"
  docker compose up -d postgres ollama
)
ok "Docker services requested"

info "Waiting for PostgreSQL"
(
  cd "$ROOT_DIR"
  for _ in {1..60}; do
    if docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
      ok "PostgreSQL is ready"
      break
    fi
    sleep 2
  done
)

info "Waiting for Ollama"
wait_for_http "Ollama" "http://127.0.0.1:11434/api/tags" 90 2

if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  info "Creating Python environment"
  (
    cd "$ROOT_DIR"
    uv sync
  )
  ok "Python environment ready"
else
  ok "Python environment already present"
fi

if [[ ! -d "$UI_DIR/node_modules" ]]; then
  info "Installing frontend dependencies"
  (
    cd "$UI_DIR"
    npm install
  )
  ok "Frontend dependencies ready"
else
  ok "Frontend dependencies already present"
fi

info "Running database migrations"
(
  cd "$ROOT_DIR"
  uv run alembic upgrade head
)
ok "Migrations applied"

info "Starting backend"
(
  cd "$ROOT_DIR"
  PYTHONUNBUFFERED=1 uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
) &
BACKEND_PID=$!

info "Starting frontend"
(
  cd "$UI_DIR"
  npm run dev
) &
FRONTEND_PID=$!

wait_for_http "Backend" "http://127.0.0.1:8000/health" 60 2
wait_for_http "Frontend" "http://127.0.0.1:3000" 90 2

cat <<'EOF'

=====================================================
  Frontend -> http://localhost:3000
  Backend  -> http://localhost:8000
  Ollama   -> http://localhost:11434
=====================================================
Press Ctrl+C to stop backend and frontend.
Docker services remain running.
EOF

wait
