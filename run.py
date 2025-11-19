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
        
        # VBT Detection - Pattern Matching (buffered analysis)
        self.BASELINE_ZONE = 0.08  # ±8% around baseline = stable
        self.MIN_REP_DURATION = 0.8  # Increased from 0.5 - squat takes time
        self.MAX_REP_DURATION = 4.0
        self.REFRACTORY_PERIOD = 1.0  # Increased from 0.8 - more time between reps
        self.ANALYSIS_BUFFER_SIZE = 100  # samples to analyze (2-4 sec @ 25-50Hz)
        self.ANALYSIS_INTERVAL = 0.2  # seconds between pattern analysis runs
        self.MIN_DEPTH_THRESHOLD = 0.90  # Minimum depth: must go below 0.90g (relaxed for explosive movements)
        self.MIN_CONCENTRIC_SAMPLES = 5  # Minimum samples in concentric phase (reduced for explosive)
        self.MIN_ECCENTRIC_SAMPLES = 5  # Minimum samples in eccentric phase (reduced for explosive)
        self.MIN_ECCENTRIC_RANGE = 0.05  # Minimum magnitude decrease during eccentric (g) - reduced for quick dips
        self.MIN_CONCENTRIC_ACCEL = 0.10  # Minimum peak acceleration during concentric (g above baseline) - reduced
        
        # Pattern matching state
        self.signal_states = deque(maxlen=self.ANALYSIS_BUFFER_SIZE)  # Track ABOVE/BELOW/BASE states
        self.last_pattern_analysis_time = 0
        self.last_rep_end_time = -self.REFRACTORY_PERIOD
        self.baseline_value = 1.0  # Will be calculated from first samples
        self.baseline_calculated = False
        self.pending_reps = []  # Reps detected but not yet finalized
        
        # VBT Results - Extended metrics
        self.rep_count = 0
        self.mean_velocity_data = deque(maxlen=50)  # Last 50 reps
        self.mpv_data = deque(maxlen=50)  # MPV for each rep
        self.last_mean_velocity = 0.0
        self.last_peak_velocity = 0.0
        self.last_mean_propulsive_velocity = 0.0
        self.last_time_to_peak_velocity = 0.0
        self.last_concentric_displacement = 0.0
        self.last_mean_power = 0.0
        self.last_peak_power = 0.0
        self.last_mean_propulsive_power = 0.0
        self.last_rep_duration = 0.0
        self.last_eccentric_duration = 0.0
        self.last_concentric_duration = 0.0
        self.timestamps_data = deque(maxlen=self.max_samples)
        
        # Velocity Loss tracking
        self.first_rep_mean_velocity = None
        self.velocity_loss_percent = 0.0
        
        # Mass for power calculation (kg) - default 1kg, should be set to athlete + bar weight
        self.MASS = 1.0
        
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
        
        # CSV Recording (first 20 seconds)
        self.csv_recording = False
        self.csv_file = None
        self.csv_writer = None
        self.csv_start_time = None
        self.csv_duration = 20.0  # seconds
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
        
        # Plot 1: Magnitude with Pattern Matching zones
        ax_mag.set_title("Magnitude + Pattern Matching Zones", fontweight='bold')
        ax_mag.set_xlabel("Samples")
        ax_mag.set_ylabel("Magnitude (g)")
        ax_mag.grid(True, alpha=0.3)
        ax_mag.axhline(y=1.0, color='blue', linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (1g)')
        # Baseline zones will be drawn dynamically after calibration
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
            mpv_values = list(self.mpv_data)
            self.lines[1].set_data(vbt_indices, vbt_values)
            
            # Clear previous text annotations
            for txt in self.axes[0, 1].texts[:]:
                txt.remove()
            
            # Add MPV text annotations for each rep
            for i, (x, y, mpv) in enumerate(zip(vbt_indices, vbt_values, mpv_values)):
                self.axes[0, 1].text(x, y + 0.05, f'{mpv:.3f}',
                                    ha='center', va='bottom',
                                    fontsize=8, fontweight='bold',
                                    color='darkgreen',
                                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.7))
            
            # Update VBT plot limits
            if vbt_indices:
                self.axes[0, 1].set_xlim(0, max(10, len(vbt_indices) + 1))
                max_vel = max(vbt_values) if vbt_values else 1.0
                self.axes[0, 1].set_ylim(0, max(2.0, max_vel * 1.3))  # Extra margin for text
        
        # Update Y acceleration line (lines[2])
        self.lines[2].set_data(indices, y_list)
        
        # Draw baseline zones after calibration (one-time)
        if self.baseline_calculated and not hasattr(self, 'baseline_zones_drawn'):
            baseline_upper = self.baseline_value * (1 + self.BASELINE_ZONE)
            baseline_lower = self.baseline_value * (1 - self.BASELINE_ZONE)
            self.axes[0, 0].axhline(y=baseline_upper, color='red', linestyle=':', linewidth=1.5, alpha=0.5, label=f'Upper Zone (+{self.BASELINE_ZONE*100:.0f}%)')
            self.axes[0, 0].axhline(y=baseline_lower, color='green', linestyle=':', linewidth=1.5, alpha=0.5, label=f'Lower Zone (-{self.BASELINE_ZONE*100:.0f}%)')
            self.axes[0, 0].fill_between([0, self.max_samples], baseline_lower, baseline_upper, color='yellow', alpha=0.1, label='Stable Zone')
            self.axes[0, 0].legend(loc='upper right', fontsize=8)
            self.baseline_zones_drawn = True
        
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
        
        # Pattern matching status
        if self.baseline_calculated:
            pattern_status = f"🟢 ACTIVE (Buffer: {len(self.magnitude_data)} samples)"
        else:
            pattern_status = "⚪ CALIBRATING..."
        state_display = pattern_status
        
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
Reps: {self.rep_count}

