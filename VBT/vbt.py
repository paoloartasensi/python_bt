# -*- coding: utf-8 -*-
"""
CL837 VBT Monitor - Translated from Dart vbt_test
Real-time velocity bar chart with rep capture system
Based on RepCaptureService from Flutter implementation
"""

import asyncio
import time
import struct
import traceback
import threading
import math
import numpy as np
import os
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Callable
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from bleak import BleakClient, BleakScanner


# =============================================================================
# CROSS-PLATFORM BEEP
# =============================================================================

def beep(frequency=1000, duration_ms=100):
    """Cross-platform beep function
    
    Args:
        frequency: Frequency in Hz (ignored on macOS)
        duration_ms: Duration in milliseconds (ignored on macOS)
    """
    try:
        if sys.platform == 'darwin':  # macOS
            # Use afplay with system beep sound
            os.system('afplay /System/Library/Sounds/Tink.aiff &')
        elif sys.platform == 'win32':  # Windows
            import winsound
            winsound.Beep(frequency, duration_ms)
        else:  # Linux
            os.system(f'beep -f {frequency} -l {duration_ms} &')
    except:
        # Fallback: print bell character
        print('\a', end='', flush=True)


# =============================================================================
# DATA CLASSES (translated from Dart)
# =============================================================================

@dataclass
class AccelerometerData:
    """Single accelerometer sample"""
    ax: float  # X acceleration (g)
    ay: float  # Y acceleration (g)
    az: float  # Z acceleration (g)
    timestamp: float  # Timestamp in seconds
    
    @property
    def magnitude(self) -> float:
        """Calculate acceleration magnitude"""
        return math.sqrt(self.ax**2 + self.ay**2 + self.az**2)


@dataclass
class CapturedRep:
    """Captured repetition with VBT metrics
    
    Translated from Dart CapturedRep class.
    Contains all info about a detected rep including velocity calculation.
    """
    rep_number: int
    velocity: float  # Mean velocity (m/s)
    trigger_time: float  # Time when movement triggered
    trigger_index: int  # Sample index of trigger
    peak_index: int  # Sample index of peak magnitude
    peak_magnitude: float  # Maximum magnitude during rep (g)
    baseline: float  # Baseline magnitude used (g)
    concentric_duration_ms: int  # Duration in milliseconds
    samples: List[AccelerometerData] = field(default_factory=list)
    velocity_loss: float = 0.0  # VL% compared to vBest
    
    def __str__(self) -> str:
        return (f"Rep #{self.rep_number}: {self.velocity:.3f} m/s, "
                f"VL={self.velocity_loss:.1f}%, "
                f"duration={self.concentric_duration_ms}ms, "
                f"peak={self.peak_magnitude:.3f}g")


class RepCaptureState(Enum):
    """States of the rep capture service"""
    IDLE = auto()       # Waiting to start
    MONITORING = auto()  # Active monitoring, waiting for trigger
    CAPTURING = auto()   # Capture in progress (post-trigger)
    PROCESSING = auto()  # Processing captured data


# =============================================================================
# REP CAPTURE SERVICE (translated from Dart)
# =============================================================================

