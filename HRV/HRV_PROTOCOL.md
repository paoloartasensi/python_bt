# HRV (Heart Rate Variability) - CL837/CL831

## Panoramica

L'HRV (Heart Rate Variability) è la variazione temporale tra battiti cardiaci consecutivi. Viene misurata attraverso gli **RR intervals**, ovvero il tempo tra i picchi R dell'ECG (o PPG nel caso dei wearable).

Il dispositivo CL837/CL831 fornisce i dati HRV attraverso **due canali distinti**:

1. **Standard BLE Heart Rate Service** → RR intervals raw
2. **Chileaf Custom Protocol** → Metriche HRV calcolate (TP, LF, HF)

---

## 1. RR Intervals (Standard BLE)

### Servizio e Caratteristica

| Campo | Valore |
|-------|--------|
| Service UUID | `0000180D-0000-1000-8000-00805F9B34FB` (Heart Rate Service) |
| Characteristic UUID | `00002A37-0000-1000-8000-00805F9B34FB` (Heart Rate Measurement) |
| Tipo | NOTIFY |

### Formato del Pacchetto

La caratteristica `2A37` segue lo standard Bluetooth SIG:

```
Byte 0: Flags
  - Bit 0: HR format (0 = uint8, 1 = uint16)
  - Bit 1-2: Sensor contact status
  - Bit 3: Energy Expended present
  - Bit 4: RR-Intervals present (1 = sì)

Byte 1(-2): Heart Rate (BPM)

Byte N+1...: Energy Expended (se bit 3 = 1)

Byte M...: RR Intervals (se bit 4 = 1)
  - Ogni RR interval è un uint16 (2 bytes, little-endian)
  - Unità: 1/1024 secondi
```

### Conversione RR Intervals

```python
# Da raw a millisecondi
rr_ms = rr_raw * 1000 / 1024

# Esempio: rr_raw = 820
# rr_ms = 820 * 1000 / 1024 = 800.78 ms
```

### Esempio Parsing (Python)

```python
def parse_hr_measurement(data):
    flags = data[0]
    hr_format = flags & 0x01
    has_rr = (flags & 0x10) != 0
    
    # Parse Heart Rate
    if hr_format == 0:
        hr = data[1]
        offset = 2
    else:
        hr = struct.unpack('<H', data[1:3])[0]
        offset = 3
    
    # Parse RR Intervals
    rr_intervals = []
    if has_rr:
        while offset < len(data) - 1:
            rr_raw = struct.unpack('<H', data[offset:offset+2])[0]
            rr_ms = rr_raw * 1000 / 1024
            rr_intervals.append(rr_ms)
            offset += 2
    
    return hr, rr_intervals
```

---

## 2. Metriche HRV Calcolate (Chileaf Protocol)

### Servizio e Caratteristica

| Campo | Valore |
|-------|--------|
| Service UUID | `AAE28F00-71B5-42A1-8C3C-F9CF6AC969D0` |
| TX Characteristic | `AAE28F01-71B5-42A1-8C3C-F9CF6AC969D0` (NOTIFY) |
| RX Characteristic | `AAE28F02-71B5-42A1-8C3C-F9CF6AC969D0` (WRITE) |

### Comando Health Data (0x02)

Il device invia automaticamente dati salute (incluso HRV) tramite notifiche con comando `0x02`:

```
[FF] [len] [02] [vo2max] [breath_rate] [emotion] [stress] [stamina] [TP(4)] [LF(4)] [HF(4)] [checksum]

Offset  Bytes  Campo           Tipo        Descrizione
0       1      Header          uint8       0xFF
1       1      Length          uint8       Lunghezza pacchetto
2       1      Command         uint8       0x02 (Health Data)
3       1      VO2 Max         uint8       ml/kg/min
4       1      Breath Rate     uint8       respiri/min
5       1      Emotion         uint8       Indice emotivo (0-100)
6       1      Stress          uint8       Percentuale stress
7       1      Stamina         uint8       0=Low, 1=Normal, 2=High
8-11    4      HRV TP          float32 BE  Total Power
12-15   4      HRV LF          float32 BE  Low Frequency Power
16-19   4      HRV HF          float32 BE  High Frequency Power
20      1      Checksum        uint8       Checksum Chileaf
```

### Metriche HRV

| Metrica | Range Freq. | Significato |
|---------|-------------|-------------|
| **TP** (Total Power) | 0-0.4 Hz | Variabilità totale |
| **LF** (Low Frequency) | 0.04-0.15 Hz | Attività simpatica e parasimpatica |
| **HF** (High Frequency) | 0.15-0.4 Hz | Attività parasimpatica (vagale) |
| **LF/HF Ratio** | - | Bilancio simpatico/parasimpatico |

---

## 3. Calcolo Metriche HRV dai RR Intervals

Se vuoi calcolare le metriche HRV lato client (invece di usare quelle del device):

### Metriche nel Dominio del Tempo

