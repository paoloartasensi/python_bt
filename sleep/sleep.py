"""
CL837 Sleep Data Management
Complete solution for sleep data download with automatic UTC sync and validation

Features:
- Automatic UTC time synchronization before download
- Sleep data download with activity indices
- Deep/Light/Awake sleep stage detection (official SDK algorithm)
- Automatic data validation and filtering
- CSV export with comprehensive statistics
- Fast execution (~15-30 seconds total)

Usage:
    python sleep.py              # Download sleep data (includes UTC sync)
    python sleep.py --sync-only  # Quick UTC sync only (3-5 seconds)
"""
import asyncio
import time
import sys
import csv
from datetime import datetime, timezone
from bleak import BleakClient, BleakScanner


class CL837SleepManager:
    """Unified CL837 sleep data manager with automatic UTC sync"""
    
    # Chileaf Protocol Constants
    CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
    CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
    CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
    CHILEAF_HEADER = 0xFF
    
    # Commands
    CMD_SET_UTC = 0x08
    CMD_GET_SLEEP = 0x05
    
    # Validation - Device release date (2020-01-01)
    MIN_VALID_TIMESTAMP = 1577836800
    
    def __init__(self, sync_only=False):
        self.sync_only = sync_only
        
        # BLE Connection
        self.client = None
        self.device = None
        self.is_connected = False
        
        # Characteristics
        self.tx_char = None
        self.rx_char = None
        
        # UTC sync tracking
        self.utc_confirmed = False
        
        # Sleep data storage
        self.sleep_data = []
        self.sleep_data_complete = False

    async def scan_and_connect(self):
        """Scan for and connect to CL837 device"""
        print("🔍 Scanning for CL837 devices...")
        
        devices = await BleakScanner.discover(timeout=5.0 if self.sync_only else 8.0)
        
        cl837_devices = [d for d in devices 
                        if d.name and ("CL837" in d.name or "CL831" in d.name)]
        
        if not cl837_devices:
            print("❌ No CL837 devices found")
            return False
        
        # Auto-select first device or prompt for multiple
        if len(cl837_devices) == 1:
            target_device = cl837_devices[0]
            print(f"📱 Found: {target_device.name}")
        else:
            print(f"\nFound {len(cl837_devices)} devices:")
            for i, device in enumerate(cl837_devices, 1):
                print(f"{i}. {device.name} - {device.address}")
            
            while True:
                try:
                    choice = int(input("\nSelect device number: "))
                    if 1 <= choice <= len(cl837_devices):
                        target_device = cl837_devices[choice - 1]
                        break
                    print(f"Invalid choice. Enter 1-{len(cl837_devices)}")
                except ValueError:
                    print("Invalid input. Enter a number.")
        
        try:
            print("🔗 Connecting...")
            self.client = BleakClient(target_device, timeout=10.0)
            await self.client.connect()
            
            if self.client.is_connected:
                self.is_connected = True
                self.device = target_device
                print(f"✅ Connected to {target_device.name}")
                return True
            else:
                print("❌ Connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    async def setup_characteristics(self):
        """Find and validate required BLE characteristics"""
        for service in self.client.services:
            if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                for char in service.characteristics:
                    if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                        self.tx_char = char
                    elif char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                        self.rx_char = char
        
        if not self.tx_char or not self.rx_char:
            print("❌ Chileaf characteristics not found")
            return False
        
        if "notify" not in self.tx_char.properties:
            print("❌ TX characteristic does not support notifications")
            return False
        
        return True

    def calculate_checksum(self, data):
        """Calculate Chileaf protocol checksum: ((0 - sum) & 0xFF) ^ 0x3A"""
        checksum = sum(data) & 0xFF
        checksum = (0 - checksum) & 0xFF
        checksum = checksum ^ 0x3A
        return checksum

    async def send_command(self, command, data=None):
        """Send Chileaf protocol command to device"""
        if data is None:
            data = []
        
        # Build frame: [HEADER, LENGTH, COMMAND, DATA..., CHECKSUM]
        frame = [self.CHILEAF_HEADER, len(data) + 4, command] + data
        checksum = self.calculate_checksum(frame)
        frame.append(checksum)
        
        await self.client.write_gatt_char(self.rx_char, bytes(frame))
        await asyncio.sleep(0.1)

    async def sync_utc_time(self):
        """Synchronize UTC time to device"""
        print("\n⏰ Syncing UTC time...")
        
        utc_timestamp = int(time.time())
        utc_datetime = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)
        
        print(f"   UTC: {utc_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Timestamp: {utc_timestamp}")
        
        # Convert to 4 bytes (big-endian)
        utc_bytes = [
            (utc_timestamp >> 24) & 0xFF,
            (utc_timestamp >> 16) & 0xFF,
            (utc_timestamp >> 8) & 0xFF,
            utc_timestamp & 0xFF
        ]
        
        await self.send_command(self.CMD_SET_UTC, utc_bytes)
        await asyncio.sleep(1.0)
        
        if self.utc_confirmed:
            print("✅ UTC sync confirmed by device")
        else:
            print("✅ UTC sync sent")
        
        return True

    async def download_sleep_data(self):
        """Request and download sleep data from device"""
        print("\n💤 Requesting sleep data...")
        
        # Command 0x05, subcommand 0x02
        await self.send_command(self.CMD_GET_SLEEP, [0x02])
        
        print("⏳ Waiting for data...")
        timeout = 30
        start_time = time.time()
        
        while not self.sleep_data_complete and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.5)
        
        if self.sleep_data_complete:
            print("✅ Sleep data received")
            return True
        else:
            print("⚠️  Timeout waiting for sleep data")
            return False

    def notification_handler(self, sender, data):
        """Handle BLE notifications from device"""
        if len(data) < 3:
            return
        
        header = data[0]
        command = data[2]
        
        if header != self.CHILEAF_HEADER:
            return
        
        # UTC sync confirmation
        if command == self.CMD_SET_UTC:
            self.utc_confirmed = True
        
        # Sleep data response
        elif command == self.CMD_GET_SLEEP:
            self._parse_sleep_packet(data)

    def _parse_sleep_packet(self, data):
        """Parse sleep data packet"""
        if len(data) < 4:
            return
        
        subcommand = data[3]
        
        # 0x03 = sleep data packet
        if subcommand == 0x03:
            payload_end = data[1]
            idx = 4
            
            while idx < payload_end - 1:  # -1 for checksum
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
                
                # Store record
                self.sleep_data.append({
                    'utc': utc,
                    'datetime': datetime.fromtimestamp(utc, tz=timezone.utc),
                    'count': count,
                    'activity_indices': activity_indices
                })
            
            # Check if last packet
            if len(data) <= 50:
                self.sleep_data_complete = True
        
        # 0xFF = end of data
        elif subcommand == 0xFF:
            self.sleep_data_complete = True

    def validate_and_filter(self):
        """Filter out invalid sleep records"""
        if not self.sleep_data:
            return
        
        current_time = int(time.time())
        valid_records = []
        invalid_count = 0
        
        for record in self.sleep_data:
            utc = record['utc']
            count = record['count']
            
            # Validate timestamp and duration
            is_valid = (
                utc >= self.MIN_VALID_TIMESTAMP and  # Not before 2020
                utc <= current_time and               # Not in future
                count > 0                             # Has data
            )
            
            if is_valid:
                valid_records.append(record)
            else:
                invalid_count += 1
        
        if invalid_count > 0:
            print(f"\n⚠️  Filtered out {invalid_count} invalid record(s)")
        
        self.sleep_data = valid_records
        print(f"✅ {len(valid_records)} valid record(s)")

    def analyze_sleep_stages(self, activity_indices):
        """
        Analyze sleep stages using official SDK algorithm
        
        Rules:
        - Activity = 0: Count consecutive zeros
          - 3+ consecutive = Deep sleep
          - < 3 consecutive = Light sleep
        - Activity 1-20: Light sleep
        - Activity > 20: Awake
        """
        deep_sleep = 0
        light_sleep = 0
        awake = 0
        consecutive_zeros = 0
        
        for action in activity_indices:
            if action == 0:
                consecutive_zeros += 1
            else:
                # Process accumulated zeros
                if consecutive_zeros >= 3:
                    deep_sleep += consecutive_zeros
                elif consecutive_zeros > 0:
                    light_sleep += consecutive_zeros
                
                consecutive_zeros = 0
                
                # Process current value
                if action > 20:
                    awake += 1
                else:  # 1-20
                    light_sleep += 1
        
        # Process remaining zeros
        if consecutive_zeros >= 3:
            deep_sleep += consecutive_zeros
        elif consecutive_zeros > 0:
            light_sleep += consecutive_zeros
        
        return deep_sleep, light_sleep, awake

    def analyze_and_display(self):
        """Analyze and display sleep data"""
        if not self.sleep_data:
            print("\n⚠️  No sleep data available")
            return
        
        self.validate_and_filter()
        
        if not self.sleep_data:
            print("\n⚠️  No valid sleep data after filtering")
            return
        
        print(f"\n{'='*70}")
        print("SLEEP DATA ANALYSIS")
        print(f"{'='*70}\n")
        
        for i, record in enumerate(self.sleep_data, 1):
            # Analyze stages
            deep, light, awake = self.analyze_sleep_stages(record['activity_indices'])
            
            # Store for CSV export
            record['deep_sleep_min'] = deep * 5
            record['light_sleep_min'] = light * 5
            record['awake_min'] = awake * 5
            
            # Display
            duration = record['count'] * 5
            print(f"Record {i}:")
            print(f"  📅 {record['datetime'].strftime('%Y-%m-%d %H:%M')} UTC")
            print(f"  ⏱️  Duration: {duration} min ({record['count']} intervals)")
            print(f"  🌙 Deep sleep: {deep * 5} min")
            print(f"  💤 Light sleep: {light * 5} min")
            print(f"  👁️  Awake: {awake * 5} min")
            print()

    def export_to_csv(self, filename=None):
        """Export sleep data to CSV file"""
        if not self.sleep_data:
            print("⚠️  No data to export")
            return False
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sleep_data_{timestamp}.csv"
        
        try:
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
            
            print(f"📄 Data exported to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting CSV: {e}")
            return False

    async def run(self):
        """Execute main workflow"""
        mode = "UTC SYNC ONLY" if self.sync_only else "SLEEP DATA DOWNLOAD"
        
        print(f"\n{'='*70}")
        print(f"CL837 {mode}")
        print(f"{'='*70}\n")
        
        # Step 1: Connect
        if not await self.scan_and_connect():
            return False
        
        # Step 2: Setup BLE
        if not await self.setup_characteristics():
            return False
        
        # Step 3: Enable notifications
        await self.client.start_notify(self.tx_char, self.notification_handler)
        await asyncio.sleep(0.2)
        
        # Step 4: Sync UTC (always required)
        await self.sync_utc_time()
        
        # Step 5: Download data (unless sync-only mode)
        if not self.sync_only:
            if await self.download_sleep_data():
                self.analyze_and_display()
                self.export_to_csv()
        
        # Step 6: Cleanup
        await self.client.stop_notify(self.tx_char)
        await self.client.disconnect()
        
        print(f"\n🔌 Disconnected")
        
        if self.sync_only:
            print(f"\n{'='*70}")
            print("✅ UTC SYNC COMPLETED")
            print(f"{'='*70}")
            print("\nDevice time synchronized. All new data will have accurate timestamps.")
        else:
            print(f"\n{'='*70}")
            print("✅ SLEEP DATA DOWNLOAD COMPLETED")
            print(f"{'='*70}")
        
        return True

    async def disconnect(self):
        """Emergency disconnect"""
        if self.client and self.is_connected:
            try:
                await self.client.stop_notify(self.tx_char)
            except:
                pass
            await self.client.disconnect()


async def main():
    """Main entry point"""
    # Parse command line arguments
    sync_only = "--sync-only" in sys.argv or "-s" in sys.argv
    
    manager = CL837SleepManager(sync_only=sync_only)
    
    try:
        await manager.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        await manager.disconnect()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        print("\nOptions:")
        print("  (no args)          Download sleep data with automatic UTC sync")
        print("  --sync-only, -s    Quick UTC sync only (3-5 seconds)")
        print("  --help, -h         Show this help message")
        sys.exit(0)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBye! 👋")
