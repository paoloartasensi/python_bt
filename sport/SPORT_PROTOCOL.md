# Sport Activity - CL837/CL831

## Panoramica

Il dispositivo CL837/CL831 fornisce dati di attività sportiva in tempo reale e storico:

- **Steps** - Passi totali giornalieri
- **Distance** - Distanza percorsa (cm)
- **Calories** - Calorie consumate (stima algoritmica)

---

## Protocollo BLE

### Servizio e Caratteristica

|Campo|Valore|
|-------|--------|
|Service UUID|`AAE28F00-71B5-42A1-8C3C-F9CF6AC969D0`|
|TX Characteristic|`AAE28F01-71B5-42A1-8C3C-F9CF6AC969D0` (NOTIFY)|
|RX Characteristic|`AAE28F02-71B5-42A1-8C3C-F9CF6AC969D0` (WRITE)|

---

## 1. Real-time Sport Data (Comando 0x15)

Il device invia automaticamente notifiche periodiche (~ogni 15 secondi) con i dati attività correnti.

### Formato Notifica

```text
[FF] [len] [15] [step_h] [step_m] [step_l] [dist_h] [dist_m] [dist_l] [cal_h] [cal_m] [cal_l] [checksum]

Offset  Bytes  Campo       Tipo        Descrizione
0       1      Header      uint8       0xFF
1       1      Length      uint8       Lunghezza pacchetto
2       1      Command     uint8       0x15 (21 decimal)
3-5     3      Steps       uint24 BE   Passi totali giornalieri
6-8     3      Distance    uint24 BE   Distanza in centimetri
9-11    3      Calories    uint24 BE   Calorie × 10 (0.1 kcal)
12      1      Checksum    uint8       Checksum Chileaf
```

### Conversioni

```python
# Steps - valore diretto
steps = (data[3] << 16) | (data[4] << 8) | data[5]

# Distance - da cm a metri/km
distance_cm = (data[6] << 16) | (data[7] << 8) | data[8]
distance_m = distance_cm / 100
distance_km = distance_cm / 100000

# Calories - dividere per 10
calories_raw = (data[9] << 16) | (data[10] << 8) | data[11]
calories_kcal = calories_raw / 10.0
```

### Esempio Parsing

```python
def parse_sport_data(data):
    """
    Parse real-time sport notification (cmd 0x15)
    """
    if len(data) < 12 or data[0] != 0xFF or data[2] != 0x15:
        return None
    
    # Big-endian 3-byte integers
    steps = (data[3] << 16) | (data[4] << 8) | data[5]
    distance_cm = (data[6] << 16) | (data[7] << 8) | data[8]
    calories_raw = (data[9] << 16) | (data[10] << 8) | data[11]
    
    return {
        'steps': steps,
        'distance_cm': distance_cm,
        'distance_m': distance_cm / 100,
        'distance_km': distance_cm / 100000,
        'calories_raw': calories_raw,
        'calories_kcal': calories_raw / 10.0
    }
```

---

## 2. 7-Day Sport History (Comando 0x16)

Richiesta dello storico attività degli ultimi 7 giorni.

### Request

```text
[FF] [04] [16] [checksum]
```

### Response

```text
[FF] [len] [16] [data...] [checksum]

Per ogni giorno (10 bytes):
  - UTC timestamp: 4 bytes (big-endian)
  - Steps: 3 bytes (big-endian)
  - Calories: 3 bytes (big-endian, × 10)
```

### Esempio Parsing

```python
def parse_sport_history(data):
    """
    Parse 7-day sport history (cmd 0x16)
    """
    if len(data) < 4 or data[0] != 0xFF or data[2] != 0x16:
        return None
    
    history = []
    offset = 3
    
    while offset + 10 <= len(data) - 1:  # -1 for checksum
        utc = (data[offset] << 24) | (data[offset+1] << 16) | \
              (data[offset+2] << 8) | data[offset+3]
        steps = (data[offset+4] << 16) | (data[offset+5] << 8) | data[offset+6]
        calories = (data[offset+7] << 16) | (data[offset+8] << 8) | data[offset+9]
        
        history.append({
            'utc': utc,
            'date': datetime.fromtimestamp(utc),
            'steps': steps,
            'calories_kcal': calories / 10.0
        })
        offset += 10
    
    return history
```

