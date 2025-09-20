"""
GUI interface for LinuxTrainer using Tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from devices.kickr_trainer import KickrTrainer
from core.models import PowerData, DeviceInfo, DeviceType
from core.session_manager import SessionManager
from core.data_export import DataExporter
from loguru import logger


class LinuxTrainerGUI:
    """Main GUI application for LinuxTrainer"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LinuxTrainer - Indoor Training Application")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Application state
        self.kickr: Optional[KickrTrainer] = None
        self.session_manager = SessionManager()
        self.data_exporter = DataExporter()
        self.current_session = None
        self.is_connected = False
        self.is_training = False
        
        # Data variables
        self.power_var = tk.StringVar(value="0 W")
        self.cadence_var = tk.StringVar(value="0 RPM")
        self.speed_var = tk.StringVar(value="0.0 km/h")
        self.duration_var = tk.StringVar(value="00:00:00")
        self.data_count_var = tk.StringVar(value="0")
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        
        # Start async loop in thread
        self.loop = None
        self.thread = None
        
    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='white', background='#2b2b2b')
        style.configure('Data.TLabel', font=('Arial', 24, 'bold'), foreground='#00ff00', background='#2b2b2b')
        style.configure('Info.TLabel', font=('Arial', 12), foreground='white', background='#2b2b2b')
        style.configure('Status.TLabel', font=('Arial', 10), foreground='#ffff00', background='#2b2b2b')
        
        # Button styles
        style.configure('Connect.TButton', font=('Arial', 12, 'bold'))
        style.configure('Start.TButton', font=('Arial', 12, 'bold'), foreground='green')
        style.configure('Stop.TButton', font=('Arial', 12, 'bold'), foreground='red')
        
    def create_widgets(self):
        """Create GUI widgets"""
        # Main title
        self.title_label = ttk.Label(self.root, text="LinuxTrainer", style='Title.TLabel')
        
        # Connection frame
        self.connection_frame = ttk.Frame(self.root)
        self.connect_button = ttk.Button(self.connection_frame, text="Connect to Kickr", 
                                       command=self.connect_to_kickr, style='Connect.TButton')
        self.status_label = ttk.Label(self.connection_frame, text="Not Connected", style='Status.TLabel')
        
        # Data display frame
        self.data_frame = ttk.Frame(self.root)
        
        # Power display
        self.power_label = ttk.Label(self.data_frame, text="Power", style='Info.TLabel')
        self.power_value = ttk.Label(self.data_frame, textvariable=self.power_var, style='Data.TLabel')
        
        # Cadence display
        self.cadence_label = ttk.Label(self.data_frame, text="Cadence", style='Info.TLabel')
        self.cadence_value = ttk.Label(self.data_frame, textvariable=self.cadence_var, style='Data.TLabel')
        
        # Speed display
        self.speed_label = ttk.Label(self.data_frame, text="Speed", style='Info.TLabel')
        self.speed_value = ttk.Label(self.data_frame, textvariable=self.speed_var, style='Data.TLabel')
        
        # Duration display
        self.duration_label = ttk.Label(self.data_frame, text="Duration", style='Info.TLabel')
        self.duration_value = ttk.Label(self.data_frame, textvariable=self.duration_var, style='Data.TLabel')
        
        # Control frame
        self.control_frame = ttk.Frame(self.root)
        self.start_button = ttk.Button(self.control_frame, text="Start Training", 
                                     command=self.start_training, style='Start.TButton')
        self.stop_button = ttk.Button(self.control_frame, text="Stop Training", 
                                    command=self.stop_training, style='Stop.TButton')
        self.export_button = ttk.Button(self.control_frame, text="Export Data", 
                                      command=self.export_data)
        
        # Log frame
        self.log_frame = ttk.Frame(self.root)
        self.log_label = ttk.Label(self.log_frame, text="Activity Log", style='Info.TLabel')
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=8, width=70, 
                                                bg='#1e1e1e', fg='#00ff00', font=('Courier', 9))
        
        # Stats frame
        self.stats_frame = ttk.Frame(self.root)
        self.stats_label = ttk.Label(self.stats_frame, text="Session Statistics", style='Info.TLabel')
        self.data_count_label = ttk.Label(self.stats_frame, text="Data Points: ", style='Info.TLabel')
        self.data_count_value = ttk.Label(self.stats_frame, textvariable=self.data_count_var, style='Info.TLabel')
        
    def setup_layout(self):
        """Setup widget layout"""
        # Title
        self.title_label.pack(pady=10)
        
        # Connection frame
        self.connection_frame.pack(pady=10)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Data display frame
        self.data_frame.pack(pady=20)
        
        # Power row
        power_row = ttk.Frame(self.data_frame)
        power_row.pack(pady=5)
        self.power_label.pack(side=tk.LEFT, padx=10)
        self.power_value.pack(side=tk.LEFT, padx=10)
        
        # Cadence row
        cadence_row = ttk.Frame(self.data_frame)
        cadence_row.pack(pady=5)
        self.cadence_label.pack(side=tk.LEFT, padx=10)
        self.cadence_value.pack(side=tk.LEFT, padx=10)
        
        # Speed row
        speed_row = ttk.Frame(self.data_frame)
        speed_row.pack(pady=5)
        self.speed_label.pack(side=tk.LEFT, padx=10)
        self.speed_value.pack(side=tk.LEFT, padx=10)
        
        # Duration row
        duration_row = ttk.Frame(self.data_frame)
        duration_row.pack(pady=5)
        self.duration_label.pack(side=tk.LEFT, padx=10)
        self.duration_value.pack(side=tk.LEFT, padx=10)
        
        # Control frame
        self.control_frame.pack(pady=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Stats frame
        self.stats_frame.pack(pady=10)
        self.stats_label.pack()
        stats_row = ttk.Frame(self.stats_frame)
        stats_row.pack()
        self.data_count_label.pack(side=tk.LEFT)
        self.data_count_value.pack(side=tk.LEFT)
        
        # Log frame
        self.log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        self.log_label.pack()
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def connect_to_kickr(self):
        """Connect to Kickr device"""
        def connect_async():
            try:
                self.root.after(0, lambda: self.log_message("Scanning for Kickr devices..."))
                
                # Run async code in thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Scan for devices
                devices = loop.run_until_complete(KickrTrainer.scan_for_devices(timeout=10.0))
                
                if not devices:
                    self.root.after(0, lambda: self.log_message("No Kickr devices found!"))
                    return
                
                device_info = devices[0]
                self.root.after(0, lambda: self.log_message(f"Found: {device_info.name}"))
                
                # Create Kickr instance
                self.kickr = KickrTrainer(device_info)
                self.kickr.add_data_callback(self.on_power_data)
                
                # Connect
                success = loop.run_until_complete(self.kickr.connect())
                
                if success:
                    self.root.after(0, self.on_connected)
                    self.loop = loop
                    # Keep loop running
                    loop.run_forever()
                else:
                    self.root.after(0, lambda: self.log_message("Failed to connect to Kickr"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Connection error: {e}"))
        
        # Start connection in thread
        self.thread = threading.Thread(target=connect_async, daemon=True)
        self.thread.start()
        
    def on_connected(self):
        """Handle successful connection"""
        self.is_connected = True
        self.status_label.config(text="Connected", foreground="green")
        self.connect_button.config(text="Disconnect", command=self.disconnect_from_kickr)
        self.log_message("Successfully connected to Kickr!")
        
    def disconnect_from_kickr(self):
        """Disconnect from Kickr"""
        if self.kickr and self.is_connected:
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
            self.is_connected = False
            self.status_label.config(text="Not Connected", foreground="yellow")
            self.connect_button.config(text="Connect to Kickr", command=self.connect_to_kickr)
            self.log_message("Disconnected from Kickr")
            
    def on_power_data(self, power_data: PowerData):
        """Handle incoming power data"""
        # Update GUI variables (thread-safe)
        self.root.after(0, lambda: self.power_var.set(f"{power_data.instantaneous_power} W"))
        
        if power_data.cadence is not None:
            self.root.after(0, lambda: self.cadence_var.set(f"{power_data.cadence} RPM"))
        else:
            self.root.after(0, lambda: self.cadence_var.set("-- RPM"))
            
        if power_data.speed is not None:
            self.root.after(0, lambda: self.speed_var.set(f"{power_data.speed:.1f} km/h"))
        else:
            self.root.after(0, lambda: self.speed_var.set("-- km/h"))
            
        # Update data count
        if hasattr(self.kickr, 'data_count'):
            self.root.after(0, lambda: self.data_count_var.set(str(self.kickr.data_count)))
            
    def start_training(self):
        """Start training session"""
        if not self.is_connected:
            messagebox.showerror("Error", "Please connect to Kickr first!")
            return
            
        if self.is_training:
            messagebox.showwarning("Warning", "Training already in progress!")
            return
            
        try:
            # Start new session
            device_info = DeviceInfo(
                address=self.kickr.device_info.address,
                name=self.kickr.device_info.name,
                device_type=DeviceType.SMART_TRAINER
            )
            self.current_session = self.session_manager.start_session(device_info)
            
            self.is_training = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            self.log_message("Training session started!")
            
            # Start duration timer
            self.start_time = datetime.now()
            self.update_duration()
            
        except Exception as e:
            self.log_message(f"Error starting training: {e}")
            messagebox.showerror("Error", f"Failed to start training: {e}")
            
    def stop_training(self):
        """Stop training session"""
        if not self.is_training:
            messagebox.showwarning("Warning", "No training session in progress!")
            return
            
        try:
            # End session
            if self.current_session:
                self.session_manager.end_session()
                self.log_message("Training session ended!")
                
            self.is_training = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
        except Exception as e:
            self.log_message(f"Error stopping training: {e}")
            messagebox.showerror("Error", f"Failed to stop training: {e}")
            
    def update_duration(self):
        """Update duration display"""
        if self.is_training and hasattr(self, 'start_time'):
            duration = datetime.now() - self.start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.duration_var.set(f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
            
        # Schedule next update
        if self.is_training:
            self.root.after(1000, self.update_duration)
            
    def export_data(self):
        """Export training data"""
        if not self.current_session:
            messagebox.showwarning("Warning", "No training session to export!")
            return
            
        try:
            # Export data
            exports = self.data_exporter.export_all_formats(self.current_session)
            
            message = "Data exported successfully!\n\n"
            for format_type, filepath in exports.items():
                message += f"{format_type.upper()}: {filepath}\n"
                
            messagebox.showinfo("Export Complete", message)
            self.log_message("Data exported successfully!")
            
        except Exception as e:
            self.log_message(f"Export error: {e}")
            messagebox.showerror("Error", f"Failed to export data: {e}")
            
    def run(self):
        """Start the GUI application"""
        self.log_message("LinuxTrainer GUI started")
        self.root.mainloop()


def main():
    """Main entry point for GUI"""
    app = LinuxTrainerGUI()
    app.run()


if __name__ == "__main__":
    main()