```python
import numpy as np

def calculate_time_domain_hrv(rr_intervals):
    """
    Calcola metriche HRV nel dominio del tempo
    rr_intervals: lista di RR in millisecondi
    """
    rr = np.array(rr_intervals)
    
    # SDNN - Standard Deviation of NN intervals
    sdnn = np.std(rr, ddof=1)
    
    # RMSSD - Root Mean Square of Successive Differences
    diff = np.diff(rr)
    rmssd = np.sqrt(np.mean(diff ** 2))
    
    # pNN50 - Percentage of successive RR differences > 50ms
    nn50 = np.sum(np.abs(diff) > 50)
    pnn50 = (nn50 / len(diff)) * 100
    
    # Mean RR
    mean_rr = np.mean(rr)
    
    # Mean HR (from RR)
    mean_hr = 60000 / mean_rr
    
    return {
        'sdnn': sdnn,
        'rmssd': rmssd,
        'pnn50': pnn50,
        'mean_rr': mean_rr,
        'mean_hr': mean_hr
    }
```

### Metriche nel Dominio della Frequenza

```python
from scipy import signal

def calculate_frequency_domain_hrv(rr_intervals, fs=4.0):
    """
    Calcola metriche HRV nel dominio della frequenza
    rr_intervals: lista di RR in millisecondi
    fs: frequenza di campionamento per interpolazione (Hz)
    """
    rr = np.array(rr_intervals)
    
    # Crea serie temporale dai RR
    t = np.cumsum(rr) / 1000  # tempo in secondi
    t = t - t[0]  # inizia da 0
    
    # Interpolazione a frequenza costante
    t_interp = np.arange(0, t[-1], 1/fs)
    rr_interp = np.interp(t_interp, t, rr)
    
    # Rimuovi trend
    rr_detrend = signal.detrend(rr_interp)
    
    # Calcola PSD (Welch)
    freqs, psd = signal.welch(rr_detrend, fs=fs, nperseg=256)
    
    # Bande di frequenza
    vlf_band = (0.003, 0.04)
    lf_band = (0.04, 0.15)
    hf_band = (0.15, 0.4)
    
    # Calcola potenza per banda
    vlf_idx = np.logical_and(freqs >= vlf_band[0], freqs < vlf_band[1])
    lf_idx = np.logical_and(freqs >= lf_band[0], freqs < lf_band[1])
    hf_idx = np.logical_and(freqs >= hf_band[0], freqs < hf_band[1])
    
    vlf = np.trapz(psd[vlf_idx], freqs[vlf_idx])
    lf = np.trapz(psd[lf_idx], freqs[lf_idx])
    hf = np.trapz(psd[hf_idx], freqs[hf_idx])
    
    tp = vlf + lf + hf
    
    return {
        'vlf': vlf,
        'lf': lf,
        'hf': hf,
        'tp': tp,
        'lf_hf_ratio': lf / hf if hf > 0 else 0,
        'lf_nu': lf / (lf + hf) * 100 if (lf + hf) > 0 else 0,  # normalized units
        'hf_nu': hf / (lf + hf) * 100 if (lf + hf) > 0 else 0
    }
```

---

## 4. Interpretazione Clinica

### RMSSD

| Valore (ms) | Interpretazione |
|-------------|-----------------|
| < 20 | Basso - possibile stress/affaticamento |
| 20-50 | Normale |
| > 50 | Alto - buon recupero |

### SDNN

| Valore (ms) | Interpretazione |
|-------------|-----------------|
| < 50 | Basso |
| 50-100 | Normale |
| > 100 | Alto |

### LF/HF Ratio

| Valore | Interpretazione |
|--------|-----------------|
| < 1 | Dominanza parasimpatica (rilassamento) |
| 1-2 | Bilanciato |
| > 2 | Dominanza simpatica (stress/attivazione) |

---

## 5. Note Tecniche

### Limitazioni del CL837

- Il device calcola TP, LF, HF internamente e li invia via comando `0x02`
- Gli RR intervals dal servizio HR standard potrebbero non essere sempre presenti
- La qualità dei dati dipende dal contatto sensore-pelle

### Best Practices

1. **Raccolta dati**: Minimo 5 minuti per analisi affidabile nel dominio della frequenza
2. **Filtraggio**: Rimuovi artefatti (RR < 300ms o > 2000ms, variazioni > 20% dal precedente)
3. **Posizione**: Dati più affidabili a riposo, seduti o sdraiati
4. **Orario**: L'HRV varia durante il giorno; misura sempre alla stessa ora per confronti

---

## 6. Riferimenti SDK

### iOS (HeartBLEDevice.m)

```objectivec
// Sottoscrizione caratteristica HR
if ([characteristic.UUID isEqual:[CBUUID UUIDWithString:@"2A37"]]) {
    [peripheral setNotifyValue:YES forCharacteristic:characteristic];
}
```

### Android (HeartRateMeasurementDataCallback.java)

```java
boolean rrIntervalsPresent = (flags & 16) != 0;
// ...
List<Integer> rrIntervals = Collections.unmodifiableList(intervals2);
onHeartRateMeasurementReceived(device, heartRate, sensorContact, energyExpanded, intervals);
```

### Callback Interface

```java
void onHeartRateMeasurementReceived(
    BluetoothDevice device,
    int heartRate,
    Boolean contactDetected,
    Integer energyExpanded,
    List<Integer> rrIntervals  // in unità di 1/1024 secondi
);
```
