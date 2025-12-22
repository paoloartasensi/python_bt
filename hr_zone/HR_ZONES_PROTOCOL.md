# HR Zones & Alarms - CL837/CL831

## Panoramica

Il dispositivo CL837/CL831 supporta configurazione di **zone cardiache** e **allarmi HR** basati su età o limiti personalizzati. Il device può:

- Vibrare quando si supera la HR massima
- Calcolare zone di allenamento ottimali
- Monitorare efficacia dell'allenamento

---

## 1. Modalità Allarme HR

### Comando 0x57 (87 decimale)

Imposta la modalità di calcolo degli allarmi HR:

```text
TX: [FF] [05] [57] [mode] [checksum]

mode:
  0x01 = Age-based (calcolo automatico da età utente)
  0x00 = Fixed limits (limiti superiore/inferiore fissi)
```

#### Modalità Age-Based (0x01)

**Formula standard:** `HR_max = 220 - età`

**Limiti default se non configurati:**

- Max: 140 bpm
- Min: 0 bpm (nessun limite inferiore)

**Esempio:**

- Utente 30 anni → HR_max = 190 bpm
- Utente 50 anni → HR_max = 170 bpm

#### Modalità Fixed Limits (0x00)

**Limiti default:**

- Max: 140 bpm
- Min: 100 bpm

Usare comando 0x46 per personalizzare i limiti.

### Esempio Python

```python
# Modalità age-based
packet = [0xFF, 0x05, 0x57, 0x01]
checksum = calculate_checksum(packet)
packet.append(checksum)
await client.write_gatt_char(rx_char, bytes(packet))

# Modalità fixed
packet = [0xFF, 0x05, 0x57, 0x00]
checksum = calculate_checksum(packet)
packet.append(checksum)
await client.write_gatt_char(rx_char, bytes(packet))
```

---

## 2. Impostare HR Max Personalizzata

### Comando 0x74 (116 decimale)

Imposta la frequenza cardiaca massima personalizzata:

```text
TX: [FF] [07] [74] [00] [06] [max_hr] [checksum]

max_hr: valore in bpm (es. 180)
```

**Uso tipico:**

- Dopo test da sforzo medico
- Per atleti con HR_max diversa dalla formula standard
- Per limitare intensità allenamento

### Esempio Python

```python
# Impostare HR_max = 185 bpm
max_hr = 185
packet = [0xFF, 0x07, 0x74, 0x00, 0x06, max_hr]
checksum = calculate_checksum(packet)
packet.append(checksum)
await client.write_gatt_char(rx_char, bytes(packet))
```

### Comando 0x75 - Leggere HR Max

```text
TX: [FF] [06] [75] [00] [06] [checksum]

RX: [FF] [len] [75] [...] [max_hr] [checksum]
```

---

## 3. Impostare Zona Target + Goal

### Comando 0x46 (70 decimale)

Imposta la zona cardiaca target per l'allenamento:

```
TX: [FF] [08] [46] [01] [min] [max] [goal] [checksum]

min:  HR minima della zona target (bpm)
max:  HR massima della zona target (bpm)
goal: HR obiettivo dell'allenamento (bpm)
```

**Esempio zona cardio moderata:**

```
min:  120 bpm
max:  150 bpm
goal: 135 bpm
```

### Comando 0x46 0x00 - Leggere Impostazioni

```
TX: [FF] [08] [46] [00] [00] [00] [00] [checksum]

RX: [FF] [len] [46] [...] [min] [max] [goal] [checksum]
```

### Esempio Python

```python
# Impostare zona 120-150 bpm, goal 135 bpm
min_hr = 120
max_hr = 150
goal_hr = 135

packet = [0xFF, 0x08, 0x46, 0x01, min_hr, max_hr, goal_hr]
checksum = calculate_checksum(packet)
packet.append(checksum)
await client.write_gatt_char(rx_char, bytes(packet))
```

---

## 4. Leggere Età Utente

### Comando 0x03 (User Info)

Per calcolare le zone in base all'età, leggere prima i dati utente:

```
TX: [FF] [04] [03] [checksum]

RX: [FF] [len] [03] [age] [sex] [weight_H] [weight_L] 
    [height_H] [height_L] [user_id_4bytes] [checksum]

age: età in anni
sex: 0=female, 1=male
```