class RepCaptureService:
    """Service for capturing reps using accelerometer data
    
    Translated from Dart RepCaptureService.
    
    Detection algorithm:
    1. Maintain a pre-buffer of samples (500ms default)
    2. Trigger when Y-axis breaks below baseline - threshold
    3. Capture samples for post_trigger_ms after trigger
    4. Find peak magnitude in captured window
    5. Calculate velocity by integrating acceleration from trigger to peak
    6. Validate rep with multiple filters
    """
    
    def __init__(
        self,
        sample_rate: int = 50,
        activation_threshold: float = 0.05,  # g below baseline to trigger
        pre_buffer_ms: int = 500,  # Pre-trigger buffer
        post_trigger_ms: int = 2000,  # Post-trigger capture window
        position_tolerance: float = 0.5,  # Position tolerance for validation
        min_velocity: float = 0.05,  # Minimum velocity to accept rep
        min_duration_ms: int = 100,  # Minimum concentric duration
    ):
        self.sample_rate = sample_rate
        self.activation_threshold = activation_threshold
        self.pre_buffer_ms = pre_buffer_ms
        self.post_trigger_ms = post_trigger_ms
        self.position_tolerance = position_tolerance
        self.min_velocity = min_velocity
        self.min_duration_ms = min_duration_ms
        
        # Calculate buffer sizes
        self._pre_buffer_size = int((pre_buffer_ms / 1000) * sample_rate)
        self._post_trigger_samples = int((post_trigger_ms / 1000) * sample_rate)
        
        # State
        self._state = RepCaptureState.IDLE
        self._pre_buffer: deque = deque(maxlen=self._pre_buffer_size)
        self._capture_buffer: List[AccelerometerData] = []
        self._trigger_index = 0
        self._samples_since_trigger = 0
        
        # Baseline (calibrated)
        self._baseline: float = 1.0  # Default magnitude at rest
        self._baseline_y: float = -1.0  # Default Y at rest (gravity)
        
        # Bounce filter (filtro rimbalzi)
        # Tracks if eccentric phase was detected before trigger
        self._was_above_baseline: bool = False
        
        # Results
        self._rep_count = 0
        self._v_best: float = 0.0
        self._captured_reps: List[CapturedRep] = []
        
        # Callback for captured reps
        self._on_rep_captured: Optional[Callable[[CapturedRep], None]] = None
        
        print(f"📊 RepCaptureService initialized:")
        print(f"   Sample rate: {sample_rate} Hz")
        print(f"   Activation threshold: {activation_threshold}g")
        print(f"   Pre-buffer: {pre_buffer_ms}ms ({self._pre_buffer_size} samples)")
        print(f"   Post-trigger: {post_trigger_ms}ms ({self._post_trigger_samples} samples)")
    
    @property
    def state(self) -> RepCaptureState:
        return self._state
    
    @property
    def v_best(self) -> float:
        return self._v_best
    
    @property
    def rep_count(self) -> int:
        return self._rep_count
    
    @property
    def captured_reps(self) -> List[CapturedRep]:
        return self._captured_reps.copy()
    
    def set_on_rep_captured(self, callback: Callable[[CapturedRep], None]):
        """Set callback for when a rep is captured"""
        self._on_rep_captured = callback
    
    def set_baseline(self, baseline: float, baseline_y: float = -1.0):
        """Set calibrated baseline values
        
        Args:
            baseline: Magnitude at rest (typically ~1g)
            baseline_y: Y-axis value at rest (typically -1g due to gravity)
        """
        self._baseline = baseline
        self._baseline_y = baseline_y
        print(f"📊 Baseline set: magnitude={baseline:.4f}g, Y={baseline_y:.4f}g")
    
    def start_monitoring(self):
        """Start monitoring for rep triggers"""
        if self._state != RepCaptureState.IDLE:
            print("⚠️ Already monitoring")
            return
        
        self._state = RepCaptureState.MONITORING
        self._pre_buffer.clear()
        print("🎯 Monitoring started - waiting for movement...")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self._state = RepCaptureState.IDLE
        self._pre_buffer.clear()
        self._capture_buffer.clear()
        print("⏹️ Monitoring stopped")
    
    def reset(self):
        """Reset service state"""
        self._state = RepCaptureState.IDLE
        self._pre_buffer.clear()
        self._capture_buffer.clear()
        self._rep_count = 0
        self._v_best = 0.0
        self._captured_reps.clear()
        print("🔄 RepCaptureService reset")
    
    def process_sample(self, sample: AccelerometerData):
        """Process incoming accelerometer sample
        
        This is the main entry point called for each new sample.
        Routes to appropriate handler based on current state.
        """
        if self._state == RepCaptureState.IDLE:
            return
        elif self._state == RepCaptureState.MONITORING:
            self._handle_monitoring_state(sample)
        elif self._state == RepCaptureState.CAPTURING:
            self._handle_capturing_state(sample)
    
    def _handle_monitoring_state(self, sample: AccelerometerData):
        """Handle sample during monitoring state
        
        Adds to pre-buffer and checks for trigger condition.
        Trigger: Y < baseline_y - threshold (movement upward)
        
        Includes bounce filter to avoid false triggers after eccentric phase.
        """
        # Add to pre-buffer
        self._pre_buffer.append(sample)
        
        # === BOUNCE FILTER (filtro rimbalzi) ===
        # Se Y rompe SOPRA baseline → segnala fase eccentrica
        if sample.ay > self._baseline_y + 0.05:
            self._was_above_baseline = True
        
        # Reset flag quando Y torna stabile a baseline
        if abs(sample.ay - self._baseline_y) < 0.03:
            self._was_above_baseline = False
        
        # Check trigger condition:
        # Y more negative than baseline_y - threshold indicates upward acceleration
        trigger_threshold = self._baseline_y - self.activation_threshold
        
        if sample.ay < trigger_threshold:
            if self._was_above_baseline:
                # ❌ Era preceduta da eccentrica → è un RIMBALZO
                print(f"⏭️ Rimbalzo ignorato (Y={sample.ay:.3f}g, preceduto da eccentrica)")
                self._was_above_baseline = False  # Reset
            else:
                # ✅ VERA CONCENTRICA - TRIGGER!
                print(f"🎯 TRIGGER! Y={sample.ay:.3f}g < threshold={trigger_threshold:.3f}g")
                self._start_capture(sample)
    
    def _start_capture(self, trigger_sample: AccelerometerData):
        """Start capture sequence after trigger detected"""
        self._state = RepCaptureState.CAPTURING
        
        # Copy pre-buffer to capture buffer
        self._capture_buffer = list(self._pre_buffer)
        self._trigger_index = len(self._capture_buffer) - 1
        self._samples_since_trigger = 0
        
        print(f"📹 Capture started with {len(self._capture_buffer)} pre-buffer samples")
    
    def _handle_capturing_state(self, sample: AccelerometerData):
        """Handle sample during capturing state
        
        Adds samples until post-trigger window complete.
        """
        self._capture_buffer.append(sample)
        self._samples_since_trigger += 1
        
        # Check if capture window complete
        if self._samples_since_trigger >= self._post_trigger_samples:
            self._finish_capture()
    
    def _finish_capture(self):
        """Finish capture and process data
        
        Finds peak, calculates velocity, validates rep.
        """
        self._state = RepCaptureState.PROCESSING
        samples = self._capture_buffer
        
        if len(samples) < 10:
            print("⚠️ Not enough samples for analysis")
            self._state = RepCaptureState.MONITORING
            self._pre_buffer.clear()
            self._capture_buffer.clear()
            return
        
        # Find peak magnitude after trigger
        start_idx = self._trigger_index
        peak_idx = start_idx
        max_mag = 0.0
        
        for i in range(start_idx, len(samples)):
            if samples[i].magnitude > max_mag:
                max_mag = samples[i].magnitude
                peak_idx = i
        
        # Calculate concentric duration
        dt = 1.0 / self.sample_rate
        duration_s = (peak_idx - start_idx) * dt
        duration_ms = int(duration_s * 1000)
        
        print(f"📊 Peak found at index {peak_idx}, magnitude={max_mag:.3f}g, duration={duration_ms}ms")
        
        # Calculate velocity by integrating acceleration
        velocity = self._calculate_velocity(samples, start_idx, peak_idx)
        
        # Calculate statistics for validation
        stats = self._calculate_stats(samples[start_idx:peak_idx+1] if peak_idx > start_idx else samples)
        
        # === VALIDATION FILTERS ===
        valid = True
        reject_reason = ""
        
        # Filter 1: Minimum velocity
        if velocity < self.min_velocity:
            valid = False
            reject_reason = f"velocity too low ({velocity:.3f} < {self.min_velocity})"
        
        # Filter 2: Minimum duration
        elif duration_ms < self.min_duration_ms:
            valid = False
            reject_reason = f"duration too short ({duration_ms}ms < {self.min_duration_ms}ms)"
        
        # Filter 3: Zero crossings (too many = irregular movement)
        elif stats['zero_crossings'] > 10:
            valid = False
            reject_reason = f"irregular movement (zero_crossings={stats['zero_crossings']})"
        
        # Filter 4: Negative velocity (captured eccentric instead of concentric)
        elif velocity < 0:
            valid = False
            reject_reason = f"negative velocity (eccentric captured)"
        
        if not valid:
            print(f"❌ Rep rejected: {reject_reason}")
            self._state = RepCaptureState.MONITORING
            self._pre_buffer.clear()
            self._capture_buffer.clear()
            return
        
        # === VALID REP ===
        self._rep_count += 1
        
        # Update vBest
        if velocity > self._v_best:
            self._v_best = velocity
        
        # Calculate velocity loss
        vl = ((self._v_best - velocity) / self._v_best * 100) if self._v_best > 0 else 0.0
        
        # Create CapturedRep
        captured_rep = CapturedRep(
            rep_number=self._rep_count,
            velocity=velocity,
            trigger_time=samples[start_idx].timestamp if start_idx < len(samples) else 0,
            trigger_index=start_idx,
            peak_index=peak_idx,
            peak_magnitude=max_mag,
            baseline=self._baseline,
            concentric_duration_ms=duration_ms,
            samples=list(samples),
            velocity_loss=vl,
        )
        
        self._captured_reps.append(captured_rep)
        print(f"✅ {captured_rep}")
        
        # Callback
        if self._on_rep_captured:
            self._on_rep_captured(captured_rep)
        
        # Reset for next rep
        self._pre_buffer.clear()
        self._capture_buffer.clear()
        self._state = RepCaptureState.MONITORING
        
        print("🔄 Ready for next rep...")
    
    def _calculate_velocity(
        self,
        samples: List[AccelerometerData],
        start_index: int,
        end_index: int
    ) -> float:
        """Calculate velocity by integrating net acceleration
        
        v = ∫(a - baseline) dt
        
        Uses trapezoidal integration.
        Sign determined by Y axis:
        - Y at rest = -1g (gravity)
        - Y more negative than baseline = movement DOWN (negative)
        - Y less negative than baseline = movement UP (positive)
        """
        if start_index >= end_index or end_index >= len(samples):
            return 0.0
        
        dt = 1.0 / self.sample_rate
        velocity = 0.0
        baseline_y = self._baseline_y
        
        for i in range(start_index + 1, end_index + 1):
            # Net magnitude (remove gravitational baseline) in m/s²
            mag_net_current = (samples[i].magnitude - self._baseline) * 9.81
            mag_net_prev = (samples[i-1].magnitude - self._baseline) * 9.81
            
            # Determine sign based on Y axis:
            # With negative Y at rest (~-1g):
            # - Y MORE negative than baseline (e.g., -1.5g) → acceleration UP → positive
            # - Y LESS negative than baseline (e.g., -0.5g) → acceleration DOWN → negative
            sign_current = 1.0 if samples[i].ay < baseline_y else -1.0
            sign_prev = 1.0 if samples[i-1].ay < baseline_y else -1.0
            
            # Acceleration with sign
            a_current = sign_current * mag_net_current
            a_prev = sign_prev * mag_net_prev
            
            # Trapezoidal integration
            avg_accel = (a_current + a_prev) / 2
            velocity += avg_accel * dt
        
        # Concentric velocity should be positive
        return velocity
    
    def _calculate_stats(self, samples: List[AccelerometerData]) -> dict:
        """Calculate statistics on sample window
        
        Returns dict with:
        - std_dev: Standard deviation of magnitude
        - avg_jerk: Average jerk (derivative of acceleration)
        - zero_crossings: Number of jerk sign changes
        """
        if len(samples) < 2:
            return {'std_dev': 0, 'avg_jerk': 0, 'zero_crossings': 0}
        
        # Standard deviation of magnitude
        magnitudes = [s.magnitude for s in samples]
        mean = sum(magnitudes) / len(magnitudes)
        variance = sum((m - mean)**2 for m in magnitudes) / len(magnitudes)
        std_dev = math.sqrt(variance)
        
        # Jerk (derivative of acceleration)
        dt = 1.0 / self.sample_rate
        jerks = []
        for i in range(1, len(samples)):
            jerk = (samples[i].magnitude - samples[i-1].magnitude) / dt
            jerks.append(jerk)
        
        avg_jerk = sum(abs(j) for j in jerks) / len(jerks) if jerks else 0
        
        # Zero crossings of jerk
        zero_crossings = 0
        for i in range(1, len(jerks)):
            if (jerks[i] > 0 and jerks[i-1] < 0) or (jerks[i] < 0 and jerks[i-1] > 0):
                zero_crossings += 1
        
        return {
            'std_dev': std_dev,
            'avg_jerk': avg_jerk,
            'zero_crossings': zero_crossings
        }


