#!/usr/bin/env bash
# =============================================================================
# Docker-free local startup (fallback mode) for AI Coach Mastery.
#
# Starts all three tiers without containers:
#   core-api  : Spring Boot 'local' profile (H2 file DB, showcase auto-seeds)
#   ai-engine : uvicorn in a .venv (mock LLM, local filesystem storage)
#   frontend  : ng serve with proxy.local.json (localhost targets)
#
# Prereqs: JDK 21+, Python 3.11+, Node 20+, Maven (or mvnw via SDK manager).
# Usage:   ./start-local.sh      (from the repo root)
# Stop:    kill the PIDs printed below, or Ctrl+C each log tail.
# =============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "== AI Coach Mastery — Docker-free local mode =="

for tool in java python3 node npm mvn; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "ERROR: required tool '$tool' not found on PATH"; exit 1; }
done

# --- ai-engine venv -----------------------------------------------------------
VENV="$ROOT/ai-engine/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  echo "Creating ai-engine venv + installing dependencies (one-time)..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" -q install --upgrade pip
  "$VENV/bin/pip" -q install fastapi "uvicorn[standard]" "pydantic>=2" \
      pydantic-settings httpx numpy scipy statsmodels python-pptx \
      python-docx reportlab matplotlib
fi

# --- frontend node_modules ------------------------------------------------------
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Installing frontend dependencies (one-time)..."
  (cd "$ROOT/frontend" && npm install --no-audit --no-fund)
fi

mkdir -p "$ROOT/.local-logs"

# --- Launch tiers ----------------------------------------------------------------
echo "Starting ai-engine on :8000 ..."
(cd "$ROOT/ai-engine" && \
  LLM_PROVIDER=mock STORAGE_PROVIDER=local \
  LOCAL_STORAGE_PATH="$ROOT/ai-engine/artifacts" \
  "$VENV/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  > "$ROOT/.local-logs/ai-engine.log" 2>&1) &
AI_PID=$!

echo "Starting core-api on :8080 (local profile, H2) ..."
(cd "$ROOT/core-api" && \
  mvn -q spring-boot:run -Dspring-boot.run.profiles=local \
  > "$ROOT/.local-logs/core-api.log" 2>&1) &
CORE_PID=$!

echo "Starting frontend on :4200 ..."
(cd "$ROOT/frontend" && \
  npx ng serve --proxy-config proxy.local.json \
  > "$ROOT/.local-logs/frontend.log" 2>&1) &
FE_PID=$!

cat <<EOF

All tiers launching (logs in .local-logs/):
  ai-engine PID $AI_PID   -> http://localhost:8000/docs
  core-api  PID $CORE_PID -> http://localhost:8080/swagger-ui.html
  frontend  PID $FE_PID   -> http://localhost:4200

First core-api start auto-seeds the 4 showcase clients (H2 file: core-api/.localdb).
Smoke-test once healthy:  python3 scripts/smoke_test.py
Stop everything:          kill $AI_PID $CORE_PID $FE_PID
EOF
