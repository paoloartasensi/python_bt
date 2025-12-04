# CL837 Sleep Data & UTC Sync System

Complete sleep data management system for CL837/CL831 devices with automatic UTC synchronization, data validation, and visualization.

## 📁 Files

- **`sleep.py`** - Unified script for UTC sync and sleep data download
- **`debug_sleep.py`** - Debug script to view ALL records (including filtered invalid ones)
- **`plot_sleep.py`** - Sleep data visualization with pie charts per night
- **`README.md`** - This file (documentation)

## 🎯 Overview

The CL837 device operates autonomously, recording sleep data internally even without smartphone connection. However, accurate timestamps require periodic UTC synchronization from an external source (phone/computer).

### How It Works

```
┌─────────────────────────────────────────┐
│ CL837 DEVICE (Autonomous)               │
├─────────────────────────────────────────┤
│ • Internal RTC (Real-Time Clock)        │
│ • Records sleep every 5 minutes         │
│ • Stores timestamps using UTC           │
│ • Limited memory (~32KB estimated)      │
└─────────────────────────────────────────┘
            ↓
     REQUIRES SYNC
            ↓
┌─────────────────────────────────────────┐
│ COMPUTER/PHONE                          │
├─────────────────────────────────────────┤
│ 1. Sync UTC time (CMD 0x08)             │
│ 2. Download sleep data (CMD 0x05)       │
│ 3. Validate timestamps                  │
│ 4. Export to CSV                        │
└─────────────────────────────────────────┘
```

## ⚙️ UTC Synchronization

### Why UTC Sync is Critical

The device's internal Real-Time Clock (RTC) maintains time autonomously, but:

- ❌ **Resets after complete battery drain** (0%)
- ❌ **Loses accuracy over time** without external reference
- ❌ **Cannot auto-detect time zone changes**

### When to Sync

| Scenario | Required? | Reason |
|----------|-----------|--------|
| **Daily use** | ✅ Recommended | Maintains timestamp accuracy |
| **After battery drain** | ✅ **CRITICAL** | RTC resets to default/random value |
| **Before downloading data** | ✅ Automatic | Script syncs before download |
| **During normal recharge** | ❌ Not needed | RTC continues running |
| **After long storage** | ✅ Recommended | Clock may have drifted |

### Battery Behavior

```
NORMAL RECHARGE (RTC maintained):
100% → 80% → 50% → 20% → Charge → 100%
✅ RTC keeps running
✅ Timestamps remain accurate

COMPLETE DRAIN (RTC resets):
20% → 5% → 1% → 0% → SHUTDOWN
❌ RTC loses power
❌ Timestamps become invalid
⚠️  SYNC REQUIRED after recharge
```

## 🚀 Quick Start

### Option 1: Quick UTC Sync Only (3-5 seconds)

```powershell
python sleep/sleep.py --sync-only
```

**When to use:**
- Daily, before wearing the device
- After battery has completely drained
- Anytime you want to ensure accurate timestamps

**Example output:**
```
======================================================================
CL837 UTC SYNC ONLY
======================================================================

🔍 Scanning for CL837 devices...
📱 Found: CL837-0759665
🔗 Connecting...
✅ Connected to CL837-0759665

⏰ Syncing UTC time...
   UTC: 2025-11-09 08:55:08
   Timestamp: 1762678508
✅ UTC sync confirmed by device

🔌 Disconnected

======================================================================
✅ UTC SYNC COMPLETED
======================================================================

Device time synchronized. All new data will have accurate timestamps.
```

### Option 2: Download Sleep Data (Includes automatic UTC sync)

```powershell
python sleep/sleep.py
```

**What it does:**
1. ✅ Scans and connects to device
2. ✅ **Automatically syncs UTC time first**
3. ✅ Downloads all sleep records
4. ✅ Validates timestamps (filters invalid data)
5. ✅ **Groups records into sleep sessions** (gap > 3h = new session)
6. ✅ Analyzes sleep stages (deep/light/awake) per session
7. ✅ Exports to CSV with timestamp

