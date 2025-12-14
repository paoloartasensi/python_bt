# -*- coding: utf-8 -*-
"""
CL837 VBT Monitor - Plotly/Dash Version
Real-time velocity bar chart with rep capture system
macOS compatible - runs in browser
"""

import asyncio
import time
import struct
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
from bleak import BleakClient, BleakScanner

# Plotly/Dash imports
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import webbrowser
from threading import Timer


# =============================================================================
# CROSS-PLATFORM BEEP
# =============================================================================

def beep(frequency=1000, duration_ms=100):
    """Cross-platform beep function"""
    try:
        if sys.platform == 'darwin':  # macOS
            os.system('afplay /System/Library/Sounds/Tink.aiff &')
        elif sys.platform == 'win32':  # Windows
            import winsound
            winsound.Beep(frequency, duration_ms)
        else:  # Linux
            os.system(f'beep -f {frequency} -l {duration_ms} &')
    except:
        print('\a', end='', flush=True)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AccelerometerData:
    """Single accelerometer sample"""
    ax: float
    ay: float
    az: float
    timestamp: float
    
    @property
    def magnitude(self) -> float:
        return math.sqrt(self.ax**2 + self.ay**2 + self.az**2)


@dataclass
class CapturedRep:
    """Captured repetition with VBT metrics"""
    rep_number: int
    velocity: float
    trigger_time: float
    trigger_index: int
    peak_index: int
    peak_magnitude: float
    baseline: float
    concentric_duration_ms: int
    samples: List[AccelerometerData] = field(default_factory=list)
    velocity_loss: float = 0.0
    
    def __str__(self) -> str:
        return (f"Rep #{self.rep_number}: {self.velocity:.3f} m/s, "
                f"VL={self.velocity_loss:.1f}%, "
                f"duration={self.concentric_duration_ms}ms")


class RepCaptureState(Enum):
    IDLE = auto()
    MONITORING = auto()
    CAPTURING = auto()
    PROCESSING = auto()


# =============================================================================
# REP CAPTURE SERVICE
# =============================================================================

