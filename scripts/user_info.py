"""
CL837 User Info Manager
Get and set user information (age, sex, weight, height, user ID)
"""
import asyncio
import time
import struct
import traceback
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837UserInfoManager:
    """CL837 User Info Manager"""
    
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
        self.CMD_GET_USER_INFO = 0x03
        self.CMD_SET_USER_INFO = 0x04
        
        # User info storage
        self.user_info = None
        self.user_info_received = False
        
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
            
            # Response to GET_USER_INFO (0x03)
            if cmd == self.CMD_GET_USER_INFO:
                self.parse_user_info_response(data)
            
            # Response to SET_USER_INFO (0x04)
            elif cmd == self.CMD_SET_USER_INFO:
                print("  ✓ User info updated successfully")
            
            # Response to SET_UTC (0x08)
            elif cmd == self.CMD_SET_UTC:
                print("  ✓ UTC time synchronized")
                
        except Exception as e:
            print(f"Notification handler error: {e}")
            traceback.print_exc()

    def parse_user_info_response(self, data):
        """Parse user info response
        
        SDK format (WearReceivedDataCallback.java line 94):
        [0]=header, [1]=len, [2]=cmd, [3]=?, [4]=?, 
        [5]=age, [6]=sex, [7]=weight, [8]=height, [9-13]=userId(5 bytes)
        """
        try:
            # Format: [header, len, cmd, ?, ?, age, sex, weight, height, userId(5 bytes)]
            if len(data) >= 14:
                age = data[5]
                sex = data[6]  # 0 = male, 1 = female
                weight = data[7]  # kg
                height = data[8]  # cm
                
                # User ID (5 bytes, 40-bit integer) - big endian
                user_id_bytes = data[9:14]
                user_id = 0
                for byte in user_id_bytes:
                    user_id = (user_id << 8) | byte
                
                self.user_info = {
                    'age': age,
                    'sex': 'Male' if sex == 1 else 'Female',  # SDK: Male=1, Female=0
                    'sex_code': sex,
                    'weight_kg': weight,
                    'height_cm': height,
                    'user_id': user_id
                }
                
                self.user_info_received = True
                
                print("\n✓ User Info Retrieved:")
                print(f"  Age: {age} years")
                print(f"  Sex: {self.user_info['sex']}")
                print(f"  Weight: {weight} kg")
                print(f"  Height: {height} cm")
                print(f"  User ID: {user_id}")
                
        except Exception as e:
            print(f"Parse user info error: {e}")
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

    async def get_user_info(self):
        """Request user info from device"""
        try:
            print("\nRequesting user info...")
            self.user_info = None
            self.user_info_received = False
            
            await self.send_command(self.CMD_GET_USER_INFO, [0x00])
            
            # Wait for response (max 5 seconds)
            timeout = 5
            start_time = time.time()
            
            while not self.user_info_received:
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("✗ Timeout waiting for user info")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Get user info error: {e}")
            return False

    async def set_user_info(self, age, sex, weight_kg, height_cm, user_id=None):
        """Set user info on device"""
        try:
            print("\nSetting user info...")
            
            # If no user_id provided, generate random one or use existing
            if user_id is None:
                if self.user_info and 'user_id' in self.user_info:
                    user_id = self.user_info['user_id']
                else:
                    import random
                    user_id = random.randint(1, 0xFFFFFFFFFF)  # 40-bit max
            
            # Build command: [age, sex, weight, height, userId(5 bytes)]
            params = [
                age & 0xFF,
                sex & 0xFF,
                weight_kg & 0xFF,
                height_cm & 0xFF,
                # User ID - 5 bytes (40 bits)
                (user_id >> 32) & 0xFF,
                (user_id >> 24) & 0xFF,
                (user_id >> 16) & 0xFF,
                (user_id >> 8) & 0xFF,
                user_id & 0xFF
            ]
            
            await self.send_command(self.CMD_SET_USER_INFO, params)
            await asyncio.sleep(0.5)
            
            print(f"  Age: {age} years")
            print(f"  Sex: {'Male' if sex == 0 else 'Female'}")
            print(f"  Weight: {weight_kg} kg")
            print(f"  Height: {height_cm} cm")
            print(f"  User ID: {user_id}")
            
            return True
            
        except Exception as e:
            print(f"Set user info error: {e}")
            return False

    def get_user_input(self):
        """Get user info from console input"""
        print("\n" + "=" * 60)
        print("ENTER USER INFORMATION")
        print("=" * 60)
        
        while True:
            try:
                age = int(input("Age (years): "))
                if 1 <= age <= 120:
                    break
                print("Age must be between 1 and 120")
            except ValueError:
                print("Invalid input. Enter a number.")
        
        while True:
            sex_input = input("Sex (m/f): ").lower()
            if sex_input in ['m', 'f']:
                sex = 0 if sex_input == 'm' else 1
                break
            print("Enter 'm' for male or 'f' for female")
        
        while True:
            try:
                weight = int(input("Weight (kg): "))
                if 20 <= weight <= 300:
                    break
                print("Weight must be between 20 and 300 kg")
            except ValueError:
                print("Invalid input. Enter a number.")
        
        while True:
            try:
                height = int(input("Height (cm): "))
                if 50 <= height <= 250:
                    break
                print("Height must be between 50 and 250 cm")
            except ValueError:
                print("Invalid input. Enter a number.")
        
        return age, sex, weight, height

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
            
            # 4. Main menu
            while True:
                print("\n" + "=" * 60)
                print("USER INFO MENU")
                print("=" * 60)
                print("1. Get current user info")
                print("2. Set new user info")
                print("3. Exit")
                
                choice = input("\nSelect option (1-3): ").strip()
                
                if choice == '1':
                    await self.get_user_info()
                    
                elif choice == '2':
                    # First get current info (if any)
                    print("\nRetrieving current user info...")
                    await self.get_user_info()
                    
                    # Get new info from user
                    age, sex, weight, height = self.get_user_input()
                    
                    # Set new info
                    await self.set_user_info(age, sex, weight, height)
                    
                    # Verify by reading back
                    print("\nVerifying update...")
                    await asyncio.sleep(1)
                    await self.get_user_info()
                    
                elif choice == '3':
                    break
                    
                else:
                    print("Invalid choice. Enter 1, 2, or 3")
            
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
    print("=" * 60)
    print("CL837 User Info Manager")
    print("Get and Set User Profile (Age, Sex, Weight, Height)")
    print("=" * 60)
    
    manager = CL837UserInfoManager()
    await manager.run()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
