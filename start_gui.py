"""
Smart GUI launcher for LinuxTrainer
Automatically finds available port and starts the web GUI
"""
import socket
import sys
from pathlib import Path

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


if __name__ == "__main__":
    main()
