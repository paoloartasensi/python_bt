# CL837 Sleep Data & UTC Sync System

Complete sleep data management system for CL837/CL831 devices with automatic UTC synchronization and data validation.

## 📁 Files

- **`sleep.py`** - Unified script for UTC sync and sleep data download
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
5. ✅ Analyzes sleep stages (deep/light/awake)
6. ✅ Exports to CSV with timestamp

**Example output:**
```
======================================================================
CL837 SLEEP DATA DOWNLOAD
======================================================================

🔍 Scanning for CL837 devices...
📱 Found: CL837-0759665
🔗 Connecting...
✅ Connected to CL837-0759665

⏰ Syncing UTC time...
   UTC: 2025-11-09 08:47:09
   Timestamp: 1762678029
✅ UTC sync confirmed by device

💤 Requesting sleep data...
⏳ Waiting for data...
✅ Sleep data received

⚠️  Filtered out 9 invalid record(s)
✅ 7 valid record(s)

======================================================================
SLEEP DATA ANALYSIS
======================================================================

Record 1:
  📅 2025-10-21 21:49 UTC
  ⏱️  Duration: 20 min (4 intervals)
  🌙 Deep sleep: 20 min
  💤 Light sleep: 0 min
  👁️  Awake: 0 min

Record 2:
  📅 2025-10-21 22:06 UTC
  ⏱️  Duration: 40 min (8 intervals)
  🌙 Deep sleep: 40 min
  💤 Light sleep: 0 min
  👁️  Awake: 0 min

...

📄 Data exported to: sleep_data_20251109_094710.csv

🔌 Disconnected

======================================================================
✅ SLEEP DATA DOWNLOAD COMPLETED
======================================================================
```

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

Based on official Android SDK implementation:

### Activity Index Interpretation

```python
For each 5-minute interval:
  
  IF activity_index == 0:
      Count consecutive zeros
      IF 3+ consecutive zeros:
          → DEEP SLEEP
      ELSE (< 3 consecutive):
          → LIGHT SLEEP
  
  ELIF 1 ≤ activity_index ≤ 20:
      → LIGHT SLEEP
  
  ELIF activity_index > 20:
      → AWAKE
```

### Example Analysis

```
Activity indices: [0, 0, 0, 5, 0, 0, 15, 25, 0]
                   └──┬──┘  │  └─┬─┘  │   │   │
                   Deep (3) │  Light  │   │   │
                            │  (2)    │   │   │
                          Light    Light Awake Light
```

Result:
- Deep sleep: 15 minutes (3 intervals)
- Light sleep: 20 minutes (4 intervals)
- Awake: 5 minutes (1 interval)

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
pip install bleak
```

**Bleak** - Cross-platform Bluetooth Low Energy library
- Windows: Uses native Windows BLE stack
- macOS: Uses Core Bluetooth
- Linux: Uses BlueZ

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

**Last updated:** November 9, 2025