class RepCaptureService:
    """Service for capturing reps using accelerometer data"""
    
    def __init__(self, 
                 sample_rate_hz: int = 50,
                 activation_threshold_g: float = 0.05,
                 pre_buffer_ms: int = 500,
                 post_trigger_ms: int = 2000):
        
        self.sample_rate_hz = sample_rate_hz
        self.activation_threshold_g = activation_threshold_g
        self.pre_buffer_samples = int(sample_rate_hz * pre_buffer_ms / 1000)
        self.post_trigger_samples = int(sample_rate_hz * post_trigger_ms / 1000)
        
        self.state = RepCaptureState.IDLE
        self.pre_buffer = deque(maxlen=self.pre_buffer_samples)
        self.capture_buffer = []
        
        self.baseline_magnitude = 1.0
        self.baseline_y = 0.0
        self.is_baseline_set = False
        
        self.trigger_index = 0
        self.post_trigger_count = 0
        
        self.rep_count = 0
        self.captured_reps = []
        self.best_velocity = 0.0
        
        self.on_rep_captured: Optional[Callable[[CapturedRep], None]] = None
        
        print(f"📊 RepCaptureService initialized:")
        print(f"   Sample rate: {sample_rate_hz} Hz")
        print(f"   Activation threshold: {activation_threshold_g}g")
        print(f"   Pre-buffer: {pre_buffer_ms}ms ({self.pre_buffer_samples} samples)")
        print(f"   Post-trigger: {post_trigger_ms}ms ({self.post_trigger_samples} samples)")
    
    def set_baseline(self, magnitude: float, y_value: float):
        """Set baseline values from calibration"""
        self.baseline_magnitude = magnitude
        self.baseline_y = y_value
        self.is_baseline_set = True
    
    def start_monitoring(self):
        """Start monitoring for reps"""
        if not self.is_baseline_set:
            raise ValueError("Baseline must be set before monitoring")
        self.state = RepCaptureState.MONITORING
    
    def process_sample(self, sample: AccelerometerData):
        """Process incoming accelerometer sample"""
        if self.state == RepCaptureState.MONITORING:
            self.pre_buffer.append(sample)
            
            # Check for trigger (Y-axis drops below baseline - threshold)
            if sample.ay < (self.baseline_y - self.activation_threshold_g):
                # Movement detected!
                self.state = RepCaptureState.CAPTURING
                self.capture_buffer = list(self.pre_buffer)
                self.trigger_index = len(self.capture_buffer) - 1
                self.post_trigger_count = 0
        
        elif self.state == RepCaptureState.CAPTURING:
            self.capture_buffer.append(sample)
            self.post_trigger_count += 1
            
            # Check if captured enough post-trigger samples
            if self.post_trigger_count >= self.post_trigger_samples:
                self._process_captured_rep()
    
    def _process_captured_rep(self):
        """Process captured buffer to extract rep metrics"""
        self.state = RepCaptureState.PROCESSING
        
        try:
            # Find peak magnitude
            magnitudes = [s.magnitude for s in self.capture_buffer]
            peak_index = np.argmax(magnitudes)
            peak_magnitude = magnitudes[peak_index]
            
            # Calculate velocity from trigger to peak
            samples_for_velocity = self.capture_buffer[self.trigger_index:peak_index+1]
            
            if len(samples_for_velocity) < 2:
                self.state = RepCaptureState.MONITORING
                return
            
            # Integrate acceleration to get velocity
            velocities = []
            for i in range(1, len(samples_for_velocity)):
                dt = samples_for_velocity[i].timestamp - samples_for_velocity[i-1].timestamp
                ay = samples_for_velocity[i].ay
                # Convert g to m/s²: g * 9.81
                accel_ms2 = ay * 9.81
                if i == 1:
                    velocities.append(accel_ms2 * dt)
                else:
                    velocities.append(velocities[-1] + accel_ms2 * dt)
            
            mean_velocity = abs(np.mean(velocities)) if velocities else 0.0
            
            # Calculate duration
            trigger_time = self.capture_buffer[self.trigger_index].timestamp
            peak_time = self.capture_buffer[peak_index].timestamp
            duration_ms = int((peak_time - trigger_time) * 1000)
            
            # Validate rep
            if mean_velocity < 0.05 or duration_ms < 100 or duration_ms > 3000:
                self.state = RepCaptureState.MONITORING
                return
            
            # Create rep object
            self.rep_count += 1
            
            # Update best velocity
            if mean_velocity > self.best_velocity:
                self.best_velocity = mean_velocity
            
            # Calculate velocity loss
            velocity_loss = 0.0
            if self.best_velocity > 0:
                velocity_loss = ((self.best_velocity - mean_velocity) / self.best_velocity) * 100
            
            rep = CapturedRep(
                rep_number=self.rep_count,
                velocity=mean_velocity,
                trigger_time=trigger_time,
                trigger_index=self.trigger_index,
                peak_index=peak_index,
                peak_magnitude=peak_magnitude,
                baseline=self.baseline_magnitude,
                concentric_duration_ms=duration_ms,
                samples=self.capture_buffer.copy(),
                velocity_loss=velocity_loss
            )
            
            self.captured_reps.append(rep)
            
            # Callback
            if self.on_rep_captured:
                self.on_rep_captured(rep)
            
            print(f"\n🎯 {rep}")
            beep(1200, 100)
            
        finally:
            # Reset to monitoring
            self.capture_buffer = []
            self.state = RepCaptureState.MONITORING


# =============================================================================
# VBT MONITOR WITH PLOTLY/DASH
# =============================================================================