**Example output:**
```
======================================================================
CL837 SLEEP DATA DOWNLOAD
======================================================================

🔍 Scanning for CL837 devices...
📱 Found: CL837-0759364
🔗 Connecting...
✅ Connected to CL837-0759364

⏰ Syncing UTC time...
   UTC: 2025-12-04 10:00:15
   Timestamp: 1764842415
✅ UTC sync confirmed by device

💤 Requesting sleep data...
⏳ Waiting for data...
✅ Sleep data received

⚠️  Filtered out 43 invalid record(s)
✅ 50 valid record(s)

======================================================================
SLEEP DATA ANALYSIS
======================================================================

📊 Found 4 sleep session(s), 50 record(s)

──────────────────────────────────────────────────────────────────────
SESSION 1: 2025-11-07 20:25 → 23:25 UTC
──────────────────────────────────────────────────────────────────────
  📊 Total tracked: 195 min (3h 15m)
  🌙 Deep sleep:    120 min (2h 0m)
  💤 Light sleep:   60 min (1h 0m)
  👁️  Awake:         15 min
  📦 Records:       4

──────────────────────────────────────────────────────────────────────
SESSION 2: 2025-12-02 23:25 → 06:25 UTC
──────────────────────────────────────────────────────────────────────
  📊 Total tracked: 420 min (7h 0m)
  🌙 Deep sleep:    180 min (3h 0m)
  💤 Light sleep:   200 min (3h 20m)
  👁️  Awake:         40 min
  📦 Records:       12

📄 Data exported to: sleep_data_20251204_110015.csv

🔌 Disconnected

======================================================================
✅ SLEEP DATA DOWNLOAD COMPLETED
======================================================================
```

### Option 3: Debug All Records (Including Invalid)

```powershell
python sleep/debug_sleep.py
```

**When to use:**
- Investigating missing data
- Verifying device is recording correctly
- Checking raw timestamps before filtering

**Shows ALL 93 records** including those filtered as invalid (wrong timestamps, future dates, etc.)

### Option 4: Visualize Sleep Data

```powershell
python sleep/plot_sleep.py
```

**What it does:**
1. ✅ Loads most recent CSV export
2. ✅ Groups records into nights (18:00→18:00 logic)
3. ✅ **Generates pie chart per night** with sleep phases
4. ✅ Shows bedtime and wake-up time for each night
5. ✅ Calculates sleep efficiency percentage
6. ✅ Saves charts to `plots/` folder

## 📊 Data Visualization

### Pie Charts per Night

The `plot_sleep.py` script generates intuitive pie charts for each night:

```
┌─────────────────────────────────────────────────────────┐
│          Night 3→4 Dec 2025                             │
│                                                         │
│              🌙 Deep: 45%                               │
│           ┌────────────┐                                │
│          ╱   Deep      ╲     💤 Light: 42%              │
│         │    Sleep     │                                │
│          ╲   (3h 15m)  ╱     👁️ Awake: 13%              │
│           └────────────┘                                │
│                                                         │
│  🛏️ Bedtime: 22:25    ⏰ Wake: 08:25                    │
│  📊 Total: 7h 15m     💯 Efficiency: 87%               │
└─────────────────────────────────────────────────────────┘
```

### Chart Features

| Feature | Description |
|---------|-------------|
| **Pie chart per night** | Visual breakdown of sleep phases |
| **Sleep/wake times** | Extracted from first/last record |
| **Total duration** | Sum of all phases |
| **Sleep efficiency** | (Deep + Light) / Total × 100 |
| **Color coding** | Deep=navy, Light=blue, Awake=orange |

### Output Files

Charts are saved to `sleep/plots/`:
- `night_pies.png` - Grid of pie charts for all nights
- `daily_summary.png` - Bar chart comparison
- `activity_heatmap.png` - Movement patterns
- `hypnogram.png` - Classic sleep stage timeline

## 📊 Data Validation

### Automatic Filtering

The script automatically filters out invalid records based on:

| Criterion | Rule | Example |
|-----------|------|---------|
| **Too old** | Before 2020-01-01 | ❌ 2008-04-18 (corrupted/default value) |
| **Future date** | After current time | ❌ 2030-03-17 (impossible) |
| **Empty records** | Duration = 0 | ❌ No actual sleep data |
| **Valid** | 2020 ≤ date ≤ now AND duration > 0 | ✅ 2025-10-21 |

### Why Invalid Timestamps Occur

1. **Corrupted records** - Device memory errors or firmware defaults
2. **Factory test data** - Pre-release testing timestamps
3. **Battery drain** - RTC reset to default values (often 2008 or 1970)
4. **No initial sync** - Device never received correct time after manufacturing

## 📄 CSV Output Format

Generated CSV files contain comprehensive sleep statistics:

```csv
record_number,utc_timestamp,datetime_utc,duration_minutes,interval_count,deep_sleep_min,light_sleep_min,awake_min,activity_indices
1,1761083392,2025-10-21 21:49:52,20,4,20,0,0,"[0, 0, 0, 0]"
2,1761084416,2025-10-21 22:06:56,40,8,40,0,0,"[0, 0, 0, 0, 0, 0, 0, 0]"
3,1761218584,2025-10-23 11:23:04,60,12,55,5,0,"[0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]"
```

### CSV Fields

- **record_number** - Sequential record ID
- **utc_timestamp** - Unix timestamp (seconds since 1970-01-01)
- **datetime_utc** - Human-readable UTC datetime
- **duration_minutes** - Total sleep duration
- **interval_count** - Number of 5-minute intervals
- **deep_sleep_min** - Deep sleep duration
- **light_sleep_min** - Light sleep duration
- **awake_min** - Awake time during sleep period
- **activity_indices** - Raw activity data (0-255 per 5 minutes)

## 🧠 Sleep Stage Detection Algorithm

Based on official Android SDK implementation.

### Activity Index Rules

| Activity Index | State | Classification |
|----------------|-------|----------------|
| **0** (3+ consecutive) | 😴😴 Deep Sleep | 3+ consecutive zeros = deep sleep |
| **0** (< 3 consecutive) | 💤 Light Sleep | Less than 3 consecutive zeros |
| **1-20** | 💤 Light Sleep | Low activity, sleeping |
| **> 20** | 👁️ Awake | High activity, awake |

### Example Analysis

```
Activity indices: [0, 0, 0, 5, 0, 0, 15, 25, 0]
                   └──┬──┘  │  └─┬─┘  │   │   │
                   Deep (3) │  Light  │   │   │
                            │  (2)    │   │   │
                          Light    Light Awake Light
```

**Result:**
- Deep sleep: 15 minutes (3 intervals)
- Light sleep: 20 minutes (4 intervals)
- Awake: 5 minutes (1 interval)

---

## 🌙 Night Awakenings Detection

### How the Device Handles Awakenings

The device **does NOT create separate records for night awakenings**. Instead:

✅ **Single continuous record** - One sleep session from bedtime to wake-up
✅ **Awakenings embedded** - High activity indices (≥20) within the record
✅ **Automatic detection** - Peaks in activity array indicate wake periods

### Example: Sleep with Awakenings

```python
Record: 23:00 → 07:00 (8 hours)
Activity: [5, 3, 2, 0, 0, 0, 15, 25, 30, 22, 10, 5, 0, 0, 0, 2, 1]
           │  │  │  └──┬──┘  │   │   │   │   │   │  └──┬──┘  │  │
           │  │  │  Deep     │   └────┬────┘   │   │  Deep   │  │
           │  │  │  sleep    │   AWAKENING     │   │  sleep  │  │
           │  │  │           │   (3×5min=15min)│   │         │  │
           └──┴──┴───────────┴─────────────────┴───┴─────────┴──┘
              Light sleep        Awake period      Light/Deep
```

### Timeline Breakdown

| Time | Activity | State | Notes |
|------|----------|-------|-------|
| 23:00-23:15 | [5,3,2] | Light sleep | Falling asleep |
| 23:15-23:30 | [0,0,0] | **Deep sleep** | First deep cycle |
| 23:30-23:45 | [15] | Light sleep | Transitioning |
| 23:45-00:15 | [25,30,22] | 👁️ **AWAKENING #1** | Bathroom/movement |
| 00:15-00:25 | [10,5] | Light sleep | Back to sleep |
| 00:25-00:40 | [0,0,0] | **Deep sleep** | Second deep cycle |
| 00:40-00:50 | [2,1] | Light sleep | Light sleep continues |

### Detecting Awakenings (Analysis Guide)

To analyze awakenings in your CSV data:

```python
# Pseudo-code for awakening detection
def detect_awakenings(activity_indices, threshold=20):
    """
    Detect night awakenings in a sleep record
    
    Returns:
        - Number of awakenings
        - Duration of each awakening
        - Total time awake
        - Sleep efficiency %
    """
    awakenings = []
    in_awakening = False
    awakening_start = None
    
    for i, activity in enumerate(activity_indices):
        if activity >= threshold:
            if not in_awakening:
                # New awakening started
                awakening_start = i
                in_awakening = True
        else:
            if in_awakening:
                # Awakening ended
                duration = (i - awakening_start) * 5  # minutes
                awakenings.append({
                    'start_interval': awakening_start,
                    'end_interval': i,
                    'duration_min': duration
                })
                in_awakening = False
    
    total_awake_min = sum(a['duration_min'] for a in awakenings)
    total_duration = len(activity_indices) * 5
    sleep_efficiency = ((total_duration - total_awake_min) / total_duration) * 100
    
    return {
        'num_awakenings': len(awakenings),
        'awakenings': awakenings,
        'total_awake_min': total_awake_min,
        'sleep_efficiency': sleep_efficiency
    }
```

