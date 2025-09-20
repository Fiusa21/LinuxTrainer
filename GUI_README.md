# 🖥️ LinuxTrainer GUI Options

LinuxTrainer now supports multiple GUI interfaces! Choose the one that works best for you.

## 🎯 Available GUI Options

### 1. **Web GUI** (Recommended) 🌐
Modern, responsive web interface that works in any browser.

**Features:**
- Real-time data display (Power, Cadence, Speed, Duration)
- Beautiful, modern design with dark theme
- Responsive layout (works on desktop, tablet, mobile)
- Live activity log
- One-click connect/disconnect
- Start/stop training sessions
- Export data functionality

**How to run:**
```bash
# Start web GUI
python3 web_gui.py

# Or via CLI
python3 cli.py gui --type web
```

**Access:** Open your browser and go to `http://127.0.0.1:5000`

### 2. **Tkinter GUI** 🖼️
Native desktop application using Python's built-in Tkinter.

**Features:**
- Native desktop application
- Real-time data display
- Activity log
- Training session management
- Data export

**How to run:**
```bash
# Start Tkinter GUI
python3 gui.py

# Or via CLI
python3 cli.py gui --type tkinter
```

### 3. **Command Line Interface** 💻
Text-based interface for terminal users.

**How to run:**
```bash
# Scan for devices
python3 cli.py scan

# Start training
python3 cli.py train

# Start structured workout
python3 cli.py train --workout steady

# List workouts
python3 cli.py workouts

# Export data
python3 cli.py export <session-id> --format csv
```

## 🚀 Quick Start Guide

### **Option 1: Web GUI (Easiest)**
1. Start the web GUI:
   ```bash
   python3 web_gui.py
   ```
2. Open your browser: `http://127.0.0.1:5000`
3. Click "Connect to Kickr"
4. Click "Start Training"
5. Start pedaling!

### **Option 2: Tkinter GUI**
1. Start the desktop GUI:
   ```bash
   python3 gui.py
   ```
2. Click "Connect to Kickr"
3. Click "Start Training"
4. Start pedaling!

### **Option 3: Command Line**
1. Scan for devices:
   ```bash
   python3 cli.py scan
   ```
2. Start training:
   ```bash
   python3 cli.py train
   ```
3. Press Ctrl+C to stop

## 📊 Features Comparison

| Feature | Web GUI | Tkinter GUI | CLI |
|---------|---------|-------------|-----|
| Real-time data | ✅ | ✅ | ✅ |
| Modern design | ✅ | ❌ | ❌ |
| Mobile friendly | ✅ | ❌ | ❌ |
| Native desktop | ❌ | ✅ | ❌ |
| Easy to use | ✅ | ✅ | ⚠️ |
| No dependencies | ❌ | ✅ | ✅ |

## 🔧 Requirements

### Web GUI
- Flask: `pip install flask`
- Modern web browser

### Tkinter GUI
- Python with Tkinter (usually included)
- No additional dependencies

### CLI
- No additional dependencies

## 🎨 Web GUI Screenshots

The web GUI features:
- **Dark theme** with blue gradient background
- **Real-time data cards** showing Power, Cadence, Speed, Duration
- **Status indicators** for connection and training state
- **Control buttons** for all operations
- **Activity log** with timestamped messages
- **Responsive design** that works on all screen sizes

## 🛠️ Customization

### Web GUI
- Edit `src/ui/templates/index.html` for HTML/CSS changes
- Edit `src/ui/web_gui.py` for backend logic

### Tkinter GUI
- Edit `src/ui/gui.py` for GUI modifications

## 🐛 Troubleshooting

### Web GUI Issues
- **Port already in use**: Change port in `web_gui.py`
- **Can't connect**: Check if Kickr is powered on and in range
- **No data**: Try disconnecting and reconnecting

### Tkinter GUI Issues
- **Import error**: Install tkinter: `sudo apt-get install python3-tk` (Linux)
- **Window not showing**: Check if you're running in a GUI environment

### General Issues
- **No devices found**: Make sure Kickr is powered on and Bluetooth is enabled
- **Connection failed**: Try moving closer to the Kickr or restarting Bluetooth

## 🎯 Recommendations

- **For most users**: Use the **Web GUI** - it's modern, easy to use, and works everywhere
- **For desktop users**: Use the **Tkinter GUI** if you prefer native applications
- **For developers**: Use the **CLI** for scripting and automation

## 📱 Mobile Support

The Web GUI is fully responsive and works great on:
- Desktop computers
- Tablets
- Mobile phones
- Any device with a modern web browser

Just start the web GUI and open the URL on any device on your network!

---

**Happy Training! 🚴‍♂️💪**
