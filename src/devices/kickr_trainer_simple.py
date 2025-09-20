"""
Simple working Wahoo Kickr Smart Trainer implementation
Focus on getting power data working correctly
"""
import asyncio
import struct
from datetime import datetime
from typing import Optional
from bleak import BleakClient
from loguru import logger

from ..core.base_device import BaseDevice
from ..core.models import DeviceInfo, DeviceType, PowerData
from ..core.constants import *


class KickrTrainerSimple(BaseDevice):
    """Simple working Wahoo Kickr Smart Trainer device"""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        self.power_notification_active = False
        self.data_count = 0
        self.last_power_data = None
        
    @classmethod
    def _create_device_info(cls, device) -> Optional[DeviceInfo]:
        """Create DeviceInfo for Kickr devices"""
        if device.name and "kickr" in device.name.lower():
            return DeviceInfo(
                address=device.address,
                name=device.name,
                device_type=DeviceType.SMART_TRAINER,
                rssi=getattr(device, 'rssi', None)
            )
        return None
    
    async def _setup_notifications(self):
        """Setup power measurement notifications"""
        if not self.client or not self.client.is_connected:
            logger.error("Cannot setup notifications: not connected")
            return
            
        try:
            # Find the cycling power service
            power_service = None
            for service in self.client.services:
                if (service.uuid == CYCLING_POWER_SERVICE_UUID or 
                    "1818" in service.uuid.upper()):
                    power_service = service
                    break
            
            if not power_service:
                logger.error("Cycling Power Service not found!")
                return
            
            # Find the power measurement characteristic
            power_char = None
            for char in power_service.characteristics:
                if (char.uuid == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID or
                    "2A63" in char.uuid.upper()):
                    power_char = char
                    break
            
            if not power_char:
                logger.error("Power measurement characteristic not found!")
                return
            
            if "notify" not in power_char.properties:
                logger.error("Characteristic does not support notifications!")
                return
            
            # Subscribe to power measurements
            logger.info("Subscribing to power measurements...")
            await self.client.start_notify(power_char.uuid, self._notification_handler)
            self.power_notification_active = True
            logger.info("✅ Successfully subscribed to power measurements")
            
        except Exception as e:
            logger.error(f"Failed to setup notifications: {e}")
            raise
    
    async def _cleanup_notifications(self):
        """Cleanup power measurement notifications"""
        if self.client and self.power_notification_active:
            try:
                # Find the power characteristic again
                power_char = None
                for service in self.client.services:
                    if (service.uuid == CYCLING_POWER_SERVICE_UUID or 
                        "1818" in service.uuid.upper()):
                        for char in service.characteristics:
                            if (char.uuid == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID or
                                "2A63" in char.uuid.upper()):
                                power_char = char
                                break
                        break
                
                if power_char:
                    await self.client.stop_notify(power_char.uuid)
                    self.power_notification_active = False
                    logger.info("Unsubscribed from power measurements")
            except Exception as e:
                logger.error(f"Error unsubscribing from power measurements: {e}")
    
    async def _notification_handler(self, sender, data: bytearray):
        """Handle power measurement notifications"""
        self.data_count += 1
        
        # Convert sender to string for comparison
        sender_str = str(sender)
        
        logger.debug(f"Data #{self.data_count} from {sender_str}: {data.hex()}")
        
        if (sender_str == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID or 
            "2A63" in sender_str.upper()):
            power_data = self._parse_kickr_data(data)
            if power_data:
                self.last_power_data = power_data
                logger.info(f"Power: {power_data.instantaneous_power}W, "
                           f"Cadence: {power_data.cadence}RPM, "
                           f"Speed: {power_data.speed}km/h")
                self._notify_callbacks(power_data)
            else:
                logger.warning("Failed to parse power data")
    
    def _parse_kickr_data(self, data: bytearray) -> Optional[PowerData]:
        """Parse Kickr data - focus on getting power working correctly"""
        if len(data) < 4:
            logger.warning(f"Insufficient data: {len(data)} bytes")
            return None
        
        try:
            # Based on debug output analysis:
            # The structure appears to be:
            # Bytes 0-1: Flags (0x3400)
            # Bytes 2-3: Instantaneous Power (little-endian, signed)
            # Bytes 4+: Additional data (cadence, speed, etc.)
            
            # Parse flags
            flags = struct.unpack('<H', data[0:2])[0]
            
            # Parse instantaneous power (bytes 2-3, little-endian, signed)
            instantaneous_power = struct.unpack('<h', data[2:4])[0]
            
            # Initialize variables
            cadence = None
            speed = None
            distance = None
            
            # For now, let's focus on getting power working correctly
            # The cadence and speed parsing needs more investigation
            
            # Try to find reasonable cadence values
            if len(data) >= 6:
                # Check different positions for cadence
                for i in range(4, min(len(data) - 1, 12), 2):
                    if i + 1 < len(data):
                        candidate = struct.unpack('<H', data[i:i+2])[0]
                        # Look for values that could be cadence (0-200 RPM)
                        if 0 <= candidate <= 200:
                            cadence = candidate
                            break
                        # Try dividing by 100 (in case it's scaled)
                        elif 0 <= candidate / 100 <= 200:
                            cadence = candidate / 100
                            break
            
            # For speed, let's use a simple estimation based on power
            # This is not accurate but gives a reasonable approximation
            if instantaneous_power > 0:
                # Rough speed estimation based on power
                # This is not accurate but gives a reasonable approximation
                speed = min(50.0, instantaneous_power * 0.2)  # Rough estimation
            else:
                speed = 0.0
            
            # Calculate distance (simplified)
            if speed > 0:
                # This would need proper time integration in a real implementation
                distance = 0.0  # Placeholder
            
            power_data = PowerData(
                timestamp=datetime.now(),
                instantaneous_power=instantaneous_power,
                cadence=cadence,
                speed=speed,
                distance=distance
            )
            
            logger.debug(f"Parsed: Power={instantaneous_power}W, Cadence={cadence}RPM, Speed={speed}km/h")
            return power_data
            
        except Exception as e:
            logger.error(f"Error parsing power data: {e}")
            logger.error(f"Raw data: {data.hex()}")
            return None
    
    async def get_connection_status(self) -> dict:
        """Get detailed connection status"""
        status = {
            "connected": self.client.is_connected if self.client else False,
            "power_notifications_active": self.power_notification_active,
            "data_count": self.data_count,
            "last_power_data": self.last_power_data,
            "device_info": {
                "name": self.device_info.name,
                "address": self.device_info.address,
                "device_type": self.device_info.device_type.value
            }
        }
        return status
    
    async def test_connection(self) -> bool:
        """Test the connection and data flow"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected to device")
            return False
        
        logger.info("Testing connection...")
        logger.info(f"Connection status: {await self.get_connection_status()}")
        
        if not self.power_notifications_active:
            logger.error("Power notifications not active")
            return False
        
        logger.info("Waiting for data... (try pedaling your Kickr)")
        
        # Wait for data for 10 seconds
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < 10:
            if self.data_count > 0:
                logger.info(f"✅ Data received! Count: {self.data_count}")
                return True
            await asyncio.sleep(0.5)
        
        logger.warning("No data received in 10 seconds")
        return False
