#!/bin/bash
# Recruiter AI Platform - Local Demo Run Script (Linux/macOS)

echo -e "\033[0;36m🚀 Starting Recruiter AI Platform Local Demo...\033[0m"

# 1. Initialize Backend
echo -e "\n\033[0;33m📦 Setting up Backend...\033[0m"
if [ ! -f ".env" ]; then
    echo -e "\033[0;90m⚠️ .env not found. Creating from env.example...\033[0m"
    cp env.example .env
fi

# Ensure SQLite DB exists
if [ ! -f "recruiter_ai.db" ]; then
    echo -e "\033[0;90m📂 Initializing SQLite database...\033[0m"
    python3 -c "from app.database import create_tables; create_tables()"
fi

# Start Backend
echo -e "\033[0;32m⚡ Starting Backend API on http://localhost:8000\033[0m"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 2. Initialize Frontend
echo -e "\n\033[0;33m🎨 Setting up Frontend...\033[0m"
cd frontend

if [ ! -d "node_modules" ]; then
    echo -e "\033[0;90m📥 Installing frontend dependencies (npm install)...\033[0m"
    npm install
fi

if [ ! -f ".env.local" ]; then
    echo -e "\033[0;90m⚠️ .env.local not found. Creating...\033[0m"
    echo "VITE_API_URL=" > .env.local
fi

# Start Frontend
echo -e "\033[0;32m🌐 Starting Frontend UI on http://localhost:3000\033[0m"
npm run dev -- --port 3000 &
FRONTEND_PID=$!

echo -e "\n\033[0;36m✅ Local Demo Environment is launching!\033[0m"
echo "👉 Backend: http://localhost:8000/docs"
echo "👉 Frontend: http://localhost:3000"
echo -e "\n\033[0;90mPress Ctrl+C to stop both servers.\033[0m"

# Handle Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
