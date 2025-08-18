#!/usr/bin/env python3
"""
Battery History Viewer GUI
Battery history visualization and management tool
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime
from battery_history import BatteryHistoryManager

class HistoryViewer:
    def __init__(self, parent=None):
        """Initialize History Viewer"""
        self.parent = parent
        
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
            
        self.window.title("🔋 Battery History Viewer")
        self.window.geometry("1000x700")
        
        # Initialize History Manager
        self.history_manager = BatteryHistoryManager()
        
        # Setup GUI
        self.create_widgets()
        self.load_data()
        
    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔋 Battery History Viewer", 
                               font=('SF Pro Display', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="💾 Backup", command=self.create_backup).pack(side=tk.LEFT)
        
        # Chart frame
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_chart()
        
    def create_chart(self):
        """Create chart"""
        # Create matplotlib Figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(1, 1, 1)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def load_data(self):
        """Load data and update chart"""
        try:
            # Get Mac battery history
            history_data = self.history_manager.get_mac_history(days=30)
            
            if not history_data:
                self.ax.clear()
                self.ax.text(0.5, 0.5, 'No history data available\n\nPlease run Battery Monitor\nto collect data', 
                           ha='center', va='center', transform=self.ax.transAxes, fontsize=14)
                self.canvas.draw()
                return
            
            # Draw chart
            self.update_chart(history_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load data: {e}")
    
    def update_chart(self, history_data):
        """Update chart"""
        self.ax.clear()
        
        # Prepare data
        timestamps = []
        health_values = []
        cycle_values = []
        
        for record in history_data:
            if record.get('timestamp') and record.get('battery_health'):
                try:
                    # Parse timestamp
                    if isinstance(record['timestamp'], str):
                        dt = datetime.fromisoformat(record['timestamp'])
                    else:
                        dt = record['timestamp']
                    
                    timestamps.append(dt)
                    health_values.append(float(record['battery_health']))
                    cycle_values.append(int(record.get('cycle_count', 0)))
                except:
                    continue
        
        if not timestamps:
            self.ax.text(0.5, 0.5, 'No valid data available', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        # Battery health chart
        self.ax.plot(timestamps, health_values, 'b-', linewidth=2, marker='o', markersize=4, label='Battery Health')
        
        # Create secondary y-axis (cycle count)
        ax2 = self.ax.twinx()
        ax2.plot(timestamps, cycle_values, 'r-', linewidth=2, marker='s', markersize=4, label='Cycle Count')
        
        # Axis settings
        self.ax.set_xlabel('Date', fontsize=12)
        self.ax.set_ylabel('Battery Health (%)', color='b', fontsize=12)
        ax2.set_ylabel('Cycle Count', color='r', fontsize=12)
        
        self.ax.set_title('Battery History (Last 30 Days)', fontsize=14, fontweight='bold')
        
        # Grid
        self.ax.grid(True, alpha=0.3)
        
        # Legend
        lines1, labels1 = self.ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # Date format
        self.fig.autofmt_xdate()
        
        # Layout adjustment
        self.fig.tight_layout()
        self.canvas.draw()
    
    def create_backup(self):
        """Create backup"""
        try:
            backup_path = self.history_manager.create_backup()
            messagebox.showinfo("Backup Complete", f"Backup created:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Backup Error", f"Cannot create backup: {e}")
    
    def run(self):
        """Run application"""
        if not self.parent:
            self.window.protocol("WM_DELETE_WINDOW", self.window.quit)
            self.window.mainloop()

def main():
    """Main function"""
    app = HistoryViewer()
    app.run()

if __name__ == "__main__":
    main()
