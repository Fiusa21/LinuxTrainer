"""
Data Export Module for LinuxTrainer
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataExporter:
    """Handles data export in various formats"""
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def export_all_formats(self, session) -> Dict[str, str]:
        """Export session data in all supported formats"""
        exports = {}
        
        try:
            # Export JSON
            json_file = self.export_json(session)
            if json_file:
                exports['json'] = str(json_file)
            
            # Export CSV
            csv_file = self.export_csv(session)
            if csv_file:
                exports['csv'] = str(csv_file)
            
            logger.info(f"Exported session data: {exports}")
            return exports
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {}
    
    def export_json(self, session) -> Path:
        """Export session data as JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session.session_id}_{timestamp}.json"
            filepath = self.export_dir / filename
            
            # Prepare session data for export
            session_data = {
                "session_id": session.session_id,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "duration_seconds": session.duration_seconds,
                "data_points": len(session.data_points),
                "data": [
                    {
                        "timestamp": data_point.timestamp.isoformat(),
                        "power": data_point.instantaneous_power,
                        "cadence": data_point.cadence,
                        "speed": data_point.speed
                    }
                    for data_point in session.data_points
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Exported JSON to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return None
    
    def export_csv(self, session) -> Path:
        """Export session data as CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session.session_id}_{timestamp}.csv"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['timestamp', 'power_watts', 'cadence_rpm', 'speed_kmh'])
                
                # Write data points
                for data_point in session.data_points:
                    writer.writerow([
                        data_point.timestamp.isoformat(),
                        data_point.instantaneous_power,
                        data_point.cadence or '',
                        data_point.speed or ''
                    ])
            
            logger.info(f"Exported CSV to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return None
    
    def export_tcx(self, session) -> Path:
        """Export session data as TCX (Training Center XML)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session.session_id}_{timestamp}.tcx"
            filepath = self.export_dir / filename
            
            # Basic TCX structure
            tcx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities>
    <Activity Sport="Biking">
      <Id>{session.start_time.isoformat() if session.start_time else datetime.now().isoformat()}</Id>
      <Lap StartTime="{session.start_time.isoformat() if session.start_time else datetime.now().isoformat()}">
        <TotalTimeSeconds>{session.duration_seconds}</TotalTimeSeconds>
        <DistanceMeters>0</DistanceMeters>
        <MaximumSpeed>0</MaximumSpeed>
        <Calories>0</Calories>
        <AverageHeartRateBpm>
          <Value>0</Value>
        </AverageHeartRateBpm>
        <MaximumHeartRateBpm>
          <Value>0</Value>
        </MaximumHeartRateBpm>
        <Intensity>Active</Intensity>
        <Cadence>0</Cadence>
        <TriggerMethod>Manual</TriggerMethod>
        <Track>
"""
            
            # Add track points
            for data_point in session.data_points:
                tcx_content += f"""          <Trackpoint>
            <Time>{data_point.timestamp.isoformat()}</Time>
            <Cadence>{data_point.cadence or 0}</Cadence>
            <Extensions>
              <TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
                <Speed>{data_point.speed or 0}</Speed>
                <Watts>{data_point.instantaneous_power}</Watts>
              </TPX>
            </Extensions>
          </Trackpoint>
"""
            
            tcx_content += """        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>"""
            
            with open(filepath, 'w') as f:
                f.write(tcx_content)
            
            logger.info(f"Exported TCX to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting TCX: {e}")
            return None
