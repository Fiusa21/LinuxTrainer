# LinuxTrainer

An indoor training application for Linux that connects to smart trainers and cycling devices via Bluetooth Low Energy.

## 🚀 Features

- **Bluetooth Low Energy** device scanning and connection
- **Wahoo Kickr** smart trainer support
- **Real-time data collection** (power, cadence, speed, heart rate)
- **Live display** with beautiful TUI interface
- **Structured workouts** (steady state, intervals, tempo)
- **Data export** (CSV, JSON, TCX formats)
- **Session management** with automatic data persistence
- **Cross-platform** compatibility (Linux, macOS, Windows)

## 📋 Requirements

- Python 3.8+
- Bluetooth Low Energy adapter
- Compatible smart trainer (tested with Wahoo Kickr)

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
python cli.py --help
```

## 🎯 Quick Start

### 1. Scan for Devices
```bash
python cli.py scan
```

### 2. Start a Training Session
```bash
# Free ride with live display
python cli.py train

# Structured workout
python cli.py train --workout steady
python cli.py train --workout intervals
python cli.py train --workout tempo

# Without live display (for headless operation)
python cli.py train --no-display
```

### 3. View Training Sessions
```bash
# List all sessions
python cli.py sessions

# Export session data
python cli.py export <session-id> --format csv
python cli.py export <session-id> --format json
python cli.py export <session-id> --format tcx
python cli.py export <session-id> --format all
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

## 🎮 Available Workouts

| Workout Type | Description | Duration | Target Power |
|--------------|-------------|----------|--------------|
| `steady`     | Steady state ride | 30 min | 200W |
| `intervals`  | High-intensity intervals | ~10 min | 300W work, 150W rest |
| `tempo`      | Tempo ride | 20 min | 250W @ 90 RPM |
| `free`       | Free ride | Unlimited | Your choice |

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

## 🙏 Acknowledgments

- [Bleak](https://github.com/hbldh/bleak) for Bluetooth Low Energy support
- [Rich](https://github.com/Textualize/rich) for beautiful terminal interfaces
- [Wahoo Fitness](https://www.wahoofitness.com/) for excellent smart trainers
