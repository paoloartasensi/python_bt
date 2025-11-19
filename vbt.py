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
from collections import deque
import winsound  # Per beep audio su Windows
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from bleak import BleakClient, BleakScanner

class CL837VBTMonitor:
    """Minimalist VBT monitor with Output Sports style bar chart"""
    
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
        
        # Data buffers (small - only for current rep)
        self.max_samples = 150  # ~3 seconds at 50Hz
        self.magnitude_data = deque(maxlen=self.max_samples)
        self.timestamps_data = deque(maxlen=self.max_samples)
        self.velocity_data = deque(maxlen=self.max_samples)
        
        # VBT State Machine - BASATO SU MAGNITUDINE (più affidabile)
        self.BASELINE_ZONE = 0.08  # ±8% dalla baseline = zona REST
        self.MIN_DEPTH_MAG = 0.90  # Deve scendere sotto 0.90g per validare squat
        
        self.MIN_ECCENTRIC_WINDOW = 0.20  # s - minimo 200ms discesa
        self.MAX_CONCENTRIC_WINDOW = 2.0  # s - massimo 2s spinta
        self.MIN_CONCENTRIC_DURATION = 0.15  # s - minimo 150ms spinta
        self.REFRACTORY_PERIOD = 0.5  # s - pausa tra rep
        
        self.MAG_SMOOTH_WINDOW = 5  # Smoothing magnitudine
        self.mag_smooth_buffer = deque(maxlen=self.MAG_SMOOTH_WINDOW)
        
        # State Machine
        self.vbt_state = 'REST'
        self.eccentric_start_time = None
        self.eccentric_start_idx = None
        self.bottom_time = None
        self.bottom_idx = None
        self.concentric_start_time = None
        self.concentric_start_idx = None
        self.last_rep_end_time = -self.REFRACTORY_PERIOD
        
        # Baseline calibration
        self.baseline_calculated = False
        self.baseline_samples = []
        self.BASELINE_SAMPLES_COUNT = 25
        self.baseline_value = 1.0
        
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
                                                           gridspec_kw={'height_ratios': [2, 1]})
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
        self.ax_scope.set_ylim(0, 4.0)  # SCALA FISSA 0-4g
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
        self.ax_scope.set_ylim(0, 4.0)  # SCALA FISSA 0-4g
        self.ax_scope.grid(True, alpha=0.3)
        
        if len(self.magnitude_data) > 0:
            mag_list = list(self.magnitude_data)
            vel_list = list(self.velocity_data)
            indices = list(range(len(mag_list)))
            
            # Plot magnitude
            self.ax_scope.plot(indices, mag_list, 'purple', linewidth=2, alpha=0.8, label='Magnitude')
            
            # Reference lines
            self.ax_scope.axhline(y=1.0, color='blue', linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (1g)')
            
            # Highlight current state with background color
            if self.vbt_state == 'ECCENTRIC':
                self.ax_scope.axhspan(0, 2, color='red', alpha=0.1, label='ECCENTRIC')
            elif self.vbt_state == 'CONCENTRIC':
                self.ax_scope.axhspan(0, 2, color='green', alpha=0.1, label='CONCENTRIC')
            
            # Mark bottom position if in concentric
            if self.vbt_state == 'CONCENTRIC' and self.bottom_idx is not None:
                bottom_relative = self.bottom_idx - (len(self.magnitude_data) - len(mag_list))
                if 0 <= bottom_relative < len(mag_list):
                    self.ax_scope.scatter([bottom_relative], [mag_list[bottom_relative]], 
                                         s=200, marker='o', color='red', edgecolors='black', 
                                         linewidths=2, zorder=10, label='Bottom')
            
            # Update X-axis
            if indices:
                self.ax_scope.set_xlim(0, max(self.max_samples, len(indices)))
            
            # Add baseline zones
            if self.baseline_calculated:
                baseline_upper = self.baseline_value * (1 + self.BASELINE_ZONE)
                baseline_lower = self.baseline_value * (1 - self.BASELINE_ZONE)
                self.ax_scope.axhline(y=baseline_upper, color='red', linestyle=':', linewidth=1, alpha=0.3)
                self.ax_scope.axhline(y=baseline_lower, color='green', linestyle=':', linewidth=1, alpha=0.3)
                self.ax_scope.axhline(y=self.MIN_DEPTH_MAG, color='orange', linestyle='--', linewidth=1, alpha=0.5, label=f'Min Depth ({self.MIN_DEPTH_MAG}g)')
            
            # Add state and velocity info as text
            state_color = {'REST': 'gray', 'ECCENTRIC': 'red', 'CONCENTRIC': 'green'}.get(self.vbt_state, 'black')
            current_vel = vel_list[-1] if vel_list else 0.0
            current_mag = mag_list[-1] if mag_list else 0.0
            info_text = f"State: {self.vbt_state} | Mag: {current_mag:.3f}g | Vel: {current_vel:.3f} m/s"
            self.ax_scope.text(0.02, 0.98, info_text, transform=self.ax_scope.transAxes,
                              fontsize=10, verticalalignment='top', fontweight='bold',
                              color=state_color,
                              bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
            
            self.ax_scope.legend(loc='upper right', fontsize=8)
        
        return [self.status_text, self.countdown_text]

    def get_status_text(self):
        """Generate status text for display"""
        elapsed = time.time() - self.start_time
        
        if not self.baseline_calculated:
            status = "🔄 CALIBRATING..."
        elif self.vbt_state == 'REST':
            status = "⏳ WAITING FOR REP..."
        elif self.vbt_state == 'ECCENTRIC':
            status = "⬇️  ECCENTRIC"
        elif self.vbt_state == 'CONCENTRIC':
            status = "⬆️  CONCENTRIC"
        else:
            status = "🔵 MONITORING"
        
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
            
            # Baseline calibration (first 25 samples after countdown)
            if not self.baseline_calculated and not self.countdown_active:
                self.baseline_samples.append(magnitude)
                if len(self.baseline_samples) >= self.BASELINE_SAMPLES_COUNT:
                    import numpy as np
                    self.baseline_value = np.median(self.baseline_samples)
                    self.baseline_calculated = True
                    print(f"\n✅ BASELINE CALIBRATED: {self.baseline_value:.3f}g")
                    print("🟢 VBT MONITORING ACTIVE\n")
                return
            
            # Real-time velocity integration (FIXED 1.0g gravity compensation)
            if self.baseline_calculated and len(self.timestamps_data) >= 2:
                dt = self.timestamps_data[-1] - self.timestamps_data[-2]
                # GRAVITY COMPENSATION - Fixed 1.0g (Vitruve/Beast/Enode standard)
                mag_accel_net = (magnitude - 1.0) * 9.81  # m/s²
                self.current_velocity = self.current_velocity + mag_accel_net * dt
                self.velocity_data.append(self.current_velocity)
                
                # Check state transitions (basato su magnitudine, non velocity)
                self.check_vbt_state_transition(timestamp, len(self.magnitude_data) - 1)
            else:
                self.velocity_data.append(0.0)
                
        except struct.error as e:
            print(f"Unpack error: {e}")

    def check_vbt_state_transition(self, current_time, current_idx):
        """VBT state machine basato su MAGNITUDINE (pattern matching)"""
        if not self.baseline_calculated:
            return
        
        if len(self.mag_smooth_buffer) < self.MAG_SMOOTH_WINDOW:
            return
        
        # Calcola magnitudine smoothed
        mag_smooth = sum(self.mag_smooth_buffer) / len(self.mag_smooth_buffer)
        
        # Soglie baseline
        baseline_upper = self.baseline_value * (1 + self.BASELINE_ZONE)
        baseline_lower = self.baseline_value * (1 - self.BASELINE_ZONE)
        
        # STATE MACHINE BASATO SU MAGNITUDINE
        if self.vbt_state == 'REST':
            # Inizia ECCENTRIC quando scende sotto baseline
            if mag_smooth < baseline_lower:
                if (current_time - self.last_rep_end_time) >= self.REFRACTORY_PERIOD:
                    self.vbt_state = 'ECCENTRIC'
                    self.eccentric_start_time = current_time
                    self.eccentric_start_idx = current_idx
                    self.bottom_time = None
                    self.bottom_idx = None
                    print(f"⬇️  ECCENTRIC START (mag={mag_smooth:.3f}g < {baseline_lower:.3f}g)")
        
        elif self.vbt_state == 'ECCENTRIC':
            # Rileva BOTTOM quando magnitudine risale verso baseline
            # Cerca il minimo locale
            mag_list = list(self.magnitude_data)
            if len(mag_list) >= 10:
                recent_mags = mag_list[-10:]
                current_mag = mag_list[-1]
                min_mag = min(recent_mags)
                
                # Bottom = minimo raggiunto E sta risalendo
                if current_mag > min_mag + 0.02:  # Risalendo di almeno 0.02g
                    eccentric_duration = current_time - self.eccentric_start_time
                    if eccentric_duration >= self.MIN_ECCENTRIC_WINDOW:
                        # Trova indice del vero bottom (minimo)
                        min_idx = len(mag_list) - 10 + recent_mags.index(min_mag)
                        
                        # Verifica profondità
                        if min_mag < self.MIN_DEPTH_MAG:
                            self.vbt_state = 'CONCENTRIC'
                            self.bottom_time = current_time - (0.02 * (len(recent_mags) - recent_mags.index(min_mag)))
                            self.bottom_idx = min_idx
                            self.concentric_start_time = self.bottom_time
                            self.concentric_start_idx = min_idx
                            self.current_velocity = 0.0  # Reset at bottom
                            print(f"🔄 BOTTOM DETECTED (mag={min_mag:.3f}g) → CONCENTRIC START")
                        else:
                            print(f"⚠️  Depth insufficiente: {min_mag:.3f}g >= {self.MIN_DEPTH_MAG}g")
                            self.vbt_state = 'REST'
        
        elif self.vbt_state == 'CONCENTRIC':
            concentric_duration = current_time - self.concentric_start_time
            
            # Fine CONCENTRIC quando:
            # 1. Ritorna in zona baseline (non solo tocca, ma stabilizza)
            # 2. Magnitudine è risalita sopra il bottom di almeno 0.15g
            mag_list = list(self.magnitude_data)
            if len(mag_list) >= 5:
                # Verifica stabilità in baseline (ultimi 5 samples)
                recent_mags = mag_list[-5:]
                all_in_baseline = all(baseline_lower <= m <= baseline_upper for m in recent_mags)
                
                # Verifica risalita significativa dal bottom
                if self.bottom_idx is not None and len(mag_list) > self.bottom_idx:
                    bottom_mag = mag_list[self.bottom_idx]
                    rise_amount = mag_smooth - bottom_mag
                else:
                    rise_amount = 0.0
                
                if all_in_baseline and rise_amount >= 0.15:
                    if concentric_duration >= self.MIN_CONCENTRIC_DURATION:
                        print(f"✅ CONCENTRIC END (mag={mag_smooth:.3f}g, rise={rise_amount:.3f}g)")
                        self.finalize_rep(current_time, current_idx)
                        self.vbt_state = 'REST'
            
            # Timeout
            if concentric_duration > self.MAX_CONCENTRIC_WINDOW:
                print(f"⚠️  CONCENTRIC TIMEOUT ({concentric_duration:.1f}s) - Resetting to REST")
                self.vbt_state = 'REST'
                self.current_velocity = 0.0

    def finalize_rep(self, end_time, end_idx):
        """Calculate VBT metrics and finalize rep"""
        if self.concentric_start_idx is None or end_idx <= self.concentric_start_idx:
            return
        
        # Extract concentric phase
        mag_list = list(self.magnitude_data)
        time_list = list(self.timestamps_data)
        vel_list = list(self.velocity_data)
        
        concentric_mag = mag_list[self.concentric_start_idx:end_idx + 1]
        concentric_time = time_list[self.concentric_start_idx:end_idx + 1]
        concentric_vel = vel_list[self.concentric_start_idx:end_idx + 1]
        
        if len(concentric_vel) < 2:
            return
        
        # Calculate metrics
        import numpy as np
        
        # Mean Velocity (positive only)
        positive_vel = [v for v in concentric_vel if v > 0]
        if positive_vel:
            mean_velocity = np.mean(positive_vel)
            peak_velocity = np.max(concentric_vel)
            
            # Mean Propulsive Velocity (where acceleration > 0)
            mag_accel = [(concentric_mag[i] - 1.0) * 9.81 for i in range(len(concentric_mag))]
            propulsive_indices = [i for i, a in enumerate(mag_accel) if a > 0]
            if propulsive_indices:
                mpv = np.mean([concentric_vel[i] for i in propulsive_indices])
            else:
                mpv = 0.0
        else:
            mean_velocity = 0.0
            peak_velocity = 0.0
            mpv = 0.0
        
        # Store metrics
        self.rep_count += 1
        self.rep_numbers.append(self.rep_count)
        self.rep_velocities.append(mean_velocity)
        self.last_mean_velocity = mean_velocity
        self.last_peak_velocity = peak_velocity
        self.last_mpv = mpv
        self.last_rep_end_time = end_time
        
        # Print rep summary
        print(f"\n✅ REP #{self.rep_count} COMPLETED")
        print(f"   Mean Velocity: {mean_velocity:.3f} m/s")
        print(f"   Peak Velocity: {peak_velocity:.3f} m/s")
        print(f"   MPV: {mpv:.3f} m/s")
        
        # Velocity Loss
        if len(self.rep_velocities) >= 2:
            vl = ((self.rep_velocities[0] - self.rep_velocities[-1]) / self.rep_velocities[0]) * 100
            print(f"   Velocity Loss: {vl:.1f}%")
        
        # BEEP ACUSTICO! 🔊
        try:
            # Frequency 2000Hz (acuto), duration 150ms
            winsound.Beep(2000, 150)
        except:
            pass  # Ignora errori se audio non disponibile

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

def main():
    """Main entry point"""
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    monitor = CL837VBTMonitor()
    
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
