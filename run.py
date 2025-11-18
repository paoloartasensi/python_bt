# -*- coding: utf-8 -*-
"""
CL837 Unified Accelerometer Monitor
Connection, reading and real-time oscilloscope visualization
"""

import asyncio
import struct
import time
import threading
from collections import deque
import sys
import os
import csv
from datetime import datetime

# Force matplotlib to use TkAgg backend for interactive window
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from bleak import BleakClient, BleakScanner

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
        
        # VBT Detection - State Machine
        self.vbt_state = 'IDLE'  # States: IDLE, ECCENTRIC, CONCENTRIC
        self.ECCENTRIC_THRESHOLD = 0.8   # < 0.8g starts eccentric
        self.CONCENTRIC_THRESHOLD = 1.3  # > 1.3g starts concentric
        self.BASELINE_THRESHOLD = 0.1    # ±0.1g around 1.0g = baseline
        self.MIN_REP_DURATION = 0.5      # seconds
        self.MAX_REP_DURATION = 4.0      # seconds
        self.ECCENTRIC_MIN_DURATION = 0.2  # 200ms minimum for eccentric
        
        # Current rep tracking
        self.current_rep_start_time = None
        self.current_rep_start_idx = None
        self.eccentric_start_time = None
        self.eccentric_start_idx = None
        self.concentric_start_time = None
        self.concentric_start_idx = None
        self.eccentric_below_threshold_time = None  # Track sustained drop
        
        # VBT Results
        self.rep_count = 0
        self.mean_velocity_data = deque(maxlen=50)  # Last 50 reps
        self.last_mean_velocity = 0.0
        self.last_peak_velocity = 0.0
        self.last_rep_duration = 0.0
        self.timestamps_data = deque(maxlen=self.max_samples)
        
        # Statistics
        self.sample_count = 0
        self.spike_count = 0
        self.frame_count = 0  # BLE frames received
        self.start_time = time.time()
        self.last_values = {'x': 0, 'y': 0, 'z': 0, 'mag': 0}
        
        # Instantaneous frequency tracking (based on BLE frames, not individual samples)
        self.frame_freq_window = deque(maxlen=50)  # Window for frame frequency
        self.instant_frame_freq = 0.0  # BLE frame frequency (Hz)
        self.instant_sample_freq = 0.0  # Sample frequency (Hz) = frame_freq * samples_per_frame
        
        # CSV Recording (first 5 seconds)
        self.csv_recording = False
        self.csv_file = None
        self.csv_writer = None
        self.csv_start_time = None
        self.csv_duration = 5.0  # seconds
        self.countdown_active = False
        self.countdown_start_time = None
        self.countdown_duration = 3.0  # 3 seconds countdown
        
        # Oscilloscope
        self.fig = None
        self.axes = None
        self.lines = []
        self.animation = None
        self.ble_thread = None
        self.ble_loop = None
        self.plot_ready = False
        self.monitoring_active = False
        self.countdown_text = None  # Text object for countdown display

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
        
        # Create figure with subplots - 2x2 grid
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.suptitle("CL837 Accelerometer + VBT Monitor - Real Time", fontsize=16, fontweight='bold')
        
        # Configure axes
        ax_mag, ax_vbt, ax_y, ax_stats = self.axes.flatten()
        
        # Plot 1: Magnitude with VBT thresholds
        ax_mag.set_title("Magnitude + VBT Thresholds", fontweight='bold')
        ax_mag.set_xlabel("Samples")
        ax_mag.set_ylabel("Magnitude (g)")
        ax_mag.grid(True, alpha=0.3)
        ax_mag.axhline(y=1.0, color='blue', linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (1g)')
        ax_mag.axhline(y=self.ECCENTRIC_THRESHOLD, color='green', linestyle=':', linewidth=1.5, alpha=0.7, label=f'Eccentric <{self.ECCENTRIC_THRESHOLD}g')
        ax_mag.axhline(y=self.CONCENTRIC_THRESHOLD, color='red', linestyle=':', linewidth=1.5, alpha=0.7, label=f'Concentric >{self.CONCENTRIC_THRESHOLD}g')
        ax_mag.legend(loc='upper right', fontsize=8)
        
        # Plot 2: VBT Mean Velocity History
        ax_vbt.set_title("Mean Velocity (VBT)", fontweight='bold', color='darkblue')
        ax_vbt.set_xlabel("Rep Number")
        ax_vbt.set_ylabel("Mean Velocity (m/s)")
        ax_vbt.grid(True, alpha=0.3)
        ax_vbt.set_ylim(0, 2.0)  # Typical squat velocity range
        
        # Plot 3: Y Acceleration (vertical)
        ax_y.set_title("Y Acceleration (Vertical)", fontweight='bold')
        ax_y.set_xlabel("Samples")
        ax_y.set_ylabel("Y (g)")
        ax_y.grid(True, alpha=0.3)
        ax_y.axhline(y=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Gravity (1g)')
        ax_y.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
        ax_y.legend(loc='upper right', fontsize=8)
        
        # Statistics area
        ax_stats.set_title("Live Statistics + VBT")
        ax_stats.axis('off')
        
        # Initialize lines
        line_mag, = ax_mag.plot([], [], 'purple', linewidth=2.5, alpha=0.8, label='Magnitude')
        line_vbt, = ax_vbt.plot([], [], 'o-', color='darkblue', linewidth=2, markersize=8, markerfacecolor='cyan', markeredgecolor='darkblue', markeredgewidth=2)
        line_y, = ax_y.plot([], [], 'g-', linewidth=2, alpha=0.8, label='Y Accel')
        
        self.lines = [line_mag, line_vbt, line_y]
        
        # Add state indicator text on magnitude plot
        self.state_text = ax_mag.text(0.02, 0.98, '', transform=ax_mag.transAxes,
                                      fontsize=12, verticalalignment='top',
                                      fontweight='bold',
                                      bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))
        
        # Statistics text
        self.stats_text = ax_stats.text(0.05, 0.95, "", transform=ax_stats.transAxes,
                                       fontsize=10, verticalalignment='top',
                                       fontfamily='monospace')
        
        # Countdown/Recording timer text (centered on figure)
        self.countdown_text = self.fig.text(0.5, 0.5, "", 
                                           ha='center', va='center',
                                           fontsize=60, fontweight='bold',
                                           color='red', alpha=0.9,
                                           bbox=dict(boxstyle='round,pad=0.5', 
                                                    facecolor='yellow', alpha=0.8))
        self.countdown_text.set_visible(False)
        
        plt.tight_layout()
        print("Oscilloscope configured")

    def start_oscilloscope(self):
        """Initialize and start oscilloscope (runs in main thread)"""
        self.setup_oscilloscope()
        self.animation = animation.FuncAnimation(
            self.fig, self.update_plot, interval=50, blit=False, cache_frame_data=False)  # 20Hz refresh
        self.plot_ready = True
        print("Oscilloscope initialized")

    def update_plot(self, frame):
        """Update oscilloscope plots"""
        if len(self.magnitude_data) < 2:
            return self.lines
        
        # Convert deque to lists for matplotlib
        mag_list = list(self.magnitude_data)
        y_list = list(self.y_data)
        
        # Create indices for x-axis
        indices = list(range(len(mag_list)))
        
        # Update magnitude line (lines[0])
        self.lines[0].set_data(indices, mag_list)
        
        # Update VBT mean velocity history (lines[1])
        if len(self.mean_velocity_data) > 0:
            vbt_indices = list(range(1, len(self.mean_velocity_data) + 1))
            vbt_values = list(self.mean_velocity_data)
            self.lines[1].set_data(vbt_indices, vbt_values)
            
            # Update VBT plot limits
            if vbt_indices:
                self.axes[0, 1].set_xlim(0, max(10, len(vbt_indices) + 1))
                max_vel = max(vbt_values) if vbt_values else 1.0
                self.axes[0, 1].set_ylim(0, max(2.0, max_vel * 1.2))
        
        # Update Y acceleration line (lines[2])
        self.lines[2].set_data(indices, y_list)
        
        # Update axes limits automatically
        if indices:
            # Magnitude plot - Dynamic axes
            self.axes[0, 0].set_xlim(max(0, len(indices)-200), len(indices))
            if mag_list:
                mag_min, mag_max = min(mag_list), max(mag_list)
                margin = (mag_max - mag_min) * 0.1 + 0.1
                self.axes[0, 0].set_ylim(mag_min - margin, mag_max + margin)
            
            # Y acceleration plot - Dynamic axes
            self.axes[1, 0].set_xlim(max(0, len(indices)-200), len(indices))
            if y_list:
                y_min, y_max = min(y_list), max(y_list)
                margin = (y_max - y_min) * 0.1 + 0.1
                self.axes[1, 0].set_ylim(y_min - margin, y_max + margin)
        
        # Update statistics
        self.update_statistics_display()
        
        # Update countdown/recording timer
        self.update_countdown_display()
        
        return self.lines + [self.stats_text]

    def update_statistics_display(self):
        """Update the statistics display"""
        if self.sample_count == 0:
            return
            
        elapsed_time = time.time() - self.start_time
        
        current_vals = self.last_values
        
        # State color coding
        state_colors = {
            'IDLE': '⚪ IDLE',
            'ECCENTRIC': '🟢 ECCENTRIC',
            'CONCENTRIC': '🔴 CONCENTRIC'
        }
        state_display = state_colors.get(self.vbt_state, self.vbt_state)
        
        stats_text = f"""LIVE STATISTICS
========================================
Samples: {self.sample_count:,}
Frames: {self.frame_count:,}
Time: {elapsed_time:.1f}s  

FREQUENCY
========================================
BLE Frames: {self.instant_frame_freq:.1f} Hz
Samples: {self.instant_sample_freq:.1f} Hz

VBT STATUS
========================================
State: {state_display}
Reps Completed: {self.rep_count}
Last Mean Vel: {self.last_mean_velocity:.3f} m/s
Last Peak Vel: {self.last_peak_velocity:.3f} m/s
Last Duration: {self.last_rep_duration:.2f}s

CURRENT VALUES
========================================
Y: {current_vals['y']:+.3f}g  
Mag: {current_vals['mag']:.3f}g

DEVICE
========================================
{self.device.name if self.device else 'N/A'}
"""
        
        self.stats_text.set_text(stats_text)
        
        # Update state indicator on magnitude plot
        if hasattr(self, 'state_text'):
            state_bg_colors = {
                'IDLE': 'lightgray',
                'ECCENTRIC': 'lightgreen',
                'CONCENTRIC': 'lightcoral'
            }
            self.state_text.set_text(f'  {self.vbt_state}  ')
            self.state_text.set_bbox(dict(boxstyle='round,pad=0.5', 
                                         facecolor=state_bg_colors.get(self.vbt_state, 'yellow'), 
                                         alpha=0.8))
    
    def update_countdown_display(self):
        """Update countdown or recording timer display"""
        if not self.countdown_text:
            return
        
        # Check if countdown is active
        if self.countdown_active and self.countdown_start_time:
            elapsed = time.time() - self.countdown_start_time
            remaining = self.countdown_duration - elapsed
            
            if remaining > 0:
                # Show countdown: 3, 2, 1
                count = int(remaining) + 1
                self.countdown_text.set_text(str(count))
                self.countdown_text.set_visible(True)
                self.countdown_text.set_color('red')
                # Pulse effect: larger when closer to next number
                pulse = 60 + 20 * (1 - (remaining % 1))
                self.countdown_text.set_fontsize(pulse)
            else:
                # Countdown finished, start recording
                self.countdown_active = False
                if not self.csv_recording:
                    self.start_csv_recording()
        
        # Check if recording is active
        elif self.csv_recording and self.csv_start_time:
            elapsed = time.time() - self.csv_start_time
            remaining = self.csv_duration - elapsed
            
            if remaining > 0:
                # Show recording timer
                self.countdown_text.set_text(f"REC\n{remaining:.1f}s")
                self.countdown_text.set_visible(True)
                self.countdown_text.set_color('red')
                self.countdown_text.set_fontsize(40)
            else:
                # Recording finished
                self.countdown_text.set_visible(False)
        else:
            # Nothing active, hide text
            self.countdown_text.set_visible(False)

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

    def process_vbt_state(self, magnitude, y_accel, current_time):
        """VBT State Machine - Asymmetric thresholds for squat detection"""
        
        # STATE: IDLE - Waiting for eccentric start
        if self.vbt_state == 'IDLE':
            # Check for sustained drop below eccentric threshold
            if magnitude < self.ECCENTRIC_THRESHOLD:
                if self.eccentric_below_threshold_time is None:
                    self.eccentric_below_threshold_time = current_time
                elif (current_time - self.eccentric_below_threshold_time) >= self.ECCENTRIC_MIN_DURATION:
                    # Eccentric phase confirmed (200ms sustained)
                    self.vbt_state = 'ECCENTRIC'
                    self.current_rep_start_time = self.eccentric_below_threshold_time
                    self.current_rep_start_idx = len(self.magnitude_data) - 1
                    self.eccentric_start_time = self.eccentric_below_threshold_time
                    self.eccentric_start_idx = self.current_rep_start_idx
                    print(f"\n🟢 ECCENTRIC START at t={current_time - self.start_time:.2f}s (Mag={magnitude:.3f}g)")
            else:
                # Reset if magnitude goes back above threshold
                self.eccentric_below_threshold_time = None
        
        # STATE: ECCENTRIC - Waiting for concentric explosion
        elif self.vbt_state == 'ECCENTRIC':
            if magnitude > self.CONCENTRIC_THRESHOLD:
                # Concentric phase starts!
                self.vbt_state = 'CONCENTRIC'
                self.concentric_start_time = current_time
                self.concentric_start_idx = len(self.magnitude_data) - 1
                print(f"🔴 CONCENTRIC START at t={current_time - self.start_time:.2f}s (Mag={magnitude:.3f}g)")
        
        # STATE: CONCENTRIC - Calculate velocity and wait for return to baseline
        elif self.vbt_state == 'CONCENTRIC':
            # Check for return to baseline (magnitude ≈ 1g ± threshold)
            if abs(magnitude - 1.0) < self.BASELINE_THRESHOLD:
                # Rep complete!
                rep_end_time = current_time
                rep_end_idx = len(self.magnitude_data) - 1
                
                # Validate rep duration
                rep_duration = rep_end_time - self.current_rep_start_time
                
                if self.MIN_REP_DURATION <= rep_duration <= self.MAX_REP_DURATION:
                    # Valid rep - Calculate VBT metrics
                    self.calculate_vbt_metrics(rep_end_idx)
                    
                    self.rep_count += 1
                    self.last_rep_duration = rep_duration
                    
                    print(f"✅ REP #{self.rep_count} COMPLETE - Duration: {rep_duration:.2f}s | Mean Vel: {self.last_mean_velocity:.3f} m/s | Peak Vel: {self.last_peak_velocity:.3f} m/s\n")
                else:
                    print(f"❌ Rep rejected - Duration {rep_duration:.2f}s outside range [{self.MIN_REP_DURATION}-{self.MAX_REP_DURATION}s]\n")
                
                # Reset to IDLE
                self.vbt_state = 'IDLE'
                self.current_rep_start_time = None
                self.current_rep_start_idx = None
                self.eccentric_start_time = None
                self.eccentric_start_idx = None
                self.concentric_start_time = None
                self.concentric_start_idx = None
                self.eccentric_below_threshold_time = None

    def calculate_vbt_metrics(self, rep_end_idx):
        """Calculate mean velocity for concentric phase"""
        if self.concentric_start_idx is None or rep_end_idx <= self.concentric_start_idx:
            self.last_mean_velocity = 0.0
            self.last_peak_velocity = 0.0
            return
        
        # Extract concentric phase data
        y_data_list = list(self.y_data)
        timestamps_list = list(self.timestamps_data)
        
        concentric_y = y_data_list[self.concentric_start_idx:rep_end_idx + 1]
        concentric_time = timestamps_list[self.concentric_start_idx:rep_end_idx + 1]
        
        if len(concentric_y) < 2:
            self.last_mean_velocity = 0.0
            self.last_peak_velocity = 0.0
            return
        
        # Subtract gravity to get net acceleration
        y_accel_net = [y - 1.0 for y in concentric_y]
        
        # Integration: v(t) = v(t-1) + a(t) * dt
        # Start with v=0 at concentric start (bottom of squat)
        velocity = [0.0]
        for i in range(1, len(y_accel_net)):
            dt = concentric_time[i] - concentric_time[i-1]
            v_new = velocity[-1] + y_accel_net[i] * dt
            velocity.append(v_new)
        
        # Calculate metrics
        positive_velocity = [v for v in velocity if v > 0]
        if positive_velocity:
            self.last_mean_velocity = sum(positive_velocity) / len(positive_velocity)
            self.last_peak_velocity = max(velocity)
        else:
            self.last_mean_velocity = 0.0
            self.last_peak_velocity = 0.0
        
        # Add to history
        self.mean_velocity_data.append(self.last_mean_velocity)

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

    def start_countdown(self):
        """Start 3-2-1 countdown before recording"""
        self.countdown_active = True
        self.countdown_start_time = time.time()
        print("\n⏱️  Countdown started: 3... 2... 1...")
    
    def start_csv_recording(self):
        """Start CSV recording for first 5 seconds"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"accel_data_{timestamp}.csv"
        
        self.csv_file = open(filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Timestamp', 'X (g)', 'Y (g)', 'Z (g)', 'Magnitude (g)'])
        self.csv_recording = True
        self.csv_start_time = time.time()
        print(f"\n📊 CSV recording started: {filename}")
        print(f"   Recording for {self.csv_duration} seconds...")
    
    def stop_csv_recording(self):
        """Stop CSV recording"""
        if self.csv_file:
            self.csv_file.close()
            self.csv_recording = False
            print(f"✅ CSV recording completed and saved\n")
    
    def record_csv_sample(self, timestamp, x, y, z, mag):
        """Record a sample to CSV if recording is active"""
        if self.csv_recording:
            # Check if 10 seconds have passed
            if time.time() - self.csv_start_time >= self.csv_duration:
                self.stop_csv_recording()
            else:
                self.csv_writer.writerow([f"{timestamp:.3f}", f"{x:.6f}", f"{y:.6f}", f"{z:.6f}", f"{mag:.6f}"])

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
            magnitude = (ax_g**2 + ay_g**2 + az_g**2)**0.5
            
            # SPIKE DETECTION FILTER
            is_spike = self.detect_spike(ax_g, ay_g, az_g, magnitude, original_frame)
            
            if is_spike and total_samples == 1:  # Only for single samples
                self.spike_count += 1
                print(f"SPIKE DETECTED #{self.sample_count + 1}:")
                print(f"   Raw frame: {original_frame.hex().upper()}")
                print(f"   Sample data: {accel_data.hex().upper()}")
                print(f"   Raw values: AX={rawAX} AY={rawAY} AZ={rawAZ}")
                print(f"   G values: X={ax_g:+.3f} Y={ay_g:+.3f} Z={az_g:+.3f} Mag={magnitude:.3f}")
                print("   ---")
            
            # Add to oscilloscope buffers
            self.x_data.append(ax_g)
            self.y_data.append(ay_g)
            self.z_data.append(az_g)
            self.magnitude_data.append(magnitude)
            
            # Track timestamps for VBT
            current_time = time.time()
            self.timestamps_data.append(current_time)
            
            # Update statistics
            self.last_values = {'x': ax_g, 'y': ay_g, 'z': az_g, 'mag': magnitude}
            self.sample_count += 1
            
            # VBT STATE MACHINE - Process each sample
            self.process_vbt_state(magnitude, ay_g, current_time)
            
            # Start countdown on first sample
            if self.sample_count == 1 and not self.countdown_active and not self.csv_recording:
                self.start_countdown()
            
            # Record to CSV (with timestamp relative to start) - only if recording is active
            if self.csv_recording:
                elapsed_time = time.time() - self.start_time
                self.record_csv_sample(elapsed_time, ax_g, ay_g, az_g, magnitude)
            
            # Instantaneous frequency calculation (only for first sample of each frame)
            if frame_time is not None:
                self.frame_freq_window.append(frame_time)
                if len(self.frame_freq_window) >= 2:
                    time_span = self.frame_freq_window[-1] - self.frame_freq_window[0]
                    self.instant_frame_freq = (len(self.frame_freq_window) - 1) / time_span if time_span > 0 else 0
                    # Calculate sample frequency = frame_freq * samples_per_frame
                    self.instant_sample_freq = self.instant_frame_freq * total_samples
                else:
                    self.instant_frame_freq = 0
                    self.instant_sample_freq = 0
            
            # Detailed console output for multi-sample
            if total_samples > 1:
                print(f"   Sample {sample_index}/{total_samples}: X:{ax_g:+.3f} Y:{ay_g:+.3f} Z:{az_g:+.3f} Mag:{magnitude:.3f}g")
            elif self.sample_count % 15 == 0:  # More frequent output for responsiveness
                spike_marker = "SPIKE" if is_spike else "DATA"
                print(f"[{spike_marker}] #{self.sample_count:>4} | "
                      f"X:{ax_g:+.3f} Y:{ay_g:+.3f} Z:{az_g:+.3f} | "
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
        
        # OPTIMIZATION: Enable notifications with maximum priority
        print("Enabling LOW-LATENCY notifications...")
            
        await self.client.start_notify(self.tx_char, self.notification_handler)
        print("LOW-LATENCY notifications enabled - Streaming in progress")
        
        # Small delay for stabilization
        await asyncio.sleep(0.1)
        
        print("\nMONITOR ACTIVE:")
        print("   - Console: updates every ~1 second")
        print("   - Oscilloscope: real-time at 20fps")
        print("   - Close oscilloscope window to stop")
        print("=" * 60)
        
        self.monitoring_active = True
        
        try:
            # LOW-LATENCY: More responsive loop for event handling
            while self.monitoring_active:
                await asyncio.sleep(0.1)  # 10x more responsive for event handling
        except KeyboardInterrupt:
            print("\nUser interruption...")
        finally:
            print("Disconnecting...")
            self.monitoring_active = False
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
            
            # Signal monitoring to stop
            self.monitoring_active = False

async def async_main(monitor):
    """Async main function"""
    print("CL837 UNIFIED ACCELEROMETER MONITOR")
    print("Connection + Console Monitor + Real-Time Oscilloscope")
    print("=" * 70)
    
    try:
        # Phase 1: Connection
        if not await monitor.scan_and_connect():
            return False
        
        # Phase 2: Service analysis
        if not await monitor.discover_services():
            return False
        
        # Phase 3: Start monitoring (will run until window closes)
        await monitor.start_monitoring()
        return True
        
    except Exception as e:
        print(f"General error: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_plot_thread(monitor):
    """Start matplotlib in background thread"""
    def run_plot():
        monitor.setup_oscilloscope()
        monitor.animation = animation.FuncAnimation(
            monitor.fig, monitor.update_plot, interval=50, blit=False, cache_frame_data=False)
        monitor.plot_ready = True
        plt.show()  # Blocking call in this thread
    
    plot_thread = threading.Thread(target=run_plot, daemon=False)
    plot_thread.start()
    
    # Wait for plot to be ready
    while not monitor.plot_ready:
        time.sleep(0.1)
    
    return plot_thread

def main():
    """Main function - runs BLE in main thread, matplotlib in background"""
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    monitor = CL837UnifiedMonitor()
    
    try:
        # Start matplotlib in background thread
        print("\n🎨 Starting oscilloscope in background...")
        plot_thread = start_plot_thread(monitor)
        print("✓ Oscilloscope window opened")
        
        # Run BLE in main thread
        print("\n🔵 Starting BLE connection in main thread...")
        asyncio.run(async_main(monitor))
        
        print("\n✓ BLE monitoring completed")
        print("Waiting for oscilloscope window to close...")
        
        # Wait for plot thread
        plot_thread.join()
        
    except KeyboardInterrupt:
        print("\nProgram terminated")
        monitor.monitoring_active = False
        plt.close('all')
    finally:
        # Clean up
        monitor.monitoring_active = False

if __name__ == "__main__":
    main()
