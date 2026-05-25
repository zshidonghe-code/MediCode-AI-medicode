# =============================================================================
# MediCode — Development Startup Script (Bash / Git Bash / WSL)
# =============================================================================
# Usage:
#   bash scripts/dev.sh          # start both services
#   bash scripts/dev.sh backend  # start backend only
#   bash scripts/dev.sh frontend # start frontend only
# =============================================================================

set -euo pipefail

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ---- Paths ----
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "${CYAN}  MediCode Development Environment${NC}"
echo -e "${CYAN}══════════════════════════════════════════${NC}"

start_backend() {
    echo -e "\n${GREEN}[backend]${NC} Starting FastAPI server..."

    cd "$BACKEND_DIR"

    # Check if .env exists
    if [ ! -f .env ]; then
        echo -e "${YELLOW}[backend]${NC} No .env found, copying from .env.example..."
        cp .env.example .env
        echo -e "${YELLOW}[backend]${NC} Please edit backend/.env and re-run."
        exit 1
    fi

    # Check/create virtual environment
    if [ ! -d .venv ]; then
        echo -e "${YELLOW}[backend]${NC} Creating Python virtual environment..."
        python3 -m venv .venv
    fi

    # Activate and install deps
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate

    if [ ! -f .venv/.deps_installed ]; then
        echo -e "${YELLOW}[backend]${NC} Installing Python dependencies..."
        pip install --upgrade pip -q
        pip install -r requirements.txt -q
        touch .venv/.deps_installed
        echo -e "${GREEN}[backend]${NC} Dependencies installed."
    fi

    echo -e "${GREEN}[backend]${NC} Running on http://localhost:8000"
    echo -e "${GREEN}[backend]${NC} API docs: http://localhost:8000/docs"
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
}

start_frontend() {
    echo -e "\n${GREEN}[frontend]${NC} Starting Vite dev server..."

    cd "$FRONTEND_DIR"

    # Install deps if needed
    if [ ! -d node_modules ]; then
        echo -e "${YELLOW}[frontend]${NC} Installing Node.js dependencies..."
        npm install
        echo -e "${GREEN}[frontend]${NC} Dependencies installed."
    fi

    echo -e "${GREEN}[frontend]${NC} Running on http://localhost:5173"
    npm run dev
}

# ---- Trap Ctrl+C ----
cleanup() {
    echo -e "\n${YELLOW}[shutdown]${NC} Stopping all services..."
    kill 0
    exit 0
}
trap cleanup SIGINT SIGTERM

# ---- Main ----
case "${1:-all}" in
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        # Start backend in background, frontend in foreground
        start_backend &
        BACKEND_PID=$!

        # Wait for backend to be healthy
        echo -e "${YELLOW}[wait]${NC} Waiting for backend to be ready..."
        for i in $(seq 1 30); do
            if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                echo -e "${GREEN}[wait]${NC} Backend is ready."
                break
            fi
            sleep 1
        done

        start_frontend &
        FRONTEND_PID=$!

        wait
        ;;
    *)
        echo -e "${RED}Usage: $0 [backend|frontend|all]${NC}"
        exit 1
        ;;
esac
