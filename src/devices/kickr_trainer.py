"""
Wahoo Kickr Smart Trainer Device Driver
"""
import asyncio
import struct
import math
from datetime import datetime
from typing import Optional, List, Callable, Any
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import logging

# Try relative imports first, fall back to absolute
try:
    from ..core.base_device import BaseDevice
    from ..core.models import DeviceInfo, PowerData, DeviceType
    from ..core.constants import (
        CYCLING_POWER_SERVICE_UUID, CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID,
        FITNESS_MACHINE_SERVICE_UUID, INDOOR_BIKE_DATA_CHARACTERISTIC_UUID,
        FITNESS_MACHINE_CONTROL_POINT_CHARACTERISTIC_UUID, FITNESS_MACHINE_FEATURE_CHARACTERISTIC_UUID
    )
except ImportError:
    # Fallback to absolute imports when running as script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.core.base_device import BaseDevice
    from src.core.models import DeviceInfo, PowerData, DeviceType
    from src.core.constants import (
        CYCLING_POWER_SERVICE_UUID, CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID,
        FITNESS_MACHINE_SERVICE_UUID, INDOOR_BIKE_DATA_CHARACTERISTIC_UUID,
        FITNESS_MACHINE_CONTROL_POINT_CHARACTERISTIC_UUID, FITNESS_MACHINE_FEATURE_CHARACTERISTIC_UUID
    )

logger = logging.getLogger(__name__)

