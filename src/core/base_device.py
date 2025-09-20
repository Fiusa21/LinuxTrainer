"""
Base class for BLE device connections
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, List
from bleak import BleakClient, BleakScanner
from loguru import logger

from .models import DeviceInfo, ConnectionStatus, DeviceType


class BaseDevice(ABC):
    """Base class for all BLE devices"""
    
    def __init__(self, device_info: DeviceInfo):
        self.device_info = device_info
        self.client: Optional[BleakClient] = None
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.data_callbacks: List[Callable] = []
        
    def add_data_callback(self, callback: Callable):
        """Add a callback function to be called when data is received"""
        self.data_callbacks.append(callback)
        
    def remove_data_callback(self, callback: Callable):
        """Remove a data callback"""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
            
    def _notify_callbacks(self, data: Any):
        """Notify all registered callbacks with new data"""
        for callback in self.data_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in data callback: {e}")
    
    async def connect(self) -> bool:
        """Connect to the device"""
        if self.connection_status == ConnectionStatus.CONNECTED:
            return True
            
        self.connection_status = ConnectionStatus.CONNECTING
        logger.info(f"Connecting to {self.device_info.name} ({self.device_info.address})")
        
        try:
            self.client = BleakClient(self.device_info.address)
            await self.client.connect()
            
            if self.client.is_connected:
                self.connection_status = ConnectionStatus.CONNECTED
                await self._setup_notifications()
                logger.info(f"Successfully connected to {self.device_info.name}")
                return True
            else:
                self.connection_status = ConnectionStatus.ERROR
                logger.error(f"Failed to connect to {self.device_info.name}")
                return False
                
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            logger.error(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the device"""
        if self.client and self.client.is_connected:
            await self._cleanup_notifications()
            await self.client.disconnect()
            self.connection_status = ConnectionStatus.DISCONNECTED
            logger.info(f"Disconnected from {self.device_info.name}")
    
    @abstractmethod
    async def _setup_notifications(self):
        """Setup device-specific notifications"""
        pass
    
    @abstractmethod
    async def _cleanup_notifications(self):
        """Cleanup device-specific notifications"""
        pass
    
    @abstractmethod
    async def _notification_handler(self, sender: str, data: bytearray):
        """Handle incoming notifications"""
        pass
    
    @classmethod
    async def scan_for_devices(cls, timeout: float = 5.0) -> List[DeviceInfo]:
        """Scan for compatible devices"""
        logger.info("Scanning for BLE devices...")
        devices = await BleakScanner.discover(timeout=timeout)
        
        found_devices = []
        for device in devices:
            device_info = cls._create_device_info(device)
            if device_info:
                found_devices.append(device_info)
                
        logger.info(f"Found {len(found_devices)} compatible devices")
        return found_devices
    
    @classmethod
    @abstractmethod
    def _create_device_info(cls, device) -> Optional[DeviceInfo]:
        """Create DeviceInfo from discovered device"""
        pass
