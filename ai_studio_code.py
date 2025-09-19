import asyncio
from bleak import BleakScanner

async def run_scan():
    print("Scanning for Bluetooth LE devices...")
    devices = await BleakScanner.discover()
    
    if not devices:
        print("No devices found.")
        return

    print("Found devices:")
    for device in devices:
        print(f"  Address: {device.address}, Name: {device.name}")
        # You might want to print more details for debugging, e.g.:
        # print(f"    Details: {device.details}")
        # print(f"    Metadata: {device.metadata}")

async def main():
    await run_scan()

if __name__ == "__main__":
    asyncio.run(main())