class KickrTrainer(BaseDevice):
    """Wahoo Kickr Smart Trainer Device Driver"""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        self.power_notification_active = False
        self.fitness_machine_notification_active = False
        self.data_count = 0
        
        # Power-based speed calculation parameters (default values)
        self.rider_weight_kg = 75.0
        self.bike_weight_kg = 8.0
        self.crr = 0.004  # Coefficient of rolling resistance
        self.cda = 0.25   # Coefficient of drag * frontal area (m^2)
        self.gradient_percent = 0.0  # % gradient
        
        logger.info(f"Rider weight set to {self.rider_weight_kg} kg")
        logger.info(f"Gradient set to {self.gradient_percent}%")

    @classmethod
    async def scan_for_devices(cls, timeout: float = 10.0) -> List[DeviceInfo]:
        """Scan for Kickr devices"""
        logger.info("Scanning for Kickr devices...")
        
        def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            if device.name and "kickr" in device.name.lower():
                logger.info(f"Found Kickr: {device.name} ({device.address})")
        
        devices = await BleakScanner.discover(timeout=timeout, detection_callback=detection_callback)
        
        kickr_devices = []
        for device in devices:
            if device.name and "kickr" in device.name.lower():
                device_info = DeviceInfo(
                    address=device.address,
                    name=device.name,
                    device_type=DeviceType.SMART_TRAINER
                )
                kickr_devices.append(device_info)
        
        return kickr_devices
    
    @classmethod
    def _create_device_info(cls, device: BLEDevice) -> Optional[DeviceInfo]:
        """Create DeviceInfo from discovered device"""
        if device.name and "kickr" in device.name.lower():
            return DeviceInfo(
                address=device.address,
                name=device.name,
                device_type=DeviceType.SMART_TRAINER
            )
        return None
    
    async def _setup_notifications(self):
        """Setup device-specific notifications"""
        try:
            logger.info("Setting up notifications...")
            services = self.client.services
            
            # --- Fitness Machine Service (Primary) ---
            fitness_machine_service = None
            for service in services:
                logger.debug(f"Service: {service.uuid}")
                if service.uuid.lower() == FITNESS_MACHINE_SERVICE_UUID.lower():
                    fitness_machine_service = service
                    logger.info(f"Found Fitness Machine Service: {service.uuid}")
                    break
            
            if fitness_machine_service:
                # Find Indoor Bike Data Characteristic
                indoor_bike_char = None
                control_point_char = None
                feature_char = None
                
                for char in fitness_machine_service.characteristics:
                    logger.debug(f"Fitness Machine Characteristic: {char.uuid}")
                    if char.uuid.lower() == INDOOR_BIKE_DATA_CHARACTERISTIC_UUID.lower():
                        indoor_bike_char = char
                        logger.info(f"Found Indoor Bike Data Characteristic: {char.uuid}")
                    elif char.uuid.lower() == FITNESS_MACHINE_CONTROL_POINT_CHARACTERISTIC_UUID.lower():
                        control_point_char = char
                        logger.info(f"Found Fitness Machine Control Point Characteristic: {char.uuid}")
                    elif char.uuid.lower() == FITNESS_MACHINE_FEATURE_CHARACTERISTIC_UUID.lower():
                        feature_char = char
                        logger.info(f"Found Fitness Machine Feature Characteristic: {char.uuid}")

                if indoor_bike_char:
                    await self.client.start_notify(indoor_bike_char, self._indoor_bike_notification_handler)
                    self.fitness_machine_notification_active = True
                    logger.info("Started Indoor Bike Data notifications successfully")
                else:
                    logger.warning("Indoor Bike Data Characteristic not found")

                # Try to activate the trainer
                if control_point_char:
                    try:
                        # Request Control (Op Code 0x00)
                        await self.client.write_gatt_char(control_point_char, bytearray([0x00]), response=True)
                        logger.info("Sent Request Control to Fitness Machine Control Point")
                        
                        # Start or Resume (Op Code 0x07)
                        await self.client.write_gatt_char(control_point_char, bytearray([0x07]), response=True)
                        logger.info("Sent Start/Resume command to Fitness Machine Control Point")
                    except Exception as e:
                        logger.warning(f"Failed to write to Fitness Machine Control Point: {e}")
                else:
                    logger.warning("Fitness Machine Control Point Characteristic not found")

            else:
                logger.warning("Fitness Machine Service not found")
                
                # Fallback to Cycling Power Service
                power_service = None
                for service in services:
                    if service.uuid.lower() == CYCLING_POWER_SERVICE_UUID.lower():
                        power_service = service
                        logger.info(f"Found Cycling Power Service: {service.uuid}")
                        break
                
                if power_service:
                    power_char = None
                    for char in power_service.characteristics:
                        if char.uuid.lower() == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID.lower():
                            power_char = char
                            logger.info(f"Found Cycling Power Measurement Characteristic: {char.uuid}")
                            break
                    
                    if power_char:
                        await self.client.start_notify(power_char, self._power_notification_handler)
                        self.power_notification_active = True
                        logger.info("Started power notifications successfully")
                    else:
                        logger.warning("Cycling Power Measurement Characteristic not found")
                else:
                    logger.warning("Cycling Power Service not found")

            return True
                
        except Exception as e:
            logger.error(f"Failed to setup notifications: {e}")
            return False
    
    async def _cleanup_notifications(self):
        """Cleanup device-specific notifications"""
        try:
            if self.fitness_machine_notification_active and self.client:
                services = self.client.services
                fitness_machine_service = None
                for service in services:
                    if service.uuid.lower() == FITNESS_MACHINE_SERVICE_UUID.lower():
                        fitness_machine_service = service
                        break
                if fitness_machine_service:
                    indoor_bike_char = None
                    for char in fitness_machine_service.characteristics:
                        if char.uuid.lower() == INDOOR_BIKE_DATA_CHARACTERISTIC_UUID.lower():
                            indoor_bike_char = char
                            break
                    if indoor_bike_char:
                        await self.client.stop_notify(indoor_bike_char)
                        self.fitness_machine_notification_active = False
                        logger.info("Stopped Indoor Bike Data notifications")

            if self.power_notification_active and self.client:
                services = self.client.services
                power_service = None
                for service in services:
                    if service.uuid.lower() == CYCLING_POWER_SERVICE_UUID.lower():
                        power_service = service
                        break
                if power_service:
                    power_char = None
                    for char in power_service.characteristics:
                        if char.uuid.lower() == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID.lower():
                            power_char = char
                            break
                    if power_char:
                        await self.client.stop_notify(power_char)
                        self.power_notification_active = False
                        logger.info("Stopped power notifications")

        except Exception as e:
            logger.error(f"Failed to cleanup notifications: {e}")

    async def _notification_handler(self, sender, data: bytearray):
        """Handle incoming notifications (required by base class)"""
        # This method is required by the base class but we use specific handlers
        # The actual notification handling is done by _indoor_bike_notification_handler
        # and _power_notification_handler
        pass

    def _calculate_power_based_speed(self, power_watts: int, rider_weight_kg: float, bike_weight_kg: float, crr: float, cda: float, gradient_percent: float) -> float:
        """
        Calculate speed based on power output, mimicking virtual cycling apps.
        Formula adapted from various cycling power models.
        """
        if power_watts <= 0:
            return 0.0

        # Constants
        GRAVITY = 9.8067  # m/s^2
        AIR_DENSITY = 1.225  # kg/m^3 (at sea level, 15C)

        # Convert gradient to decimal
        gradient = gradient_percent / 100.0

        # Total mass
        total_mass_kg = rider_weight_kg + bike_weight_kg

        # Forces
        frr = crr * total_mass_kg * GRAVITY * math.cos(math.atan(gradient))
        fg = total_mass_kg * GRAVITY * math.sin(math.atan(gradient))

        # Simple iterative solver for speed (v in m/s)
        v_mps = 0.0  # Initial guess
        tolerance = 0.01  # m/s
        max_iterations = 10
        
        for _ in range(max_iterations):
            fa = 0.5 * cda * AIR_DENSITY * v_mps**2
            total_force = frr + fg + fa
            
            if total_force <= 0:
                if power_watts > 0:
                    v_mps += 0.1
                else:
                    v_mps = 0.0
                break
            
            new_v_mps = power_watts / total_force
            
            if abs(new_v_mps - v_mps) < tolerance:
                v_mps = new_v_mps
                break
            v_mps = new_v_mps
        
        # Convert m/s to km/h
        speed_kmh = v_mps * 3.6
        return max(0.0, speed_kmh)

    def _estimate_cadence(self, power_watts: int) -> Optional[int]:
        """Estimate cadence based on power output (simple model)"""
        if power_watts <= 0:
            return 0
        if power_watts < 50:
            return 60
        elif power_watts < 100:
            return 70
        elif power_watts < 150:
            return 80
        elif power_watts < 200:
            return 85
        else:
            return 90

    async def _indoor_bike_notification_handler(self, sender, data: bytearray):
        """Handle BLE notifications from Indoor Bike Data characteristic."""
        logger.debug(f"Raw Indoor Bike Data from {sender.uuid}: {data.hex()}")
        
        if len(data) < 2:
            logger.warning("Received Indoor Bike data too short.")
            return

        try:
            # Parse Indoor Bike Data according to FTMS specification
            # Flags (2 bytes)
            flags = struct.unpack('<H', data[0:2])[0]
            offset = 2
            
            # Initialize values
            instantaneous_speed = None
            average_speed = None
            instantaneous_cadence = None
            average_cadence = None
            total_distance = None
            resistance_level = None
            instantaneous_power = None
            average_power = None
            total_energy = None
            heart_rate = None
            elapsed_time = None
            
            # Parse based on flags
            if flags & 0x01:  # More Data
                logger.debug("More data flag set")
            
            if flags & 0x02:  # Average Speed present
                if offset + 2 <= len(data):
                    average_speed = struct.unpack('<H', data[offset:offset+2])[0] / 100.0  # 0.01 km/h
                    offset += 2
            
            if flags & 0x04:  # Instantaneous Cadence present
                if offset + 2 <= len(data):
                    # CORRECTED: The Kickr seems to use non-standard field order
                    # Despite setting the cadence flag, bytes 2-3 appear to be speed
                    # and bytes 4-5 appear to be cadence
                    instantaneous_speed = struct.unpack('<H', data[offset:offset+2])[0] / 100.0  # 0.01 km/h
                    offset += 2
            
            if flags & 0x08:  # Average Cadence present
                if offset + 2 <= len(data):
                    average_cadence = struct.unpack('<H', data[offset:offset+2])[0] / 100.0  # 0.01 RPM
                    offset += 2
            
            if flags & 0x10:  # Total Distance present
                if offset + 3 <= len(data):
                    total_distance = struct.unpack('<I', data[offset:offset+3] + b'\x00')[0]  # 1 meter
                    offset += 3
            
            if flags & 0x20:  # Resistance Level present
                if offset + 2 <= len(data):
                    resistance_level = struct.unpack('<h', data[offset:offset+2])[0]  # 1 unit
                    offset += 2
            
            if flags & 0x40:  # Instantaneous Power present
                if offset + 2 <= len(data):
                    # CORRECTED: The Kickr seems to use non-standard field order
                    # Despite setting the power flag, bytes 4-5 appear to be cadence
                    # and bytes 6-7 appear to be power
                    instantaneous_cadence = struct.unpack('<H', data[offset:offset+2])[0]  # 1 RPM
                    offset += 2
            
            if flags & 0x80:  # Average Power present
                if offset + 2 <= len(data):
                    average_power = struct.unpack('<h', data[offset:offset+2])[0]  # 1 watt
                    offset += 2
            
            if flags & 0x100:  # Total Energy present
                if offset + 2 <= len(data):
                    total_energy = struct.unpack('<H', data[offset:offset+2])[0]  # 1 kJ
                    offset += 2
            
            if flags & 0x200:  # Energy per Hour present
                if offset + 2 <= len(data):
                    energy_per_hour = struct.unpack('<H', data[offset:offset+2])[0]  # 1 kJ
                    offset += 2
            
            if flags & 0x400:  # Energy per Minute present
                if offset + 1 <= len(data):
                    energy_per_minute = struct.unpack('<B', data[offset:offset+1])[0]  # 1 kJ
                    offset += 1
            
            if flags & 0x800:  # Heart Rate present
                if offset + 1 <= len(data):
                    heart_rate = struct.unpack('<B', data[offset:offset+1])[0]  # 1 BPM
                    offset += 1
            
            if flags & 0x1000:  # Metabolic Equivalent present
                if offset + 1 <= len(data):
                    met = struct.unpack('<B', data[offset:offset+1])[0] / 10.0  # 0.1
                    offset += 1
            
            if flags & 0x2000:  # Elapsed Time present
                if offset + 2 <= len(data):
                    elapsed_time = struct.unpack('<H', data[offset:offset+2])[0]  # 1 second
                    offset += 2
            
            if flags & 0x4000:  # Remaining Time present
                if offset + 2 <= len(data):
                    remaining_time = struct.unpack('<H', data[offset:offset+2])[0]  # 1 second
                    offset += 2
            
            # CORRECTED: Get power from bytes 6-7 (non-standard Kickr behavior)
            if len(data) >= 8:
                power_from_bytes_6_7 = struct.unpack('<H', data[6:8])[0]
                # Use this power value if it's reasonable (> 0 and < 2000W)
                if 0 < power_from_bytes_6_7 < 2000:
                    instantaneous_power = power_from_bytes_6_7
                else:
                    instantaneous_power = 0
            else:
                instantaneous_power = 0
            
            # Use speed from Indoor Bike Data if available, otherwise calculate from power
            if instantaneous_speed is not None:
                speed = instantaneous_speed
            elif instantaneous_power is not None and instantaneous_power > 0:
                speed = self._calculate_power_based_speed(
                    instantaneous_power,
                    self.rider_weight_kg,
                    self.bike_weight_kg,
                    self.crr,
                    self.cda,
                    self.gradient_percent
                )
            else:
                speed = 0.0
            
            # Use cadence from Indoor Bike Data if available, otherwise estimate
            if instantaneous_cadence is not None:
                # CORRECTED: Apply ÷2 scaling factor for realistic cadence values
                cadence = int(instantaneous_cadence / 2.0)
            elif instantaneous_power is not None and instantaneous_power > 0:
                cadence = self._estimate_cadence(instantaneous_power)
            else:
                cadence = 0

            power_data = PowerData(
                timestamp=datetime.now(),
                instantaneous_power=instantaneous_power if instantaneous_power is not None else 0,
                average_power=average_power,
                cadence=cadence,
                speed=speed,
            )
            
            logger.info(f"Indoor Bike Data: Power={power_data.instantaneous_power}W, Speed={power_data.speed:.1f} km/h, Cadence={power_data.cadence} RPM")
            self.data_count += 1
            self.last_power_data = power_data
            self._notify_callbacks(power_data)

        except struct.error as se:
            logger.error(f"Struct parsing error in _indoor_bike_notification_handler: {se} with data: {data.hex()}")
        except Exception as e:
            logger.error(f"Error parsing Indoor Bike data: {e} with data: {data.hex()}")

    def _power_notification_handler(self, sender, data: bytearray):
        """Handle BLE notifications for cycling power measurement (fallback)."""
        logger.debug(f"Raw power notification from {sender.uuid}: {data.hex()}")
        
        if len(data) < 4:
            logger.warning("Received power data too short.")
            return None

        try:
            flags = struct.unpack('<H', data[0:2])[0]
            instantaneous_power = struct.unpack('<h', data[2:4])[0]

            # Power-based calculations
            speed = self._calculate_power_based_speed(
                instantaneous_power,
                self.rider_weight_kg,
                self.bike_weight_kg,
                self.crr,
                self.cda,
                self.gradient_percent
            )
            cadence = self._estimate_cadence(instantaneous_power)

            power_data = PowerData(
                timestamp=datetime.now(),
                instantaneous_power=instantaneous_power,
                cadence=cadence,
                speed=speed,
            )
            logger.info(f"Power: {power_data.instantaneous_power}W, Speed: {power_data.speed:.1f} km/h, Cadence: {power_data.cadence} RPM")
            self.data_count += 1
            self.last_power_data = power_data
            self._notify_callbacks(power_data)

        except struct.error as se:
            logger.error(f"Struct parsing error in _power_notification_handler: {se} with data: {data.hex()}")
        except Exception as e:
            logger.error(f"Error parsing power data: {e} with data: {data.hex()}")
