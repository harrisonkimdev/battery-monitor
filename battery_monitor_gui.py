#!/usr/bin/env python3
"""
macOS Battery Monitor GUI
Battery monitoring tool similar to CoconutBattery - GUI version
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import re
import sys
import shutil
import ctypes
from ctypes import c_int, c_void_p, c_char_p, c_uint32, POINTER, Structure, CFUNCTYPE
import time
import threading
from datetime import datetime
from battery_monitor import BatteryMonitor
from battery_history import BatteryHistoryManager

class BatteryMonitorGUI:
    def __init__(self):
        # Enhanced settings to fix menubar issues in macOS app bundle
        try:
            # Environment setup before creating Tkinter root window
            import os
            os.environ['TK_SILENCE_DEPRECATION'] = '1'
            # Disable macOS menubar
            os.environ['TKINTER_NO_MENUBAR'] = '1'
        except:
            pass
            
        self.root = tk.Tk()
        
        # Complete menubar deactivation (try multiple methods)
        try:
            # Method 1: Set empty menubar
            self.root.option_add('*tearOff', False)
            # Method 2: Disable macOS menu commands
            self.root.tk.call('set', 'tcl_platform(os)', 'unix')
        except:
            pass
        
        self.root.title("🔋 Battery Monitor")
        self.root.geometry("800x900")
        self.root.resizable(True, True)
        
        # Fix menubar issue when running app bundle on macOS (enhanced)
        try:
            # Don't explicitly set default menubar
            self.root.createcommand('tk::mac::Quit', self.on_closing)
            # Prevent menu creation
            self.root.tk.call('package', 'require', 'Tk')
        except:
            pass
        
        # macOS styling
        self.setup_styles()
        
        # Battery monitor instance
        self.battery_monitor = BatteryMonitor()
        
        # History manager instance
        self.history_manager = BatteryHistoryManager()
        
        # GUI setup
        self.create_widgets()
        
        # Auto refresh disabled - manual refresh only
        self.auto_refresh = False
        
        # Initial data load
        self.refresh_data()
    
    def setup_styles(self):
        """Setup macOS styling"""
        style = ttk.Style()
        
        # Use macOS theme (when available)
        try:
            style.theme_use('aqua')
        except:
            style.theme_use('default')
        
        # Define custom styles
        style.configure('Title.TLabel', font=('SF Pro Display', 16, 'bold'))
        style.configure('Header.TLabel', font=('SF Pro Display', 14, 'bold'))
        style.configure('Info.TLabel', font=('SF Pro Display', 12))
        style.configure('Status.TLabel', font=('SF Pro Display', 11))
        
        # Set background color
        self.root.configure(bg='#f0f0f0')
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🔋 Battery Monitor", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Button frame
        button_frame = ttk.Frame(title_frame)
        button_frame.pack(side=tk.RIGHT)
        
        # History button
        history_btn = ttk.Button(button_frame, text="📊 History", command=self.show_history)
        history_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Refresh button
        refresh_btn = ttk.Button(button_frame, text="🔄 Refresh", command=self.refresh_data)
        refresh_btn.pack(side=tk.RIGHT)
        
        # Scrollable main content
        self.create_scrollable_content(main_frame)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", style='Status.TLabel')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    def create_scrollable_content(self, parent):
        """Create scrollable content area"""
        # Setup scrollbar and canvas
        canvas = tk.Canvas(parent, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scroll support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Create content frames
        self.create_content_frames()
    
    def create_content_frames(self):
        """Create content frames"""
        # macOS battery section
        self.macos_frame = self.create_section_frame("🖥️ macOS Battery")
        
        # iOS devices section
        self.ios_frame = self.create_section_frame("📱 iOS Devices")
    
    def create_section_frame(self, title):
        """Create section frame"""
        # Section container
        section_frame = ttk.LabelFrame(self.scrollable_frame, text=title, padding="15")
        section_frame.pack(fill=tk.X, pady=(0, 15))
        
        return section_frame
    
    def refresh_data(self):
        """Refresh data"""
        # Status update
        self.status_bar.config(text="Fetching data...")
        self.root.update_idletasks()
        
        # Collect data in background
        def collect_data():
            try:
                self.battery_monitor.collect_all_data()
                # UI update on main thread
                self.root.after(0, self.update_ui)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Data collection error: {e}"))
                self.root.after(0, lambda: self.status_bar.config(text="Error occurred"))
        
        # Run in separate thread
        threading.Thread(target=collect_data, daemon=True).start()
    
    def update_ui(self):
        """Update UI"""
        try:
            self.update_macos_battery()
            self.update_ios_devices()
            
            # Status update
            now = datetime.now().strftime('%H:%M:%S')
            self.status_bar.config(text=f"Last update: {now}")
            
            # Save history (run in background)
            self.save_history_data()
            
        except Exception as e:
            messagebox.showerror("Error", f"UI update error: {e}")
            self.status_bar.config(text="UI update error")
        
        # No auto refresh - manual refresh only
    
    def update_macos_battery(self):
        """Update macOS battery information"""
        # Remove existing widgets
        for widget in self.macos_frame.winfo_children():
            widget.destroy()
        
        battery_data = self.battery_monitor.battery_data
        
        if not battery_data:
            no_data_label = ttk.Label(self.macos_frame, text="Cannot retrieve battery information.", 
                                    style='Info.TLabel')
            no_data_label.pack(pady=10)
            return
        
        # Basic information section
        info_frame = ttk.Frame(self.macos_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Left column
        left_col = ttk.Frame(info_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right column
        right_col = ttk.Frame(info_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Basic information (left)
        self.add_info_row(left_col, "📱 Device:", battery_data.get('device_name', 'N/A'))
        self.add_info_row(left_col, "🔢 Serial:", battery_data.get('serial', 'N/A'))
        self.add_info_row(left_col, "💾 Firmware:", battery_data.get('firmware_version', 'N/A'))
        
        # Current status (right)
        current_capacity = battery_data.get('current_capacity')
        if current_capacity:
            self.add_info_row(right_col, "🔋 Current Charge:", f"{current_capacity}%")
        
        # Charging status
        status = self.get_charging_status(battery_data)
        self.add_info_row(right_col, "⚡ Status:", status)
        
        # Remaining time
        time_remaining = battery_data.get('time_remaining')
        if time_remaining:
            formatted_time = self.battery_monitor.format_time_remaining(time_remaining)
            self.add_info_row(right_col, "⏱️ Time Remaining:", formatted_time)
        
        # Separator
        separator = ttk.Separator(self.macos_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        # Health information
        health_frame = ttk.Frame(self.macos_frame)
        health_frame.pack(fill=tk.X, pady=(0, 15))
        
        health_left = ttk.Frame(health_frame)
        health_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        health_right = ttk.Frame(health_frame)
        health_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Cycle count
        cycle_count = battery_data.get('cycle_count')
        if cycle_count:
            self.add_info_row(health_left, "🔄 Cycle Count:", f"{cycle_count} times")
        
        # Battery health
        health = self.battery_monitor.calculate_battery_health()
        if health:
            color = self.get_health_color(health)
            self.add_info_row(health_left, "💚 Battery Health:", f"{health}%", color)
        
        condition = battery_data.get('condition')
        if condition:
            self.add_info_row(health_right, "🏥 Condition:", condition)
        
        # Technical information
        self.add_technical_info(battery_data)
    
    def add_technical_info(self, battery_data):
        """Add technical information"""
        # Separator
        separator = ttk.Separator(self.macos_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        tech_frame = ttk.Frame(self.macos_frame)
        tech_frame.pack(fill=tk.X)
        
        tech_left = ttk.Frame(tech_frame)
        tech_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tech_right = ttk.Frame(tech_frame)
        tech_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Capacity information
        design_capacity = battery_data.get('design_capacity')
        apple_raw_max = battery_data.get('apple_raw_max_capacity')
        apple_raw_current = battery_data.get('apple_raw_current_capacity')
        
        if design_capacity:
            self.add_info_row(tech_left, "🏭 Design Capacity:", f"{design_capacity} mAh")
        if apple_raw_max:
            self.add_info_row(tech_left, "📊 Current Max Capacity:", f"{apple_raw_max} mAh")
        if apple_raw_current:
            self.add_info_row(tech_left, "⚡ Current Capacity:", f"{apple_raw_current} mAh")
        
        # Voltage/Current
        voltage = battery_data.get('voltage')
        if voltage:
            voltage_v = self.battery_monitor.format_voltage(voltage)
            self.add_info_row(tech_right, "⚡ Voltage:", f"{voltage_v}V")
        
        amperage = battery_data.get('amperage')
        if amperage:
            amperage_ma = self.battery_monitor.format_amperage(amperage)
            self.add_info_row(tech_right, "🔌 Current:", f"{amperage_ma} mA")
    
    def update_ios_devices(self):
        """Update iOS device information"""
        # Remove existing widgets
        for widget in self.ios_frame.winfo_children():
            widget.destroy()
        
        ios_devices = self.battery_monitor.ios_devices
        
        if not ios_devices:
            no_device_frame = ttk.Frame(self.ios_frame)
            no_device_frame.pack(fill=tk.X, pady=10)
            
            no_device_label = ttk.Label(no_device_frame, text="🔍 No connected iOS devices found.", 
                                      style='Info.TLabel')
            no_device_label.pack()
            
            if not shutil.which('ideviceinfo'):
                tip_label = ttk.Label(no_device_frame, 
                                    text="📝 Install 'brew install libimobiledevice' for more detailed information.",
                                    style='Status.TLabel')
                tip_label.pack(pady=(5, 0))
            return
        
        # Display each iOS device
        for i, device in enumerate(ios_devices):
            self.create_ios_device_widget(device, i + 1)
    
    def create_ios_device_widget(self, device, index):
        """Create iOS device widget"""
        # Device frame
        device_frame = ttk.LabelFrame(self.ios_frame, text=f"📱 Device #{index}", padding="10")
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Device basic information
        info_frame = ttk.Frame(device_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        left_col = ttk.Frame(info_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_col = ttk.Frame(info_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Basic information
        self.add_info_row(left_col, "• Name:", device.get('name', 'N/A'))
        self.add_info_row(left_col, "• Model:", device.get('model', 'N/A'))
        
        if device.get('ios_version', 'Unknown') != 'Unknown':
            self.add_info_row(left_col, "• iOS:", device['ios_version'])
        
        if device.get('serial', 'Unknown') != 'Unknown':
            self.add_info_row(right_col, "• Serial:", device['serial'])
        
        self.add_info_row(right_col, "• Connection:", device.get('connection', 'USB'))
        
        # Battery information (when fetched via MobileDevice.framework)
        has_battery_info = False
        
        if device.get('battery_capacity', 'Unknown') != 'Unknown':
            has_battery_info = True
            capacity_color = self.get_capacity_color(device['battery_capacity'])
            self.add_info_row(right_col, "🔋 Battery:", f"{device['battery_capacity']}%", capacity_color)
        
        if device.get('battery_charging', 'Unknown') != 'Unknown':
            has_battery_info = True
            charging_status = "Charging" if device['battery_charging'] == 'True' else "Discharging"
            status_color = "#28a745" if device['battery_charging'] == 'True' else "#6c757d"
            self.add_info_row(right_col, "⚡ Charging Status:", charging_status, status_color)
        
        if device.get('battery_voltage', 'Unknown') != 'Unknown':
            has_battery_info = True
            self.add_info_row(right_col, "⚡ Voltage:", f"{device['battery_voltage']}V")
        
        # 배터리 건강도 및 사이클 정보 표시
        if device.get('battery_health', 'Unknown') != 'Unknown':
            has_battery_info = True
            try:
                health_value = float(device['battery_health'])
                health_color = self.get_health_color(health_value)
            except ValueError:
                health_color = None
            self.add_info_row(right_col, "💚 Battery Health:", f"{device['battery_health']}%", health_color)
        
        if device.get('cycle_count', 'Unknown') != 'Unknown':
            has_battery_info = True
            self.add_info_row(right_col, "🔄 Cycle Count:", f"{device['cycle_count']} times")
        
        if device.get('design_capacity', 'Unknown') != 'Unknown':
            has_battery_info = True
            self.add_info_row(right_col, "🏢 Design Capacity:", f"{device['design_capacity']} mAh")
        
        # Separator
        if has_battery_info:
            separator = ttk.Separator(device_frame, orient='horizontal')
            separator.pack(fill=tk.X, pady=5)
        
        # Connection method display
        status_frame = ttk.Frame(device_frame)
        status_frame.pack(fill=tk.X)
        
        if device.get('method') == 'libimobiledevice':
            status_label = ttk.Label(status_frame, text="✅ Battery info retrieved via libimobiledevice", 
                                   style='Status.TLabel', foreground='#28a745')
            status_label.pack()
        elif device.get('method') == 'MobileDevice.framework':
            status_label = ttk.Label(status_frame, text="✅ Successfully connected via CoconutBattery method!", 
                                   style='Status.TLabel', foreground='#28a745')
            status_label.pack()
        elif not shutil.which('ideviceinfo'):
            status_label = ttk.Label(status_frame, 
                                   text="⚠️ Recommend installing 'brew install libimobiledevice' for detailed information", 
                                   style='Status.TLabel', foreground='#ffc107')
            status_label.pack()
    
    def add_info_row(self, parent, label, value, color=None):
        """Add information row"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)
        
        label_widget = ttk.Label(row_frame, text=label, style='Info.TLabel')
        label_widget.pack(side=tk.LEFT)
        
        value_widget = ttk.Label(row_frame, text=value, style='Info.TLabel')
        if color:
            value_widget.configure(foreground=color)
        value_widget.pack(side=tk.RIGHT)
    
    def get_charging_status(self, battery_data):
        """Return charging status string"""
        is_charging = battery_data.get('is_charging', battery_data.get('charging'))
        fully_charged = battery_data.get('fully_charged')
        external_connected = battery_data.get('external_connected')
        
        if is_charging == 'Yes':
            return "Charging"
        elif fully_charged == 'Yes':
            return "Fully Charged"
        elif external_connected == 'Yes':
            return "Adapter Connected (Not Charging)"
        else:
            return "On Battery"
    
    def get_health_color(self, health):
        """Return color based on battery health"""
        if health >= 90:
            return "#28a745"  # Green
        elif health >= 80:
            return "#ffc107"  # Yellow
        else:
            return "#dc3545"  # Red
    
    def get_capacity_color(self, capacity_str):
        """Return color based on battery capacity"""
        try:
            capacity = float(capacity_str.replace('%', ''))
            if capacity >= 50:
                return "#28a745"  # Green
            elif capacity >= 20:
                return "#ffc107"  # Yellow
            else:
                return "#dc3545"  # Red
        except:
            return None
    
    def save_history_data(self):
        """Save history data"""
        def save_background():
            try:
                # Save Mac battery data
                if self.battery_monitor.battery_data:
                    self.history_manager.save_mac_battery_data(self.battery_monitor.battery_data)
                
                # Save iOS device data
                for device in self.battery_monitor.ios_devices:
                    self.history_manager.save_ios_battery_data(device)
                    
            except Exception as e:
                print(f"History save error: {e}")
        
        # Run in background thread
        threading.Thread(target=save_background, daemon=True).start()
    
    def show_history(self):
        """Show history viewer"""
        try:
            from history_viewer import HistoryViewer
            viewer = HistoryViewer(parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open history viewer: {e}")
    
    
    def run(self):
        """Run application"""
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Run application
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application exit"""
        self.auto_refresh = False
        self.root.quit()
        self.root.destroy()

def main():
    """Main function"""
    try:
        app = BatteryMonitorGUI()
        app.run()
        
    except KeyboardInterrupt:
        print("\nProgram terminated.")
        sys.exit(0)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
