# -*- coding: utf-8 -*-
"""
CL837 VBT Monitor - Output Sports Style
Real-time velocity bar chart with color-coded load zones
"""

import asyncio
import time
import struct
import traceback
import threading
import winsound
import numpy as np
from collections import deque
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from bleak import BleakClient, BleakScanner
from vbt_config import VBTConfig

class CL837VBTMonitor:
    """Minimalist VBT monitor with Output Sports style bar chart"""
    
    def __init__(self, config_file: str = "vbt_config.json", profile: str = None):
        # Save profile name
        self.profile = profile if profile else 'default'
        
        # Load VBT configuration
        try:
            self.vbt_config = VBTConfig(config_file)
            
            if profile:
                self.vbt_config.set_profile(profile)
            
            # Get parameters
            params = self.vbt_config.get_params()
            
            # Validate before using
            if not self.vbt_config.validate_params(params):
                raise ValueError("Invalid VBT configuration parameters")
            
            print("\n" + "="*70)
            print("VBT CONFIGURATION LOADED")
            print("="*70)
            self.vbt_config.print_current_config()
            
        except FileNotFoundError:
            print("⚠️  Config file not found. Using default hardcoded values.")
            params = self._get_default_params()
        except Exception as e:
            print(f"⚠️  Error loading config: {e}. Using default hardcoded values.")
            params = self._get_default_params()
        
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
        
        # Data buffers (small - only for current rep)
        self.max_samples = 150  # ~3 seconds at 50Hz
        self.magnitude_data = deque(maxlen=self.max_samples)
        self.timestamps_data = deque(maxlen=self.max_samples)
        self.velocity_data = deque(maxlen=self.max_samples)
        
        # VBT State Machine - FROM CONFIG
        self.BASELINE_ZONE = params['BASELINE_ZONE']
        self.MIN_DEPTH_MAG = params['MIN_DEPTH_MAG']
        self.MIN_PEAK_MAG = params['MIN_PEAK_MAG']
        
        self.MIN_ECCENTRIC_WINDOW = params['MIN_ECCENTRIC_WINDOW']
        self.MAX_CONCENTRIC_WINDOW = params['MAX_CONCENTRIC_WINDOW']
        self.MIN_CONCENTRIC_DURATION = params['MIN_CONCENTRIC_DURATION']
        self.REFRACTORY_PERIOD = params['REFRACTORY_PERIOD']
        
        self.MAG_SMOOTH_WINDOW = params['MAG_SMOOTH_WINDOW']
        self.mag_smooth_buffer = deque(maxlen=self.MAG_SMOOTH_WINDOW)
        
        # Variance/STD analysis to distinguish movement from noise
        self.STD_WINDOW = params['STD_WINDOW']
        self.mag_std_buffer = deque(maxlen=self.STD_WINDOW)
        self.MIN_MOVEMENT_STD = params['MIN_MOVEMENT_STD']
        self.MAX_NOISE_STD = params['MAX_NOISE_STD']
        self.current_std = 0.0
        
        # Event Window System - FROM CONFIG
        self.WINDOW_DURATION = params['WINDOW_DURATION']
        self.PRE_BUFFER_SIZE = params['PRE_BUFFER_SIZE']
        self.pre_buffer_mag = deque(maxlen=self.PRE_BUFFER_SIZE)
        self.pre_buffer_time = deque(maxlen=self.PRE_BUFFER_SIZE)
        self.pre_buffer_idx = deque(maxlen=self.PRE_BUFFER_SIZE)
        self.window_active = False
        self.window_start_time = None
        self.window_start_idx = None
        self.window_data_mag = []  # Magnitudes in window
        self.window_data_time = []  # Timestamps in window
        self.window_data_idx = []   # Indices in window
        
        # Markers found in window
        self.markers = {
            'counter_movement': None,  # Inverted cusp preparation
            'bottom': None,             # Absolute minimum
            'peak': None,               # Maximum concentric peak
            'deceleration': None        # Minimum after peak (drop)
        }
        
        # Refractory period
        self.last_rep_end_time = -self.REFRACTORY_PERIOD
        
        # Beep timing control
        self.last_beep_time = 0
        
        # Baseline calibration
        self.baseline_calculated = False
        self.baseline_samples = []
        self.BASELINE_SAMPLES_COUNT = 25
        self.baseline_value = 1.0
        
        # Velocity conversion factor - FROM CONFIG
        self.VELOCITY_FACTOR = params['VELOCITY_FACTOR']
        self.VELOCITY_CALIBRATED = params['VELOCITY_CALIBRATED']
        if not self.VELOCITY_CALIBRATED:
            print("\n⚠️  WARNING: Velocity conversion factor NOT calibrated!")
            print(f"   Current factor: {self.VELOCITY_FACTOR:.2f}")
            print("   Velocity metrics may not be accurate.")
            print("   Calibrate with linear encoder for ground truth.\n")
        
        # Load weight (kg) - for power calculations
        self.load_weight_kg = 0.0  # Will be set by user input
        
        # Real-time velocity integration
        self.current_velocity = 0.0
        
        # VBT Results - History of reps
        self.rep_velocities = []  # List of mean velocities
        self.rep_numbers = []     # List of rep numbers
        self.rep_count = 0
        
        # Current rep metrics (for display)
        self.last_mean_velocity = 0.0
        self.last_peak_velocity = 0.0
        self.last_mpv = 0.0
        
        # Statistics
        self.sample_count = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Matplotlib
        self.fig = None
        self.ax = None
        self.animation_obj = None
        self.plot_ready = False
        self.monitoring_active = False
        
        # Calibration countdown
        self.countdown_active = False
        self.countdown_start_time = None
        self.countdown_duration = 3.0
        self.countdown_text = None
    
    def _get_default_params(self) -> dict:
        """Fallback default parameters if config file not available"""
        return {
            'BASELINE_ZONE': 0.06,
            'MIN_DEPTH_MAG': 0.60,
            'MIN_PEAK_MAG': 1.05,
            'MIN_ECCENTRIC_WINDOW': 0.30,
            'MAX_CONCENTRIC_WINDOW': 2.5,
            'MIN_CONCENTRIC_DURATION': 0.15,
            'REFRACTORY_PERIOD': 0.8,
            'MAG_SMOOTH_WINDOW': 5,
            'STD_WINDOW': 20,
            'MIN_MOVEMENT_STD': 0.015,
            'MAX_NOISE_STD': 0.008,
            'WINDOW_DURATION': 2.5,
            'PRE_BUFFER_SIZE': 25,
            'VELOCITY_FACTOR': 0.5,
            'VELOCITY_CALIBRATED': False
        }

    async def scan_and_connect(self):
        """Scan and connect to CL837"""
        while True:
            print("\n🔍 Scanning for CL837 devices...")
            devices = await BleakScanner.discover(timeout=5.0)
            
            cl837_devices = [d for d in devices if d.name and 'CL837' in d.name.upper()]
            
            if not cl837_devices:
                print("❌ No CL837 devices found")
                retry = input("Retry scan? (y/n): ").strip().lower()
                if retry != 'y':
                    return False
                continue
            
            print(f"\n✅ Found {len(cl837_devices)} CL837 device(s):")
            for i, dev in enumerate(cl837_devices, 1):
                print(f"   {i}. {dev.name} ({dev.address})")
            
            if len(cl837_devices) == 1:
                self.device = cl837_devices[0]
                print(f"\n→ Auto-selecting: {self.device.name}")
            else:
                while True:
                    try:
                        choice = int(input(f"\nSelect device (1-{len(cl837_devices)}): "))
                        if 1 <= choice <= len(cl837_devices):
                            self.device = cl837_devices[choice - 1]
                            break
                    except ValueError:
                        pass
                    print("Invalid selection")
            
            print(f"\n🔵 Connecting to {self.device.name}...")
            try:
                self.client = BleakClient(self.device.address, timeout=10.0)
                await self.client.connect()
                self.is_connected = True
                print(f"✅ Connected to {self.device.name}")
                return True
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                retry = input("Retry? (y/n): ").strip().lower()
                if retry != 'y':
                    return False

    async def discover_services(self):
        """Discover and validate Chileaf service"""
        print("\n🔍 Discovering services...")
        
        chileaf_service = None
        tx_characteristic = None
        
        for service in self.client.services:
            if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                chileaf_service = service
                print(f"✅ Chileaf service found: {service.uuid}")
                
                for char in service.characteristics:
                    if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                        tx_characteristic = char
                        print(f"✅ TX characteristic found: {char.uuid}")
                        print(f"   Properties: {char.properties}")
                break
        
        if not tx_characteristic:
            print("❌ Chileaf TX characteristic not found")
            return False
        
        if "notify" not in tx_characteristic.properties:
            print("❌ TX characteristic does not support notifications")
            return False
        
        self.tx_char = tx_characteristic
        print("✅ Service configuration valid")
        return True

    def setup_plot(self):
        """Initialize Output Sports style bar chart + oscilloscope"""
        print("🎨 Setting up VBT display...")
        
        # Create 2 subplots: bar chart (top) + oscilloscope (bottom)
        self.fig, (self.ax, self.ax_scope) = plt.subplots(2, 1, figsize=(12, 10), 
                                                           gridspec_kw={'height_ratios': [1, 2]})
        self.fig.suptitle("VBT MONITOR - Output Sports Style", fontsize=18, fontweight='bold')
        
        # SUBPLOT 1: Bar chart (top)
        self.ax.set_xlabel("Repetition Number", fontsize=14, fontweight='bold')
        self.ax.set_ylabel("Mean Velocity (m/s)", fontsize=14, fontweight='bold')
        self.ax.set_ylim(0, 1.5)  # Typical squat velocity range
        self.ax.grid(True, alpha=0.3, axis='y')
        
        # Add velocity zone reference lines (Output Sports style)
        self.ax.axhspan(0.0, 0.15, color='red', alpha=0.1, label='Max Strength (>90% 1RM)')
        self.ax.axhspan(0.15, 0.30, color='orange', alpha=0.1, label='Strength (80-90% 1RM)')
        self.ax.axhspan(0.30, 0.50, color='yellow', alpha=0.1, label='Strength-Speed (60-80% 1RM)')
        self.ax.axhspan(0.50, 1.5, color='green', alpha=0.1, label='Speed/Power (<60% 1RM)')
        
        # Legend
        self.ax.legend(loc='upper right', fontsize=9)
        
        # Status text
        self.status_text = self.ax.text(0.02, 0.98, "", transform=self.ax.transAxes,
                                        fontsize=11, verticalalignment='top',
                                        fontfamily='monospace',
                                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
        
        # SUBPLOT 2: Oscilloscope (bottom)
        self.ax_scope.set_title("Real-Time Magnitude", fontweight='bold', fontsize=12)
        self.ax_scope.set_xlabel("Samples (last 150)", fontsize=10)
        self.ax_scope.set_ylabel("Magnitude (g)", fontsize=10)
        self.ax_scope.set_ylim(0.5, 1.5)
        self.ax_scope.grid(True, alpha=0.3)
        self.ax_scope.axhline(y=1.0, color='blue', linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (1g)')
        self.ax_scope.legend(loc='upper right', fontsize=8)
        
        # Initialize empty line for oscilloscope
        self.line_scope, = self.ax_scope.plot([], [], 'purple', linewidth=2, alpha=0.8)
        
        # Countdown text (large overlay)
        self.countdown_text = self.fig.text(0.5, 0.5, "", 
                                           ha='center', va='center',
                                           fontsize=80, fontweight='bold',
                                           color='red', alpha=0.0,
                                           bbox=dict(boxstyle='round,pad=1.0', 
                                                    facecolor='yellow', alpha=0.0))
        
        plt.tight_layout()
        print("✅ Display configured")

    def update_plot(self, frame):
        """Update bar chart + oscilloscope with latest data"""
        # Update countdown if active
        if self.countdown_active and self.countdown_start_time:
            elapsed = time.time() - self.countdown_start_time
            remaining = self.countdown_duration - elapsed
            
            if remaining > 0:
                countdown_num = int(remaining) + 1
                self.countdown_text.set_text(f"{countdown_num}")
                self.countdown_text.set_alpha(0.95)
                self.countdown_text.get_bbox_patch().set_alpha(0.9)
            else:
                self.countdown_active = False
                self.countdown_text.set_alpha(0.0)
                self.countdown_text.get_bbox_patch().set_alpha(0.0)
                if not self.baseline_calculated:
                    print("\n📊 CALIBRATING BASELINE...")
        else:
            self.countdown_text.set_alpha(0.0)
            self.countdown_text.get_bbox_patch().set_alpha(0.0)
        
        # === UPDATE BAR CHART (TOP) ===
        self.ax.clear()
        
        # Redraw zones
        self.ax.axhspan(0.0, 0.15, color='red', alpha=0.1)
        self.ax.axhspan(0.15, 0.30, color='orange', alpha=0.1)
        self.ax.axhspan(0.30, 0.50, color='yellow', alpha=0.1)
        self.ax.axhspan(0.50, 1.5, color='green', alpha=0.1)
        
        self.ax.set_xlabel("Repetition Number", fontsize=14, fontweight='bold')
        self.ax.set_ylabel("Mean Velocity (m/s)", fontsize=14, fontweight='bold')
        self.ax.set_ylim(0, 1.5)
        self.ax.grid(True, alpha=0.3, axis='y')
        
        # Draw bars if we have reps
        if self.rep_numbers:
            # Determine bar colors based on velocity zones
            colors = []
            for vel in self.rep_velocities:
                if vel < 0.15:
                    colors.append('#D32F2F')  # Red - Max strength
                elif vel < 0.30:
                    colors.append('#FF6F00')  # Orange - Strength
                elif vel < 0.50:
                    colors.append('#FBC02D')  # Yellow - Strength-speed
                else:
                    colors.append('#388E3C')  # Green - Speed/power
            
            # Draw bars
            bars = self.ax.bar(self.rep_numbers, self.rep_velocities, 
                              color=colors, alpha=0.8, edgecolor='black', linewidth=2)
            
            # Add velocity labels on top of bars
            for bar, vel in zip(bars, self.rep_velocities):
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{vel:.3f}',
                           ha='center', va='bottom', fontweight='bold', fontsize=10)
            
            # Set x-axis limits with padding
            self.ax.set_xlim(0.5, max(self.rep_numbers) + 0.5)
        
        # Update status text
        status = self.get_status_text()
        self.status_text = self.ax.text(0.02, 0.98, status, transform=self.ax.transAxes,
                                        fontsize=11, verticalalignment='top',
                                        fontfamily='monospace',
                                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
        
        # === UPDATE OSCILLOSCOPE (BOTTOM) ===
        self.ax_scope.clear()
        self.ax_scope.set_title("Real-Time Magnitude + State Machine", fontweight='bold', fontsize=12)
        self.ax_scope.set_xlabel("Samples (last 150)", fontsize=10)
        self.ax_scope.set_ylabel("Magnitude (g)", fontsize=10)
        self.ax_scope.grid(True, alpha=0.3)
        
        if len(self.magnitude_data) > 0:
            mag_list = list(self.magnitude_data)
            vel_list = list(self.velocity_data)
            indices = list(range(len(mag_list)))
            
            # Plot magnitude
            self.ax_scope.plot(indices, mag_list, 'purple', linewidth=2.5, alpha=0.9, label='Magnitude')
            
            # Reference lines
            self.ax_scope.axhline(y=1.0, color='blue', linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (1g)')
            
            # Highlight window active with background color
            if self.window_active:
                self.ax_scope.axhspan(0, 4, color='blue', alpha=0.05, label='WINDOW ACTIVE')
            
            # Y-axis FISSO 0-4g (non adattivo)
            self.ax_scope.set_ylim(0, 4.0)
            
            # Update X-axis
            if indices:
                self.ax_scope.set_xlim(0, max(self.max_samples, len(indices)))
            
            # Add baseline zones
            if self.baseline_calculated:
                baseline_upper = self.baseline_value * (1 + self.BASELINE_ZONE)
                baseline_lower = self.baseline_value * (1 - self.BASELINE_ZONE)
                self.ax_scope.axhline(y=baseline_upper, color='red', linestyle=':', linewidth=1, alpha=0.3)
                self.ax_scope.axhline(y=baseline_lower, color='green', linestyle=':', linewidth=1, alpha=0.3)
                self.ax_scope.axhline(y=self.MIN_DEPTH_MAG, color='orange', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Min Depth ({self.MIN_DEPTH_MAG}g)')
                self.ax_scope.axhline(y=self.MIN_PEAK_MAG, color='cyan', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Min Peak ({self.MIN_PEAK_MAG}g)')
            
            # Add info text
            current_vel = vel_list[-1] if vel_list else 0.0
            current_mag = mag_list[-1] if mag_list else 0.0
            
            # Indicatore movimento basato su STD
            if self.current_std >= self.MIN_MOVEMENT_STD:
                movement_indicator = "🔴 MOVING"
            elif self.current_std <= self.MAX_NOISE_STD:
                movement_indicator = "🟢 STABLE"
            else:
                movement_indicator = "🟡 TRANSITION"
            
            # Window status
            window_status = "🔵 WINDOW ACTIVE" if self.window_active else "⏳ WAITING"
            
            info_text = f"{window_status} | Mag: {current_mag:.3f}g | Vel: {current_vel:.3f} m/s\nSTD: {self.current_std:.4f}g {movement_indicator}"
            info_color = 'blue' if self.window_active else 'gray'
            self.ax_scope.text(0.02, 0.98, info_text, transform=self.ax_scope.transAxes,
                              fontsize=10, verticalalignment='top', fontweight='bold',
                              color=info_color,
                              bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
            
            self.ax_scope.legend(loc='upper right', fontsize=8)
        
        return [self.status_text, self.countdown_text]

    def get_status_text(self):
        """Generate status text for display"""
        elapsed = time.time() - self.start_time
        
        if not self.baseline_calculated:
            status = "🔄 CALIBRATING..."
        elif self.window_active:
            window_elapsed = time.time() - self.window_start_time
            status = f"🔵 WINDOW: {window_elapsed:.1f}s / {self.WINDOW_DURATION:.1f}s"
        else:
            status = "⏳ WAITING FOR REP..."
        
        # Velocity Loss calculation
        if len(self.rep_velocities) >= 2:
            vl_percent = ((self.rep_velocities[0] - self.rep_velocities[-1]) / self.rep_velocities[0]) * 100
            vl_text = f"VL: {vl_percent:.1f}%"
            if vl_percent > 20:
                vl_text += " ⚠️"
            elif vl_percent > 10:
                vl_text += " ⚡"
            else:
                vl_text += " ✅"
        else:
            vl_text = "VL: --"
        
        text = f"""STATUS: {status}
REPS: {self.rep_count}
TIME: {elapsed:.0f}s
{vl_text}

LAST REP:
  MV: {self.last_mean_velocity:.3f} m/s
  PV: {self.last_peak_velocity:.3f} m/s
  MPV: {self.last_mpv:.3f} m/s
"""
        return text

    def parse_chileaf_data(self, data):
        """Parse Chileaf accelerometer frame"""
        try:
            if len(data) < 4:
                return False
            
            header = data[0]
            length = data[1]
            command = data[2]
            
            if header != self.CHILEAF_HEADER or command != self.CHILEAF_CMD_ACCELEROMETER:
                return False
            
            self.frame_count += 1
            frame_time = time.time()
            
            payload_bytes = len(data) - 4
            samples_count = payload_bytes // 6
            
            for i in range(samples_count):
                offset = 3 + (i * 6)
                accel_data = data[offset:offset + 6]
                self.parse_single_sample(accel_data, frame_time)
            
            return True
        except Exception as e:
            print(f"Parse error: {e}")
            return False

    def parse_single_sample(self, accel_data, frame_time):
        """Parse single 6-byte accelerometer sample"""
        if len(accel_data) < 6:
            return
        
        try:
            ax_raw, ay_raw, az_raw = struct.unpack('<hhh', accel_data)
            
            ax = ax_raw / self.CHILEAF_CONVERSION_FACTOR
            ay = ay_raw / self.CHILEAF_CONVERSION_FACTOR
            az = az_raw / self.CHILEAF_CONVERSION_FACTOR
            
            magnitude = (ax**2 + ay**2 + az**2)**0.5
            
            self.sample_count += 1
            timestamp = frame_time
            
            # Store data
            self.magnitude_data.append(magnitude)
            self.timestamps_data.append(timestamp)
            self.mag_smooth_buffer.append(magnitude)  # Per smoothing state machine
            self.mag_std_buffer.append(magnitude)  # Per calcolo STD
            
            # Populate pre-buffer continuously (only if window not active)
            if not self.window_active:
                self.pre_buffer_mag.append(magnitude)
                self.pre_buffer_time.append(timestamp)
                self.pre_buffer_idx.append(self.sample_count - 1)
            
            # Calculate current STD (movement variability)
            if len(self.mag_std_buffer) >= 10:
                self.current_std = np.std(list(self.mag_std_buffer))
            else:
                self.current_std = 0.0
            
            # Baseline calibration (first 25 samples after countdown)
            if not self.baseline_calculated and not self.countdown_active:
                self.baseline_samples.append(magnitude)
                if len(self.baseline_samples) >= self.BASELINE_SAMPLES_COUNT:
                    self.baseline_value = np.median(self.baseline_samples)
                    self.baseline_calculated = True
                    print(f"\n✅ BASELINE CALIBRATED: {self.baseline_value:.3f}g")
                    print("🟢 VBT MONITORING ACTIVE (STD-based detection)\n")
                return
            
            # Real-time velocity integration (FIXED 1.0g gravity compensation)
            if self.baseline_calculated and len(self.timestamps_data) >= 2:
                dt = self.timestamps_data[-1] - self.timestamps_data[-2]
                # GRAVITY COMPENSATION - Fixed 1.0g (Vitruve/Beast/Enode standard)
                mag_accel_net = (magnitude - 1.0) * 9.81  # m/s²
                self.current_velocity = self.current_velocity + mag_accel_net * dt
                self.velocity_data.append(self.current_velocity)
                
                # Check event window (event window system with markers)
                self.check_event_window(timestamp, len(self.magnitude_data) - 1, magnitude)
            else:
                self.velocity_data.append(0.0)
                
        except struct.error as e:
            print(f"Unpack error: {e}")

    def open_event_window(self, current_time, current_idx):
        """Opens 2.5s window for movement analysis (with 0.5s pre-buffer)"""
        self.window_active = True
        
        # Include pre-buffer data in window
        self.window_data_mag = list(self.pre_buffer_mag)
        self.window_data_time = list(self.pre_buffer_time)
        self.window_data_idx = list(self.pre_buffer_idx)
        
        # The "true" start time is that of the first sample in the pre-buffer
        if len(self.window_data_time) > 0:
            self.window_start_time = self.window_data_time[0]
            self.window_start_idx = self.window_data_idx[0]
        else:
            self.window_start_time = current_time
            self.window_start_idx = current_idx
        
        self.markers = {
            'counter_movement': None,
            'bottom': None,
            'peak': None,
            'deceleration': None
        }
        
        pre_buffer_duration = current_time - self.window_start_time if len(self.window_data_time) > 0 else 0
        print(f"\n🔵 EVENT WINDOW OPENED at {current_time:.2f}s (with {pre_buffer_duration:.2f}s pre-buffer)")
        
        # Grave beep for window opening (non-blocking, only if >0.5s since last)
        now = time.time()
        if now - self.last_beep_time > 0.5:
            self.last_beep_time = now
            threading.Thread(target=lambda: winsound.Beep(400, 300), daemon=True).start()
    
    def close_and_analyze_window(self, current_time):
        """Closes window and analyzes markers to validate squat"""
        print(f"\n🔴 EVENT WINDOW CLOSED at {current_time:.2f}s ({len(self.window_data_mag)} samples)")
        
        if len(self.window_data_mag) < 30:  # Minimo 30 samples (~0.6s @ 50Hz)
            print("⚠️  Window too short - ignore event")
            self.window_active = False
            return
        
        # === FIND MARKERS ===
        baseline = self.baseline_value
        
        # 1. Counter-movement (YELLOW - window opening, first cusp below baseline)
        for i in range(min(25, len(self.window_data_mag))):  # Primi 0.5s
            if self.window_data_mag[i] < baseline * 0.92:  # Sotto 92% baseline
                if self.markers['counter_movement'] is None:
                    self.markers['counter_movement'] = {
                        'idx': self.window_data_idx[i],
                        'mag': self.window_data_mag[i],
                        'time': self.window_data_time[i]
                    }
                    break
        
        # 2. Concentric push peak (BLUE - absolute maximum = push acceleration)
        max_global_idx = np.argmax(self.window_data_mag)
        self.markers['peak'] = {
            'idx': self.window_data_idx[max_global_idx],
            'mag': self.window_data_mag[max_global_idx],
            'time': self.window_data_time[max_global_idx]
        }
        
        # 3. Accelerometer recoil (RED - minimum after blue peak)
        post_peak_start = max_global_idx + 1
        if post_peak_start < len(self.window_data_mag):
            post_peak_mag = self.window_data_mag[post_peak_start:]
            min_idx_relative = np.argmin(post_peak_mag)
            min_idx = post_peak_start + min_idx_relative
            self.markers['bottom'] = {
                'idx': self.window_data_idx[min_idx],
                'mag': self.window_data_mag[min_idx],
                'time': self.window_data_time[min_idx]
            }
            
            # 4. Return to baseline (GREEN - rise towards baseline after recoil)
            post_recoil_start = min_idx + 1
            if post_recoil_start < len(self.window_data_mag) - 5:
                post_recoil_mag = self.window_data_mag[post_recoil_start:]
                green_idx_relative = np.argmax(post_recoil_mag)
                green_idx = post_recoil_start + green_idx_relative
                self.markers['deceleration'] = {
                    'idx': self.window_data_idx[green_idx],
                    'mag': self.window_data_mag[green_idx],
                    'time': self.window_data_time[green_idx]
                }
        else:
            # Fallback if not enough data after peak
            min_idx = np.argmin(self.window_data_mag)
            self.markers['bottom'] = {
                'idx': self.window_data_idx[min_idx],
                'mag': self.window_data_mag[min_idx],
                'time': self.window_data_time[min_idx]
            }
        
        # === PRINT MARKERS ===
        print("\n📍 MARKERS FOUND:")
        for name, marker in self.markers.items():
            if marker:
                print(f"  {name:20s}: {marker['mag']:.3f}g at {marker['time']:.2f}s")
        
        # === VALIDATE SQUAT ===
        is_valid = self.validate_squat_from_markers()
        
        # === SAVE SCREENSHOT AND CSV ===
        self.save_window_data(is_valid)
        
        if is_valid:
            self.finalize_rep_from_markers()
        else:
            print("❌ Pattern non valido - NON è uno squat")
        
        self.window_active = False
    
    def save_window_data(self, is_valid):
        """Saves window screenshot AND CSV with all data and VBT metrics"""
        try:
            import os
            import csv
            
            # Create base directories if they don't exist
            screenshot_base = "windowshots"
            csv_base = "csv_shots"
            
            # Create subdirectory for current profile
            screenshot_dir = os.path.join(screenshot_base, self.profile)
            csv_dir = os.path.join(csv_base, self.profile)
            
            for d in [screenshot_dir, csv_dir]:
                if not os.path.exists(d):
                    os.makedirs(d)
            
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            status = "VALID" if is_valid else "REJECTED"
            
            # === SAVE SCREENSHOT ===
            fig_s = plt.figure(figsize=(14, 6))
            ax_s = fig_s.add_subplot(111)
            times_rel = [(t - self.window_start_time) for t in self.window_data_time]
            ax_s.plot(times_rel, self.window_data_mag, 'purple', linewidth=2, label='Magnitude', alpha=0.8)
            ax_s.axhline(y=self.baseline_value, color='blue', linestyle='--', linewidth=1.5, label='Baseline')
            ax_s.axhline(y=self.MIN_DEPTH_MAG, color='orange', linestyle='--', linewidth=1, alpha=0.6, label='Min Depth')
            ax_s.axhline(y=self.MIN_PEAK_MAG, color='cyan', linestyle='--', linewidth=1, alpha=0.6, label='Min Peak')
            colors = {'counter_movement': 'yellow', 'peak': 'blue', 'bottom': 'red', 'deceleration': 'green'}
            for name, m in self.markers.items():
                if m:
                    t = m['time'] - self.window_start_time
                    ax_s.scatter([t], [m['mag']], s=200, marker='o', color=colors[name], edgecolors='black', linewidths=2, zorder=10, label=name.replace('_', ' ').title())
                    ax_s.annotate(f"{m['mag']:.3f}g", xy=(t, m['mag']), xytext=(10, 10), textcoords='offset points', fontsize=9, fontweight='bold', bbox=dict(boxstyle='round', facecolor=colors[name], alpha=0.7))
            ax_s.set_title(f"Event Window - {status}", fontsize=14, fontweight='bold')
            ax_s.set_xlabel("Time (s)", fontsize=12)
            ax_s.set_ylabel("Magnitude (g)", fontsize=12)
            ax_s.set_ylim(0, 2.0)
            ax_s.grid(True, alpha=0.3)
            ax_s.legend(loc='upper right', fontsize=8)
            png_fname = os.path.join(screenshot_dir, f"window_{ts}_{status}.png")
            fig_s.savefig(png_fname, dpi=150, bbox_inches='tight')
            plt.close(fig_s)
            print(f"📸 PNG: {png_fname}")
            
            # === SAVE CSV ===
            csv_fname = os.path.join(csv_dir, f"window_{ts}_{status}.csv")
            with open(csv_fname, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header: Metadata
                writer.writerow(['# VBT Window Data Export'])
                writer.writerow(['# Timestamp', ts])
                writer.writerow(['# Status', status])
                writer.writerow(['# Load Weight (kg)', self.load_weight_kg])
                writer.writerow(['# Baseline (g)', f"{self.baseline_value:.4f}"])
                writer.writerow(['# Min Depth Threshold (g)', f"{self.MIN_DEPTH_MAG:.2f}"])
                writer.writerow(['# Min Peak Threshold (g)', f"{self.MIN_PEAK_MAG:.2f}"])
                writer.writerow([])
                
                # VBT Metrics (if valid)
                if is_valid:
                    # Calculate simple metrics from markers
                    peak = self.markers['peak']
                    recoil = self.markers['bottom']
                    time_to_peak = peak['time'] - self.window_start_time
                    delta_mag = peak['mag'] - self.baseline_value
                    mean_velocity = abs(delta_mag) * 9.81 * self.VELOCITY_FACTOR
                    peak_velocity = mean_velocity * 1.3  # Estimate
                    mpv = mean_velocity * 1.15  # Estimate
                    
                    # Power calculations (if load provided)
                    if self.load_weight_kg > 0:
                        mean_power = self.load_weight_kg * 9.81 * mean_velocity
                        peak_power = self.load_weight_kg * 9.81 * peak_velocity
                        mpv_power = self.load_weight_kg * 9.81 * mpv
                    else:
                        mean_power = 0.0
                        peak_power = 0.0
                        mpv_power = 0.0
                    
                    writer.writerow(['# VBT METRICS'])
                    writer.writerow(['Mean Velocity (MV)', f"{mean_velocity:.3f}", 'm/s'])
                    writer.writerow(['Peak Velocity (PV)', f"{peak_velocity:.3f}", 'm/s'])
                    writer.writerow(['Mean Propulsive Velocity (MPV)', f"{mpv:.3f}", 'm/s'])
                    writer.writerow(['Time to Peak', f"{time_to_peak:.3f}", 's'])
                    writer.writerow(['Mean Power', f"{mean_power:.1f}", 'W'])
                    writer.writerow(['Peak Power', f"{peak_power:.1f}", 'W'])
                    writer.writerow(['MPV Power', f"{mpv_power:.1f}", 'W'])
                    writer.writerow([])
                
                # Markers
                writer.writerow(['# MARKERS'])
                writer.writerow(['Marker', 'Time (s)', 'Magnitude (g)', 'Color'])
                for name, m in self.markers.items():
                    if m:
                        t_rel = m['time'] - self.window_start_time
                        writer.writerow([name, f"{t_rel:.4f}", f"{m['mag']:.4f}", colors[name]])
                writer.writerow([])
                
                # Time series data
                writer.writerow(['# TIME SERIES DATA'])
                writer.writerow(['Time_Relative (s)', 'Magnitude (g)'])
                for t, mag in zip(times_rel, self.window_data_mag):
                    writer.writerow([f"{t:.4f}", f"{mag:.4f}"])
            
            print(f"💾 CSV: {csv_fname}")
            
        except Exception as e:
            print(f"⚠️  Save error: {e}")
            import traceback
            traceback.print_exc()
    
    def validate_squat_from_markers(self):
        """Validates that markers form a valid squat pattern"""
        peak = self.markers['peak']  # BLUE - concentric push peak
        recoil = self.markers['bottom']  # RED - accelerometer recoil
        
        if not peak:
            print("⚠️  Peak missing")
            return False
        
        # 1. Push peak must be sufficiently high
        if peak['mag'] <= self.MIN_PEAK_MAG:
            print(f"⚠️  Peak too low: {peak['mag']:.3f}g <= {self.MIN_PEAK_MAG}g")
            return False
        
        # 2. There must be recoil after the peak
        if not recoil:
            print(f"⚠️  Recoil missing")
            return False
        
        # 3. Recoil must be AFTER the peak (correct temporal order)
        if recoil['time'] <= peak['time']:
            print(f"⚠️  Wrong order: recoil before peak")
            return False
        
        # 4. Calculate concentric phase duration (window start -> peak)
        time_to_peak = peak['time'] - self.window_start_time
        
        # DURATION VALIDATION: full VBT range (from explosive to controlled)
        if time_to_peak < self.MIN_CONCENTRIC_DURATION:
            print(f"⚠️  Movimento troppo rapido: {time_to_peak:.2f}s < {self.MIN_CONCENTRIC_DURATION}s")
            return False
        
        # 5. Calcola velocità media: formula VBT standard
        # Velocità = (picco_accelerazione - baseline) * g * sqrt(2 * spostamento_stimato)
        # Semplificato: delta_mag rappresenta accelerazione netta, moltiplichiamo per g
        delta_mag = peak['mag'] - self.baseline_value
        # Velocità media per VBT: assumiamo spostamento proporzionale a tempo²
        # Formula semplificata usata da sistemi commerciali
        mean_velocity = abs(delta_mag) * 9.81 * 0.5  # g -> m/s² con fattore medio
        
        print(f"✅ SQUAT VALIDO: picco={peak['mag']:.3f}g, rinculo={recoil['mag']:.3f}g, tempo={time_to_peak:.2f}s, MV={mean_velocity:.3f}m/s")
        return True
    
    def finalize_rep_from_markers(self):
        """Finalizza rep usando marker invece di state machine"""
        peak = self.markers['peak']  # BLU - picco spinta concentrica
        
        # Calcola velocità media dalla spinta: baseline -> picco
        time_to_peak = peak['time'] - self.window_start_time
        delta_mag = peak['mag'] - self.baseline_value
        # Formula VBT: delta accelerazione * g * fattore (FROM CONFIG)
        mean_velocity = abs(delta_mag) * 9.81 * self.VELOCITY_FACTOR
        
        # Store rep
        self.rep_count += 1
        self.rep_numbers.append(self.rep_count)
        self.rep_velocities.append(mean_velocity)
        
        self.last_mean_velocity = mean_velocity
        self.last_peak_velocity = mean_velocity * 1.3  # Stima
        self.last_mpv = mean_velocity * 1.15
        
        self.last_rep_end_time = peak['time']
        
        print(f"\n🎯 REP #{self.rep_count} COMPLETED - MV: {mean_velocity:.3f} m/s\n")
        
        # Beep acuto completamento (non bloccante, solo se passati >0.5s dall'ultimo)
        now = time.time()
        if now - self.last_beep_time > 0.5:
            self.last_beep_time = now
            threading.Thread(target=lambda: winsound.Beep(1000, 200), daemon=True).start()

    def check_event_window(self, current_time, current_idx, magnitude):
        """Sistema a finestra evento per rilevare squat"""
        if not self.baseline_calculated:
            return
        
        if len(self.mag_smooth_buffer) < self.MAG_SMOOTH_WINDOW:
            return
        
        # Calcola magnitudine smoothed
        mag_smooth = sum(self.mag_smooth_buffer) / len(self.mag_smooth_buffer)
        
        # Soglie baseline
        baseline_lower = self.baseline_value * (1 - self.BASELINE_ZONE)
        baseline_upper = self.baseline_value * (1 + self.BASELINE_ZONE)
        
        # === WINDOW MANAGEMENT ===
        
        # Apri finestra se baseline break + refractory rispettato + STD movimento
        if not self.window_active:
            # Trigger verso il BASSO (squat, bench press - fase eccentrica)
            trigger_down = mag_smooth < baseline_lower
            
            # Trigger verso l'ALTO (deadlift - inizio concentrico)
            # Attivo solo per profilo deadlift
            trigger_up = False
            if self.profile == 'deadlift':
                trigger_up = mag_smooth > baseline_upper
            
            if trigger_down or trigger_up:
                if (current_time - self.last_rep_end_time) >= self.REFRACTORY_PERIOD:
                    if self.current_std >= self.MIN_MOVEMENT_STD:
                        trigger_type = "DOWN" if trigger_down else "UP"
                        print(f"🔔 Trigger {trigger_type} detected: {mag_smooth:.3f}g")
                        self.open_event_window(current_time, current_idx)
            return  # Non fare altro se finestra non attiva
        
        # Finestra attiva: accumula dati
        if self.window_active:
            self.window_data_mag.append(magnitude)
            self.window_data_time.append(current_time)
            self.window_data_idx.append(current_idx)
            
            # Chiudi finestra dopo 3 secondi
            window_duration = current_time - self.window_start_time
            if window_duration >= self.WINDOW_DURATION:
                self.close_and_analyze_window(current_time)
        
        # Nota: analisi marker avviene in close_and_analyze_window()
        return

    # === OLD STATE MACHINE REMOVED - NOW USING EVENT WINDOW SYSTEM ===
    
    def notification_handler(self, sender, data):
        """BLE notification handler"""
        try:
            self.parse_chileaf_data(data)
        except Exception as e:
            print(f"Handler error: {e}")

    async def start_monitoring(self):
        """Start BLE monitoring"""
        print("\n🔵 Starting VBT monitoring...")
        
        await self.client.start_notify(self.tx_char, self.notification_handler)
        print("✅ Notifications enabled")
        
        # Start countdown
        self.countdown_active = True
        self.countdown_start_time = time.time()
        print("\n⏱️  COUNTDOWN: 3... 2... 1...")
        
        self.monitoring_active = True
        
        try:
            while self.monitoring_active and self.is_connected:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping...")
        finally:
            await self.client.stop_notify(self.tx_char)

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            print("✅ Disconnected")

async def async_main(monitor):
    """Async main function"""
    print("=" * 70)
    print("CL837 VBT MONITOR - Output Sports Style")
    print("Real-time velocity bar chart")
    print("=" * 70)
    
    try:
        if not await monitor.scan_and_connect():
            return False
        
        if not await monitor.discover_services():
            return False
        
        await monitor.start_monitoring()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def start_plot_thread(monitor):
    """Start matplotlib in background thread"""
    def run_plot():
        monitor.setup_plot()
        monitor.animation_obj = animation.FuncAnimation(
            monitor.fig, monitor.update_plot, interval=50, blit=False, cache_frame_data=False)
        monitor.plot_ready = True
        plt.show()
    
    plot_thread = threading.Thread(target=run_plot, daemon=False)
    plot_thread.start()
    
    while not monitor.plot_ready:
        time.sleep(0.1)
    
    return plot_thread

def get_load_weight() -> float:
    """Prompt user for load weight in kg"""
    print("\n" + "="*70)
    print("LOAD WEIGHT INPUT")
    print("="*70)
    print("\n⚖️  Enter the weight you're lifting (kg)")
    print("   Examples: 20, 60, 100, 140")
    print("   Press Enter to skip (power metrics will not be calculated)")
    
    while True:
        weight_input = input("\nLoad weight (kg): ").strip()
        
        if not weight_input:
            print("✅ No load weight specified. Power metrics will be 0.")
            return 0.0
        
        try:
            weight = float(weight_input)
            if weight < 0:
                print("⚠️  Weight cannot be negative. Try again.")
                continue
            if weight > 500:
                print("⚠️  Weight seems unrealistic (>500kg). Try again.")
                continue
            
            print(f"✅ Load weight set to: {weight:.1f} kg")
            return weight
            
        except ValueError:
            print("⚠️  Invalid input. Enter a number (e.g., 60)")

def select_profile_interactive() -> str:
    """Interactive profile selection menu"""
    try:
        config = VBTConfig("vbt_config.json")
        profiles = config.list_profiles()
        default_profile = config.config.get('default_profile', 'squat_speed')
        
        print("\n" + "="*70)
        print("VBT PROFILE SELECTION")
        print("="*70)
        print("\n📋 Available Profiles:\n")
        
        profile_list = list(profiles.items())
        for i, (name, desc) in enumerate(profile_list, 1):
            default_marker = " [DEFAULT]" if name == default_profile else ""
            print(f"   {i}. {name:20s} - {desc}{default_marker}")
        
        print(f"\n{'='*70}")
        choice = input(f"\nSelect profile (1-{len(profile_list)}) or press Enter for default: ").strip()
        
        if not choice:
            print(f"✅ Using default profile: {default_profile}")
            return default_profile
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(profile_list):
                selected = profile_list[idx][0]
                print(f"✅ Selected profile: {selected}")
                return selected
            else:
                print(f"⚠️  Invalid choice. Using default: {default_profile}")
                return default_profile
        except ValueError:
            print(f"⚠️  Invalid input. Using default: {default_profile}")
            return default_profile
            
    except Exception as e:
        print(f"⚠️  Error loading profiles: {e}")
        print("   Using default profile: squat_speed")
        return "squat_speed"

def main():
    """Main entry point"""
    import warnings
    import sys
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    # Parse command line args for profile selection
    profile = None
    if len(sys.argv) > 1:
        # Profile specified via command line
        profile = sys.argv[1]
        print(f"\n🚀 Starting VBT Monitor with profile: {profile}")
    else:
        # Interactive menu
        profile = select_profile_interactive()
    
    # Get load weight
    load_weight = get_load_weight()
    
    monitor = CL837VBTMonitor(config_file="vbt_config.json", profile=profile)
    monitor.load_weight_kg = load_weight
    
    try:
        # Start matplotlib in background
        print("\n🎨 Starting VBT display...")
        plot_thread = start_plot_thread(monitor)
        print("✅ Display ready")
        
        # Run BLE in main thread
        print("\n🔵 Starting BLE connection...")
        asyncio.run(async_main(monitor))
        
        print("\n✅ Monitoring completed")
        print("Waiting for display to close...")
        
        plot_thread.join()
        
    except KeyboardInterrupt:
        print("\n⏹️  Program terminated")
        monitor.monitoring_active = False
        plt.close('all')
    finally:
        monitor.monitoring_active = False

if __name__ == "__main__":
    main()
