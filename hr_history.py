"""
CL837 Heart Rate History Download
Connection, UTC sync, and HR data retrieval
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime
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
            
            # DEBUG: Print all received packets
            print(f"[DEBUG] Received: header=0x{header:02X}, len={length}, cmd=0x{cmd:02X}, data={data.hex()}")
            
            if header != self.CHILEAF_HEADER:
                return
            
            # Response to GET_HR_RECORD (0x21)
            if cmd == self.CMD_GET_HR_RECORD:
                self.parse_hr_record_response(data)
            
            # Response to GET_HR_DATA (0x22)
            elif cmd == self.CMD_GET_HR_DATA:
                self.parse_hr_data_response(data)
            
            # Response to SET_UTC (0x08)
            elif cmd == self.CMD_SET_UTC:
                print("  ✓ UTC time synchronized")
            else:
                print(f"[DEBUG] Unknown command: 0x{cmd:02X}")
                
        except Exception as e:
            print(f"Notification handler error: {e}")
            traceback.print_exc()

    def parse_hr_record_response(self, data):
        """Parse HR record list response"""
        try:
            if len(data) < 5:
                return
            
            # Check if this is the end marker
            if len(data) == 5 and data[3] == 0xFF and data[4] == 0xFF:
                self.hr_records_complete = True
                print(f"\n✓ HR records download complete ({len(self.hr_records)} records)")
                return
            
            # Parse record: [header, length, cmd, utc(4 bytes), ...]
            if len(data) >= 7:
                utc_bytes = data[3:7]
                utc_timestamp = struct.unpack('>I', bytes(utc_bytes))[0]
                
                self.hr_records.append({
                    'utc': utc_timestamp,
                    'datetime': datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                })
                
                print(f"  HR Record: {datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            print(f"Parse HR record error: {e}")
            traceback.print_exc()

    def parse_hr_data_response(self, data):
        """Parse HR data response"""
        try:
            if len(data) < 5:
                return
            
            # Check if this is the end marker
            if len(data) == 5 and data[3] == 0xFF and data[4] == 0xFF:
                self.hr_data_complete = True
                print(f"\n✓ HR data download complete ({len(self.hr_data)} measurements)")
                return
            
            # Parse HR data: [header, length, cmd, sequence, hr_value, ...]
            # Based on Android SDK: HistoryOfHeartRate.java
            # Format may vary, this is a basic parser
            if len(data) >= 5:
                sequence = data[3]
                hr_value = data[4]
                
                self.hr_data.append({
                    'sequence': sequence,
                    'hr_bpm': hr_value,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                print(f"  HR Data: Seq={sequence}, BPM={hr_value}")
                
        except Exception as e:
            print(f"Parse HR data error: {e}")
            traceback.print_exc()

    def checksum(self, data):
        """Calculate checksum (XOR of all bytes)"""
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum

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

    async def get_hr_data(self, utc_timestamp):
        """Request HR data for specific timestamp"""
        try:
            print(f"\nRequesting HR data for {datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')}...")
            self.hr_data = []
            self.hr_data_complete = False
            
            # Convert timestamp to bytes
            utc_bytes = [
                0x01,  # Request type (1 = get data)
                (utc_timestamp >> 24) & 0xFF,
                (utc_timestamp >> 16) & 0xFF,
                (utc_timestamp >> 8) & 0xFF,
                utc_timestamp & 0xFF
            ]
            
            await self.send_command(self.CMD_GET_HR_DATA, utc_bytes)
            
            # Wait for data to download (max 30 seconds)
            timeout = 30
            start_time = time.time()
            
            while not self.hr_data_complete:
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("✗ Timeout waiting for HR data")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Get HR data error: {e}")
            return False

    def export_to_csv(self):
        """Export HR data to CSV file"""
        try:
            if not self.hr_records:
                print("\nNo HR data to export")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hr_history_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow([
                    'record_number',
                    'utc_timestamp',
                    'datetime_utc',
                    'measurement_count',
                    'avg_bpm',
                    'min_bpm',
                    'max_bpm'
                ])
                
                # Data rows
                for i, record in enumerate(self.hr_records, 1):
                    # Filter data for this record (if we downloaded detailed data)
                    record_data = [d for d in self.hr_data if d.get('record_utc') == record['utc']]
                    
                    if record_data:
                        hr_values = [d['hr_bpm'] for d in record_data if d['hr_bpm'] > 0]
                        avg_bpm = sum(hr_values) / len(hr_values) if hr_values else 0
                        min_bpm = min(hr_values) if hr_values else 0
                        max_bpm = max(hr_values) if hr_values else 0
                        count = len(record_data)
                    else:
                        avg_bpm = min_bpm = max_bpm = count = 0
                    
                    writer.writerow([
                        i,
                        record['utc'],
                        record['datetime'],
                        count,
                        f"{avg_bpm:.1f}" if avg_bpm > 0 else "N/A",
                        min_bpm if min_bpm > 0 else "N/A",
                        max_bpm if max_bpm > 0 else "N/A"
                    ])
            
            print(f"\n✓ Data exported to: {filename}")
            print(f"  Records: {len(self.hr_records)}")
            print(f"  Measurements: {len(self.hr_data)}")
            
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
            
            # 5. Optionally download detailed data for each record
            if self.hr_records:
                print(f"\nFound {len(self.hr_records)} HR records")
                download_details = input("Download detailed HR data for all records? (y/n): ").lower()
                
                if download_details == 'y':
                    for i, record in enumerate(self.hr_records, 1):
                        print(f"\n[{i}/{len(self.hr_records)}] Processing record...")
                        if await self.get_hr_data(record['utc']):
                            # Mark data with record UTC for CSV export
                            for data_point in self.hr_data:
                                data_point['record_utc'] = record['utc']
                        await asyncio.sleep(0.5)
            
            # 6. Export to CSV
            self.export_to_csv()
            
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
