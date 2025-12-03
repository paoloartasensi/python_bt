"""
CL837 Heart Rate History Download
Connection, UTC sync, and HR data retrieval

Protocol based on decompiled Chileaf Android SDK:
- Command 0x21: Get HR history records (timestamps)
- Command 0x22: Get HR data for specific timestamp
- Command 0x23: End marker (0xFFFFFFFF)

Checksum formula (from FitnessManager.java):
  checksum = ((0 - sum(packet)) ^ 0x3A) & 0xFF
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime, timedelta
from bleak import BleakClient, BleakScanner


class CL837HRMonitor:
    """CL837 Heart Rate History Monitor"""
    
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
        self.CMD_GET_HR_RECORD = 0x21  # Get HR records (timestamps)
        self.CMD_GET_HR_DATA = 0x22    # Get HR data for specific timestamp
        self.CMD_HR_DATA_END = 0x23    # End marker for HR data download
        
        # HR data storage
        self.hr_records = []
        self.hr_data = []
        self.hr_records_complete = False
        self.hr_data_complete = False
        
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
        """Discover and setup BLE services"""
        try:
            services = self.client.services
            
            # Find Chileaf service
            chileaf_service = None
            for service in services:
                if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                    chileaf_service = service
                    print(f"\n✓ Found Chileaf Service: {service.uuid}")
                    break
            
            if not chileaf_service:
                print("✗ Chileaf service not found")
                return False
            
            # Find TX and RX characteristics
            for char in chileaf_service.characteristics:
                if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                    self.tx_char = char
                    print(f"  ✓ TX Char (notify): {char.uuid}")
                elif char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                    self.rx_char = char
                    print(f"  ✓ RX Char (write): {char.uuid}")
            
            if not self.tx_char or not self.rx_char:
                print("✗ Required characteristics not found")
                return False
            
            # Enable notifications on TX characteristic
            await self.client.start_notify(self.tx_char, self.notification_handler)
            print("  ✓ Notifications enabled")
            
            return True
            
        except Exception as e:
            print(f"Service discovery error: {e}")
            traceback.print_exc()
            return False

    def notification_handler(self, sender, data):
        """Handle incoming notifications"""
        try:
            if len(data) < 4:
                return
            
            header = data[0]
            length = data[1]
            cmd = data[2]
            
            if header != self.CHILEAF_HEADER:
                return
            
            # Response to GET_HR_RECORD (0x21)
            if cmd == self.CMD_GET_HR_RECORD:
                self.parse_hr_record_response(data)
            
            # Response to GET_HR_DATA (0x22) - accumulate packets
            elif cmd == self.CMD_GET_HR_DATA:
                self.parse_hr_data_response(data)
            
            # Response to HR_DATA_END (0x23) - end marker, download complete
            elif cmd == self.CMD_HR_DATA_END:
                self.hr_data_complete = True
                print(f"  ✓ HR data complete ({len(self.hr_data)} values)")
            
            # Response to SET_UTC (0x08)
            elif cmd == self.CMD_SET_UTC:
                print("  ✓ UTC time synchronized")
            # Ignore other commands (0x0C=accel, 0x38=temp, 0x15=sport, 0x75=health)
                
        except Exception as e:
            print(f"Notification handler error: {e}")
            traceback.print_exc()

    def parse_hr_record_response(self, data):
        """Parse HR record response - contains multiple 4-byte UTC timestamps"""
        try:
            if len(data) < 4:
                return
            
            # Check if this is the end marker packet (short packet with 0xFFFFFFFF)
            if len(data) == 8 and data[3:7] == bytes([0xFF, 0xFF, 0xFF, 0xFF]):
                self.hr_records_complete = True
                print(f"\n✓ HR records download complete ({len(self.hr_records)} records)")
                return
            
            # Parse multiple timestamps from packet
            # Format: [header(1), length(1), cmd(1), utc1(4), utc2(4), ..., checksum(1)]
            payload = data[3:-1]  # Remove header, length, cmd, and checksum
            
            # Each timestamp is 4 bytes (big-endian)
            num_timestamps = len(payload) // 4
            
            for i in range(num_timestamps):
                offset = i * 4
                if offset + 4 <= len(payload):
                    utc_bytes = payload[offset:offset+4]
                    utc_timestamp = struct.unpack('>I', bytes(utc_bytes))[0]  # Big-endian
                    
                    # Check for end marker within packet
                    if utc_timestamp == 0xFFFFFFFF:
                        self.hr_records_complete = True
                        print(f"\n✓ HR records download complete ({len(self.hr_records)} records)")
                        return
                    
                    # Convert to datetime (local time)
                    dt = datetime.fromtimestamp(utc_timestamp)
                    
                    self.hr_records.append({
                        'utc': utc_timestamp,
                        'datetime': dt.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    print(f"  HR Record #{len(self.hr_records)}: {dt.strftime('%Y-%m-%d %H:%M:%S')} (UTC: {utc_timestamp})")
                
        except Exception as e:
            print(f"Parse HR record error: {e}")
            traceback.print_exc()

    def parse_hr_data_response(self, data):
        """Parse HR data response - contains multiple HR values per packet.
        
        Format: [header(1), length(1), cmd(1), seq(4), hr1, hr2, ..., checksum(1)]
        
        SDK accumulates 0x22 packets, then processes all when 0x23 (end marker) arrives.
        Each packet contains ~128 HR values (1 per minute).
        """
        try:
            if len(data) < 8:
                return
            
            # Parse sequence number (4 bytes, big-endian) at positions 3-6
            sequence = struct.unpack('>I', bytes(data[3:7]))[0]
            
            # HR values start at position 7, end before checksum
            hr_values = data[7:-1]  # Exclude header(3), seq(4), and checksum(1)
            
            # Get current session UTC (set by get_hr_data)
            session_utc = getattr(self, '_current_session_utc', 0)
            
            # Store all HR values from this packet
            packet_hr_count = 0
            for hr_value in hr_values:
                if hr_value > 0 and hr_value < 250:  # Valid HR range
                    self.hr_data.append({
                        'sequence': sequence,
                        'packet_index': packet_hr_count,
                        'hr_bpm': hr_value,
                        'session_utc': session_utc,  # Tag with session
                    })
                    packet_hr_count += 1
            
            # Update progress (print every 1000 values)
            if packet_hr_count > 0:
                total_hr = len(self.hr_data)
                if total_hr % 1000 == 0:
                    print(f"    ... {total_hr} HR values...")
                
        except Exception as e:
            print(f"Parse HR data error: {e}")
            traceback.print_exc()

    def checksum(self, data):
        """Calculate checksum used by Chileaf protocol.
        
        From decompiled Android SDK (FitnessManager.java line 174):
        protected byte checkSum(final byte[] data) {
            int result = 0;
            for (byte item : data) {
                result += item;
            }
            return (byte) (((-result) ^ 58) & 255);
        }
        
        Formula: ((0 - sum(data)) ^ 0x3A) & 0xFF
        """
        result = 0
        for byte in data:
            result += (byte & 0xFF)
        return ((-result) ^ 0x3A) & 0xFF

    async def send_command(self, cmd, params=None):
        """Send command to device"""
        try:
            if params is None:
                params = []
            
            # Build packet: [header, length, cmd, params..., checksum]
            length = 4 + len(params)
            packet = [self.CHILEAF_HEADER, length, cmd] + params
            
            # Calculate and append checksum
            checksum = self.checksum(packet)
            packet.append(checksum)
            
            # Send command
            await self.client.write_gatt_char(self.rx_char, bytes(packet), response=True)
            
            return True
            
        except Exception as e:
            print(f"Send command error: {e}")
            return False

    async def set_utc_time(self):
        """Set device UTC time"""
        try:
            print("\nSynchronizing UTC time...")
            
            # Get current UTC timestamp
            utc_timestamp = int(time.time())
            
            # Convert to 4 bytes (big-endian)
            utc_bytes = [
                (utc_timestamp >> 24) & 0xFF,
                (utc_timestamp >> 16) & 0xFF,
                (utc_timestamp >> 8) & 0xFF,
                utc_timestamp & 0xFF
            ]
            
            await self.send_command(self.CMD_SET_UTC, utc_bytes)
            await asyncio.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"Set UTC error: {e}")
            return False

    async def get_hr_records(self):
        """Request HR record list"""
        try:
            print("\nRequesting HR records...")
            self.hr_records = []
            self.hr_records_complete = False
            
            await self.send_command(self.CMD_GET_HR_RECORD, [0x00])
            
            # Wait for records to download (max 30 seconds)
            timeout = 30
            start_time = time.time()
            
            while not self.hr_records_complete:
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("✗ Timeout waiting for HR records")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Get HR records error: {e}")
            return False

    async def get_hr_data(self, utc_timestamp, session_name=""):
        """Request HR data for specific timestamp"""
        try:
            dt = datetime.fromtimestamp(utc_timestamp)
            print(f"\nDownloading HR data for {dt.strftime('%Y-%m-%d %H:%M:%S')}...")
            # Don't reset self.hr_data here - accumulate across sessions
            self.hr_data_complete = False
            self._current_session_utc = utc_timestamp  # Track current session for tagging
            
            # Convert timestamp to bytes
            utc_bytes = [
                0x01,  # Request type (1 = get data)
                (utc_timestamp >> 24) & 0xFF,
                (utc_timestamp >> 16) & 0xFF,
                (utc_timestamp >> 8) & 0xFF,
                utc_timestamp & 0xFF
            ]
            
            await self.send_command(self.CMD_GET_HR_DATA, utc_bytes)
            
            # Wait for data to download - SDK sends 0x23 when complete
            timeout = 60  # Max 60 seconds for large datasets
            start_time = time.time()
            
            while not self.hr_data_complete:
                await asyncio.sleep(0.1)
                
                elapsed = time.time() - start_time
                
                # Progress every 5 seconds
                if int(elapsed) % 5 == 0 and int(elapsed) > 0 and len(self.hr_data) > 0:
                    print(f"    ... {len(self.hr_data)} HR values downloaded")
                
                # Hard timeout
                if elapsed > timeout:
                    if len(self.hr_data) > 0:
                        print(f"  ⚠ Timeout but got {len(self.hr_data)} values")
                        return True
                    else:
                        print("  ✗ Timeout - no data received")
                        return False
            
            return True
            
        except Exception as e:
            print(f"Get HR data error: {e}")
            return False

    def export_to_csv(self, selected_date, selected_records):
        """Export HR data to CSV file for selected day"""
        try:
            if not self.hr_data:
                print("\nNo HR data to export")
                return
            
            # Create filename with date
            date_str = selected_date.strftime("%Y%m%d")
            filename = f"hr_history_{date_str}.csv"
            
            # Calculate time offset per HR value (typically 1 minute intervals)
            # Based on typical HR monitoring: ~128 values per packet, multiple packets per session
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow([
                    'datetime',
                    'hr_bpm',
                    'session_start',
                    'minute_offset'
                ])
                
                # Sort data by session and index
                sorted_data = sorted(self.hr_data, key=lambda x: (x.get('session_utc', 0), x.get('packet_index', 0)))
                
                current_session = None
                minute_offset = 0
                
                for data_point in sorted_data:
                    session_utc = data_point.get('session_utc', 0)
                    
                    # Reset offset for new session
                    if session_utc != current_session:
                        current_session = session_utc
                        minute_offset = 0
                        session_dt = datetime.fromtimestamp(session_utc)
                    
                    # Calculate timestamp for this HR value
                    hr_dt = session_dt + timedelta(minutes=minute_offset)
                    
                    writer.writerow([
                        hr_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        data_point['hr_bpm'],
                        session_dt.strftime('%H:%M:%S'),
                        minute_offset
                    ])
                    
                    minute_offset += 1
            
            # Calculate stats
            hr_values = [d['hr_bpm'] for d in self.hr_data]
            avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
            min_hr = min(hr_values) if hr_values else 0
            max_hr = max(hr_values) if hr_values else 0
            
            print(f"\n{'='*50}")
            print(f"✓ Exported to: {filename}")
            print(f"  Date: {selected_date.strftime('%Y-%m-%d')}")
            print(f"  Sessions: {len(selected_records)}")
            print(f"  Total HR values: {len(self.hr_data)}")
            print(f"  Average HR: {avg_hr:.0f} BPM")
            print(f"  Min HR: {min_hr} BPM")
            print(f"  Max HR: {max_hr} BPM")
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"Export error: {e}")
            traceback.print_exc()

    async def disconnect(self):
        """Disconnect from device"""
        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                print("\n✓ Disconnected")
                self.is_connected = False
        except Exception as e:
            print(f"Disconnect error: {e}")

    async def run(self):
        """Main execution flow"""
        try:
            # 1. Scan and connect
            if not await self.scan_and_connect():
                return
            
            # 2. Discover services
            if not await self.discover_services():
                await self.disconnect()
                return
            
            # 3. Set UTC time
            if not await self.set_utc_time():
                await self.disconnect()
                return
            
            # 4. Get HR records
            if not await self.get_hr_records():
                print("\n⚠ No HR records found or device doesn't support HR tracking")
                await self.disconnect()
                return
            
            # 5. Group records by day
            if self.hr_records:
                days = {}
                for record in self.hr_records:
                    dt = datetime.fromtimestamp(record['utc'])
                    day_key = dt.strftime('%Y-%m-%d')
                    if day_key not in days:
                        days[day_key] = []
                    days[day_key].append(record)
                
                # Show available days
                print(f"\n{'='*50}")
                print("Available days with HR data:")
                print(f"{'='*50}")
                sorted_days = sorted(days.keys(), reverse=True)
                for i, day in enumerate(sorted_days, 1):
                    records = days[day]
                    print(f"  {i}. {day} ({len(records)} sessions)")
                    for rec in records:
                        rec_dt = datetime.fromtimestamp(rec['utc'])
                        print(f"      - {rec_dt.strftime('%H:%M:%S')}")
                
                print(f"\n  0. Exit without download")
                
                # Select day
                while True:
                    try:
                        choice = input(f"\nSelect day to download (1-{len(sorted_days)}, or 0 to exit): ")
                        choice = int(choice)
                        if choice == 0:
                            print("Exiting...")
                            await self.disconnect()
                            return
                        if 1 <= choice <= len(sorted_days):
                            selected_day = sorted_days[choice - 1]
                            selected_records = days[selected_day]
                            break
                        else:
                            print(f"Please enter 0-{len(sorted_days)}")
                    except ValueError:
                        print("Please enter a number")
                
                # Download data for selected day
                selected_date = datetime.strptime(selected_day, '%Y-%m-%d')
                print(f"\nDownloading HR data for {selected_day}...")
                print(f"Sessions to download: {len(selected_records)}")
                
                self.hr_data = []  # Reset
                
                for i, record in enumerate(selected_records, 1):
                    rec_dt = datetime.fromtimestamp(record['utc'])
                    print(f"\n[{i}/{len(selected_records)}] Session {rec_dt.strftime('%H:%M:%S')}...")
                    
                    data_before = len(self.hr_data)
                    if await self.get_hr_data(record['utc']):
                        session_count = len(self.hr_data) - data_before
                        print(f"  ✓ Got {session_count} HR values")
                    
                    await asyncio.sleep(0.3)
                
                # 6. Export to CSV
                self.export_to_csv(selected_date, selected_records)
            
            # 7. Disconnect
            await self.disconnect()
            
        except Exception as e:
            print(f"\nError: {e}")
            traceback.print_exc()
            await self.disconnect()


async def main():
    """Entry point"""
    print("=" * 60)
    print("CL837 Heart Rate History Download")
    print("=" * 60)
    
    monitor = CL837HRMonitor()
    await monitor.run()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
