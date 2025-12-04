#!/usr/bin/env python3
"""
Sleep Data Visualization - CL837 Fitness Tracker
Genera grafici matplotlib dell'andamento del sonno

Funzionalità principali:
- Grafici a torta per ogni notte con fasi del sonno
- Orario di addormentamento e sveglia per ogni notte
- Durata totale ed efficienza del sonno
- Classificazione fasi basata su SDK Chileaf (activity_indices)

Logica di aggregazione:
- Notte = tutto il sonno tra 18:00 giorno X e 18:00 giorno X+1
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import ast
import sys
import os
from pathlib import Path


def classify_sleep_phases_sdk(activity_indices: list) -> dict:
    """
    Classifica le fasi del sonno usando la logica dell'SDK Chileaf.
    
    Regole (da HistorySleepActivity.java):
    - action > 20: Not Sleeping (sveglio/movimento)
    - action 1-20: Light Sleep
    - action == 0: Accumulato, poi:
        - ≥3 zeri consecutivi → Deep Sleep
        - <3 zeri consecutivi → Light Sleep
    
    Ogni intervallo = 5 minuti
    
    Returns: dict con minuti per fase
    """
    deep_min = 0
    light_min = 0
    awake_min = 0
    
    consecutive_zeros = 0
    zero_start_idx = -1
    
    for i, action in enumerate(activity_indices):
        if action == 0:
            if consecutive_zeros == 0:
                zero_start_idx = i
            consecutive_zeros += 1
        else:
            # Fine sequenza di zeri - classifica
            if consecutive_zeros >= 3:
                deep_min += consecutive_zeros * 5
            elif consecutive_zeros > 0:
                light_min += consecutive_zeros * 5
            
            consecutive_zeros = 0
            
            # Classifica azione corrente
            if action > 20:
                awake_min += 5
            else:  # 1-20
                light_min += 5
    
    # Fine array - gestisci zeri rimasti
    if consecutive_zeros >= 3:
        deep_min += consecutive_zeros * 5
    elif consecutive_zeros > 0:
        light_min += consecutive_zeros * 5
    
    return {
        'deep_min': deep_min,
        'light_min': light_min,
        'awake_min': awake_min,
        'total_min': deep_min + light_min + awake_min
    }


def load_sleep_data(csv_path: str) -> pd.DataFrame:
    """Carica i dati del sonno dal CSV e ricalcola le fasi con logica SDK"""
    df = pd.read_csv(csv_path)
    df['datetime_utc'] = pd.to_datetime(df['datetime_utc'], format='%Y-%m-%d %H:%M:%S')
    df['date'] = df['datetime_utc'].dt.date
    
    # Calcola "sleep_night" - la notte di appartenenza
    # Logica: tutto il sonno tra 18:00 giorno X e 18:00 giorno X+1 appartiene alla "notte del giorno X"
    # Es: sonno alle 23:00 del 2/12 e alle 02:00 del 3/12 = "notte del 2/12"
    df['sleep_night'] = df['datetime_utc'].apply(lambda x: 
        (x - timedelta(hours=18)).date() if x.hour < 18 else x.date()
    )
    
    # Ricalcola le fasi usando la logica SDK
    sdk_phases = []
    for _, row in df.iterrows():
        try:
            activities = ast.literal_eval(row['activity_indices'])
            phases = classify_sleep_phases_sdk(activities)
            sdk_phases.append(phases)
        except:
            sdk_phases.append({'deep_min': 0, 'light_min': 0, 'awake_min': 0, 'total_min': 0})
    
    phases_df = pd.DataFrame(sdk_phases)
    df['deep_sleep_sdk'] = phases_df['deep_min']
    df['light_sleep_sdk'] = phases_df['light_min']
    df['awake_sdk'] = phases_df['awake_min']
    
    return df


def get_night_label(night_date) -> str:
    """Genera etichetta per la notte (es: 'Night 2→3 Dec')"""
    next_day = night_date + timedelta(days=1)
    return f"{night_date.strftime('%d')}→{next_day.strftime('%d %b')}"


def format_duration(minutes: int) -> str:
    """Formatta durata in ore e minuti"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def plot_night_pies(df: pd.DataFrame, output_path: str = None):
    """
    Genera grafici a torta per ogni notte con:
    - Fasi del sonno (Deep, Light, Awake)
    - Orario di addormentamento e sveglia
    - Durata totale ed efficienza
    """
    # Aggrega per notte
    nights_data = []
    
    for night_date in sorted(df['sleep_night'].unique()):
        night_df = df[df['sleep_night'] == night_date].sort_values('datetime_utc')
        
        if len(night_df) == 0:
            continue
        
        # Calcola totali per la notte
        deep = night_df['deep_sleep_sdk'].sum()
        light = night_df['light_sleep_sdk'].sum()
        awake = night_df['awake_sdk'].sum()
        total = deep + light + awake
        
        if total == 0:
            continue
        
        # Orari di addormentamento e sveglia
        bedtime = night_df['datetime_utc'].min()
        # Calcola wake time: ultimo record + sua durata
        last_record = night_df.iloc[-1]
        wake_time = last_record['datetime_utc'] + timedelta(minutes=int(last_record['duration_minutes']))
        
        # Efficienza del sonno
        sleep_time = deep + light
        efficiency = (sleep_time / total * 100) if total > 0 else 0
        
        nights_data.append({
            'night_date': night_date,
            'label': get_night_label(night_date),
            'deep': int(deep),
            'light': int(light),
            'awake': int(awake),
            'total': int(total),
            'bedtime': bedtime,
            'wake_time': wake_time,
            'efficiency': efficiency
        })
    
    if not nights_data:
        print("No valid night data to plot")
        return None, None
    
    # Determina layout griglia
    n_nights = len(nights_data)
    cols = min(3, n_nights)
    rows = (n_nights + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 6 * rows))
    fig.suptitle('Sleep Analysis by Night', fontsize=16, fontweight='bold', y=1.02)
    
    # Flatten axes per iterazione facile
    if n_nights == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
    
    # Colori
    colors = ['#1a237e', '#42a5f5', '#ff7043']  # Deep, Light, Awake
    
    for idx, night in enumerate(nights_data):
        ax = axes[idx]
        
        # Dati per la torta
        sizes = [night['deep'], night['light'], night['awake']]
        labels_pie = ['Deep', 'Light', 'Awake']
        
        # Rimuovi fette con 0
        non_zero = [(s, l, c) for s, l, c in zip(sizes, labels_pie, colors) if s > 0]
        if non_zero:
            sizes, labels_pie, pie_colors = zip(*non_zero)
        else:
            continue
        
        # Grafico a torta
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=None,  # Mettiamo le label nella legenda
            autopct=lambda pct: f'{pct:.0f}%' if pct > 5 else '',
            colors=pie_colors,
            startangle=90,
            explode=[0.02] * len(sizes),
            shadow=True,
            textprops={'fontsize': 10, 'fontweight': 'bold', 'color': 'white'}
        )
        
        # Titolo con data notte
        ax.set_title(f"Night {night['label']}", fontsize=14, fontweight='bold', pad=10)
        
        # Legenda con durate
        legend_labels = []
        for label, size in zip(labels_pie, sizes):
            legend_labels.append(f"{label}: {format_duration(size)}")
        
        ax.legend(wedges, legend_labels, loc='upper left', fontsize=9)
        
        # Info sotto il grafico
        info_text = (
            f"Bedtime: {night['bedtime'].strftime('%H:%M')}\n"
            f"Wake: {night['wake_time'].strftime('%H:%M')}\n"
            f"Total: {format_duration(night['total'])}\n"
            f"Efficiency: {night['efficiency']:.0f}%"
        )
        
        ax.text(0.5, -0.15, info_text, transform=ax.transAxes, 
                fontsize=10, ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.3))
    
    # Nascondi assi vuoti
    for idx in range(n_nights, len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    return fig, axes

def plot_sleep_summary_table(df: pd.DataFrame, output_path: str = None):
    """
    Tabella riassuntiva testuale di tutte le notti
    """
    # Aggrega per notte
    nights_data = []
    
    for night_date in sorted(df['sleep_night'].unique()):
        night_df = df[df['sleep_night'] == night_date].sort_values('datetime_utc')
        
        if len(night_df) == 0:
            continue
        
        deep = night_df['deep_sleep_sdk'].sum()
        light = night_df['light_sleep_sdk'].sum()
        awake = night_df['awake_sdk'].sum()
        total = deep + light + awake
        
        if total == 0:
            continue
        
        bedtime = night_df['datetime_utc'].min()
        last_record = night_df.iloc[-1]
        wake_time = last_record['datetime_utc'] + timedelta(minutes=int(last_record['duration_minutes']))
        
        sleep_time = deep + light
        efficiency = (sleep_time / total * 100) if total > 0 else 0
        
        nights_data.append({
            'Night': get_night_label(night_date),
            'Bedtime': bedtime.strftime('%H:%M'),
            'Wake': wake_time.strftime('%H:%M'),
            'Total': format_duration(int(total)),
            'Deep': format_duration(int(deep)),
            'Light': format_duration(int(light)),
            'Awake': format_duration(int(awake)),
            'Eff%': f"{efficiency:.0f}%"
        })
    
    if not nights_data:
        print("No night data for summary")
        return
    
    # Stampa tabella
    print("\n" + "="*80)
    print("SLEEP SUMMARY BY NIGHT")
    print("="*80)
    
    # Header
    print(f"{'Night':<15} {'Bedtime':<8} {'Wake':<8} {'Total':<10} {'Deep':<10} {'Light':<10} {'Awake':<8} {'Eff%':<6}")
    print("-"*80)
    
    for night in nights_data:
        print(f"{night['Night']:<15} {night['Bedtime']:<8} {night['Wake']:<8} {night['Total']:<10} {night['Deep']:<10} {night['Light']:<10} {night['Awake']:<8} {night['Eff%']:<6}")
    
    print("="*80)


def plot_sleep_quality_timeline(df: pd.DataFrame, output_path: str = None):
    """
    Timeline del sonno con qualità (% deep sleep) - usando logica SDK
    """
    fig, ax = plt.subplots(figsize=(14, 5))
    
    # Usa i dati ricalcolati con logica SDK
    df['total_sleep'] = df['deep_sleep_sdk'] + df['light_sleep_sdk']
    df['deep_pct'] = np.where(df['total_sleep'] > 0, 
                               df['deep_sleep_sdk'] / df['total_sleep'] * 100, 0)
    
    # Colore basato sulla qualità
    colors = plt.cm.RdYlGn(df['deep_pct'] / 100)
    
    scatter = ax.scatter(df['datetime_utc'], df['deep_pct'], 
                        c=df['deep_pct'], cmap='RdYlGn', 
                        s=df['duration_minutes'] * 3, alpha=0.7,
                        edgecolors='black', linewidth=0.5)
    
    # Linea di trend
    ax.plot(df['datetime_utc'], df['deep_pct'], '--', alpha=0.3, color='gray')
    
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Deep Sleep %', fontsize=11)
    ax.set_title('Sleep Quality Over Time (SDK logic, bubble size = duration)', fontsize=14, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Deep Sleep %')
    
    # Linea soglia qualità
    ax.axhline(y=50, color='green', linestyle=':', alpha=0.5, label='Good quality threshold')
    ax.axhline(y=25, color='orange', linestyle=':', alpha=0.5, label='Poor quality threshold')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.xticks(rotation=45)
    
    ax.set_ylim(-5, 105)
    ax.grid(alpha=0.3)
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    return fig, ax

def plot_daily_summary(df: pd.DataFrame, output_path: str = None):
    """
    Sommario per NOTTE di sonno (non per giorno solare)
    Una notte = sonno tra 18:00 giorno X e 18:00 giorno X+1
    Usa classificazione fasi SDK (basata su consecutività zeri)
    """
    # Aggrega per NOTTE usando dati SDK
    nightly = df.groupby('sleep_night').agg({
        'deep_sleep_sdk': 'sum',
        'light_sleep_sdk': 'sum',
        'awake_sdk': 'sum',
        'duration_minutes': 'sum'
    }).reset_index()
    
    nightly['sleep_night'] = pd.to_datetime(nightly['sleep_night'])
    nightly['total_hours'] = nightly['duration_minutes'] / 60
    nightly['night_label'] = nightly['sleep_night'].apply(
        lambda x: f"{x.strftime('%d')}→{(x + timedelta(days=1)).strftime('%d %b')}"
    )
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Grafico 1: Durata totale sonno per NOTTE
    ax1 = axes[0]
    x_pos = range(len(nightly))
    bars = ax1.bar(x_pos, nightly['total_hours'], color='#5c6bc0', alpha=0.8, edgecolor='black')
    ax1.axhline(y=7, color='green', linestyle='--', alpha=0.7, label='Recommended (7h)')
    ax1.axhline(y=8, color='green', linestyle='--', alpha=0.3)
    ax1.set_ylabel('Total Sleep (hours)', fontsize=11)
    ax1.set_title('Sleep Duration per Night (18:00→18:00)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, max(nightly['total_hours']) + 1)
    
    # Etichette sui bar
    for bar, hours in zip(bars, nightly['total_hours']):
        if hours > 0:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{hours:.1f}h', ha='center', va='bottom', fontsize=9)
    
    # Grafico 2: Composizione sonno (stacked) - usando dati SDK
    ax2 = axes[1]
    ax2.bar(x_pos, nightly['deep_sleep_sdk']/60, label='Deep', color='#1a237e', alpha=0.9)
    ax2.bar(x_pos, nightly['light_sleep_sdk']/60, bottom=nightly['deep_sleep_sdk']/60,
            label='Light', color='#42a5f5', alpha=0.9)
    ax2.bar(x_pos, nightly['awake_sdk']/60, 
            bottom=(nightly['deep_sleep_sdk'] + nightly['light_sleep_sdk'])/60,
            label='Awake', color='#ff7043', alpha=0.9)
    
    ax2.set_xlabel('Night', fontsize=11)
    ax2.set_ylabel('Hours', fontsize=11)
    ax2.set_title('Sleep Composition by Night (SDK classification)', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(axis='y', alpha=0.3)
    
    # X labels con notti
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(nightly['night_label'], rotation=45, ha='right')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(nightly['night_label'], rotation=45, ha='right')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    return fig, axes

def plot_activity_heatmap(df: pd.DataFrame, output_path: str = None):
    """
    Heatmap dell'attività durante il sonno (activity_indices)
    """
    # Parsa gli activity indices
    all_activities = []
    timestamps = []
    
    for idx, row in df.iterrows():
        try:
            activities = ast.literal_eval(row['activity_indices'])
            start_time = row['datetime_utc']
            interval_min = row['duration_minutes'] / len(activities) if len(activities) > 0 else 5
            
            for i, act in enumerate(activities):
                timestamps.append(start_time + timedelta(minutes=i * interval_min))
                all_activities.append(act)
        except:
            pass
    
    if not all_activities:
        print("No activity data to plot")
        return None, None
    
    fig, ax = plt.subplots(figsize=(14, 4))
    
    # Crea il grafico ad area
    ax.fill_between(range(len(all_activities)), all_activities, alpha=0.6, color='#7e57c2')
    ax.plot(range(len(all_activities)), all_activities, color='#4527a0', linewidth=0.5)
    
    ax.set_xlabel('Time Intervals (5 min each)', fontsize=11)
    ax.set_ylabel('Activity Index', fontsize=11)
    ax.set_title('Sleep Activity/Movement Over Time', fontsize=14, fontweight='bold')
    
    # Evidenzia zone di alta attività
    threshold = np.mean(all_activities) + np.std(all_activities)
    ax.axhline(y=threshold, color='red', linestyle='--', alpha=0.5, 
               label=f'High activity threshold ({threshold:.1f})')
    
    ax.grid(alpha=0.3)
    ax.legend()
    ax.set_ylim(0, max(all_activities) + 2)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    return fig, ax

def plot_sleep_hypnogram(df: pd.DataFrame, night_date: str = None, output_path: str = None):
    """
    Ipnogramma: grafico classico delle fasi del sonno
    """
    if night_date:
        # Filtra per una notte specifica
        df_night = df[df['date'] == pd.to_datetime(night_date).date()]
    else:
        # Prendi l'ultima notte con dati sufficienti
        dates_with_data = df.groupby('date')['duration_minutes'].sum()
        dates_with_data = dates_with_data[dates_with_data > 60]
        if len(dates_with_data) == 0:
            print("Not enough data for hypnogram")
            return None, None
        night_date = dates_with_data.index[-1]
        df_night = df[df['date'] == night_date]
    
    if len(df_night) == 0:
        print(f"No data for {night_date}")
        return None, None
    
    fig, ax = plt.subplots(figsize=(14, 4))
    
    # Costruisci ipnogramma
    times = []
    stages = []  # 0=Awake, 1=Light, 2=Deep
    
    for idx, row in df_night.iterrows():
        try:
            activities = ast.literal_eval(row['activity_indices'])
            start_time = row['datetime_utc']
            interval_min = row['duration_minutes'] / len(activities) if len(activities) > 0 else 5
            
            # Determina la fase del sonno basandosi sull'attività
            for i, act in enumerate(activities):
                t = start_time + timedelta(minutes=i * interval_min)
                times.append(t)
                
                # Euristica: alta attività = awake/light, bassa = deep
                if act > 10:
                    stages.append(0)  # Awake
                elif act > 3:
                    stages.append(1)  # Light
                else:
                    stages.append(2)  # Deep
        except:
            pass
    
    if not times:
        print("No detailed data for hypnogram")
        return None, None
    
    # Plot
    ax.step(times, stages, where='post', linewidth=2, color='#5c6bc0')
    ax.fill_between(times, stages, step='post', alpha=0.3, color='#7986cb')
    
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(['Awake', 'Light', 'Deep'])
    ax.set_ylim(-0.5, 2.5)
    ax.invert_yaxis()  # Deep sleep in basso come negli ipnogrammi standard
    
    ax.set_xlabel('Time', fontsize=11)
    ax.set_title(f'Sleep Hypnogram - {night_date}', fontsize=14, fontweight='bold')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    return fig, ax

def main():
    # Trova il CSV più recente
    sleep_dir = Path(__file__).parent
    csv_files = list(sleep_dir.glob("sleep_data_*.csv"))
    
    if not csv_files:
        print("No sleep CSV files found!")
        sys.exit(1)
    
    csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading: {csv_path}")
    
    df = load_sleep_data(str(csv_path))
    print(f"Loaded {len(df)} sleep records")
    print(f"Date range: {df['datetime_utc'].min()} to {df['datetime_utc'].max()}")
    
    # Mostra tabella riassuntiva
    plot_sleep_summary_table(df)
    
    # Genera tutti i grafici
    output_dir = sleep_dir / "plots"
    output_dir.mkdir(exist_ok=True)
    
    print("\n📊 Generating sleep charts...")
    
    # 1. PRINCIPALE: Grafici a torta per notte
    plot_night_pies(df, str(output_dir / "night_pies.png"))
    
    # 2. Sommario giornaliero (bar chart)
    plot_daily_summary(df, str(output_dir / "daily_summary.png"))
    
    # 3. Qualità nel tempo
    plot_sleep_quality_timeline(df, str(output_dir / "sleep_quality_timeline.png"))
    
    # 4. Attività durante il sonno
    plot_activity_heatmap(df, str(output_dir / "activity_heatmap.png"))
    
    # 5. Ipnogramma ultima notte
    plot_sleep_hypnogram(df, output_path=str(output_dir / "hypnogram.png"))
    
    print(f"\n✅ All charts saved to: {output_dir}")
    
    # Mostra i grafici
    plt.show()

if __name__ == "__main__":
    main()
