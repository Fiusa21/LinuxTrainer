"""
Session Management for Training Data
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import logging

from .models import TrainingSession, PowerData, HeartRateData, DeviceInfo

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages training sessions and data persistence"""
    
    def __init__(self, data_dir: str = "training_sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.current_session: Optional[TrainingSession] = None
        
    def start_session(self, device_info: DeviceInfo) -> TrainingSession:
        """Start a new training session"""
        session_id = str(uuid.uuid4())
        self.current_session = TrainingSession(
            session_id=session_id,
            start_time=datetime.now(),
            device_info=device_info
        )
        logger.info(f"Started training session: {session_id}")
        return self.current_session
    
    def end_session(self) -> Optional[TrainingSession]:
        """End the current training session"""
        if not self.current_session:
            logger.warning("No active session to end")
            return None
            
        self.current_session.end_time = datetime.now()
        duration = (self.current_session.end_time - self.current_session.start_time).total_seconds()
        
        # Calculate totals
        if self.current_session.power_data:
            total_power = sum(p.instantaneous_power for p in self.current_session.power_data)
            avg_power = total_power / len(self.current_session.power_data) if self.current_session.power_data else 0
            self.current_session.total_energy = (total_power * duration) / 3600  # kJ
            
        logger.info(f"Ended training session: {self.current_session.session_id}")
        logger.info(f"Duration: {duration:.1f}s, Data points: {len(self.current_session.power_data)}")
        
        # Save session
        self.save_session(self.current_session)
        
        completed_session = self.current_session
        self.current_session = None
        return completed_session
    
    def add_power_data(self, power_data: PowerData):
        """Add power data to current session"""
        if not self.current_session:
            logger.warning("No active session to add power data to")
            return
            
        self.current_session.power_data.append(power_data)
        
        # Update distance if speed is available
        if power_data.speed and self.current_session.power_data:
            # Simple distance calculation (would need more sophisticated integration in real app)
            if len(self.current_session.power_data) > 1:
                prev_data = self.current_session.power_data[-2]
                time_diff = (power_data.timestamp - prev_data.timestamp).total_seconds()
                distance_increment = (power_data.speed * time_diff) / 3600  # km
                self.current_session.total_distance += distance_increment
    
    def add_heart_rate_data(self, hr_data: HeartRateData):
        """Add heart rate data to current session"""
        if not self.current_session:
            logger.warning("No active session to add heart rate data to")
            return
            
        self.current_session.heart_rate_data.append(hr_data)
    
    def save_session(self, session: TrainingSession):
        """Save session to file"""
        filename = f"{session.session_id}.json"
        filepath = self.data_dir / filename
        
        try:
            session_data = {
                'session_id': session.session_id,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'device_info': {
                    'address': session.device_info.address,
                    'name': session.device_info.name,
                    'device_type': session.device_info.device_type.value if session.device_info.device_type else None,
                    'manufacturer': session.device_info.manufacturer,
                    'model': session.device_info.model
                } if session.device_info else None,
                'power_data': [
                    {
                        'timestamp': pd.timestamp.isoformat(),
                        'instantaneous_power': pd.instantaneous_power,
                        'average_power': pd.average_power,
                        'cadence': pd.cadence,
                        'speed': pd.speed,
                        'distance': pd.distance
                    } for pd in session.power_data
                ],
                'heart_rate_data': [
                    {
                        'timestamp': hr.timestamp.isoformat(),
                        'heart_rate': hr.heart_rate,
                        'rr_intervals': hr.rr_intervals
                    } for hr in session.heart_rate_data
                ],
                'total_distance': session.total_distance,
                'total_energy': session.total_energy
            }
            
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            logger.info(f"Saved session to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def load_session(self, session_id: str) -> Optional[TrainingSession]:
        """Load session from file"""
        filename = f"{session_id}.json"
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Session file not found: {filepath}")
            return None
            
        try:
            with open(filepath, 'r') as f:
                session_data = json.load(f)
            
            # Parse device info
            device_info = None
            if session_data.get('device_info'):
                di = session_data['device_info']
                device_info = DeviceInfo(
                    address=di['address'],
                    name=di['name'],
                    device_type=DeviceType(di['device_type']) if di['device_type'] else None,
                    manufacturer=di.get('manufacturer'),
                    model=di.get('model')
                )
            
            # Parse power data
            power_data = []
            for pd in session_data.get('power_data', []):
                power_data.append(PowerData(
                    timestamp=datetime.fromisoformat(pd['timestamp']),
                    instantaneous_power=pd['instantaneous_power'],
                    average_power=pd.get('average_power'),
                    cadence=pd.get('cadence'),
                    speed=pd.get('speed'),
                    distance=pd.get('distance')
                ))
            
            # Parse heart rate data
            heart_rate_data = []
            for hr in session_data.get('heart_rate_data', []):
                heart_rate_data.append(HeartRateData(
                    timestamp=datetime.fromisoformat(hr['timestamp']),
                    heart_rate=hr['heart_rate'],
                    rr_intervals=hr.get('rr_intervals')
                ))
            
            # Create session
            session = TrainingSession(
                session_id=session_data['session_id'],
                start_time=datetime.fromisoformat(session_data['start_time']),
                end_time=datetime.fromisoformat(session_data['end_time']) if session_data.get('end_time') else None,
                device_info=device_info,
                power_data=power_data,
                heart_rate_data=heart_rate_data,
                total_distance=session_data.get('total_distance', 0.0),
                total_energy=session_data.get('total_energy', 0.0)
            )
            
            logger.info(f"Loaded session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """List all available session IDs"""
        session_files = list(self.data_dir.glob("*.json"))
        return [f.stem for f in session_files]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file"""
        filename = f"{session_id}.json"
        filepath = self.data_dir / filename
        
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted session: {session_id}")
                return True
            else:
                logger.warning(f"Session file not found: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
