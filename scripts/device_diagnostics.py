"""
CL837 Feature Diagnostics
Automatic testing of all available commands to determine device capabilities
"""
import asyncio
import time
import struct
import traceback
from datetime import datetime
from bleak import BleakClient, BleakScanner


class CL837Diagnostics:
    """CL837 Device Feature Diagnostics"""
    
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
        
        # Standard BLE
        self.HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
        self.HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
        
        # Commands to test
        self.CMD_SET_UTC = 0x08
        self.COMMANDS_TO_TEST = {
            'Sleep History': {'cmd': 0x05, 'params': [0x02], 'timeout': 10},
            'Sport 7-Day History': {'cmd': 0x16, 'params': [0x00], 'timeout': 10},
            'HR Record List': {'cmd': 0x21, 'params': [0x00], 'timeout': 10},
            'RR Record List': {'cmd': 0x24, 'params': [], 'timeout': 10},
            'Step Record List': {'cmd': 0x90, 'params': [], 'timeout': 10},
            'Interval Steps': {'cmd': 0x40, 'params': [0x00], 'timeout': 10},
            'Single Tap Records': {'cmd': 0x42, 'params': [0x00], 'timeout': 10},
            'User Info': {'cmd': 0x03, 'params': [0x00], 'timeout': 5},
        }
        
        # Test results
        self.test_results = {}
        self.responses_received = []
        self.current_test = None
        self.test_complete = False
        
        # Characteristics
        self.hr_char = None
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
            
            # Check for standard HR service
            hr_service_found = False
            for service in services:
                if service.uuid.lower() == self.HR_SERVICE_UUID.lower():
                    hr_service_found = True
                    print(f"\n✓ Standard HR Service: Found")
                    for char in service.characteristics:
                        if char.uuid.lower() == self.HR_MEASUREMENT_UUID.lower():
                            self.hr_char = char
                            print(f"  ✓ HR Measurement Characteristic: Found")
                    break
            
            if not hr_service_found:
                print(f"\n✗ Standard HR Service: Not found")
            
            # Find Chileaf service
            chileaf_service = None
            for service in services:
                if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                    chileaf_service = service
                    print(f"✓ Chileaf Service: Found")
                    break
            
            if not chileaf_service:
                print("✗ Chileaf service not found")
                return False
            
            # Find TX and RX characteristics
            for char in chileaf_service.characteristics:
                if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                    self.tx_char = char
                    print(f"  ✓ TX Characteristic (notify): Found")
                elif char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                    self.rx_char = char
                    print(f"  ✓ RX Characteristic (write): Found")
            
            if not self.tx_char or not self.rx_char:
                print("✗ Required characteristics not found")
                return False
            
            # Enable notifications
            if self.hr_char:
                await self.client.start_notify(self.hr_char, self.hr_notification_handler)
                print(f"  ✓ HR notifications enabled")
            
            await self.client.start_notify(self.tx_char, self.notification_handler)
            print(f"  ✓ Chileaf notifications enabled")
            
            return True
            
        except Exception as e:
            print(f"Service discovery error: {e}")
            traceback.print_exc()
            return False

    def hr_notification_handler(self, sender, data):
        """Handle HR notifications"""
        if self.current_test == 'HR_SERVICE':
            self.responses_received.append(('HR_DATA', data))
            self.test_complete = True

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
            
            # Record response
            self.responses_received.append((cmd, data))
            
            # Check for end markers (0xFF 0xFF) or actual data
            if len(data) >= 5:
                if data[3] == 0xFF and data[4] == 0xFF:
                    # End marker - no data available
                    self.test_complete = True
                elif len(data) > 5:
                    # Has actual data
                    self.test_complete = True
            
        except Exception as e:
            print(f"Notification error: {e}")

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

    async def test_command(self, name, cmd, params, timeout):
        """Test a single command"""
        try:
            print(f"\n[Testing] {name} (cmd: 0x{cmd:02X})...", end='', flush=True)
            
            self.current_test = name
            self.test_complete = False
            self.responses_received = []
            
            # Send command
            await self.send_command(cmd, params)
            
            # Wait for response
            start_time = time.time()
            while not self.test_complete and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.1)
            
            # Analyze results
            if not self.responses_received:
                print(" ❌ TIMEOUT (no response)")
                return {'status': 'timeout', 'responses': 0}
            
            # Check if we got data or just end marker
            has_data = False
            response_count = 0
            
            for cmd_resp, data_resp in self.responses_received:
                if len(data_resp) > 5:
                    # Check if it's not just end marker
                    if not (data_resp[3] == 0xFF and data_resp[4] == 0xFF):
                        has_data = True
                        response_count += 1
            
            if has_data:
                print(f" ✅ SUPPORTED ({response_count} records)")
                return {'status': 'supported', 'responses': response_count}
            else:
                print(f" ⚠️  NO DATA (command accepted but empty)")
                return {'status': 'no_data', 'responses': 0}
                
        except Exception as e:
            print(f" ❌ ERROR: {e}")
            return {'status': 'error', 'responses': 0}

    async def test_hr_service(self):
        """Test standard HR service"""
        try:
            print(f"\n[Testing] Standard BLE HR Service...", end='', flush=True)
            
            if not self.hr_char:
                print(" ❌ NOT AVAILABLE (no HR characteristic)")
                return {'status': 'not_available', 'responses': 0}
            
            self.current_test = 'HR_SERVICE'
            self.test_complete = False
            self.responses_received = []
            
            # Wait for HR notification
            start_time = time.time()
            while not self.test_complete and (time.time() - start_time) < 5:
                await asyncio.sleep(0.1)
            
            if self.responses_received:
                print(" ✅ SUPPORTED (receiving HR data)")
                return {'status': 'supported', 'responses': len(self.responses_received)}
            else:
                print(" ⚠️  NO DATA (HR not being measured)")
                return {'status': 'no_data', 'responses': 0}
                
        except Exception as e:
            print(f" ❌ ERROR: {e}")
            return {'status': 'error', 'responses': 0}

    async def run_diagnostics(self):
        """Run all diagnostic tests"""
        print("\n" + "=" * 70)
        print("RUNNING DIAGNOSTICS")
        print("=" * 70)
        
        # Test standard HR service
        self.test_results['Standard HR Service'] = await self.test_hr_service()
        
        # Test all Chileaf commands
        for name, config in self.COMMANDS_TO_TEST.items():
            result = await self.test_command(
                name, 
                config['cmd'], 
                config['params'], 
                config['timeout']
            )
            self.test_results[name] = result
            await asyncio.sleep(0.5)  # Small delay between tests

    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "=" * 70)
        print("DIAGNOSTIC REPORT")
        print("=" * 70)
        print(f"Device: {self.device.name}")
        print(f"Address: {self.device.address}")
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Categorize results
        supported = []
        no_data = []
        not_working = []
        
        for name, result in self.test_results.items():
            if result['status'] == 'supported':
                supported.append((name, result['responses']))
            elif result['status'] == 'no_data':
                no_data.append(name)
            else:
                not_working.append(name)
        
        # Print supported features
        print(f"\n✅ SUPPORTED FEATURES ({len(supported)}):")
        if supported:
            for name, count in supported:
                print(f"   • {name} ({count} records/responses)")
        else:
            print("   None")
        
        # Print empty/no data features
        print(f"\n⚠️  ACCEPTED BUT NO DATA ({len(no_data)}):")
        if no_data:
            for name in no_data:
                print(f"   • {name}")
        else:
            print("   None")
        
        # Print not working features
        print(f"\n❌ NOT WORKING/TIMEOUT ({len(not_working)}):")
        if not_working:
            for name in not_working:
                print(f"   • {name}")
        else:
            print("   None")
        
        # Recommended scripts
        print(f"\n📋 RECOMMENDED SCRIPTS FOR YOUR DEVICE:")
        print("=" * 70)
        
        script_map = {
            'Sleep History': 'sleep.py',
            'Sport 7-Day History': 'sport_history.py',
            'Interval Steps': 'steps_history.py',
            'Step Record List': 'steps_history.py',
            'HR Record List': 'hr_history.py',
            'Standard HR Service': 'realtime_monitor.py',
            'User Info': 'user_info.py'
        }
        
        recommended = set()
        for name in supported:
            feature_name = name[0] if isinstance(name, tuple) else name
            if feature_name in script_map:
                recommended.add(script_map[feature_name])
        
        if recommended:
            for script in sorted(recommended):
                print(f"   ✓ python {script}")
        else:
            print("   ⚠️  Limited functionality - only realtime_monitor.py recommended")
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"device_diagnostics_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("CL837 DEVICE DIAGNOSTICS REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Device: {self.device.name}\n")
            f.write(f"Address: {self.device.address}\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"SUPPORTED FEATURES ({len(supported)}):\n")
            for name, count in supported:
                f.write(f"  • {name} ({count} records/responses)\n")
            
            f.write(f"\nACCEPTED BUT NO DATA ({len(no_data)}):\n")
            for name in no_data:
                f.write(f"  • {name}\n")
            
            f.write(f"\nNOT WORKING/TIMEOUT ({len(not_working)}):\n")
            for name in not_working:
                f.write(f"  • {name}\n")
            
            f.write(f"\nRECOMMENDED SCRIPTS:\n")
            for script in sorted(recommended):
                f.write(f"  ✓ python {script}\n")
        
        print(f"\n💾 Report saved to: {filename}")
        print("=" * 70)

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
            
            # 4. Run diagnostics
            await self.run_diagnostics()
            
            # 5. Generate report
            self.generate_report()
            
            # 6. Disconnect
            await self.disconnect()
            
        except Exception as e:
            print(f"\nError: {e}")
            traceback.print_exc()
            await self.disconnect()


async def main():
    """Entry point"""
    print("=" * 70)
    print("CL837 FEATURE DIAGNOSTICS")
    print("Automatic detection of supported device capabilities")
    print("=" * 70)
    print("\nThis will test all known commands to determine what your")
    print("device supports. The process takes about 1-2 minutes.")
    print("=" * 70)
    
    input("\nPress ENTER to start diagnostics...")
    
    diagnostics = CL837Diagnostics()
    await diagnostics.run()
    
    print("\n" + "=" * 70)
    print("DIAGNOSTICS COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
