"""
Test script to verify power data flow through the system
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.devices.kickr_trainer import KickrTrainer
from loguru import logger

class DataFlowTester:
    def __init__(self):
        self.data_received = False
        self.power_values = []
        
    def on_power_data(self, power_data):
        """Callback to receive power data"""
        self.data_received = True
        self.power_values.append(power_data.instantaneous_power)
        logger.info(f"✅ Data Flow Test - Received: {power_data.instantaneous_power}W")
        logger.info(f"   Timestamp: {power_data.timestamp}")
        logger.info(f"   Cadence: {power_data.cadence}")
        logger.info(f"   Speed: {power_data.speed}")

async def test_data_flow():
    """Test the complete data flow"""
    logger.info("🔄 Testing Power Data Flow...")
    
    # Scan for devices
    devices = await KickrTrainer.scan_for_devices(timeout=10.0)
    
    if not devices:
        logger.error("❌ No Kickr devices found!")
        return
    
    device_info = devices[0]
    logger.info(f"📱 Found: {device_info.name}")
    
    # Create Kickr instance
    kickr = KickrTrainer(device_info)
    
    # Create data flow tester
    tester = DataFlowTester()
    
    # Add callback
    kickr.add_data_callback(tester.on_power_data)
    
    # Connect
    logger.info("�� Connecting to Kickr...")
    success = await kickr.connect()
    
    if success:
        logger.info("✅ Connected! Data flow test starting...")
        logger.info("🚴‍♂️ Start pedaling to see data flow!")
        
        # Listen for 20 seconds
        for i in range(20):
            await asyncio.sleep(1)
            if tester.data_received:
                logger.info(f"📊 Data flow working! Received {len(tester.power_values)} power readings")
                logger.info(f"   Power range: {min(tester.power_values)}W - {max(tester.power_values)}W")
                break
        else:
            logger.warning("⚠️  No power data received in 20 seconds")
        
        await kickr.disconnect()
        logger.info("🔌 Disconnected")
    else:
        logger.error("❌ Failed to connect")

if __name__ == "__main__":
    asyncio.run(test_data_flow())
