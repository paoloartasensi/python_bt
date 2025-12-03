"""
CL837 Sport/Activity History Download
7-day sport history with steps, distance, and calories
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837SportMonitor:
    """CL837 Sport History Monitor"""
    
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
        self.CMD_GET_SPORT_HISTORY = 0x16  # 22 in decimal - 7 day history
        
        # Sport data storage
        self.sport_records = []
        self.sport_complete = False
        self.sport_packets = []  # Accumulate packets until END_TAG
        
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
            
            # Response to GET_SPORT_HISTORY (0x16)
            if cmd == self.CMD_GET_SPORT_HISTORY:
                self.parse_sport_response(data)
            
            # Response to SET_UTC (0x08)
            elif cmd == self.CMD_SET_UTC:
                print("  ✓ UTC time synchronized")
                
        except Exception as e:
            print(f"Notification handler error: {e}")
            traceback.print_exc()

    def parse_sport_response(self, data):
        """Parse sport history response.
        
        CL837 sends all sport data in a single packet (no END_TAG like CL833):
        - Packet: [0xFF, len, 0x16, payload..., checksum]
        - Payload = (len - 4) bytes of sport records
        - Sport record format (10 bytes each):
          - stamp: 4 bytes (BIG-endian UTC timestamp)
          - step: 3 bytes (BIG-endian)
          - calorie: 3 bytes (BIG-endian) - value in 0.1 cal units
        """
        try:
            if len(data) < 7:
                return
            
            # Print raw data for debug
            hex_str = ' '.join(f'{b:02X}' for b in data)
            print(f"  [DEBUG] RX ({len(data)} bytes): {hex_str}")
            
            # Extract payload: skip header(1), len(1), cmd(1) and checksum(1)
            # payload = data[3:-1]
            payload = data[3:-1] if len(data) > 4 else data[3:]
            
            hex_payload = ' '.join(f'{b:02X}' for b in payload)
            print(f"  [DEBUG] Payload ({len(payload)} bytes): {hex_payload}")
            
            # Parse 10-byte records directly
            record_size = 10
            num_records = len(payload) // record_size
            
            print(f"  [DEBUG] Parsing {num_records} records...")
            
            for i in range(num_records):
                offset = i * record_size
                
                # BIG-ENDIAN parsing (SDK getLongParse does val << 8 | byte)
                stamp = ((payload[offset] << 24) | 
                        (payload[offset+1] << 16) | 
                        (payload[offset+2] << 8) | 
                        payload[offset+3])
                
                step = ((payload[offset+4] << 16) | 
                       (payload[offset+5] << 8) | 
                       payload[offset+6])
                
                calorie_raw = ((payload[offset+7] << 16) | 
                              (payload[offset+8] << 8) | 
                              payload[offset+9])
                calorie = calorie_raw / 10.0
                
                # Debug print raw values
                raw_hex = ' '.join(f'{payload[offset+j]:02X}' for j in range(10))
                print(f"  [DEBUG] Record {i}: {raw_hex} -> stamp={stamp} (0x{stamp:08X}), step={step}, cal_raw={calorie_raw}")
                
                # Skip invalid records
                if stamp == 0 or stamp == 0xFFFFFFFF:
                    print(f"  [DEBUG] Skipping invalid record {i}")
                    continue
                
                try:
                    dt = datetime.fromtimestamp(stamp)
                    dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception as e:
                    print(f"  [DEBUG] Invalid timestamp {stamp}: {e}")
                    continue
                
                sport_record = {
                    'utc': stamp,
                    'datetime': dt_str,
                    'date': date_str,
                    'steps': step,
                    'calories': calorie
                }
                
                self.sport_records.append(sport_record)
                print(f"  Day {len(self.sport_records)}: {dt_str} - {step:,} steps, {calorie:.1f} cal")
            
            # Mark complete after parsing
            if num_records > 0:
                self.sport_complete = True
                print(f"\n✓ Sport history download complete ({len(self.sport_records)} days)")
                
        except Exception as e:
            print(f"Parse sport response error: {e}")
            traceback.print_exc()

    def checksum(self, data):
        """Calculate Chileaf protocol checksum.
        
        From decompiled SDK (FitnessManager.java):
        return (byte) (((-result) ^ 58) & 255);
        """
        result = sum(byte & 0xFF for byte in data)
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

    async def get_sport_history(self):
        """Request 7-day sport history"""
        try:
            print("\nRequesting 7-day sport history...")
            self.sport_records = []
            self.sport_packets = []
            self.sport_complete = False
            
            await self.send_command(self.CMD_GET_SPORT_HISTORY, [0x00])
            
            # Wait for data to download (max 30 seconds)
            timeout = 30
            start_time = time.time()
            
            while not self.sport_complete:
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("✗ Timeout waiting for sport history")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Get sport history error: {e}")
            return False

    def export_to_csv(self):
        """Export sport data to CSV file"""
        try:
            if not self.sport_records:
                print("\nNo sport data to export")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sport_history_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow([
                    'day_number',
                    'utc_timestamp',
                    'datetime_utc',
                    'date',
                    'steps',
                    'calories'
                ])
                
                # Data rows
                for i, record in enumerate(self.sport_records, 1):
                    writer.writerow([
                        i,
                        record['utc'],
                        record['datetime'],
                        record['date'],
                        record['steps'],
                        record['calories']
                    ])
            
            # Print summary
            print(f"\n✓ Data exported to: {filename}")
            print(f"\n📊 SUMMARY:")
            print(f"  Days recorded: {len(self.sport_records)}")
            
            if self.sport_records:
                total_steps = sum(r['steps'] for r in self.sport_records)
                total_calories = sum(r['calories'] for r in self.sport_records)
                avg_steps = total_steps / len(self.sport_records)
                
                print(f"  Total steps: {total_steps:,}")
                print(f"  Total calories: {total_calories:,}")
                print(f"  Average steps/day: {avg_steps:.0f}")
                
                # Find most active day
                most_active = max(self.sport_records, key=lambda x: x['steps'])
                print(f"  Most active day: {most_active['date']} ({most_active['steps']:,} steps)")
            
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
            
            # 4. Get 7-day sport history
            if not await self.get_sport_history():
                print("\n⚠ No sport history found or device doesn't support this feature")
                await self.disconnect()
                return
            
            # 5. Export to CSV
            self.export_to_csv()
            
            # 6. Disconnect
            await self.disconnect()
            
        except Exception as e:
            print(f"\nError: {e}")
            traceback.print_exc()
            await self.disconnect()


async def main():
    """Entry point"""
    print("=" * 60)
    print("CL837 Sport History Download (7-Day Activity)")
    print("=" * 60)
    
    monitor = CL837SportMonitor()
    await monitor.run()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
