"""
CL837 Steps History Download
Step records, interval steps, and detailed step data
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837StepsMonitor:
    """CL837 Steps History Monitor"""
    
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
        self.CMD_GET_STEP_RECORD = 0x90  # -112 in signed byte
        self.CMD_GET_STEP_DATA = 0x91    # -111 in signed byte
        self.CMD_GET_INTERVAL_STEPS = 0x40  # Interval steps
        
        # Step data storage
        self.step_records = []
        self.step_data = []
        self.interval_steps = []
        self.step_records_complete = False
        self.step_data_complete = False
        self.interval_steps_complete = False
        
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
            
            # Response to GET_STEP_RECORD (0x90)
            if cmd == 0x90:
                self.parse_step_record_response(data)
            
            # Response to GET_STEP_DATA (0x91)
            elif cmd == 0x91:
                self.parse_step_data_response(data)
            
            # Response to GET_INTERVAL_STEPS (0x40)
            elif cmd == 0x40:
                self.parse_interval_steps_response(data)
            
            # Response to SET_UTC (0x08)
            elif cmd == self.CMD_SET_UTC:
                print("  ✓ UTC time synchronized")
                
        except Exception as e:
            print(f"Notification handler error: {e}")
            traceback.print_exc()

    def parse_step_record_response(self, data):
        """Parse step record list response"""
        try:
            if len(data) < 5:
                return
            
            # Check if this is the end marker
            if len(data) == 5 and data[3] == 0xFF and data[4] == 0xFF:
                self.step_records_complete = True
                print(f"\n✓ Step records download complete ({len(self.step_records)} records)")
                return
            
            # Parse record: [header, length, cmd, utc(4 bytes), ...]
            if len(data) >= 7:
                utc_bytes = data[3:7]
                utc_timestamp = struct.unpack('>I', bytes(utc_bytes))[0]
                
                self.step_records.append({
                    'utc': utc_timestamp,
                    'datetime': datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                })
                
                print(f"  Step Record: {datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            print(f"Parse step record error: {e}")
            traceback.print_exc()

    def parse_step_data_response(self, data):
        """Parse step data response (detailed step counts)"""
        try:
            if len(data) < 5:
                return
            
            # Check if this is the end marker
            if len(data) == 5 and data[3] == 0xFF and data[4] == 0xFF:
                self.step_data_complete = True
                print(f"\n✓ Step data download complete ({len(self.step_data)} entries)")
                return
            
            # Parse step data: Based on HistoryOfStep.java
            # Format: [header, length, cmd, sequence, step_count(4), distance(4), calorie(4)]
            if len(data) >= 15:
                sequence = data[3]
                
                # Step count (4 bytes)
                step_bytes = data[4:8]
                step_count = struct.unpack('>I', bytes(step_bytes))[0]
                
                # Distance (4 bytes) - likely in meters
                dist_bytes = data[8:12]
                distance = struct.unpack('>I', bytes(dist_bytes))[0]
                
                # Calories (4 bytes)
                cal_bytes = data[12:16]
                calories = struct.unpack('>I', bytes(cal_bytes))[0]
                
                self.step_data.append({
                    'sequence': sequence,
                    'steps': step_count,
                    'distance_m': distance,
                    'calories': calories
                })
                
                print(f"  Step Data: Seq={sequence}, Steps={step_count}, Dist={distance}m, Cal={calories}")
                
        except Exception as e:
            print(f"Parse step data error: {e}")
            traceback.print_exc()

    def parse_interval_steps_response(self, data):
        """Parse interval steps response"""
        try:
            if len(data) < 5:
                return
            
            # Check if this is the end marker
            if len(data) == 5 and data[3] == 0xFF and data[4] == 0xFF:
                self.interval_steps_complete = True
                print(f"\n✓ Interval steps download complete ({len(self.interval_steps)} intervals)")
                return
            
            # Parse interval: Based on IntervalStep.java
            # Format: [header, length, cmd, utc(4), step_count(2), ...]
            if len(data) >= 9:
                utc_bytes = data[3:7]
                utc_timestamp = struct.unpack('>I', bytes(utc_bytes))[0]
                
                step_bytes = data[7:9]
                step_count = struct.unpack('>H', bytes(step_bytes))[0]
                
                self.interval_steps.append({
                    'utc': utc_timestamp,
                    'datetime': datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                    'steps': step_count
                })
                
                print(f"  Interval: {datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')} - {step_count} steps")
                
        except Exception as e:
            print(f"Parse interval steps error: {e}")
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

    async def get_step_records(self):
        """Request step record list"""
        try:
            print("\nRequesting step records...")
            self.step_records = []
            self.step_records_complete = False
            
            await self.send_command(self.CMD_GET_STEP_RECORD, [])
            
            # Wait for records to download (max 30 seconds)
            timeout = 30
            start_time = time.time()
            
            while not self.step_records_complete:
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("✗ Timeout waiting for step records")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Get step records error: {e}")
            return False

    async def get_step_data(self, utc_timestamp):
        """Request step data for specific timestamp"""
        try:
            print(f"\nRequesting step data for {datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')}...")
            self.step_data = []
            self.step_data_complete = False
            
            # Convert timestamp to bytes
            utc_bytes = [
                0x01,  # Request type (1 = get data)
                (utc_timestamp >> 24) & 0xFF,
                (utc_timestamp >> 16) & 0xFF,
                (utc_timestamp >> 8) & 0xFF,
                utc_timestamp & 0xFF
            ]
            
            await self.send_command(self.CMD_GET_STEP_DATA, utc_bytes)
            
            # Wait for data to download (max 30 seconds)
            timeout = 30
            start_time = time.time()
            
            while not self.step_data_complete:
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("✗ Timeout waiting for step data")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Get step data error: {e}")
            return False

    async def get_interval_steps(self):
        """Request interval steps"""
        try:
            print("\nRequesting interval steps...")
            self.interval_steps = []
            self.interval_steps_complete = False
            
            await self.send_command(self.CMD_GET_INTERVAL_STEPS, [0x00])
            
            # Wait for data to download (max 30 seconds)
            timeout = 30
            start_time = time.time()
            
            while not self.interval_steps_complete:
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("✗ Timeout waiting for interval steps")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Get interval steps error: {e}")
            return False

    def export_to_csv(self):
        """Export step data to CSV files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export step records with detailed data
            if self.step_records:
                filename = f"steps_records_{timestamp}.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['record_number', 'utc_timestamp', 'datetime_utc', 'total_steps', 'total_distance_m', 'total_calories'])
                    
                    for i, record in enumerate(self.step_records, 1):
                        # Sum data for this record if available
                        record_data = [d for d in self.step_data if d.get('record_utc') == record['utc']]
                        total_steps = sum(d['steps'] for d in record_data) if record_data else 0
                        total_dist = sum(d['distance_m'] for d in record_data) if record_data else 0
                        total_cal = sum(d['calories'] for d in record_data) if record_data else 0
                        
                        writer.writerow([i, record['utc'], record['datetime'], total_steps, total_dist, total_cal])
                
                print(f"\n✓ Records exported to: {filename}")
                print(f"  Total records: {len(self.step_records)}")
            
            # Export interval steps
            if self.interval_steps:
                filename = f"steps_intervals_{timestamp}.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['interval_number', 'utc_timestamp', 'datetime_utc', 'steps'])
                    
                    for i, interval in enumerate(self.interval_steps, 1):
                        writer.writerow([i, interval['utc'], interval['datetime'], interval['steps']])
                
                print(f"✓ Intervals exported to: {filename}")
                print(f"  Total intervals: {len(self.interval_steps)}")
                print(f"  Total steps in intervals: {sum(i['steps'] for i in self.interval_steps)}")
            
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
            
            # 4. Get interval steps (confirmed working by user)
            print("\n" + "="*60)
            print("INTERVAL STEPS")
            print("="*60)
            await self.get_interval_steps()
            
            # 5. Get step records
            print("\n" + "="*60)
            print("STEP RECORDS")
            print("="*60)
            if await self.get_step_records():
                # 6. Optionally download detailed data for each record
                if self.step_records:
                    print(f"\nFound {len(self.step_records)} step records")
                    download_details = input("Download detailed step data for all records? (y/n): ").lower()
                    
                    if download_details == 'y':
                        for i, record in enumerate(self.step_records, 1):
                            print(f"\n[{i}/{len(self.step_records)}] Processing record...")
                            if await self.get_step_data(record['utc']):
                                # Mark data with record UTC for CSV export
                                for data_point in self.step_data:
                                    data_point['record_utc'] = record['utc']
                            await asyncio.sleep(0.5)
            
            # 7. Export to CSV
            self.export_to_csv()
            
            # 8. Disconnect
            await self.disconnect()
            
        except Exception as e:
            print(f"\nError: {e}")
            traceback.print_exc()
            await self.disconnect()


async def main():
    """Entry point"""
    print("=" * 60)
    print("CL837 Steps History Download")
    print("=" * 60)
    
    monitor = CL837StepsMonitor()
    await monitor.run()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
