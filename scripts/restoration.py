"""
CL837 Device Restoration (Factory Reset)
Sends 0xF3 command to reset the device to factory settings

⚠️  WARNING: This will erase ALL data on the device including:
   - Sleep history
   - Heart rate history
   - Step/sport history
   - User settings
   - All recorded data

Usage:
    python restoration.py
"""
import asyncio
import time
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837Restoration:
    """CL837 Device Factory Reset Manager"""
    
    def __init__(self):
        self.client = None
        self.device = None
        self.is_connected = False
        
        # Chileaf Protocol
        self.CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_HEADER = 0xFF
        
        # Commands
        self.CMD_RESTORATION = 0xF3  # Factory reset command
        
        self.restoration_confirmed = False
        self.tx_char = None
        self.rx_char = None

    async def scan_and_connect(self):
        """Scan and connect to CL837 device"""
        print("🔍 Scanning for CL837 devices...")
        
        devices = await BleakScanner.discover(timeout=8.0)
        
        cl837_devices = [d for d in devices if d.name and ("CL837" in d.name or "CL831" in d.name)]
        
        if not cl837_devices:
            print("❌ No CL837 devices found")
            return False
        
        # Device selection
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
            print("\n🔗 Connecting...")
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
        """Find and setup BLE characteristics"""
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
        
        frame_bytes = bytes(frame)
        await self.client.write_gatt_char(self.rx_char, frame_bytes)
        await asyncio.sleep(0.1)

    def notification_handler(self, sender, data):
        """Handle BLE notifications from device"""
        try:
            if len(data) >= 3:
                header = data[0]
                command = data[2]
                
                if header == self.CHILEAF_HEADER and command == self.CMD_RESTORATION:
                    self.restoration_confirmed = True
                    print("   ✅ Device confirmed restoration")
        except Exception as e:
            pass

    async def perform_restoration(self):
        """Send factory reset command to device"""
        print("\n" + "="*60)
        print("⚠️  WARNING: FACTORY RESET")
        print("="*60)
        print("\nThis will ERASE ALL DATA from the device:")
        print("  • Sleep history")
        print("  • Heart rate records")
        print("  • Step/sport history")
        print("  • Respiratory rate data")
        print("  • User settings and configuration")
        print("\nThe device will be restored to factory default settings.")
        print("\n" + "="*60)
        
        # Confirmation prompt
        confirm = input("\nType 'RESET' to confirm factory reset: ").strip()
        
        if confirm != 'RESET':
            print("\n❌ Factory reset cancelled")
            return False
        
        # Double confirmation
        confirm2 = input("\nAre you absolutely sure? (yes/no): ").strip().lower()
        
        if confirm2 != 'yes':
            print("\n❌ Factory reset cancelled")
            return False
        
        print("\n🔄 Sending factory reset command...")
        print("   Command: 0xF3 (RESTORATION)")
        
        # Send restoration command (0xF3 with no parameters)
        await self.send_command(self.CMD_RESTORATION, [0x00])
        
        # Wait for confirmation or disconnection
        print("   ⏳ Waiting for device response...")
        await asyncio.sleep(3.0)
        
        # Check if device disconnected (expected behavior during reset)
        device_disconnected = not self.client.is_connected
        
        if device_disconnected:
            print("\n✅ FACTORY RESET COMPLETED")
            print("   Device disconnected (expected during reset)")
            print("\nThe device has been restored to factory settings.")
        elif self.restoration_confirmed:
            print("\n✅ FACTORY RESET COMPLETED")
            print("   Device confirmed restoration")
            print("\nThe device has been restored to factory settings.")
        else:
            print("\n⚠️  Factory reset command sent")
            print("   (No explicit confirmation received)")
            print("\nThe device should be resetting now.")
        
        print("\nNext steps:")
        print("  1. Wait ~10 seconds for device to complete reset")
        print("  2. Re-scan and reconnect to the device")
        print("  3. Set user information (age, sex, weight, height)")
        print("  4. Sync UTC time")
        
        return True

    async def disconnect(self):
        """Disconnect from device"""
        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                print("\n🔌 Disconnected")
                self.is_connected = False
        except Exception as e:
            print(f"Disconnect error: {e}")

    async def run(self):
        """Execute restoration workflow"""
        print("\n" + "="*60)
        print("CL837 DEVICE RESTORATION (Factory Reset)")
        print("="*60)
        
        try:
            # Step 1: Connect
            if not await self.scan_and_connect():
                return False
            
            # Step 2: Setup BLE
            if not await self.setup_characteristics():
                await self.disconnect()
                return False
            
            # Step 3: Enable notifications
            await self.client.start_notify(self.tx_char, self.notification_handler)
            await asyncio.sleep(0.2)
            
            # Step 4: Perform restoration
            success = await self.perform_restoration()
            
            # Step 5: Cleanup (device might already be disconnected after reset)
            try:
                if self.client and self.client.is_connected:
                    await self.client.stop_notify(self.tx_char)
            except Exception:
                # Device likely disconnected during reset - this is expected
                pass
            
            await self.disconnect()
            
            return success
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            await self.disconnect()
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await self.disconnect()
            return False


async def main():
    """Main entry point"""
    manager = CL837Restoration()
    
    try:
        success = await manager.run()
        
        if success:
            print("\n" + "="*60)
            print("✅ OPERATION COMPLETED")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ OPERATION CANCELLED OR FAILED")
            print("="*60)
            
    except KeyboardInterrupt:
        print("\n\nBye! 👋")


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(main())