### Example Output

```
Record 1: 2025-10-23 23:00:00 UTC
Duration: 480 minutes (8 hours)

Sleep Stages:
  🌙 Deep sleep: 180 min (37.5%)
  💤 Light sleep: 240 min (50.0%)
  👁️  Awake: 60 min (12.5%)

⚠️  Night Awakenings: 3
  Awakening 1: 23:45-24:00 (15 min) - peak activity: 30
  Awakening 2: 02:30-02:40 (10 min) - peak activity: 25
  Awakening 3: 05:15-05:50 (35 min) - peak activity: 28

💤 Sleep Efficiency: 87.5%
   (420 min asleep / 480 min total)
```

### Sleep Efficiency Calculation

```
Sleep Efficiency = (Total Sleep Time / Total Time in Bed) × 100

Normal ranges:
  85-100% = Excellent
  75-84%  = Good
  65-74%  = Fair
  <65%    = Poor (consider sleep consultation)
```

### Key Insights

1. **Multiple awakenings are normal** - Average adult: 1-3 per night
2. **Short awakenings (<5min)** - Often not consciously remembered
3. **Long awakenings (>20min)** - May indicate sleep issues
4. **Pattern matters** - Frequent brief awakenings vs. few long ones

### Data Analysis Tips

**In Excel/Python:**
```python
import pandas as pd

df = pd.read_csv('sleep_data_20251109_094710.csv')

# Parse activity indices from string
df['activity'] = df['activity_indices'].apply(eval)

# Count awakenings per record
df['num_awakenings'] = df['activity'].apply(
    lambda x: sum(1 for i in range(len(x)-1) 
                  if x[i] < 20 and x[i+1] >= 20)
)

# Calculate sleep efficiency
df['sleep_efficiency'] = (
    (df['deep_sleep_min'] + df['light_sleep_min']) / 
    df['duration_minutes'] * 100
)

print(df[['datetime_utc', 'num_awakenings', 'sleep_efficiency']])
```

### Visual Representation

```
Sleep Timeline (ASCII):
23:00 |████████▓▓▓▓░░░░▓▓████████| 07:00
      └─Light──┘Deep│Awake│Deep──┘
                    └─15min

Legend:
  █ = Deep sleep (activity = 0,0,0)
  ▓ = Light sleep (activity 1-20)
  ░ = Awake (activity > 20)
```

---

## �️ Sleep Onset Detection (When Sleep Starts)

### How the Device Determines Sleep Start

The CL837 device automatically detects sleep onset using these criteria:

**Hardware Detection:**
1. **Movement reduction** - Accelerometer detects sustained low activity
2. **Consistency window** - Activity must stay low for several intervals
3. **Timestamp recording** - Device records UTC timestamp of first qualifying interval

**Typical Algorithm (Firmware):**
```python
# Simplified firmware logic
def detect_sleep_onset():
    MIN_CONSECUTIVE_INTERVALS = 3  # 15 minutes sustained
    ACTIVITY_THRESHOLD = 20
    
    for i in intervals:
        if activity[i:i+3] all < ACTIVITY_THRESHOLD:
            sleep_start_time = current_timestamp
            start_recording()
            break
```

### Device-Provided Start Time

Each sleep record includes a `utc_timestamp` field:
- This is the **device-calculated start time**
- Based on firmware's sleep onset detection
- Subject to RTC accuracy (requires UTC sync!)

### Validation Rules

**Valid timestamp criteria:**
```python
MIN_VALID_TIMESTAMP = 1577836800  # 2020-01-01 (device release)
MAX_VALID_TIMESTAMP = current_time

is_valid = (
    timestamp >= MIN_VALID_TIMESTAMP and
    timestamp <= MAX_VALID_TIMESTAMP and
    duration > 0
)
```

**Invalid timestamps indicate:**
- ❌ Battery was completely drained (RTC reset)
- ❌ Device never received initial UTC sync
- ❌ Factory test data or corrupted memory

### Manual Sleep Onset Calculation

If device timestamp is invalid, you can recalculate sleep start from activity data:

