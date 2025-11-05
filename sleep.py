"""
CL837 Sleep Data Download
Connection, UTC sync, and sleep data retrieval
"""
import asyncio
import time
import struct
import traceback
from datetime import datetime
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

    def analyze_sleep_data(self):
        """Analyze and display sleep data"""
        print("\n" + "="*70)
        print("SLEEP DATA ANALYSIS")
        print("="*70)
        
        if not self.sleep_data:
            print("No sleep data available")
            return
        
        print(f"\nTotal sleep records: {len(self.sleep_data)}\n")
        
        for i, record in enumerate(self.sleep_data, 1):
            print(f"Record {i}:")
            print(f"  Start time: {record['datetime']} UTC")
            print(f"  Duration: {record['count'] * 5} minutes ({record['count']} x 5min intervals)")
            
            # Analyze sleep stages
            deep_sleep = 0
            light_sleep = 0
            awake = 0
            
            indices = record['activity_indices']
            
            # Detect deep sleep (3 consecutive zeros)
            i_idx = 0
            while i_idx < len(indices):
                if i_idx + 2 < len(indices) and indices[i_idx] == 0 and indices[i_idx+1] == 0 and indices[i_idx+2] == 0:
                    deep_sleep += 3
                    i_idx += 3
                elif indices[i_idx] < 20:
                    light_sleep += 1
                    i_idx += 1
                else:
                    awake += 1
                    i_idx += 1
            
            print(f"  Deep sleep: {deep_sleep * 5} minutes ({deep_sleep} intervals)")
            print(f"  Light sleep: {light_sleep * 5} minutes ({light_sleep} intervals)")
            print(f"  Awake: {awake * 5} minutes ({awake} intervals)")
            print(f"  Activity indices: {indices}")
            print()

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