---

## 5. Zone Cardiache Standard

### Classificazione per % di HR_max

|Zona|% HR Max|Descrizione|Uso Tipico|
|------|----------|-------------|------------|
| **🔵 Riposo** |<50%|Recupero attivo|Cool-down, stretching|
| **🟢 Brucia Grassi** |50-60%|Aerobica leggera|Perdita peso, resistenza base|
| **🟡 Cardio** |60-70%|Aerobica moderata|Fitness generale|
| **🟠 Intensa** |70-85%|Anaerobica|Miglioramento performance|
| **🔴 Massima** |85-100%|Sforzo massimo|Interval training, sprint|

### Calcolo delle Zone

#### Esempio: Utente 30 anni

```
HR_max = 220 - 30 = 190 bpm

Zona 1 (Riposo):        < 95 bpm     (<50%)
Zona 2 (Brucia Grassi): 95-114 bpm   (50-60%)
Zona 3 (Cardio):        114-133 bpm  (60-70%)
Zona 4 (Intensa):       133-162 bpm  (70-85%)
Zona 5 (Massima):       162-190 bpm  (85-100%)
```

---

## 6. Lettura UTC e Switch Allarme

### Comando 0x5B (91 decimale)

Legge timestamp UTC corrente e stato switch allarme:

```
TX: [FF] [04] [5B] [checksum]

RX: [FF] [len] [5B] [utc_4bytes] [alarm_enabled] [checksum]

alarm_enabled: 0x00=off, 0x01=on
```

---

## 7. Comportamento Device

### Quando HR > Max

1. **Vibrazione**: Device vibra per allertare
2. **Display**: Icona allarme (se presente)
3. **Log**: Evento registrato per analisi

### Durante Allenamento

- Device calcola **tempo in zona**
- Mostra **zona corrente** sul display
- Calcola **efficacia** dell'allenamento

### Dati Salvati

I dati sport (comando 0x15/0x16) includono:

- HR media
- HR massima
- Tempo in ogni zona (nei modelli superiori)
- Calorie bruciate (basate su zone)

---

## 8. Best Practices

### Configurazione Iniziale

1. **Leggere età** utente (cmd 0x03)
2. **Calcolare HR_max** = 220 - età
3. **Impostare modalità** age-based (cmd 0x57)
4. **Opzionale**: Personalizzare HR_max (cmd 0x74)
5. **Impostare zona** target per allenamento (cmd 0x46)

### Per Allenamento Specifico

```python
# Zona brucia grassi (50-60% HR_max)
age = 35
hr_max = 220 - age  # 185 bpm
min_hr = int(hr_max * 0.50)  # 93 bpm
max_hr = int(hr_max * 0.60)  # 111 bpm
goal_hr = int(hr_max * 0.55)  # 102 bpm

# Imposta zona
set_hr_zone(min_hr, max_hr, goal_hr)
```

### Per Sicurezza

```python
# Limitare HR max per utenti con condizioni mediche
# Esempio: limitare a 140 bpm indipendentemente dall'età
set_max_heart_rate(140)
set_alert_mode_fixed()  # Usa limiti fissi
```

---

## 9. Comandi Correlati

|Comando|Funzione|Read/Write|
|---------|----------|------------|
| `0x03` | User Info (età, sesso, peso, altezza) | Read |
| `0x04` | Set User Info | Write |
| `0x46` | HR Zone (min, max, goal) | Read/Write |
| `0x57` | Alert Mode (age/fixed) | Write |
| `0x5B` | UTC + Alert Status | Read |
| `0x74` | Set Max HR | Write |
| `0x75` | Get Max HR | Read |

---

## 10. Limitazioni CL837

- **Nessuno storico zone**: Il device NON salva cronologia tempo-in-zona
- **Solo real-time**: Zone visibili solo durante monitoraggio attivo
- **App necessaria**: Per analisi dettagliata, l'app deve loggare dati BLE in tempo reale

**Modelli superiori** (CL838+) potrebbero supportare:

- Cronologia tempo-in-zona
- Allarmi multipli
- Zone personalizzate oltre le 5 standard
