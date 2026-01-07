#!/usr/bin/env python3
"""
macOS Battery Monitor GUI
Battery monitoring tool with a modern, graphical UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, Canvas
import threading
import math
from datetime import datetime
import sys
import os

# Import backend modules
from battery_monitor import BatteryMonitor
from battery_history import BatteryHistoryManager

# Color Palette (macOS inspired)
COLORS = {
    'bg': '#F5F5F7',
    'card_bg': '#FFFFFF',
    'text': '#1D1D1F',
    'text_secondary': '#86868B',
    'accent_blue': '#007AFF',
    'accent_green': '#34C759',
    'accent_yellow': '#FF9500',
    'accent_red': '#FF3B30',
    'border': '#D1D1D6',
    'shadow': '#000000'
}

class ModernBatteryGUI:
    def __init__(self):
        self.setup_environment()
        
        # Initialize Root
        self.root = tk.Tk()
        self.root.title("Battery Monitor")
        self.root.geometry("500x700")
        self.root.configure(bg=COLORS['bg'])
        self.root.resizable(True, True)
        
        self.setup_styles()
        
        # Backend initialization
        self.battery_monitor = self.safe_init(BatteryMonitor)
        self.history_manager = self.safe_init(BatteryHistoryManager)
        
        # UI Components
        self.create_widgets()
        
        # Start data collection
        self.root.after(100, self.refresh_data)

    def setup_environment(self):
        """Setup environment variables for macOS"""
        try:
            os.environ['TK_SILENCE_DEPRECATION'] = '1'
            os.environ['TKINTER_NO_MENUBAR'] = '1'
        except Exception:
            pass

    def safe_init(self, cls):
        try:
            return cls()
        except Exception as e:
            print(f"Failed to initialize {cls.__name__}: {e}")
            return None

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('aqua')
        except:
            style.theme_use('clam')
            
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('Card.TFrame', background=COLORS['card_bg'])
        
        # Custom Label Styles
        style.configure('Header.TLabel', background=COLORS['bg'], foreground=COLORS['text'], font=('Helvetica', 24, 'bold'))
        style.configure('Section.TLabel', background=COLORS['bg'], foreground=COLORS['text_secondary'], font=('Helvetica', 13, 'bold'))
        
        style.configure('CardTitle.TLabel', background=COLORS['card_bg'], foreground=COLORS['text'], font=('Helvetica', 16, 'bold'))
        style.configure('CardValue.TLabel', background=COLORS['card_bg'], foreground=COLORS['text'], font=('Helvetica', 28, 'bold'))
        style.configure('CardLabel.TLabel', background=COLORS['card_bg'], foreground=COLORS['text_secondary'], font=('Helvetica', 12))
        style.configure('CardSmall.TLabel', background=COLORS['card_bg'], foreground=COLORS['text_secondary'], font=('Helvetica', 11))

        # Button Style
        style.configure('Action.TButton', font=('Helvetica', 12))

    def create_widgets(self):
        # Main Scrollable Container
        self.canvas = Canvas(self.root, bg=COLORS['bg'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas, style='TFrame')

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind resize to adjust width
        self.root.bind('<Configure>', self.on_window_resize)

        # Layout
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Header
        header_frame = ttk.Frame(self.scroll_frame, style='TFrame', padding=(20, 20, 20, 10))
        header_frame.pack(fill='x')
        ttk.Label(header_frame, text="Battery Monitor", style='Header.TLabel').pack(side='left')
        
        # Buttons
        btn_frame = ttk.Frame(header_frame, style='TFrame')
        btn_frame.pack(side='right')
        ttk.Button(btn_frame, text="History", command=self.show_history, style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_data, style='Action.TButton').pack(side='left')

        # Content Container
        self.content_frame = ttk.Frame(self.scroll_frame, style='TFrame', padding=20)
        self.content_frame.pack(fill='both', expand=True)

        # Placeholders for dynamic content
        self.mac_card = None
        self.ios_container = None

    def on_window_resize(self, event):
        # Adjust the width of the inner frame to match the canvas
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def refresh_data(self):
        if not self.battery_monitor:
            return

        def task():
            try:
                self.battery_monitor.collect_all_data()
                self.root.after(0, self.update_ui)
            except Exception as e:
                print(f"Error collecting data: {e}")

        threading.Thread(target=task, daemon=True).start()

    def update_ui(self):
        # Clear previous content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        data = self.battery_monitor.battery_data
        
        # --- macOS Battery Card ---
        self.create_mac_card(data)

        # --- iOS Devices ---
        ios_label = ttk.Label(self.content_frame, text="CONNECTED DEVICES", style='Section.TLabel')
        ios_label.pack(fill='x', pady=(20, 10))

        if self.battery_monitor.ios_devices:
            for device in self.battery_monitor.ios_devices:
                self.create_ios_card(device)
        else:
            self.create_empty_state_card("No iOS devices connected")
            
        # Save history
        if self.history_manager:
            threading.Thread(target=self.save_history, daemon=True).start()

    def create_card_frame(self, parent):
        """Creates a styled card frame"""
        # Using a canvas to draw a rounded rect background would be ideal, 
        # but for simplicity and stability, we use a Frame with padding and a white background.
        # To make it look like a card, we can add a border or shadow if we want, 
        # but a clean white box on gray bg is sufficient for modern flat UI.
        
        frame = tk.Frame(parent, bg=COLORS['card_bg'], padx=20, pady=20)
        # Add subtle border effect if desired, or just rely on color contrast
        return frame

    def create_mac_card(self, data):
        card = self.create_card_frame(self.content_frame)
        card.pack(fill='x', pady=(0, 10))

        # Top Row: Icon + Name + Percentage
        top_row = tk.Frame(card, bg=COLORS['card_bg'])
        top_row.pack(fill='x', pady=(0, 15))

        # Icon (Text based for now, can be image)
        device_name = data.get('device_name', 'MacBook')
        tk.Label(top_row, text="💻", font=("Apple Color Emoji", 30), bg=COLORS['card_bg']).pack(side='left', padx=(0, 10))
        
        name_frame = tk.Frame(top_row, bg=COLORS['card_bg'])
        name_frame.pack(side='left')
        tk.Label(name_frame, text=device_name, font=('Helvetica', 16, 'bold'), bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w')
        tk.Label(name_frame, text=data.get('serial', 'Unknown Serial'), font=('Helvetica', 11), bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(anchor='w')

        # Big Percentage
        try:
            current = int(data.get('current_capacity', 0))
        except:
            current = 0
            
        tk.Label(top_row, text=f"{current}%", font=('Helvetica', 36, 'bold'), bg=COLORS['card_bg'], fg=COLORS['text']).pack(side='right')

        # Visual Battery Indicator
        self.draw_battery_bar(card, current, self.get_charging_status(data))

        # Stats Grid
        stats_frame = tk.Frame(card, bg=COLORS['card_bg'])
        stats_frame.pack(fill='x', pady=20)
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)

        # Health Donut
        health_container = tk.Frame(stats_frame, bg=COLORS['card_bg'])
        health_container.grid(row=0, column=0, sticky='nsew')
        
        health_val = self.battery_monitor.calculate_battery_health() or 0
        self.draw_donut_chart(health_container, health_val, "Health")

        # Details Column
        details_container = tk.Frame(stats_frame, bg=COLORS['card_bg'], padx=20)
        details_container.grid(row=0, column=1, sticky='nsew')

        self.add_detail_row(details_container, "Status", self.get_charging_status_text(data))
        
        time_rem = data.get('time_remaining')
        if time_rem:
             self.add_detail_row(details_container, "Time Left", self.battery_monitor.format_time_remaining(time_rem))
        
        cycle = data.get('cycle_count')
        if cycle:
            self.add_detail_row(details_container, "Cycles", f"{cycle}")

        temp = data.get('temperature') # Raw value often needs formatting
        if temp:
             # Basic check if it's likely Celsius or Kelvin*10
             try:
                 t = float(temp)
                 if t > 100: t = (t / 10.0) - 273.15
                 self.add_detail_row(details_container, "Temp", f"{t:.1f}°C")
             except:
                 pass

    def create_ios_card(self, device):
        card = self.create_card_frame(self.content_frame)
        card.pack(fill='x', pady=(0, 10))

        top_row = tk.Frame(card, bg=COLORS['card_bg'])
        top_row.pack(fill='x', pady=(0, 10))

        # Icon
        dev_type = device.get('model', 'iPhone')
        icon = "📱" if "iPhone" in dev_type else "IPad" if "iPad" in dev_type else "device"
        tk.Label(top_row, text=icon, font=("Apple Color Emoji", 24), bg=COLORS['card_bg']).pack(side='left', padx=(0, 10))

        # Info
        info_frame = tk.Frame(top_row, bg=COLORS['card_bg'])
        info_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(info_frame, text=device.get('name', 'iOS Device'), font=('Helvetica', 14, 'bold'), bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w')
        tk.Label(info_frame, text=f"{device.get('model', '')} • iOS {device.get('ios_version', '')}", font=('Helvetica', 11), bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(anchor='w')

        # Battery Right Side
        cap = device.get('battery_capacity', 'N/A')
        if cap != 'N/A':
            tk.Label(top_row, text=f"{cap}%", font=('Helvetica', 20, 'bold'), bg=COLORS['card_bg'], fg=COLORS['text']).pack(side='right')

        # Progress Bar for iOS
        if cap != 'N/A':
            try:
                cap_val = int(float(cap))
                self.draw_mini_progress(card, cap_val, device.get('battery_charging') == 'True')
            except:
                pass

        # Detail Row (Health)
        if 'battery_health' in device:
            health_frame = tk.Frame(card, bg=COLORS['card_bg'], pady=5)
            health_frame.pack(fill='x')
            h_val = device['battery_health']
            tk.Label(health_frame, text=f"Health: {h_val}%", font=('Helvetica', 11, 'bold'), bg=COLORS['card_bg'], fg=COLORS['accent_green']).pack(side='left')
        
        # Capacity Information
        capacity_frame = tk.Frame(card, bg=COLORS['card_bg'], pady=5)
        capacity_frame.pack(fill='x')
        
        if 'nominal_charge_capacity' in device and device['nominal_charge_capacity'] != 'Unknown':
            tk.Label(capacity_frame, text=f"Max Capacity: {device['nominal_charge_capacity']} mAh", font=('Helvetica', 11), bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(side='left')
        
        if 'design_capacity' in device and device['design_capacity'] != 'Unknown':
            tk.Label(capacity_frame, text=f"Design: {device['design_capacity']} mAh", font=('Helvetica', 11), bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(side='left', padx=(10, 0))

    def create_empty_state_card(self, message):
        card = self.create_card_frame(self.content_frame)
        card.pack(fill='x', pady=(0, 10))
        tk.Label(card, text="🔍", font=("Arial", 24), bg=COLORS['card_bg']).pack(pady=(0,5))
        tk.Label(card, text=message, font=('Helvetica', 12), bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack()

    def add_detail_row(self, parent, label, value):
        row = tk.Frame(parent, bg=COLORS['card_bg'])
        row.pack(fill='x', pady=2)
        tk.Label(row, text=label, font=('Helvetica', 11), bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(side='left')
        tk.Label(row, text=value, font=('Helvetica', 11, 'bold'), bg=COLORS['card_bg'], fg=COLORS['text']).pack(side='right')

    def draw_battery_bar(self, parent, percentage, is_charging):
        # Canvas based modern battery bar
        h = 24
        w = 300 # Fixed width for stability
        canvas = Canvas(parent, height=h, width=w, bg=COLORS['card_bg'], highlightthickness=0)
        canvas.pack(pady=10)
        
        # Determine Color
        if percentage <= 20 and not is_charging:
            color = COLORS['accent_red']
        elif percentage <= 50 and not is_charging:
            color = COLORS['accent_yellow']
        else:
            color = COLORS['accent_green']
            
        if is_charging:
            color = COLORS['accent_green']

        # Background Track
        canvas.create_rectangle(0, 0, w, h, fill='#E5E5EA', outline='')
        
        # Fill
        fill_width = (w * percentage) / 100
        canvas.create_rectangle(0, 0, fill_width, h, fill=color, outline='')
        
        # Bolt Icon if charging
        if is_charging:
            bx, by = w/2, h/2
            canvas.create_text(bx, by, text="⚡", font=("Arial", 14), fill="white")

    def draw_mini_progress(self, parent, percentage, is_charging):
        h = 6
        w = 300
        canvas = Canvas(parent, height=h, width=w, bg=COLORS['card_bg'], highlightthickness=0)
        canvas.pack(pady=(5,0))
        
        color = COLORS['accent_green']
        if percentage <= 20: color = COLORS['accent_red']
        if is_charging: color = COLORS['accent_green']

        # Track
        canvas.create_rectangle(0, 0, w, h, fill='#E5E5EA', outline='')
        # Fill
        fill_w = (w * percentage) / 100
        canvas.create_rectangle(0, 0, fill_w, h, fill=color, outline='')

    def draw_donut_chart(self, parent, percentage, label):
        size = 100
        canvas = Canvas(parent, width=size, height=size, bg=COLORS['card_bg'], highlightthickness=0)
        canvas.pack()
        
        x, y, r = size/2, size/2, 35
        
        # Background Ring
        canvas.create_oval(x-r, y-r, x+r, y+r, outline='#E5E5EA', width=8)
        
        # Foreground Arc
        start = 90
        extent = -(percentage * 360) / 100
        
        color = COLORS['accent_green']
        if percentage < 80: color = COLORS['accent_yellow']
        if percentage < 60: color = COLORS['accent_red']
        
        canvas.create_arc(x-r, y-r, x+r, y+r, start=start, extent=extent, outline=color, width=8, style='arc')
        
        # Text
        canvas.create_text(x, y, text=f"{percentage}%", font=('Helvetica', 14, 'bold'), fill=COLORS['text'])
        canvas.create_text(x, y+15, text=label, font=('Helvetica', 8), fill=COLORS['text_secondary'])

    def get_charging_status(self, data):
        return data.get('is_charging') == 'Yes' or data.get('charging') == 'Yes'

    def get_charging_status_text(self, data):
        if data.get('is_charging') == 'Yes' or data.get('charging') == 'Yes':
            return "Charging"
        if data.get('fully_charged') == 'Yes':
            return "Full"
        if data.get('external_connected') == 'Yes':
            return "AC Connected"
        return "Discharging"

    def show_history(self):
        try:
            from history_viewer import HistoryViewer
            HistoryViewer(parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open history: {e}")

    def save_history(self):
        try:
            if self.battery_monitor.battery_data:
                self.history_manager.save_mac_battery_data(self.battery_monitor.battery_data)
            for device in self.battery_monitor.ios_devices:
                self.history_manager.save_ios_battery_data(device)
        except Exception as e:
            print(f"Background save error: {e}")

    def run(self):
        self.root.mainloop()

def main():
    app = ModernBatteryGUI()
    app.run()

if __name__ == "__main__":
    main()
