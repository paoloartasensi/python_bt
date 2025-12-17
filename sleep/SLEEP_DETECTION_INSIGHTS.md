# 🛏️ Sleep Detection Insights - CL837 vs Professional Devices

## 📋 Sommario

Questo documento riepiloga le intuizioni sul rilevamento del sonno con il CL837 e confronta l'approccio con dispositivi professionali come WHOOP e Oura Ring.

---

## 1. 🔬 Come Funziona il CL837

### Cosa registra il dispositivo

Il firmware del CL837 **NON distingue giorno/notte**. Registra continuamente:

- **Activity Index** ogni 5 minuti (movimento del braccio via accelerometro)
- **Heart Rate** quando richiesto (non continuo durante il sonno)

### Chi decide cosa è "sonno"

È l'**APP** (o il nostro codice Python) che interpreta i dati post-download:

1. Raggruppa i record in "sessioni" basandosi sui gap temporali (>3h = nuova sessione)
2. Classifica le sessioni come NIGHT o NAP basandosi su orario e durata
3. Applica l'algoritmo SDK Chileaf:
   - `activity = 0` per 3+ intervalli consecutivi → **Deep Sleep**
   - `activity = 1-20` → **Light Sleep**
   - `activity > 20` → **Awake**

### Limiti del CL837

- **Solo accelerometro** → non può distinguere "immobile sul divano" da "addormentato"
- **Nessuna HR continua** durante il sonno
- **Nessun dato fisiologico** (HRV, temperatura, SpO2 continuo)

### Il problema "Divano"

Se ti siedi sul divano alle 20:00 e non ti muovi, il device registra `activity = 0` e l'app pensa che stai dormendo.

**Soluzione implementata:**

- **Bedtime Hints**: finestra oraria personalizzabile ("di solito vado a letto dopo le 21:30")
- **Confidence Score**: punteggio basato su orario + durata + deep% + HR
- **Classificazione 🛋️ COUCH**: sessioni sospette alle 20:00-21:30 con bassa confidence

---

## 2. ⌚ Come Funziona WHOOP

### Sensori

| Sensore | Uso |
|---------|-----|
| Accelerometro 3-axis | Movimento, rilevamento indossamento |
| PPG (fotopletismografo) | HR continua, HRV, SpO2 |
| Sensore temperatura | Temperatura cutanea |
| Giroscopio | Orientamento |

### Algoritmo di rilevamento sonno

WHOOP usa **machine learning** su dati fisiologici multipli:

1. **HR durante il giorno** → calcola baseline personale
2. **Rilevamento onset sonno:**
   - HR scende **sotto la baseline** (tipicamente -10/15 bpm)
   - HRV **aumenta** (attivazione parasimpatica)
   - Movimento **ridotto** per almeno 15 minuti
   - Temperatura cutanea **sale** leggermente

3. **Classificazione fasi (ogni 30 secondi):**
   - **REM**: HR variabile, HRV più bassa, assenza movimenti oculari rapidi (dedotta da micro-movimenti)
   - **Deep (SWS)**: HR minima, HRV massima, nessun movimento
   - **Light**: HR stabile, HRV media, occasionali micro-movimenti
   - **Awake**: HR elevata, movimento o cambio posizione

4. **Auto-detect**: Può rilevare sonno **qualsiasi ora** (anche pisolino alle 15:00) perché si basa su pattern fisiologici, non sull'orario.

### Perché WHOOP è più preciso

- **Multi-sensore**: combina 4+ segnali invece di 1
- **HR continua**: campiona ogni secondo durante il sonno
- **HRV**: indicatore gold-standard della qualità del sonno
- **Machine Learning**: modello allenato su milioni di notti
- **Calibrazione personale**: impara il TUO pattern in 4-5 giorni

---

## 3. 💍 Come Funziona Oura Ring

### Oura Sensori

| Sensore | Uso |
|---------|-----|
| LED infrarossi (PPG) | HR, HRV, SpO2 |
| NTC termistori | Temperatura corporea |
| Accelerometro 3D | Movimento, attività |

### Vantaggi del form factor anello

- **Dito**: arterie più superficiali → segnale PPG più pulito
- **Meno artefatti da movimento** rispetto al polso
- **Temperatura più stabile** (meno variazioni ambientali)

### Oura Algoritmo di rilevamento sonno

Oura usa un approccio simile a WHOOP ma con enfasi sulla **temperatura**:

1. **Temperatura corporea**:
   - Sale di 0.5-1°C nelle prime ore di sonno
   - Pattern caratteristico: picco a metà notte, poi cala verso il risveglio
   - Variazioni anomale → indicatore di malattia/stress

