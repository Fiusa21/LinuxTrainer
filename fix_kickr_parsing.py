"""
Fix for Kickr data parsing based on debug output
"""
import struct
from datetime import datetime

def parse_kickr_power_data(data: bytes):
    """Parse Kickr power data correctly based on debug output"""
    print(f"Raw data: {data.hex()}")
    print(f"Length: {len(data)} bytes")
    
    if len(data) < 8:
        print("Insufficient data")
        return None
    
    # Based on the debug output, the data structure appears to be:
    # Bytes 0-1: Flags (0x3400)
    # Bytes 2-3: Instantaneous Power (little-endian, signed)
    # Bytes 4-5: Cadence (little-endian, unsigned) - but this seems wrong
    # Bytes 6-7: Speed (little-endian, unsigned, 0.01 km/h units)
    # Bytes 8-15: Additional data (cumulative values, etc.)
    
    flags = struct.unpack('<H', data[0:2])[0]
    power = struct.unpack('<h', data[2:4])[0]  # signed 16-bit
    
    print(f"Flags: 0x{flags:04x}")
    print(f"Power: {power}W")
    
    # The cadence parsing seems wrong - let's try different approaches
    if len(data) >= 6:
        # Try different cadence parsing
        cadence_raw = struct.unpack('<H', data[4:6])[0]
        print(f"Cadence raw: {cadence_raw}")
        
        # Maybe cadence is in a different position or format
        # Let's check if it's in the later bytes
        if len(data) >= 8:
            cadence_alt1 = struct.unpack('<H', data[6:8])[0]
            print(f"Cadence alt1: {cadence_alt1}")
        
        if len(data) >= 10:
            cadence_alt2 = struct.unpack('<H', data[8:10])[0]
            print(f"Cadence alt2: {cadence_alt2}")
    
    # Speed parsing
    if len(data) >= 8:
        speed_raw = struct.unpack('<H', data[6:8])[0]
        speed = speed_raw / 100.0  # Convert to km/h
        print(f"Speed: {speed}km/h")
    
    return {
        'power': power,
        'flags': flags,
        'raw_data': data.hex()
    }

# Test with the data from debug output
test_data = bytes.fromhex("340000007b5db6cc0000799cb6fd450e")
print("Testing with idle data:")
result1 = parse_kickr_power_data(test_data)
print()

test_data2 = bytes.fromhex("340022003f5eb9cc0000074eb6fd450e")
print("Testing with power data:")
result2 = parse_kickr_power_data(test_data2)
print()

test_data3 = bytes.fromhex("340034000463c2cc0000f882b6fd450e")
print("Testing with higher power data:")
result3 = parse_kickr_power_data(test_data3)
