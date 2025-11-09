# CL837 Sleep Data Download - Documentazione

## Overview

Script Python per scaricare e analizzare i dati del sonno dal dispositivo CL837/CL831.

## Protocollo Chileaf - Comandi Utilizzati

### 1. Set UTC Time (0x08)

Sincronizza l'orologio del dispositivo con l'ora UTC corrente.

**Formato comando:**
```
FF 08 08 [UTC_MSB] [UTC] [UTC] [UTC_LSB] [CHECKSUM]
```

**Esempio:**
- Header: `0xFF`
- Length: `0x08` (8 bytes totali)
- Command: `0x08`
- UTC: 4 bytes big-endian (timestamp Unix)
- Checksum: calcolato

### 2. Get Sleep Data (0x05)

Richiede lo storico dei dati del sonno.

**Formato richiesta:**
```
FF 05 05 02 [CHECKSUM]
```

**Formato risposta:**
```
FF [LEN] 05 03 [COUNT] [UTC(4)] [ACT_0] [ACT_1] ... [ACT_n] [CHECKSUM]
```

**Campi risposta:**
- `0x03`: Pacchetto dati sonno
- `COUNT`: Numero di intervalli da 5 minuti
- `UTC(4)`: Timestamp inizio sonno (4 bytes)
- `ACT_x`: Activity index per ogni intervallo da 5 minuti

**Fine dati:**
- `0xFF` come subcommand: indica fine trasmissione
- Pacchetto < 50 bytes: ultimo pacchetto

## Interpretazione Activity Index

Ogni byte rappresenta 5 minuti di sonno:

- **> 20**: Non addormentato / Sveglio
- **< 20**: Sonno leggero
- **3 zeri consecutivi**: Sonno profondo

### Esempi:

```
[5, 3, 2, 0, 0, 0, 15, 25, 10]
 │  │  │  └──┬──┘  │   │   │
 │  │  │     │     │   │   └─ Sveglio (>20)
 │  │  │     │     │   └───── Sonno leggero
 │  │  │     │     └───────── Sveglio (>20)
 │  │  │     └───────────── Sonno profondo (3 zeri)
 │  │  └─────────────────── Sonno leggero
 │  └────────────────────── Sonno leggero
 └───────────────────────── Sonno leggero
```

## Calcolo Checksum

Il checksum Chileaf usa questo algoritmo:

```python
def calculate_checksum(data):
    # 1. Somma tutti i bytes
    checksum = sum(data) & 0xFF
    # 2. Sottrai da 0
    checksum = (0 - checksum) & 0xFF
    # 3. XOR con 0x3A
    checksum = checksum ^ 0x3A
    return checksum
```

## Utilizzo dello Script

### Esecuzione

```powershell
python sleep.py
```

### Flusso Operativo

1. **Scan dispositivi BLE**
   - Cerca dispositivi con nome "CL837" o "CL831"
   - Mostra lista dispositivi trovati
   - Permette selezione manuale se multipli

2. **Connessione**
   - Si connette al dispositivo selezionato
   - Timeout: 10 secondi

3. **Discover Services**
   - Cerca il servizio Chileaf: `aae28f00-71b5-42a1-8c3c-f9cf6ac969d0`
   - Identifica caratteristiche TX (notify) e RX (write)

4. **Sincronizzazione UTC**
   - Invia timestamp UTC corrente al dispositivo
   - Necessario per interpretare correttamente i dati storici

5. **Download Dati Sonno**
   - Invia comando 0x05 0x02
   - Riceve pacchetti di risposta
   - Timeout: 30 secondi

6. **Analisi e Display**
   - Decodifica gli activity indices
   - Calcola durata sonno profondo/leggero/veglia
   - Mostra report dettagliato

### Output Esempio

```
SLEEP DATA ANALYSIS
======================================================================

Total sleep records: 2

Record 1:
  Start time: 2024-11-04 22:30:00 UTC
  Duration: 420 minutes (84 x 5min intervals)
  Deep sleep: 180 minutes (36 intervals)
  Light sleep: 210 minutes (42 intervals)
  Awake: 30 minutes (6 intervals)
  Activity indices: [5, 3, 2, 0, 0, 0, ...]

Record 2:
  Start time: 2024-11-05 00:15:00 UTC
  Duration: 180 minutes (36 x 5min intervals)
  ...
```

## Struttura Codice

### Classe `CL837SleepMonitor`

#### Attributi Principali

- `CHILEAF_SERVICE_UUID`: UUID servizio principale
- `CHILEAF_TX_UUID`: UUID caratteristica notifiche
- `CHILEAF_RX_UUID`: UUID caratteristica scrittura
- `sleep_data`: Array di record sonno
- `sleep_data_complete`: Flag completamento download

#### Metodi Principali

1. **`scan_and_connect()`**
   - Scansiona e connette al dispositivo

2. **`discover_services()`**
   - Identifica servizi e caratteristiche BLE

3. **`set_utc_time()`**
   - Sincronizza orologio dispositivo

4. **`get_sleep_data()`**
   - Richiede dati sonno

5. **`notification_handler()`**
   - Gestisce notifiche BLE in arrivo

6. **`parse_sleep_data()`**
   - Decodifica pacchetti dati sonno

7. **`analyze_sleep_data()`**
   - Analizza e mostra statistiche sonno

## Riferimenti SDK

### Android (WearManager.java)

```java
public void setUTCTime(final long stamp) {
    sendCommand((byte) 8, utc2Bytes(stamp));
}

public void getHistoryOfSleep() {
    this.mReceivedDataCallback.clearType(22);
    sendCommand((byte) 5, 2);
}
```

### iOS (HeartBLEDevice.m)

```objectivec
- (void)asynUTCTime {
    NSDate *date = [NSDate date];
    NSTimeInterval ti = [date timeIntervalSince1970];
    int time = [timeStr intValue] + 28800;
    NSString *UTCStr = @"ff0808";
    // ... build command
    [self BLEReadData:UTCStr1];
}

- (void)getSleepData {
    NSString *command = @"ff050502";
    [self BLEReadData:command];
}
```

## Troubleshooting

### Nessun dispositivo trovato
- Verificare che il dispositivo sia acceso
- Controllare che Bluetooth sia abilitato
- Avvicinare il dispositivo al computer

### Timeout ricezione dati
- Il dispositivo potrebbe non avere dati sonno
- Verificare che l'UTC sia stato sincronizzato
- Riprovare la connessione

### Errori di parsing
- Controllare i log esadecimali dei pacchetti
- Verificare il calcolo del checksum
- Assicurarsi che il dispositivo sia compatibile (CL831/CL837)

## Note Tecniche

1. **Intervalli da 5 minuti**: Tutti i dati sonno sono aggregati in intervalli di 5 minuti

2. **UTC Timezone**: I timestamp sono sempre in UTC, non in timezone locale

3. **Pacchetti multipli**: I dati possono arrivare in più pacchetti se il periodo di sonno è lungo

4. **Deep Sleep Detection**: 3 zeri consecutivi = deep sleep (non solo valori bassi)

5. **Checksum Protocol**: Specifico Chileaf, diverso da checksum standard

## Dipendenze

```
bleak>=0.21.0
```

Installazione:
```powershell
pip install bleak
```

## Compatibilità

- **Dispositivi**: CL831, CL837
- **OS**: Windows, macOS, Linux
- **Python**: 3.7+
- **BLE**: 4.0+
