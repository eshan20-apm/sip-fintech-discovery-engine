#!/usr/bin/env python3
"""
Universal Cross-Platform Runner for SIP & Fintech Investor Discovery Engine.
Works seamlessly across macOS, Linux, and Windows.
Usage:
    python run.py
"""

import os
import sys
import subprocess
import time
import signal
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

def print_banner():
    print("=" * 80)
    print("  🚀 Starting SIP & Fintech Investor Discovery Engine (Prompt-Driven AI)")
    print("  🌐 Universal Cross-Platform Launcher (macOS, Linux, Windows)")
    print("=" * 80)

def get_venv_python():
    if sys.platform == "win32":
        return os.path.join(PROJECT_ROOT, "backend", "venv", "Scripts", "python.exe")
    return os.path.join(PROJECT_ROOT, "backend", "venv", "bin", "python")

def get_venv_pip():
    if sys.platform == "win32":
        return os.path.join(PROJECT_ROOT, "backend", "venv", "Scripts", "pip.exe")
    return os.path.join(PROJECT_ROOT, "backend", "venv", "bin", "pip")

def check_and_setup_venv():
    venv_dir = os.path.join(PROJECT_ROOT, "backend", "venv")
    venv_python = get_venv_python()

    if not os.path.exists(venv_python):
        print("📦 Creating virtual environment in backend/venv...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        pip_exe = get_venv_pip()
        print("📥 Installing backend dependencies from requirements.txt...")
        subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
        subprocess.check_call([pip_exe, "install", "-r", "requirements.txt"])
    
    # Symlink root .venv if on unix and not present
    root_venv = os.path.join(PROJECT_ROOT, ".venv")
    if not os.path.exists(root_venv) and hasattr(os, "symlink") and sys.platform != "win32":
        try:
            os.symlink("backend/venv", root_venv)
        except Exception:
            pass

def check_and_setup_frontend():
    node_modules = os.path.join(PROJECT_ROOT, "frontend", "node_modules")
    if not os.path.exists(node_modules):
        npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
        if npm_cmd:
            print("📦 Installing frontend dependencies in frontend/...")
            subprocess.check_call([npm_cmd, "install"], cwd=os.path.join(PROJECT_ROOT, "frontend"))
        else:
            print("⚠️ Notice: npm not found in PATH. Using pre-built production bundle in frontend/dist if available.")

def init_database():
    venv_python = get_venv_python()
    print("💾 Initializing SQLite database...")
    code = """
from backend.database import init_db, get_stats
init_db()
stats = get_stats()
print(f'   -> Active Posts: {stats[\"total_posts\"]}')
print(f'   -> Golden Benchmarks: {stats[\"golden_count\"]}')
"""
    subprocess.check_call([venv_python, "-c", code])

def main():
    print_banner()

    if sys.version_info < (3, 9):
        print("❌ Error: Python 3.9 or higher is required.")
        sys.exit(1)

    check_and_setup_venv()
    check_and_setup_frontend()
    init_database()

    venv_python = get_venv_python()
    processes = []

    def cleanup(*args):
        print("\n🛑 Shutting down SIP Discovery Engine services...")
        for p in processes:
            try:
                if sys.platform == "win32":
                    p.terminate()
                else:
                    p.send_signal(signal.SIGTERM)
            except Exception:
                pass
        print("✅ Shutdown complete. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cleanup)

    print("\n🌐 Starting FastAPI Backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=PROJECT_ROOT
    )
    processes.append(backend_proc)

    # Launch Vite frontend if npm is available
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_cmd and os.path.exists(os.path.join(PROJECT_ROOT, "frontend", "package.json")):
        print("💻 Starting Vite Frontend Workbench on http://127.0.0.1:5173...")
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=os.path.join(PROJECT_ROOT, "frontend")
        )
        processes.append(frontend_proc)
    else:
        print("ℹ️ Serving production frontend directly through FastAPI on http://127.0.0.1:8000")

    print("\n" + "=" * 80)
    print("  ✅ SIP Discovery Engine is LIVE!")
    print("     👉 Frontend Workbench:    http://127.0.0.1:5173 (or http://127.0.0.1:8000)")
    print("     👉 API Health & Docs:     http://127.0.0.1:8000/docs")
    print("     👉 Evaluation Dashboard:  http://127.0.0.1:8000/api/evaluation/metrics")
    print("=" * 80)
    print("  Press [CTRL+C] at any time to stop services.\n")

    try:
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    # One of the processes died
                    print(f"⚠️ A service stopped with exit code {p.returncode}")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()

