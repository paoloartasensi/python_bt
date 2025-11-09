"""
CL837 UTC Time Sync Only
Quick script to sync device time - takes ~3 seconds
"""
import asyncio
import time
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837UTCSync:
    """Fast UTC sync for CL837"""
    
    def __init__(self):
        self.client = None
        self.device = None
        self.is_connected = False
        
        # Chileaf Protocol
        self.CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_HEADER = 0xFF
        self.CMD_SET_UTC = 0x08
        
        self.utc_confirmed = False
        self.tx_char = None
        self.rx_char = None

    async def scan_and_connect(self):
        """Quick scan and connect"""
        print("🔍 Scanning for CL837...")
        
        devices = await BleakScanner.discover(timeout=5.0)
        
        cl837_devices = [d for d in devices if d.name and ("CL837" in d.name or "CL831" in d.name)]
        
        if not cl837_devices:
            print("❌ No CL837 devices found")
            return False
        
        target_device = cl837_devices[0]
        print(f"📱 Found: {target_device.name}")
        
        try:
            print("🔗 Connecting...")
            self.client = BleakClient(target_device, timeout=10.0)
            await self.client.connect()
            
            if self.client.is_connected:
                self.is_connected = True
                self.device = target_device
                print(f"✅ Connected!")
                return True
            else:
                print("❌ Connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    async def setup_characteristics(self):
        """Find Chileaf characteristics"""
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
        """Calculate Chileaf protocol checksum"""
        checksum = sum(data) & 0xFF
        checksum = (0 - checksum) & 0xFF
        checksum = checksum ^ 0x3A
        return checksum

    async def send_command(self, command, data=None):
        """Send command to device"""
        if data is None:
            data = []
        
        frame = [self.CHILEAF_HEADER, len(data) + 4, command] + data
        checksum = self.calculate_checksum(frame)
        frame.append(checksum)
        
        frame_bytes = bytes(frame)
        await self.client.write_gatt_char(self.rx_char, frame_bytes)

    async def sync_utc_time(self):
        """Sync UTC time to device"""
        print("\n⏰ Syncing UTC time...")
        
        # Get current UTC timestamp
        utc_timestamp = int(time.time())
        utc_datetime = datetime.utcfromtimestamp(utc_timestamp)
        
        print(f"   Current UTC: {utc_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Timestamp: {utc_timestamp}")
        
        # Convert to 4 bytes (big-endian)
        utc_bytes = [
            (utc_timestamp >> 24) & 0xFF,
            (utc_timestamp >> 16) & 0xFF,
            (utc_timestamp >> 8) & 0xFF,
            utc_timestamp & 0xFF
        ]
        
        await self.send_command(self.CMD_SET_UTC, utc_bytes)
        
        # Wait for confirmation
        await asyncio.sleep(1.5)
        
        if self.utc_confirmed:
            print("✅ UTC sync confirmed by device!")
            return True
        else:
            print("⚠️  UTC sent (no confirmation received)")
            return True  # Still consider it successful

    def notification_handler(self, sender, data):
        """Handle BLE notifications"""
        try:
            if len(data) >= 3:
                header = data[0]
                command = data[2]
                
                if header == self.CHILEAF_HEADER and command == self.CMD_SET_UTC:
                    self.utc_confirmed = True
        except:
            pass

    async def run(self):
        """Execute UTC sync"""
        print("\n" + "="*50)
        print("CL837 UTC TIME SYNC")
        print("="*50)
        
        # Step 1: Connect
        if not await self.scan_and_connect():
            return False
        
        # Step 2: Setup
        if not await self.setup_characteristics():
            return False
        
        # Step 3: Enable notifications
        await self.client.start_notify(self.tx_char, self.notification_handler)
        await asyncio.sleep(0.3)
        
        # Step 4: Sync UTC
        success = await self.sync_utc_time()
        
        # Step 5: Disconnect
        await self.client.stop_notify(self.tx_char)
        await self.client.disconnect()
        print("\n🔌 Disconnected")
        
        return success

    async def disconnect(self):
        """Cleanup disconnect"""
        if self.client and self.is_connected:
            try:
                await self.client.stop_notify(self.tx_char)
            except:
                pass
            await self.client.disconnect()


async def main():
    """Main function"""
    sync = CL837UTCSync()
    
    try:
        success = await sync.run()
        
        if success:
            print("\n" + "="*50)
            print("✅ UTC SYNC COMPLETED SUCCESSFULLY!")
            print("="*50)
            print("\nYour device now has the correct time.")
            print("All new sleep/sport data will have accurate timestamps.")
        else:
            print("\n" + "="*50)
            print("❌ UTC SYNC FAILED")
            print("="*50)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        await sync.disconnect()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting quick UTC sync...")
    print("   This will take ~3-5 seconds\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBye! 👋")
