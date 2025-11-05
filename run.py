"""
CL837 Unified Accelerometer Monitor
Connection, reading and real-time oscilloscope visualization
"""

import asyncio
import struct
import time
import threading
from collections import deque
import numpy as np

import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend which works better with threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from bleak import BleakClient, BleakScanner

class KalmanFilter1D:
    """Simple 1D Kalman Filter for accelerometer data"""
    def __init__(self, process_variance=0.001, measurement_variance=0.1, estimate_error=1.0):
        """
        Initialize Kalman Filter
        
        Args:
            process_variance: How much we expect the value to change (Q)
            measurement_variance: Sensor noise variance (R)
            estimate_error: Initial estimate error (P)
        """
        self.process_variance = process_variance  # Q
        self.measurement_variance = measurement_variance  # R
        self.estimate_error = estimate_error  # P
        self.estimate = 0.0  # x_hat
        self.is_initialized = False
    
    def update(self, measurement):
        """Update filter with new measurement"""
        if not self.is_initialized:
            self.estimate = measurement
            self.is_initialized = True
            return self.estimate
        
        # Prediction step
        # x_hat_minus = x_hat (assuming constant value)
        # P_minus = P + Q
        self.estimate_error += self.process_variance
        
        # Update step
        # K = P_minus / (P_minus + R)
        kalman_gain = self.estimate_error / (self.estimate_error + self.measurement_variance)
        
        # x_hat = x_hat_minus + K * (z - x_hat_minus)
        self.estimate = self.estimate + kalman_gain * (measurement - self.estimate)
        
        # P = (1 - K) * P_minus
        self.estimate_error = (1.0 - kalman_gain) * self.estimate_error
        
        return self.estimate
    
    def reset(self):
        """Reset the filter"""
        self.estimate = 0.0
        self.estimate_error = 1.0
        self.is_initialized = False

