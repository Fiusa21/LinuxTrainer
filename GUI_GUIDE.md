# 🖥️ LinuxTrainer GUI Guide

Your LinuxTrainer now has **3 different GUI options**! Choose the one that works best for you.

## 🚀 Quick Start (Recommended)

**Easiest way to get started:**

```bash
python3 start_gui.py
```

This will automatically find an available port and start the web GUI. Then open your browser to the displayed URL.

## 🎯 Available GUI Options

### 1. **Web GUI** 🌐 (Recommended)
Modern, responsive web interface that works in any browser.

**Features:**
- ✅ Real-time data display (Power, Cadence, Speed, Duration)
- ✅ Beautiful, modern design with dark theme
- ✅ Responsive layout (works on desktop, tablet, mobile)
- ✅ Live activity log
- ✅ One-click connect/disconnect
- ✅ Start/stop training sessions
- ✅ Export data functionality
- ✅ Works on any device with a web browser

**How to run:**
```bash
# Smart launcher (finds available port)
python3 start_gui.py

# Manual launcher
python3 web_gui.py

# Via CLI
python3 cli.py gui --type web
```

**Access:** Open your browser to the displayed URL (usually `http://127.0.0.1:8080`)

### 2. **Tkinter GUI** 🖼️
Native desktop application using Python's built-in Tkinter.

**Features:**
- ✅ Native desktop application
- ✅ Real-time data display
- ✅ Activity log
- ✅ Training session management
- ✅ Data export

**How to run:**
```bash
# Start Tkinter GUI
python3 gui.py

# Via CLI
python3 cli.py gui --type tkinter
```

### 3. **Command Line Interface** 💻
Text-based interface for terminal users.

**Features:**
- ✅ All functionality available
- ✅ Perfect for scripting and automation
- ✅ Lightweight and fast

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

## 🎨 Web GUI Features

The web GUI features a beautiful, modern interface:

- **Dark theme** with blue gradient background
- **Real-time data cards** showing Power, Cadence, Speed, Duration
- **Status indicators** for connection and training state
- **Control buttons** for all operations
- **Activity log** with timestamped messages
- **Responsive design** that works on all screen sizes
- **Mobile-friendly** - works great on phones and tablets

## 📱 Mobile Support

The Web GUI is fully responsive and works great on:
- 🖥️ Desktop computers
- �� Mobile phones
- 📱 Tablets
- 🖥️ Any device with a modern web browser

Just start the web GUI and open the URL on any device on your network!

## 🔧 Requirements

### Web GUI
- Flask: `pip install flask`
- Modern web browser

### Tkinter GUI
- Python with Tkinter (usually included)
- No additional dependencies

### CLI
- No additional dependencies

## 🛠️ Troubleshooting

### Web GUI Issues
- **Port already in use**: Use `python3 start_gui.py` (finds free port automatically)
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

## 📊 Features Comparison

| Feature | Web GUI | Tkinter GUI | CLI |
|---------|---------|-------------|-----|
| Real-time data | ✅ | ✅ | ✅ |
| Modern design | ✅ | ❌ | ❌ |
| Mobile friendly | ✅ | ❌ | ❌ |
| Native desktop | ❌ | ✅ | ❌ |
| Easy to use | ✅ | ✅ | ⚠️ |
| No dependencies | ❌ | ✅ | ✅ |
| Auto port finding | ✅ | N/A | N/A |

## 🚀 Getting Started

1. **Start the web GUI:**
   ```bash
   python3 start_gui.py
   ```

2. **Open your browser** to the displayed URL

3. **Connect to your Kickr:**
   - Click "Connect to Kickr"
   - Wait for connection

4. **Start training:**
   - Click "Start Training"
   - Start pedaling!

5. **View real-time data:**
   - Power, Cadence, Speed, Duration
   - Live activity log

6. **Export data when done:**
   - Click "Export Data"
   - Choose format (CSV, JSON, TCX)

## 🎉 Success!

Your LinuxTrainer now has a complete, professional GUI interface! 

- **Web GUI**: Modern, responsive, works everywhere
- **Tkinter GUI**: Native desktop application
- **CLI**: Full command-line interface

Choose the interface that works best for you and start training! 🚴‍♂️💪

---

**Happy Training! 🚴‍♂️💪**