VELOCITY
Mean: {self.last_mean_velocity:.3f} m/s
Peak: {self.last_peak_velocity:.3f} m/s
MPV: {self.last_mean_propulsive_velocity:.3f} m/s
Time to Peak: {self.last_time_to_peak_velocity:.3f}s

POWER
Mean: {self.last_mean_power:.1f} W
Peak: {self.last_peak_power:.1f} W
MPP: {self.last_mean_propulsive_power:.1f} W

DISPLACEMENT & TIME
ROM: {self.last_concentric_displacement:.3f} m
TUT: {self.last_rep_duration:.2f}s
Ecc: {self.last_eccentric_duration:.2f}s
Conc: {self.last_concentric_duration:.2f}s

FATIGUE
VL%: {self.velocity_loss_percent:.1f}%

CURRENT VALUES
========================================
Y: {current_vals['y']:+.3f}g  
Mag: {current_vals['mag']:.3f}g

DEVICE
========================================
{self.device.name if self.device else 'N/A'}
"""
        
        self.stats_text.set_text(stats_text)
        
        # Update pattern matching indicator on magnitude plot
        if hasattr(self, 'state_text'):
            if self.baseline_calculated:
                status_text = 'MONITORING'
                bg_color = 'lightgreen'
            else:
                status_text = 'CALIBRATING'
                bg_color = 'lightyellow'
            self.state_text.set_text(f'  {status_text}  ')
            self.state_text.set_bbox(dict(boxstyle='round,pad=0.5', 
                                         facecolor=bg_color, 
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

    def analyze_pattern_buffer(self, current_time):
        """Analyze buffered signal for pattern matching - runs periodically"""
        if len(self.magnitude_data) < 20:  # Need minimum samples
            return
        
        # Calculate baseline from first stable samples if not done
        if not self.baseline_calculated and len(self.magnitude_data) >= 30:
            mag_list = list(self.magnitude_data)
            self.baseline_value = sum(mag_list[:30]) / 30
            self.baseline_calculated = True
            print(f"\n📊 Baseline calculated: {self.baseline_value:.3f}g")
        
        if not self.baseline_calculated:
            return
        
        baseline_upper = self.baseline_value * (1 + self.BASELINE_ZONE)
        baseline_lower = self.baseline_value * (1 - self.BASELINE_ZONE)
        
        # Classify recent samples into states
        mag_list = list(self.magnitude_data)
        time_list = list(self.timestamps_data)
        
        # Look for state transitions in buffer
        state_changes = []
        prev_state = 'BASE'
        
        for i in range(max(0, len(mag_list) - self.ANALYSIS_BUFFER_SIZE), len(mag_list)):
            mag = mag_list[i]
            
            if mag > baseline_upper:
                current_state = 'ABOVE'
            elif mag < baseline_lower:
                current_state = 'BELOW'
            else:
                current_state = 'BASE'
            
            if current_state != prev_state:
                state_changes.append({
                    'idx': i,
                    'time': time_list[i],
                    'from': prev_state,
                    'to': current_state,
                    'mag': mag
                })
                prev_state = current_state
        
        # Pattern matching: BASE → movement → BASE
        for i in range(len(state_changes) - 1):
            if state_changes[i]['from'] == 'BASE':
                rep_start_idx = state_changes[i]['idx']
                rep_start_time = state_changes[i]['time']
                
                # Apply refractory period
                if rep_start_time - self.last_rep_end_time < self.REFRACTORY_PERIOD:
                    continue
                
                # Look for return to BASE
                for j in range(i + 1, len(state_changes)):
                    if state_changes[j]['to'] == 'BASE':
                        rep_end_idx = state_changes[j]['idx']
                        rep_end_time = state_changes[j]['time']
                        rep_duration = rep_end_time - rep_start_time
                        
                        # Validate duration
                        if self.MIN_REP_DURATION <= rep_duration <= self.MAX_REP_DURATION:
                            # Find bottom and concentric peak
                            rep_segment = mag_list[rep_start_idx:rep_end_idx + 1]
                            
                            if len(rep_segment) < 20:  # Need minimum samples
                                continue
                            
                            bottom_relative = rep_segment.index(min(rep_segment))
                            bottom_idx = rep_start_idx + bottom_relative
                            bottom_mag = rep_segment[bottom_relative]
                            
                            # VALIDATION 1: Check depth - must go below threshold
                            if bottom_mag >= self.MIN_DEPTH_THRESHOLD:
                                continue  # Not deep enough for a squat
                            
                            # VALIDATION 2: Check eccentric phase has minimum samples
                            if bottom_relative < self.MIN_ECCENTRIC_SAMPLES:
                                continue  # Too fast descent = not a controlled squat
                            
                            # VALIDATION 3: Check eccentric pattern - magnitude must decrease progressively
                            eccentric_segment = rep_segment[:bottom_relative + 1]
                            eccentric_start_mag = eccentric_segment[0]
                            eccentric_range = eccentric_start_mag - bottom_mag
                            
                            if eccentric_range < self.MIN_ECCENTRIC_RANGE:
                                continue  # Not enough movement = just standing or small oscillation
                            
                            # Check for progressive descent (at least 60% of samples should show downward trend)
                            decreasing_count = sum(1 for i in range(1, len(eccentric_segment)) 
                                                  if eccentric_segment[i] <= eccentric_segment[i-1])
                            descent_ratio = decreasing_count / len(eccentric_segment) if len(eccentric_segment) > 1 else 0
                            
                            if descent_ratio < 0.3:  # At least 30% progressive descent (relaxed for explosive)
                                continue  # Not a controlled descent pattern
                            
                            # Concentric peak after bottom
                            if bottom_relative < len(rep_segment) - 1:
                                concentric_segment = rep_segment[bottom_relative:]
                                concentric_peak_relative = concentric_segment.index(max(concentric_segment))
                                concentric_peak_idx = bottom_idx + concentric_peak_relative
                                
                                # VALIDATION 4: Check concentric phase has minimum samples
                                if concentric_peak_relative < self.MIN_CONCENTRIC_SAMPLES:
                                    continue  # Too fast ascent = not a proper squat
                                
                                # VALIDATION 5: Concentric peak should be higher than bottom
                                peak_mag = concentric_segment[concentric_peak_relative]
                                if peak_mag <= bottom_mag + 0.05:  # At least 0.05g difference
                                    continue  # No clear concentric phase
                                
                                # VALIDATION 6: Check concentric has sufficient acceleration above baseline
                                # This ensures real upward movement, not just recovery to standing
                                max_concentric_accel = max(concentric_segment) - self.baseline_value
                                if max_concentric_accel < self.MIN_CONCENTRIC_ACCEL:
                                    continue  # Not enough upward acceleration = no real concentric effort
                            else:
                                concentric_peak_idx = rep_end_idx
                            
                            # Calculate VBT metrics
                            self.calculate_vbt_metrics_from_indices(
                                bottom_idx, concentric_peak_idx, rep_end_idx,
                                time_list[bottom_idx], time_list[concentric_peak_idx],
                                rep_start_time, rep_end_time
                            )
                            
                            self.rep_count += 1
                            self.last_rep_duration = rep_duration
                            self.last_rep_end_time = rep_end_time
                            
                            print(f"\n✅ REP #{self.rep_count} DETECTED (buffered)")
                            print(f"   Depth: {bottom_mag:.3f}g | Range: {eccentric_range:.3f}g | Descent: {descent_ratio*100:.0f}%")
                            print(f"   Concentric Accel: {max_concentric_accel:.3f}g | Peak Mag: {peak_mag:.3f}g")
                            print(f"   Samples: Ecc={bottom_relative} Conc={concentric_peak_relative - bottom_relative}")
                            print(f"   Duration: TUT={rep_duration:.2f}s | Ecc={self.last_eccentric_duration:.2f}s | Conc={self.last_concentric_duration:.2f}s")
                            print(f"   Velocity: Mean={self.last_mean_velocity:.3f} m/s | Peak={self.last_peak_velocity:.3f} m/s | MPV={self.last_mean_propulsive_velocity:.3f} m/s")
                            print(f"   Power: Mean={self.last_mean_power:.1f}W | Peak={self.last_peak_power:.1f}W | MPP={self.last_mean_propulsive_power:.1f}W")
                            print(f"   ROM: {self.last_concentric_displacement:.3f}m | VL: {self.velocity_loss_percent:.1f}%\n")
                            
                            break  # Process one rep at a time

    def calculate_vbt_metrics_from_indices(self, bottom_idx, concentric_peak_idx, rep_end_idx,
                                           bottom_time, concentric_peak_time, rep_start_time, rep_end_time):
        """Calculate all VBT metrics from explicit indices"""
        if concentric_peak_idx <= bottom_idx:
            self.reset_vbt_metrics()
            return
        
        # Extract concentric phase data (bottom to peak)
        mag_data_list = list(self.magnitude_data)
        timestamps_list = list(self.timestamps_data)
        
        concentric_mag = mag_data_list[bottom_idx:concentric_peak_idx + 1]
        concentric_time = timestamps_list[bottom_idx:concentric_peak_idx + 1]
        
        if len(concentric_mag) < 2:
            self.reset_vbt_metrics()
            return
        
        # Use the calibrated baseline value (not fixed 1.0)
        baseline_value = self.baseline_value
        mag_accel_net = [mag - baseline_value for mag in concentric_mag]
        
        # DEBUG: Print concentric data for analysis
        print(f"\n🔍 DEBUG VBT Calculation:")
        print(f"   Baseline used: {baseline_value:.3f}g")
        print(f"   Concentric mag range: {min(concentric_mag):.3f}g to {max(concentric_mag):.3f}g")
        print(f"   Net accel range: {min(mag_accel_net):.3f}g to {max(mag_accel_net):.3f}g")
        print(f"   Samples in concentric: {len(concentric_mag)}")
        
        # Integration: velocity and displacement
        velocity = [0.0]
        displacement = [0.0]
        for i in range(1, len(mag_accel_net)):
            dt = concentric_time[i] - concentric_time[i-1]
            v_new = velocity[-1] + mag_accel_net[i] * dt
            velocity.append(v_new)
            d_new = displacement[-1] + v_new * dt
            displacement.append(d_new)
        
        # Metriche VBT di base
        positive_velocity = [v for v in velocity if v > 0]
        if positive_velocity:
            self.last_mean_velocity = sum(positive_velocity) / len(positive_velocity)
            self.last_peak_velocity = max(velocity)
            
            # Mean Propulsive Velocity (MPV) - solo dove accelerazione è positiva
            propulsive_indices = [i for i, a in enumerate(mag_accel_net) if a > 0 and i > 0]
            if propulsive_indices:
                propulsive_velocities = [velocity[i] for i in propulsive_indices]
                self.last_mean_propulsive_velocity = sum(propulsive_velocities) / len(propulsive_velocities)
            else:
                self.last_mean_propulsive_velocity = 0.0
        else:
            self.last_mean_velocity = 0.0
            self.last_peak_velocity = 0.0
            self.last_mean_propulsive_velocity = 0.0
        
        # Time to Peak Velocity
        peak_vel_idx = velocity.index(max(velocity))
        self.last_time_to_peak_velocity = concentric_time[peak_vel_idx] - concentric_time[0]
        
        # ROM (Range of Motion)
        self.last_concentric_displacement = displacement[-1]
        
        # Calcolo potenza (P = m * a * v)
        power = [self.MASS * mag_accel_net[i] * velocity[i] for i in range(len(velocity))]
        positive_power = [p for p in power if p > 0]
        if positive_power:
            self.last_mean_power = sum(positive_power) / len(positive_power)
            self.last_peak_power = max(power)
        else:
            self.last_mean_power = 0.0
            self.last_peak_power = 0.0
        
        # Mean Propulsive Power
        propulsive_indices = [i for i, a in enumerate(mag_accel_net) if a > 0]
        if propulsive_indices:
            propulsive_power = [power[i] for i in propulsive_indices]
            self.last_mean_propulsive_power = sum(propulsive_power) / len(propulsive_power) if propulsive_power else 0.0
        else:
            self.last_mean_propulsive_power = 0.0
        
        # Durate
        self.last_eccentric_duration = bottom_time - rep_start_time
        self.last_concentric_duration = concentric_time[-1] - concentric_time[0]
        
        # Velocity Loss calculation
        if self.first_rep_mean_velocity is None:
            self.first_rep_mean_velocity = self.last_mean_velocity
        if self.first_rep_mean_velocity > 0:
            self.velocity_loss_percent = ((self.first_rep_mean_velocity - self.last_mean_velocity) / self.first_rep_mean_velocity) * 100
        
        # Add to history
        self.mean_velocity_data.append(self.last_mean_velocity)
        self.mpv_data.append(self.last_mean_propulsive_velocity)
    
    def reset_vbt_metrics(self):
        """Reset all VBT metrics to zero"""
        self.last_mean_velocity = 0.0
        self.last_peak_velocity = 0.0
        self.last_mean_propulsive_velocity = 0.0
        self.last_time_to_peak_velocity = 0.0
        self.last_concentric_displacement = 0.0
        self.last_mean_power = 0.0
        self.last_peak_power = 0.0
        self.last_mean_propulsive_power = 0.0

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
            
            # PATTERN ANALYSIS - Run periodically (not every sample for efficiency)
            if current_time - self.last_pattern_analysis_time >= self.ANALYSIS_INTERVAL:
                self.analyze_pattern_buffer(current_time)
                self.last_pattern_analysis_time = current_time
            
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
