"""
Improved Wahoo Kickr Smart Trainer implementation with better debugging
"""
import asyncio
from datetime import datetime
from typing import Optional
from bleak import BleakClient
from loguru import logger

from ..core.base_device import BaseDevice
from ..core.models import DeviceInfo, DeviceType, PowerData
from ..core.constants import *


class KickrTrainerImproved(BaseDevice):
    """Improved Wahoo Kickr Smart Trainer device with better debugging"""
    
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
        """Setup power measurement notifications with better error handling"""
        if not self.client or not self.client.is_connected:
            logger.error("Cannot setup notifications: not connected")
            return
            
        try:
            # First, let's discover all services and characteristics
            logger.info("Discovering services and characteristics...")
            await self._debug_services()
            
            # Find the cycling power service
            power_service = None
            for service in self.client.services:
                if (service.uuid == CYCLING_POWER_SERVICE_UUID or 
                    "1818" in service.uuid.upper()):
                    power_service = service
                    break
            
            if not power_service:
                logger.error("Cycling Power Service not found!")
                await self._list_all_services()
                return
            
            logger.info(f"Found Cycling Power Service: {power_service.uuid}")
            
            # Find the power measurement characteristic
            power_char = None
            for char in power_service.characteristics:
                if (char.uuid == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID or
                    "2A63" in char.uuid.upper()):
                    power_char = char
                    break
            
            if not power_char:
                logger.error("Power measurement characteristic not found!")
                await self._list_characteristics(power_service)
                return
            
            logger.info(f"Found power characteristic: {power_char.uuid}")
            logger.info(f"Characteristic properties: {list(power_char.properties)}")
            
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
    
    async def _debug_services(self):
        """Debug available services"""
        logger.info("Available services:")
        for service in self.client.services:
            logger.info(f"  Service: {service.uuid} - {service.description}")
    
    async def _list_all_services(self):
        """List all available services for debugging"""
        logger.error("All available services:")
        for service in self.client.services:
            logger.error(f"  {service.uuid} - {service.description}")
    
    async def _list_characteristics(self, service):
        """List characteristics for a service"""
        logger.error(f"Characteristics for service {service.uuid}:")
        for char in service.characteristics:
            logger.error(f"  {char.uuid} - {char.description} - {list(char.properties)}")
    
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
    
    async def _notification_handler(self, sender: str, data: bytearray):
        """Handle power measurement notifications with detailed logging"""
        self.data_count += 1
        
        logger.debug(f"Data #{self.data_count} from {sender}: {data.hex()}")
        logger.debug(f"Data length: {len(data)} bytes")
        
        if sender == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID or "2A63" in sender.upper():
            power_data = self._parse_power_data(data)
            if power_data:
                self.last_power_data = power_data
                logger.info(f"Power: {power_data.instantaneous_power}W, "
                           f"Cadence: {power_data.cadence}RPM")
                self._notify_callbacks(power_data)
            else:
                logger.warning("Failed to parse power data")
        else:
            logger.debug(f"Received data from unexpected characteristic: {sender}")
    
    def _parse_power_data(self, data: bytearray) -> Optional[PowerData]:
        """Parse cycling power measurement data with better error handling"""
        if len(data) < 4:
            logger.warning(f"Insufficient data for power measurement: {len(data)} bytes")
            return None
            
        try:
            # Parse instantaneous power (bytes 2-3, little-endian, signed)
            instantaneous_power = int.from_bytes(data[2:4], byteorder='little', signed=True)
            
            # Parse cadence if available (bytes 4-5, little-endian, unsigned)
            cadence = None
            if len(data) >= 6:
                cadence = int.from_bytes(data[4:6], byteorder='little', signed=False)
            
            # Parse speed if available (bytes 6-7, little-endian, unsigned, 0.01 km/h units)
            speed = None
            if len(data) >= 8:
                speed_raw = int.from_bytes(data[6:8], byteorder='little', signed=False)
                speed = speed_raw / 100.0  # Convert to km/h
            
            power_data = PowerData(
                timestamp=datetime.now(),
                instantaneous_power=instantaneous_power,
                cadence=cadence,
                speed=speed
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
        
        if not self.power_notification_active:
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
