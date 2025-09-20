"""
Simple test script for Kickr connection issues
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.devices.kickr_trainer_improved import KickrTrainerImproved
from loguru import logger


async def test_kickr():
    """Test Kickr connection and data reception"""
    print("🧪 Testing Wahoo Kickr Connection")
    print("=" * 50)
    
    # Scan for devices
    print("1. Scanning for Kickr devices...")
    devices = await KickrTrainerImproved.scan_for_devices(timeout=10.0)
    
    if not devices:
        print("❌ No Kickr devices found!")
        print("\nTroubleshooting:")
        print("- Make sure your Kickr is powered on")
        print("- Check if Kickr is in pairing mode")
        print("- Ensure Bluetooth is enabled")
        print("- Try moving closer to the device")
        return
    
    print(f"✅ Found {len(devices)} Kickr device(s)")
    for device in devices:
        print(f"   - {device.name} ({device.address})")
    
    # Connect to first device
    device_info = devices[0]
    print(f"\n2. Connecting to {device_info.name}...")
    
    kickr = KickrTrainerImproved(device_info)
    
    # Add data callback
    def on_power_data(power_data):
        print(f"📊 Power: {power_data.instantaneous_power}W, "
              f"Cadence: {power_data.cadence}RPM, "
              f"Speed: {power_data.speed}km/h")
    
    kickr.add_data_callback(on_power_data)
    
    try:
        # Connect
        if await kickr.connect():
            print("✅ Connected successfully!")
            
            # Test connection
            print("\n3. Testing data reception...")
            print("   (Try pedaling your Kickr now)")
            
            if await kickr.test_connection():
                print("✅ Data reception working!")
            else:
                print("❌ No data received!")
                print("\nTroubleshooting:")
                print("- Make sure you're pedaling the Kickr")
                print("- Check if another app is connected to the Kickr")
                print("- Try disconnecting and reconnecting")
                print("- Check if the Kickr is in the correct mode")
            
            # Show connection status
            print("\n4. Connection Status:")
            status = await kickr.get_connection_status()
            for key, value in status.items():
                print(f"   {key}: {value}")
            
        else:
            print("❌ Failed to connect!")
            print("\nTroubleshooting:")
            print("- Check if device is already connected elsewhere")
            print("- Try restarting Bluetooth")
            print("- Check device permissions")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check Bluetooth permissions")
        print("- Try running with sudo (Linux)")
        print("- Check if device is in range")
    
    finally:
        # Cleanup
        print("\n5. Cleaning up...")
        await kickr.disconnect()
        print("✅ Disconnected")


async def main():
    """Main test function"""
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    try:
        await test_kickr()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
