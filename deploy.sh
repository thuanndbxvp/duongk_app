#!/usr/bin/env bash
# =====================================================
# deploy.sh — Deploy appdk lên VPS ai86.click
# Chạy từ thư mục repo trên VPS dưới user `deploy`.
#
# Usage:
#   ./deploy.sh           # build + up
#   ./deploy.sh --logs    # build + up + tail logs
#   ./deploy.sh --pull    # git pull trước khi build
# =====================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)]${NC} $*"; }
err()  { echo -e "${RED}[$(date +%H:%M:%S)]${NC} $*" >&2; }

# --- Pre-flight checks ---
if ! command -v docker >/dev/null 2>&1; then
    err "Docker chưa cài. Chạy bootstrap.sh trước."
    exit 1
fi

if [[ ! -f .env.production ]]; then
    err ".env.production chưa tồn tại."
    err "   cp .env.production.template .env.production"
    err "   chmod 600 .env.production"
    err "   nano .env.production"
    exit 1
fi

PULL=0
LOGS=0
for arg in "$@"; do
    case "$arg" in
        --pull) PULL=1 ;;
        --logs) LOGS=1 ;;
        *) err "Unknown arg: $arg"; exit 1 ;;
    esac
done

# --- Git pull (optional) ---
if [[ $PULL -eq 1 ]]; then
    log "Git pull..."
    git pull --ff-only
fi

# --- Sanity: env file perm ---
PERM=$(stat -c '%a' .env.production)
if [[ "$PERM" != "600" ]]; then
    warn ".env.production đang chmod $PERM, set về 600"
    chmod 600 .env.production
fi

# --- Build ---
log "docker compose build..."
docker compose -f docker-compose.prod.yml --env-file .env.production build

# --- Up ---
log "docker compose up -d..."
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# --- Wait healthcheck (api) ---
log "Chờ API healthcheck..."
for i in {1..30}; do
    if docker compose -f docker-compose.prod.yml exec -T api curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
        log "API healthy."
        break
    fi
    sleep 2
done

# --- Prune old images ---
log "docker system prune -f..."
docker system prune -f

# --- Show status ---
log "=== Trạng thái services ==="
docker compose -f docker-compose.prod.yml ps

# --- Tail logs ---
if [[ $LOGS -eq 1 ]]; then
    log "Tailing logs (Ctrl+C để thoát)..."
    docker compose -f docker-compose.prod.yml logs -f --tail 100
fi

log "✅ Deploy xong. Test: curl -I https://app.ai86.click"