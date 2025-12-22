# CL837 Sleep Data - Known Issues and Concerns

## Overview

This document outlines the concerns and issues discovered while working with sleep data from the CL837/CL831 Chileaf fitness band.

---

## 🔴 Critical Issues

### 1. Invalid Default Timestamps

**Problem:** The device returns timestamp `0x48000000` (April 12, 2008) for uninitialized or empty sleep records.

**Impact:**

- Data appears to be from 2008 when the device was manufactured in 2020+
- All records show identical timestamps regardless of actual sleep time
- Impossible to correlate sleep data with real dates

**Example:**

```csv
record_number,utc_timestamp,datetime_utc,duration_minutes
1,1207959552,2008-04-12 00:19:12,0
2,1207959552,2008-04-12 00:19:12,0
...
```

### 2. UTC Clock Synchronization Not Persistent

**Problem:** The device does not retain UTC time after:

- Battery fully depletes
- Device reset
- Extended periods without app connection

**Observed Behavior:**

- Fresh/reset devices return year 2008 timestamps
- Manual UTC sync via `CMD_SET_UTC (0x08)` is required
- Sync must be repeated if device loses power

**Workaround:**

```bash
python sleep.py --sync-only
```

---

## 🟡 Data Reliability Concerns

### 3. Empty Sleep Slots

**Problem:** Device returns 14 fixed memory slots regardless of actual data.

**Observed:**
- All 14 slots returned even when no sleep was tracked
- Empty slots have `duration_minutes = 0` and `activity_indices = []`
- No way to distinguish "no sleep recorded" from "device not worn"

### 4. Data Cleared After App Sync

**Problem:** The official Chileaf app may download and clear sleep data from the device.

**Impact:**
- If user syncs with official app, data is removed from device
- Our Python script will only see empty/zeroed records
- No way to recover data once cleared

### 5. Sleep Detection Accuracy Unknown

**Concerns:**
- Algorithm relies solely on accelerometer activity index
- No heart rate correlation for sleep staging
- Thresholds (deep=0 for 3+ intervals, light=1-20, awake=>20) are undocumented
- Cannot verify accuracy against polysomnography

---

## 🟠 Protocol Limitations

### 6. Limited Historical Data

**Limitation:** Device stores only ~14 sleep sessions (approximately 2 weeks).

**Impact:**
- Older data is overwritten
- No way to retrieve historical data beyond storage limit
- Must download frequently to preserve data

### 7. No Data Integrity Verification

**Problem:** No CRC or hash for sleep data packets.

**Risk:**
- Corrupted BLE transmissions may go undetected
- Packet loss during download affects data accuracy
- Only basic checksum per packet (XOR-based)

### 8. Ambiguous Activity Index Scale

**Undocumented:**
- Maximum value of activity index (observed: 0-255?)
- Calibration methodology
- Sensitivity settings
- How device distinguishes sleep from stationary wakefulness

---

## 📋 Recommendations

### For Users

1. **Sync UTC immediately** after device reset or battery replacement
2. **Avoid using official app** if you want to preserve raw data
3. **Download data daily** to prevent loss from memory overflow
4. **Verify timestamps** before trusting sleep analysis

### For Developers

1. **Always validate timestamps** against `MIN_VALID_TIMESTAMP = 1577836800` (2020-01-01)
2. **Filter empty records** where `count = 0` or `activity_indices = []`
3. **Handle missing data gracefully** in visualization code
4. **Implement retry logic** for BLE packet loss

### Validation Code Example

```python
MIN_VALID_TIMESTAMP = 1577836800  # 2020-01-01

def is_valid_sleep_record(record):
    """Check if sleep record contains valid data"""
    current_time = int(time.time())
    utc = record['utc']
    count = record['count']
    
    return (
        utc >= MIN_VALID_TIMESTAMP and  # Not before 2020
        utc <= current_time and          # Not in future
        count > 0 and                    # Has intervals
        len(record['activity_indices']) > 0  # Has activity data
    )
```

---

## 🔬 Open Questions

1. **Why 0x48000000?** - Is this a firmware-specific default or industry standard?
2. **Sleep detection algorithm** - How does the device determine sleep onset/offset?
3. **Activity index calibration** - Are values device-specific or standardized?
4. **Memory management** - FIFO or circular buffer? What triggers overwrites?
5. **Heart rate during sleep** - Why isn't HR data correlated with sleep stages?

---

## 📅 Document History

|Date|Notes|
|------|-------|
|2025-12-05|Initial documentation after discovering timestamp issues|

---

## References

- [CL831 SDK Specification](../docs/CL831%20SDK%20Specification.doc.md)
- [Sleep Data Protocol](../docs/SLEEP_DATA_README.md)
- [Device Capabilities](../docs/CL837_CAPABILITIES.md)
