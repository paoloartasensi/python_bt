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
        """Parse sport history response"""
        try:
            if len(data) < 5:
                return
            
            # Check if this is the end marker
            if len(data) == 5 and data[3] == 0xFF and data[4] == 0xFF:
                self.sport_complete = True
                print(f"\n✓ Sport history download complete ({len(self.sport_records)} days)")
                return
            
            # Parse sport record: Based on HistoryOfSport.java
            # Format: [header, length, cmd, utc(4), step(4), distance(4), calorie(4)]
            if len(data) >= 19:
                # UTC timestamp (4 bytes)
                utc_bytes = data[3:7]
                utc_timestamp = struct.unpack('>I', bytes(utc_bytes))[0]
                
                # Step count (4 bytes)
                step_bytes = data[7:11]
                steps = struct.unpack('>I', bytes(step_bytes))[0]
                
                # Distance (4 bytes) - in meters
                dist_bytes = data[11:15]
                distance = struct.unpack('>I', bytes(dist_bytes))[0]
                
                # Calories (4 bytes)
                cal_bytes = data[15:19]
                calories = struct.unpack('>I', bytes(cal_bytes))[0]
                
                sport_record = {
                    'utc': utc_timestamp,
                    'datetime': datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                    'date': datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d'),
                    'steps': steps,
                    'distance_m': distance,
                    'distance_km': distance / 1000.0,
                    'calories': calories
                }
                
                self.sport_records.append(sport_record)
                
                print(f"  Day {len(self.sport_records)}: {sport_record['date']} - "
                      f"{steps} steps, {distance}m, {calories} cal")
                
        except Exception as e:
            print(f"Parse sport response error: {e}")
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

    async def get_sport_history(self):
        """Request 7-day sport history"""
        try:
            print("\nRequesting 7-day sport history...")
            self.sport_records = []
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
                    'distance_m',
                    'distance_km',
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
                        record['distance_m'],
                        f"{record['distance_km']:.2f}",
                        record['calories']
                    ])
            
            # Print summary
            print(f"\n✓ Data exported to: {filename}")
            print(f"\n📊 SUMMARY:")
            print(f"  Days recorded: {len(self.sport_records)}")
            
            if self.sport_records:
                total_steps = sum(r['steps'] for r in self.sport_records)
                total_distance = sum(r['distance_km'] for r in self.sport_records)
                total_calories = sum(r['calories'] for r in self.sport_records)
                avg_steps = total_steps / len(self.sport_records)
                
                print(f"  Total steps: {total_steps:,}")
                print(f"  Total distance: {total_distance:.2f} km")
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
