"""
Real Sleep Analysis - Ricostruzione intelligente delle notti di sonno
=====================================================================

Questo script:
1. Legge i dati raw frammentati dal device
2. Aggrega i record in sessioni di sonno notturno
3. Rimuove duplicati e gestisce sovrapposizioni
4. Calcola statistiche reali per ogni notte
5. Distingue sonno notturno da pisolini diurni

Logica di aggregazione:
- Una "notte" va dalle 20:00 alle 12:00 del giorno dopo
- Record entro 30 minuti l'uno dall'altro = stessa sessione
- Record duplicati (stesso timestamp ±2min) vengono uniti
"""

import csv
import ast
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional, Tuple


class SleepRecord:
    """Singolo record di sonno dal device"""
    
    def __init__(self, row: dict):
        self.record_number = int(row['record_number'])
        self.utc = int(row['utc_timestamp'])
        self.datetime = datetime.fromisoformat(row['datetime_utc'])
        self.duration = int(row['duration_minutes'])
        self.deep = int(row['deep_sleep_min'])
        self.light = int(row['light_sleep_min'])
        self.awake = int(row['awake_min'])
        self.intervals = ast.literal_eval(row['activity_indices'])
        
        # Calcola end time
        self.end_datetime = self.datetime + timedelta(minutes=self.duration)
    
    def __repr__(self):
        return f"Record({self.datetime.strftime('%m/%d %H:%M')}, {self.duration}min)"
    
    def overlaps_with(self, other: 'SleepRecord', tolerance_min: int = 2) -> bool:
        """Verifica se due record si sovrappongono (possibili duplicati)"""
        time_diff = abs((self.datetime - other.datetime).total_seconds() / 60)
        return time_diff <= tolerance_min


