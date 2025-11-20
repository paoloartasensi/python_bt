import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

# Load the bench press data
df = pd.read_csv('accel_data_20251120_152715.csv')

print("=" * 80)
print("BENCH PRESS DATA ANALYSIS")
print("=" * 80)

# Basic stats
print(f"\nTotal samples: {len(df)}")
print(f"Duration: {df['Timestamp'].max() - df['Timestamp'].min():.2f} seconds")
print(f"Sampling rate: ~{len(df)/(df['Timestamp'].max() - df['Timestamp'].min()):.1f} Hz")

print("\n" + "=" * 80)
print("MAGNITUDE STATISTICS")
print("=" * 80)
print(df['Magnitude (g)'].describe())

print("\n" + "=" * 80)
print("RAW AXIS STATISTICS")
print("=" * 80)
print(df[['X (g)', 'Y (g)', 'Z (g)']].describe())

# Apply smoothing
sigma = 2
df['Mag_smooth'] = gaussian_filter1d(df['Magnitude (g)'], sigma=sigma)

# Find baseline (first 2 seconds - likely lockout position)
baseline_mask = df['Timestamp'] < (df['Timestamp'].min() + 2.0)
baseline_mag = df.loc[baseline_mask, 'Magnitude (g)'].mean()
baseline_std = df.loc[baseline_mask, 'Magnitude (g)'].std()

print("\n" + "=" * 80)
print("BASELINE (LOCKOUT POSITION) - First 2 seconds")
print("=" * 80)
print(f"Mean magnitude: {baseline_mag:.4f} g")
print(f"Std deviation: {baseline_std:.4f} g")
print(f"Range: {df.loc[baseline_mask, 'Magnitude (g)'].min():.4f} - {df.loc[baseline_mask, 'Magnitude (g)'].max():.4f} g")

# Find minimum magnitude (chest touch)
min_mag = df['Magnitude (g)'].min()
min_idx = df['Magnitude (g)'].idxmin()
min_time = df.loc[min_idx, 'Timestamp']

print("\n" + "=" * 80)
print("MINIMUM MAGNITUDE (CHEST TOUCH)")
print("=" * 80)
print(f"Minimum magnitude: {min_mag:.4f} g")
print(f"At time: {min_time:.2f} s")

# Find all local minima (potential rep bottoms)
from scipy.signal import find_peaks

# Invert magnitude to find minima as peaks
inverted_mag = -df['Mag_smooth'].values
peaks, properties = find_peaks(inverted_mag, prominence=0.05, distance=50)

print("\n" + "=" * 80)
print(f"DETECTED REP BOTTOMS: {len(peaks)}")
print("=" * 80)
for i, peak_idx in enumerate(peaks):
    peak_time = df.loc[peak_idx, 'Timestamp']
    peak_mag = df.loc[peak_idx, 'Magnitude (g)']
    print(f"Rep {i+1}: Time={peak_time:6.2f}s, Magnitude={peak_mag:.4f}g")

# Find peaks (concentric power)
peaks_conc, _ = find_peaks(df['Mag_smooth'].values, prominence=0.05, distance=50)

print("\n" + "=" * 80)
print(f"DETECTED CONCENTRIC PEAKS: {len(peaks_conc)}")
print("=" * 80)
for i, peak_idx in enumerate(peaks_conc):
    peak_time = df.loc[peak_idx, 'Timestamp']
    peak_mag = df.loc[peak_idx, 'Magnitude (g)']
    print(f"Peak {i+1}: Time={peak_time:6.2f}s, Magnitude={peak_mag:.4f}g")

# Calculate magnitude velocity
df['Mag_velocity'] = np.gradient(df['Mag_smooth'], df['Timestamp'])

print("\n" + "=" * 80)
print("VELOCITY STATISTICS")
print("=" * 80)
print(df['Mag_velocity'].describe())

# Look for patterns - calculate time between reps
if len(peaks) > 1:
    rep_times = df.loc[peaks, 'Timestamp'].values
    rep_durations = np.diff(rep_times)
    print("\n" + "=" * 80)
    print("REP TIMING")
    print("=" * 80)
    print(f"Average rep duration: {rep_durations.mean():.2f} seconds")
    print(f"Rep durations: {rep_durations}")

