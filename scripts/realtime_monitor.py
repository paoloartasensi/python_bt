"""
CL837 Real-Time Monitor
Live monitoring of HR, health metrics, HRV, and accelerometer data
Based on standard BLE Heart Rate Service + Chileaf custom notifications
"""
import asyncio
import time
import struct
import traceback
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837RealtimeMonitor:
    """CL837 Real-Time Data Monitor"""
    
    def __init__(self):
        # BLE Connection
        self.client = None
        self.device = None
        self.is_connected = False
        
        # Standard BLE Services
        self.HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
        self.HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
        
        # Chileaf Protocol
        self.CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_HEADER = 0xFF
        
        # Commands
        self.CMD_SET_UTC = 0x08
        self.CMD_ACCELEROMETER = 0x0C  # 12 in decimal
        
        # Real-time data
        self.latest_hr = None
        self.latest_sport = {}
        self.latest_health = {}
        self.latest_accel = {}
        self.rr_intervals = []
        
        # Characteristics
        self.hr_char = None
        self.tx_char = None
        self.rx_char = None
        
        # Monitoring control
        self.monitoring = False

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
            
            # Find standard HR service
            hr_service = None
            for service in services:
                if service.uuid.lower() == self.HR_SERVICE_UUID.lower():
                    hr_service = service
                    print(f"\n✓ Found Heart Rate Service: {service.uuid}")
                    break
            
            if hr_service:
                for char in hr_service.characteristics:
                    if char.uuid.lower() == self.HR_MEASUREMENT_UUID.lower():
                        self.hr_char = char
                        print(f"  ✓ HR Measurement Char: {char.uuid}")
                        break
            
            # Find Chileaf service
            chileaf_service = None
            for service in services:
                if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                    chileaf_service = service
                    print(f"✓ Found Chileaf Service: {service.uuid}")
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
            
            # Enable notifications
            if self.hr_char:
                await self.client.start_notify(self.hr_char, self.hr_notification_handler)
                print("  ✓ HR notifications enabled")
            
            await self.client.start_notify(self.tx_char, self.chileaf_notification_handler)
            print("  ✓ Chileaf notifications enabled")
            
            return True
            
        except Exception as e:
            print(f"Service discovery error: {e}")
            traceback.print_exc()
            return False

    def hr_notification_handler(self, sender, data):
        """Handle standard BLE HR notifications"""
        try:
            # Parse Heart Rate Measurement
            # Byte 0: Flags
            flags = data[0]
            hr_format = flags & 0x01  # 0 = uint8, 1 = uint16
            has_contact = (flags & 0x06) >> 1
            has_energy = flags & 0x08
            has_rr = flags & 0x10
            
            # Byte 1 (or 1-2): Heart Rate
            if hr_format == 0:
                hr = data[1]
                offset = 2
            else:
                hr = struct.unpack('<H', data[1:3])[0]
                offset = 3
            
            self.latest_hr = hr
            
            # Parse RR intervals if present
            if has_rr and len(data) > offset:
                self.rr_intervals = []
                while offset < len(data) - 1:
                    rr = struct.unpack('<H', data[offset:offset+2])[0]
                    self.rr_intervals.append(rr * 1000 / 1024)  # Convert to ms
                    offset += 2
            
        except Exception as e:
            print(f"HR parse error: {e}")

    def chileaf_notification_handler(self, sender, data):
        """Handle Chileaf custom notifications"""
        try:
            if len(data) < 4:
                return
            
            header = data[0]
            length = data[1]
            cmd = data[2]
            
            if header != self.CHILEAF_HEADER:
                return
            
            # Sport data (step, distance, calorie)
            if cmd == 0x01 and len(data) >= 15:
                self.parse_sport_data(data)
            
            # Health data (VO2Max, breath rate, emotion, stress, stamina, HRV)
            elif cmd == 0x02 and len(data) >= 27:
                self.parse_health_data(data)
            
            # Accelerometer data
            elif cmd == self.CMD_ACCELEROMETER and len(data) >= 9:
                self.parse_accelerometer_data(data)
            
            # UTC sync response
            elif cmd == self.CMD_SET_UTC:
                pass  # Silent
                
        except Exception as e:
            print(f"Chileaf parse error: {e}")

    def parse_sport_data(self, data):
        """Parse sport/activity data"""
        try:
            # Format: [header, len, cmd, step(4), distance(4), calorie(4)]
            step_bytes = data[3:7]
            dist_bytes = data[7:11]
            cal_bytes = data[11:15]
            
            steps = struct.unpack('>I', bytes(step_bytes))[0]
            distance = struct.unpack('>I', bytes(dist_bytes))[0]
            calories = struct.unpack('>I', bytes(cal_bytes))[0]
            
            self.latest_sport = {
                'steps': steps,
                'distance_m': distance,
                'calories': calories,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Parse sport error: {e}")

    def parse_health_data(self, data):
        """Parse health metrics data"""
        try:
            # Format based on BodyHealthCallback
            # [header, len, cmd, vo2max, breath_rate, emotion, stress%, stamina, tp(4), lf(4), hf(4)]
            vo2max = data[3]
            breath_rate = data[4]
            emotion = data[5]
            stress = data[6]
            stamina = data[7]
            
            # HRV components (as floats, 4 bytes each)
            tp_bytes = data[8:12]
            lf_bytes = data[12:16]
            hf_bytes = data[16:20]
            
            tp = struct.unpack('>f', bytes(tp_bytes))[0]
            lf = struct.unpack('>f', bytes(lf_bytes))[0]
            hf = struct.unpack('>f', bytes(hf_bytes))[0]
            
            # Interpret emotion level (like Android app)
            if emotion < 30:
                emotion_label = "Relaxed"
            elif emotion < 60:
                emotion_label = "Normal"
            else:
                emotion_label = "Stressed"
            
            # Interpret stamina (like Android app)
            stamina_labels = {0: "Low", 1: "Normal", 2: "High"}
            stamina_label = stamina_labels.get(stamina, f"Code:{stamina}")
            
            # Interpret VO2 Max fitness level
            if vo2max < 30:
                vo2_label = "Poor"
            elif vo2max < 40:
                vo2_label = "Fair"
            elif vo2max < 50:
                vo2_label = "Good"
            else:
                vo2_label = "Excellent"
            
            self.latest_health = {
                'vo2max': vo2max,
                'vo2max_label': vo2_label,
                'breath_rate': breath_rate,
                'emotion': emotion,
                'emotion_label': emotion_label,
                'stress_percent': stress,
                'stamina': stamina,
                'stamina_label': stamina_label,
                'hrv_tp': tp,
                'hrv_lf': lf,
                'hrv_hf': hf,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Parse health error: {e}")

    def parse_accelerometer_data(self, data):
        """Parse accelerometer data"""
        try:
            # Format: [header, len, cmd, x(2), y(2), z(2)]
            x_bytes = data[3:5]
            y_bytes = data[5:7]
            z_bytes = data[7:9]
            
            x = struct.unpack('>h', bytes(x_bytes))[0]  # signed int16
            y = struct.unpack('>h', bytes(y_bytes))[0]
            z = struct.unpack('>h', bytes(z_bytes))[0]
            
            self.latest_accel = {
                'x': x,
                'y': y,
                'z': z,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Parse accel error: {e}")

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
            print("  ✓ UTC synchronized")
            
            return True
            
        except Exception as e:
            print(f"Set UTC error: {e}")
            return False

    def display_dashboard(self):
        """Display real-time dashboard"""
        # Clear screen (cross-platform)
        print("\033[2J\033[H", end='')
        
        print("=" * 70)
        print(f"CL837 REAL-TIME MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Heart Rate
        if self.latest_hr is not None:
            print(f"\n❤️  HEART RATE: {self.latest_hr} bpm")
            if self.rr_intervals:
                print(f"   RR Intervals: {[f'{rr:.0f}ms' for rr in self.rr_intervals[-5:]]}")
        else:
            print(f"\n❤️  HEART RATE: --")
        
        # Sport/Activity
        if self.latest_sport:
            print(f"\n🏃 ACTIVITY:")
            print(f"   Steps: {self.latest_sport['steps']:,}")
            print(f"   Distance: {self.latest_sport['distance_m']}m ({self.latest_sport['distance_m']/1000:.2f}km)")
            print(f"   Calories: {self.latest_sport['calories']}")
        
        # Health Metrics
        if self.latest_health:
            print(f"\n💪 HEALTH METRICS:")
            print(f"   VO2 Max: {self.latest_health['vo2max']} ({self.latest_health['vo2max_label']})")
            print(f"   Breath Rate: {self.latest_health['breath_rate']} breaths/min")
            print(f"   Emotion: {self.latest_health['emotion_label']} (score: {self.latest_health['emotion']})")
            print(f"   Stress: {self.latest_health['stress_percent']}%")
            print(f"   Stamina: {self.latest_health['stamina_label']}")
            print(f"\n📊 HRV (Heart Rate Variability):")
            print(f"   TP: {self.latest_health['hrv_tp']:.2f}")
            print(f"   LF: {self.latest_health['hrv_lf']:.2f}")
            print(f"   HF: {self.latest_health['hrv_hf']:.2f}")
        
        # Accelerometer
        if self.latest_accel:
            print(f"\n📐 ACCELEROMETER (raw):")
            print(f"   X: {self.latest_accel['x']:5d}  Y: {self.latest_accel['y']:5d}  Z: {self.latest_accel['z']:5d}")
        
        print("\n" + "=" * 70)
        print("Press Ctrl+C to stop monitoring")
        print("=" * 70)

    async def monitor_loop(self):
        """Continuous monitoring loop"""
        self.monitoring = True
        
        try:
            while self.monitoring:
                self.display_dashboard()
                await asyncio.sleep(1)  # Update every second
                
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
            await self.set_utc_time()
            
            # 4. Start monitoring
            print("\nStarting real-time monitoring...")
            print("(Data will appear as the device sends updates)")
            await asyncio.sleep(2)
            
            await self.monitor_loop()
            
            # 5. Disconnect
            await self.disconnect()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            await self.disconnect()
        except Exception as e:
            print(f"\nError: {e}")
            traceback.print_exc()
            await self.disconnect()


async def main():
    """Entry point"""
    print("=" * 70)
    print("CL837 Real-Time Monitor")
    print("Live HR, Activity, Health Metrics, HRV, Accelerometer")
    print("=" * 70)
    
    monitor = CL837RealtimeMonitor()
    await monitor.run()
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