class SleepSession:
    """Sessione di sonno aggregata (es. una notte intera)"""
    
    def __init__(self):
        self.records: List[SleepRecord] = []
        self.start: Optional[datetime] = None
        self.end: Optional[datetime] = None
        self.deep_min = 0
        self.light_min = 0
        self.awake_min = 0
        self.total_min = 0
        self.gaps_min = 0  # Tempo tra record (risvegli non tracciati)
        self.all_intervals: List[int] = []
    
    def add_record(self, record: SleepRecord):
        """Aggiunge un record alla sessione"""
        # Controlla duplicati
        for existing in self.records:
            if existing.overlaps_with(record):
                # Duplicato - prendi quello con più dati
                if record.duration > existing.duration:
                    self.records.remove(existing)
                    break
                else:
                    return  # Ignora questo record
        
        self.records.append(record)
        self._recalculate()
    
    def _recalculate(self):
        """Ricalcola statistiche della sessione"""
        if not self.records:
            return
        
        # Ordina per timestamp
        self.records.sort(key=lambda r: r.datetime)
        
        self.start = self.records[0].datetime
        self.end = self.records[-1].end_datetime
        
        # Calcola tempo effettivo a letto PRIMA (serve per scalare deep/light)
        # usando merge intervals per gestire sovrapposizioni
        intervals = [(r.datetime, r.end_datetime, r) for r in self.records]
        intervals.sort(key=lambda x: x[0])
        
        # Merge overlapping intervals e raccogli dati proporzionalmente
        self._actual_time_in_bed = 0
        self.gaps_min = 0
        self.deep_min = 0
        self.light_min = 0
        self.awake_min = 0
        
        merged_ranges = []
        current_start, current_end = intervals[0][0], intervals[0][1]
        current_records = [intervals[0][2]]
        
        for start, end, rec in intervals[1:]:
            if start <= current_end:  # Sovrapposizione o contiguo
                current_end = max(current_end, end)
                current_records.append(rec)
            else:  # Gap - nuova sezione
                # Salva sezione precedente
                merged_ranges.append((current_start, current_end, current_records))
                gap = (start - current_end).total_seconds() / 60
                self.gaps_min += gap
                # Inizia nuova sezione
                current_start, current_end = start, end
                current_records = [rec]
        
        # Ultima sezione
        merged_ranges.append((current_start, current_end, current_records))
        
        # Calcola tempo effettivo e proporziona deep/light/awake
        for range_start, range_end, recs in merged_ranges:
            range_min = (range_end - range_start).total_seconds() / 60
            self._actual_time_in_bed += range_min
            
            # Se un solo record, usa i suoi valori direttamente
            if len(recs) == 1:
                self.deep_min += recs[0].deep
                self.light_min += recs[0].light
                self.awake_min += recs[0].awake
            else:
                # Più record sovrapposti: media pesata per durata
                total_dur = sum(r.duration for r in recs)
                if total_dur > 0:
                    deep_ratio = sum(r.deep for r in recs) / total_dur
                    light_ratio = sum(r.light for r in recs) / total_dur
                    awake_ratio = sum(r.awake for r in recs) / total_dur
                    self.deep_min += range_min * deep_ratio
                    self.light_min += range_min * light_ratio
                    self.awake_min += range_min * awake_ratio
        
        # Arrotonda
        self.deep_min = round(self.deep_min)
        self.light_min = round(self.light_min)
        self.awake_min = round(self.awake_min)
        
        # Total = tempo effettivo dormito (non somma durate)
        self.total_min = self.deep_min + self.light_min + self.awake_min
        
        # Unisci tutti gli intervalli
        self.all_intervals = []
        for r in self.records:
            self.all_intervals.extend(r.intervals)
    
    @property
    def time_in_bed(self) -> float:
        """Tempo totale a letto (senza contare sovrapposizioni)"""
        return self._actual_time_in_bed if hasattr(self, '_actual_time_in_bed') else 0
    
    @property
    def efficiency(self) -> float:
        """Efficienza del sonno (tempo dormito / tempo a letto)"""
        if self.time_in_bed > 0:
            return (self.total_min / self.time_in_bed) * 100
        return 0
    
    @property
    def deep_percentage(self) -> float:
        """Percentuale sonno profondo"""
        if self.total_min > 0:
            return (self.deep_min / self.total_min) * 100
        return 0
    
    @property
    def avg_activity(self) -> float:
        """Media degli indici di attività"""
        if self.all_intervals:
            return sum(self.all_intervals) / len(self.all_intervals)
        return 0
    
    def get_night_label(self) -> str:
        """Etichetta della notte (es. '14→15 Dic')"""
        if not self.start:
            return "Unknown"
        
        # Se inizia dopo le 20:00, è la notte che va al giorno dopo
        if self.start.hour >= 20:
            next_day = self.start + timedelta(days=1)
            return f"{self.start.day:02d}→{next_day.day:02d} {self.start.strftime('%b')}"
        else:
            prev_day = self.start - timedelta(days=1)
            return f"{prev_day.day:02d}→{self.start.day:02d} {self.start.strftime('%b')}"
    
    def is_nap(self) -> bool:
        """Verifica se è un pisolino diurno (non sonno notturno)"""
        if not self.start:
            return True
        hour = self.start.hour
        # Pisolino se:
        # - inizia tra 10:00-19:00 E dura meno di 3 ore
        # - oppure inizia mattina presto (8-10) e dura poco
        if 10 <= hour < 19 and self.total_min < 180:
            return True
        if 8 <= hour < 10 and self.total_min < 90:
            return True
        return False


