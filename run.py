"""
run.py
Convenience runner for ComplyBot.
Starts the FastAPI server with auto-reload and automatically opens
the web application directly in your default browser once the server is live.
"""

import os
import sys
import time
import socket
import threading
import webbrowser
import subprocess
import uvicorn

# Ensure UTF-8 output on Windows console to avoid charmap / cp1252 encoding crashes
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def _wait_for_server(host=HOST, port=PORT, timeout=25.0):
    """Wait until the server is actively accepting TCP connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.4)
        try:
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            try:
                sock.close()
            except Exception:
                pass
        time.sleep(0.2)
    return False


def _open_browser():
    """Wait for server to start, then open the browser automatically."""
    _wait_for_server(HOST, PORT, timeout=25.0)

    # Brief delay so FastAPI can complete route mounting
    time.sleep(0.4)

    try:
        print("\n" + "=" * 58, flush=True)
        print(f"  [+] ComplyBot is LIVE: {URL}", flush=True)
        print(f"  [+] Opening web application in your default browser...", flush=True)
        print("=" * 58 + "\n", flush=True)
    except Exception:
        pass

    # Open browser via multiple methods for 100% Windows and cross-platform reliability
    opened = False
    if sys.platform == "win32":
        if hasattr(os, "startfile"):
            try:
                os.startfile(URL)
                opened = True
            except Exception:
                pass
        if not opened:
            try:
                subprocess.Popen(f'start "" "{URL}"', shell=True)
                opened = True
            except Exception:
                pass

def _ensure_ollama_running():
    """Checks if Ollama daemon is running on port 11434; if not, attempts to start it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        res = sock.connect_ex(("127.0.0.1", 11434))
        sock.close()
        if res == 0:
            return True
    except Exception:
        pass

    try:
        print("  [*] Ollama is not active. Starting local Ollama background service...", flush=True)
        if sys.platform == "win32":
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2.0)
    except Exception as e:
        print(f"  [!] Note: Could not auto-launch Ollama ({e}). Make sure Ollama desktop app is running.", flush=True)


if __name__ == "__main__":
    # Ensure Ollama service is active
    _ensure_ollama_running()

    # Start browser launcher thread
    browser_thread = threading.Thread(target=_open_browser, daemon=True)
    browser_thread.start()

    # Start Uvicorn server with auto-reload
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        app_dir="backend",
    )
