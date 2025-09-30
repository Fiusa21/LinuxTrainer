"""
Data models for training sessions and device data
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DeviceType(Enum):
    SMART_TRAINER = "smart_trainer"
    HEART_RATE_MONITOR = "heart_rate_monitor"
    POWER_METER = "power_meter"
    SPEED_CADENCE_SENSOR = "speed_cadence_sensor"


class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class DeviceInfo:
    """Information about a BLE device"""
    address: str
    name: Optional[str]
    device_type: DeviceType
    rssi: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None


@dataclass
class PowerData:
    """Cycling power measurement data"""
    timestamp: datetime
    instantaneous_power: int  # Watts
    average_power: Optional[int] = None
    cadence: Optional[int] = None  # RPM
    speed: Optional[float] = None  # km/h
    distance: Optional[float] = None  # meters


@dataclass
class HeartRateData:
    """Heart rate measurement data"""
    timestamp: datetime
    heart_rate: int  # BPM
    rr_intervals: Optional[List[int]] = None  # milliseconds


@dataclass
class TrainingSession:
    """Complete training session data"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    device_info: Optional[DeviceInfo] = None
    power_data: List[PowerData] = None
    heart_rate_data: List[HeartRateData] = None
    total_distance: float = 0.0
    total_energy: float = 0.0  # kJ
    avg_power: float = 0.0
    max_power: int = 0
    power_count: int = 0
    
    def __post_init__(self):
        if self.power_data is None:
            self.power_data = []
        if self.heart_rate_data is None:
            self.heart_rate_data = []
    
    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        else:
            return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def data_points(self) -> List[PowerData]:
        """Get all power data points"""
        return self.power_data
