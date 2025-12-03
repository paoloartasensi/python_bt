# CL837 Heart Rate Protocol - Reverse Engineering Report

## Panoramica

Documentazione del protocollo BLE per il download della cronologia Heart Rate dal fitness tracker Chileaf CL837, ottenuta tramite reverse engineering dell'SDK Android decompilato.

---

## Frequenza di Campionamento HR

### Intervallo: **1 minuto (60 secondi)**

Il dispositivo CL837 campiona automaticamente la frequenza cardiaca **ogni 60 secondi** durante il monitoraggio continuo.

#### Evidenza dal codice SDK (`WearReceivedDataCallback.java`):

```java
// Linee 234-237
for (int i20 = 4; i20 < bArrSubSlice4.length; i20++) {
    this.mHistoryOfHeartRates.add(new HistoryOfHeartRate(
        DateUtil.restoreZoneUTC(this.mStamp), 
        getIntParse(bArrSubSlice4, i20, 1)
    ));
    this.mStamp++;  // Incrementa di 1 minuto per ogni valore HR
}
```

Il timestamp `mStamp` viene incrementato di 1 per ogni valore HR, dove l'unità è il **minuto**.

#### Verifica empirica dai dati scaricati:

```csv
datetime,hr_bpm,session_start,minute_offset
2025-12-03 00:22:44,72,00:22:44,0
2025-12-03 00:23:44,73,00:22:44,1   ← +1 minuto
2025-12-03 00:24:44,74,00:22:44,2   ← +1 minuto
2025-12-03 00:25:44,78,00:22:44,3   ← +1 minuto
```

---

## Sessioni HR Multiple

### Perché ci sono più sessioni nello stesso giorno?

Il monitoraggio HR **non è continuo 24/7**. Una nuova sessione inizia quando:

| Evento | Descrizione |
|--------|-------------|
| 🖐️ **Polso rilevato/perso** | Il sensore ottico rileva/perde contatto con la pelle |
| ⌚ **Indosso/rimozione** | Metti o togli l'orologio |
| 🔄 **Riavvio dispositivo** | Il tracker si riavvia o va in standby |
| 💪 **Attività sportiva** | Inizi/termini un workout |
| 📱 **Misurazione manuale** | Avvii una lettura HR on-demand |
| 🌙 **Movimento notturno** | Perdi contatto durante il sonno |

### Struttura Dati

```
Giorno
├── Sessione 1 (00:22:44)
│   ├── HR[0]: 72 bpm @ 00:22:44
│   ├── HR[1]: 73 bpm @ 00:23:44
│   ├── HR[2]: 74 bpm @ 00:24:44
│   └── ...
├── Sessione 2 (00:58:19)
│   ├── HR[0]: 68 bpm @ 00:58:19
│   └── ...
└── Sessione N (...)
```

### Esempio reale (3 Dicembre 2025):

```
Sessioni notturne rilevate:
00:22:44 ─── Sessione lunga (monitoraggio stabile)
00:58:19 ─┐
01:00:04  │
01:00:44  ├─ Sessioni brevi ravvicinate
01:02:53  │  (movimento nel sonno, perdita contatto)
01:04:07  │
01:05:32 ─┘
...
```

---

## Protocollo BLE

### Service UUID
```
AAE28F00-71B5-42A1-8C3C-F9CF6AC969D0
```

### Characteristics
| Nome | UUID | Direzione |
|------|------|-----------|
| TX (Write) | `AAE28F01-...` | App → Device |
| RX (Notify) | `AAE28F02-...` | Device → App |

### Comandi HR History

| Comando | Hex | Descrizione |
|---------|-----|-------------|
| `CMD_HR_RECORD` | `0x21` | Richiede lista sessioni (timestamp) |
| `CMD_HR_DATA` | `0x22` | Richiede dati HR per sessione |
| `CMD_HR_DATA_END` | `0x23` | Marker fine trasmissione dati |

### Checksum Formula

```python
def checksum(data: bytes) -> int:
    return ((-sum(data)) ^ 0x3A) & 0xFF
```

Derivato da `FitnessManager.java` linea 174:
```java
protected byte checkSum(final byte[] data) {
    int result = 0;
    for (byte item : data) {
        result += item;
    }
    return (byte) (((-result) ^ 58) & 255);
}
```

### Formato Pacchetto

```
┌──────┬────────┬─────────┬───────────┬──────────┐
│ 0xFF │ Length │ Command │ Payload   │ Checksum │
├──────┼────────┼─────────┼───────────┼──────────┤
│ 1B   │ 1B     │ 1B      │ Variable  │ 1B       │
└──────┴────────┴─────────┴───────────┴──────────┘
```

### Risposta CMD_HR_RECORD (0x21)

Contiene timestamp UTC (4 byte big-endian) per ogni sessione:

```
[0xFF][Len][0x21][TS1_4B][TS2_4B][TS3_4B]...[Checksum]
```

### Risposta CMD_HR_DATA (0x22)

Contiene valori HR (1 byte ciascuno):

```
[0xFF][Len][0x22][SeqNum_4B][HR1][HR2][HR3]...[Checksum]
```

- `SeqNum`: Timestamp inizio sessione (big-endian, UTC seconds)
- `HR1..HRn`: Valori BPM, uno per minuto

### Fine Trasmissione (0x23)

Il comando `0x23` segnala la fine del download dati HR.

---

## Riferimenti Codice SDK

| File | Funzione |
|------|----------|
| `FitnessManager.java` | Checksum, BLE setup |
| `WearManager.java` | API alto livello |
| `WearReceivedDataCallback.java` | Parsing risposte HR |
| `HistoryOfHeartRate.java` | Model dati HR |
| `DateUtil.java` | Conversione timestamp |

---

## Note

- Il campionamento a 1 minuto è per **risparmio batteria** durante monitoraggio automatico
- Le misurazioni **on-demand** (manuali) possono avere frequenza diversa
- I dati sono memorizzati sul dispositivo fino al sync con l'app
- Capacità storage: dipende dal modello (tipicamente 7-30 giorni)

---

*Documento generato: 3 Dicembre 2025*  
*Basato su: Chileaf SDK Android decompilato*
