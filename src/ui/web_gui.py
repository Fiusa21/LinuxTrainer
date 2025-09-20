"""
LinuxTrainer Web GUI
"""
import asyncio
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import logging # Changed from loguru to logging
import sys
from pathlib import Path
from typing import Optional

# Ensure the project root is in the sys.path for absolute imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.devices.kickr_trainer import KickrTrainer
from src.core.models import PowerData, DeviceInfo, ConnectionStatus
from src.core.session_manager import SessionManager
from src.core.data_exporter import DataExporter

logger = logging.getLogger(__name__)

class LinuxTrainerWebGUI:
    def __init__(self):
        self.app = Flask(__name__, template_folder=str(project_root / 'src' / 'ui' / 'templates'))
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
        
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html', rider_weight=self.rider_weight_kg, gradient=self.gradient_percent)

        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                'connected': self.is_connected,
                'training': self.is_training,
                'data': self.latest_data,
                'config': {
                    'rider_weight_kg': self.rider_weight_kg,
                    'gradient_percent': self.gradient_percent
                }
            })

        @self.app.route('/api/set_config', methods=['POST'])
        def api_set_config():
            data = request.get_json()
            if 'rider_weight_kg' in data:
                try:
                    self.rider_weight_kg = float(data['rider_weight_kg'])
                    if self.kickr:
                        self.kickr.rider_weight_kg = self.rider_weight_kg
                    logger.info(f"Rider weight set to {self.rider_weight_kg} kg")
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid rider weight'}), 400
            if 'gradient_percent' in data:
                try:
                    self.gradient_percent = float(data['gradient_percent'])
                    if self.kickr:
                        self.kickr.gradient_percent = self.gradient_percent
                    logger.info(f"Gradient set to {self.gradient_percent}%")
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid gradient'}), 400
            return jsonify({'success': True, 'message': 'Configuration updated'})
        
        @self.app.route('/api/connect', methods=['POST'])
        def api_connect():
            if self.is_connected:
                return jsonify({'success': False, 'message': 'Already connected'})

            def connect_async():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    logger.info("Scanning for Kickr devices...")
                    devices = loop.run_until_complete(KickrTrainer.scan_for_devices(timeout=10))
                    
                    if not devices:
                        logger.error("No Kickr devices found!")
                        return
                    
                    device_info = devices[0]
                    logger.info(f"Found Kickr: {device_info.name}")
                    
                    # Create Kickr instance
                    self.kickr = KickrTrainer(device_info)
                    self.kickr.rider_weight_kg = self.rider_weight_kg # Apply current config
                    self.kickr.gradient_percent = self.gradient_percent # Apply current config
                    self.kickr.add_data_callback(self.on_power_data)
                    
                    # Connect
                    success = loop.run_until_complete(self.kickr.connect())
                    
                    if success:
                        self.is_connected = True
                        self.loop = loop
                        logger.info("Successfully connected to Kickr")
                        # Keep loop running
                        loop.run_forever()
                    else:
                        logger.error("Failed to connect to Kickr.")
                    
                except Exception as e:
                    logger.error(f"Connection error: {e}")
            
            # Start connection in thread
            self.thread = threading.Thread(target=connect_async, daemon=True)
            self.thread.start()
            
            return jsonify({'success': True, 'message': 'Connecting...'})

        @self.app.route('/api/disconnect', methods=['POST'])
        def api_disconnect():
            if self.kickr and self.is_connected:
                if self.loop:
                    # Schedule the disconnect in the event loop
                    asyncio.run_coroutine_threadsafe(self.kickr.disconnect(), self.loop)
                    self.loop.call_soon_threadsafe(self.loop.stop)
                self.is_connected = False
                self.kickr = None
                self.is_training = False
                self.latest_data = {
                    'power': 0, 'cadence': 0, 'speed': 0.0, 'duration': "00:00:00", 'data_count': 0
                }
                logger.info("Disconnected from Kickr")
                
            return jsonify({'success': True, 'message': 'Disconnected'})

        @self.app.route('/api/start_training', methods=['POST'])
        def api_start_training():
            if not self.is_connected:
                return jsonify({'success': False, 'message': 'Not connected to Kickr'})
            if self.is_training:
                return jsonify({'success': False, 'message': 'Training already in progress'})

            try:
                # Pass the device info from the connected Kickr
                device_info = self.kickr.device_info
                self.current_session = self.session_manager.start_session(device_info)
                self.is_training = True
                self.start_time = datetime.now()
                logger.info("Training session started")
                return jsonify({'success': True, 'message': 'Training session started'})
            except Exception as e:
                logger.error(f"Error starting training: {e}")
                return jsonify({'success': False, 'message': f'Error: {e}'})

        @self.app.route('/api/stop_training', methods=['POST'])
        def api_stop_training():
            if not self.is_training:
                return jsonify({'success': False, 'message': 'No training in progress'})

            try:
                if self.current_session:
                    self.session_manager.end_session()
                    self.session_manager.save_session(self.current_session)
                self.is_training = False
                logger.info("Training session stopped")
                
                return jsonify({'success': True, 'message': 'Training stopped'})
                
            except Exception as e:
                logger.error(f"Error stopping training: {e}")
                return jsonify({'success': False, 'message': f'Error: {e}'})
                
        @self.app.route('/api/export', methods=['POST'])
        def api_export():
            if not self.current_session:
                return jsonify({'success': False, 'message': 'No session to export'})
                
            try:
                # Export data
                exports = self.data_exporter.export_all_formats(self.current_session)
                
                return jsonify({'success': True, 'message': 'Data exported', 'files': exports})
                
            except Exception as e:
                logger.error(f"Error exporting data: {e}")
                return jsonify({'success': False, 'message': f'Error: {e}'})
    
    def on_power_data(self, power_data: PowerData):
        """Handle incoming power data"""
        logger.debug(f"Received power data in GUI: Power={power_data.instantaneous_power}W, Cadence={power_data.cadence}, Speed={power_data.speed}")
        
        # Update latest data for display
        self.latest_data['power'] = power_data.instantaneous_power
        self.latest_data['cadence'] = power_data.cadence if power_data.cadence is not None else 0
        self.latest_data['speed'] = power_data.speed if power_data.speed is not None else 0.0
        
        if hasattr(self.kickr, 'data_count'):
            self.latest_data['data_count'] = self.kickr.data_count
            
        # Add data to current session if training
        if self.is_training and self.session_manager.current_session:
            self.session_manager.add_power_data(power_data)
            
        # Update duration
        if self.is_training and hasattr(self, 'start_time'):
            duration = datetime.now() - self.start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.latest_data['duration'] = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    def run(self, host='127.0.0.1', port=5000):
        logger.info(f"Starting LinuxTrainer Web GUI at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False)

def main():
    gui = LinuxTrainerWebGUI()
    gui.run()

if __name__ == '__main__':
    main()
