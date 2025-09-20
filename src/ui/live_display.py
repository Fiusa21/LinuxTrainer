"""
Real-time live display for training data
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from ..core.models import PowerData, HeartRateData, TrainingSession


class LiveDisplay:
    """Real-time display for training data"""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.session: Optional[TrainingSession] = None
        self.current_power: Optional[PowerData] = None
        self.current_hr: Optional[HeartRateData] = None
        self.start_time: Optional[datetime] = None
        self.running = False
        
    def set_session(self, session: TrainingSession):
        """Set the current training session"""
        self.session = session
        self.start_time = session.start_time
        
    def update_power_data(self, power_data: PowerData):
        """Update current power data"""
        self.current_power = power_data
        
    def update_heart_rate_data(self, hr_data: HeartRateData):
        """Update current heart rate data"""
        self.current_hr = hr_data
        
    def _create_layout(self):
        """Create the display layout"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        self.layout["left"].split_column(
            Layout(name="power_panel"),
            Layout(name="hr_panel")
        )
        
        self.layout["right"].split_column(
            Layout(name="session_panel"),
            Layout(name="stats_panel")
        )
        
    def _render_header(self) -> Panel:
        """Render the header panel"""
        title = Text("LinuxTrainer - Live Training Session", style="bold blue")
        return Panel(Align.center(title), style="blue")
        
    def _render_power_panel(self) -> Panel:
        """Render the power data panel"""
        if not self.current_power:
            content = Text("Waiting for power data...", style="dim")
        else:
            table = Table(show_header=False, box=None)
            table.add_column(style="cyan", width=20)
            table.add_column(style="white", width=10)
            
            table.add_row("Power", f"{self.current_power.instantaneous_power}W")
            if self.current_power.cadence:
                table.add_row("Cadence", f"{self.current_power.cadence} RPM")
            if self.current_power.speed:
                table.add_row("Speed", f"{self.current_power.speed:.1f} km/h")
                
            content = table
            
        return Panel(content, title="Power Data", border_style="green")
        
    def _render_hr_panel(self) -> Panel:
        """Render the heart rate panel"""
        if not self.current_hr:
            content = Text("No heart rate data", style="dim")
        else:
            content = Text(f"{self.current_hr.heart_rate} BPM", style="red bold")
            
        return Panel(content, title="Heart Rate", border_style="red")
        
    def _render_session_panel(self) -> Panel:
        """Render the session info panel"""
        if not self.session:
            content = Text("No active session", style="dim")
        else:
            table = Table(show_header=False, box=None)
            table.add_column(style="cyan", width=15)
            table.add_column(style="white", width=15)
            
            table.add_row("Session ID", self.session.session_id[:8] + "...")
            table.add_row("Device", self.session.device_info.name if self.session.device_info else "Unknown")
            
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                table.add_row("Elapsed", str(elapsed).split('.')[0])
                
            content = table
            
        return Panel(content, title="Session Info", border_style="blue")
        
    def _render_stats_panel(self) -> Panel:
        """Render the statistics panel"""
        if not self.session or not self.session.power_data:
            content = Text("No data available", style="dim")
        else:
            power_data = self.session.power_data
            table = Table(show_header=False, box=None)
            table.add_column(style="cyan", width=15)
            table.add_column(style="white", width=15)
            
            # Calculate statistics
            powers = [p.instantaneous_power for p in power_data]
            avg_power = sum(powers) / len(powers) if powers else 0
            max_power = max(powers) if powers else 0
            
            table.add_row("Data Points", str(len(power_data)))
            table.add_row("Avg Power", f"{avg_power:.0f}W")
            table.add_row("Max Power", f"{max_power}W")
            table.add_row("Distance", f"{self.session.total_distance:.2f} km")
            table.add_row("Energy", f"{self.session.total_energy:.1f} kJ")
            
            content = table
            
        return Panel(content, title="Statistics", border_style="yellow")
        
    def _render_footer(self) -> Panel:
        """Render the footer panel"""
        footer_text = Text("Press Ctrl+C to stop training session", style="dim")
        return Panel(Align.center(footer_text), style="dim")
        
    def _render(self):
        """Render the complete display"""
        self._create_layout()
        
        self.layout["header"].update(self._render_header())
        self.layout["power_panel"].update(self._render_power_panel())
        self.layout["hr_panel"].update(self._render_hr_panel())
        self.layout["session_panel"].update(self._render_session_panel())
        self.layout["stats_panel"].update(self._render_stats_panel())
        self.layout["footer"].update(self._render_footer())
        
        return self.layout
        
    async def start_display(self):
        """Start the live display"""
        self.running = True
        
        with Live(self._render(), console=self.console, refresh_per_second=2) as live:
            while self.running:
                live.update(self._render())
                await asyncio.sleep(0.5)
                
    def stop_display(self):
        """Stop the live display"""
        self.running = False
