"""
Simple test to see what's happening with the data
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.devices.kickr_trainer import KickrTrainer
from loguru import logger


async def test_kickr_simple():
    """Simple test to see what's happening"""
    print("🧪 Simple Kickr Test")
    print("=" * 40)
    
    # Scan for devices
    devices = await KickrTrainer.scan_for_devices(timeout=10.0)
    
    if not devices:
        print("❌ No Kickr devices found!")
        return
    
    device_info = devices[0]
    print(f"Connecting to {device_info.name}...")
    
    kickr = KickrTrainer(device_info)
    
    # Add data callback
    def on_power_data(power_data):
        print(f"📊 Power: {power_data.instantaneous_power}W")
        if power_data.cadence is not None:
            print(f"   Cadence: {power_data.cadence}RPM")
        print()
    
    kickr.add_data_callback(on_power_data)
    
    try:
        if await kickr.connect():
            print("✅ Connected!")
            
            print("Listening for 10 seconds...")
            await asyncio.sleep(10)
            
            print(f"Data count: {kickr.data_count}")
            
        else:
            print("❌ Failed to connect!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await kickr.disconnect()
        print("Disconnected")


async def main():
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    try:
        await test_kickr_simple()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
