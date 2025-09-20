import asyncio
from bleak import BleakScanner

async def run_scan():
    print("Scanning for Bluetooth LE devices...")
    
    # You can pass service UUIDs directly to discover for filtering, e.g.:
    # CYCLING_POWER_SERVICE_UUID = "00001818-0000-1000-8000-00805f9b34fb" # Example
    # devices = await BleakScanner.discover(service_uuids=[CYCLING_POWER_SERVICE_UUID])
    
    # Or scan all and filter by name/services later
    devices = await BleakScanner.discover()
    
    if not devices:
        print("No devices found.")
        return

    print("Found devices:")
    found_trainers = []
    for device in devices:
        # Example: Filter by name
        if device.name and "kickr" in device.name.lower():
            print(f"  Found Smart Trainer: Address: {device.address}, Name: {device.name}")
            found_trainers.append(device)
        # Or, filter by services if you know their UUIDs
        # if CYCLING_POWER_SERVICE_UUID in device.metadata.get("uuids", []):
        #    print(f"  Found Cycling Power Device: Address: {device.address}, Name: {device.name}")


    if not found_trainers:
        print("No smart trainers found by name filter.")
    else:
        # You'll use the address of one of these trainers for connection next
        print(f"\nReady to connect to one of {len(found_trainers)} trainers.")


async def main():
    await run_scan()

if __name__ == "__main__":
    asyncio.run(main())