import asyncio
from bleak import BleakScanner, BleakClient
import platform  # To handle potential OS differences for cycling power

#UUIDS for devices, might need to look up specific UUIDs later
HEART_RATE_SERVICE_UUID = "0000180D-0000-1000-8000-00805f9b34fb"
CYCLING_POWER_SERVICE_UUID = "00001818-0000-1000-8000-00805f9b34fb"
CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID = "00002A63-0000-1000-8000-00805f9b34fb"


def notification_handler(sender, data):
    print(f"[{sender}]: {data.hex()}")

    if sender == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID:
        if len(data) >= 4:
            # Power is typically a SINT16, so two bytes.
            # Byte order for BLE is usually Little-Endian.
            instantaneous_power = int.from_bytes(data[2:4], byteorder='little', signed=True)
            print(f"  Instantaneous Power: {instantaneous_power} Watts")
        else:
            print("  Not enough data for power measurement.")


async def run_scanner_and_connect():
    print("Scanning for Bluetooth LE devices...")

    # Scan for 5 seconds.
    # devices = await BleakScanner.discover(timeout=5.0)
    # The default discover() returns BLEDevice objects. For more detailed ad_data (including RSSI),
    # it's better to use the callback or a different approach if you need RSSI directly from discovery.
    # For now, let's just get the BLEDevice objects and skip RSSI in the initial print.
    devices = await BleakScanner.discover(timeout=5.0)

    if not devices:
        print("No devices found.")
        return

    print("Found devices:")
    target_device = None
    for device in devices:
        # Corrected: Removed .rssi as it's not a direct attribute of BLEDevice
        print(f"  Device: Address: {device.address}, Name: {device.name}")

        if device.name and "kickr" in device.name.lower():
            print(f"  *** Found Smart Trainer: {device.name} at {device.address} ***")
            target_device = device
            break

    if not target_device:
        print("No smart trainer found by name filter (e.g., 'kickr').")
        return

    print(f"\nAttempting to connect to {target_device.name} ({target_device.address})...")

    # On Linux, you might need to specify an adapter
    # adapter = "hci0" # Example, change if you have multiple adapters
    # async with BleakClient(target_device.address, adapter=adapter) as client:

    # For macOS/Windows, the default client is usually fine.
    # On Linux, if you encounter connection issues, you might uncomment the 'adapter' line
    # and use BleakClient(target_device.address, adapter="hci0") or similar.

    try:
        async with BleakClient(target_device.address) as client:
            if client.is_connected:
                print(f"Successfully connected to {target_device.name}!")

                print("\nDiscovering services and characteristics...")
                for service in client.services:
                    print(f"  Service: {service.uuid} ({service.description})")
                    for char in service.characteristics:
                        print(f"    Characteristic: {char.uuid} ({char.description}) - Props: {char.properties}")
                        if "notify" in char.properties:
                            print(f"      (Supports Notifications)")

                            if char.uuid == CYCLING_POWER_MEASUREMENT_CHARACTERISTIC_UUID:
                                print(f"\nSubscribing to Cycling Power Measurement ({char.uuid})...")
                                try:
                                    await client.start_notify(char.uuid, notification_handler)
                                    print("Subscribed successfully! Waiting for data...")
                                    # Listen for a longer duration for real usage
                                    await asyncio.sleep(120)  # Listen for 2 minutes

                                    print("\nUnsubscribing from Cycling Power Measurement...")
                                    await client.stop_notify(char.uuid)
                                except Exception as e:
                                    print(f"Error subscribing or during notification: {e}")

                print("Disconnecting...")
            else:
                print(f"Failed to connect to {target_device.name}.")
    except Exception as e:
        print(f"An error occurred during connection or communication: {e}")
        # On Linux, common errors here could be 'bluetooth.btcommon.BluetoothError: Connection refused'
        # which might mean the device is already connected elsewhere, or permissions.


async def main():
    await run_scanner_and_connect()


if __name__ == "__main__":
    # Small platform specific adjustment for asyncio on Windows if you were to run it there.
    # Not strictly necessary for Linux/macOS but good practice.
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())