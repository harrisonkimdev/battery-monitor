"""
Battery Monitor 앱 생성을 위한 setup.py
py2app을 사용하여 macOS 네이티브 앱 번들 생성
"""

from setuptools import setup

APP = ['battery_monitor_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',  # 배터리 모니터 아이콘
    'includes': ['tkinter', 'ctypes', '_ctypes'],  # 필요한 모듈 명시적 포함
    'excludes': ['matplotlib', 'numpy', 'PIL', 'PyQt5', 'PyQt6'],  # 불필요한 모듈 제외
    'site_packages': True,  # site-packages 포함
    'plist': {
        'CFBundleName': 'Battery Monitor',
        'CFBundleDisplayName': 'Battery Monitor',
        'CFBundleGetInfoString': "macOS Battery Monitor - CoconutBattery Alternative",
        'CFBundleIdentifier': 'com.harrisonkim.batterymonitor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 Harrison Kim',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,  # True로 설정하면 독에서 숨김
        'NSRequiresAquaSystemAppearance': False,  # 다크모드 지원
    }
}

setup(
    app=APP,
    name='Battery Monitor',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        # 필요한 의존성이 있다면 여기에 추가
    ],
)