class CL837UnifiedMonitor:
    """Unified CL837 monitor with integrated oscilloscope"""
    
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
        self.CHILEAF_CMD_ACCELEROMETER = 0x0C
        self.CHILEAF_CONVERSION_FACTOR = 4096.0
        
        # Oscilloscope Data
        self.max_samples = 300   # Reduced window for lower latency (~12 sec at 25Hz)
        self.x_data = deque(maxlen=self.max_samples)
        self.y_data = deque(maxlen=self.max_samples)
        self.z_data = deque(maxlen=self.max_samples)
        self.magnitude_data = deque(maxlen=self.max_samples)
        
        # Kalman filters for each axis (more effective than moving average)
        # Tuning parameters:
        # - process_variance (Q): lower = smoother, higher = more responsive
        # - measurement_variance (R): based on sensor noise characteristics
        self.kalman_x = KalmanFilter1D(process_variance=0.001, measurement_variance=0.05)
        self.kalman_y = KalmanFilter1D(process_variance=0.001, measurement_variance=0.05)
        self.kalman_z = KalmanFilter1D(process_variance=0.001, measurement_variance=0.05)
        
        # Statistics
        self.sample_count = 0
        self.spike_count = 0
        self.frame_count = 0  # BLE frames received
        self.start_time = time.time()
        self.last_values = {'x': 0, 'y': 0, 'z': 0, 'mag': 0}
        
        # Instantaneous frequency tracking (based on BLE frames, not individual samples)
        self.frame_freq_window = deque(maxlen=50)  # Window for frame frequency
        self.instant_frame_freq = 0.0  # BLE frame frequency (Hz)
        self.instant_sample_freq = 0.0  # Sample frequency (Hz) = frame_freq × samples_per_frame
        
        # Adaptive oscilloscope refresh rate
        self.refresh_interval = 50  # Start with 50ms (20fps), will auto-adjust
        
        # Oscilloscope
        self.fig = None
        self.axes = None
        self.lines = []
        self.animation = None
        self.plot_thread = None
        self.plot_ready = False

    def calculate_optimal_refresh_rate(self):
        """Calculate optimal oscilloscope refresh rate based on sensor frequency"""
        if self.instant_sample_freq > 0:
            # Refresh rate should be 2-3x the sample rate for smooth display
            # But capped between 10-60 fps for performance
            optimal_fps = min(60, max(10, self.instant_sample_freq * 2.5))
            optimal_interval = int(1000 / optimal_fps)  # Convert to milliseconds
            return optimal_interval
        else:
            return 50  # Default 20fps if no data yet

    async def scan_and_connect(self):
        """Scan and connect to CL837"""
        while True:  # Loop for restart scan option
            print("Searching for CL837 devices...")
            
            devices = await BleakScanner.discover(timeout=8.0)
            
            cl837_devices = []
            for device in devices:
                if device.name and device.name.startswith("CL837"):
                    cl837_devices.append(device)
            
            if not cl837_devices:
                print("No CL837 devices found")
                print("Make sure the device is turned on and in range")
                print("Options: 'r' to restart scan, 'q' to exit")
                choice = input("> ").strip().lower()
                if choice == 'q':
                    return False
                elif choice == 'r':
                    continue  # Restart scan
                else:
                    print("Invalid choice. Enter 'r' to restart scan or 'q' to exit")
                    continue
            
            print(f"Found {len(cl837_devices)} CL837 devices:")
            for i, device in enumerate(cl837_devices, 1):
                print(f"   {i}. {device.name} ({device.address})")
            
            # INTERACTIVE DEVICE SELECTION
            if len(cl837_devices) == 1:
                # Only one available - direct connection
                target_device = cl837_devices[0]
                print(f"\nAutomatic connection to: {target_device.name}")
                break  # Exit the scan loop
            else:
                # Multiple devices - ask user
                while True:
                    try:
                        print(f"\nSelect device (1-{len(cl837_devices)}), 'r' to restart scan, or 'q' to exit:")
                        choice = input("> ").strip().lower()
                        
                        if choice == 'q':
                            print("Connection cancelled")
                            return False
                        elif choice == 'r':
                            break  # Break inner loop to restart outer scan loop
                        
                        device_index = int(choice) - 1
                        if 0 <= device_index < len(cl837_devices):
                            target_device = cl837_devices[device_index]
                            print(f"\nConnecting to: {target_device.name}")
                            break  # Exit both loops
                        else:
                            print(f"Invalid choice. Enter a number between 1 and {len(cl837_devices)}, 'r' to restart scan, or 'q' to exit")
                            
                    except ValueError:
                        print("Enter a valid number, 'r' to restart scan, or 'q' to exit")
                    except KeyboardInterrupt:
                        print("\nConnection cancelled")
                        return False
                
                if choice == 'r':
                    continue  # Restart scan
                else:
                    break  # Exit scan loop with selected device
        
        try:
            print("Connecting...")
            # LOW-LATENCY: reduced timeout for more responsive connections
            self.client = BleakClient(target_device, timeout=10.0)
            await self.client.connect()
            
            if self.client.is_connected:
                self.device = target_device
                self.is_connected = True
                print("Successfully connected!")
                
                # LATENCY OPTIMIZATION: Request low-latency parameters
                print("Configuring low-latency BLE...")
                try:
                    # Bleak doesn't have direct API for connection parameters, but some OS support hints
                    # Windows: Try to set high priority for the connection
                    if hasattr(self.client, '_backend') and hasattr(self.client._backend, '_requester'):
                        print("   Hint: Connection priority HIGH requested")
                except Exception as e:
                    print(f"   Connection parameters not configurable: {e}")
                
                return True
            else:
                print("Connection failed")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def discover_services(self):
        """Analyze device services and characteristics"""
        print("\nAnalyzing BLE services...")
        
        chileaf_service = None
        tx_characteristic = None
        
        for service in self.client.services:
            print(f"Service: {service.uuid}")
            
            if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                print("   CHILEAF SERVICE IDENTIFIED!")
                chileaf_service = service
            
            for char in service.characteristics:
                print(f"   Characteristic: {char.uuid} - {char.properties}")
                
                if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                    # Check support for indicate (faster than notify)
                    supports_indicate = "indicate" in char.properties
                    supports_notify = "notify" in char.properties
                    
                    speed_info = "INDICATE" if supports_indicate else "NOTIFY" if supports_notify else "NONE"
                    print(f"      CHILEAF TX CHARACTERISTIC ({speed_info})")
                    
                    if supports_indicate:
                        print("         INDICATE supported - Minimum latency available!")
                    
                    tx_characteristic = char
                elif char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                    print("      CHILEAF RX CHARACTERISTIC (Commands)")
        
        if not tx_characteristic:
            print("Chileaf TX characteristic not found!")
            return False
        
        if "notify" not in tx_characteristic.properties:
            print("The TX characteristic does not support notifications!")
            return False
        
        print("Chileaf service configured correctly")
        self.tx_char = tx_characteristic
        return True

    def setup_oscilloscope(self):
        """Initialize matplotlib oscilloscope"""
        print("Initializing oscilloscope...")
        
        # Create figure with subplots
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle("CL837 Accelerometer - Kalman Filtered (Adaptive Refresh)", fontsize=16)
        
        # Configure axes
        ax_xyz, ax_mag, ax_xy, ax_stats = self.axes.flatten()
        
        # XYZ plot - FIXED LIMITS for smooth scrolling
        ax_xyz.set_title("XYZ Acceleration (g)")
        ax_xyz.set_xlabel("Samples")
        ax_xyz.set_ylabel("Acceleration (g)")
        ax_xyz.grid(True, alpha=0.3)
        ax_xyz.legend(['X', 'Y', 'Z'])
        ax_xyz.set_xlim(0, 200)  # Fixed window of 200 samples
        ax_xyz.set_ylim(-2, 2)   # Fixed Y range
        
        # Magnitude plot - FIXED LIMITS
        ax_mag.set_title("Total Magnitude")
        ax_mag.set_xlabel("Samples")
        ax_mag.set_ylabel("Magnitude (g)")
        ax_mag.grid(True, alpha=0.3)
        ax_mag.set_xlim(0, 200)  # Fixed window
        ax_mag.set_ylim(0, 2.5)  # Fixed range
        
        # XY plot (top view)
        ax_xy.set_title("XY View (from top)")
        ax_xy.set_xlabel("X (g)")
        ax_xy.set_ylabel("Y (g)")
        ax_xy.grid(True, alpha=0.3)
        ax_xy.set_aspect('equal')
        ax_xy.set_xlim(-2, 2)
        ax_xy.set_ylim(-2, 2)
        
        # Statistics area
        ax_stats.set_title("Live Statistics")
        ax_stats.axis('off')
        
        # Initialize lines
        line_x, = ax_xyz.plot([], [], 'r-', label='X', alpha=0.8)
        line_y, = ax_xyz.plot([], [], 'g-', label='Y', alpha=0.8)
        line_z, = ax_xyz.plot([], [], 'b-', label='Z', alpha=0.8)
        line_mag, = ax_mag.plot([], [], 'purple', linewidth=2)
        line_xy, = ax_xy.plot([], [], 'o-', markersize=3, alpha=0.6)
        
        self.lines = [line_x, line_y, line_z, line_mag, line_xy]
        
        # Statistics text
        self.stats_text = ax_stats.text(0.05, 0.95, "", transform=ax_stats.transAxes,
                                       fontsize=10, verticalalignment='top',
                                       fontfamily='monospace')
        
        plt.tight_layout()
        print("Oscilloscope configured")

    def start_oscilloscope_thread(self):
        """Start oscilloscope in separate thread with adaptive refresh"""
        def run_plot():
            self.setup_oscilloscope()
            # Use adaptive interval that updates based on sensor frequency
            # blit=True for better performance (only redraw changed elements)
            self.animation = animation.FuncAnimation(
                self.fig, self.update_plot, interval=self.refresh_interval, 
                blit=True, cache_frame_data=False)
            self.plot_ready = True
            # Use non-blocking show to avoid threading issues
            plt.show(block=False)
            # Keep the plot window responsive
            while plt.fignum_exists(self.fig.number):
                plt.pause(0.1)
        
        self.plot_thread = threading.Thread(target=run_plot, daemon=True)
        self.plot_thread.start()
        
        # Wait for plot to be ready
        while not self.plot_ready:
            time.sleep(0.1)
        
        print("Oscilloscope started in separate thread")

    def update_plot(self, frame):
        """Update oscilloscope plots with smooth scrolling and adaptive refresh"""
        if len(self.x_data) < 2:
            return self.lines
        
        # Dynamically adjust refresh rate based on sensor frequency (every 50 frames)
        if frame % 50 == 0 and self.instant_sample_freq > 0:
            new_interval = self.calculate_optimal_refresh_rate()
            if abs(new_interval - self.refresh_interval) > 5:  # Only update if significant change
                self.refresh_interval = new_interval
                if self.animation:
                    self.animation.event_source.interval = new_interval
                    current_fps = 1000 / new_interval
                    print(f"   Oscilloscope refresh adapted to {current_fps:.1f}fps (sensor: {self.instant_sample_freq:.1f}Hz)")
        
        # Convert deque to lists for matplotlib
        x_list = list(self.x_data)
        y_list = list(self.y_data)
        z_list = list(self.z_data)
        mag_list = list(self.magnitude_data)
        
        # Create indices for x-axis (time-based for smooth scrolling)
        num_samples = len(x_list)
        indices = list(range(num_samples))
        
        # Update XYZ lines
        self.lines[0].set_data(indices, x_list)  # X
        self.lines[1].set_data(indices, y_list)  # Y
        self.lines[2].set_data(indices, z_list)  # Z
        
        # Update magnitude
        self.lines[3].set_data(indices, mag_list)
        
        # Update XY view (last 50 points)
        if len(x_list) > 50:
            xy_x = x_list[-50:]
            xy_y = y_list[-50:]
        else:
            xy_x = x_list
            xy_y = y_list
        self.lines[4].set_data(xy_x, xy_y)
        
        # Update axes limits ONLY when needed (reduces stuttering)
        # Only update every 10 frames or when significantly changed
        if frame % 10 == 0:
            # Smooth scrolling window - show last 200 samples with smooth transition
            if num_samples > 200:
                # Rolling window - always show the most recent 200 samples
                x_min = num_samples - 200
                x_max = num_samples
            else:
                # Growing window until we reach 200 samples
                x_min = 0
                x_max = max(num_samples, 10)  # Minimum 10 for visibility
            
            # Update XYZ plot limits with smooth scrolling
            self.axes[0, 0].set_xlim(x_min, x_max)
            
            # Adaptive Y limits for XYZ (based on visible window only)
            visible_x = x_list[-200:] if num_samples > 200 else x_list
            visible_y = y_list[-200:] if num_samples > 200 else y_list
            visible_z = z_list[-200:] if num_samples > 200 else z_list
            all_visible = visible_x + visible_y + visible_z
            
            if all_visible:
                y_min, y_max = min(all_visible), max(all_visible)
                margin = max((y_max - y_min) * 0.1, 0.1)  # At least 0.1g margin
                self.axes[0, 0].set_ylim(y_min - margin, y_max + margin)
            
            # Update Magnitude plot with same smooth scrolling
            self.axes[0, 1].set_xlim(x_min, x_max)
            
            visible_mag = mag_list[-200:] if num_samples > 200 else mag_list
            if visible_mag:
                mag_min, mag_max = min(visible_mag), max(visible_mag)
                margin = max((mag_max - mag_min) * 0.1, 0.1)
                self.axes[0, 1].set_ylim(mag_min - margin, mag_max + margin)
        
        # Update statistics (less frequently to reduce overhead)
        if frame % 20 == 0:  # Update stats every 20 frames
            self.update_statistics_display()
        
        return self.lines

    def update_statistics_display(self):
        """Update the statistics display"""
        if self.sample_count == 0:
            return
            
        elapsed_time = time.time() - self.start_time
        
        current_vals = self.last_values
        
        stats_text = f"""LIVE STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Samples: {self.sample_count:,}
Frames: {self.frame_count:,}
Spikes: {self.spike_count}
Time: {elapsed_time:.1f}s  

FREQUENCY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLE Frames: {self.instant_frame_freq:.1f} Hz
Samples: {self.instant_sample_freq:.1f} Hz

CURRENT VALUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
X: {current_vals['x']:+.3f}g
Y: {current_vals['y']:+.3f}g  
Z: {current_vals['z']:+.3f}g
Mag: {current_vals['mag']:.3f}g

DEVICE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{self.device.name if self.device else 'N/A'}
{self.device.address if self.device else 'N/A'}
"""
        
        self.stats_text.set_text(stats_text)

    def parse_chileaf_data(self, data):
        """Parse data from Chileaf protocol - ONLY accelerometer frames 0x0C"""
        try:
            # STRICT FILTER: Only Chileaf frames with command 0x0C
            if len(data) >= 3 and data[0] == self.CHILEAF_HEADER:
                command = data[2]
                
                if command == self.CHILEAF_CMD_ACCELEROMETER:
                    # Valid accelerometer frame
                    return self.parse_multi_sample_frame(data)
                else:
                    # Chileaf frame but NOT accelerometer - silently ignored
                    return False
            else:
                # Non-Chileaf frame - silently ignored
                return False
                
        except Exception as e:
            print(f"Parsing error: {e}")
            return False

    def parse_multi_sample_frame(self, data):
        """Parse Chileaf frame with possible multiple samples according to 0x0C doc"""
        # Track frame arrival time for frequency calculation
        frame_time = time.time()
        self.frame_count += 1
        
        # Calculate how many 6-byte samples are in the payload
        payload_bytes = len(data) - 4  # Exclude header, length, command and checksum
        samples_count = payload_bytes // 6
        remaining_bytes = payload_bytes % 6
        
        if (remaining_bytes != 0):
            print(f"   Warning: Incomplete sample detected - {remaining_bytes} extra bytes ignored")

        # Process all samples in the frame
        samples_processed = 0
        for i in range(samples_count):
            offset = 3 + (i * 6)  # 3 for header + i * 6 bytes per sample
            if offset + 6 <= len(data):
                sample_data = data[offset:offset+6]
                # Pass frame_time only for first sample to avoid duplicate frequency calculation
                is_first_sample = (i == 0)
                success = self.parse_single_sample(sample_data, data, sample_index=i+1, 
                                                   total_samples=samples_count, 
                                                   frame_time=frame_time if is_first_sample else None)
                if success:
                    samples_processed += 1
        
        return samples_processed > 0

    def parse_single_sample(self, accel_data, original_frame, sample_index=1, total_samples=1, frame_time=None):
        """Parse single accelerometer sample"""
        if len(accel_data) < 6:
            return False
        
        try:
            # Accelerometer parsing (6 bytes = 3 axes x 2 bytes int16 little-endian)
            rawAX, rawAY, rawAZ = struct.unpack('<hhh', accel_data)
            
            # Convert to g-force
            ax_g = rawAX / self.CHILEAF_CONVERSION_FACTOR
            ay_g = rawAY / self.CHILEAF_CONVERSION_FACTOR
            az_g = rawAZ / self.CHILEAF_CONVERSION_FACTOR
            
            # Apply Kalman filter to reduce noise while preserving dynamics
            ax_g_filtered = self.kalman_x.update(ax_g)
            ay_g_filtered = self.kalman_y.update(ay_g)
            az_g_filtered = self.kalman_z.update(az_g)
            magnitude = (ax_g_filtered**2 + ay_g_filtered**2 + az_g_filtered**2)**0.5
            
            # SPIKE DETECTION FILTER (using raw values)
            is_spike = self.detect_spike(ax_g, ay_g, az_g, magnitude, original_frame)
            
            if is_spike and total_samples == 1:  # Only for single samples
                self.spike_count += 1
                print(f"SPIKE DETECTED #{self.sample_count + 1}:")
                print(f"   Raw frame: {original_frame.hex().upper()}")
                print(f"   Sample data: {accel_data.hex().upper()}")
                print(f"   Raw values: AX={rawAX} AY={rawAY} AZ={rawAZ}")
                print(f"   G values: X={ax_g:+.3f} Y={ay_g:+.3f} Z={az_g:+.3f} Mag={magnitude:.3f}")
                print("   ---")
            
            # Add filtered values to oscilloscope buffers
            self.x_data.append(ax_g_filtered)
            self.y_data.append(ay_g_filtered)
            self.z_data.append(az_g_filtered)
            self.magnitude_data.append(magnitude)
            
            # Update statistics with filtered values
            self.last_values = {'x': ax_g_filtered, 'y': ay_g_filtered, 'z': az_g_filtered, 'mag': magnitude}
            self.sample_count += 1
            
            # Instantaneous frequency calculation (only for first sample of each frame)
            if frame_time is not None:
                self.frame_freq_window.append(frame_time)
                if len(self.frame_freq_window) >= 2:
                    time_span = self.frame_freq_window[-1] - self.frame_freq_window[0]
                    self.instant_frame_freq = (len(self.frame_freq_window) - 1) / time_span if time_span > 0 else 0
                    # Calculate sample frequency = frame_freq × samples_per_frame
                    self.instant_sample_freq = self.instant_frame_freq * total_samples
                else:
                    self.instant_frame_freq = 0
                    self.instant_sample_freq = 0
            
            # Detailed console output for multi-sample
            if total_samples > 1:
                print(f"   Sample {sample_index}/{total_samples}: X:{ax_g_filtered:+.3f} Y:{ay_g_filtered:+.3f} Z:{az_g_filtered:+.3f} Mag:{magnitude:.3f}g")
            elif self.sample_count % 15 == 0:  # More frequent output for responsiveness
                spike_marker = "SPIKE" if is_spike else "DATA"
                print(f"[{spike_marker}] #{self.sample_count:>4} | "
                      f"X:{ax_g_filtered:+.3f} Y:{ay_g_filtered:+.3f} Z:{az_g_filtered:+.3f} | "
                      f"Mag:{magnitude:.3f}g | Frame:{self.instant_frame_freq:.1f}Hz Sample:{self.instant_sample_freq:.1f}Hz")
            
            return True
            
        except struct.error as e:
            print(f"   Error unpacking sample: {e}")
            return False

    def detect_spike(self, ax, ay, az, mag, raw_data):
        """Detect TRUE sensor malfunctions (not frames from other commands)"""
        # Previous "spikes" were frames from different commands (0x38, 0x15, 0x75)
        
        # VERY permissive thresholds - only for truly impossible hardware failures
        MAX_PHYSICS_G = 50.0   # Physically impossible limit to exceed
        MIN_PHYSICS_MAG = 0.01 # Minimum physically possible magnitude
        
        # Only truly impossible hardware spikes
        is_spike = False
        
        # Extreme physical limit checks
        if (abs(ax) > MAX_PHYSICS_G or abs(ay) > MAX_PHYSICS_G or abs(az) > MAX_PHYSICS_G or
            mag > MAX_PHYSICS_G or mag < MIN_PHYSICS_MAG):
            is_spike = True
        
        # Frame length always 10 for command 0x0C
        if len(raw_data) != 10:
            is_spike = True
        
        return is_spike

    def notification_handler(self, sender, data):
        """Handle BLE notifications - ULTRA LOW LATENCY"""
        # Immediate processing without waiting - synchronous handler for min latency
        # Don't use async here because it adds overhead in BLE callback
        try:
            self.parse_chileaf_data(data)
        except Exception as e:
            # Minimal logging to not slow down
            print(f"Handler error: {e}")

    async def start_monitoring(self):
        """Start main monitoring"""
        print("\nStarting CL837 accelerometer monitoring")
        print("=" * 60)
        
        # Start oscilloscope
        self.start_oscilloscope_thread()
        
        # OPTIMIZATION: Enable notifications with maximum priority
        print("Enabling LOW-LATENCY notifications...")
            
        await self.client.start_notify(self.tx_char, self.notification_handler)
        print("LOW-LATENCY notifications enabled - Streaming in progress")
        
        # Small delay for stabilization
        await asyncio.sleep(0.1)
        
        print("\nMONITOR ACTIVE:")
        print("   - Console: updates every ~1 second")
        print("   - Oscilloscope: real-time at 20fps")
        print("   - Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            # LOW-LATENCY: More responsive loop for event handling
            while True:
                await asyncio.sleep(0.1)  # 10x more responsive for Ctrl+C and event handling
        except KeyboardInterrupt:
            print("\nUser interruption...")
        finally:
            print("Disconnecting...")
            await self.client.stop_notify(self.tx_char)

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            
            # Final statistics
            total_time = time.time() - self.start_time
            
            print("\nSESSION COMPLETED:")
            print(f"   Device: {self.device.name}")
            print(f"   Duration: {total_time:.1f}s")
            print(f"   BLE Frames received: {self.frame_count:,}")
            print(f"   Samples processed: {self.sample_count:,}")
            print(f"   Detected spikes: {self.spike_count}")
            if self.sample_count > 0:
                spike_percentage = (self.spike_count / self.sample_count) * 100
                print(f"   Spike percentage: {spike_percentage:.2f}%")
                avg_sample_freq = self.sample_count / total_time
                avg_frame_freq = self.frame_count / total_time
                avg_samples_per_frame = self.sample_count / self.frame_count if self.frame_count > 0 else 0
                print(f"   Average BLE frame frequency: {avg_frame_freq:.2f}Hz")
                print(f"   Average sample frequency: {avg_sample_freq:.2f}Hz")
                print(f"   Average samples per frame: {avg_samples_per_frame:.1f}")
            print("Disconnected")
            
            # Keep oscilloscope open
            if self.plot_ready:
                print("Oscilloscope remains open - close the window to terminate")
                try:
                    input("Press Enter to close completely...")
                except (EOFError, KeyboardInterrupt):
                    pass
                finally:
                    # Clean close of matplotlib
                    if self.fig is not None:
                        plt.close(self.fig)

async def main():
    """Main function"""
    monitor = CL837UnifiedMonitor()
    
    print("CL837 UNIFIED ACCELEROMETER MONITOR")
    print("Connection + Console Monitor + Real-Time Oscilloscope")
    print("=" * 70)
    
    try:
        # Phase 1: Connection
        if not await monitor.scan_and_connect():
            return
        
        # Phase 2: Service analysis
        if not await monitor.discover_services():
            return
        
        # Phase 3: Monitoring
        await monitor.start_monitoring()
        
    except Exception as e:
        print(f"General error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await monitor.disconnect()

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated")
    finally:
        # Clean matplotlib/tkinter resources to avoid warnings
        import matplotlib
        matplotlib.pyplot.close('all')
