#!/usr/bin/env bash
# ==============================================================================
# SIP & Fintech Investor Discovery Engine — Master Launch Script
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================================"
echo "  🚀 Starting SIP & Fintech Investor Discovery Engine (Prompt-Driven AI)"
echo "================================================================================"

# 1. Environment checks
if [ -d "$HOME/.local/node/bin" ]; then
    export PATH="$HOME/.local/node/bin:$PATH"
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not found."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is required but not found."
    exit 1
fi

# 2. Python Virtual Environment Check
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment in backend/venv..."
    python3 -m venv backend/venv
    source backend/venv/bin/activate
    pip install --upgrade pip
    pip install -r backend/requirements.txt
else
    source backend/venv/bin/activate
fi

# 3. Initialize SQLite Database & Ensure Tables Exist
echo "💾 Checking SQLite database and search indexes..."
python3 -c "
from backend.database import init_db, get_stats
init_db()
stats = get_stats()
print(f'   -> Active Posts: {stats[\"total_posts\"]}')
print(f'   -> Golden Benchmarks: {stats[\"golden_count\"]}')
"

# 4. Cleanup on Exit Handler
cleanup() {
    echo ""
    echo "🛑 Shutting down SIP Discovery Engine services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo "✅ Shutdown complete. Goodbye!"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 5. Launch FastAPI Backend
echo "🌐 Starting FastAPI Backend on http://127.0.0.1:8000..."
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend health
sleep 2
curl -s http://127.0.0.1:8000/api/health > /dev/null || sleep 2

# 6. Launch Vite Frontend
echo "💻 Starting Vite Frontend Workbench on http://127.0.0.1:5173..."
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!
cd ..

echo "================================================================================"
echo "  ✅ SIP Discovery Engine is LIVE!"
echo "     👉 Frontend Workbench:    http://127.0.0.1:5173"
echo "     👉 API Health & Docs:     http://127.0.0.1:8000/docs"
echo "     👉 Evaluation Dashboard:  http://127.0.0.1:8000/api/evaluation/metrics"
echo "================================================================================"
echo "  Press [CTRL+C] at any time to stop both services."

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
