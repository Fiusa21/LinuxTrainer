# LinuxTrainer

An indoor training application for Linux that connects to smart trainers and cycling devices via Bluetooth Low Energy.

## 🚀 Features

- **Bluetooth Low Energy** device scanning and connection
- **Wahoo Kickr** smart trainer support
- **Real-time data collection** (power, cadence, speed, heart rate)
- **Live display** with beautiful TUI interface
- **Structured workouts** (steady state, intervals, tempo)
- **Data export** (CSV, JSON, TCX formats) (fit is wip)
- **Session management** with automatic data persistence
- **Cross-platform** compatibility (Linux, macOS, Windows)

## 📋 Requirements

- Python 3.8+
- Bluetooth Low Energy adapter
- Compatible smart trainer (tested with Wahoo Kickr)

## Dataflow
Frontend (app.js):
powerDataHistory is a client-side only array that stores the last 100 data points
It's used only for client-side statistics display 
It's reset when training starts 
It's NOT sent to the backend during export

Backend Data Flow:
Real-time data collection: on_power_data() method in web_gui.py receives power data from the Kickr trainer
Session storage: Data is stored in self.current_session via self.session_manager.add_power_data(power_data) 
Export process: When /api/export is called (lines 214-228 in web_gui.py), 
it exports self.current_session data, not the frontend powerDataHistory

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd LinuxTrainer
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python start_gui.py 
```

## 🎯 Quick Start

### 1. Scan for Devices (OPTIONAL)
```bash
python cli.py scan
```

### 2. Start a Training Session
```bash
# Free ride with live display
python start_gui.py 

```

### 3. View Training Sessions
```bash

```

## 🏗️ Project Structure

```
LinuxTrainer/
├── src/
│   ├── core/                    # Core application logic
│   │   ├── base_device.py       # Base class for BLE devices
│   │   ├── constants.py         # BLE UUIDs and constants
│   │   ├── models.py           # Data models
│   │   ├── session_manager.py   # Training session management
│   │   ├── data_export.py       # Data export functionality
│   │   └── workout.py          # Workout management
│   ├── devices/                 # Device-specific implementations
│   │   ├── kickr_trainer.py     # Wahoo Kickr implementation
│   │   └── ...                  # Other device implementations
│   ├── ui/                      # User interface components
│   │   └── live_display.py      # Real-time display
│   └── main.py                  # Main application
├── tests/                       # Unit tests
├── cli.py                       # Command-line interface
├── requirements.txt             # Dependencies
└── README.md                    # This file
```


## 📊 Data Export Formats

- **CSV**: Spreadsheet-compatible format with timestamped data
- **JSON**: Structured data with session metadata
- **TCX**: Garmin Training Center XML format for fitness apps

## 🔧 Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Adding New Devices
1. Create a new device class in `src/devices/`
2. Inherit from `BaseDevice`
3. Implement required methods
4. Add device-specific UUIDs to `constants.py`

### Adding New Workouts
1. Create workout functions in `src/core/workout.py`
2. Add workout type to CLI options
3. Update workout executor logic

## 🐛 Troubleshooting

### Bluetooth Issues
- Ensure Bluetooth is enabled
- Check device permissions
- Try restarting Bluetooth service
- On Linux: `sudo systemctl restart bluetooth`

### Connection Problems
- Make sure device is in pairing mode
- Check if device is already connected elsewhere
- Try scanning multiple times: `python cli.py scan`

### Permission Issues
- On Linux, you may need to add user to `bluetooth` group
- On macOS, grant Bluetooth permissions in System Preferences

## 📈 Roadmap

- [ ] Live average Power data
- [ ] Live data graph
- [ ] More data during active sessions
- [ ] Start screen implementation (current version dummy only)
- [ ] Heart rate monitor support
- [ ] Multiple device support
- [ ] Web interface
- [ ] Strava integration
- [ ] Zwift compatibility
- [ ] Advanced workout builder
- [ ] Data visualization
- [ ] Mobile app companion

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

[Add your license here]


