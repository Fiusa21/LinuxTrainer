import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('..').absolute()))
from src.devices.kickr_trainer import KickrTrainer
from src.core.models import PowerData
import struct

async def test_flags():
    devices = await KickrTrainer.scan_for_devices(timeout=5)
    if not devices:
        print('No devices found')
        return
    
    kickr = KickrTrainer(devices[0])
    await kickr.connect()
    
    def debug_notification_handler(sender, data):
        print(f"Raw data: {data.hex()}")
        if len(data) >= 4:
            flags = struct.unpack('<H', data[0:2])[0]
            power = struct.unpack('<h', data[2:4])[0]
            print(f"Flags: {flags:016b} (bit 4: wheel={bool(flags & 0x10)}, bit 5: crank={bool(flags & 0x20)})")
            print(f"Power: {power}W")
            print(f"Data length: {len(data)} bytes")
            print("---")
    
    # Override the notification handler temporarily
    kickr._notification_handler = debug_notification_handler
    
    await asyncio.sleep(10)
    await kickr.disconnect()

asyncio.run(test_flags())
