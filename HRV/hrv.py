"""
CL837 HRV (Heart Rate Variability) Monitor
Real-time RR intervals collection and HRV analysis

Data sources:
1. Standard BLE Heart Rate Service (UUID: 180D, Char: 2A37) → RR intervals
2. Chileaf Custom Protocol (cmd 0x02) → TP, LF, HF from device

Based on decompiled Chileaf SDK (HeartRateMeasurementDataCallback.java)
"""
import asyncio
import time
import struct
import traceback
import csv
import numpy as np
from datetime import datetime
from collections import deque
from bleak import BleakClient, BleakScanner

try:
    from scipy import signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("⚠ scipy not installed - frequency domain analysis disabled")
    print("  Install with: pip install scipy")


class CL837HRVMonitor:
    """CL837 HRV Monitor - Collects RR intervals and calculates HRV metrics"""
    
    def __init__(self, buffer_size=300):
        # BLE Connection
        self.client = None
        self.device = None
        self.is_connected = False
        
        # Standard BLE Heart Rate Service
        self.HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
        self.HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
        
        # Chileaf Protocol
        self.CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_HEADER = 0xFF
        
        # Commands
        self.CMD_SET_UTC = 0x08
        
        # Characteristics
        self.hr_char = None
        self.tx_char = None
        self.rx_char = None
        
        # Data storage
        self.buffer_size = buffer_size  # Keep last N RR intervals
        self.rr_intervals = deque(maxlen=buffer_size)
        self.rr_timestamps = deque(maxlen=buffer_size)
        self.hr_values = deque(maxlen=buffer_size)
        
        # Device HRV metrics (from Chileaf protocol)
        self.device_hrv = {
            'tp': None,
            'lf': None,
            'hf': None,
            'timestamp': None
        }
        
        # Latest HR
        self.latest_hr = None
        
        # Recording
        self.recording = False
        self.recorded_data = []
        
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
            else:
                print("⚠ Heart Rate Service not found - RR intervals may not be available")
            
            # Find Chileaf service
            chileaf_service = None
            for service in services:
                if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                    chileaf_service = service
                    print(f"✓ Found Chileaf Service: {service.uuid}")
                    break
            
            if chileaf_service:
                for char in chileaf_service.characteristics:
                    if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                        self.tx_char = char
                        print(f"  ✓ TX Char (notify): {char.uuid}")
                    elif char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                        self.rx_char = char
                        print(f"  ✓ RX Char (write): {char.uuid}")
            
            # Enable notifications
            if self.hr_char:
                await self.client.start_notify(self.hr_char, self.hr_notification_handler)
                print("  ✓ HR notifications enabled (RR intervals)")
            
            if self.tx_char:
                await self.client.start_notify(self.tx_char, self.chileaf_notification_handler)
                print("  ✓ Chileaf notifications enabled (device HRV)")
            
            return True
            
        except Exception as e:
            print(f"Service discovery error: {e}")
            traceback.print_exc()
            return False

    def hr_notification_handler(self, sender, data):
        """Handle standard BLE HR notifications with RR intervals"""
        try:
            timestamp = datetime.now()
            
            # Parse Heart Rate Measurement (BLE standard)
            flags = data[0]
            hr_format = flags & 0x01  # 0 = uint8, 1 = uint16
            has_rr = (flags & 0x10) != 0  # Bit 4: RR intervals present
            
            # Parse Heart Rate
            if hr_format == 0:
                hr = data[1]
                offset = 2
            else:
                hr = struct.unpack('<H', data[1:3])[0]
                offset = 3
            
            self.latest_hr = hr
            self.hr_values.append(hr)
            
            # Skip energy expended if present
            if flags & 0x08:  # Bit 3: Energy Expended present
                offset += 2
            
            # Parse RR Intervals (the key data for HRV!)
            if has_rr and len(data) > offset:
                while offset < len(data) - 1:
                    rr_raw = struct.unpack('<H', data[offset:offset+2])[0]
                    # Convert from 1/1024 seconds to milliseconds
                    rr_ms = rr_raw * 1000 / 1024
                    
                    # Filter artifacts (physiologically impossible values)
                    if 300 < rr_ms < 2000:  # Valid RR range
                        self.rr_intervals.append(rr_ms)
                        self.rr_timestamps.append(timestamp)
                        
                        # Record if active
                        if self.recording:
                            self.recorded_data.append({
                                'timestamp': timestamp.isoformat(),
                                'hr': hr,
                                'rr_ms': rr_ms,
                                'rr_raw': rr_raw
                            })
                    
                    offset += 2
                    
        except Exception as e:
            print(f"HR parse error: {e}")

    def chileaf_notification_handler(self, sender, data):
        """Handle Chileaf custom notifications for device-calculated HRV"""
        try:
            if len(data) < 4:
                return
            
            header = data[0]
            cmd = data[2]
            
            if header != self.CHILEAF_HEADER:
                return
            
            # Health data (includes device HRV: TP, LF, HF)
            if cmd == 0x02 and len(data) >= 20:
                self.parse_health_hrv(data)
                
        except Exception as e:
            print(f"Chileaf parse error: {e}")

    def parse_health_hrv(self, data):
        """Parse device-calculated HRV from health data notification"""
        try:
            # Format: [FF, len, 02, vo2max, breath, emotion, stress, stamina, TP(4), LF(4), HF(4), ...]
            tp_bytes = data[8:12]
            lf_bytes = data[12:16]
            hf_bytes = data[16:20]
            
            tp = struct.unpack('>f', bytes(tp_bytes))[0]
            lf = struct.unpack('>f', bytes(lf_bytes))[0]
            hf = struct.unpack('>f', bytes(hf_bytes))[0]
            
            self.device_hrv = {
                'tp': tp,
                'lf': lf,
                'hf': hf,
                'lf_hf_ratio': lf / hf if hf > 0 else 0,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Parse health HRV error: {e}")

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

    def calculate_time_domain_hrv(self):
        """Calculate time-domain HRV metrics from collected RR intervals"""
        if len(self.rr_intervals) < 10:
            return None
        
        rr = np.array(self.rr_intervals)
        
        # Basic statistics
        mean_rr = np.mean(rr)
        std_rr = np.std(rr, ddof=1)
        
        # SDNN - Standard Deviation of NN intervals
        sdnn = std_rr
        
        # RMSSD - Root Mean Square of Successive Differences
        diff = np.diff(rr)
        rmssd = np.sqrt(np.mean(diff ** 2))
        
        # pNN50 - Percentage of successive differences > 50ms
        nn50 = np.sum(np.abs(diff) > 50)
        pnn50 = (nn50 / len(diff)) * 100 if len(diff) > 0 else 0
        
        # pNN20 - Percentage of successive differences > 20ms
        nn20 = np.sum(np.abs(diff) > 20)
        pnn20 = (nn20 / len(diff)) * 100 if len(diff) > 0 else 0
        
        # Mean HR from RR
        mean_hr = 60000 / mean_rr if mean_rr > 0 else 0
        
        return {
            'n_intervals': len(rr),
            'mean_rr': mean_rr,
            'std_rr': std_rr,
            'mean_hr': mean_hr,
            'sdnn': sdnn,
            'rmssd': rmssd,
            'pnn50': pnn50,
            'pnn20': pnn20,
            'min_rr': np.min(rr),
            'max_rr': np.max(rr)
        }

    def calculate_frequency_domain_hrv(self, fs=4.0):
        """Calculate frequency-domain HRV metrics (requires scipy)"""
        if not HAS_SCIPY:
            return None
        
        if len(self.rr_intervals) < 60:  # Need at least ~1 minute of data
            return None
        
        try:
            rr = np.array(self.rr_intervals)
            
            # Create time series from RR intervals
            t = np.cumsum(rr) / 1000  # time in seconds
            t = t - t[0]
            
            # Interpolate to constant sample rate
            t_interp = np.arange(0, t[-1], 1/fs)
            if len(t_interp) < 32:
                return None
                
            rr_interp = np.interp(t_interp, t, rr)
            
            # Detrend
            rr_detrend = signal.detrend(rr_interp)
            
            # Calculate PSD using Welch method
            nperseg = min(256, len(rr_detrend) // 2)
            if nperseg < 16:
                return None
                
            freqs, psd = signal.welch(rr_detrend, fs=fs, nperseg=nperseg)
            
            # Frequency bands
            vlf_mask = (freqs >= 0.003) & (freqs < 0.04)
            lf_mask = (freqs >= 0.04) & (freqs < 0.15)
            hf_mask = (freqs >= 0.15) & (freqs < 0.4)
            
            # Calculate power in each band
            vlf = np.trapz(psd[vlf_mask], freqs[vlf_mask]) if np.any(vlf_mask) else 0
            lf = np.trapz(psd[lf_mask], freqs[lf_mask]) if np.any(lf_mask) else 0
            hf = np.trapz(psd[hf_mask], freqs[hf_mask]) if np.any(hf_mask) else 0
            
            tp = vlf + lf + hf
            
            return {
                'vlf': vlf,
                'lf': lf,
                'hf': hf,
                'tp': tp,
                'lf_hf_ratio': lf / hf if hf > 0 else 0,
                'lf_nu': lf / (lf + hf) * 100 if (lf + hf) > 0 else 0,
                'hf_nu': hf / (lf + hf) * 100 if (lf + hf) > 0 else 0
            }
            
        except Exception as e:
            print(f"Frequency domain calculation error: {e}")
            return None

    def interpret_hrv(self, time_hrv, freq_hrv=None):
        """Provide interpretation of HRV metrics"""
        interp = []
        
        if time_hrv:
            # RMSSD interpretation
            rmssd = time_hrv['rmssd']
            if rmssd < 20:
                interp.append(f"RMSSD ({rmssd:.1f}ms): ⚠ Low - possible stress/fatigue")
            elif rmssd < 50:
                interp.append(f"RMSSD ({rmssd:.1f}ms): ✓ Normal range")
            else:
                interp.append(f"RMSSD ({rmssd:.1f}ms): ✓ Good - well recovered")
            
            # SDNN interpretation
            sdnn = time_hrv['sdnn']
            if sdnn < 50:
                interp.append(f"SDNN ({sdnn:.1f}ms): ⚠ Low variability")
            elif sdnn < 100:
                interp.append(f"SDNN ({sdnn:.1f}ms): ✓ Normal variability")
            else:
                interp.append(f"SDNN ({sdnn:.1f}ms): ✓ High variability")
        
        if freq_hrv:
            # LF/HF ratio interpretation
            ratio = freq_hrv['lf_hf_ratio']
            if ratio < 1:
                interp.append(f"LF/HF ({ratio:.2f}): Parasympathetic dominant (relaxed)")
            elif ratio < 2:
                interp.append(f"LF/HF ({ratio:.2f}): Balanced autonomic activity")
            else:
                interp.append(f"LF/HF ({ratio:.2f}): Sympathetic dominant (stressed/active)")
        
        return interp

    def display_dashboard(self):
        """Display real-time HRV dashboard"""
        print("\033[2J\033[H", end='')  # Clear screen
        
        print("=" * 70)
        print(f"CL837 HRV MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Current HR
        if self.latest_hr:
            print(f"\n❤️  Heart Rate: {self.latest_hr} bpm")
        else:
            print(f"\n❤️  Heart Rate: -- (waiting for data)")
        
        # RR Intervals buffer status
        print(f"\n📊 RR Intervals Buffer: {len(self.rr_intervals)}/{self.buffer_size}")
        if self.rr_intervals:
            recent_rr = list(self.rr_intervals)[-5:]
            print(f"   Latest: {[f'{rr:.0f}ms' for rr in recent_rr]}")
        
        # Recording status
        if self.recording:
            print(f"\n🔴 RECORDING: {len(self.recorded_data)} samples")
        
        # Time Domain HRV
        time_hrv = self.calculate_time_domain_hrv()
        if time_hrv:
            print(f"\n⏱️  TIME DOMAIN HRV ({time_hrv['n_intervals']} intervals):")
            print(f"   Mean RR: {time_hrv['mean_rr']:.1f} ms")
            print(f"   Mean HR: {time_hrv['mean_hr']:.1f} bpm")
            print(f"   SDNN:    {time_hrv['sdnn']:.1f} ms")
            print(f"   RMSSD:   {time_hrv['rmssd']:.1f} ms")
            print(f"   pNN50:   {time_hrv['pnn50']:.1f}%")
            print(f"   pNN20:   {time_hrv['pnn20']:.1f}%")
        else:
            print(f"\n⏱️  TIME DOMAIN HRV: Need more data (min 10 intervals)")
        
        # Frequency Domain HRV (calculated)
        freq_hrv = self.calculate_frequency_domain_hrv()
        if freq_hrv:
            print(f"\n📈 FREQUENCY DOMAIN HRV (calculated):")
            print(f"   VLF:       {freq_hrv['vlf']:.2f} ms²")
            print(f"   LF:        {freq_hrv['lf']:.2f} ms²")
            print(f"   HF:        {freq_hrv['hf']:.2f} ms²")
            print(f"   TP:        {freq_hrv['tp']:.2f} ms²")
            print(f"   LF/HF:     {freq_hrv['lf_hf_ratio']:.2f}")
            print(f"   LF (nu):   {freq_hrv['lf_nu']:.1f}%")
            print(f"   HF (nu):   {freq_hrv['hf_nu']:.1f}%")
        elif HAS_SCIPY:
            print(f"\n📈 FREQUENCY DOMAIN HRV: Need more data (min ~60 intervals)")
        
        # Device HRV (from Chileaf protocol)
        if self.device_hrv['tp'] is not None:
            print(f"\n📡 DEVICE HRV (from CL837):")
            print(f"   TP:    {self.device_hrv['tp']:.2f}")
            print(f"   LF:    {self.device_hrv['lf']:.2f}")
            print(f"   HF:    {self.device_hrv['hf']:.2f}")
            print(f"   LF/HF: {self.device_hrv['lf_hf_ratio']:.2f}")
        
        # Interpretation
        interpretation = self.interpret_hrv(time_hrv, freq_hrv)
        if interpretation:
            print(f"\n💡 INTERPRETATION:")
            for line in interpretation:
                print(f"   {line}")
        
        print("\n" + "=" * 70)
        print("Commands: [R]ecord start/stop  [S]ave CSV  [C]lear buffer  [Q]uit")
        print("=" * 70)

    def start_recording(self):
        """Start recording RR intervals"""
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
        filename = f"hrv_data_{device_name}_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'hr', 'rr_ms', 'rr_raw'])
                writer.writeheader()
                writer.writerows(self.recorded_data)
            
            print(f"\n✓ Saved to {filename}")
            
            # Also save HRV summary
            summary_filename = f"hrv_summary_{device_name}_{timestamp}.txt"
            with open(summary_filename, 'w') as f:
                f.write(f"HRV Analysis Summary\n")
                f.write(f"{'='*50}\n")
                f.write(f"Device: {self.device.name if self.device else 'Unknown'}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Samples: {len(self.recorded_data)}\n\n")
                
                time_hrv = self.calculate_time_domain_hrv()
                if time_hrv:
                    f.write("Time Domain Metrics:\n")
                    for key, value in time_hrv.items():
                        f.write(f"  {key}: {value:.2f}\n")
                
                freq_hrv = self.calculate_frequency_domain_hrv()
                if freq_hrv:
                    f.write("\nFrequency Domain Metrics:\n")
                    for key, value in freq_hrv.items():
                        f.write(f"  {key}: {value:.2f}\n")
            
            print(f"✓ Summary saved to {summary_filename}")
            return filename
            
        except Exception as e:
            print(f"\n✗ Save error: {e}")
            return None

    def clear_buffer(self):
        """Clear RR intervals buffer"""
        self.rr_intervals.clear()
        self.rr_timestamps.clear()
        self.hr_values.clear()
        print("\n✓ Buffer cleared")

    async def handle_input(self):
        """Handle keyboard input (non-blocking)"""
        import sys
        import select
        
        # Check if input available (Unix-like)
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
                    self.clear_buffer()
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
            print("Starting HRV monitoring...")
            print("RR intervals are collected from the HR Service (UUID 2A37)")
            print("Device HRV (TP/LF/HF) comes from Chileaf protocol")
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
    print("CL837 HRV (Heart Rate Variability) Monitor")
    print("Collects RR intervals and calculates HRV metrics")
    print("=" * 70)
    
    monitor = CL837HRVMonitor(buffer_size=500)
    await monitor.run()
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
