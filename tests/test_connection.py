"""
Test script to debug Kickr connection
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.devices.kickr_trainer import KickrTrainer
from loguru import logger

async def test_connection():
    """Test Kickr connection and data reception"""
    logger.info("Starting Kickr connection test...")
    
    # Scan for devices
    devices = await KickrTrainer.scan_for_devices(timeout=10.0)
    
    if not devices:
        logger.error("No Kickr devices found!")
        return
    
    logger.info(f"Found {len(devices)} Kickr device(s)")
    for device in devices:
        logger.info(f"  - {device.name} ({device.address})")
    
    # Connect to first device
    device_info = devices[0]
    kickr = KickrTrainer(device_info)
    
    # Add data callback
    def on_data(power_data):
        logger.info(f"Received data: {power_data.instantaneous_power}W")
    
    kickr.add_data_callback(on_data)
    
    # Connect
    logger.info("Connecting to Kickr...")
    success = await kickr.connect()
    
    if success:
        logger.info("Connected successfully! Listening for data...")
        logger.info("Start pedaling on your Kickr to see data!")
        
        # Listen for 30 seconds
        await asyncio.sleep(30)
        
        logger.info("Disconnecting...")
        await kickr.disconnect()
    else:
        logger.error("Failed to connect to Kickr")

if __name__ == "__main__":
    asyncio.run(test_connection())
