"""
Debug script - mostra TUTTI i record del sonno, anche quelli con timestamp invalidi
Ora include anche export CSV dei record validi
"""
import asyncio
import time
import csv
from datetime import datetime, timezone
from bleak import BleakClient, BleakScanner

CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"

all_records = []
data_complete = False

def calculate_checksum(data):
    checksum = sum(data) & 0xFF
    checksum = (0 - checksum) & 0xFF
    checksum = checksum ^ 0x3A
    return checksum

def notification_handler(sender, data):
    global all_records, data_complete
    
    if len(data) < 3 or data[0] != 0xFF:
        return
    
    command = data[2]
    
    if command == 0x05 and len(data) > 3:
        subcommand = data[3]
        
        if subcommand == 0x03:
            payload_end = data[1]
            idx = 4
            
            while idx < payload_end - 1:
                count = data[idx]
                idx += 1
                
                if idx + 4 > len(data):
                    break
                
                utc = (data[idx] << 24) | (data[idx+1] << 16) | (data[idx+2] << 8) | data[idx+3]
                idx += 4
                
                activity_indices = []
                for i in range(count):
                    if idx < len(data) - 1:
                        activity_indices.append(data[idx])
                        idx += 1
                
                all_records.append({
                    'utc': utc,
                    'count': count,
                    'activity_indices': activity_indices
                })
            
            if len(data) <= 50:
                data_complete = True
        
        elif subcommand == 0xFF:
            data_complete = True

async def main():
    global data_complete
    
    print("🔍 Scanning...")
    devices = await BleakScanner.discover(timeout=8.0)
    cl837 = [d for d in devices if d.name and "CL837" in d.name]
    
    if not cl837:
        print("❌ No CL837 found")
        return
    
    # Auto-select first device or prompt for multiple
    if len(cl837) == 1:
        device = cl837[0]
        print(f"📱 Found: {device.name}")
    else:
        print(f"\nFound {len(cl837)} devices:")
        for i, d in enumerate(cl837, 1):
            print(f"{i}. {d.name} - {d.address}")
        
        while True:
            try:
                choice = int(input("\nSelect device number: "))
                if 1 <= choice <= len(cl837):
                    device = cl837[choice - 1]
                    break
                print(f"Invalid choice. Enter 1-{len(cl837)}")
            except ValueError:
                print("Invalid input. Enter a number.")
    
    async with BleakClient(device) as client:
        print("✅ Connected")
        
        # Find characteristics
        tx_char = None
        rx_char = None
        for service in client.services:
            if service.uuid.lower() == CHILEAF_SERVICE_UUID.lower():
                for char in service.characteristics:
                    if char.uuid.lower() == CHILEAF_TX_UUID.lower():
                        tx_char = char
                    elif char.uuid.lower() == CHILEAF_RX_UUID.lower():
                        rx_char = char
        
        if not tx_char or not rx_char:
            print("❌ Characteristics not found")
            return
        
        await client.start_notify(tx_char, notification_handler)
        await asyncio.sleep(0.2)
        
        # Request sleep data
        print("💤 Requesting sleep data...")
        frame = [0xFF, 0x05, 0x05, 0x02]
        frame.append(calculate_checksum(frame))
        await client.write_gatt_char(rx_char, bytes(frame))
        
        # Wait for data
        timeout = 30
        start = time.time()
        while not data_complete and (time.time() - start) < timeout:
            await asyncio.sleep(0.5)
        
        await client.stop_notify(tx_char)
    
    print(f"\n{'='*80}")
    print(f"TUTTI I RECORD RAW: {len(all_records)}")
    print(f"{'='*80}\n")
    
    current_time = int(time.time())
    MIN_VALID = 1577836800  # 2020-01-01
    
    for i, rec in enumerate(all_records, 1):
        utc = rec['utc']
        count = rec['count']
        duration = count * 5
        
        # Determine validity
        if utc < MIN_VALID:
            status = "❌ TROPPO VECCHIO"
        elif utc > current_time:
            status = "❌ FUTURO"
        elif count == 0:
            status = "❌ VUOTO"
        else:
            status = "✅ VALIDO"
        
        # Try to parse datetime
        try:
            dt = datetime.fromtimestamp(utc, tz=timezone.utc)
            dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            dt_str = "INVALID"
        
        print(f"Record {i:3d}: UTC={utc:12d} | {dt_str} | {duration:4d}min | {status}")
        
        # Show activity for interesting records (December 2025 range)
        if 1733000000 < utc < 1735700000:  # ~Dec 2025
            print(f"           Activity: {rec['activity_indices'][:10]}...")
    
    # Export ALL records to CSV (raw data)
    print(f"\n{'='*80}")
    print("EXPORTING ALL RAW RECORDS TO CSV...")
    print(f"{'='*80}\n")
    
    if all_records:
        # Sort by timestamp
        all_records.sort(key=lambda x: x['utc'])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_sleep_data_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[
                'record_number',
                'utc_timestamp',
                'datetime_utc',
                'duration_minutes',
                'interval_count',
                'deep_sleep_min',
                'light_sleep_min',
                'awake_min',
                'activity_indices'
            ])
            
            writer.writeheader()
            
            for i, rec in enumerate(all_records, 1):
                utc = rec['utc']
                count = rec['count']
                activities = rec['activity_indices']
                
                # Analyze sleep stages (SDK algorithm)
                deep, light, awake = 0, 0, 0
                consecutive_zeros = 0
                
                for action in activities:
                    if action == 0:
                        consecutive_zeros += 1
                    else:
                        if consecutive_zeros >= 3:
                            deep += consecutive_zeros
                        elif consecutive_zeros > 0:
                            light += consecutive_zeros
                        consecutive_zeros = 0
                        
                        if action > 20:
                            awake += 1
                        else:
                            light += 1
                
                # Final zeros
                if consecutive_zeros >= 3:
                    deep += consecutive_zeros
                elif consecutive_zeros > 0:
                    light += consecutive_zeros
                
                writer.writerow({
                    'record_number': i,
                    'utc_timestamp': utc,
                    'datetime_utc': datetime.fromtimestamp(utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_minutes': count * 5,
                    'interval_count': count,
                    'deep_sleep_min': deep * 5,
                    'light_sleep_min': light * 5,
                    'awake_min': awake * 5,
                    'activity_indices': str(activities)
                })
        
        print(f"💾 Exported {len(all_records)} raw records to: {filename}")
        
        # Count valid vs invalid
        valid_count = sum(1 for r in all_records 
                        if r['utc'] >= MIN_VALID and r['utc'] <= current_time and r['count'] > 0)
        invalid_count = len(all_records) - valid_count
        print(f"   ✅ Valid: {valid_count} | ❌ Invalid: {invalid_count}")
    else:
        print("❌ No records to export")

if __name__ == "__main__":
    asyncio.run(main())
