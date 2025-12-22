"""
CL837 Temperature Monitor
Real-time temperature monitoring (environment, wrist, body)

Protocol: Chileaf custom protocol (command 0x38)
Data: Temperature values × 10 in big-endian format

Based on decompiled Chileaf SDK:
- iOS: HeartBLEDevice.m (buffer_[2] == 0x38)
- Android: WearReceivedDataCallback.java (iIntValue == 56)
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime
from collections import deque
from bleak import BleakClient, BleakScanner


class CL837TemperatureMonitor:
    """CL837 Temperature Monitor - Real-time temperature from wearable"""
    
    def __init__(self, buffer_size=100):
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
        self.CMD_TEMPERATURE = 0x38
        
        # Characteristics
        self.tx_char = None
        self.rx_char = None
        
        # Temperature data storage
        self.buffer_size = buffer_size
        self.temp_history = deque(maxlen=buffer_size)
        
        # Latest readings
        self.latest_temp = {
            'environment': None,
            'wrist': None,
            'body': None,
            'timestamp': None
        }
        
        # Recording
        self.recording = False
        self.recorded_data = []
        
        # Monitoring control
        self.monitoring = False
        
        # Statistics
        self.readings_count = 0

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
            
            # Temperature data (0x38 = 56 decimal)
            if cmd == self.CMD_TEMPERATURE and len(data) >= 9:
                self.parse_temperature(data)
                
        except Exception as e:
            print(f"Notification parse error: {e}")

    def parse_temperature(self, data):
        """Parse temperature data from notification"""
        try:
            timestamp = datetime.now()
            
            # Big-endian 2-byte integers, divided by 10 for °C
            env_raw = (data[3] << 8) | data[4]
            wrist_raw = (data[5] << 8) | data[6]
            body_raw = (data[7] << 8) | data[8]
            
            environment = env_raw / 10.0
            wrist = wrist_raw / 10.0
            body = body_raw / 10.0
            
            self.latest_temp = {
                'environment': environment,
                'wrist': wrist,
                'body': body,
                'timestamp': timestamp
            }
            
            # Add to history
            self.temp_history.append(self.latest_temp.copy())
            self.readings_count += 1
            
            # Record if active
            if self.recording:
                self.recorded_data.append({
                    'timestamp': timestamp.isoformat(),
                    'environment': environment,
                    'wrist': wrist,
                    'body': body,
                    'env_raw': env_raw,
                    'wrist_raw': wrist_raw,
                    'body_raw': body_raw
                })
            
        except Exception as e:
            print(f"Parse temperature error: {e}")

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

    def get_statistics(self):
        """Calculate statistics from temperature history"""
        if not self.temp_history:
            return None
        
        import statistics
        
        env_values = [t['environment'] for t in self.temp_history if t['environment']]
        wrist_values = [t['wrist'] for t in self.temp_history if t['wrist']]
        body_values = [t['body'] for t in self.temp_history if t['body']]
        
        stats = {}
        
        if env_values:
            stats['environment'] = {
                'min': min(env_values),
                'max': max(env_values),
                'mean': statistics.mean(env_values),
                'stdev': statistics.stdev(env_values) if len(env_values) > 1 else 0
            }
        
        if wrist_values:
            stats['wrist'] = {
                'min': min(wrist_values),
                'max': max(wrist_values),
                'mean': statistics.mean(wrist_values),
                'stdev': statistics.stdev(wrist_values) if len(wrist_values) > 1 else 0
            }
        
        if body_values:
            stats['body'] = {
                'min': min(body_values),
                'max': max(body_values),
                'mean': statistics.mean(body_values),
                'stdev': statistics.stdev(body_values) if len(body_values) > 1 else 0
            }
        
        return stats

    def interpret_body_temp(self, temp):
        """Interpret body temperature"""
        if temp is None:
            return "No data"
        
        if temp < 35.0:
            return "⚠ Low (hypothermia)"
        elif temp < 36.1:
            return "⚠ Below normal"
        elif temp < 37.2:
            return "✓ Normal"
        elif temp < 38.0:
            return "⚠ Slightly elevated"
        elif temp < 39.0:
            return "⚠ Fever"
        else:
            return "⚠ High fever"

    def display_dashboard(self):
        """Display real-time temperature dashboard"""
        print("\033[2J\033[H", end='')  # Clear screen
        
        print("=" * 70)
        print(f"CL837 TEMPERATURE MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Current readings
        if self.latest_temp['timestamp']:
            age = (datetime.now() - self.latest_temp['timestamp']).seconds
            freshness = "🟢 Live" if age < 20 else "🟡 Stale" if age < 60 else "🔴 Old"
            
            print(f"\n🌡️  CURRENT READINGS ({freshness}, {age}s ago)")
            print("-" * 40)
            
            env = self.latest_temp['environment']
            wrist = self.latest_temp['wrist']
            body = self.latest_temp['body']
            
            if env is not None:
                print(f"   🏠 Environment:  {env:.1f} °C")
            
            if wrist is not None:
                print(f"   ✋ Wrist:        {wrist:.1f} °C")
            
            if body is not None:
                interpretation = self.interpret_body_temp(body)
                print(f"   🩺 Body:         {body:.1f} °C  ({interpretation})")
        else:
            print(f"\n🌡️  CURRENT READINGS")
            print("-" * 40)
            print("   Waiting for data... (updates every ~15s)")
        
        # Recording status
        if self.recording:
            print(f"\n🔴 RECORDING: {len(self.recorded_data)} samples")
        
        # Statistics
        stats = self.get_statistics()
        if stats:
            print(f"\n📊 STATISTICS ({len(self.temp_history)} readings)")
            print("-" * 40)
            
            if 'environment' in stats:
                s = stats['environment']
                print(f"   Environment: {s['mean']:.1f}°C (±{s['stdev']:.1f}) [{s['min']:.1f} - {s['max']:.1f}]")
            
            if 'wrist' in stats:
                s = stats['wrist']
                print(f"   Wrist:       {s['mean']:.1f}°C (±{s['stdev']:.1f}) [{s['min']:.1f} - {s['max']:.1f}]")
            
            if 'body' in stats:
                s = stats['body']
                print(f"   Body:        {s['mean']:.1f}°C (±{s['stdev']:.1f}) [{s['min']:.1f} - {s['max']:.1f}]")
        
        # Info
        print(f"\n📈 Total readings: {self.readings_count}")
        print(f"   Buffer: {len(self.temp_history)}/{self.buffer_size}")
        
        print("\n" + "=" * 70)
        print("Commands: [R]ecord start/stop  [S]ave CSV  [C]lear  [Q]uit")
        print("=" * 70)

    def start_recording(self):
        """Start recording temperature data"""
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
        filename = f"temperature_data_{device_name}_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp', 'environment', 'wrist', 'body',
                    'env_raw', 'wrist_raw', 'body_raw'
                ])
                writer.writeheader()
                writer.writerows(self.recorded_data)
            
            print(f"\n✓ Saved to {filename}")
            return filename
            
        except Exception as e:
            print(f"\n✗ Save error: {e}")
            return None

    def clear_history(self):
        """Clear temperature history"""
        self.temp_history.clear()
        self.readings_count = 0
        print("\n✓ History cleared")

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
                elif cmd == 's':
                    self.save_to_csv()
                elif cmd == 'c':
                    self.clear_history()
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
            print("Starting temperature monitoring...")
            print("Temperature data arrives every ~15 seconds automatically")
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
    print("CL837 Temperature Monitor")
    print("Real-time environment, wrist, and body temperature")
    print("=" * 70)
    
    monitor = CL837TemperatureMonitor(buffer_size=200)
    await monitor.run()
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