---

## Riferimenti SDK

### iOS (HeartBLEDevice.m)

```objectivec
else if (buffer_[2] == 0x15) {
    // 运动实时数据 (Real-time sport data)
    
    // 步数 (Steps)
    NSString *strA = [Hex16Str substringWithRange:NSMakeRange(6, 6)];
    NSString *Para1Str = [NSString stringWithFormat:@"%lu", 
                         strtoul(strA.UTF8String, 0, 16)];
    
    // 距离 (Distance)
    NSString *strB = [Hex16Str substringWithRange:NSMakeRange(12, 6)];
    float a = [Para2Str floatValue] / 100;  // cm → m
    
    // 卡路里 (Calories)
    NSString *strC = [Hex16Str substringWithRange:NSMakeRange(18, 6)];
    float b = [Para3Str floatValue] / 10;   // ×10 → kcal
    
    [theDelegate SDKFitRunSParamter:[Para1Str intValue] 
                          andFitKM:a 
                        andFitCalor:b];
}
```

### Android (WearReceivedDataCallback.java)

```java
// iIntValue == 21 means command 0x15 (21 decimal = 0x15 hex)
if (iIntValue == 21) {
    onSportReceived(
        bluetoothDevice,
        getIntParse(value, 3, 3),  // steps (3 bytes from offset 3)
        getIntParse(value, 6, 3),  // distance (3 bytes from offset 6)
        getIntParse(value, 9, 3)   // calories (3 bytes from offset 9)
    );
}
```

### Callback Interface (Android)

```java
public interface BodySportCallback {
    void onSportReceived(
        BluetoothDevice device,
        int step,      // passi totali
        int distance,  // distanza in cm
        int calorie    // calorie × 10
    );
}
```

---

## Calcolo Calorie

Le calorie sono **calcolate dal device** usando:

1. **Numero di passi**
2. **Distanza percorsa**
3. **Dati utente** (configurati via comando `0x04`):
   - Età
   - Sesso (0=F, 1=M)
   - Peso (kg)
   - Altezza (cm)

### Formula approssimativa

Il device usa tipicamente una formula simile a:

```text
Calorie = Passi × (Peso × Fattore_Passo)
```

Dove `Fattore_Passo` dipende da altezza e sesso.

Per risultati più accurati, **configura i dati utente** sul device:

```python
async def set_user_info(client, rx_char, age, sex, weight_kg, height_cm):
    """
    Set user info for better calorie estimation
    sex: 0=female, 1=male
    """
    packet = [
        0xFF,
        0x09,        # length
        0x04,        # command
        age,
        sex,
        weight_kg,
        height_cm,
        0, 0, 0, 0, 0  # phone number (optional)
    ]
    checksum = calculate_checksum(packet)
    packet.append(checksum)
    await client.write_gatt_char(rx_char, bytes(packet))
```

---

## Note Tecniche

### Frequenza di Aggiornamento

- **Real-time (0x15)**: ~ogni 15 secondi automaticamente
- **History (0x16)**: su richiesta

### Unità di Misura

|Campo|Unità Raw|Conversione|
|-------|-----------|-------------|
|Steps|count|diretto|
|Distance|cm|÷100 per metri|
|Calories|0.1 kcal|÷10 per kcal|

### Reset Giornaliero

I contatori (steps, distance, calories) si **azzerano a mezzanotte** (basato sull'ora UTC del device).

---

## Checksum Chileaf

```python
def checksum(data):
    """
    Calculate Chileaf protocol checksum
    From SDK: return (byte) (((-result) ^ 58) & 255);
    """
    result = sum(byte & 0xFF for byte in data)
    return ((-result) ^ 0x3A) & 0xFF
```
