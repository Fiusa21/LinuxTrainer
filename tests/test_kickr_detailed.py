"""
Detailed test of the fixed Kickr implementation
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.devices.kickr_trainer import KickrTrainer
from loguru import logger


async def test_kickr_detailed():
    """Test the fixed Kickr implementation with detailed output"""
    print("🧪 Detailed Kickr Test - Power Data Reception")
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
    
    # Add data callback with detailed output
    def on_power_data(power_data):
        print(f"📊 Power: {power_data.instantaneous_power}W")
        if power_data.cadence is not None:
            print(f"   Cadence: {power_data.cadence}RPM")
        if power_data.speed is not None:
            print(f"   Speed: {power_data.speed}km/h")
        if power_data.distance is not None:
            print(f"   Distance: {power_data.distance}km")
        print()
    
    kickr.add_data_callback(on_power_data)
    
    try:
        # Connect
        if await kickr.connect():
            print("✅ Connected successfully!")
            
            # Test connection
            print("\n3. Testing data reception...")
            print("   (Try pedaling your Kickr now - we'll listen for 20 seconds)")
            print("   Press Ctrl+C to stop early")
            
            # Wait for data for 20 seconds
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < 20:
                if kickr.data_count > 0:
                    print(f"✅ Data received! Count: {kickr.data_count}")
                await asyncio.sleep(0.5)
            
            print(f"\n4. Final Results:")
            print(f"   Total data packets received: {kickr.data_count}")
            
            if kickr.data_count == 0:
                print("❌ No data received!")
                print("\nTroubleshooting:")
                print("- Make sure you're pedaling the Kickr")
                print("- Check if another app is connected to the Kickr")
                print("- Try disconnecting and reconnecting")
            else:
                print("✅ Data reception is working!")
            
        else:
            print("❌ Failed to connect!")
    
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
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
        await test_kickr_detailed()
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
