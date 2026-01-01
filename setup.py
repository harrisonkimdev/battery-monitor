"""
setup.py for creating Battery Monitor app
Create macOS native app bundle using py2app
"""

from setuptools import setup
import os
import sys
import glob

APP = ['battery_monitor_gui.py']
DATA_FILES = []

# Include icon if it exists
if os.path.exists('icon.icns'):
    DATA_FILES.append(('', ['icon.icns']))

# Get the directory containing this setup.py
setup_dir = os.path.dirname(os.path.abspath(__file__))

# Find libffi library automatically
libffi_path = None
# Common locations for libffi on macOS
possible_paths = [
    # Python framework location
    os.path.join(os.path.dirname(sys.executable), '../lib/libffi.8.dylib'),
    os.path.join(os.path.dirname(sys.executable), '../lib/libffi.dylib'),
    # Homebrew
    '/opt/homebrew/lib/libffi.8.dylib',
    '/opt/homebrew/lib/libffi.dylib',
    # MacPorts / Local
    '/usr/local/lib/libffi.8.dylib',
    '/usr/local/lib/libffi.dylib',
    # System
    '/usr/lib/libffi.dylib',
]

frameworks = []
print("Searching for libffi...")
for path in possible_paths:
    if os.path.exists(path):
        print(f"✅ Found libffi at: {path}")
        frameworks.append(path)
        break
else:
    print("⚠️  Warning: libffi not found in standard locations.")

# Also find Tcl/Tk libraries for Conda environments
tcl_tk_paths = [
    os.path.join(os.path.dirname(sys.executable), '../lib/libtk8.6.dylib'),
    os.path.join(os.path.dirname(sys.executable), '../lib/libtcl8.6.dylib'),
]

print("Searching for Tcl/Tk libraries...")
for path in tcl_tk_paths:
    if os.path.exists(path):
        print(f"✅ Found Tcl/Tk lib at: {path}")
        frameworks.append(path)
    else:
        print(f"⚠️  Could not find: {path}")

# Also find sqlite3 library for Conda environments
sqlite_path = os.path.join(os.path.dirname(sys.executable), '../lib/libsqlite3.0.dylib')
if os.path.exists(sqlite_path):
    print(f"✅ Found sqlite3 lib at: {sqlite_path}")
    frameworks.append(sqlite_path)
else:
    print(f"⚠️  Could not find sqlite3 at: {sqlite_path}")

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns' if os.path.exists('icon.icns') else None,  # Battery monitor icon
    'includes': [
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'ctypes',
        '_ctypes',
        'sqlite3',
        'pathlib',
        'typing',
        'threading',
        'subprocess',
        'json',
        're',
        'shutil',
        'datetime',
        'battery_monitor',
        'battery_history',
    ],  # Explicitly include required modules
    'packages': [],  # Empty packages list - we're using includes for modules
    'frameworks': frameworks,  # Include necessary dylibs
    'excludes': ['matplotlib', 'numpy', 'PIL', 'PyQt5', 'PyQt6', 'pandas'],  # Exclude unnecessary modules
    'site_packages': False,  # Create standalone app without external dependencies
    'optimize': 0,  # Disable optimization for better debugging
    'strip': False,  # Don't strip symbols for better debugging
    'semi_standalone': False,  # Create fully standalone app
    'plist': {
        'CFBundleName': 'Battery Monitor',
        'CFBundleDisplayName': 'Battery Monitor',
        'CFBundleGetInfoString': "macOS Battery Monitor - CoconutBattery Alternative",
        'CFBundleIdentifier': 'com.harrisonkim.batterymonitor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 Harrison Kim',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,  # Set to True to hide from Dock
        'NSRequiresAquaSystemAppearance': False,  # Dark mode support
    }
}

# Add local modules to Python path for py2app to find them
sys.path.insert(0, setup_dir)

setup(
    app=APP,
    name='Battery Monitor',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        # No external dependencies required for basic functionality
    ],
    py_modules=['battery_monitor', 'battery_history'],  # Explicitly list local modules
)
