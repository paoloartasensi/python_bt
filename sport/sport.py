"""
CL837 Sport Activity Monitor
Real-time steps, distance, and calories tracking

Protocol: Chileaf custom protocol
- Command 0x15: Real-time sport data (auto-push ~15s)
- Command 0x16: 7-day sport history

Based on decompiled Chileaf SDK:
- iOS: HeartBLEDevice.m (buffer_[2] == 0x15)
- Android: WearReceivedDataCallback.java (iIntValue == 21)
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime, timedelta
from bleak import BleakClient, BleakScanner


class CL837SportMonitor:
    """CL837 Sport Activity Monitor - Steps, Distance, Calories"""
    
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
        self.CMD_SPORT_REALTIME = 0x15  # 21 decimal
        self.CMD_SPORT_HISTORY = 0x16   # 22 decimal
        
        # Characteristics
        self.tx_char = None
        self.rx_char = None
        
        # Latest reading (solo ultimo valore)
        self.latest_sport = None
        
        # 7-day history
        self.history_7day = []
        self.history_complete = False
        
        # Recording
        self.recording = False
        self.recorded_data = []
        
        # Monitoring control
        self.monitoring = False
        
        # Session tracking
        self.readings_count = 0
        self.session_start = None
        self.session_start_data = None

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
            
            if not self.tx_char:
                print("✗ TX characteristic not found")
                return False
            
            # Enable notifications
            await self.client.start_notify(self.tx_char, self.notification_handler)
            print("  ✓ Notifications enabled")
            
            return True
            
        except Exception as e:
            print(f"Service discovery error: {e}")
            traceback.print_exc()
            return False

    def notification_handler(self, sender, data):
        """Handle Chileaf notifications"""
        try:
            if len(data) < 4:
                return
            
            header = data[0]
            cmd = data[2]
            
            if header != self.CHILEAF_HEADER:
                return
            
            # Real-time sport data (0x15 = 21 decimal)
            if cmd == self.CMD_SPORT_REALTIME and len(data) >= 12:
                self.parse_sport_realtime(data)
            
            # 7-day history response (0x16 = 22 decimal)
            elif cmd == self.CMD_SPORT_HISTORY and len(data) >= 4:
                self.parse_sport_history(data)
                
        except Exception as e:
            print(f"Notification parse error: {e}")

    def parse_sport_realtime(self, data):
        """Parse real-time sport data (cmd 0x15)"""
        try:
            timestamp = datetime.now()
            
            # Big-endian 3-byte integers
            steps = (data[3] << 16) | (data[4] << 8) | data[5]
            distance_cm = (data[6] << 16) | (data[7] << 8) | data[8]
            calories_raw = (data[9] << 16) | (data[10] << 8) | data[11]
            
            self.latest_sport = {
                'steps': steps,
                'distance_cm': distance_cm,
                'distance_m': distance_cm / 100,
                'distance_km': distance_cm / 100000,
                'calories_raw': calories_raw,
                'calories_kcal': calories_raw / 10.0,
                'timestamp': timestamp
            }
            
            # Initialize session start if first reading
            if self.session_start is None:
                self.session_start = timestamp
                self.session_start_data = self.latest_sport.copy()
            
            self.readings_count += 1
            
            # Record if active
            if self.recording:
                self.recorded_data.append({
                    'timestamp': timestamp.isoformat(),
                    'steps': steps,
                    'distance_cm': distance_cm,
                    'distance_m': distance_cm / 100,
                    'calories_kcal': calories_raw / 10.0
                })
            
        except Exception as e:
            print(f"Parse sport realtime error: {e}")

    def parse_sport_history(self, data):
        """Parse 7-day sport history (cmd 0x16)"""
        try:
            # Check for end marker
            if len(data) >= 7:
                utc_check = (data[3] << 24) | (data[4] << 16) | (data[5] << 8) | data[6]
                if utc_check == 0xFFFFFFFF:
                    self.history_complete = True
                    return
            
            offset = 3
            while offset + 10 <= len(data) - 1:  # -1 for checksum
                utc = (data[offset] << 24) | (data[offset+1] << 16) | \
                      (data[offset+2] << 8) | data[offset+3]
                steps = (data[offset+4] << 16) | (data[offset+5] << 8) | data[offset+6]
                calories = (data[offset+7] << 16) | (data[offset+8] << 8) | data[offset+9]
                
                if utc != 0xFFFFFFFF:
                    self.history_7day.append({
                        'utc': utc,
                        'date': datetime.fromtimestamp(utc),
                        'steps': steps,
                        'calories_kcal': calories / 10.0
                    })
                
                offset += 10
            
        except Exception as e:
            print(f"Parse sport history error: {e}")

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

    async def set_utc_time(self):
        """Set device UTC time"""
        try:
            print("\nSynchronizing UTC time...")
            utc_timestamp = int(time.time())
            utc_bytes = [
                (utc_timestamp >> 24) & 0xFF,
                (utc_timestamp >> 16) & 0xFF,
                (utc_timestamp >> 8) & 0xFF,
                utc_timestamp & 0xFF
            ]
            await self.send_command(self.CMD_SET_UTC, utc_bytes)
            await asyncio.sleep(0.5)
            print("  ✓ UTC synchronized")
            return True
        except Exception as e:
            print(f"Set UTC error: {e}")
            return False

    async def get_7day_history(self):
        """Request 7-day sport history"""
        try:
            print("\nRequesting 7-day history...")
            self.history_7day = []
            self.history_complete = False
            
            await self.send_command(self.CMD_SPORT_HISTORY)
            
            # Wait for response
            timeout = 5
            while not self.history_complete and timeout > 0:
                await asyncio.sleep(0.5)
                timeout -= 0.5
            
            if self.history_7day:
                print(f"  ✓ Received {len(self.history_7day)} days of history")
            else:
                print("  ⚠ No history data received")
            
            return self.history_7day
            
        except Exception as e:
            print(f"Get history error: {e}")
            return []

    def get_session_stats(self):
        """Calculate session statistics"""
        if not self.session_start_data or not self.latest_sport or not self.latest_sport['steps']:
            return None
        
        duration = datetime.now() - self.session_start
        
        steps_delta = self.latest_sport['steps'] - self.session_start_data['steps']
        distance_delta = self.latest_sport['distance_m'] - self.session_start_data['distance_m']
        calories_delta = self.latest_sport['calories_kcal'] - self.session_start_data['calories_kcal']
        
        # Steps per minute
        minutes = duration.total_seconds() / 60
        steps_per_min = steps_delta / minutes if minutes > 0 else 0
        
        # Calories per hour
        hours = duration.total_seconds() / 3600
        cal_per_hour = calories_delta / hours if hours > 0 else 0
        
        return {
            'duration': duration,
            'duration_str': str(duration).split('.')[0],
            'steps_delta': steps_delta,
            'distance_delta_m': distance_delta,
            'calories_delta': calories_delta,
            'steps_per_min': steps_per_min,
            'cal_per_hour': cal_per_hour
        }

    def format_distance(self, meters):
        """Format distance nicely"""
        if meters >= 1000:
            return f"{meters/1000:.2f} km"
        else:
            return f"{meters:.0f} m"

    def display_dashboard(self):
        """Display real-time sport dashboard"""
        print("\033[2J\033[H", end='')  # Clear screen
        
        print("=" * 70)
        print(f"CL837 SPORT ACTIVITY MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Current readings
        if self.latest_sport and self.latest_sport['timestamp']:
            age = (datetime.now() - self.latest_sport['timestamp']).seconds
            freshness = "🟢 Live" if age < 20 else "🟡 Stale" if age < 60 else "🔴 Old"
            
            print(f"\n📊 TODAY'S ACTIVITY ({freshness}, {age}s ago)")
            print("-" * 50)
            
            steps = self.latest_sport['steps']
            dist_m = self.latest_sport['distance_m']
            cal = self.latest_sport['calories_kcal']
            
            # Steps with progress bar (goal: 10000)
            goal = 10000
            progress = min(steps / goal * 100, 100)
            bar_len = 20
            filled = int(bar_len * progress / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            
            print(f"   👣 Steps:     {steps:,}")
            print(f"      Goal:      [{bar}] {progress:.0f}% of {goal:,}")
            print(f"   🚶 Distance:  {self.format_distance(dist_m)}")
            print(f"   🔥 Calories:  {cal:.1f} kcal")
        else:
            print(f"\n📊 TODAY'S ACTIVITY")
            print("-" * 50)
            print("   Waiting for data... (updates every ~15s)")
        
        # Session stats
        session = self.get_session_stats()
        if session:
            print(f"\n⏱️  SESSION STATS (since connection)")
            print("-" * 50)
            print(f"   Duration:     {session['duration_str']}")
            print(f"   Steps:        +{session['steps_delta']:,}")
            print(f"   Distance:     +{self.format_distance(session['distance_delta_m'])}")
            print(f"   Calories:     +{session['calories_delta']:.1f} kcal")
            print(f"   Pace:         {session['steps_per_min']:.1f} steps/min")
            print(f"   Burn rate:    {session['cal_per_hour']:.1f} kcal/hour")
        
        # Recording status
        if self.recording:
            print(f"\n🔴 RECORDING: {len(self.recorded_data)} samples")
        
        # 7-day history if available
        if self.history_7day:
            print(f"\n📅 7-DAY HISTORY")
            print("-" * 50)
            total_steps = 0
            total_cal = 0
            for day in self.history_7day[-7:]:
                date_str = day['date'].strftime('%a %d/%m')
                print(f"   {date_str}: {day['steps']:>6,} steps, {day['calories_kcal']:>6.1f} kcal")
                total_steps += day['steps']
                total_cal += day['calories_kcal']
            print(f"   {'─' * 40}")
            print(f"   Total:    {total_steps:>6,} steps, {total_cal:>6.1f} kcal")
            print(f"   Average:  {total_steps//len(self.history_7day):>6,} steps/day")
        
        print(f"\n📈 Readings: {self.readings_count}")
        
        print("\n" + "=" * 70)
        print("Commands: [R]ecord  [H]istory 7-day  [S]ave CSV  [C]lear  [Q]uit")
        print("=" * 70)

    def start_recording(self):
        """Start recording sport data"""
        self.recording = True
        self.recorded_data = []
        print("\n🔴 Recording started...")

    def stop_recording(self):
        """Stop recording"""
        self.recording = False
        print(f"\n⬛ Recording stopped. {len(self.recorded_data)} samples collected.")

    def save_to_csv(self):
        """Save recorded data to CSV"""
        if not self.recorded_data:
            print("\n⚠ No recorded data to save")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        device_name = self.device.name.replace("-", "_") if self.device else "unknown"
        filename = f"sport_data_{device_name}_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp', 'steps', 'distance_cm', 'distance_m', 'calories_kcal'
                ])
                writer.writeheader()
                writer.writerows(self.recorded_data)
            
            print(f"\n✓ Saved to {filename}")
            return filename
            
        except Exception as e:
            print(f"\n✗ Save error: {e}")
            return None

    def clear_session(self):
        """Clear session data"""
        self.latest_sport = None
        self.readings_count = 0
        self.session_start = None
        self.session_start_data = None
        print("\n✓ Session cleared")

    async def handle_input(self):
        """Handle keyboard input (non-blocking)"""
        import sys
        import select
        
        if sys.platform != 'win32':
            if select.select([sys.stdin], [], [], 0)[0]:
                cmd = sys.stdin.readline().strip().lower()
                if cmd == 'r':
                    if self.recording:
                        self.stop_recording()
                    else:
                        self.start_recording()
                elif cmd == 'h':
                    await self.get_7day_history()
                elif cmd == 's':
                    self.save_to_csv()
                elif cmd == 'c':
                    self.clear_session()
                elif cmd == 'q':
                    self.monitoring = False

    async def monitor_loop(self):
        """Continuous monitoring loop"""
        self.monitoring = True
        
        try:
            while self.monitoring:
                self.display_dashboard()
                await self.handle_input()
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            self.monitoring = False

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
            if self.rx_char:
                await self.set_utc_time()
            
            # 4. Start monitoring
            print("\n" + "=" * 70)
            print("Starting sport activity monitoring...")
            print("Data arrives automatically every ~15 seconds")
            print("=" * 70)
            await asyncio.sleep(2)
            
            await self.monitor_loop()
            
            # 5. Save if recording
            if self.recording and self.recorded_data:
                save = input("\nSave recorded data? (y/n): ").lower()
                if save == 'y':
                    self.save_to_csv()
            
            # 6. Disconnect
            await self.disconnect()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            if self.recorded_data:
                save = input("\nSave recorded data? (y/n): ").lower()
                if save == 'y':
                    self.save_to_csv()
            await self.disconnect()
        except Exception as e:
            print(f"\nError: {e}")
            traceback.print_exc()
            await self.disconnect()


async def main():
    """Entry point"""
    print("=" * 70)
    print("CL837 Sport Activity Monitor")
    print("Real-time steps, distance, and calories tracking")
    print("=" * 70)
    
    monitor = CL837SportMonitor()
    await monitor.run()
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