class SleepAnalyzer:
    """Analizzatore intelligente del sonno"""
    
    def __init__(self):
        self.records: List[SleepRecord] = []
        self.night_sessions: List[SleepSession] = []
        self.naps: List[SleepSession] = []
    
    def load_csv(self, filepath: str):
        """Carica dati da CSV"""
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    self.records.append(SleepRecord(row))
                except Exception as e:
                    print(f"Error parsing row: {e}")
        
        print(f"✓ Loaded {len(self.records)} raw records")
        self.records.sort(key=lambda r: r.datetime)
    
    def _get_night_key(self, dt: datetime) -> str:
        """Genera chiave per raggruppare per notte"""
        # La "notte" appartiene al giorno in cui ci si sveglia
        # Es: 23:00 del 14/12 → notte del 15/12
        # Es: 02:00 del 15/12 → notte del 15/12
        if dt.hour >= 20:
            wake_date = dt.date() + timedelta(days=1)
        else:
            wake_date = dt.date()
        return wake_date.isoformat()
    
    def aggregate_sessions(self, gap_threshold_min: int = 60):
        """
        Aggrega i record in sessioni di sonno.
        
        gap_threshold_min: se c'è un gap > di questo valore, 
                          considera una nuova sessione
        """
        if not self.records:
            return
        
        # Raggruppa per notte
        nights: Dict[str, List[SleepRecord]] = defaultdict(list)
        
        for record in self.records:
            night_key = self._get_night_key(record.datetime)
            nights[night_key].append(record)
        
        # Processa ogni notte - prima raccogli tutte le sessioni
        all_sessions = []
        
        for night_key in sorted(nights.keys()):
            night_records = sorted(nights[night_key], key=lambda r: r.datetime)
            
            # Separa in sessioni basate sui gap
            current_session = SleepSession()
            
            for record in night_records:
                if current_session.records:
                    last_end = current_session.records[-1].end_datetime
                    gap = (record.datetime - last_end).total_seconds() / 60
                    
                    # Se gap troppo grande, nuova sessione
                    if gap > gap_threshold_min:
                        # Salva sessione corrente
                        if current_session.total_min >= 15:
                            all_sessions.append(current_session)
                        current_session = SleepSession()
                
                current_session.add_record(record)
            
            # Salva ultima sessione
            if current_session.total_min >= 15:
                all_sessions.append(current_session)
        
        # Ordina tutte le sessioni per timestamp
        all_sessions.sort(key=lambda s: s.start)
        
        # Merge sessioni consecutive della stessa notte
        # (es. 19:00-20:00 gap di 30min poi 20:30-07:00 = una notte)
        merged_sessions = []
        i = 0
        while i < len(all_sessions):
            current = all_sessions[i]
            
            # Guarda avanti per merge
            while i + 1 < len(all_sessions):
                next_session = all_sessions[i + 1]
                gap = (next_session.start - current.end).total_seconds() / 60
                
                # Merge se: gap < 2 ore E entrambe nella stessa "notte logica"
                # (cioè non merge sessione delle 10:00 con quella delle 20:00)
                same_night = (
                    (current.start.hour >= 19 and next_session.start.hour < 12) or
                    (current.start.hour < 12 and next_session.start.hour < 12)
                )
                
                if gap <= 120 and same_night:
                    # Merge: aggiungi tutti i record della prossima sessione
                    for rec in next_session.records:
                        current.add_record(rec)
                    i += 1
                else:
                    break
            
            merged_sessions.append(current)
            i += 1
        
        # Classifica: notte se >= 3 ore e inizia sera/notte
        # Oppure se inizia >= 20:00 (potrebbe essere notte in corso)
        for session in merged_sessions:
            starts_evening = session.start.hour >= 20
            long_enough = session.total_min >= 180  # >= 3 ore
            night_hours = session.start.hour >= 19 or session.start.hour < 10
            
            is_night = (long_enough and night_hours) or starts_evening
            
            if is_night:
                self.night_sessions.append(session)
            elif session.total_min >= 15:
                self.naps.append(session)
        
        print(f"✓ Aggregated into {len(self.night_sessions)} night sessions + {len(self.naps)} naps")
    
    def print_summary(self):
        """Stampa riepilogo delle notti"""
        print("\n" + "=" * 80)
        print("🌙 ANALISI SONNO NOTTURNO")
        print("=" * 80)
        
        if not self.night_sessions:
            print("Nessuna sessione notturna trovata.")
            return
        
        # Header tabella
        print(f"\n{'Notte':<12} {'Letto':<12} {'Dormito':<12} {'Deep':<12} "
              f"{'Light':<12} {'Awake':<10} {'Eff%':<6} {'Deep%':<6}")
        print("-" * 80)
        
        total_deep = 0
        total_light = 0
        total_awake = 0
        total_time = 0
        
        for session in self.night_sessions:
            label = session.get_night_label()
            bed_h = session.time_in_bed / 60
            sleep_h = session.total_min / 60
            deep_h = session.deep_min / 60
            light_h = session.light_min / 60
            awake_h = session.awake_min / 60
            
            bed_time = f"{session.time_in_bed:.0f}m ({bed_h:.1f}h)"
            sleep_time = f"{session.total_min:.0f}m ({sleep_h:.1f}h)"
            deep = f"{session.deep_min:.0f}m ({deep_h:.1f}h)"
            light = f"{session.light_min:.0f}m ({light_h:.1f}h)"
            awake = f"{session.awake_min:.0f}m ({awake_h:.1f}h)"
            eff = f"{session.efficiency:.0f}%"
            deep_pct = f"{session.deep_percentage:.0f}%"
            
            print(f"{label:<12} {bed_time:<12} {sleep_time:<12} {deep:<12} "
                  f"{light:<12} {awake:<10} {eff:<6} {deep_pct:<6}")
            
            total_deep += session.deep_min
            total_light += session.light_min
            total_awake += session.awake_min
            total_time += session.total_min
        
        # Statistiche generali
        print("-" * 80)
        avg_sleep = total_time / len(self.night_sessions) if self.night_sessions else 0
        avg_deep_pct = (total_deep / total_time * 100) if total_time > 0 else 0
        
        print(f"\n📊 STATISTICHE GENERALI ({len(self.night_sessions)} notti analizzate)")
        print(f"   Media sonno/notte:     {avg_sleep:.0f} min ({avg_sleep/60:.1f} ore)")
        print(f"   Media sonno profondo:  {avg_deep_pct:.0f}%")
        print(f"   Totale deep sleep:     {total_deep} min ({total_deep/60:.1f} ore)")
        print(f"   Totale light sleep:    {total_light} min ({total_light/60:.1f} ore)")
    
    def print_detailed(self):
        """Stampa dettaglio per ogni notte"""
        print("\n" + "=" * 80)
        print("📋 DETTAGLIO NOTTI")
        print("=" * 80)
        
        for i, session in enumerate(self.night_sessions, 1):
            print(f"\n🌙 Notte {i}: {session.get_night_label()}")
            print(f"   Inizio:      {session.start.strftime('%H:%M')} "
                  f"({session.start.strftime('%d/%m/%Y')})")
            print(f"   Fine:        {session.end.strftime('%H:%M')} "
                  f"({session.end.strftime('%d/%m/%Y')})")
            print(f"   A letto:     {session.time_in_bed:.0f} min "
                  f"({session.time_in_bed/60:.1f} ore)")
            print(f"   Dormito:     {session.total_min} min "
                  f"({session.total_min/60:.1f} ore)")
            print(f"   Deep:        {session.deep_min} min "
                  f"({session.deep_percentage:.0f}%)")
            print(f"   Light:       {session.light_min} min")
            print(f"   Awake:       {session.awake_min} min")
            print(f"   Gaps:        {session.gaps_min:.0f} min "
                  "(risvegli non tracciati)")
            print(f"   Efficienza:  {session.efficiency:.0f}%")
            print(f"   Records:     {len(session.records)} frammenti aggregati")
            print(f"   Mov. medio:  {session.avg_activity:.1f}")
            
            # Valutazione
            quality = self._evaluate_night(session)
            print(f"   Qualità:     {quality}")
    
    def print_naps(self):
        """Stampa pisolini rilevati"""
        if not self.naps:
            return
        
        print("\n" + "=" * 80)
        print("😴 PISOLINI DIURNI")
        print("=" * 80)
        
        for nap in self.naps:
            print(f"   {nap.start.strftime('%d/%m %H:%M')} - "
                  f"{nap.total_min} min (Deep: {nap.deep_min}m, Light: {nap.light_min}m)")
    
    def _evaluate_night(self, session: SleepSession) -> str:
        """Valuta la qualità della notte"""
        score = 0
        notes = []
        
        # Durata (ideale 7-9 ore)
        hours = session.total_min / 60
        if 7 <= hours <= 9:
            score += 3
            notes.append("durata ottimale")
        elif 6 <= hours < 7 or 9 < hours <= 10:
            score += 2
            notes.append("durata ok")
        elif hours < 6:
            score += 0
            notes.append("troppo breve")
        else:
            score += 1
            notes.append("troppo lunga")
        
        # Deep sleep (ideale 15-25%)
        deep_pct = session.deep_percentage
        if 15 <= deep_pct <= 30:
            score += 3
            notes.append("deep ok")
        elif 10 <= deep_pct < 15 or 30 < deep_pct <= 40:
            score += 2
        else:
            score += 1
            notes.append("deep basso" if deep_pct < 10 else "deep alto")
        
        # Efficienza (ideale >85%)
        if session.efficiency >= 90:
            score += 3
        elif session.efficiency >= 80:
            score += 2
        else:
            score += 1
            notes.append("frammentato")
        
        # Movimento medio (basso = sonno profondo)
        if session.avg_activity < 3:
            score += 2
        elif session.avg_activity < 5:
            score += 1
        
        # Rating
        if score >= 10:
            emoji = "⭐⭐⭐ Ottima"
        elif score >= 7:
            emoji = "⭐⭐ Buona"
        elif score >= 4:
            emoji = "⭐ Sufficiente"
        else:
            emoji = "❌ Scarsa"
        
        return f"{emoji} ({', '.join(notes[:2])})"
    
    def export_summary_csv(self, filepath: str):
        """Esporta riepilogo in CSV"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'night_label', 'date', 'start_time', 'end_time',
                'time_in_bed_min', 'total_sleep_min', 'deep_sleep_min',
                'light_sleep_min', 'awake_min', 'gaps_min',
                'efficiency_pct', 'deep_pct', 'avg_activity', 'num_records'
            ])
            
            for session in self.night_sessions:
                writer.writerow([
                    session.get_night_label(),
                    session.start.strftime('%Y-%m-%d'),
                    session.start.strftime('%H:%M'),
                    session.end.strftime('%H:%M'),
                    f"{session.time_in_bed:.0f}",
                    session.total_min,
                    session.deep_min,
                    session.light_min,
                    session.awake_min,
                    f"{session.gaps_min:.0f}",
                    f"{session.efficiency:.1f}",
                    f"{session.deep_percentage:.1f}",
                    f"{session.avg_activity:.2f}",
                    len(session.records)
                ])
        
        print(f"\n✓ Exported to {filepath}")


def find_latest_csv(folder: str = ".") -> Optional[str]:
    """Trova il CSV più recente nella cartella"""
    csvs = list(Path(folder).glob("raw_sleep_data_*.csv"))
    if not csvs:
        return None
    return str(max(csvs, key=lambda p: p.stat().st_mtime))


def main():
    parser = argparse.ArgumentParser(
        description='Analisi intelligente del sonno - Aggrega i dati raw in notti complete'
    )
    parser.add_argument('--file', '-f', type=str, 
                        help='CSV file da analizzare (default: più recente)')
    parser.add_argument('--detailed', '-d', action='store_true',
                        help='Mostra dettaglio per ogni notte')
    parser.add_argument('--naps', '-n', action='store_true',
                        help='Mostra anche i pisolini diurni')
    parser.add_argument('--export', '-e', type=str,
                        help='Esporta riepilogo in CSV')
    parser.add_argument('--gap', '-g', type=int, default=60,
                        help='Gap in minuti per separare sessioni (default: 60)')
    
    args = parser.parse_args()
    
    # Trova file
    if args.file:
        csv_file = args.file
    else:
        csv_file = find_latest_csv()
        if not csv_file:
            print("❌ Nessun file raw_sleep_data_*.csv trovato")
            return
    
    print(f"📁 Analyzing: {csv_file}")
    
    # Analizza
    analyzer = SleepAnalyzer()
    analyzer.load_csv(csv_file)
    analyzer.aggregate_sessions(gap_threshold_min=args.gap)
    
    # Output
    analyzer.print_summary()
    
    if args.detailed:
        analyzer.print_detailed()
    
    if args.naps:
        analyzer.print_naps()
    
    if args.export:
        analyzer.export_summary_csv(args.export)
    
    print("\n" + "=" * 80)
    print("Uso: python real_sleep.py --detailed --naps")
    print("=" * 80)


if __name__ == "__main__":
    main()
