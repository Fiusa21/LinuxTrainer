"""
Demo script showing LinuxTrainer features
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.models import PowerData, HeartRateData, TrainingSession, DeviceInfo, DeviceType
from src.core.session_manager import SessionManager
from src.core.data_export import DataExporter
from src.core.workout import create_steady_state_workout, create_interval_workout
from datetime import datetime, timedelta


def create_demo_session():
    """Create a demo training session with sample data"""
    # Create device info
    device_info = DeviceInfo(
        address="AA:BB:CC:DD:EE:FF",
        name="Demo Kickr",
        device_type=DeviceType.SMART_TRAINER
    )
    
    # Create session
    session = TrainingSession(
        session_id="demo-session-123",
        start_time=datetime.now() - timedelta(minutes=30),
        device_info=device_info
    )
    
    # Add sample power data
    base_time = session.start_time
    for i in range(1800):  # 30 minutes of data (1 second intervals)
        timestamp = base_time + timedelta(seconds=i)
        power = 200 + (i % 60) * 2  # Varying power
        cadence = 85 + (i % 20)  # Varying cadence
        
        power_data = PowerData(
            timestamp=timestamp,
            instantaneous_power=power,
            cadence=cadence,
            speed=25.0 + (i % 10) * 0.5
        )
        session.power_data.append(power_data)
    
    # Add sample heart rate data
    for i in range(0, 1800, 5):  # Every 5 seconds
        timestamp = base_time + timedelta(seconds=i)
        hr = 140 + (i % 30)  # Varying heart rate
        
        hr_data = HeartRateData(
            timestamp=timestamp,
            heart_rate=hr
        )
        session.heart_rate_data.append(hr_data)
    
    # Calculate totals
    session.total_distance = 12.5  # km
    session.total_energy = 450.0  # kJ
    session.end_time = datetime.now()
    
    return session


def demo_data_export():
    """Demonstrate data export functionality"""
    print("🚀 LinuxTrainer Demo - Data Export")
    print("=" * 50)
    
    # Create demo session
    session = create_demo_session()
    print(f"Created demo session: {session.session_id}")
    print(f"Duration: {(session.end_time - session.start_time).total_seconds()/60:.1f} minutes")
    print(f"Power data points: {len(session.power_data)}")
    print(f"Heart rate data points: {len(session.heart_rate_data)}")
    print()
    
    # Export data
    exporter = DataExporter("demo_exports")
    print("Exporting data to multiple formats...")
    
    try:
        exports = exporter.export_all_formats(session)
        print("✅ Export successful!")
        print("Files created:")
        for format_type, filepath in exports.items():
            print(f"  {format_type.upper()}: {filepath}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
    
    print()


def demo_workouts():
    """Demonstrate workout functionality"""
    print("🚀 LinuxTrainer Demo - Workouts")
    print("=" * 50)
    
    # Create different workout types
    workouts = [
        create_steady_state_workout(30, 200),
        create_interval_workout(60, 60, 300, 150, 5),
        create_interval_workout(30, 90, 400, 200, 8)
    ]
    
    print("Available workouts:")
    for i, workout in enumerate(workouts, 1):
        print(f"  {i}. {workout.name}")
        print(f"     Description: {workout.description}")
        print(f"     Duration: {workout.total_duration/60:.1f} minutes")
        print(f"     Type: {workout.workout_type.value}")
        print()
    
    print("Workout intervals example:")
    workout = workouts[1]  # Interval workout
    for i, interval in enumerate(workout.intervals, 1):
        print(f"  Interval {i}: {interval.description}")
        if interval.rest_seconds > 0:
            print(f"    Rest: {interval.rest_seconds}s")
    print()


def demo_session_management():
    """Demonstrate session management"""
    print("🚀 LinuxTrainer Demo - Session Management")
    print("=" * 50)
    
    # Create session manager
    session_manager = SessionManager("demo_sessions")
    
    # Create and save demo session
    session = create_demo_session()
    session_manager.save_session(session)
    print(f"✅ Saved session: {session.session_id}")
    
    # List sessions
    sessions = session_manager.list_sessions()
    print(f"📋 Found {len(sessions)} sessions:")
    for session_id in sessions:
        print(f"  - {session_id}")
    
    # Load session
    if sessions:
        loaded_session = session_manager.load_session(sessions[0])
        if loaded_session:
            print(f"✅ Loaded session: {loaded_session.session_id}")
            print(f"   Power data points: {len(loaded_session.power_data)}")
            print(f"   Heart rate data points: {len(loaded_session.heart_rate_data)}")
    
    print()


def main():
    """Run all demos"""
    print("🎯 LinuxTrainer Feature Demo")
    print("=" * 60)
    print()
    
    demo_data_export()
    demo_workouts()
    demo_session_management()
    
    print("🎉 Demo completed!")
    print()
    print("To run the actual application:")
    print("  python cli.py scan")
    print("  python cli.py train")
    print("  python cli.py workouts")


if __name__ == "__main__":
    main()
