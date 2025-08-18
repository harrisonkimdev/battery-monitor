"""
setup.py for creating Battery Monitor app
Create macOS native app bundle using py2app
"""

from setuptools import setup

APP = ['battery_monitor_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',  # Battery monitor icon
    'includes': ['tkinter', 'ctypes', '_ctypes'],  # Explicitly include required modules
    'excludes': ['matplotlib', 'numpy', 'PIL', 'PyQt5', 'PyQt6'],  # Exclude unnecessary modules
    'site_packages': True,  # Include site-packages
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

setup(
    app=APP,
    name='Battery Monitor',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        # Add required dependencies here if needed
    ],
)
