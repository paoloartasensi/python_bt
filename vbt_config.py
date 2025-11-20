# -*- coding: utf-8 -*-
"""
VBT Configuration Manager
Load and validate parameters from JSON config file
"""

import json
from pathlib import Path
from typing import Dict, Any

class VBTConfig:
    """Configuration manager for VBT parameters with JSON profiles"""
    
    def __init__(self, config_path: str = "vbt_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.current_profile = self.config.get('default_profile', 'squat_speed')
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_profile(self, profile_name: str = None) -> Dict[str, Any]:
        """Get parameters for specific profile"""
        if profile_name is None:
            profile_name = self.current_profile
        
        if profile_name not in self.config['profiles']:
            available = list(self.config['profiles'].keys())
            raise ValueError(f"Profile '{profile_name}' not found. Available: {available}")
        
        return self.config['profiles'][profile_name]
    
    def set_profile(self, profile_name: str):
        """Switch to different profile"""
        if profile_name not in self.config['profiles']:
            raise ValueError(f"Profile '{profile_name}' not found")
        self.current_profile = profile_name
        print(f"✅ Profile switched to: {profile_name}")
    
    def list_profiles(self) -> Dict[str, str]:
        """List all available profiles with descriptions"""
        return {
            name: profile['description'] 
            for name, profile in self.config['profiles'].items()
        }
    
    def get_params(self, profile_name: str = None) -> Dict[str, float]:
        """Get flattened parameter dictionary for easy access"""
        profile = self.get_profile(profile_name)
        
        params = {}
        
        # Magnitude thresholds
        mag = profile['magnitude_thresholds']
        params['BASELINE_ZONE'] = mag['baseline_zone']
        params['MIN_DEPTH_MAG'] = mag['min_depth_mag']
        params['MIN_PEAK_MAG'] = mag['min_peak_mag']
        
        # Temporal windows
        temp = profile['temporal_windows']
        params['MIN_ECCENTRIC_WINDOW'] = temp['min_eccentric_window']
        params['MAX_CONCENTRIC_WINDOW'] = temp['max_concentric_window']
        params['MIN_CONCENTRIC_DURATION'] = temp['min_concentric_duration']
        params['REFRACTORY_PERIOD'] = temp['refractory_period']
        
        # Signal processing
        sig = profile['signal_processing']
        params['MAG_SMOOTH_WINDOW'] = sig['mag_smooth_window']
        params['STD_WINDOW'] = sig['std_window']
        
        # Movement detection
        mov = profile['movement_detection']
        params['MIN_MOVEMENT_STD'] = mov['min_movement_std']
        params['MAX_NOISE_STD'] = mov['max_noise_std']
        
        # Event window
        win = profile['event_window']
        params['WINDOW_DURATION'] = win['window_duration']
        params['PRE_BUFFER_SIZE'] = win['pre_buffer_size']
        
        # Velocity conversion
        vel = profile['velocity_conversion']
        params['VELOCITY_FACTOR'] = vel['factor']
        params['VELOCITY_CALIBRATED'] = vel.get('calibrated', False)
        
        return params
    
    def validate_params(self, params: Dict[str, float]) -> bool:
        """Validate parameter constraints"""
        errors = []
        
        # Check magnitude ordering
        if params['MIN_DEPTH_MAG'] >= params['MIN_PEAK_MAG']:
            errors.append("MIN_DEPTH_MAG must be < MIN_PEAK_MAG")
        
        # Check temporal ordering
        if params['MIN_CONCENTRIC_DURATION'] >= params['MAX_CONCENTRIC_WINDOW']:
            errors.append("MIN_CONCENTRIC_DURATION must be < MAX_CONCENTRIC_WINDOW")
        
        # Check STD gap
        if params['MAX_NOISE_STD'] >= params['MIN_MOVEMENT_STD']:
            errors.append("MAX_NOISE_STD must be < MIN_MOVEMENT_STD")
        
        std_gap = params['MIN_MOVEMENT_STD'] - params['MAX_NOISE_STD']
        if std_gap < 0.005:
            errors.append(f"STD gap too small ({std_gap:.4f}g). Recommended: >=0.005g")
        
        # Check window buffer
        max_buffer = params['WINDOW_DURATION'] * 50  # Assume 50Hz sampling
        if params['PRE_BUFFER_SIZE'] >= max_buffer:
            errors.append(f"PRE_BUFFER_SIZE ({params['PRE_BUFFER_SIZE']}) >= window capacity ({max_buffer:.0f})")
        
        if errors:
            print("❌ Parameter validation failed:")
            for err in errors:
                print(f"   - {err}")
            return False
        
        print("✅ Parameters validated successfully")
        return True
    
    def print_current_config(self):
        """Print current configuration in readable format"""
        profile = self.get_profile()
        params = self.get_params()
        
        print(f"\n{'='*70}")
        print(f"VBT CONFIGURATION: {self.current_profile}")
        print(f"Description: {profile['description']}")
        print(f"{'='*70}\n")
        
        print("📊 MAGNITUDE THRESHOLDS:")
        print(f"   Baseline Zone:   ±{params['BASELINE_ZONE']*100:.0f}% ({params['BASELINE_ZONE']:.3f})")
        print(f"   Min Depth:       {params['MIN_DEPTH_MAG']:.2f}g")
        print(f"   Min Peak:        {params['MIN_PEAK_MAG']:.2f}g")
        
        print("\n⏱️  TEMPORAL WINDOWS:")
        print(f"   Min Eccentric:   {params['MIN_ECCENTRIC_WINDOW']:.2f}s")
        print(f"   Max Concentric:  {params['MAX_CONCENTRIC_WINDOW']:.2f}s")
        print(f"   Min Concentric:  {params['MIN_CONCENTRIC_DURATION']:.2f}s")
        print(f"   Refractory:      {params['REFRACTORY_PERIOD']:.2f}s")
        
        print("\n🔧 SIGNAL PROCESSING:")
        print(f"   Mag Smooth:      {params['MAG_SMOOTH_WINDOW']} samples")
        print(f"   STD Window:      {params['STD_WINDOW']} samples")
        
        print("\n🎯 MOVEMENT DETECTION:")
        print(f"   Min Movement:    {params['MIN_MOVEMENT_STD']:.4f}g")
        print(f"   Max Noise:       {params['MAX_NOISE_STD']:.4f}g")
        std_gap = params['MIN_MOVEMENT_STD'] - params['MAX_NOISE_STD']
        print(f"   Gap:             {std_gap:.4f}g")
        
        print("\n📦 EVENT WINDOW:")
        print(f"   Duration:        {params['WINDOW_DURATION']:.2f}s")
        print(f"   Pre-buffer:      {params['PRE_BUFFER_SIZE']} samples (~{params['PRE_BUFFER_SIZE']/50:.2f}s @ 50Hz)")
        
        print("\n⚡ VELOCITY CONVERSION:")
        print(f"   Factor:          {params['VELOCITY_FACTOR']:.2f}")
        calib_status = "✅ CALIBRATED" if params['VELOCITY_CALIBRATED'] else "⚠️  NOT CALIBRATED"
        print(f"   Status:          {calib_status}")
        
        print(f"\n{'='*70}\n")


# Usage example
if __name__ == "__main__":
    # Load configuration
    config = VBTConfig("vbt_config.json")
    
    # List available profiles
    print("📋 Available Profiles:")
    for name, desc in config.list_profiles().items():
        marker = " (DEFAULT)" if name == config.current_profile else ""
        print(f"   - {name}: {desc}{marker}")
    
    # Get current parameters
    params = config.get_params()
    
    # Validate
    config.validate_params(params)
    
    # Print readable config
    config.print_current_config()
    
    # Switch profile example
    print("\n" + "="*70)
    print("Testing profile switch...")
    print("="*70)
    config.set_profile("jump")
    config.print_current_config()