```python
def calculate_sleep_onset(activity_indices, 
                         threshold=20, 
                         min_consecutive=3):
    """
    Calculate sleep onset from activity data
    
    Args:
        activity_indices: List of activity values (5-min intervals)
        threshold: Activity below this = sleep (default 20)
        min_consecutive: Sustained intervals required (default 3 = 15min)
    
    Returns:
        index: First interval where sleep is sustained
        None: If no valid sleep onset found
    """
    for i in range(len(activity_indices) - min_consecutive + 1):
        window = activity_indices[i:i + min_consecutive]
        if all(act < threshold for act in window):
            return i  # Sleep onset at interval i
    return None  # No sustained sleep detected

# Example usage
activity = [25, 30, 22, 15, 10, 5, 3, 0, 0, 0, 2, 1]
onset_index = calculate_sleep_onset(activity)
# Returns: 4 (at 10 minutes from record start)
# Actual sleep start = record_utc + (4 × 5 × 60) seconds
```

### Sleep Onset Latency

**Definition:** Time from lights-out to sleep onset

```
Sleep Onset Latency = Sleep Start Time - Bedtime

Normal ranges:
  < 15 min   = Good
  15-30 min  = Normal
  30-60 min  = Borderline
  > 60 min   = Sleep onset insomnia
```

**Note:** Device records from first sustained sleep, not from bedtime.
You need to manually log bedtime to calculate true latency.

### Edge Cases

**Short records (< 30 minutes):**
```python
if duration < 30:
    classification = "NAP"
else:
    classification = "NIGHT_SLEEP"
```

**Multiple sleep sessions:**
- Device creates separate records for distinct sleep periods
- Gap between records typically > 60 minutes
- Naps and night sleep are separate records

**Interrupted recording:**
- If you remove the device mid-sleep, current record ends
- New record starts when device detects sleep again
- Results in fragmented data for one night

### Example: Full Sleep Detection Flow

```
22:30 - User goes to bed (not detected by device)
22:45 - Still moving, reading [activity = 28, 25, 30]
23:00 - Getting sleepy [activity = 15, 12, 10]
23:15 - SLEEP ONSET DETECTED [activity = 8, 5, 3]
        ↓
        Device creates record with UTC = 1762678500 (23:15)
        
Activity array starts: [8, 5, 3, 0, 0, 0, ...]
Record timestamp: 2025-10-23 23:15:00 UTC

Sleep onset latency: 23:15 - 22:30 = 45 minutes
(but device doesn't know 22:30 - you need to log that manually)
```

### Practical Tips

1. **Trust device timestamp** if validated (between 2020 and now)
2. **Manual bedtime log** for accurate onset latency
3. **Activity threshold** can be adjusted (default 20 works well)
4. **Min duration filter** removes false positives (micro-naps)

### Configuration Parameters

| Parameter | Default | Purpose | Tuning |
|-----------|---------|---------|--------|
| `activity_threshold` | 20 | Sleep/wake boundary | Lower = more sensitive |
| `min_consecutive` | 3 (15min) | Onset detection window | Higher = less false positives |
| `min_duration` | 30 min | Nap vs. sleep filter | Adjust based on use case |

---

## �🔬 Advanced Analysis

## 🔧 Technical Details

### Chileaf Protocol

#### UTC Sync Command (0x08)

```
Frame structure:
[HEADER][LENGTH][CMD][UTC_MSB][UTC][UTC][UTC_LSB][CHECKSUM]
  0xFF    0x08   0x08   ...UTC timestamp...      calculated

UTC: 4 bytes, big-endian, Unix timestamp
```

#### Sleep Data Command (0x05)

```
Request:
[HEADER][LENGTH][CMD][SUBCMD][CHECKSUM]
  0xFF    0x05   0x05   0x02    calculated

Response (multiple packets):
[HEADER][LENGTH][CMD][SUBCMD][DATA...][CHECKSUM]
  0xFF    varies  0x05   0x03   sleep records

Data format per record:
[COUNT][UTC(4 bytes)][ACTIVITY_0]...[ACTIVITY_N]
```

### Checksum Calculation

```python
def calculate_checksum(data):
    # Sum all bytes
    checksum = sum(data) & 0xFF
    # Subtract from 0
    checksum = (0 - checksum) & 0xFF
    # XOR with 0x3A
    checksum = checksum ^ 0x3A
    return checksum
```

### BLE Services

- **Service UUID:** `aae28f00-71b5-42a1-8c3c-f9cf6ac969d0`
- **TX Characteristic:** `aae28f01-71b5-42a1-8c3c-f9cf6ac969d0` (notifications)
- **RX Characteristic:** `aae28f02-71b5-42a1-8c3c-f9cf6ac969d0` (write)

