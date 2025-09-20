"""
Main application entry point for LinuxTrainer
"""
import asyncio
import signal
import sys
from datetime import datetime
from loguru import logger

from .devices.kickr_trainer import KickrTrainer
from .core.session_manager import SessionManager
from .core.data_export import DataExporter
from .core.workout import WorkoutExecutor, create_steady_state_workout, create_interval_workout
from .ui.live_display import LiveDisplay


class LinuxTrainerApp:
    """Main application class"""
    
    def __init__(self, use_live_display: bool = True):
        self.session_manager = SessionManager()
        self.data_exporter = DataExporter()
        self.workout_executor = WorkoutExecutor()
        self.device: KickrTrainer = None
        self.live_display = LiveDisplay() if use_live_display else None
        self.running = False
        
    async def run(self, workout_type: str = None):
        """Main application loop"""
        logger.info("Starting LinuxTrainer...")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Scan for devices
            devices = await KickrTrainer.scan_for_devices(timeout=10.0)
            
            if not devices:
                logger.error("No Kickr devices found")
                return
            
            # Use the first found device
            device_info = devices[0]
            logger.info(f"Using device: {device_info.name} ({device_info.address})")
            
            # Create device instance
            self.device = KickrTrainer(device_info)
            
            # Add data callbacks
            self.device.add_data_callback(self._on_power_data)
            
            # Connect to device
            if await self.device.connect():
                # Start training session
                session = self.session_manager.start_session(device_info)
                logger.info(f"Started training session: {session.session_id}")
                
                # Setup live display
                if self.live_display:
                    self.live_display.set_session(session)
                
                # Setup workout if specified
                if workout_type:
                    await self._setup_workout(workout_type)
                
                # Start live display in background if enabled
                if self.live_display:
                    display_task = asyncio.create_task(self.live_display.start_display())
                
                # Main loop
                self.running = True
                await self._main_loop()
                
                # Stop live display
                if self.live_display:
                    self.live_display.stop_display()
                    if 'display_task' in locals():
                        display_task.cancel()
            else:
                logger.error("Failed to connect to device")
                
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self._cleanup()
    
    async def _setup_workout(self, workout_type: str):
        """Setup workout based on type"""
        if workout_type == "steady":
            workout = create_steady_state_workout(30, 200)  # 30 min at 200W
        elif workout_type == "intervals":
            workout = create_interval_workout(60, 60, 300, 150, 5)  # 5x1min intervals
        elif workout_type == "tempo":
            workout = create_tempo_workout(20, 250)  # 20 min tempo
        else:
            logger.warning(f"Unknown workout type: {workout_type}")
            return
        
        # Add workout callbacks
        self.workout_executor.add_callback(self._on_workout_event)
        
        # Start workout
        self.workout_executor.start_workout(workout)
        logger.info(f"Started workout: {workout.name}")
    
    async def _main_loop(self):
        """Main application loop"""
        logger.info("Training session active. Press Ctrl+C to stop.")
        
        while self.running:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
    
    def _on_power_data(self, power_data):
        """Handle incoming power data"""
        # Update live display
        if self.live_display:
            self.live_display.update_power_data(power_data)
        
        # Add to current session
        self.session_manager.add_power_data(power_data)
        
        # Update workout executor
        if self.workout_executor.current_workout:
            guidance = self.workout_executor.update(power_data)
            if guidance:
                self._log_workout_guidance(guidance)
    
    def _on_workout_event(self, event_type: str, data):
        """Handle workout events"""
        logger.info(f"Workout event: {event_type}")
        
        if event_type == "workout_completed":
            logger.info("Workout completed! Great job!")
        elif event_type == "interval_started":
            interval = data.get("interval")
            logger.info(f"New interval: {interval.description}")
    
    def _log_workout_guidance(self, guidance):
        """Log workout guidance (simplified)"""
        if guidance.get("guidance"):
            logger.info(f"Guidance: {guidance['guidance']}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")
        
        # Stop workout
        if self.workout_executor.current_workout:
            self.workout_executor.stop_workout()
        
        # Disconnect device
        if self.device:
            await self.device.disconnect()
        
        # End session and export data
        if self.session_manager.current_session:
            session = self.session_manager.end_session()
            if session and session.power_data:
                try:
                    exports = self.data_exporter.export_all_formats(session)
                    logger.info(f"Exported session data: {list(exports.keys())}")
                except Exception as e:
                    logger.error(f"Failed to export session data: {e}")


async def main(workout_type: str = None, use_live_display: bool = True):
    """Application entry point"""
    app = LinuxTrainerApp(use_live_display=use_live_display)
    await app.run(workout_type=workout_type)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # Run the application
    asyncio.run(main())
