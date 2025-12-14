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
        self.velocity_data = deque(maxlen=self.max_samples)  # Integrated velocity for real-time plot
        
        # VBT Detection - Real-time State Machine (production-ready like Vitruve, Enode, Beast)
        # Velocity thresholds (m/s)
        self.VEL_ECCENTRIC_THRESHOLD = -0.12  # Must be < this for eccentric detection (200-250ms window)
        self.VEL_CONCENTRIC_THRESHOLD = 0.08   # Must drop < this to close rep
        self.VEL_ZERO_CROSSING_TOLERANCE = 0.03  # Window around zero for bottom detection
        
        # Temporal windows (seconds) - like commercial devices
        self.MIN_ECCENTRIC_WINDOW = 0.20   # 200ms minimum eccentric phase (like Vitruve)
        self.MAX_CONCENTRIC_WINDOW = 1.5   # 1.5s maximum concentric phase
        self.MIN_CONCENTRIC_DURATION = 0.15  # 150ms minimum concentric
        self.REFRACTORY_PERIOD = 0.5       # 500ms between reps
        
        # Smoothing for velocity state detection
        self.VEL_SMOOTH_WINDOW = 5  # samples for moving average (50-100ms @ 50Hz)
        
        # Real-time State Machine (like commercial VBT devices)
        self.vbt_state = 'REST'  # States: REST, ECCENTRIC, CONCENTRIC
        self.eccentric_start_time = None
        self.eccentric_start_idx = None
        self.bottom_time = None
        self.bottom_idx = None
        self.concentric_start_time = None
        self.concentric_start_idx = None
        self.last_rep_end_time = -self.REFRACTORY_PERIOD
        self.baseline_value = 1.0  # Will be calculated from first samples
        self.baseline_calculated = False
        self.baseline_samples = []  # Accumulate first samples for baseline calculation
        self.BASELINE_SAMPLES_COUNT = 25  # Number of samples to use for baseline (~0.5s at 50Hz)
        
        # Velocity smoothing buffer for state detection
        self.velocity_smooth_buffer = deque(maxlen=self.VEL_SMOOTH_WINDOW)
        
        # State history for visualization
        self.state_history = deque(maxlen=10)  # Last 10 reps for temporal display
        
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
        
        # Real-time velocity integration
        self.current_velocity = 0.0  # Current integrated velocity (m/s)
        
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
            print("   (timeout: 20s - assicurati che il dispositivo sia vicino e non connesso ad altre app)")
            # Aumentato timeout per connessioni più lente
            self.client = BleakClient(target_device, timeout=20.0)
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
            import traceback
            print(f"Connection error: {e}")
            traceback.print_exc()
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

    def on_close(self, event):
        """Handle window close event"""
        print("\n🔴 Closing oscilloscope window...")
        self.monitoring_active = False
        plt.close('all')
    
    def setup_oscilloscope(self):
        """Initialize matplotlib oscilloscope"""
        print("Initializing oscilloscope...")
        
        # Create figure with subplots - 2x2 grid
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.suptitle("CL837 Accelerometer + VBT Monitor - Real Time", fontsize=16, fontweight='bold')
        
        # Register close event handler
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        
        # Configure axes
        ax_mag, ax_vbt, ax_y, ax_stats = self.axes.flatten()
        
        # Plot 1: Magnitude with Pattern Matching zones + Velocity
        ax_mag.set_title("Magnitude + Velocity (Real-Time Integration)", fontweight='bold')
        ax_mag.set_xlabel("Samples")
        ax_mag.set_ylabel("Magnitude (g)", color='purple', fontweight='bold')
        ax_mag.tick_params(axis='y', labelcolor='purple')
        ax_mag.grid(True, alpha=0.3)
        ax_mag.axhline(y=1.0, color='blue', linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (1g)')
        
        # Create second Y-axis for velocity
        self.ax_velocity = ax_mag.twinx()
        self.ax_velocity.set_ylabel('Velocity (m/s)', color='navy', fontweight='bold')
        self.ax_velocity.tick_params(axis='y', labelcolor='navy')
        self.ax_velocity.axhline(y=0, color='navy', linestyle=':', linewidth=1, alpha=0.3)
        
        # Baseline zones will be drawn dynamically after calibration
        ax_mag.legend(loc='upper left', fontsize=8)
        
        # Plot 2: VBT Mean Velocity History
        ax_vbt.set_title("Mean Velocity (VBT)", fontweight='bold', color='darkblue')
        ax_vbt.set_xlabel("Rep Number")
        ax_vbt.set_ylabel("Mean Velocity (m/s)")
        ax_vbt.grid(True, alpha=0.3)
        ax_vbt.set_ylim(0, 2.0)  # Typical squat velocity range
        
        # Plot 3: VBT Temporal Windows (Real-Time State Visualization)
        ax_y.set_title("VBT State Machine (Real-Time)", fontweight='bold', color='darkgreen')
        ax_y.set_xlabel("Time (last 10 reps)")
        ax_y.set_ylabel("State")
        ax_y.set_ylim(-0.5, 3.5)
        ax_y.set_yticks([0, 1, 2, 3])
        ax_y.set_yticklabels(['REST', 'ECCENTRIC', 'BOTTOM', 'CONCENTRIC'])
        ax_y.grid(True, alpha=0.3, axis='x')
        ax_y.axhline(y=0.5, color='gray', linestyle=':', linewidth=0.5, alpha=0.3)
        ax_y.axhline(y=1.5, color='gray', linestyle=':', linewidth=0.5, alpha=0.3)
        ax_y.axhline(y=2.5, color='gray', linestyle=':', linewidth=0.5, alpha=0.3)
        
        # Statistics area
        ax_stats.set_title("Live Statistics + VBT")
        ax_stats.axis('off')
        
        # Initialize lines
        line_mag, = ax_mag.plot([], [], 'purple', linewidth=2.5, alpha=0.8, label='Magnitude')
        line_vbt, = ax_vbt.plot([], [], 'o-', color='darkblue', linewidth=2, markersize=8, markerfacecolor='cyan', markeredgecolor='darkblue', markeredgewidth=2)
        line_velocity, = self.ax_velocity.plot([], [], 'navy', linewidth=2, linestyle='--', alpha=0.8, label='Velocity')
        
        self.lines = [line_mag, line_vbt, line_velocity]
        
        # VBT temporal windows tracking
        self.vbt_windows = []  # List of dicts with {rep_num, ecc_start, bottom, conc_end, durations}
        self.ax_temporal = ax_y  # Reference for temporal window plot
        
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
        
        # Update velocity line (lines[2]) on second Y-axis
        if len(self.velocity_data) > 0:
            vel_list = list(self.velocity_data)
            self.lines[2].set_data(indices, vel_list)
            
            # Update velocity axis limits
            if vel_list:
                vel_min, vel_max = min(vel_list), max(vel_list)
                vel_range = max(abs(vel_min), abs(vel_max))
                margin = vel_range * 0.2 + 0.1
                self.ax_velocity.set_ylim(-vel_range - margin, vel_range + margin)
        
        # Update axes limits automatically
        if indices:
            # Magnitude plot - Dynamic axes
            self.axes[0, 0].set_xlim(max(0, len(indices)-200), len(indices))
            if mag_list:
                mag_min, mag_max = min(mag_list), max(mag_list)
                margin = (mag_max - mag_min) * 0.1 + 0.1
                self.axes[0, 0].set_ylim(mag_min - margin, mag_max + margin)
        
        # Update temporal windows bar plot
        self.update_temporal_windows_plot()
        
        # Update statistics
        self.update_statistics_display()
        
        # Update countdown/recording timer
        self.update_countdown_display()
        
        return self.lines + [self.stats_text]

    def update_temporal_windows_plot(self):
        """Update the temporal windows bar plot showing VBT states"""
        # Clear previous bars
        self.ax_temporal.clear()
        
        # Reconfigure axes
        self.ax_temporal.set_title("VBT State Machine (Real-Time)", fontweight='bold', color='darkgreen')
        self.ax_temporal.set_xlabel("Rep Number")
        self.ax_temporal.set_ylabel("Phase Duration (s)")
        self.ax_temporal.grid(True, alpha=0.3, axis='y')
        
        if not self.state_history:
            self.ax_temporal.text(0.5, 0.5, 'Waiting for first rep...', 
                                 transform=self.ax_temporal.transAxes,
                                 ha='center', va='center', fontsize=12, color='gray')
            return
        
        # Prepare data for stacked bars
        rep_nums = [entry['rep_num'] for entry in self.state_history]
        ecc_durations = [entry['ecc_duration'] for entry in self.state_history]
        conc_durations = [entry['conc_duration'] for entry in self.state_history]
        
        # Create stacked bars
        bar_width = 0.6
        bars_ecc = self.ax_temporal.bar(rep_nums, ecc_durations, bar_width, 
                                        label='Eccentric', color='#FF6B6B', alpha=0.8)
        bars_conc = self.ax_temporal.bar(rep_nums, conc_durations, bar_width,
                                         bottom=ecc_durations,
                                         label='Concentric', color='#4ECDC4', alpha=0.8)
        
        # Add duration labels on bars
        for i, (rep_num, ecc_dur, conc_dur) in enumerate(zip(rep_nums, ecc_durations, conc_durations)):
            total = ecc_dur + conc_dur
            # Eccentric label
            self.ax_temporal.text(rep_num, ecc_dur/2, f'{ecc_dur:.2f}s',
                                 ha='center', va='center', fontsize=8, fontweight='bold', color='white')
            # Concentric label
            self.ax_temporal.text(rep_num, ecc_dur + conc_dur/2, f'{conc_dur:.2f}s',
                                 ha='center', va='center', fontsize=8, fontweight='bold', color='white')
            # Total label above bar
            self.ax_temporal.text(rep_num, total + 0.05, f'{total:.2f}s',
                                 ha='center', va='bottom', fontsize=7, color='black')
        
        # Configure axes
        if rep_nums:
            self.ax_temporal.set_xlim(min(rep_nums) - 0.5, max(rep_nums) + 0.5)
            self.ax_temporal.set_xticks(rep_nums)
        
        self.ax_temporal.legend(loc='upper right', fontsize=9)
        self.ax_temporal.set_ylim(0, max([e+c for e, c in zip(ecc_durations, conc_durations)]) * 1.2)
    
    def update_temporal_windows_plot(self):
        """Update the temporal windows bar plot showing VBT states"""
        # Clear previous bars
        self.ax_temporal.clear()
        
        # Reconfigure axes
        self.ax_temporal.set_title("VBT State Machine (Real-Time)", fontweight='bold', color='darkgreen')
        self.ax_temporal.set_xlabel("Rep Number")
        self.ax_temporal.set_ylabel("Phase Duration (s)")
        self.ax_temporal.grid(True, alpha=0.3, axis='y')
        
        if not self.state_history:
            self.ax_temporal.text(0.5, 0.5, 'Waiting for first rep...', 
                                 transform=self.ax_temporal.transAxes,
                                 ha='center', va='center', fontsize=12, color='gray')
            return
        
        # Prepare data for stacked bars
        rep_nums = [entry['rep_num'] for entry in self.state_history]
        ecc_durations = [entry['ecc_duration'] for entry in self.state_history]
        conc_durations = [entry['conc_duration'] for entry in self.state_history]
        
        # Create stacked bars
        bar_width = 0.6
        bars_ecc = self.ax_temporal.bar(rep_nums, ecc_durations, bar_width, 
                                        label='Eccentric', color='#FF6B6B', alpha=0.8)
        bars_conc = self.ax_temporal.bar(rep_nums, conc_durations, bar_width,
                                         bottom=ecc_durations,
                                         label='Concentric', color='#4ECDC4', alpha=0.8)
        
        # Add duration labels on bars
        for i, (rep_num, ecc_dur, conc_dur) in enumerate(zip(rep_nums, ecc_durations, conc_durations)):
            total = ecc_dur + conc_dur
            # Eccentric label
            if ecc_dur > 0.1:  # Only show if duration is significant
                self.ax_temporal.text(rep_num, ecc_dur/2, f'{ecc_dur:.2f}s',
                                     ha='center', va='center', fontsize=8, fontweight='bold', color='white')
            # Concentric label
            if conc_dur > 0.1:
                self.ax_temporal.text(rep_num, ecc_dur + conc_dur/2, f'{conc_dur:.2f}s',
                                     ha='center', va='center', fontsize=8, fontweight='bold', color='white')
            # Total label above bar
            self.ax_temporal.text(rep_num, total + 0.02, f'{total:.2f}s',
                                 ha='center', va='bottom', fontsize=7, color='black', fontweight='bold')
        
        # Configure axes
        if rep_nums:
            self.ax_temporal.set_xlim(min(rep_nums) - 0.5, max(rep_nums) + 0.5)
            self.ax_temporal.set_xticks(rep_nums)
        
        self.ax_temporal.legend(loc='upper right', fontsize=9)
        max_duration = max([e+c for e, c in zip(ecc_durations, conc_durations)]) if ecc_durations else 1.0
        self.ax_temporal.set_ylim(0, max_duration * 1.15)
    
    def update_statistics_display(self):
        """Update the statistics display"""
        if self.sample_count == 0:
            return
            
        elapsed_time = time.time() - self.start_time
        
        current_vals = self.last_values
        
        # VBT State Machine status
        if self.baseline_calculated:
            state_emoji = {'REST': '⚪', 'ECCENTRIC': '🔵', 'CONCENTRIC': '🟢'}
            state_display = f"{state_emoji.get(self.vbt_state, '⚪')} {self.vbt_state}"
        else:
            state_display = "⚪ CALIBRATING..."
        
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

    def check_vbt_state_transition(self, current_time, current_idx):
        """Real-time state machine for VBT detection (like Vitruve, Enode, Beast)"""
        if not self.baseline_calculated:
            return
        
        # Get smoothed velocity for state detection
        if len(self.velocity_smooth_buffer) < self.VEL_SMOOTH_WINDOW:
            return  # Not enough samples for smooth velocity
        
        velocity_smooth = sum(self.velocity_smooth_buffer) / len(self.velocity_smooth_buffer)
        
        # STATE MACHINE
        if self.vbt_state == 'REST':
            # Look for eccentric start: velocity < -0.12 m/s
            if velocity_smooth < self.VEL_ECCENTRIC_THRESHOLD:
                # Check refractory period
                if current_time - self.last_rep_end_time >= self.REFRACTORY_PERIOD:
                    # Start eccentric phase
                    self.vbt_state = 'ECCENTRIC'
                    self.eccentric_start_time = current_time
                    self.eccentric_start_idx = current_idx
                    print(f"\n🔵 ECCENTRIC START (vel={velocity_smooth:.3f} m/s)")
        
        elif self.vbt_state == 'ECCENTRIC':
            eccentric_duration = current_time - self.eccentric_start_time
            
            # Look for zero-crossing (bottom): velocity goes from negative to positive
            if velocity_smooth >= -self.VEL_ZERO_CROSSING_TOLERANCE:
                # Check minimum eccentric window (200ms like Vitruve)
                if eccentric_duration >= self.MIN_ECCENTRIC_WINDOW:
                    # Bottom detected!
                    self.vbt_state = 'CONCENTRIC'
                    self.bottom_time = current_time
                    self.bottom_idx = current_idx
                    self.concentric_start_time = current_time
                    self.concentric_start_idx = current_idx
                    print(f"⚫ BOTTOM (vel={velocity_smooth:.3f} m/s, ecc_duration={eccentric_duration:.3f}s)")
                else:
                    # False start - eccentric too short
                    self.vbt_state = 'REST'
                    print(f"❌ FALSE START - eccentric too short ({eccentric_duration:.3f}s < {self.MIN_ECCENTRIC_WINDOW}s)")
            
            # Timeout check - eccentric too long (invalid movement)
            elif eccentric_duration > 3.0:
                self.vbt_state = 'REST'
                print(f"❌ ECCENTRIC TIMEOUT - too slow")
        
        elif self.vbt_state == 'CONCENTRIC':
            concentric_duration = current_time - self.concentric_start_time
            
            # Look for rep end: velocity drops below threshold
            if velocity_smooth < self.VEL_CONCENTRIC_THRESHOLD:
                # Check minimum concentric duration
                if concentric_duration >= self.MIN_CONCENTRIC_DURATION:
                    # REP COMPLETED! Calculate metrics immediately
                    self.finalize_rep(current_time, current_idx)
                    self.vbt_state = 'REST'
                else:
                    # Too fast - invalid rep
                    self.vbt_state = 'REST'
                    print(f"❌ CONCENTRIC TOO SHORT ({concentric_duration:.3f}s)")
            
            # Timeout check - concentric window exceeded (1.5s like Vitruve)
            elif concentric_duration > self.MAX_CONCENTRIC_WINDOW:
                # Invalid rep - concentric too long
                self.vbt_state = 'REST'
                print(f"❌ CONCENTRIC TIMEOUT ({concentric_duration:.3f}s > {self.MAX_CONCENTRIC_WINDOW}s)")
    
    def finalize_rep(self, end_time, end_idx):
        """Finalize rep and calculate all VBT metrics immediately (80-250ms response like commercial devices)"""
        # Find concentric peak (max velocity during concentric phase)
        concentric_velocities = list(self.velocity_data)[self.concentric_start_idx:end_idx+1]
        if not concentric_velocities:
            return
        
        peak_vel_relative = concentric_velocities.index(max(concentric_velocities))
        concentric_peak_idx = self.concentric_start_idx + peak_vel_relative
        
        # Calculate all VBT metrics
        self.calculate_vbt_metrics_from_indices(
            self.bottom_idx,
            concentric_peak_idx,
            end_idx,
            self.bottom_time,
            list(self.timestamps_data)[concentric_peak_idx],
            self.eccentric_start_time,
            end_time
        )
        
        self.rep_count += 1
        self.last_rep_end_time = end_time
        
        # Save temporal window data for visualization
        self.state_history.append({
            'rep_num': self.rep_count,
            'ecc_start': self.eccentric_start_time,
            'bottom': self.bottom_time,
            'conc_end': end_time,
            'ecc_duration': self.last_eccentric_duration,
            'conc_duration': self.last_concentric_duration
        })
        
        # Instant feedback (like commercial devices)
        print(f"\n✅ REP #{self.rep_count} COMPLETED (INSTANT)")
        print(f"   ⚡ Response time: ~{(time.time() - end_time)*1000:.0f}ms")
        print(f"   Duration: TUT={self.last_rep_duration:.2f}s | Ecc={self.last_eccentric_duration:.2f}s | Conc={self.last_concentric_duration:.2f}s")
        print(f"   Velocity: Mean={self.last_mean_velocity:.3f} m/s | Peak={self.last_peak_velocity:.3f} m/s | MPV={self.last_mean_propulsive_velocity:.3f} m/s")
        print(f"   Power: Mean={self.last_mean_power:.1f}W | Peak={self.last_peak_power:.1f}W | MPP={self.last_mean_propulsive_power:.1f}W")
        print(f"   ROM: {self.last_concentric_displacement:.3f}m | VL: {self.velocity_loss_percent:.1f}%\n")

    def calculate_vbt_metrics_from_indices(self, bottom_idx, concentric_peak_idx, rep_end_idx,
                                           bottom_time, concentric_peak_time, rep_start_time, rep_end_time):
        """Calculate all VBT metrics from explicit indices"""
        if concentric_peak_idx <= bottom_idx:
            self.reset_vbt_metrics()
            return
        
        # Extract concentric phase data (bottom to peak)
        mag_data_list = list(self.magnitude_data)  # Use magnitude (orientation-independent)
        timestamps_list = list(self.timestamps_data)
        
        concentric_mag = mag_data_list[bottom_idx:concentric_peak_idx + 1]
        concentric_time = timestamps_list[bottom_idx:concentric_peak_idx + 1]
        
        if len(concentric_mag) < 2:
            self.reset_vbt_metrics()
            return
        
        # Use the calibrated baseline value (not fixed 1.0)
        baseline_value = self.baseline_value
        mag_accel_net = [(mag - baseline_value) * 9.81 for mag in concentric_mag]  # Convert to m/s²
        
        # DEBUG: Print concentric data for analysis
        print(f"\n🔍 DEBUG VBT Calculation:")
        print(f"   Baseline used: {baseline_value:.3f}g")
        print(f"   Concentric mag range: {min(concentric_mag):.3f}g to {max(concentric_mag):.3f}g")
        print(f"   Net accel range: {min(mag_accel_net):.3f} to {max(mag_accel_net):.3f} m/s²")
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
            
            # Real-time velocity integration from magnitude
            if self.baseline_calculated and len(self.timestamps_data) >= 2:
                # Calculate dt from last timestamp
                dt = self.timestamps_data[-1] - self.timestamps_data[-2]
                # GRAVITY COMPENSATION - Sottrai SEMPRE 1.0g fisso (come Vitruve, Beast, Enode, Metric VBT)
                mag_accel_net = (magnitude - 1.0) * 9.81  # m/s²
                # Integrate: v = v0 + a*dt
                self.current_velocity = self.current_velocity + mag_accel_net * dt
                self.velocity_data.append(self.current_velocity)
                
                # DISABLED: Auto-reset was too aggressive and interfered with rep detection
                # Only rely on state machine to manage velocity
            else:
                # Not calibrated yet or first sample
                self.velocity_data.append(0.0)
            
            # Update statistics
            self.last_values = {'x': ax_g, 'y': ay_g, 'z': az_g, 'mag': magnitude}
            self.sample_count += 1
            
            # Add to velocity smoothing buffer
            self.velocity_smooth_buffer.append(self.current_velocity)
            
            # CALIBRATION SEQUENCE:
            # 1. First sample -> Start countdown
            # 2. After countdown -> Start baseline calibration
            # 3. After 50 stable samples -> Start VBT monitoring
            
            # Start countdown on first sample
            if self.sample_count == 1 and not self.countdown_active and not self.csv_recording:
                self.start_countdown()
            
            # BASELINE CALIBRATION - Start only after countdown finishes
            if not self.baseline_calculated:
                # Check if countdown has finished
                if self.countdown_active:
                    # Still counting down - don't start calibration yet
                    pass
                elif not self.csv_recording:
                    # Countdown finished but CSV not started yet - wait for CSV to start
                    pass
                else:
                    # CSV recording active - now we can calibrate
                    self.baseline_samples.append(magnitude)
                    
                    if len(self.baseline_samples) >= self.BASELINE_SAMPLES_COUNT:
                        # Calculate baseline as mean of first samples (should be ~1g at rest)
                        self.baseline_value = sum(self.baseline_samples) / len(self.baseline_samples)
                        self.baseline_calculated = True
                        print(f"\n✅ BASELINE CALIBRATED: {self.baseline_value:.3f}g (from {self.BASELINE_SAMPLES_COUNT} samples)")
                        print(f"   VBT monitoring ACTIVE - Ready to detect reps\n")
                        # Reset velocity to start fresh after calibration
                        self.current_velocity = 0.0
            
            # REAL-TIME STATE MACHINE - Check EVERY sample (like commercial devices)
            if self.baseline_calculated:
                self.check_vbt_state_transition(current_time, len(self.velocity_data) - 1)
            
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

def start_ble_thread(monitor):
    """Start BLE in background thread"""
    def run_ble():
        asyncio.run(async_main(monitor))
    
    ble_thread = threading.Thread(target=run_ble, daemon=True)
    ble_thread.start()
    return ble_thread

def main():
    """Main function - runs matplotlib in main thread, BLE in background (macOS compatible)"""
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    monitor = CL837UnifiedMonitor()
    ble_thread = None
    
    try:
        # Start BLE in background thread
        print("\n🔵 Starting BLE connection in background thread...")
        ble_thread = start_ble_thread(monitor)
        
        # Wait a moment for BLE to initialize
        time.sleep(1)
        
        # Setup matplotlib in main thread (REQUIRED on macOS)
        print("\n🎨 Starting oscilloscope in main thread...")
        monitor.setup_oscilloscope()
        monitor.animation = animation.FuncAnimation(
            monitor.fig, monitor.update_plot, interval=50, blit=False, cache_frame_data=False)
        monitor.plot_ready = True
        print("✓ Oscilloscope window opened")
        
        # Show plot (blocking call in main thread)
        plt.show(block=True)
        
        print("\n✓ Oscilloscope window closed")
        print("Stopping BLE monitoring...")
        monitor.monitoring_active = False
        
        # Give BLE thread time to clean up
        if ble_thread and ble_thread.is_alive():
            time.sleep(0.5)
        
    except KeyboardInterrupt:
        print("\n⚠️  Program interrupted by user")
        monitor.monitoring_active = False
        try:
            plt.close('all')
        except:
            pass
    except Exception as e:
        print(f"\n❌ Error: {e}")
        monitor.monitoring_active = False
        try:
            plt.close('all')
        except:
            pass
    finally:
        # Clean up
        monitor.monitoring_active = False
        print("\n✓ Program terminated cleanly")

if __name__ == "__main__":
    main()
