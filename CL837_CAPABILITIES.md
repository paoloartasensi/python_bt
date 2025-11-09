# CL837 Device Capabilities

Based on testing with actual CL837 hardware and comparison with official Android/iOS SDKs.

**See also:** [SDK_COMPARISON_ANALYSIS.md](SDK_COMPARISON_ANALYSIS.md) for detailed SDK code analysis.

## Key Finding

**Both Android and iOS SDKs support HR/RR history commands (0x21, 0x22, 0x24, 0x25)**, but the **CL837 device does NOT respond** to these commands. This is a **hardware/firmware limitation**, not a protocol issue. The SDKs are designed for the entire Chileaf product line, including higher-end models that DO support these features.

## ✅ WORKING FEATURES (Confirmed)

### 1. Sleep History (`sleep.py`)
- **Command:** 0x05
- **Status:** ✅ Fully functional
- **Test Results:** Successfully downloaded 29 sleep records
- **Data:** Timestamps, durations, activity indices (deep/light/awake detection)
- **CSV Export:** Yes

### 2. Sport 7-Day History (`sport_history.py`)
- **Commands:** 0x16
- **Status:** ✅ User confirmed working
- **Data:** Steps, distance, calories, activity statistics
- **CSV Export:** Yes

### 3. Step History (`steps_history.py`)
- **Commands:** 0x90 (records), 0x91 (data), 0x40 (interval steps)
- **Status:** ✅ Interval command (0x40) confirmed working
- **Data:** Step counts, timestamps, interval data
- **CSV Export:** Yes

### 4. Real-Time Monitoring (`realtime_monitor.py`)
- **Services:** Standard BLE HR Service (0000180d) + Chileaf custom notifications
- **Status:** ✅ Should work (not yet tested)
- **Data Available:**
  - Heart Rate (real-time via BLE HR service)
  - Sport activity (cmd 0x01 push notifications)
  - Health metrics (cmd 0x02 push notifications): VO2 Max, Emotion, Stamina, possibly RR
  - HRV data (RR intervals from HR service)
  - Accelerometer (cmd 0x0C continuous stream)
- **Features:** Live dashboard with human-readable interpretations

### 5. User Info (`user_info.py`)
- **Commands:** 0x03 (get), 0x04 (set)
- **Status:** ⚠️ Not yet tested
- **Data:** User ID, age, sex, weight, height

## ❌ NON-WORKING FEATURES (Device Limitation)

### 1. HR History (`hr_history.py`)
- **Commands:** 0x21 (records), 0x22 (data)
- **Status:** ❌ NOT SUPPORTED on CL837
- **SDK Evidence:** 
  - Android SDK has `mManager.getHistoryOfHRRecord()` method (WearManager.java line 684)
  - iOS SDK has full parsing logic for 0x21/0x22/0x23 responses (HeartBLEDevice.m line 555-704)
  - **But CL837 device doesn't respond** - confirmed by testing with debug logging
- **Reason:** Device doesn't respond to command 0x21, doesn't store HR history
- **Alternative:** Use `realtime_monitor.py` for live HR readings via BLE HR service
- **Note:** Higher-end models (CL838+) likely support this feature

### 2. Respiratory Rate History (`rr_history.py`)
- **Commands:** 0x24 (records), 0x25 (data)
- **Status:** ❌ LIKELY NOT SUPPORTED on CL837
- **SDK Evidence:**
  - Android SDK has `mManager.getHistoryOfRRRecord()` method (WearManager.java line 694)
  - Similar structure to HR history commands
- **Reason:** Device doesn't store RR history (same limitation as HR)
- **Alternative:** Real-time RR may be available in health data push notifications (cmd 0x02)
- **Note:** May work on other Chileaf models

### Why These Commands Exist in SDKs

The official SDKs support the **complete Chileaf protocol specification** for all device models:
- **CL831/CL833:** Entry-level models
- **CL837:** Mid-range (our tested device)
- **CL838/CL839/CL880N:** High-end models with more memory

**The CL837 is a subset implementation** - it only responds to commands its hardware can support. The SDK code is correct; it's the device firmware that selectively implements features based on available memory and target price point.

## 📊 Debug Output Analysis

When testing `hr_history.py`, the device only responded with:

| Command | Description | Frequency |
|---------|-------------|-----------|
| 0x0C | Accelerometer data | Continuous stream (majority of packets) |
| 0x38 | Unknown periodic data | Every ~15 seconds |
| 0x15 | Unknown periodic data | Every ~15 seconds |
| 0x75 | Unknown periodic data | Every ~15 seconds |

**No response to command 0x21** (HR records request) - device completely ignores it.

## 🔍 Device Behavior Patterns

### Real-Time vs Historical Data

The CL837 distinguishes between:

1. **Historical Data** (stored on device, downloadable):
   - Sleep records (5-minute intervals, days of history)
   - Sport summary (7-day history)
   - Step records (daily/hourly aggregates)

2. **Real-Time Data** (push notifications, NOT stored):
   - Heart Rate (via standard BLE service)
   - Accelerometer (continuous stream)
   - Sport/Health metrics (periodic broadcasts)
   - HRV (RR intervals from HR service)

### Memory Limitations

The CL837 appears to have limited storage:
- **Stores:** Sleep, sport summaries, step counts
- **Does NOT store:** Individual HR readings, RR measurements
- **Strategy:** Likely stores only aggregated/compressed data to save memory

## 📝 Recommendations

### For CL837 Users:

1. **Historical Analysis:** Use `sleep.py`, `sport_history.py`, `steps_history.py`
2. **Real-Time Monitoring:** Use `realtime_monitor.py` for live HR/activity/health data
3. **User Configuration:** Use `user_info.py` to set/get user profile
4. **Avoid:** `hr_history.py` and `rr_history.py` (won't work on CL837)

### For Other Chileaf Models:

- Higher-end models (CL838, CL839, etc.) may support HR/RR history
- Check WearManager.java in the Android SDK for model-specific features
- Test with `device_diagnostics.py` first to identify supported commands

## 🧪 Testing Checklist

- [x] sleep.py - Works perfectly (29 records)
- [x] sport_history.py - User confirmed working
- [x] steps_history.py - Interval command confirmed working
- [x] hr_history.py - Does NOT work (device limitation)
- [ ] rr_history.py - Likely won't work (not yet tested)
- [ ] user_info.py - Not yet tested
- [ ] realtime_monitor.py - Not yet tested (should work)

## 📱 Comparison to Android/iOS Apps

The official Android and iOS apps likely:
1. Use real-time HR service for live readings (BLE UUID 00002a37)
2. **Store readings locally** in the phone's database (SQLite on Android, CoreData on iOS)
3. Show "HR history" from **phone storage**, not device storage
4. Continuously sync and cache data while connected

**Evidence from SDKs:**
- Android app (HistoryActivity.java) calls `mManager.getHistoryOfHRRecord()`
- iOS SDK subscribes to real-time HR: `[peripheral setNotifyValue:YES forCharacteristic:characteristic]`
- **But on CL837, the HR history command returns nothing** - apps must rely on locally cached real-time data

**The device itself doesn't store HR history** - any historical HR data in the official apps is stored on the phone, not the CL837. The apps build the history by logging real-time readings over time.
