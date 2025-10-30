# CL837 BLE Accelerometer Monitor

Real-time monitoring and visualization tool for CL837 accelerometer devices using Chileaf BLE protocol.

## Features

- **Multi-device Support**: Interactive selection when multiple CL837 devices are detected
- **Real-time Oscilloscope**: 4-panel visualization (XYZ, Magnitude, XY-View, Live Stats)
- **Low-latency Processing**: Optimized BLE handling with ~50-150ms response time
- **Chileaf Protocol**: Native support for CL837 protocol (0x0C command frames)
- **Smart Filtering**: Automatic rejection of non-accelerometer frames (0x38, 0x15, 0x75)
- **Live Statistics**: Sample count, frequency, spike detection, device info

## Visualizations

1. **XYZ Acceleration Plot**: Real-time 3-axis accelerometer data
2. **Magnitude Plot**: Total acceleration magnitude over time  
3. **XY Top View**: 2D visualization from above (gravity plane)
4. **Live Statistics**: Device info, sampling frequency, data quality metrics

## Installation

### Prerequisites
- Python 3.8+
- Windows 10 1903+ / macOS 10.15+ / Linux with BlueZ

### Setup
```bash
# Clone the repository
git clone https://github.com/paoloartasensi/python_bt.git
cd python_bt

# Install dependencies
pip install -r requirements.txt

# Run the monitor
python cl837_unified.py
```

## Usage

1. **Power on** your CL837 device
2. **Run the script**: `python cl837_unified.py`
3. **Select device** from the interactive menu (if multiple found)
4. **Monitor data** in real-time console and oscilloscope
5. **Stop monitoring** with `Ctrl+C`

### Sample Output
```
CL837 UNIFIED ACCELEROMETER MONITOR
Connessione + Monitor Console + Oscilloscopio Real-Time
======================================================================
Ricerca dispositivi CL837...
Trovati 2 dispositivi CL837:
   1. CL837-0758807 (CB:AB:D2:0D:2B:E7)  
   2. CL837-1234567 (AA:BB:CC:DD:EE:FF)

Seleziona dispositivo (1-2) o 'q' per uscire:
> 1

[DATA] # 1500 | X:+0.094 Y:+0.000 Z:+0.938 | Mag:0.942g | 25.3Hz
```

## Technical Details

### CL837 Protocol
- **Service UUID**: `aae28f00-71b5-42a1-8c3c-f9cf6ac969d0`
- **TX Characteristic**: `aae28f01-71b5-42a1-8c3c-f9cf6ac969d0`  
- **Data Format**: 6-byte frames (3×int16 little-endian)
- **Conversion**: Raw values ÷ 4096.0 = g-force
- **Frequency**: ~20-30Hz (device-dependent)

### Data Spikes Explanation

The CL837 device uses the **Chileaf protocol** which transmits multiple types of data frames over the same BLE characteristic. **Spikes** in accelerometer data were initially observed due to:

#### **Root Cause Analysis**
- **Mixed Protocol Frames**: CL837 sends different command frames (0x38, 0x15, 0x75) alongside accelerometer data (0x0C)
- **Protocol Multiplexing**: All frame types use the same BLE notification channel
- **False Parsing**: Non-accelerometer frames were incorrectly interpreted as sensor data

#### **Current Solution** 
```python
# Strict filtering - only accelerometer frames (0x0C)
if command == self.CHILEAF_CMD_ACCELEROMETER:
    return self.parse_multi_sample_frame(data)
else:
    # Ignore non-accelerometer frames silently
    return False
```

#### **Frame Types Observed**
- **0x0C**: Accelerometer data (6-byte samples: X, Y, Z axes)
- **0x38**: Device status/configuration frames (ignored)
- **0x15**: Battery/system information (ignored)  
- **0x75**: Firmware/diagnostic data (ignored)

#### **Result**
With proper protocol filtering, **spikes are eliminated** and only clean accelerometer data is processed. Any remaining spikes indicate genuine hardware issues (sensor malfunction, extreme G-forces >50g, etc.).

### Performance
- **Latency**: 50-150ms typical (BLE + processing)
- **Throughput**: Up to 30 samples/second
- **Buffer Size**: 300 samples (~12 seconds at 25Hz)
- **Visualization**: 25Hz refresh rate with blitting optimization
- **Spike Rate**: <0.01% with proper filtering (hardware-only issues)

## Project Structure

```
python_bt/
├── cl837_unified.py          # Main application
├── requirements.txt          # Python dependencies  
├── documentation/           
│   ├── info.md              # Technical specifications
│   ├── info_acc.txt         # Accelerometer details
│   └── Chileaf BLE Protocol_v0.6-EN.docx.pdf
└── README.md                # This file
```

## Troubleshooting

### Common Issues

**"No CL837 devices found"**
- Ensure device is powered and in pairing mode
- Check Bluetooth is enabled on your system
- Try moving closer to the device

**"Connection failed"**  
- Device may be connected to another application
- Restart the CL837 device
- Clear Bluetooth cache (Windows: Device Manager)

**Low sampling frequency**
- Check RF environment (WiFi interference)
- Reduce distance to device
- Close other Bluetooth applications

**Accelerometer spikes in data**
- **Normal behavior**: Mixed protocol frames (0x38, 0x15, 0x75) are automatically filtered
- **Hardware spikes**: Values >50g indicate genuine sensor malfunction
- **Check connections**: Loose wiring or low battery can cause erratic readings
- **Environmental**: Strong vibrations or magnetic fields may affect readings

**Too many rejected frames**
- Expected: ~70% frames are non-accelerometer (normal protocol behavior)
- Monitor console for "Frame Chileaf ignorato" messages (should be silent in current version)
- If excessive: Check for firmware compatibility or device malfunction

### Debug Mode
Add verbose logging by modifying the notification handler:
```python
def notification_handler(self, sender, data):
    print(f"Raw data: {data.hex().upper()}")  # Debug line
    self.parse_chileaf_data(data)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes  
4. Push to the branch
5. Create a Pull Request

## License

This project is open source. See the repository for license details.

## Related

- [Bleak BLE Library](https://github.com/hbldh/bleak)
- [Matplotlib Documentation](https://matplotlib.org/)
- [CL837 Device Manual](documentation/)