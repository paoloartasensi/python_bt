"""
CL837 HR + Sleep Data Correlation Analysis
Combines HR history with sleep data to validate sleep detection accuracy
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import ast

def load_and_prepare_data():
    """Load HR and sleep data, prepare for analysis"""
    # Load HR data
    hr_df = pd.read_csv('/Users/rtspla/VS_code/python_bt/python_bt/scripts/hr_history_20251222.csv')
    hr_df['datetime'] = pd.to_datetime(hr_df['datetime'])
    hr_df['timestamp'] = hr_df['datetime'].astype('int64') // 10**9  # Unix timestamp

    # Load sleep data
    sleep_df = pd.read_csv('/Users/rtspla/VS_code/python_bt/python_bt/sleep/raw_sleep_data_CL837-0758807_20251223_075441.csv')
    sleep_df['datetime_utc'] = pd.to_datetime(sleep_df['datetime_utc'])
    sleep_df['timestamp'] = sleep_df['datetime_utc'].astype('int64') // 10**9

    # Parse activity indices
    sleep_df['activity_indices'] = sleep_df['activity_indices'].apply(ast.literal_eval)

    return hr_df, sleep_df

def classify_sleep_state(hr_bpm, sleep_state, is_night=True):
    """
    Classify sleep state based on HR and sleep data
    Returns: 'sleep_confirmed', 'awake_confirmed', 'uncertain'
    """
    if pd.isna(hr_bpm):
        return 'no_hr_data'

    # During night hours (22:00-06:00), use HR as primary indicator
    if is_night:
        if hr_bpm < 70:
            return 'sleep_confirmed'
        elif hr_bpm > 80:
            return 'awake_confirmed'
        else:
            return 'uncertain'
    else:
        # During day, use combination of HR and sleep state
        if hr_bpm < 70 and sleep_state in ['deep', 'light']:
            return 'sleep_confirmed'
        elif hr_bpm > 80 and sleep_state == 'awake':
            return 'awake_confirmed'
        else:
            return 'uncertain'

def analyze_night_period(hr_df, sleep_df, night_date):
    """Analyze sleep for a specific night"""
    # Define night period (22:00 previous day to 06:00 current day)
    night_start = pd.Timestamp(f"{night_date} 22:00:00")
    night_end = pd.Timestamp(f"{night_date} 06:00:00") + pd.Timedelta(days=1)

    print(f"\n🌙 Analyzing night: {night_date}")
    print(f"   Period: {night_start} → {night_end}")

    # Filter data for night period
    hr_night = hr_df[(hr_df['datetime'] >= night_start) & (hr_df['datetime'] <= night_end)].copy()
    sleep_night = sleep_df[(sleep_df['datetime_utc'] >= night_start) & (sleep_df['datetime_utc'] <= night_end)].copy()

    print(f"   HR records: {len(hr_night)}")
    print(f"   Sleep records: {len(sleep_night)}")

    if len(hr_night) == 0 or len(sleep_night) == 0:
        print("   ❌ Insufficient data for analysis")
        return None

    # Analyze each sleep record
    results = []

    for _, sleep_row in sleep_night.iterrows():
        sleep_start = sleep_row['datetime_utc']
        sleep_end = sleep_start + pd.Timedelta(minutes=sleep_row['duration_minutes'])

        # Get HR data for this sleep period
        hr_period = hr_night[(hr_night['datetime'] >= sleep_start) & (hr_night['datetime'] <= sleep_end)]

        if len(hr_period) == 0:
            continue

        # Determine sleep state from activity indices
        activity_indices = sleep_row['activity_indices']
        deep_min = sleep_row['deep_sleep_min']
        light_min = sleep_row['light_sleep_min']
        awake_min = sleep_row['awake_min']

        # Classify overall sleep state
        if deep_min > light_min and deep_min > awake_min:
            sleep_state = 'deep'
        elif light_min > awake_min:
            sleep_state = 'light'
        else:
            sleep_state = 'awake'

        # Analyze HR during this period
        avg_hr = hr_period['hr_bpm'].mean()
        min_hr = hr_period['hr_bpm'].min()
        max_hr = hr_period['hr_bpm'].max()
        hr_std = hr_period['hr_bpm'].std()

        # Classify combined state
        classification = classify_sleep_state(avg_hr, sleep_state, is_night=True)

        results.append({
            'period_start': sleep_start,
            'period_end': sleep_end,
            'duration_min': sleep_row['duration_minutes'],
            'sleep_state': sleep_state,
            'avg_hr': avg_hr,
            'min_hr': min_hr,
            'max_hr': max_hr,
            'hr_std': hr_std,
            'classification': classification,
            'hr_records': len(hr_period)
        })

    return results

def analyze_day_period(hr_df, sleep_df, day_date):
    """Analyze sleep for a specific day (daytime)"""
    # Define day period (06:00 to 22:00)
    day_start = pd.Timestamp(f"{day_date} 06:00:00")
    day_end = pd.Timestamp(f"{day_date} 22:00:00")

    print(f"\n☀️  Analyzing day: {day_date}")
    print(f"   Period: {day_start} → {day_end}")

    # Filter data for day period
    hr_day = hr_df[(hr_df['datetime'] >= day_start) & (hr_df['datetime'] <= day_end)].copy()
    sleep_day = sleep_df[(sleep_df['datetime_utc'] >= day_start) & (sleep_df['datetime_utc'] <= day_end)].copy()

    print(f"   HR records: {len(hr_day)}")
    print(f"   Sleep records: {len(sleep_day)}")

    if len(hr_day) == 0:
        print("   ❌ No HR data for analysis")
        return None

    # Analyze HR patterns during day
    hr_stats = {
        'avg_hr': hr_day['hr_bpm'].mean(),
        'min_hr': hr_day['hr_bpm'].min(),
        'max_hr': hr_day['hr_bpm'].max(),
        'std_hr': hr_day['hr_bpm'].std(),
        'records': len(hr_day)
    }

    print(f"   HR: {hr_stats['avg_hr']:.1f} ± {hr_stats['std_hr']:.1f} BPM (min: {hr_stats['min_hr']}, max: {hr_stats['max_hr']})")

    return hr_stats

def main():
    print("=" * 70)
    print("CL837 HR + Sleep Data Correlation Analysis")
    print("=" * 70)

    # Load data
    print("\n📊 Loading data...")
    hr_df, sleep_df = load_and_prepare_data()

    print(f"HR data: {len(hr_df)} records from {hr_df['datetime'].min()} to {hr_df['datetime'].max()}")
    print(f"Sleep data: {len(sleep_df)} records from {sleep_df['datetime_utc'].min()} to {sleep_df['datetime_utc'].max()}")

    # Analyze recent nights and days
    recent_dates = ['2025-12-21', '2025-12-22']  # Dates we have data for

    all_results = []
    day_stats = []

    for date in recent_dates:
        # Analyze night
        night_results = analyze_night_period(hr_df, sleep_df, date)
        if night_results:
            all_results.extend(night_results)

        # Analyze day
        day_result = analyze_day_period(hr_df, sleep_df, date)
        if day_result:
            day_result['date'] = date
            day_stats.append(day_result)

    # Day vs Night HR Analysis
    if day_stats:
        print(f"\n🌅 DAY vs NIGHT HR COMPARISON")
        print("=" * 70)

        night_hr_data = [r['avg_hr'] for r in all_results if r['classification'] == 'sleep_confirmed']
        if night_hr_data:
            night_avg = np.mean(night_hr_data)
            print(f"Night sleep periods: {len(night_hr_data)} periods, avg HR: {night_avg:.1f} BPM")

        day_avg = np.mean([s['avg_hr'] for s in day_stats])
        print(f"Day periods: {len(day_stats)} periods, avg HR: {day_avg:.1f} BPM")

        if night_hr_data:
            hr_diff = day_avg - night_avg
            print(f"Day-Night HR difference: {hr_diff:.1f} BPM")

    # HR-only Sleep Detection Analysis
    print(f"\n🫀 HR-ONLY SLEEP DETECTION ANALYSIS")
    print("=" * 70)

    # Analyze all HR data for sleep detection potential
    hr_night_all = hr_df[hr_df['datetime'].dt.hour.isin([22,23,0,1,2,3,4,5])].copy()
    hr_day_all = hr_df[~hr_df['datetime'].dt.hour.isin([22,23,0,1,2,3,4,5])].copy()

    if len(hr_night_all) > 0 and len(hr_day_all) > 0:
        night_sleep_pct = (hr_night_all['hr_bpm'] < 70).mean() * 100
        day_awake_pct = (hr_day_all['hr_bpm'] > 70).mean() * 100

        print(f"Night periods (22:00-06:00): {len(hr_night_all)} records")
        print(f"  HR < 70 BPM (potential sleep): {night_sleep_pct:.1f}%")
        print(f"  Avg HR: {hr_night_all['hr_bpm'].mean():.1f} ± {hr_night_all['hr_bpm'].std():.1f} BPM")

        print(f"\nDay periods (06:00-22:00): {len(hr_day_all)} records")
        print(f"  HR > 70 BPM (potential awake): {day_awake_pct:.1f}%")
        print(f"  Avg HR: {hr_day_all['hr_bpm'].mean():.1f} ± {hr_day_all['hr_bpm'].std():.1f} BPM")

        # Calculate detection accuracy
        total_night = len(hr_night_all)
        true_positives = (hr_night_all['hr_bpm'] < 70).sum()  # Correctly identified sleep
        false_positives = (hr_day_all['hr_bpm'] < 70).sum()   # Incorrectly identified sleep during day

        if total_night > 0:
            sensitivity = true_positives / total_night * 100  # % of actual sleep periods detected
            specificity = (len(hr_day_all) - false_positives) / len(hr_day_all) * 100  # % of awake periods correctly identified

            print(f"\n🎯 Detection Performance:")
            print(f"  Sensitivity (sleep detection): {sensitivity:.1f}%")
            print(f"  Specificity (awake detection): {specificity:.1f}%")
            print(f"  Overall accuracy: {(sensitivity + specificity) / 2:.1f}%")

if __name__ == "__main__":
    main()