print("\n" + "=" * 80)
print("KEY PATTERNS")
print("=" * 80)
print(f"Baseline magnitude: ~{baseline_mag:.3f} g (lockout position)")
print(f"Minimum magnitude: ~{min_mag:.3f} g (chest touch)")
print(f"Magnitude drop: {baseline_mag - min_mag:.3f} g")
print(f"Maximum magnitude: {df['Magnitude (g)'].max():.3f} g")
print(f"Number of reps detected: {len(peaks)}")

print("\n" + "=" * 80)
print("COMPARISON TO SQUAT")
print("=" * 80)
print("SIMILARITIES:")
print("  - Eccentric → Bottom → Concentric pattern")
print("  - Clear magnitude drop during descent")
print("  - Return to baseline after rep")
print("\nDIFFERENCES TO INVESTIGATE:")
print("  - Baseline magnitude range")
print("  - Depth of magnitude change")
print("  - Velocity patterns")
print("  - Duration of bottom phase")

# Create visualization
plt.figure(figsize=(16, 10))

# Plot 1: Full magnitude trace
plt.subplot(3, 1, 1)
plt.plot(df['Timestamp'], df['Magnitude (g)'], 'b-', alpha=0.3, label='Raw')
plt.plot(df['Timestamp'], df['Mag_smooth'], 'b-', linewidth=2, label='Smoothed')
plt.axhline(y=baseline_mag, color='g', linestyle='--', linewidth=2, label=f'Baseline: {baseline_mag:.3f}g')
plt.axhline(y=baseline_mag + baseline_std, color='g', linestyle=':', alpha=0.5)
plt.axhline(y=baseline_mag - baseline_std, color='g', linestyle=':', alpha=0.5)

# Mark rep bottoms
if len(peaks) > 0:
    plt.scatter(df.loc[peaks, 'Timestamp'], df.loc[peaks, 'Magnitude (g)'], 
                color='red', s=100, zorder=5, label=f'Rep Bottoms ({len(peaks)})')

# Mark concentric peaks
if len(peaks_conc) > 0:
    plt.scatter(df.loc[peaks_conc, 'Timestamp'], df.loc[peaks_conc, 'Magnitude (g)'], 
                color='orange', s=80, marker='^', zorder=5, label=f'Concentric Peaks ({len(peaks_conc)})')

plt.ylabel('Magnitude (g)', fontweight='bold')
plt.title('Bench Press - Magnitude Analysis', fontsize=14, fontweight='bold')
plt.legend(loc='best')
plt.grid(True, alpha=0.3)

# Plot 2: Velocity
plt.subplot(3, 1, 2)
plt.plot(df['Timestamp'], df['Mag_velocity'], 'purple', linewidth=1.5)
plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.ylabel('Magnitude Velocity (g/s)', fontweight='bold')
plt.title('Rate of Change', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3)

# Plot 3: All axes
plt.subplot(3, 1, 3)
plt.plot(df['Timestamp'], df['X (g)'], 'r-', alpha=0.7, label='X axis')
plt.plot(df['Timestamp'], df['Y (g)'], 'g-', alpha=0.7, label='Y axis')
plt.plot(df['Timestamp'], df['Z (g)'], 'b-', alpha=0.7, label='Z axis')
plt.xlabel('Time (s)', fontweight='bold')
plt.ylabel('Acceleration (g)', fontweight='bold')
plt.title('Individual Axes', fontsize=12, fontweight='bold')
plt.legend(loc='best')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('bench_press_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ Visualization saved to 'bench_press_analysis.png'")
plt.show()

print("\n" + "=" * 80)
print("RECOMMENDED THRESHOLDS FOR BENCH PRESS NOTEBOOK")
print("=" * 80)
print(f"BASELINE_MAG_MIN = {baseline_mag - 2*baseline_std:.4f}")
print(f"BASELINE_MAG_MAX = {baseline_mag + 2*baseline_std:.4f}")
print(f"ECCENTRIC_THRESHOLD = -{abs(df['Mag_velocity'].quantile(0.1)):.4f}  # Negative velocity")
print(f"CONCENTRIC_THRESHOLD = {df['Mag_velocity'].quantile(0.9):.4f}  # Positive velocity")
print(f"BOTTOM_MAG_THRESHOLD = {min_mag + 0.05:.4f}  # Slightly above minimum")
print(f"MIN_REP_DURATION = 1.0  # seconds")
print(f"PROMINENCE = 0.05  # For peak detection")
