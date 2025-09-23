"""
Smart GUI launcher for LinuxTrainer
Automatically finds available port and starts the web GUI
"""
import socket
import sys
from pathlib import Path
import subprocess
import time
import threading
import os

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ui.web_gui import LinuxTrainerWebGUI


def find_free_port(start_port=8080, max_port=8090):
    """Find a free port starting from start_port"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


def main():
    """Start the web GUI on an available port"""
    port = find_free_port()
    
    if port is None:
        print("❌ No available ports found (8080-8089)")
        return

    # Start browser thread HERE with the correct port
    threading.Thread(target=open_browser_kiosk, args=(port,), daemon=True).start()
    
    print(f"🚀 Starting LinuxTrainer Web GUI...")
    print(f"🌐 Open your browser: http://127.0.0.1:{port}")
    print(f"📱 Works on desktop, tablet, and mobile!")
    print(f"⏹️  Press Ctrl+C to stop")
    print()
    
    try:
        gui = LinuxTrainerWebGUI()
        gui.run(port=port)
    except KeyboardInterrupt:
        print("\n�� LinuxTrainer Web GUI stopped")
    except Exception as e:
        print(f"❌ Error: {e}")




# Add this to your existing start_gui.py



def open_browser_kiosk(port):
    time.sleep(6)  # Wait for Flask server to fully start
    url = 'http://127.0.0.1:' + str(port)

    # Try different Chrome paths
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser'
    ]



    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            subprocess.Popen([
                chrome_path,
                '--kiosk',
                '--no-first-run',
                '--disable-infobars',
                '--disable-extensions',
                url
            ])
            print(f"Opening LinuxTrainer in fullscreen mode...")
            break
    else:
        print("Chrome not found. Please open http://localhost:5003 manually")


if __name__ == "__main__":
    main()
