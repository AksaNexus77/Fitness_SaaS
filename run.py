#!/usr/bin/env python3
"""
FitZone - Fitness Management System
Auto-run script: installs deps, initializes DB, seeds data, and starts server.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

# Configuration
PROJECT_DIR = Path(__file__).parent.resolve()
VENV_DIR = PROJECT_DIR / ".venv"
PYTHON_EXE = VENV_DIR / "Scripts" / "python.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "python"
PIP_EXE = VENV_DIR / "Scripts" / "pip.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "pip"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"
APP_FILE = PROJECT_DIR / "app.py"
URL = "http://127.0.0.1:5000"


def print_step(step: str):
    print(f"\n{'='*60}")
    print(f"  {step}")
    print(f"{'='*60}")


def run_cmd(cmd, cwd=None, check=True):
    """Run a shell command and stream output."""
    print(f"  > {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        print(f"[WARNING] Command failed with code {result.returncode}, continuing...")
    return result


def ensure_venv():
    """Create virtual environment if it doesn't exist."""
    if not VENV_DIR.exists():
        print_step("Creating virtual environment...")
        run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print_step("Virtual environment found.")


def install_requirements():
    """Install Python dependencies."""
    print_step("Installing / updating requirements...")
    run_cmd([str(PYTHON_EXE), "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install packages with binary wheels only to avoid build issues on Python 3.14
    # Use --only-binary :all: to ensure we get pre-built wheels
    run_cmd([str(PYTHON_EXE), "-m", "pip", "install", "--only-binary", ":all:", "numpy", "pandas", "scikit-learn"])
    
    # Install remaining requirements
    run_cmd([str(PYTHON_EXE), "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def init_and_seed():
    """Initialize database and seed demo data."""
    print_step("Initializing database & seeding demo data...")
    # We import app inside a small script to init DB
    script = PROJECT_DIR / "_init_db.py"
    script.write_text("""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from app import app, init_db, seed_data
with app.app_context():
    init_db()
    seed_data()
print("Database ready!")
""")
    run_cmd([str(PYTHON_EXE), str(script)])
    script.unlink(missing_ok=True)


def start_server():
    """Start the Flask development server."""
    print_step("Starting FitZone server...")
    print(f"  URL: {URL}")
    print("  Press CTRL+C to stop\n")

    # Open browser after short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open(URL)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Flask app directly (blocking)
    os.environ["FLASK_APP"] = "app.py"
    os.environ["FLASK_ENV"] = "development"
    try:
        subprocess.run([str(PYTHON_EXE), str(APP_FILE)], cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        print("\n[FitZone] Server stopped.")


def main():
    print("""
    ███████╗██╗████████╗███████╗ ██████╗ ███╗   ██╗███████╗
    ██╔════╝██║╚══██╔══╝██╔════╝██╔═══██╗████╗  ██║██╔════╝
    █████╗  ██║   ██║   █████╗  ██║   ██║██╔██╗ ██║█████╗  
    ██╔══╝  ██║   ██║   ██╔══╝  ██║   ██║██║╚██╗██║██╔══╝  
    ██║     ██║   ██║   ███████╗╚██████╔╝██║ ╚████║███████╗
    ╚═╝     ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
    """)

    ensure_venv()
    install_requirements()
    init_and_seed()
    start_server()


if __name__ == "__main__":
    main()

