# BLE Accelerometer Standalone App - CL837 Device

## 📋 Specifiche Tecniche Device CL837

### BLE Services & Characteristics
```dart
// Service UUID per accelerometro
static const String ACCELEROMETER_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb";

// Characteristic UUID per lettura dati accelerometrici
static const String ACCELEROMETER_DATA_CHARACTERISTIC_UUID = "0000fff1-0000-1000-8000-00805f9b34fb";

// Characteristic UUID per configurazione device
static const String ACCELEROMETER_CONFIG_CHARACTERISTIC_UUID = "0000fff2-0000-1000-8000-00805f9b34fb";
```

### Formato Dati Accelerometrici
Il device CL837 invia pacchetti di **6 bytes**:
```
Byte 0-1: AX (accelerazione asse X) - signed int16, little-endian
Byte 2-3: AY (accelerazione asse Y) - signed int16, little-endian
Byte 4-5: AZ (accelerazione asse Z) - signed int16, little-endian
```

### Conversione Raw → G (forza di gravità)
```dart
// Fattore di conversione da raw value a G
static const double CONVERSION_FACTOR = 4096.0; // 12-bit ADC, ±2g range

double ax = rawAX / CONVERSION_FACTOR; // Risultato in G (-2.0 to +2.0)
double ay = rawAY / CONVERSION_FACTOR;
double az = rawAZ / CONVERSION_FACTOR;