2. **HR & HRV**:
   - **Lowest Resting HR**: punto più basso della notte (indica recupero)
   - **HRV Balance**: confronta HRV notturna con media personale
   - Pattern HRV durante le fasi (alta in Deep, bassa in REM)

3. **Classificazione fasi:**
   - Usa **combinazione HR + HRV + movimento + temperatura**
   - Algoritmo proprietario validato vs polisonnografia
   - Accuracy dichiarata: ~79% agreement con PSG (gold standard)

4. **Sleep Score** (0-100):
   - Total Sleep Time: 35%
   - Efficiency: 25%
   - REM Sleep: 20%
   - Deep Sleep: 20%

### Oura Features Uniche

- **Readiness Score**: combina sonno + HRV + temperatura per predire "recovery"
- **Period Prediction**: usa temperatura per predire ciclo mestruale
- **Illness Detection**: spike temperatura notturna → possibile malattia in arrivo

---

## 4. 📊 Confronto Dettagliato

### Tabella Comparativa

| Feature | CL837 | WHOOP | Oura Ring |
|---------|-------|-------|-----------|
| **Rilevamento automatico** | ❌ Orario-based | ✅ Fisiologico | ✅ Fisiologico |
| **Fasi sonno** | 3 (Deep/Light/Awake) | 4 (+REM) | 4 (+REM) |
| **HR continua** | ❌ No | ✅ Sì (1Hz) | ✅ Sì |
| **HRV** | ❌ No | ✅ Sì | ✅ Sì |
| **Temperatura** | ❌ No | ✅ Sì | ✅ Sì (migliore) |
| **SpO2** | ❌ No | ✅ Sì | ✅ Sì |
| **ML/AI** | ❌ No | ✅ Cloud | ✅ On-device |
| **Accuracy vs PSG** | ~60-65%? | ~80% | ~79% |
| **Prezzo** | ~€30 | €239 + €259/anno | €299-549 |

---

## 5. 💡 Come Migliorare il CL837

### Cosa abbiamo implementato

```python
# Bedtime Hints - personalizzabili
TYPICAL_BEDTIME_START = 21.5  # 21:30
TYPICAL_BEDTIME_END = 24.0    # 00:00
TYPICAL_WAKE_START = 6.0      # 06:00
TYPICAL_WAKE_END = 9.0        # 09:00

# Confidence Score basato su:
# - Orario in range tipico: +30
# - Durata sufficiente: +25
# - Deep sleep buono: +25
# - HR bassa (se disponibile): +20
```

### Cosa potremmo aggiungere

1. **Correlazione HR**: scaricare HR history della stessa notte e verificare che la media sia inferiore alla baseline diurna
2. **Pattern recognition**: cercare il "drop" di activity all'inizio del sonno reale
3. **Learning personale**: dopo N notti, imparare il TUO pattern tipico

### Limitazioni Hardware

- ❌ Rilevamento REM (richiede EEG o HR ad alta frequenza)
- ❌ HRV (richiede campionamento HR continuo)
- ❌ Temperatura corporea
- ❌ Auto-detect senza hint orari

---

## 6. 🎯 Conclusioni

### Il CL837 è adatto per

- ✅ Tracking basico durata sonno
- ✅ Stima grezza Deep/Light
- ✅ Trend settimanali
- ✅ Chi vuole spendere poco

### Non è adatto per

- ❌ Analisi qualità sonno precisa
- ❌ Rilevamento disturbi del sonno
- ❌ Ottimizzazione recovery atletico
- ❌ Chi vuole dati scientifici

### Upgrade consigliati

- **Budget**: Xiaomi Mi Band 8 (~€40) - aggiunge SpO2 e HR migliorata
- **Mid-range**: Garmin Venu 3 (~€400) - HRV, body battery, sleep coaching
- **Pro**: WHOOP 4.0 o Oura Gen3 - gold standard consumer

---

## 📚 Riferimenti

1. WHOOP Sleep Performance Assessment - [whoop.com/thelocker](https://www.whoop.com/thelocker/whoop-sleep-performance-assessment/)
2. Oura Ring Accuracy Study (2020) - [ouraring.com/accuracy](https://ouraring.com/blog/sleep-accuracy/)
3. Chileaf SDK Documentation - Internal
4. "Consumer Sleep Tracking Devices: A Review of Current Technologies" - Sleep Medicine Reviews, 2023

---

*Documento creato il 15 Dicembre 2025*
*Progetto: python_bt/sleep*
