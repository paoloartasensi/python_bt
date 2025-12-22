# Temperature - CL837/CL831

## Panoramica

Il dispositivo CL837/CL831 supporta la misurazione di **tre tipi di temperatura**:

1. **Environment Temperature** - Temperatura ambientale
2. **Wrist Temperature** - Temperatura del polso (sensore a contatto)
3. **Body Temperature** - Temperatura corporea (stimata)

La temperatura viene ottenuta tramite il **protocollo Chileaf proprietario** (comando `0x38`).

---

## Protocollo BLE

### Servizio e Caratteristica

|Campo|Valore|
|-------|--------|
|Service UUID|`AAE28F00-71B5-42A1-8C3C-F9CF6AC969D0`|
|TX Characteristic|`AAE28F01-71B5-42A1-8C3C-F9CF6AC969D0` (NOTIFY)|
|RX Characteristic|`AAE28F02-71B5-42A1-8C3C-F9CF6AC969D0` (WRITE)|

---

## Comando Temperature (0x38)

### Formato Notifica

Il device invia automaticamente dati temperatura tramite notifiche con comando `0x38`:

```text
[FF] [len] [38] [env_h] [env_l] [wrist_h] [wrist_l] [body_h] [body_l] [checksum]

Offset  Bytes  Campo              Tipo       Descrizione
0       1      Header             uint8      0xFF
1       1      Length             uint8      Lunghezza pacchetto
2       1      Command            uint8      0x38 (Temperature)
3-4     2      Environment Temp   uint16 BE  Temperatura ambiente × 10
5-6     2      Wrist Temp         uint16 BE  Temperatura polso × 10
7-8     2      Body Temp          uint16 BE  Temperatura corpo × 10
9       1      Checksum           uint8      Checksum Chileaf
```

### Conversione Temperatura

I valori sono **interi moltiplicati per 10**. Per ottenere la temperatura in °C:

```python
# Da raw a gradi Celsius
temp_celsius = raw_value / 10.0

# Esempio: raw = 365
# temp = 365 / 10.0 = 36.5 °C
```

### Esempio Parsing

```python
def parse_temperature(data):
    """
    Parse temperature notification from Chileaf protocol
    data: bytes from notification
    """
    if len(data) < 9 or data[0] != 0xFF or data[2] != 0x38:
        return None
    
    # Big-endian 2-byte integers
    env_raw = (data[3] << 8) | data[4]
    wrist_raw = (data[5] << 8) | data[6]
    body_raw = (data[7] << 8) | data[8]
    
    return {
        'environment': env_raw / 10.0,  # °C
        'wrist': wrist_raw / 10.0,       # °C
        'body': body_raw / 10.0          # °C
    }
```

---

## Riferimenti SDK

### iOS (HeartBLEDevice.m)

```objectivec
else if (buffer_[2] == 0x38) {
    // (单位：10℃) 温度数据数值扩大了10倍
    int environmentTemp = [self bytes2ToInt:buffer_[3] byte2:buffer_[4]];
    int wristTemp = [self bytes2ToInt:buffer_[5] byte2:buffer_[6]];
    int bodyTemp = [self bytes2ToInt:buffer_[7] byte2:buffer_[8]];
    
    if ([theDelegate respondsToSelector:@selector(SDKGetRealTimeTemp:wrist:body:)]) {
        [theDelegate SDKGetRealTimeTemp:environmentTemp/10.0 
                                  wrist:wristTemp/10.0 
                                   body:bodyTemp/10.0];
    }
}
```

### Android (WearReceivedDataCallback.java)

```java
// iIntValue == 56 means command 0x38 (56 decimal = 0x38 hex)
if (iIntValue == 56) {
    onTemperatureReceived(
        bluetoothDevice,
        getIntParse(value, 3, 2) / 10.0f,  // environment
        getIntParse(value, 5, 2) / 10.0f,  // wrist
        getIntParse(value, 7, 2) / 10.0f   // body
    );
    return;
}
```

### Callback Interface (Android)

```java
public interface TemperatureCallback {
    void onTemperatureReceived(
        BluetoothDevice device,
        float environment,  // °C
        float wrist,        // °C
        float body          // °C
    );
}
```

---

## Tipi di Temperatura

|Tipo|Descrizione|Range Tipico|
|------|-------------|--------------|
| **Environment** |Temperatura dell'aria circostante|15-35 °C|
| **Wrist** |Temperatura cutanea del polso|28-35 °C|
| **Body** |Temperatura corporea stimata|35-38 °C|

### Nota sulla Body Temperature

La temperatura corporea (`body`) è una **stima** calcolata dal device basandosi sulla temperatura del polso e algoritmi di compensazione. Non è una misurazione diretta (come un termometro orale/auricolare).

---

## Frequenza di Aggiornamento

- Il device invia notifiche temperatura **ogni ~15 secondi** circa
- Non è necessario inviare comandi per riceverle
- Basta abilitare le notifiche sulla caratteristica TX

---

## Note Tecniche

### Limitazioni

- La precisione dipende dal contatto sensore-pelle
- Il movimento può influenzare le letture
- L'ambiente (sole diretto, aria condizionata) influenza `environment` e `wrist`

### Best Practices

1. Assicurarsi che il sensore sia a contatto con la pelle
2. Attendere 2-3 minuti dopo aver indossato il device per letture stabili
3. Evitare misurazioni durante attività fisica intensa
4. Per temperatura corporea accurata, misurare a riposo

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
