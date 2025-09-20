"""
Tests for data models
"""
import pytest
from datetime import datetime
from src.core.models import PowerData, HeartRateData, TrainingSession, DeviceInfo, DeviceType


def test_power_data_creation():
    """Test PowerData creation"""
    timestamp = datetime.now()
    power_data = PowerData(
        timestamp=timestamp,
        instantaneous_power=200,
        cadence=90,
        speed=25.5
    )
    
    assert power_data.timestamp == timestamp
    assert power_data.instantaneous_power == 200
    assert power_data.cadence == 90
    assert power_data.speed == 25.5


def test_heart_rate_data_creation():
    """Test HeartRateData creation"""
    timestamp = datetime.now()
    hr_data = HeartRateData(
        timestamp=timestamp,
        heart_rate=150,
        rr_intervals=[800, 820, 810]
    )
    
    assert hr_data.timestamp == timestamp
    assert hr_data.heart_rate == 150
    assert hr_data.rr_intervals == [800, 820, 810]


def test_training_session_creation():
    """Test TrainingSession creation"""
    session_id = "test-session-123"
    start_time = datetime.now()
    device_info = DeviceInfo(
        address="AA:BB:CC:DD:EE:FF",
        name="Test Kickr",
        device_type=DeviceType.SMART_TRAINER
    )
    
    session = TrainingSession(
        session_id=session_id,
        start_time=start_time,
        device_info=device_info
    )
    
    assert session.session_id == session_id
    assert session.start_time == start_time
    assert session.device_info == device_info
    assert session.power_data == []
    assert session.heart_rate_data == []
    assert session.total_distance == 0.0
    assert session.total_energy == 0.0


def test_device_info_creation():
    """Test DeviceInfo creation"""
    device_info = DeviceInfo(
        address="AA:BB:CC:DD:EE:FF",
        name="Test Kickr",
        device_type=DeviceType.SMART_TRAINER,
        rssi=-50
    )
    
    assert device_info.address == "AA:BB:CC:DD:EE:FF"
    assert device_info.name == "Test Kickr"
    assert device_info.device_type == DeviceType.SMART_TRAINER
    assert device_info.rssi == -50
