"""
CL837 3D Accelerometer History Download
Accelerometer data (X/Y/Z) history retrieval

Protocol based on decompiled Chileaf Android SDK:
- Command 0x77: Get 3D accelerometer history
- Data format: accX, accY, accZ values
"""
import asyncio
import time
import struct
import traceback
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL8373DMonitor:
    """CL837 3D Accelerometer History Monitor"""

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
        self.CMD_GET_3D_HISTORY = 0x77  # Get 3D accelerometer history

        # 3D data storage
        self.three_d_data = []
        self.three_d_complete = False

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
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def discover_services(self):
        """Discover BLE services and characteristics"""
        try:
            services = self.client.services
            for service in services:
                if service.uuid == self.CHILEAF_SERVICE_UUID:
                    for char in service.characteristics:
                        if char.uuid == self.CHILEAF_TX_UUID:
                            self.tx_char = char
                        elif char.uuid == self.CHILEAF_RX_UUID:
                            self.rx_char = char

            if self.tx_char and self.rx_char:
                print("✓ Services discovered")
                return True
            else:
                print("✗ Required characteristics not found")
                return False
        except Exception as e:
            print(f"Service discovery error: {e}")
            return False

    async def set_utc_time(self):
        """Set device UTC time"""
        try:
            utc_time = int(time.time())
            packet = struct.pack('<BBI', self.CHILEAF_HEADER, self.CMD_SET_UTC, utc_time)
            checksum = ((0 - sum(packet[1:])) ^ 0x3A) & 0xFF
            packet += bytes([checksum])

            await self.client.write_gatt_char(self.tx_char, packet)
            print("✓ UTC time set")
            return True
        except Exception as e:
            print(f"UTC time set error: {e}")
            return False

    def notification_handler(self, sender, data):
        """Handle incoming BLE notifications"""
        try:
            if len(data) < 3:
                return

            header = data[0]
            if header != self.CHILEAF_HEADER:
                return

            cmd = data[1]
            payload = data[2:-1]  # Exclude checksum
            
            # Debug: print raw data
            print(f"DEBUG: cmd=0x{cmd:02X}, payload_len={len(payload)}, payload={payload.hex() if payload else 'empty'}")

            if cmd == self.CMD_GET_3D_HISTORY:
                self.parse_3d_data(payload)

        except Exception as e:
            print(f"Notification handler error: {e}")

    def parse_3d_data(self, payload):
        """Parse 3D accelerometer data"""
        try:
            print(f"DEBUG parse_3d_data: payload_len={len(payload)}")
            
            if len(payload) < 12:  # 3 int32 values
                print(f"DEBUG: payload too short ({len(payload)} < 12)")
                return

            # Parse X, Y, Z accelerometer values (signed 32-bit integers)
            acc_x = struct.unpack('<i', payload[0:4])[0]
            acc_y = struct.unpack('<i', payload[4:8])[0]
            acc_z = struct.unpack('<i', payload[8:12])[0]

            # Calculate timestamp (current time for this sample)
            timestamp = datetime.now()

            self.three_d_data.append({
                'timestamp': timestamp,
                'datetime': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'acc_x': acc_x,
                'acc_y': acc_y,
                'acc_z': acc_z,
                'magnitude': (acc_x**2 + acc_y**2 + acc_z**2)**0.5
            })

            print(f"  3D: X={acc_x:6d}, Y={acc_y:6d}, Z={acc_z:6d}, Mag={self.three_d_data[-1]['magnitude']:6.1f}")

        except Exception as e:
            print(f"3D data parse error: {e}")
            import traceback
            traceback.print_exc()

    async def get_3d_history(self):
        """Request 3D accelerometer history"""
        try:
            print("\nRequesting 3D accelerometer history...")

            # Start notifications (use TX char for notifications)
            await self.client.start_notify(self.tx_char, self.notification_handler)

            # Send command
            packet = struct.pack('<BBB', self.CHILEAF_HEADER, self.CMD_GET_3D_HISTORY, 0x00)
            checksum = ((0 - sum(packet[1:])) ^ 0x3A) & 0xFF
            packet += bytes([checksum])

            await self.client.write_gatt_char(self.tx_char, packet)

            # Wait for data (adjust timeout as needed)
            timeout = 30
            start_time = time.time()
            while time.time() - start_time < timeout:
                if len(self.three_d_data) > 0:
                    await asyncio.sleep(1)  # Wait a bit more for all data
                    break
                await asyncio.sleep(0.1)

            await self.client.stop_notify(self.tx_char)

            print(f"✓ Received {len(self.three_d_data)} 3D data points")
            self.three_d_complete = True

        except Exception as e:
            print(f"3D history request error: {e}")

    def export_to_csv(self):
        """Export 3D data to CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"3d_history_{timestamp}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['timestamp', 'datetime', 'acc_x', 'acc_y', 'acc_z', 'magnitude'])

                for data in self.three_d_data:
                    writer.writerow([
                        data['timestamp'].isoformat(),
                        data['datetime'],
                        data['acc_x'],
                        data['acc_y'],
                        data['acc_z'],
                        f"{data['magnitude']:.1f}"
                    ])

            print(f"\n✓ 3D data exported to: {filename}")
            print(f"  Total data points: {len(self.three_d_data)}")

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

            # 4. Get 3D history
            await self.get_3d_history()

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
    print("CL837 3D Accelerometer History Download")
    print("=" * 60)

    monitor = CL8373DMonitor()
    await monitor.run()

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())