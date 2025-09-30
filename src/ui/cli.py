"""
Command-line interface for LinuxTrainer CURRENTLY NOT RUNNABLE!!!
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import LinuxTrainerApp
from src.devices.kickr_trainer import KickrTrainer
from src.core.session_manager import SessionManager
from src.core.data_export import DataExporter
from loguru import logger


async def scan_devices():
    """Scan for available devices"""
    logger.info("Scanning for Kickr devices...")
    devices = await KickrTrainer.scan_for_devices(timeout=10.0)
    
    if not devices:
        print("No Kickr devices found")
        return
    
    print(f"Found {len(devices)} Kickr device(s):")
    for i, device in enumerate(devices, 1):
        print(f"  {i}. {device.name} ({device.address})")


async def list_sessions():
    """List all saved training sessions"""
    session_manager = SessionManager()
    sessions = session_manager.list_sessions()
    
    if not sessions:
        print("No training sessions found")
        return
    
    print(f"Found {len(sessions)} training session(s):")
    for session_id in sessions:
        print(f"  - {session_id}")


async def export_session(session_id: str, format_type: str = "all"):
    """Export a training session"""
    session_manager = SessionManager()
    data_exporter = DataExporter()
    
    session = session_manager.load_session(session_id)
    if not session:
        print(f"Session {session_id} not found")
        return
    
    try:
        if format_type == "all":
            exports = data_exporter.export_all_formats(session)
            print(f"Exported session to: {list(exports.keys())}")
        elif format_type == "csv":
            filepath = data_exporter.export_to_csv(session)
            print(f"Exported to CSV: {filepath}")
        elif format_type == "json":
            filepath = data_exporter.export_to_json(session)
            print(f"Exported to JSON: {filepath}")
        elif format_type == "tcx":
            filepath = data_exporter.export_to_tcx(session)
            print(f"Exported to TCX: {filepath}")
        else:
            print(f"Unknown format: {format_type}")
    except Exception as e:
        print(f"Export failed: {e}")


async def run_training(workout_type: str = None, no_display: bool = False):
    """Run the main training application"""
    app = LinuxTrainerApp(use_live_display=not no_display)
    await app.run(workout_type=workout_type)


def list_workouts():
    """List available workout types"""
    print("Available workout types:")
    print("  steady    - 30 minute steady state at 200W")
    print("  intervals - 5x1 minute intervals (300W work, 150W rest)")
    print("  tempo     - 20 minute tempo at 250W")
    print("  free      - Free ride (no structured workout)")


def run_gui(gui_type: str = "tkinter"):
    """Run GUI application"""
    if gui_type == "tkinter":
        try:
            from src.ui.gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"Tkinter GUI not available: {e}")
            print("Try: python3 web_gui.py")
    elif gui_type == "web":
        try:
            from src.ui.web_gui import main as web_main
            web_main()
        except ImportError as e:
            print(f"Web GUI not available: {e}")
            print("Install Flask: pip install flask")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="LinuxTrainer - Indoor Training Application")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Scan command
    subparsers.add_parser("scan", help="Scan for available devices")
    
    # List sessions command
    subparsers.add_parser("sessions", help="List saved training sessions")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export training session")
    export_parser.add_argument("session_id", help="Session ID to export")
    export_parser.add_argument("--format", choices=["csv", "json", "tcx", "all"], 
                              default="all", help="Export format")
    
    # List workouts command
    subparsers.add_parser("workouts", help="List available workout types")
    
    # Run training command
    train_parser = subparsers.add_parser("train", help="Start training session")
    train_parser.add_argument("--workout", choices=["steady", "intervals", "tempo", "free"],
                             help="Workout type to run")
    train_parser.add_argument("--no-display", action="store_true",
                             help="Disable live display")
    
    # GUI command
    gui_parser = subparsers.add_parser("gui", help="Start GUI application")
    gui_parser.add_argument("--type", choices=["tkinter", "web"], default="tkinter",
                           help="GUI type to use")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # Execute command
    if args.command == "scan":
        asyncio.run(scan_devices())
    elif args.command == "sessions":
        asyncio.run(list_sessions())
    elif args.command == "export":
        asyncio.run(export_session(args.session_id, args.format))
    elif args.command == "workouts":
        list_workouts()
    elif args.command == "train":
        asyncio.run(run_training(args.workout, args.no_display))
    elif args.command == "gui":
        run_gui(args.type)


if __name__ == "__main__":
    main()
