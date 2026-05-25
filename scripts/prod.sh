# =============================================================================
# MediCode — Production Startup Script (Bash)
# =============================================================================
# Usage:
#   bash scripts/prod.sh help           # show available commands
#   bash scripts/prod.sh up             # start production stack
#   bash scripts/prod.sh down           # stop production stack
#   bash scripts/prod.sh restart        # restart production stack
#   bash scripts/prod.sh logs           # tail all logs
#   bash scripts/prod.sh build          # rebuild images before starting
#   bash scripts/prod.sh pull           # pull latest images from registry
# =============================================================================

set -euo pipefail

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

# ---- Ensure .env exists ----
if [ ! -f .env ]; then
    echo -e "${RED}[error] No .env file found at project root.${NC}"
    echo -e "${YELLOW}Copy .env.example to .env and configure it:${NC}"
    echo "  cp .env.example .env && nano .env"
    exit 1
fi

# ---- Commands ----
cmd_help() {
    echo -e "${CYAN}MediCode Production Commands:${NC}"
    echo "  up          Start production stack (detached)"
    echo "  down        Stop production stack"
    echo "  restart     Restart all services"
    echo "  logs        Tail logs (Ctrl+C to exit)"
    echo "  build       Rebuild Docker images"
    echo "  pull        Pull latest images from registry"
    echo "  status      Show running containers"
    echo "  shell       Open a shell in the backend container"
    echo "  backup      Run database backup"
    echo "  migrate     Run Alembic migrations"
}

cmd_up() {
    echo -e "${GREEN}[prod]${NC} Starting production stack..."
    docker compose $COMPOSE_FILES up -d --wait --wait-timeout 60
    echo -e "${GREEN}[prod]${NC} Services are running. Health check:"
    docker compose ps
}

cmd_down() {
    echo -e "${YELLOW}[prod]${NC} Stopping production stack..."
    docker compose $COMPOSE_FILES down --remove-orphans
}

cmd_restart() {
    echo -e "${YELLOW}[prod]${NC} Restarting production stack..."
    docker compose $COMPOSE_FILES restart
}

cmd_logs() {
    docker compose $COMPOSE_FILES logs -f --tail=100
}

cmd_build() {
    echo -e "${GREEN}[prod]${NC} Rebuilding Docker images..."
    docker compose $COMPOSE_FILES build --no-cache --pull
    echo -e "${GREEN}[prod]${NC} Build complete. Run 'bash $0 up' to start."
}

cmd_pull() {
    echo -e "${GREEN}[prod]${NC} Pulling latest images..."
    docker compose $COMPOSE_FILES pull
}

cmd_status() {
    docker compose $COMPOSE_FILES ps
    echo ""
    echo -e "${CYAN}Backend health:${NC}"
    curl -sf http://localhost:8000/health 2>/dev/null || echo -e "${RED}unreachable${NC}"
}

cmd_shell() {
    docker compose $COMPOSE_FILES exec backend /bin/bash
}

cmd_backup() {
    echo -e "${GREEN}[prod]${NC} Running database backup..."
    if [ -f "scripts/backup.sh" ]; then
        bash scripts/backup.sh
    else
        echo -e "${YELLOW}Backup script not found. Use docker to access data volume.${NC}"
    fi
}

cmd_migrate() {
    echo -e "${GREEN}[prod]${NC} Running Alembic migrations..."
    docker compose $COMPOSE_FILES exec backend alembic upgrade head
}

# ---- Dispatch ----
case "${1:-help}" in
    up)       cmd_up ;;
    down)     cmd_down ;;
    restart)  cmd_restart ;;
    logs)     cmd_logs ;;
    build)    cmd_build ;;
    pull)     cmd_pull ;;
    status)   cmd_status ;;
    shell)    cmd_shell ;;
    backup)   cmd_backup ;;
    migrate)  cmd_migrate ;;
    help|-h)  cmd_help ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        cmd_help
        exit 1
        ;;
esac
