"""
LinuxTrainer Web GUI
"""
import asyncio
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
import logging
import sys
from pathlib import Path
from typing import Optional, List
import json

# Ensure the project root is in the sys.path for absolute imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.devices.kickr_trainer import KickrTrainer
from src.core.models import PowerData, DeviceInfo, ConnectionStatus
from src.core.session_manager import SessionManager
from src.core.data_exporter import DataExporter

logger = logging.getLogger(__name__)

class ConnectionLogHandler:
    """Simple log handler that only stores connection-related messages"""
    def __init__(self):
        self.logs = []
        self.max_logs = 20  # Keep only last 20 logs
    
    def add_log(self, message, level="INFO"):
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        
        # Keep only the last max_logs entries
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
    
    def get_logs(self):
        return self.logs.copy()
    
    def clear_logs(self):
        self.logs.clear()

class LinuxTrainerWebGUI:
    def __init__(self):
        # Configure Flask with proper static file paths
        self.app = Flask(
            __name__, 
            template_folder=str(project_root / 'src' / 'ui' / 'templates'),
            static_folder=str(project_root / 'src' / 'ui' / 'static'),
            static_url_path='/static'
        )
        
        self.kickr: Optional[KickrTrainer] = None
        self.is_connected = False
        self.is_training = False
        self.latest_data = {
            'power': 0,
            'cadence': 0,
            'speed': 0.0,
            'duration': "00:00:00",
            'data_count': 0
        }
        self.start_time: Optional[datetime] = None
        self.current_session = None
        self.session_manager = SessionManager()
        self.data_exporter = DataExporter()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        
        # Configuration for power-based speed calculation
        self.rider_weight_kg = 75.0
        self.gradient_percent = 0.0
        
        # Setup connection log handler
        self.connection_log = ConnectionLogHandler()
        
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files"""
            return send_from_directory(self.app.static_folder, filename)
        
        @self.app.route('/api/status')
        def api_status():
            """Get current status and data"""
            return jsonify({
                'connected': self.is_connected,
                'training': self.is_training,
                'data': self.latest_data
            })
        
        @self.app.route('/api/connect', methods=['POST'])
        def api_connect():
            """Connect to Kickr trainer"""
            try:
                if self.is_connected:
                    return jsonify({'success': False, 'message': 'Already connected'})
                
                self.connection_log.add_log("Searching for Kickr devices...", "INFO")
                
                # Start the asyncio event loop in a separate thread
                if not self.loop or self.loop.is_closed():
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                    self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
                    self.thread.start()
                
                # Schedule the connection in the event loop
                future = asyncio.run_coroutine_threadsafe(self._connect_async(), self.loop)
                result = future.result(timeout=30)  # 30 second timeout
                
                if result:
                    self.is_connected = True
                    self.connection_log.add_log("✅ Successfully connected to Kickr trainer", "SUCCESS")
                    return jsonify({'success': True, 'message': 'Connected to Kickr trainer'})
                else:
                    self.connection_log.add_log("❌ Failed to connect to Kickr trainer", "ERROR")
                    return jsonify({'success': False, 'message': 'Failed to connect to Kickr trainer'})
                    
            except Exception as e:
                self.connection_log.add_log(f"❌ Connection error: {str(e)}", "ERROR")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/disconnect', methods=['POST'])
        def api_disconnect():
            """Disconnect from Kickr trainer"""
            try:
                if not self.is_connected:
                    return jsonify({'success': False, 'message': 'Not connected'})
                
                self.connection_log.add_log("Disconnecting from Kickr trainer...", "INFO")
                
                if self.kickr:
                    # Schedule disconnection in the event loop
                    future = asyncio.run_coroutine_threadsafe(self._disconnect_async(), self.loop)
                    future.result(timeout=10)  # 10 second timeout
                
                self.is_connected = False
                self.is_training = False
                self.kickr = None
                self.connection_log.add_log("✅ Disconnected from Kickr trainer", "SUCCESS")
                return jsonify({'success': True, 'message': 'Disconnected from Kickr trainer'})
                
            except Exception as e:
                self.connection_log.add_log(f"❌ Disconnection error: {str(e)}", "ERROR")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/start_training', methods=['POST'])
        def api_start_training():
            """Start training session"""
            try:
                if not self.is_connected:
                    return jsonify({'success': False, 'message': 'Not connected to trainer'})
                
                if self.is_training:
                    return jsonify({'success': False, 'message': 'Already training'})
                
                # Start new session
                if self.kickr and self.kickr.device_info:
                    self.current_session = self.session_manager.start_session(self.kickr.device_info)
                    self.start_time = datetime.now()
                    self.is_training = True
                    self.connection_log.add_log("🚴 Training session started", "SUCCESS")
                    return jsonify({'success': True, 'message': 'Training started'})
                else:
                    return jsonify({'success': False, 'message': 'No device info available'})
                    
            except Exception as e:
                self.connection_log.add_log(f"❌ Failed to start training: {str(e)}", "ERROR")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/stop_training', methods=['POST'])
        def api_stop_training():
            """Stop training session"""
            try:
                if not self.is_training:
                    return jsonify({'success': False, 'message': 'Not currently training'})
                
                # End current session - FIXED: end_session() takes no parameters
                if self.current_session:
                    self.session_manager.end_session()  # No parameter needed
                    self.current_session = None
                
                self.is_training = False
                self.start_time = None
                self.connection_log.add_log("⏹️ Training session stopped", "SUCCESS")
                return jsonify({'success': True, 'message': 'Training stopped'})
                
            except Exception as e:
                self.connection_log.add_log(f"❌ Failed to stop training: {str(e)}", "ERROR")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/export', methods=['POST'])
        def api_export():
            """Export training data"""
            try:
                if not self.current_session:
                    return jsonify({'success': False, 'message': 'No active session to export'})
                
                # Export data
                export_paths = self.data_exporter.export_all_formats(self.current_session)
                self.connection_log.add_log("📁 Data exported successfully", "SUCCESS")
                return jsonify({'success': True, 'message': 'Data exported successfully', 'paths': export_paths})
                
            except Exception as e:
                self.connection_log.add_log(f"❌ Export failed: {str(e)}", "ERROR")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/logs')
        def api_logs():
            """Get connection logs"""
            logs = self.connection_log.get_logs()
            return jsonify({'logs': logs})
        
        @self.app.route('/api/logs/clear', methods=['POST'])
        def api_clear_logs():
            """Clear all logs"""
            self.connection_log.clear_logs()
            self.connection_log.add_log("System ready", "INFO")
            return jsonify({'success': True, 'message': 'Logs cleared'})

    def _run_async_loop(self):
        """Run the asyncio event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect_async(self):
        """Async connection to Kickr trainer"""
        try:
            # Scan for devices
            self.connection_log.add_log("Scanning for Kickr devices...", "INFO")
            devices = await KickrTrainer.scan_for_devices(timeout=10)
            if not devices:
                self.connection_log.add_log("❌ No Kickr devices found", "ERROR")
                return False
            
            self.connection_log.add_log(f"Found Kickr device: {devices[0].name}", "INFO")
            
            # Create trainer instance
            self.kickr = KickrTrainer(devices[0])
            self.kickr.rider_weight_kg = self.rider_weight_kg
            self.kickr.gradient_percent = self.gradient_percent
            
            # Add data callback
            self.kickr.add_data_callback(self.on_power_data)
            
            # Connect
            self.connection_log.add_log("Connecting to Kickr trainer...", "INFO")
            await self.kickr.connect()
            self.connection_log.add_log(f"✅ Connected to {self.kickr.device_info.name}", "SUCCESS")
            return True
            
        except Exception as e:
            self.connection_log.add_log(f"❌ Connection failed: {str(e)}", "ERROR")
            return False

    async def _disconnect_async(self):
        """Async disconnection from Kickr trainer"""
        try:
            if self.kickr:
                await self.kickr.disconnect()
        except Exception as e:
            self.connection_log.add_log(f"❌ Disconnection error: {str(e)}", "ERROR")

    def on_power_data(self, power_data: PowerData):
        """Handle incoming power data"""
        try:
            # Update latest data
            self.latest_data.update({
                'power': power_data.instantaneous_power,
                'cadence': power_data.cadence if power_data.cadence is not None else 0,
                'speed': power_data.speed if power_data.speed is not None else 0.0,
                'data_count': self.latest_data.get('data_count', 0) + 1
            })
            
            # Update duration
            if self.start_time:
                duration = datetime.now() - self.start_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.latest_data['duration'] = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
            # Add to current session if training
            if self.is_training and self.current_session:
                self.session_manager.add_power_data(power_data)
                
        except Exception as e:
            self.connection_log.add_log(f"❌ Data processing error: {str(e)}", "ERROR")

    def run(self, host='0.0.0.0', port=5003, debug=False):
        """Run the web GUI"""
        self.connection_log.add_log("System ready", "INFO")
        logger.info(f"Starting LinuxTrainer Web GUI on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    gui = LinuxTrainerWebGUI()
    gui.run(debug=True)