## 🔄 Comparison with Commercial Devices

### Similar Devices (Whoop, Fitbit, Garmin, Apple Watch)

All use the same fundamental approach:

| Feature | CL837 | Commercial Devices |
|---------|-------|-------------------|
| **Autonomous recording** | ✅ Yes | ✅ Yes |
| **Internal RTC** | ✅ Yes | ✅ Yes |
| **UTC sync requirement** | ✅ Periodic | ✅ Automatic (via app) |
| **Battery drain reset** | ❌ Loses time | ❌ Loses time |
| **Invalid data filtering** | ✅ Our scripts | ✅ Built-in apps |
| **Data storage** | Device + Phone | Device + Cloud |

**Key difference:** Commercial devices sync automatically when connected to their apps. With CL837, you must manually run `sync_utc.py`.

## 📱 Recommended Workflow

### Daily Routine

```
1. Wake up
2. Run: python sleep/sleep.py --sync-only    (3-5 seconds)
3. Wear device throughout the day
4. Before bed: Device on charger
5. Weekly: Download sleep data
```

### Weekly Analysis

```powershell
# Download all sleep data with automatic UTC sync
python sleep/sleep.py

# Result: sleep_data_YYYYMMDD_HHMMSS.csv
# Open in Excel/Python for analysis
```

### After Battery Drain

```
⚠️ CRITICAL: If device battery reached 0%

1. Recharge device
2. IMMEDIATELY run: python sleep/sleep.py --sync-only
3. Now safe to use - future timestamps will be correct
```

### Command Reference

```powershell
# Quick UTC sync only (3-5 seconds)
python sleep/sleep.py --sync-only
python sleep/sleep.py -s

# Full download with automatic UTC sync (15-30 seconds)
python sleep/sleep.py

# Debug: view ALL records including invalid
python sleep/debug_sleep.py

# Visualize sleep data with pie charts
python sleep/plot_sleep.py

# Show help
python sleep/sleep.py --help
```

## 🐛 Troubleshooting

### "No CL837 devices found"

- Ensure device is charged and powered on
- Check Bluetooth is enabled on computer
- Move device closer to computer
- Restart device (if possible)

### "Connection failed" or "Unreachable"

- Device may be connected to another app (disconnect from phone)
- Restart Bluetooth on computer
- Restart device
- Try again after 30 seconds

### "Invalid timestamps in CSV"

- Old data before first UTC sync (safe to filter out)
- Battery was completely drained in the past
- Run `sync_utc.py` to prevent future issues

### "No sleep data available"

- Device has no recorded sleep yet
- All records were filtered out as invalid
- Check device has been worn during sleep

## 📚 Dependencies

```bash
pip install bleak pandas matplotlib numpy
```

- **Bleak** - Cross-platform Bluetooth Low Energy library
- **Pandas** - Data manipulation and CSV handling
- **Matplotlib** - Chart generation
- **NumPy** - Numerical operations

## ⚡ Performance

| Operation | Time | Details |
|-----------|------|---------|
| UTC Sync Only | 3-5s | Scan + Connect + Sync + Disconnect |
| Full Download | 15-30s | Includes UTC sync + Data download + Analysis + CSV |
| BLE Connection | ~2s | Device scanning + connection |
| Data Transfer | ~10-20s | Depends on number of sleep records |

## 🔐 Privacy & Data Storage

- **Data stays local** - No cloud upload
- **CSV files on your computer** - Full control
- **No telemetry** - Scripts don't send any data
- **Open source** - Review all code

## ⚡ Performance

- **UTC sync**: 3-5 seconds
- **Sleep data download**: 10-30 seconds (depends on data volume)
- **CSV export**: Instant
- **BLE connection**: ~2 seconds

## 📖 Further Reading

- `docs/SLEEP_DATA_README.md` - Detailed protocol documentation
- `docs/CL831 doc d Sonnet 4.1.md` - Full command specifications
- `docs/WearManager.java` - Android SDK reference
- `docs/HeartBLEDevice.m` - iOS SDK reference

## 🤝 Related Scripts

- `scripts/sport_history.py` - 7-day sport data (steps, calories)
- `scripts/steps_history.py` - Interval step counts
- `scripts/realtime_monitor.py` - Live heart rate monitoring
- `scripts/user_info.py` - Device user configuration

---

**Last updated:** December 4, 2025
