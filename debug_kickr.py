"""
Debug tool for Wahoo Kickr connection and data issues
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bleak import BleakScanner, BleakClient
from src.core.constants import *
from loguru import logger


class KickrDebugger:
    """Debug tool for Kickr connection issues"""
    
    def __init__(self):
        self.device = None
        self.client = None
        self.data_received = False
        
    async def scan_and_connect(self):
        """Scan for Kickr and attempt connection with detailed logging"""
        print("🔍 Scanning for Wahoo Kickr devices...")
        
        # Scan for devices
        devices = await BleakScanner.discover(timeout=10.0)
        kickr_devices = []
        
        print(f"\n📡 Found {len(devices)} BLE devices:")
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device.name or 'Unknown'} ({device.address})")
            if device.name and "kickr" in device.name.lower():
                kickr_devices.append(device)
                print(f"     ⭐ KICKR DETECTED!")
        
        if not kickr_devices:
            print("❌ No Kickr devices found!")
            print("\nTroubleshooting tips:")
            print("1. Make sure your Kickr is powered on")
            print("2. Check if Kickr is in pairing mode")
            print("3. Ensure Bluetooth is enabled")
            print("4. Try moving closer to the device")
            return False
        
        # Use first Kickr device
        self.device = kickr_devices[0]
        print(f"\n🎯 Connecting to: {self.device.name} ({self.device.address})")
        
        try:
            self.client = BleakClient(self.device.address)
            await self.client.connect()
            
            if self.client.is_connected:
                print("✅ Connected successfully!")
                await self.debug_services()
                await self.debug_characteristics()
                await self.debug_notifications()
            else:
                print("❌ Failed to connect")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        
        return True
    
    async def debug_services(self):
        """Debug available services"""
        print("\n🔧 Available Services:")
        print("-" * 50)
        
        for service in self.client.services:
            print(f"Service: {service.uuid}")
            print(f"  Description: {service.description}")
            print(f"  Characteristics: {len(service.characteristics)}")
            
            # Check for cycling power service
            if service.uuid == CYCLING_POWER_SERVICE_UUID:
                print("  ⭐ CYCLING POWER SERVICE FOUND!")
            elif "1818" in service.uuid.upper():
                print("  ⭐ CYCLING POWER SERVICE (alternative UUID)")
            
            print()
    
    async def debug_characteristics(self):
        """Debug characteristics and their properties"""
        print("🔧 Cycling Power Service Characteristics:")
        print("-" * 50)
        
        cycling_power_service = None
        for service in self.client.services:
            if service.uuid == CYCLING_POWER_SERVICE_UUID or "1818" in service.uuid.upper():
                cycling_power_service = service
                break
        
        if not cycling_power_service:
            print("❌ Cycling Power Service not found!")
            print("Available services:")
            for service in self.client.services:
                print(f"  - {service.uuid} ({service.description})")
            return
        
        print(f"Service UUID: {cycling_power_service.uuid}")
        print(f"Service Description: {cycling_power_service.description}")
        print()
        
        for char in cycling_power_service.characteristics:
            print(f"Characteristic: {char.uuid}")
            print(f"  Description: {char.description}")
            print(f"  Properties: {list(char.properties)}")
            
            # Check for power measurement characteristic
            if char.uuid == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID:
                print("  ⭐ POWER MEASUREMENT CHARACTERISTIC FOUND!")
            elif "2A63" in char.uuid.upper():
                print("  ⭐ POWER MEASUREMENT CHARACTERISTIC (alternative UUID)")
            
            # Check if it supports notifications
            if "notify" in char.properties:
                print("  ✅ Supports notifications")
            else:
                print("  ❌ Does NOT support notifications")
            
            print()
    
    async def debug_notifications(self):
        """Debug notification setup and data reception"""
        print("🔧 Testing Notifications:")
        print("-" * 50)
        
        # Find the power measurement characteristic
        power_char = None
        for service in self.client.services:
            if service.uuid == CYCLING_POWER_SERVICE_UUID or "1818" in service.uuid.upper():
                for char in service.characteristics:
                    if char.uuid == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID or "2A63" in char.uuid.upper():
                        power_char = char
                        break
                break
        
        if not power_char:
            print("❌ Power measurement characteristic not found!")
            return
        
        if "notify" not in power_char.properties:
            print("❌ Characteristic does not support notifications!")
            return
        
        print(f"✅ Found power characteristic: {power_char.uuid}")
        print("🔄 Setting up notifications...")
        
        try:
            await self.client.start_notify(power_char.uuid, self.notification_handler)
            print("✅ Notifications enabled!")
            print("⏳ Listening for data for 30 seconds...")
            print("   (Try pedaling your Kickr to generate data)")
            print()
            
            # Listen for 30 seconds
            await asyncio.sleep(30)
            
            if self.data_received:
                print("✅ Data received successfully!")
            else:
                print("❌ No data received!")
                print("\nTroubleshooting tips:")
                print("1. Make sure you're pedaling the Kickr")
                print("2. Check if the Kickr is in the correct mode")
                print("3. Try disconnecting and reconnecting")
                print("4. Check if another app is connected to the Kickr")
            
            await self.client.stop_notify(power_char.uuid)
            print("🛑 Notifications stopped")
            
        except Exception as e:
            print(f"❌ Notification setup failed: {e}")
    
    def notification_handler(self, sender, data):
        """Handle incoming notifications"""
        self.data_received = True
        print(f"📊 Data received from {sender}:")
        print(f"   Raw data: {data.hex()}")
        print(f"   Length: {len(data)} bytes")
        
        if len(data) >= 4:
            try:
                # Parse power data
                power = int.from_bytes(data[2:4], byteorder='little', signed=True)
                print(f"   Power: {power}W")
                
                if len(data) >= 6:
                    cadence = int.from_bytes(data[4:6], byteorder='little', signed=False)
                    print(f"   Cadence: {cadence} RPM")
                
                print()
            except Exception as e:
                print(f"   Error parsing data: {e}")
        else:
            print("   Insufficient data for power measurement")
            print()
    
    async def cleanup(self):
        """Cleanup connection"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("🔌 Disconnected")


async def main():
    """Main debug function"""
    print("🐛 Wahoo Kickr Debug Tool")
    print("=" * 50)
    
    debugger = KickrDebugger()
    
    try:
        success = await debugger.scan_and_connect()
        if success:
            print("\n🎉 Debug session completed!")
        else:
            print("\n❌ Debug session failed!")
    except KeyboardInterrupt:
        print("\n⏹️  Debug session interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        await debugger.cleanup()


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    asyncio.run(main())
