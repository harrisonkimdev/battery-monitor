# 🔋 Battery Monitor

A comprehensive battery monitoring tool for macOS - Open source alternative to CoconutBattery

## ✨ Key Features

### 🖥️ macOS Battery Monitoring
- **Real-time Battery Info**: Current charge, health percentage, cycle count, temperature, voltage
- **Power Management**: Low Power Mode detection, charging status, time remaining
- **Hardware Details**: Model identifier, serial number, firmware version
- **Technical Data**: Design capacity vs current capacity, manufacture date, battery age

### 📱 iOS Device Support
- **Connected iPhone/iPad**: Battery info using MobileDevice.framework and libimobiledevice
- **Device Information**: Model, iOS version, serial number, storage capacity
- **Battery Metrics**: Charge percentage, health, cycles, temperature
- **Connection Status**: USB connection type, charging power

### 📊 Advanced History Tracking
- **Timeline History**: Complete battery history with SQLite database
- **Interactive Charts**: Battery health and cycle trends visualization
- **Monthly Summaries**: Average health and cycle statistics by month
- **Multi-device Support**: Separate tracking for Mac and iOS devices
- **Smart Backup**: Automatic backup with JSON export capability
- **Trend Analysis**: Health degradation patterns and predictions

### 🎨 User Interface
- **Modern GUI**: Clean, intuitive graphical interface
- **History Viewer**: Advanced charts with matplotlib integration
- **Real-time Updates**: Auto-refresh with configurable intervals
- **CLI Version**: Terminal-based version for automation

## 🚀 Usage

### GUI Version (Recommended)
```bash
python3 battery_monitor_gui.py
```

### History Viewer (Standalone)
```bash
python3 history_viewer.py
```

### CLI Version
```bash
python3 battery_monitor.py
```

## 📱 iOS Device Support

This app uses the same methods as CoconutBattery to retrieve iOS device battery information:

1. **MobileDevice.framework** (Priority): Direct use of Apple's private framework
2. **libimobiledevice** (Alternative): Install with `brew install libimobiledevice`
3. **system_profiler** (Basic): Limited but basic device detection

### Connecting iOS Devices
1. Connect your iOS device to Mac using Lightning/USB-C cable
2. Select "Trust" when prompted "Trust this computer?"
3. Run Battery Monitor

## 🏗️ Building Native App

To create a macOS native application:

1. Install py2app:
   ```bash
   pip3 install py2app
   ```

2. Build app bundle:
   ```bash
   python3 setup.py py2app
   ```

3. The generated app will be in `dist/Battery Monitor.app`

## 📦 Dependencies

```bash
pip3 install matplotlib pandas
```

## 📋 System Requirements

- macOS 10.15 Catalina or later
- Python 3.7 or later
- Tkinter (included with Python by default)

## 🔧 Technical Details

### macOS Battery Information
- `system_profiler SPPowerDataType`: Basic battery information
- `ioreg -rc AppleSmartBattery`: Detailed technical information

### iOS Battery Information
- **MobileDevice.framework**: Direct calls to Apple's private API
  - `AMDeviceNotificationSubscribe`: Device connection monitoring
  - `AMDeviceConnect`: Device connection
  - `AMDeviceCopyValue`: Battery information extraction
- **ctypes**: Python C library calls
- **CoreFoundation**: Apple object parsing

## 📊 Display Information

### macOS Battery
- Current charge level (%)
- Charge status (Charging/Charged/Battery)
- Time remaining
- Cycle count
- Battery health (%)
- Design/Current/Max capacity (mAh)
- Voltage (V) / Current (mA)

### iOS Devices
- Device name, model, iOS version
- Battery charge level (%)
- Charging status
- Voltage
- Connection type

## ⚠️ Important Notes

- iOS battery information uses Apple's private APIs and may not work with future macOS updates
- Some features may require administrator privileges
- MobileDevice.framework is a developer-only documented API and may behave unexpectedly

## 📄 License

MIT License - Free to use, modify, and distribute

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## 🐛 Bug Reports / Feature Requests

Please report bugs or request new features at [GitHub Issues](https://github.com/harrisonkim/battery-monitor/issues).

---

Created as an open source alternative to **CoconutBattery**. 💚
