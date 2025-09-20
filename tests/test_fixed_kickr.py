"""
Test the fixed Kickr implementation
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.devices.kickr_trainer import KickrTrainer
from loguru import logger


async def test_fixed_kickr():
    """Test the fixed Kickr implementation"""
    print("🧪 Testing Fixed Wahoo Kickr Implementation")
    print("=" * 60)
    
    # Scan for devices
    print("1. Scanning for Kickr devices...")
    devices = await KickrTrainer.scan_for_devices(timeout=10.0)
    
    if not devices:
        print("❌ No Kickr devices found!")
        return
    
    print(f"✅ Found {len(devices)} Kickr device(s)")
    for device in devices:
        print(f"   - {device.name} ({device.address})")
    
    # Connect to first device
    device_info = devices[0]
    print(f"\n2. Connecting to {device_info.name}...")
    
    kickr = KickrTrainer(device_info)
    
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
            
            # Wait for data for 15 seconds
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < 15:
                if kickr.data_count > 0:
                    print("✅ Data received!")
                    break
                await asyncio.sleep(0.5)
            
            if kickr.data_count == 0:
                print("❌ No data received!")
                print("\nTroubleshooting:")
                print("- Make sure you're pedaling the Kickr")
                print("- Check if another app is connected to the Kickr")
                print("- Try disconnecting and reconnecting")
            
            # Show connection status
            print(f"\n4. Data received: {kickr.data_count} packets")
            
        else:
            print("❌ Failed to connect!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
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
        await test_fixed_kickr()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
