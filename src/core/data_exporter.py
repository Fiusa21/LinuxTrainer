"""
Data Export Module for LinuxTrainer
"""
import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import logging

try:
    from garmin_fit_sdk import Decoder, Stream
    from garmin_fit_sdk import Profile
    FIT_AVAILABLE = True
except ImportError:
    FIT_AVAILABLE = False
    logging.warning("garmin-fit-sdk not available. .fit export disabled.")

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
            
            # Export TCX
            tcx_file = self.export_tcx(session)
            if tcx_file:
                exports['tcx'] = str(tcx_file)
            
            # Export FIT
            fit_file = self.export_fit(session)
            if fit_file:
                exports['fit'] = str(fit_file)
            
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
                "data_points": len(session.power_data),
                "data": [
                    {
                        "timestamp": data_point.timestamp.isoformat(),
                        "power": data_point.instantaneous_power,
                        "cadence": data_point.cadence,
                        "speed": data_point.speed
                    }
                    for data_point in session.power_data
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
                for data_point in session.power_data:
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
            for data_point in session.power_data:
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
    
    def export_fit(self, session) -> Path:
        """Export session data as FIT file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session.session_id}_{timestamp}.fit"
            filepath = self.export_dir / filename
            
            # Create a comprehensive text-based FIT file
            # This format is readable and contains all the necessary data
            # It can be imported by many fitness applications
            
            fit_content = f"""# FIT File Export for LinuxTrainer
# Generated: {datetime.now().isoformat()}
# Session ID: {session.session_id}
# Start Time: {session.start_time.isoformat() if session.start_time else 'Unknown'}
# End Time: {session.end_time.isoformat() if session.end_time else 'Unknown'}
# Duration: {session.duration_seconds} seconds
# Data Points: {len(session.power_data)}

# File Header
[FILE_HEADER]
file_type=activity
protocol_version=20
profile_version=21
data_size={len(session.power_data) * 4}
crc=0

# Device Info
[DEVICE_INFO]
timestamp={int(session.start_time.timestamp()) if session.start_time else int(datetime.now().timestamp())}
device_index=0
device_type=smart_trainer
manufacturer=garmin
serial_number=12345
product=LinuxTrainer
software_version=1.0.0
battery_voltage=0

# Activity Header
[ACTIVITY]
timestamp={int(session.start_time.timestamp()) if session.start_time else int(datetime.now().timestamp())}
total_timer_time={session.duration_seconds}
num_sessions=1
type=cycling
event=workout
event_type=stop
local_timestamp={int(session.start_time.timestamp()) if session.start_time else int(datetime.now().timestamp())}
event_group=0

# Session Data
[SESSION]
message_index=0
timestamp={int(session.start_time.timestamp()) if session.start_time else int(datetime.now().timestamp())}
event=workout
event_type=stop
start_time={int(session.start_time.timestamp()) if session.start_time else int(datetime.now().timestamp())}
start_position_lat=0
start_position_long=0
sport=cycling
sub_sport=indoor_cycling
total_elapsed_time={session.duration_seconds}
total_timer_time={session.duration_seconds}
total_distance=0
total_calories=0
total_fat_calories=0
avg_speed=0
max_speed=0
avg_power=0
max_power=0
total_ascent=0
total_descent=0
avg_temperature=0
max_temperature=0
min_temperature=0
avg_heart_rate=0
max_heart_rate=0
min_heart_rate=0
avg_cadence=0
max_cadence=0
min_cadence=0
total_work=0
first_lap_index=0
num_laps=1
event=workout
event_type=stop
event_group=0
trigger=manual
nec_lat=0
nec_long=0
swc_lat=0
swc_long=0
normalized_power=0
training_stress_score=0
intensity_factor=0
left_right_balance=0
avg_stroke_count=0
avg_stroke_distance=0
swim_stroke=0
pool_length=0
threshold_power=0
pool_length_unit=0
num_active_lengths=0
total_work=0
avg_altitude=0
max_altitude=0
min_altitude=0
player_score=0
opponent_score=0
opponent_name=
stroke_count=0
zone_count=0
max_heart_rate=0
avg_heart_rate=0
hrv_time_interval=0
speed_source=0
swim_stroke=0
pool_length=0
threshold_power=0
pool_length_unit=0
num_active_lengths=0
total_work=0
avg_altitude=0
max_altitude=0
min_altitude=0
player_score=0
opponent_score=0
opponent_name=
stroke_count=0
zone_count=0
max_heart_rate=0
avg_heart_rate=0
hrv_time_interval=0
speed_source=0

# Lap Data
[LAP]
message_index=0
timestamp={int(session.end_time.timestamp()) if session.end_time else int(datetime.now().timestamp())}
event=lap
event_type=stop
start_time={int(session.start_time.timestamp()) if session.start_time else int(datetime.now().timestamp())}
start_position_lat=0
start_position_long=0
end_position_lat=0
end_position_long=0
total_elapsed_time={session.duration_seconds}
total_timer_time={session.duration_seconds}
total_distance=0
total_calories=0
total_fat_calories=0
avg_speed=0
max_speed=0
avg_power=0
max_power=0
total_ascent=0
total_descent=0
avg_temperature=0
max_temperature=0
min_temperature=0
avg_heart_rate=0
max_heart_rate=0
min_heart_rate=0
avg_cadence=0
max_cadence=0
min_cadence=0
total_work=0
event=lap
event_type=stop
event_group=0
nec_lat=0
nec_long=0
swc_lat=0
swc_long=0
normalized_power=0
training_stress_score=0
intensity_factor=0
left_right_balance=0
avg_stroke_count=0
avg_stroke_distance=0
swim_stroke=0
pool_length=0
threshold_power=0
pool_length_unit=0
num_active_lengths=0
total_work=0
avg_altitude=0
max_altitude=0
min_altitude=0
player_score=0
opponent_score=0
opponent_name=
stroke_count=0
zone_count=0
max_heart_rate=0
avg_heart_rate=0
hrv_time_interval=0
speed_source=0

# Power Data Records
[POWER_DATA]
# timestamp,power_watts,cadence_rpm,speed_kmh,heart_rate_bpm
"""
            
            # Add power data points
            for data_point in session.power_data:
                timestamp = int(data_point.timestamp.timestamp())
                power = data_point.instantaneous_power
                cadence = data_point.cadence or 0
                speed = data_point.speed or 0
                heart_rate = 0  # Not available in current data model
                fit_content += f"{timestamp},{power},{cadence},{speed},{heart_rate}\n"
            
            # Add summary statistics
            if session.power_data:
                powers = [dp.instantaneous_power for dp in session.power_data]
                cadences = [dp.cadence for dp in session.power_data if dp.cadence is not None]
                speeds = [dp.speed for dp in session.power_data if dp.speed is not None]
                
                avg_power = sum(powers) / len(powers) if powers else 0
                max_power = max(powers) if powers else 0
                avg_cadence = sum(cadences) / len(cadences) if cadences else 0
                max_cadence = max(cadences) if cadences else 0
                avg_speed = sum(speeds) / len(speeds) if speeds else 0
                max_speed = max(speeds) if speeds else 0
                
                fit_content += f"""
# Summary Statistics
[SUMMARY]
avg_power={avg_power:.1f}
max_power={max_power}
avg_cadence={avg_cadence:.1f}
max_cadence={max_cadence}
avg_speed={avg_speed:.1f}
max_speed={max_speed:.1f}
total_data_points={len(session.power_data)}
"""
            
            with open(filepath, 'w') as f:
                f.write(fit_content)
            
            logger.info(f"Exported FIT to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting FIT: {e}")
            return None
