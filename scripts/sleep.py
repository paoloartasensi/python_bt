"""
CL837 Sleep Data Download
Connection, UTC sync, and sleep data retrieval
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime, timezone
from bleak import BleakClient, BleakScanner


class CL837SleepMonitor:
    """CL837 Sleep Data Monitor"""
    
    def __init__(self):
        # BLE Connection
        self.client = None
        self.device = None
        self.is_connected = False
        
        # Chileaf Protocol
        self.CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_HEADER = 0xFF
        
        # Commands
        self.CMD_SET_UTC = 0x08
        self.CMD_GET_SLEEP = 0x05
        
        # Sleep data storage
        self.sleep_data = []
        self.sleep_data_complete = False
        
        # Notification characteristics
        self.tx_char = None
        self.rx_char = None

    async def scan_and_connect(self):
        """Scan and connect to CL837"""
        while True:
            print("Searching for CL837 devices...")
            
            devices = await BleakScanner.discover(timeout=8.0)
            
            cl837_devices = []
            for device in devices:
                if device.name and ("CL837" in device.name or "CL831" in device.name):
                    cl837_devices.append(device)
            
            if not cl837_devices:
                print("No CL837 devices found.")
                retry = input("Retry scan? (y/n): ").lower()
                if retry != 'y':
                    return False
                continue
            
            print(f"\nFound {len(cl837_devices)} CL837 devices:")
            for i, device in enumerate(cl837_devices, 1):
                print(f"{i}. {device.name} - {device.address}")
            
            # Device selection
            if len(cl837_devices) == 1:
                target_device = cl837_devices[0]
                print(f"\nAuto-selected: {target_device.name}")
            else:
                while True:
                    try:
                        choice = int(input("\nSelect device number: "))
                        if 1 <= choice <= len(cl837_devices):
                            target_device = cl837_devices[choice - 1]
                            break
                        else:
                            print(f"Invalid choice. Enter 1-{len(cl837_devices)}")
                    except ValueError:
                        print("Invalid input. Enter a number.")
            
            break
        
        try:
            print("\nConnecting...")
            self.client = BleakClient(target_device, timeout=10.0)
            await self.client.connect()
            
            if self.client.is_connected:
                self.is_connected = True
                self.device = target_device
                print(f"✓ Connected to {target_device.name}")
                print(f"  Address: {target_device.address}")
                return True
            else:
                print("✗ Connection failed")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def discover_services(self):
        """Analyze device services and characteristics"""
        print("\nAnalyzing BLE services...")
        
        chileaf_service = None
        tx_characteristic = None
        rx_characteristic = None
        
        for service in self.client.services:
            print(f"Service: {service.uuid}")
            
            if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                chileaf_service = service
                print(f"  ✓ Chileaf service found")
            
            for char in service.characteristics:
                print(f"  Char: {char.uuid} - {char.properties}")
                
                if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                    tx_characteristic = char
                    print(f"    ✓ TX characteristic (notifications)")
                
                if char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                    rx_characteristic = char
                    print(f"    ✓ RX characteristic (write)")
        
        if not tx_characteristic:
            print("✗ Chileaf TX characteristic not found!")
            return False
        
        if not rx_characteristic:
            print("✗ Chileaf RX characteristic not found!")
            return False
        
        if "notify" not in tx_characteristic.properties:
            print("✗ TX characteristic does not support notifications!")
            return False
        
        print("✓ Chileaf service configured correctly")
        self.tx_char = tx_characteristic
        self.rx_char = rx_characteristic
        return True

    def calculate_checksum(self, data):
        """Calculate Chileaf protocol checksum"""
        # Sum all bytes
        checksum = sum(data) & 0xFF
        # Subtract from 0
        checksum = (0 - checksum) & 0xFF
        # XOR with 0x3a
        checksum = checksum ^ 0x3A
        return checksum

    async def send_command(self, command, data=None):
        """Send command to device"""
        if data is None:
            data = []
        
        # Build frame: [HEADER, LENGTH, COMMAND, DATA..., CHECKSUM]
        frame = [self.CHILEAF_HEADER, len(data) + 4, command] + data
        checksum = self.calculate_checksum(frame)
        frame.append(checksum)
        
        frame_bytes = bytes(frame)
        print(f"Sending: {frame_bytes.hex()}")
        
        await self.client.write_gatt_char(self.rx_char, frame_bytes)
        await asyncio.sleep(0.2)  # Small delay for device processing

    async def set_utc_time(self):
        """Set UTC time on device"""
        print("\nSetting UTC time...")
        
        # Get current UTC timestamp
        utc_timestamp = int(time.time())
        print(f"UTC timestamp: {utc_timestamp} ({datetime.utcfromtimestamp(utc_timestamp)})")
        
        # Convert to 4 bytes (big-endian)
        utc_bytes = [
            (utc_timestamp >> 24) & 0xFF,
            (utc_timestamp >> 16) & 0xFF,
            (utc_timestamp >> 8) & 0xFF,
            utc_timestamp & 0xFF
        ]
        
        await self.send_command(self.CMD_SET_UTC, utc_bytes)
        print("✓ UTC time set")

    async def get_sleep_data(self):
        """Request sleep data from device"""
        print("\nRequesting sleep data...")
        
        # Command 0x05, subcmd 0x02 to get sleep data
        await self.send_command(self.CMD_GET_SLEEP, [0x02])
        print("✓ Sleep data request sent")
        
        # Wait for data reception
        print("Waiting for sleep data...")
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while not self.sleep_data_complete and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.5)
        
        if self.sleep_data_complete:
            print("✓ Sleep data received")
            return True
        else:
            print("✗ Timeout waiting for sleep data")
            return False

    def notification_handler(self, sender, data):
        """Handle BLE notifications"""
        try:
            if len(data) < 3:
                return
            
            # Parse frame header
            header = data[0]
            length = data[1]
            command = data[2]
            
            if header != self.CHILEAF_HEADER:
                return
            
            print(f"Received: {data.hex()} (cmd=0x{command:02x})")
            
            # Handle sleep data response (0x05)
            if command == self.CMD_GET_SLEEP:
                self.parse_sleep_data(data)
            
            # Handle UTC set response (0x08)
            elif command == self.CMD_SET_UTC:
                print("  UTC time confirmed by device")
                
        except Exception as e:
            print(f"Notification handler error: {e}")
            traceback.print_exc()

    def parse_sleep_data(self, data):
        """Parse sleep data from device"""
        try:
            if len(data) < 4:
                return
            
            subcommand = data[3]
            
            # 0x03 = sleep data packet
            if subcommand == 0x03:
                print("  Sleep data packet received")
                
                # Parse sleep data structure
                # Format: [count][utc(4 bytes)][activity_indices...]
                payload_start = 4
                payload_end = data[1]  # Length includes checksum position
                
                idx = payload_start
                while idx < payload_end - 1:  # -1 for checksum
                    # Read count of activity indices
                    count = data[idx]
                    idx += 1
                    
                    if idx + 4 > len(data):
                        break
                    
                    # Read UTC timestamp (4 bytes, big-endian)
                    utc = (data[idx] << 24) | (data[idx+1] << 16) | (data[idx+2] << 8) | data[idx+3]
                    idx += 4
                    
                    # Read activity indices
                    activity_indices = []
                    for i in range(count):
                        if idx < len(data) - 1:
                            activity_indices.append(data[idx])
                            idx += 1
                    
                    # Store sleep record
                    sleep_record = {
                        'utc': utc,
                        'datetime': datetime.utcfromtimestamp(utc),
                        'count': count,
                        'activity_indices': activity_indices
                    }
                    self.sleep_data.append(sleep_record)
                    
                    print(f"    UTC: {utc} ({sleep_record['datetime']})")
                    print(f"    Count: {count}")
                    print(f"    Indices: {activity_indices}")
                
                # Check if this is the last packet (small packet size)
                if len(data) <= 50:
                    print("  Last packet detected")
                    self.sleep_data_complete = True
            
            # 0xFF = end of data
            elif subcommand == 0xFF:
                print("  End of sleep data (0xFF)")
                self.sleep_data_complete = True
                
        except Exception as e:
            print(f"Sleep data parsing error: {e}")
            traceback.print_exc()

    def is_valid_timestamp(self, utc_timestamp):
        """
        Validate if a UTC timestamp is reasonable
        
        Returns: (is_valid, reason)
        """
        current_time = int(time.time())
        
        # Device release date: assume CL837 released around 2020
        # 2020-01-01 00:00:00 UTC = 1577836800
        MIN_VALID_TIMESTAMP = 1577836800
        
        # Maximum: current time (can't be in the future)
        MAX_VALID_TIMESTAMP = current_time
        
        # Check if before 2020
        if utc_timestamp < MIN_VALID_TIMESTAMP:
            year = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc).year
            return False, f"too old ({year})"
        
        # Check if in the future
        if utc_timestamp > MAX_VALID_TIMESTAMP:
            future_date = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)
            return False, f"future date ({future_date.strftime('%Y-%m-%d')})"
        
        return True, "valid"

    def filter_valid_records(self):
        """Filter sleep data to keep only valid records"""
        if not self.sleep_data:
            return
        
        valid_records = []
        invalid_records = []
        
        for record in self.sleep_data:
            # Check timestamp validity
            is_valid, reason = self.is_valid_timestamp(record['utc'])
            
            # Also filter out empty records (duration = 0)
            has_data = record['count'] > 0
            
            if is_valid and has_data:
                valid_records.append(record)
            else:
                invalid_records.append({
                    'record': record,
                    'reason': reason if not has_data else f"{reason}, empty"
                })
        
        if invalid_records:
            print(f"\n⚠️  Filtered out {len(invalid_records)} invalid records:")
            for item in invalid_records:
                rec = item['record']
                dt = datetime.fromtimestamp(rec['utc'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                print(f"   - {dt} UTC (timestamp={rec['utc']}) - Reason: {item['reason']}")
        
        self.sleep_data = valid_records
        print(f"\n✅ {len(valid_records)} valid records retained")

    def analyze_sleep_data(self):
        """Analyze and display sleep data"""
        print("\n" + "="*70)
        print("SLEEP DATA ANALYSIS")
        print("="*70)
        
        if not self.sleep_data:
            print("No sleep data available")
            return
        
        # Filter invalid records first
        self.filter_valid_records()
        
        if not self.sleep_data:
            print("\nNo valid sleep data after filtering")
            return
        
        print(f"\nAnalyzing {len(self.sleep_data)} valid records:\n")
        
        for i, record in enumerate(self.sleep_data, 1):
            print(f"Record {i}:")
            print(f"  Start time: {record['datetime']} UTC")
            print(f"  Duration: {record['count'] * 5} minutes ({record['count']} x 5min intervals)")
            
            # Analyze sleep stages - CORRECT ALGORITHM from Android SDK
            deep_sleep = 0
            light_sleep = 0
            awake = 0
            
            indices = record['activity_indices']
            consecutive_zeros = 0
            
            for idx, action in enumerate(indices):
                if action == 0:
                    # Count consecutive zeros
                    consecutive_zeros += 1
                else:
                    # Process accumulated zeros
                    if consecutive_zeros >= 3:
                        # 3+ consecutive zeros = deep sleep
                        deep_sleep += consecutive_zeros
                    elif consecutive_zeros > 0:
                        # Less than 3 zeros = light sleep
                        light_sleep += consecutive_zeros
                    
                    consecutive_zeros = 0  # Reset counter
                    
                    # Process current non-zero value
                    if action > 20:
                        # Awake
                        awake += 1
                    else:  # 1-20
                        # Light sleep
                        light_sleep += 1
            
            # Process remaining zeros at the end
            if consecutive_zeros >= 3:
                deep_sleep += consecutive_zeros
            elif consecutive_zeros > 0:
                light_sleep += consecutive_zeros
            
            print(f"  Deep sleep: {deep_sleep * 5} minutes ({deep_sleep} intervals)")
            print(f"  Light sleep: {light_sleep * 5} minutes ({light_sleep} intervals)")
            print(f"  Awake: {awake * 5} minutes ({awake} intervals)")
            print(f"  Activity indices: {indices}")
            print()
            
            # Store analysis in record for CSV export
            record['deep_sleep_min'] = deep_sleep * 5
            record['light_sleep_min'] = light_sleep * 5
            record['awake_min'] = awake * 5

    def export_to_csv(self, filename=None):
        """Export sleep data to CSV file"""
        if not self.sleep_data:
            print("No data to export")
            return False
        
        if filename is None:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sleep_data_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'record_number',
                    'utc_timestamp',
                    'datetime_utc',
                    'duration_minutes',
                    'interval_count',
                    'deep_sleep_min',
                    'light_sleep_min',
                    'awake_min',
                    'activity_indices'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for i, record in enumerate(self.sleep_data, 1):
                    writer.writerow({
                        'record_number': i,
                        'utc_timestamp': record['utc'],
                        'datetime_utc': record['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'duration_minutes': record['count'] * 5,
                        'interval_count': record['count'],
                        'deep_sleep_min': record.get('deep_sleep_min', 0),
                        'light_sleep_min': record.get('light_sleep_min', 0),
                        'awake_min': record.get('awake_min', 0),
                        'activity_indices': str(record['activity_indices'])
                    })
            
            print(f"\n✓ Data exported to: {filename}")
            print(f"  Total records: {len(self.sleep_data)}")
            return True
            
        except Exception as e:
            print(f"✗ Error exporting to CSV: {e}")
            traceback.print_exc()
            return False

    async def start_monitoring(self):
        """Start sleep data monitoring"""
        print("\nStarting CL837 sleep data download")
        print("=" * 60)
        
        # Enable notifications
        print("Enabling notifications...")
        await self.client.start_notify(self.tx_char, self.notification_handler)
        print("✓ Notifications enabled")
        
        # Small delay for stabilization
        await asyncio.sleep(0.5)
        
        # Set UTC time
        await self.set_utc_time()
        await asyncio.sleep(1)
        
        # Get sleep data
        await self.get_sleep_data()
        
        # Analyze results
        self.analyze_sleep_data()
        
        # Export to CSV
        self.export_to_csv()

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.is_connected:
            try:
                await self.client.stop_notify(self.tx_char)
            except:
                pass
            
            await self.client.disconnect()
            print("\n✓ Disconnected")


async def main():
    """Main function"""
    monitor = CL837SleepMonitor()
    
    print("CL837 SLEEP DATA DOWNLOADER")
    print("=" * 70)
    
    try:
        # Phase 1: Connection
        if not await monitor.scan_and_connect():
            print("Connection failed")
            return
        
        # Phase 2: Service analysis
        if not await monitor.discover_services():
            print("Service discovery failed")
            return
        
        # Phase 3: Download sleep data
        await monitor.start_monitoring()
        
    except Exception as e:
        print(f"General error: {e}")
        traceback.print_exc()
    finally:
        await monitor.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated")