class CL837VBTMonitor:
    """VBT Monitor with BLE and Plotly/Dash visualization"""
    
    def __init__(self):
        # BLE
        self.CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_HEADER = 0xFF
        self.CHILEAF_CMD_ACCELEROMETER = 0x0C
        self.CHILEAF_CONVERSION_FACTOR = 4096.0
        
        self.client = None
        self.device = None
        self.monitoring_active = False
        
        # Rep capture service
        self.rep_service = RepCaptureService(
            sample_rate_hz=50,
            activation_threshold_g=0.05,
            pre_buffer_ms=500,
            post_trigger_ms=2000
        )
        self.rep_service.on_rep_captured = self.on_rep_captured
        
        # Data buffers
        self.magnitude_data = deque(maxlen=300)
        self.timestamps_data = deque(maxlen=300)
        self.velocity_history = []
        self.rep_numbers = []
        
        # Calibration
        self.baseline_calculated = False
        self.countdown_active = False
        self.countdown_start_time = None
        self.countdown_duration = 3.0
        self.baseline_samples = []
        self.BASELINE_SAMPLES_COUNT = 25
        
        # Weight
        self.load_weight_kg = 20.0
        
        # Stats
        self.sample_count = 0
        
        # Dash app
        self.app = None
    
    def on_rep_captured(self, rep: CapturedRep):
        """Callback when rep is captured"""
        self.velocity_history.append(rep.velocity)
        self.rep_numbers.append(rep.rep_number)
    
    async def scan_and_connect(self):
        """Scan and connect to CL837"""
        print("\n🔍 Searching for CL837 devices...")
        
        devices = await BleakScanner.discover(timeout=5.0)
        cl837_devices = [d for d in devices if d.name and "CL837" in d.name]
        
        if not cl837_devices:
            print("❌ No CL837 devices found")
            return False
        
        print(f"\nFound {len(cl837_devices)} CL837 device(s):")
        for i, device in enumerate(cl837_devices):
            print(f"   {i+1}. {device.name} ({device.address})")
        
        self.device = cl837_devices[0]
        print(f"\n→ Connecting to: {self.device.name}")
        
        try:
            self.client = BleakClient(self.device.address, timeout=20.0)
            await self.client.connect()
            print("✅ Connected!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def discover_services(self):
        """Discover and configure BLE services"""
        if not self.client or not self.client.is_connected:
            return False
        
        print("\n📡 Discovering services...")
        
        # Find Chileaf service
        service = None
        tx_char = None
        
        for s in self.client.services:
            if s.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                service = s
                for char in s.characteristics:
                    if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                        tx_char = char
                break
        
        if not service or not tx_char:
            print("❌ Chileaf service not found")
            return False
        
        if "notify" not in tx_char.properties:
            print("❌ TX characteristic doesn't support notify")
            return False
        
        print("✅ Chileaf service configured")
        self.tx_char = tx_char
        return True
    
    async def start_monitoring(self):
        """Start BLE monitoring"""
        # Enable notifications
        await self.client.start_notify(self.CHILEAF_TX_UUID, self.notification_handler)
        
        # Send accelerometer command
        cmd = bytes([self.CHILEAF_HEADER, self.CHILEAF_CMD_ACCELEROMETER, 0x01])
        await self.client.write_gatt_char(self.CHILEAF_RX_UUID, cmd, response=False)
        
        print("\n✅ Monitoring started")
        print("🎯 Keep device still for calibration countdown...")
        
        # Keep monitoring alive
        while self.monitoring_active:
            await asyncio.sleep(0.1)
    
    def notification_handler(self, sender, data):
        """Handle BLE notifications"""
        if len(data) < 7:
            return
        
        if data[0] != self.CHILEAF_HEADER or data[1] != self.CHILEAF_CMD_ACCELEROMETER:
            return
        
        # Parse accelerometer data
        ax_raw = struct.unpack('<h', data[2:4])[0]
        ay_raw = struct.unpack('<h', data[4:6])[0]
        az_raw = struct.unpack('<h', data[6:8])[0]
        
        ax = ax_raw / self.CHILEAF_CONVERSION_FACTOR
        ay = ay_raw / self.CHILEAF_CONVERSION_FACTOR
        az = az_raw / self.CHILEAF_CONVERSION_FACTOR
        
        sample = AccelerometerData(
            ax=ax, ay=ay, az=az,
            timestamp=time.time()
        )
        
        self.magnitude_data.append(sample.magnitude)
        self.timestamps_data.append(sample.timestamp)
        self.sample_count += 1
        
        # Baseline calibration
        if not self.baseline_calculated:
            if not self.countdown_active:
                self.countdown_active = True
                self.countdown_start_time = time.time()
                print("\n⏱️ Calibration countdown started...")
            else:
                elapsed = time.time() - self.countdown_start_time
                if elapsed >= self.countdown_duration:
                    self.baseline_samples.append(sample)
                    
                    if len(self.baseline_samples) >= self.BASELINE_SAMPLES_COUNT:
                        magnitudes = [s.magnitude for s in self.baseline_samples]
                        y_values = [s.ay for s in self.baseline_samples]
                        
                        baseline_mag = sum(magnitudes) / len(magnitudes)
                        baseline_y = sum(y_values) / len(y_values)
                        
                        self.rep_service.set_baseline(baseline_mag, baseline_y)
                        self.rep_service.start_monitoring()
                        self.baseline_calculated = True
                        
                        print(f"\n✅ Baseline: mag={baseline_mag:.4f}g, Y={baseline_y:.4f}g")
                        print("🎯 START TRAINING!\n")
                        beep(800, 200)
        else:
            self.rep_service.process_sample(sample)
    
    async def run_ble(self):
        """Run BLE connection and monitoring"""
        try:
            if not await self.scan_and_connect():
                return
            if not await self.discover_services():
                return
            await self.start_monitoring()
        except Exception as e:
            print(f"\n❌ BLE Error: {e}")
        finally:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
    
    def create_dash_app(self):
        """Create Dash app for visualization"""
        self.app = dash.Dash(__name__)
        
        self.app.layout = html.Div([
            html.H1("🏋️ CL837 VBT Monitor", style={'textAlign': 'center'}),
            html.Div(id='stats', style={'textAlign': 'center', 'fontSize': 20, 'marginBottom': 20}),
            dcc.Graph(id='live-graph'),
            dcc.Interval(
                id='interval-component',
                interval=100,  # Update every 100ms
                n_intervals=0
            )
        ])
        
        @self.app.callback(
            [Output('live-graph', 'figure'),
             Output('stats', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_graph(n):
            # Create subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Magnitude (Real-time)', 'Velocity History (VBT)'),
                vertical_spacing=0.15,
                row_heights=[0.5, 0.5]
            )
            
            # Magnitude trace
            if len(self.magnitude_data) > 0:
                fig.add_trace(
                    go.Scatter(
                        y=list(self.magnitude_data),
                        mode='lines',
                        name='Magnitude',
                        line=dict(color='purple', width=2)
                    ),
                    row=1, col=1
                )
            
            # Velocity bar chart
            if len(self.velocity_history) > 0:
                colors = ['green' if i == 0 else 'lightgreen' if vl < 10 else 'yellow' if vl < 20 else 'red' 
                          for i, vl in enumerate([
                              ((self.rep_service.best_velocity - v) / self.rep_service.best_velocity * 100) if self.rep_service.best_velocity > 0 else 0
                              for v in self.velocity_history
                          ])]
                
                fig.add_trace(
                    go.Bar(
                        x=self.rep_numbers,
                        y=self.velocity_history,
                        name='Velocity',
                        marker=dict(color=colors),
                        text=[f'{v:.3f}' for v in self.velocity_history],
                        textposition='outside'
                    ),
                    row=2, col=1
                )
            
            fig.update_xaxes(title_text="Sample", row=1, col=1)
            fig.update_yaxes(title_text="Magnitude (g)", row=1, col=1)
            fig.update_xaxes(title_text="Rep Number", row=2, col=1)
            fig.update_yaxes(title_text="Velocity (m/s)", row=2, col=1)
            
            fig.update_layout(
                height=800,
                showlegend=False,
                title_text=f"Load: {self.load_weight_kg:.0f} kg"
            )
            
            # Stats text
            reps = len(self.velocity_history)
            best_v = self.rep_service.best_velocity
            last_v = self.velocity_history[-1] if self.velocity_history else 0
            vl = ((best_v - last_v) / best_v * 100) if best_v > 0 else 0
            
            stats_text = f"Reps: {reps} | Best: {best_v:.3f} m/s | Last: {last_v:.3f} m/s | VL: {vl:.1f}%"
            
            return fig, stats_text
    
    def run(self):
        """Main run loop"""
        # Get weight
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
        
        print(f"\n→ Weight: {self.load_weight_kg:.0f} kg")
        
        # Create Dash app
        self.create_dash_app()
        
        # Start BLE in background thread
        def run_ble_thread():
            asyncio.run(self.run_ble())
        
        ble_thread = threading.Thread(target=run_ble_thread, daemon=True)
        self.monitoring_active = True
        
        print("\n🔵 Starting BLE...")
        ble_thread.start()
        
        # Open browser after short delay
        def open_browser():
            webbrowser.open('http://127.0.0.1:8050')
        
        Timer(1.5, open_browser).start()
        
        # Run Dash app (blocking)
        print("\n🌐 Starting web dashboard at http://127.0.0.1:8050")
        print("   (Browser will open automatically)")
        print("\n   Press Ctrl+C to stop\n")
        
        try:
            self.app.run_server(debug=False, use_reloader=False, port=8050)
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted")
        finally:
            self.monitoring_active = False
            print("\n✓ VBT Monitor terminated cleanly")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("CL837 VBT MONITOR - PLOTLY VERSION")
    print("Browser-based visualization (macOS compatible)")
    print("="*70)
    
    monitor = CL837VBTMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
