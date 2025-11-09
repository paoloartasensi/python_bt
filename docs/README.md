# Documentation Overview

Documentazione completa del progetto CL837 BLE Monitor.

## Documentazione Principale

### Analisi Dispositivo
- **[CL837_CAPABILITIES.md](CL837_CAPABILITIES.md)** - Analisi delle capacità hardware del CL837 e limitazioni
- **[SDK_COMPARISON_ANALYSIS.md](SDK_COMPARISON_ANALYSIS.md)** - Confronto tra SDK Android e iOS
- **[SLEEP_DATA_README.md](SLEEP_DATA_README.md)** - Formato e analisi dati sonno

## Documentazione Tecnica

### Protocollo Chileaf
- **[Chileaf BLE Protocol_v0.6-EN.docx.pdf](Chileaf%20BLE%20Protocol_v0.6-EN%20.docx.pdf)** - Protocollo BLE ufficiale
- **[info.md](info.md)** - Note tecniche sul protocollo
- **[info_acc.txt](info_acc.txt)** - Specifiche accelerometro

### SDK Android
- **[docs/CL831SE_Android_SDK_V3.0.4/](docs/CL831SE_Android_SDK_V3.0.4/)** - SDK Android completo
  - Codice Java di riferimento
  - Esempi DFU (Device Firmware Update)
  - Layout e risorse Android

### File Tecnici
- **[classes.dex](classes.dex)** - File DEX Android per analisi reverse engineering
- **[from_CL831_sdk_app.jpeg](from_CL831_sdk_app.jpeg)** - Screenshot app SDK

## Temi Principali

### 1. Limitazioni Hardware CL837
Il CL837 è un modello entry-level che **non supporta** alcune funzionalità presenti negli SDK:
- Storico HR/RR (comandi 0x21, 0x22, 0x24, 0x25)
- Alcune modalità avanzate di sleep tracking

Vedi: [CL837_CAPABILITIES.md](CL837_CAPABILITIES.md)

### 2. Protocollo BLE Chileaf
- Header: `0xFF`
- Servizio UUID: `aae28f00-71b5-42a1-8c3c-f9cf6ac969d0`
- Comando accelerometro: `0x0C`
- Frequenza campionamento: ~25Hz

### 3. DFU (Device Firmware Update)
Il sistema supporta aggiornamento firmware via BLE:
- Comando ingresso DFU: `0xFF 0x04 0x27`
- Utilizza Nordic DFU Library
- Implementazione completa nell'SDK Android

Vedi: `docs/CL831SE_Android_SDK_V3.0.4/CL831_Sample/app/src/main/java/com/chileaf/cl831/sample/dfu/`

## Come Navigare

1. **Per informazioni sul protocollo BLE**: Leggi `info.md` e il PDF del protocollo
2. **Per limitazioni hardware**: Leggi `CL837_CAPABILITIES.md`
3. **Per riferimento codice**: Esplora `docs/CL831SE_Android_SDK_V3.0.4/`
4. **Per dati sonno**: Leggi `SLEEP_DATA_README.md`

## Note

La documentazione è una combinazione di:
- Documentazione ufficiale Chileaf
- Reverse engineering dell'SDK Android
- Analisi sperimentale del dispositivo CL837
- Confronto tra comportamenti iOS e Android
