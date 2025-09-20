"""
Data export functionality for training sessions
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from .models import TrainingSession, PowerData, HeartRateData


class DataExporter:
    """Export training session data to various formats"""
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
    def export_to_csv(self, session: TrainingSession, filename: Optional[str] = None) -> str:
        """Export session to CSV format"""
        if not filename:
            timestamp = session.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session.session_id[:8]}_{timestamp}.csv"
            
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'timestamp', 'power_watts', 'cadence_rpm', 'speed_kmh', 
                    'distance_m', 'heart_rate_bpm'
                ])
                
                # Combine power and heart rate data
                power_dict = {pd.timestamp: pd for pd in session.power_data}
                hr_dict = {hr.timestamp: hr for hr in session.heart_rate_data}
                
                # Get all timestamps and sort
                all_timestamps = set(power_dict.keys()) | set(hr_dict.keys())
                all_timestamps = sorted(all_timestamps)
                
                # Write data rows
                for timestamp in all_timestamps:
                    power = power_dict.get(timestamp)
                    hr = hr_dict.get(timestamp)
                    
                    writer.writerow([
                        timestamp.isoformat(),
                        power.instantaneous_power if power else '',
                        power.cadence if power and power.cadence else '',
                        power.speed if power and power.speed else '',
                        power.distance if power and power.distance else '',
                        hr.heart_rate if hr else ''
                    ])
                    
            logger.info(f"Exported session to CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
            
    def export_to_json(self, session: TrainingSession, filename: Optional[str] = None) -> str:
        """Export session to JSON format"""
        if not filename:
            timestamp = session.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session.session_id[:8]}_{timestamp}.json"
            
        filepath = self.export_dir / filename
        
        try:
            session_data = {
                'session_info': {
                    'session_id': session.session_id,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'total_distance_km': session.total_distance,
                    'total_energy_kj': session.total_energy,
                    'device_info': {
                        'name': session.device_info.name if session.device_info else None,
                        'address': session.device_info.address if session.device_info else None,
                        'device_type': session.device_info.device_type.value if session.device_info else None
                    } if session.device_info else None
                },
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
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            logger.info(f"Exported session to JSON: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise
            
    def export_to_tcx(self, session: TrainingSession, filename: Optional[str] = None) -> str:
        """Export session to TCX format (simplified)"""
        if not filename:
            timestamp = session.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session.session_id[:8]}_{timestamp}.tcx"
            
        filepath = self.export_dir / filename
        
        try:
            # Simple TCX format (would need more sophisticated implementation for full TCX)
            tcx_content = self._generate_tcx_content(session)
            
            with open(filepath, 'w') as f:
                f.write(tcx_content)
                
            logger.info(f"Exported session to TCX: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export TCX: {e}")
            raise
            
    def _generate_tcx_content(self, session: TrainingSession) -> str:
        """Generate TCX content (simplified)"""
        start_time = session.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_time = session.end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z") if session.end_time else start_time
        
        tcx = f'''<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2.xsd" xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Activities>
    <Activity Sport="Biking">
      <Id>{start_time}</Id>
      <Lap StartTime="{start_time}">
        <TotalTimeSeconds>{(session.end_time - session.start_time).total_seconds() if session.end_time else 0}</TotalTimeSeconds>
        <DistanceMeters>{session.total_distance * 1000}</DistanceMeters>
        <Calories>{int(session.total_energy)}</Calories>
        <Track>
'''
        
        # Add track points
        for power_data in session.power_data:
            timestamp = power_data.timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            tcx += f'''          <Trackpoint>
            <Time>{timestamp}</Time>
            <DistanceMeters>{power_data.distance * 1000 if power_data.distance else 0}</DistanceMeters>
            <Cadence>{power_data.cadence if power_data.cadence else 0}</Cadence>
            <Extensions>
              <TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
                <Speed>{power_data.speed / 3.6 if power_data.speed else 0}</Speed>
                <Watts>{power_data.instantaneous_power}</Watts>
              </TPX>
            </Extensions>
          </Trackpoint>
'''
        
        tcx += '''        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>'''
        
        return tcx
        
    def export_all_formats(self, session: TrainingSession) -> Dict[str, str]:
        """Export session to all available formats"""
        exports = {}
        
        try:
            exports['csv'] = self.export_to_csv(session)
            exports['json'] = self.export_to_json(session)
            exports['tcx'] = self.export_to_tcx(session)
            
            logger.info(f"Exported session to all formats: {list(exports.keys())}")
            return exports
            
        except Exception as e:
            logger.error(f"Failed to export all formats: {e}")
            raise