# =============================================================================
# VBT MONITOR (combines BLE + RepCaptureService + UI)
# =============================================================================

class CL837VBTMonitor:
    """VBT Monitor with CL837 BLE connection and bar chart display
    
    Integrates:
    - BLE connection via Chileaf protocol
    - RepCaptureService for rep detection
    - Matplotlib bar chart for velocity display
    """
    
    def __init__(self, profile: str = None):
        # Save profile name
        self.profile = profile if profile else 'default'
        
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
        
        # Rep Capture Service
        self.rep_service = RepCaptureService(
            sample_rate=50,
            activation_threshold=0.05,  # 0.05g below baseline
            pre_buffer_ms=500,  # 500ms pre-trigger
            post_trigger_ms=2000,  # 2 seconds post-trigger
        )
        self.rep_service.set_on_rep_captured(self._on_rep_captured)
        
        # Data buffers for oscilloscope display
        self.max_samples = 150  # ~3 seconds at 50Hz
        self.magnitude_data = deque(maxlen=self.max_samples)
        self.timestamps_data = deque(maxlen=self.max_samples)
        
        # Baseline calibration
        self.baseline_calculated = False
        self.baseline_samples = []
        self.BASELINE_SAMPLES_COUNT = 50  # 1 second at 50Hz
        
        # VBT Results
        self.rep_velocities = []  # List of mean velocities
        self.rep_numbers = []     # List of rep numbers
        
        # Current rep metrics (for display)
        self.last_velocity = 0.0
        
        # Statistics
        self.sample_count = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Load weight (kg)
        self.load_weight_kg = 0.0
        
        # Matplotlib
        self.fig = None
        self.ax = None
        self.ax_scope = None
        self.animation_obj = None
        self.plot_ready = False
        self.monitoring_active = False
        
        # Calibration countdown
        self.countdown_active = False
        self.countdown_start_time = None
        self.countdown_duration = 3.0
        self.countdown_text = None
        self.last_countdown_num = 0  # Track last beep
        
        print("\n" + "="*70)
        print("VBT MONITOR - Dart Translation")
        print("="*70)
    
    def on_close(self, event):
        """Handle window close event"""
        print("\n🔴 Closing VBT window...")
        self.monitoring_active = False
        plt.close('all')
    
    def _on_rep_captured(self, rep: CapturedRep):
        """Callback when rep is captured"""
        self.rep_velocities.append(rep.velocity)
        self.rep_numbers.append(rep.rep_number)
        self.last_velocity = rep.velocity
        
        # Beep on rep detection
        beep(1000, 100)  # 1kHz, 100ms
    
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
                self.client = BleakClient(self.device.address, timeout=20.0)
                await self.client.connect()
                self.is_connected = True
                print(f"✅ Connected to {self.device.name}")
                return True
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                traceback.print_exc()
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
        """Initialize bar chart + oscilloscope display"""
        print("🎨 Setting up VBT display...")
        
        # Create 2 subplots: bar chart (top) + oscilloscope (bottom)
        self.fig, (self.ax, self.ax_scope) = plt.subplots(2, 1, figsize=(12, 10), 
                                                           gridspec_kw={'height_ratios': [1, 2]})
        self.fig.suptitle("VBT MONITOR - Rep Capture", fontsize=18, fontweight='bold')
        
        # Register close event handler
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        
        # SUBPLOT 1: Bar chart (top)
        self.ax.set_xlabel("Repetition Number", fontsize=14, fontweight='bold')
        self.ax.set_ylabel("Mean Velocity (m/s)", fontsize=14, fontweight='bold')
        self.ax.set_ylim(0, 1.5)
        self.ax.grid(True, alpha=0.3, axis='y')
        
        # Velocity zone reference lines
        self.ax.axhspan(0.0, 0.15, color='red', alpha=0.1, label='Max Strength (>90% 1RM)')
        self.ax.axhspan(0.15, 0.30, color='orange', alpha=0.1, label='Strength (80-90% 1RM)')
        self.ax.axhspan(0.30, 0.50, color='yellow', alpha=0.1, label='Strength-Speed (60-80% 1RM)')
        self.ax.axhspan(0.50, 1.5, color='green', alpha=0.1, label='Speed/Power (<60% 1RM)')
        
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
        """Update bar chart + oscilloscope"""
        # Update countdown if active
        if self.countdown_active and self.countdown_start_time:
            elapsed = time.time() - self.countdown_start_time
            remaining = self.countdown_duration - elapsed
            
            if remaining > 0:
                countdown_num = int(remaining) + 1
                self.countdown_text.set_text(f"{countdown_num}")
                self.countdown_text.set_alpha(0.95)
                self.countdown_text.get_bbox_patch().set_alpha(0.9)
                
                # Beep on each countdown number change
                if countdown_num != self.last_countdown_num:
                    self.last_countdown_num = countdown_num
                    # Different frequency for each number
                    freq = 600 + (3 - countdown_num) * 200  # 600, 800, 1000 Hz
                    beep(freq, 150)
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
        status = self._get_status_text()
        self.status_text = self.ax.text(0.02, 0.98, status, transform=self.ax.transAxes,
                                        fontsize=11, verticalalignment='top',
                                        fontfamily='monospace',
                                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
        
        # === UPDATE OSCILLOSCOPE (BOTTOM) ===
        self.ax_scope.clear()
        self.ax_scope.set_title("Real-Time Magnitude + State", fontweight='bold', fontsize=12)
        self.ax_scope.set_xlabel("Samples (last 150)", fontsize=10)
        self.ax_scope.set_ylabel("Magnitude (g)", fontsize=10)
        self.ax_scope.grid(True, alpha=0.3)
        
        if len(self.magnitude_data) > 0:
            mag_list = list(self.magnitude_data)
            x_data = list(range(len(mag_list)))
            
            # Dynamic Y limits
            min_mag = min(mag_list) - 0.1
            max_mag = max(mag_list) + 0.1
            self.ax_scope.set_ylim(max(0.3, min_mag), max(1.5, max_mag))
            
            # Plot magnitude line
            self.ax_scope.plot(x_data, mag_list, 'purple', linewidth=2, alpha=0.8, label='Magnitude')
            
            # Draw baseline reference
            if self.baseline_calculated:
                baseline = self.rep_service._baseline
                self.ax_scope.axhline(y=baseline, color='blue', linestyle='--', 
                                      linewidth=1.5, alpha=0.7, label=f'Baseline ({baseline:.3f}g)')
                
                # Draw trigger threshold
                threshold = self.rep_service._baseline_y - self.rep_service.activation_threshold
                # Note: threshold is for Y-axis, not magnitude, but we show it as reference
            
            # State indicator
            state = self.rep_service.state
            state_colors = {
                RepCaptureState.IDLE: 'gray',
                RepCaptureState.MONITORING: 'green',
                RepCaptureState.CAPTURING: 'red',
                RepCaptureState.PROCESSING: 'orange'
            }
            state_color = state_colors.get(state, 'gray')
            self.ax_scope.text(0.98, 0.98, f"State: {state.name}", 
                              transform=self.ax_scope.transAxes,
                              ha='right', va='top',
                              fontsize=10, fontweight='bold',
                              color=state_color,
                              bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            self.ax_scope.legend(loc='upper left', fontsize=8)
        
        self.frame_count += 1
        return []
    
    def _get_status_text(self) -> str:
        """Generate status text for display"""
        elapsed = time.time() - self.start_time
        rate = self.sample_count / elapsed if elapsed > 0 else 0
        
        v_best = self.rep_service.v_best
        rep_count = self.rep_service.rep_count
        
        # Calculate VL% for last rep
        vl = 0.0
        if self.rep_velocities and v_best > 0:
            vl = ((v_best - self.rep_velocities[-1]) / v_best * 100)
        
        lines = [
            f"Device: {self.device.name if self.device else 'N/A'}",
            f"Weight: {self.load_weight_kg:.0f} kg",
            f"",
            f"Reps: {rep_count}",
            f"V Best: {v_best:.3f} m/s",
            f"Last V: {self.last_velocity:.3f} m/s",
            f"VL%: {vl:.1f}%",
            f"",
            f"Rate: {rate:.1f} Hz",
        ]
        
        return "\n".join(lines)
    
    def _handle_accelerometer_data(self, sender, data: bytes):
        """Handle incoming accelerometer data from BLE"""
        try:
            if len(data) < 8:
                return
            
            # Parse Chileaf protocol
            header = data[0]
            cmd = data[1]
            
            if header != self.CHILEAF_HEADER or cmd != self.CHILEAF_CMD_ACCELEROMETER:
                return
            
            # Extract raw accelerometer values (16-bit signed, big-endian)
            ax_raw = struct.unpack('>h', data[2:4])[0]
            ay_raw = struct.unpack('>h', data[4:6])[0]
            az_raw = struct.unpack('>h', data[6:8])[0]
            
            # Convert to g (gravity units)
            ax = ax_raw / self.CHILEAF_CONVERSION_FACTOR
            ay = ay_raw / self.CHILEAF_CONVERSION_FACTOR
            az = az_raw / self.CHILEAF_CONVERSION_FACTOR
            
            # Create sample
            sample = AccelerometerData(
                ax=ax,
                ay=ay,
                az=az,
                timestamp=time.time()
            )
            
            # Update display buffer
            self.magnitude_data.append(sample.magnitude)
            self.timestamps_data.append(sample.timestamp)
            
            self.sample_count += 1
            
            # Baseline calibration
            if not self.baseline_calculated:
                if not self.countdown_active:
                    # Start countdown
                    self.countdown_active = True
                    self.countdown_start_time = time.time()
                    print("\n🔔 CALIBRATION COUNTDOWN: Keep device still!")
                else:
                    # Check if countdown finished
                    elapsed = time.time() - self.countdown_start_time
                    if elapsed >= self.countdown_duration:
                        # Collect baseline samples
                        self.baseline_samples.append(sample)
                        
                        if len(self.baseline_samples) >= self.BASELINE_SAMPLES_COUNT:
                            # Calculate baseline
                            magnitudes = [s.magnitude for s in self.baseline_samples]
                            y_values = [s.ay for s in self.baseline_samples]
                            
                            baseline_mag = sum(magnitudes) / len(magnitudes)
                            baseline_y = sum(y_values) / len(y_values)
                            
                            self.rep_service.set_baseline(baseline_mag, baseline_y)
                            self.rep_service.start_monitoring()
                            self.baseline_calculated = True
                            self.monitoring_active = True
                            
                            print(f"✅ Baseline calibrated: mag={baseline_mag:.4f}g, Y={baseline_y:.4f}g")
                            print("🎯 MONITORING ACTIVE - Perform reps!")
                            
                            # Beep to signal ready
                            beep(800, 200)
            else:
                # Process sample through rep capture service
                self.rep_service.process_sample(sample)
                
        except Exception as e:
            print(f"⚠️ Error processing data: {e}")
            traceback.print_exc()

    async def start_accelerometer_stream(self):
        """Start receiving accelerometer data"""
        print("\n🎯 Starting accelerometer stream...")
        
        # Subscribe to notifications
        await self.client.start_notify(self.tx_char.uuid, self._handle_accelerometer_data)
        
        # Send start command
        start_cmd = bytes([self.CHILEAF_HEADER, self.CHILEAF_CMD_ACCELEROMETER, 0x01])
        await self.client.write_gatt_char(self.CHILEAF_RX_UUID, start_cmd)
        
        print("✅ Accelerometer stream started")

    async def run_ble(self):
        """Run BLE connection (to be called in background thread)"""
        # Connect
        if not await self.scan_and_connect():
            return False
        
        # Discover services
        if not await self.discover_services():
            return False
        
        # Start accelerometer
        await self.start_accelerometer_stream()
        
        # Keep connection alive
        try:
            while self.monitoring_active:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        
        # Cleanup
        print("\n🛑 Stopping BLE...")
        try:
            if self.client and self.client.is_connected:
                await self.client.stop_notify(self.tx_char.uuid)
                await self.client.disconnect()
                print("✅ Disconnected")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        
        return True
    
    def run(self):
        """Main run loop (macOS compatible - matplotlib in main thread)"""
        # Get weight from user FIRST (before any threading or matplotlib)
        while True:
            try:
                weight_str = input("\n🏋️ Enter weight (kg) [default: 20]: ").strip()
                if not weight_str:
                    self.load_weight_kg = 20.0
                else:
                    self.load_weight_kg = float(weight_str)
                break
            except ValueError:
                print("Invalid weight. Please enter a number.")
        
        print(f"\n→ Weight set to: {self.load_weight_kg:.0f} kg")
        
        # Setup plot in main thread BEFORE starting BLE (REQUIRED on macOS)
        print("\n🎨 Setting up display in main thread...")
        self.setup_plot()
        
        # Start BLE in background thread
        def run_ble_thread():
            asyncio.run(self.run_ble())
        
        ble_thread = threading.Thread(target=run_ble_thread, daemon=True)
        self.monitoring_active = True
        
        print("\n🔵 Starting BLE in background thread...")
        ble_thread.start()
        
        # Start animation
        print("🎬 Starting real-time display...")
        self.animation_obj = animation.FuncAnimation(
            self.fig, 
            self.update_plot, 
            interval=100,  # 10 FPS
            blit=False,
            cache_frame_data=False
        )
        
        # Show plot (blocking call in main thread)
        try:
            plt.show(block=True)
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.monitoring_active = False
            print("\n✓ VBT Monitor terminated cleanly")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("CL837 VBT MONITOR")
    print("Translated from Dart vbt_test")
    print("macOS Compatible Version")
    print("="*70)
    
    monitor = CL837VBTMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
