"""
CL837 Heart Rate Zones & Alarms Configuration
Configure HR zones, max HR, and alarm modes

Protocol: Chileaf custom protocol
- Command 0x03/0x04: User info (age, sex, weight, height)
- Command 0x46: Set/Get HR zone (min, max, goal)
- Command 0x57: Set alarm mode (age-based or fixed)
- Command 0x74/0x75: Set/Get max HR
- Command 0x5B: Get UTC + alarm status

Based on decompiled Chileaf SDK:
- iOS: HeartBLEDevice.m
- Android: WearManager.java
"""
import asyncio
import argparse
import struct
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837HRZoneManager:
    """CL837 Heart Rate Zones & Alarms Manager"""
    
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
        self.CMD_GET_USER_INFO = 0x03
        self.CMD_SET_USER_INFO = 0x04
        self.CMD_SET_HR_ZONE = 0x46
        self.CMD_GET_HR_ZONE = 0x46
        self.CMD_SET_ALERT_MODE = 0x57
        self.CMD_GET_UTC_ALERT = 0x5B
        self.CMD_SET_MAX_HR = 0x74
        self.CMD_GET_MAX_HR = 0x75
        
        # Characteristics
        self.tx_char = None
        self.rx_char = None
        
        # User data
        self.user_age = None
        self.user_sex = None
        self.user_weight = None
        self.user_height = None
        
        # HR settings
        self.hr_max = None
        self.hr_min = None
        self.hr_goal = None
        self.alarm_mode = None  # 'age' or 'fixed'
        
        # Response events
        self.response_received = asyncio.Event()
        self.response_data = None

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
                    except ValueError:
                        pass
                    print(f"Invalid choice. Enter 1-{len(cl837_devices)}")
            
            break
        
        try:
            print("\nConnecting...")
            self.client = BleakClient(target_device, timeout=10.0)
            await self.client.connect()
            
            if self.client.is_connected:
                self.is_connected = True
                self.device = target_device
                print(f"✓ Connected to {target_device.name}")
                return True
            else:
                print("✗ Connection failed")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def discover_services(self):
        """Discover and setup GATT characteristics"""
        try:
            for service in self.client.services:
                if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                    for char in service.characteristics:
                        if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                            self.tx_char = char
                        elif char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                            self.rx_char = char
            
            if not self.tx_char or not self.rx_char:
                print("✗ Chileaf service not found")
                return False
            
            # Subscribe to notifications
            await self.client.start_notify(self.tx_char, self.notification_handler)
            print("✓ Subscribed to notifications")
            
            return True
            
        except Exception as e:
            print(f"Service discovery error: {e}")
            return False

    def notification_handler(self, sender, data):
        """Handle incoming notifications"""
        if len(data) < 3:
            return
        
        if data[0] != self.CHILEAF_HEADER:
            return
        
        cmd = data[2]
        
        # Debug: print raw data
        print(f"[DEBUG] RX [{len(data)}]: {' '.join(f'{b:02X}' for b in data)}")
        
        # Ignore common push notifications (not responses to our commands)
        PUSH_COMMANDS = [0x01, 0x02, 0x0C, 0x15, 0x38]  # Sport, Health, Accel, etc.
        if cmd in PUSH_COMMANDS:
            print(f"[INFO] Ignoring push notification (cmd 0x{cmd:02X})")
            return
        
        try:
            if cmd == self.CMD_GET_USER_INFO:
                self.parse_user_info(data)
            elif cmd == self.CMD_GET_HR_ZONE:
                self.parse_hr_zone(data)
            elif cmd == self.CMD_GET_MAX_HR:
                self.parse_max_hr(data)
            elif cmd == self.CMD_GET_UTC_ALERT:
                self.parse_utc_alert(data)
            else:
                print(f"[INFO] Unknown command: 0x{cmd:02X}")
        except Exception as e:
            print(f"[ERROR] Parse error: {e}")

    def parse_user_info(self, data):
        """Parse user info response (cmd 0x03)"""
        # SDK parsing: age=value[5], sex=value[6], weight=value[7], height=value[8], userId=value[9-13]
        # Expected: [FF] [len] [03] [??] [??] [age] [sex] [weight] [height] [user_id_5bytes] [checksum]
        if len(data) < 14:
            print(f"[WARN] User info packet too short: {len(data)} bytes")
            return
        
        self.user_age = data[5]
        self.user_sex = data[6]  # 0=female, 1=male
        self.user_weight = data[7]  # 1 byte, not 2!
        self.user_height = data[8]  # 1 byte, not 2!
        
        print(f"\n📋 User Info:")
        print(f"   Age:    {self.user_age} years")
        print(f"   Sex:    {'Male' if self.user_sex == 1 else 'Female'}")
        print(f"   Weight: {self.user_weight} kg")
        print(f"   Height: {self.user_height} cm")
        
        # Calculate HR_max from age
        if self.user_age and self.user_age > 0:
            calculated_max = 220 - self.user_age
            print(f"\n💓 HR Max (calculated): {calculated_max} bpm")
        
        self.response_received.set()

    def parse_hr_zone(self, data):
        """Parse HR zone response (cmd 0x46/70)"""
        # SDK parsing: min=value[4], max=value[5], goal=value[6]
        # Expected: [FF] [len] [46] [??] [min] [max] [goal] [checksum]
        if len(data) < 8:
            return
        
        self.hr_min = data[4]
        self.hr_max = data[5]
        self.hr_goal = data[6]
        
        print(f"\n🎯 HR Zone Settings:")
        print(f"   Min:  {self.hr_min} bpm")
        print(f"   Max:  {self.hr_max} bpm")
        print(f"   Goal: {self.hr_goal} bpm")
        
        self.response_received.set()

    def parse_max_hr(self, data):
        """Parse max HR response (cmd 0x75/117)"""
        # SDK parsing: if (value[4] == 6) { max_hr = value[5]; }
        # Expected: [FF] [len] [75] [??] [06] [max_hr] [checksum]
        if len(data) < 7:
            return
        
        # Verify structure: byte at position 4 should be 0x06
        if data[4] != 0x06:
            print(f"[WARN] Not a valid max HR response (byte[4]={data[4]:02X}, expected 06)")
            return
        
        self.hr_max = data[5]
        
        # Sanity check: HR max should be reasonable (100-220)
        if self.hr_max < 100 or self.hr_max > 220:
            print(f"[WARN] Unusual HR max value: {self.hr_max} bpm (ignored)")
            return
        
        print(f"\n💓 Max HR Setting: {self.hr_max} bpm")
        
        self.response_received.set()

    def parse_utc_alert(self, data):
        """Parse UTC + alarm status (cmd 0x5B)"""
        if len(data) < 8:
            return
        
        utc = (data[3] << 24) | (data[4] << 16) | (data[5] << 8) | data[6]
        alarm_enabled = data[7]
        
        dt = datetime.fromtimestamp(utc)
        
        print(f"\n⏰ Device Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Alarm: {'Enabled' if alarm_enabled else 'Disabled'}")
        
        self.response_received.set()

    def checksum(self, data):
        """Calculate Chileaf protocol checksum"""
        result = sum(byte & 0xFF for byte in data)
        return ((-result) ^ 0x3A) & 0xFF

    async def send_command(self, cmd, params=None):
        """Send command to device"""
        try:
            if params is None:
                params = []
            
            length = 4 + len(params)
            packet = [self.CHILEAF_HEADER, length, cmd] + params
            checksum = self.checksum(packet)
            packet.append(checksum)
            
            await self.client.write_gatt_char(self.rx_char, bytes(packet), response=True)
            return True
            
        except Exception as e:
            print(f"Send command error: {e}")
            return False

    async def get_user_info(self):
        """Get user info (age, sex, weight, height)"""
        print("\n📥 Requesting user info...")
        self.response_received.clear()
        await self.send_command(self.CMD_GET_USER_INFO)
        
        try:
            await asyncio.wait_for(self.response_received.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            print("⚠️  No response (timeout)")

    async def get_hr_zone(self):
        """Get HR zone settings"""
        print("\n📥 Requesting HR zone settings...")
        self.response_received.clear()
        # SDK: sendCommand((byte) 70, 0)  -> single 0 byte param
        await self.send_command(self.CMD_GET_HR_ZONE, [0x00])
        
        try:
            await asyncio.wait_for(self.response_received.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            print("⚠️  No response (timeout)")

    async def get_max_hr(self):
        """Get max HR setting"""
        print("\n📥 Requesting max HR...")
        self.response_received.clear()
        await self.send_command(self.CMD_GET_MAX_HR, [0x00, 0x06])
        
        try:
            await asyncio.wait_for(self.response_received.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            print("⚠️  No response (timeout)")

    async def get_utc_alert(self):
        """Get UTC time and alarm status"""
        print("\n📥 Requesting UTC + alarm status...")
        self.response_received.clear()
        await self.send_command(self.CMD_GET_UTC_ALERT)
        
        try:
            await asyncio.wait_for(self.response_received.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            print("⚠️  No response (timeout)")

    async def set_alert_mode(self, mode='age'):
        """Set alarm mode (age-based or fixed)"""
        mode_byte = 0x01 if mode == 'age' else 0x00
        print(f"\n📤 Setting alarm mode: {mode.upper()}")
        await self.send_command(self.CMD_SET_ALERT_MODE, [mode_byte])
        await asyncio.sleep(0.5)
        print("✓ Command sent")

    async def set_max_hr(self, max_hr):
        """Set max HR"""
        print(f"\n📤 Setting max HR: {max_hr} bpm")
        await self.send_command(self.CMD_SET_MAX_HR, [0x00, 0x06, max_hr])
        await asyncio.sleep(0.5)
        print("✓ Command sent")

    async def set_hr_zone(self, min_hr, max_hr, goal_hr):
        """Set HR zone (min, max, goal)"""
        print(f"\n📤 Setting HR zone:")
        print(f"   Min:  {min_hr} bpm")
        print(f"   Max:  {max_hr} bpm")
        print(f"   Goal: {goal_hr} bpm")
        await self.send_command(self.CMD_SET_HR_ZONE, [0x01, min_hr, max_hr, goal_hr])
        await asyncio.sleep(0.5)
        print("✓ Command sent")

    def calculate_zones(self, age=None, hr_max=None):
        """Calculate HR zones based on age or max HR"""
        if hr_max is None:
            if age is None:
                age = self.user_age if self.user_age else 30
            hr_max = 220 - age
        
        zones = {
            'max_hr': hr_max,
            'age': age if age else (220 - hr_max),
            'rest': (0, int(hr_max * 0.5)),
            'fat_burn': (int(hr_max * 0.5), int(hr_max * 0.6)),
            'cardio': (int(hr_max * 0.6), int(hr_max * 0.7)),
            'intense': (int(hr_max * 0.7), int(hr_max * 0.85)),
            'maximum': (int(hr_max * 0.85), hr_max)
        }
        
        return zones

    def display_zones(self, zones):
        """Display HR zones"""
        print("\n" + "=" * 50)
        print("💓 HEART RATE ZONES")
        print("=" * 50)
        print(f"Based on: Age {zones['age']} → HR_max {zones['max_hr']} bpm\n")
        
        print(f"🔵 Zone 1 - Rest/Recovery")
        print(f"   < {zones['rest'][1]} bpm  (<50% max)")
        print(f"   Use: Cool-down, recovery\n")
        
        print(f"🟢 Zone 2 - Fat Burn")
        print(f"   {zones['fat_burn'][0]}-{zones['fat_burn'][1]} bpm  (50-60% max)")
        print(f"   Use: Weight loss, endurance base\n")
        
        print(f"🟡 Zone 3 - Cardio")
        print(f"   {zones['cardio'][0]}-{zones['cardio'][1]} bpm  (60-70% max)")
        print(f"   Use: General fitness, stamina\n")
        
        print(f"🟠 Zone 4 - Intense")
        print(f"   {zones['intense'][0]}-{zones['intense'][1]} bpm  (70-85% max)")
        print(f"   Use: Performance improvement\n")
        
        print(f"🔴 Zone 5 - Maximum")
        print(f"   {zones['maximum'][0]}-{zones['maximum'][1]} bpm  (85-100% max)")
        print(f"   Use: Intervals, sprints")
        print("=" * 50)

    async def disconnect(self):
        """Disconnect from device"""
        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                print("\n✓ Disconnected")
                self.is_connected = False
        except Exception as e:
            print(f"Disconnect error: {e}")

    async def run_read_only(self):
        """Read current settings"""
        try:
            if not await self.scan_and_connect():
                return
            
            if not await self.discover_services():
                await self.disconnect()
                return
            
            # Read all settings
            await self.get_user_info()
            await asyncio.sleep(1)
            
            await self.get_max_hr()
            await asyncio.sleep(1)
            
            await self.get_hr_zone()
            await asyncio.sleep(1)
            
            await self.get_utc_alert()
            await asyncio.sleep(1)
            
            # Display calculated zones if we have age
            if self.user_age:
                zones = self.calculate_zones(self.user_age)
                self.display_zones(zones)
            
            await self.disconnect()
            
        except Exception as e:
            print(f"\nError: {e}")
            await self.disconnect()

    async def run_configure(self, mode, age=None, max_hr=None, zone=None):
        """Configure HR settings"""
        try:
            if not await self.scan_and_connect():
                return
            
            if not await self.discover_services():
                await self.disconnect()
                return
            
            # Get current user info
            await self.get_user_info()
            await asyncio.sleep(1)
            
            # Set alarm mode
            await self.set_alert_mode(mode)
            await asyncio.sleep(1)
            
            # Set max HR if specified
            if max_hr:
                await self.set_max_hr(max_hr)
                await asyncio.sleep(1)
            
            # Set zone if specified
            if zone:
                min_hr, max_hr_zone, goal_hr = zone
                await self.set_hr_zone(min_hr, max_hr_zone, goal_hr)
                await asyncio.sleep(1)
            
            # Display zones
            if age or self.user_age:
                zones = self.calculate_zones(age if age else self.user_age, max_hr)
                self.display_zones(zones)
            
            print("\n✓ Configuration complete")
            
            await self.disconnect()
            
        except Exception as e:
            print(f"\nError: {e}")
            await self.disconnect()


async def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description='CL837 HR Zones & Alarms Configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read current settings
  python hr_zones.py --read
  
  # Set age-based mode
  python hr_zones.py --mode age
  
  # Set fixed limits with custom max HR
  python hr_zones.py --mode fixed --max 180
  
  # Set training zone (fat burn: 50-60%)
  python hr_zones.py --age 35 --zone fatburn
  
  # Set custom zone
  python hr_zones.py --zone-custom 120 150 135
  
  # Calculate zones for age (no device needed)
  python hr_zones.py --calc-only --age 30
        """
    )
    
    parser.add_argument('--read', action='store_true',
                        help='Read current HR settings from device')
    parser.add_argument('--mode', choices=['age', 'fixed'],
                        help='Set alarm mode (age-based or fixed limits)')
    parser.add_argument('--max', type=int, metavar='BPM',
                        help='Set max HR (bpm)')
    parser.add_argument('--age', type=int,
                        help='User age (for calculations)')
    parser.add_argument('--zone', choices=['fatburn', 'cardio', 'intense'],
                        help='Set predefined training zone')
    parser.add_argument('--zone-custom', nargs=3, type=int, metavar=('MIN', 'MAX', 'GOAL'),
                        help='Set custom zone (min max goal in bpm)')
    parser.add_argument('--calc-only', action='store_true',
                        help='Only calculate zones (no device connection)')
    
    args = parser.parse_args()
    
    # Calc-only mode (no device)
    if args.calc_only:
        if not args.age:
            print("Error: --age required for --calc-only")
            return
        
        manager = CL837HRZoneManager()
        zones = manager.calculate_zones(age=args.age, hr_max=args.max)
        manager.display_zones(zones)
        return
    
    # Read mode
    if args.read:
        print("=" * 70)
        print("CL837 HR Zones - Read Settings")
        print("=" * 70)
        
        manager = CL837HRZoneManager()
        await manager.run_read_only()
        return
    
    # Configure mode
    if args.mode or args.max or args.zone or args.zone_custom:
        print("=" * 70)
        print("CL837 HR Zones - Configuration")
        print("=" * 70)
        
        manager = CL837HRZoneManager()
        
        # Prepare zone tuple if needed
        zone_tuple = None
        if args.zone_custom:
            zone_tuple = tuple(args.zone_custom)
        elif args.zone and args.age:
            zones = manager.calculate_zones(age=args.age)
            if args.zone == 'fatburn':
                zone_tuple = (zones['fat_burn'][0], zones['fat_burn'][1], 
                             int((zones['fat_burn'][0] + zones['fat_burn'][1]) / 2))
            elif args.zone == 'cardio':
                zone_tuple = (zones['cardio'][0], zones['cardio'][1],
                             int((zones['cardio'][0] + zones['cardio'][1]) / 2))
            elif args.zone == 'intense':
                zone_tuple = (zones['intense'][0], zones['intense'][1],
                             int((zones['intense'][0] + zones['intense'][1]) / 2))
        
        await manager.run_configure(
            mode=args.mode if args.mode else 'age',
            age=args.age,
            max_hr=args.max,
            zone=zone_tuple
        )
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
