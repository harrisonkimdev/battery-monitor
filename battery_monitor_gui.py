#!/usr/bin/env python3
"""
macOS Battery Monitor GUI
CoconutBattery와 유사한 배터리 정보 모니터링 도구 - GUI 버전
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

class BatteryMonitorGUI:
    def __init__(self):
        # macOS 앱 번들에서 메뉴바 문제 해결을 위한 설정
        try:
            # Tkinter 루트 윈도우 생성 전 환경 설정
            import os
            os.environ['TK_SILENCE_DEPRECATION'] = '1'
        except:
            pass
            
        self.root = tk.Tk()
        self.root.title("🔋 Battery Monitor")
        self.root.geometry("800x900")
        self.root.resizable(True, True)
        
        # macOS에서 앱 번들 실행 시 메뉴바 문제 해결
        try:
            # 기본 메뉴바를 명시적으로 설정하지 않음
            self.root.createcommand('tk::mac::Quit', self.on_closing)
        except:
            pass
        
        # macOS 스타일링
        self.setup_styles()
        
        # 배터리 모니터 인스턴스
        self.battery_monitor = BatteryMonitor()
        
        # GUI 구성
        self.create_widgets()
        
        # 자동 새로고침 설정
        self.auto_refresh = True
        self.refresh_interval = 5000  # 5초
        
        # 초기 데이터 로드
        self.refresh_data()
    
    def setup_styles(self):
        """macOS 스타일 설정"""
        style = ttk.Style()
        
        # macOS 테마 사용 (가능한 경우)
        try:
            style.theme_use('aqua')
        except:
            style.theme_use('default')
        
        # 커스텀 스타일 정의
        style.configure('Title.TLabel', font=('SF Pro Display', 16, 'bold'))
        style.configure('Header.TLabel', font=('SF Pro Display', 14, 'bold'))
        style.configure('Info.TLabel', font=('SF Pro Display', 12))
        style.configure('Status.TLabel', font=('SF Pro Display', 11))
        
        # 배경색 설정
        self.root.configure(bg='#f0f0f0')
    
    def create_widgets(self):
        """GUI 위젯 생성"""
        # 메인 컨테이너
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🔋 Battery Monitor", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(title_frame, text="🔄 새로고침", command=self.refresh_data)
        refresh_btn.pack(side=tk.RIGHT)
        
        # 자동 새로고침 체크박스
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = ttk.Checkbutton(title_frame, text="자동 새로고침", 
                                        variable=self.auto_refresh_var,
                                        command=self.toggle_auto_refresh)
        auto_refresh_cb.pack(side=tk.RIGHT, padx=(0, 10))
        
        # 스크롤 가능한 메인 콘텐츠
        self.create_scrollable_content(main_frame)
        
        # 상태바
        self.status_bar = ttk.Label(main_frame, text="준비", style='Status.TLabel')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    def create_scrollable_content(self, parent):
        """스크롤 가능한 콘텐츠 영역 생성"""
        # 스크롤바와 캔버스 설정
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
        
        # 마우스 휠 스크롤 지원
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 콘텐츠 프레임들 생성
        self.create_content_frames()
    
    def create_content_frames(self):
        """콘텐츠 프레임들 생성"""
        # macOS 배터리 섹션
        self.macos_frame = self.create_section_frame("🖥️ macOS 배터리")
        
        # iOS 디바이스 섹션
        self.ios_frame = self.create_section_frame("📱 iOS 디바이스")
    
    def create_section_frame(self, title):
        """섹션 프레임 생성"""
        # 섹션 컨테이너
        section_frame = ttk.LabelFrame(self.scrollable_frame, text=title, padding="15")
        section_frame.pack(fill=tk.X, pady=(0, 15))
        
        return section_frame
    
    def refresh_data(self):
        """데이터 새로고침"""
        # 상태 업데이트
        self.status_bar.config(text="데이터를 가져오는 중...")
        self.root.update_idletasks()
        
        # 백그라운드에서 데이터 수집
        def collect_data():
            try:
                self.battery_monitor.collect_all_data()
                # UI 업데이트는 메인 스레드에서
                self.root.after(0, self.update_ui)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("오류", f"데이터 수집 중 오류: {e}"))
                self.root.after(0, lambda: self.status_bar.config(text="오류 발생"))
        
        # 별도 스레드에서 실행
        threading.Thread(target=collect_data, daemon=True).start()
    
    def update_ui(self):
        """UI 업데이트"""
        try:
            self.update_macos_battery()
            self.update_ios_devices()
            
            # 상태 업데이트
            now = datetime.now().strftime('%H:%M:%S')
            self.status_bar.config(text=f"마지막 업데이트: {now}")
            
        except Exception as e:
            messagebox.showerror("오류", f"UI 업데이트 중 오류: {e}")
            self.status_bar.config(text="UI 업데이트 오류")
        
        # 자동 새로고침 스케줄링
        if self.auto_refresh:
            self.root.after(self.refresh_interval, self.refresh_data)
    
    def update_macos_battery(self):
        """macOS 배터리 정보 업데이트"""
        # 기존 위젯들 제거
        for widget in self.macos_frame.winfo_children():
            widget.destroy()
        
        battery_data = self.battery_monitor.battery_data
        
        if not battery_data:
            no_data_label = ttk.Label(self.macos_frame, text="배터리 정보를 가져올 수 없습니다.", 
                                    style='Info.TLabel')
            no_data_label.pack(pady=10)
            return
        
        # 기본 정보 섹션
        info_frame = ttk.Frame(self.macos_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 왼쪽 컬럼
        left_col = ttk.Frame(info_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 오른쪽 컬럼
        right_col = ttk.Frame(info_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 기본 정보 (왼쪽)
        self.add_info_row(left_col, "📱 디바이스:", battery_data.get('device_name', 'N/A'))
        self.add_info_row(left_col, "🔢 시리얼:", battery_data.get('serial', 'N/A'))
        self.add_info_row(left_col, "💾 펌웨어:", battery_data.get('firmware_version', 'N/A'))
        
        # 현재 상태 (오른쪽)
        current_capacity = battery_data.get('current_capacity')
        if current_capacity:
            self.add_info_row(right_col, "🔋 현재 충전량:", f"{current_capacity}%")
        
        # 충전 상태
        status = self.get_charging_status(battery_data)
        self.add_info_row(right_col, "⚡ 상태:", status)
        
        # 남은 시간
        time_remaining = battery_data.get('time_remaining')
        if time_remaining:
            formatted_time = self.battery_monitor.format_time_remaining(time_remaining)
            self.add_info_row(right_col, "⏱️ 남은 시간:", formatted_time)
        
        # 구분선
        separator = ttk.Separator(self.macos_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        # 건강도 정보
        health_frame = ttk.Frame(self.macos_frame)
        health_frame.pack(fill=tk.X, pady=(0, 15))
        
        health_left = ttk.Frame(health_frame)
        health_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        health_right = ttk.Frame(health_frame)
        health_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 사이클 수
        cycle_count = battery_data.get('cycle_count')
        if cycle_count:
            self.add_info_row(health_left, "🔄 사이클 수:", f"{cycle_count}회")
        
        # 배터리 건강도
        health = self.battery_monitor.calculate_battery_health()
        if health:
            color = self.get_health_color(health)
            self.add_info_row(health_left, "💚 배터리 건강도:", f"{health}%", color)
        
        condition = battery_data.get('condition')
        if condition:
            self.add_info_row(health_right, "🏥 컨디션:", condition)
        
        # 기술적 정보
        self.add_technical_info(battery_data)
    
    def add_technical_info(self, battery_data):
        """기술적 정보 추가"""
        # 구분선
        separator = ttk.Separator(self.macos_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        tech_frame = ttk.Frame(self.macos_frame)
        tech_frame.pack(fill=tk.X)
        
        tech_left = ttk.Frame(tech_frame)
        tech_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tech_right = ttk.Frame(tech_frame)
        tech_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 용량 정보
        design_capacity = battery_data.get('design_capacity')
        apple_raw_max = battery_data.get('apple_raw_max_capacity')
        apple_raw_current = battery_data.get('apple_raw_current_capacity')
        
        if design_capacity:
            self.add_info_row(tech_left, "🏭 설계 용량:", f"{design_capacity} mAh")
        if apple_raw_max:
            self.add_info_row(tech_left, "📊 현재 최대 용량:", f"{apple_raw_max} mAh")
        if apple_raw_current:
            self.add_info_row(tech_left, "⚡ 현재 용량:", f"{apple_raw_current} mAh")
        
        # 전압/전류
        voltage = battery_data.get('voltage')
        if voltage:
            voltage_v = self.battery_monitor.format_voltage(voltage)
            self.add_info_row(tech_right, "⚡ 전압:", f"{voltage_v}V")
        
        amperage = battery_data.get('amperage')
        if amperage:
            amperage_ma = self.battery_monitor.format_amperage(amperage)
            self.add_info_row(tech_right, "🔌 전류:", f"{amperage_ma} mA")
    
    def update_ios_devices(self):
        """iOS 디바이스 정보 업데이트"""
        # 기존 위젯들 제거
        for widget in self.ios_frame.winfo_children():
            widget.destroy()
        
        ios_devices = self.battery_monitor.ios_devices
        
        if not ios_devices:
            no_device_frame = ttk.Frame(self.ios_frame)
            no_device_frame.pack(fill=tk.X, pady=10)
            
            no_device_label = ttk.Label(no_device_frame, text="🔍 연결된 iOS 디바이스가 없습니다.", 
                                      style='Info.TLabel')
            no_device_label.pack()
            
            if not shutil.which('ideviceinfo'):
                tip_label = ttk.Label(no_device_frame, 
                                    text="📝 'brew install libimobiledevice'로 더 상세한 정보를 얻을 수 있습니다.",
                                    style='Status.TLabel')
                tip_label.pack(pady=(5, 0))
            return
        
        # 각 iOS 디바이스 표시
        for i, device in enumerate(ios_devices):
            self.create_ios_device_widget(device, i + 1)
    
    def create_ios_device_widget(self, device, index):
        """iOS 디바이스 위젯 생성"""
        # 디바이스 프레임
        device_frame = ttk.LabelFrame(self.ios_frame, text=f"📱 디바이스 #{index}", padding="10")
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 디바이스 기본 정보
        info_frame = ttk.Frame(device_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        left_col = ttk.Frame(info_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_col = ttk.Frame(info_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 기본 정보
        self.add_info_row(left_col, "• 이름:", device.get('name', 'N/A'))
        self.add_info_row(left_col, "• 모델:", device.get('model', 'N/A'))
        
        if device.get('ios_version', 'Unknown') != 'Unknown':
            self.add_info_row(left_col, "• iOS:", device['ios_version'])
        
        if device.get('serial', 'Unknown') != 'Unknown':
            self.add_info_row(right_col, "• 시리얼:", device['serial'])
        
        self.add_info_row(right_col, "• 연결:", device.get('connection', 'USB'))
        
        # 배터리 정보 (MobileDevice.framework로 가져온 경우)
        has_battery_info = False
        
        if device.get('battery_capacity', 'Unknown') != 'Unknown':
            has_battery_info = True
            capacity_color = self.get_capacity_color(device['battery_capacity'])
            self.add_info_row(right_col, "🔋 배터리:", f"{device['battery_capacity']}%", capacity_color)
        
        if device.get('battery_charging', 'Unknown') != 'Unknown':
            has_battery_info = True
            charging_status = "충전 중" if device['battery_charging'] == 'True' else "방전 중"
            status_color = "#28a745" if device['battery_charging'] == 'True' else "#6c757d"
            self.add_info_row(right_col, "⚡ 충전 상태:", charging_status, status_color)
        
        if device.get('battery_voltage', 'Unknown') != 'Unknown':
            has_battery_info = True
            self.add_info_row(right_col, "⚡ 전압:", f"{device['battery_voltage']}V")
        
        # 구분선
        if has_battery_info:
            separator = ttk.Separator(device_frame, orient='horizontal')
            separator.pack(fill=tk.X, pady=5)
        
        # 연결 방식 표시
        status_frame = ttk.Frame(device_frame)
        status_frame.pack(fill=tk.X)
        
        if device.get('method') == 'MobileDevice.framework':
            status_label = ttk.Label(status_frame, text="✅ CoconutBattery 방식으로 연결 성공!", 
                                   style='Status.TLabel', foreground='#28a745')
            status_label.pack()
        elif not shutil.which('ideviceinfo'):
            status_label = ttk.Label(status_frame, 
                                   text="⚠️ 상세 정보를 위해 'brew install libimobiledevice' 설치 권장", 
                                   style='Status.TLabel', foreground='#ffc107')
            status_label.pack()
    
    def add_info_row(self, parent, label, value, color=None):
        """정보 행 추가"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)
        
        label_widget = ttk.Label(row_frame, text=label, style='Info.TLabel')
        label_widget.pack(side=tk.LEFT)
        
        value_widget = ttk.Label(row_frame, text=value, style='Info.TLabel')
        if color:
            value_widget.configure(foreground=color)
        value_widget.pack(side=tk.RIGHT)
    
    def get_charging_status(self, battery_data):
        """충전 상태 문자열 반환"""
        is_charging = battery_data.get('is_charging', battery_data.get('charging'))
        fully_charged = battery_data.get('fully_charged')
        external_connected = battery_data.get('external_connected')
        
        if is_charging == 'Yes':
            return "충전 중"
        elif fully_charged == 'Yes':
            return "충전 완료"
        elif external_connected == 'Yes':
            return "어댑터 연결됨 (충전 안함)"
        else:
            return "배터리 사용 중"
    
    def get_health_color(self, health):
        """배터리 건강도에 따른 색상 반환"""
        if health >= 90:
            return "#28a745"  # 녹색
        elif health >= 80:
            return "#ffc107"  # 노란색
        else:
            return "#dc3545"  # 빨간색
    
    def get_capacity_color(self, capacity_str):
        """배터리 용량에 따른 색상 반환"""
        try:
            capacity = float(capacity_str.replace('%', ''))
            if capacity >= 50:
                return "#28a745"  # 녹색
            elif capacity >= 20:
                return "#ffc107"  # 노란색
            else:
                return "#dc3545"  # 빨간색
        except:
            return None
    
    def toggle_auto_refresh(self):
        """자동 새로고침 토글"""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self.refresh_data()
    
    def run(self):
        """애플리케이션 실행"""
        # 윈도우 종료 시 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 애플리케이션 실행
        self.root.mainloop()
    
    def on_closing(self):
        """애플리케이션 종료 처리"""
        self.auto_refresh = False
        self.root.quit()
        self.root.destroy()

def main():
    """메인 함수"""
    try:
        app = BatteryMonitorGUI()
        app.run()
        
    except KeyboardInterrupt:
        print("\n프로그램이 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
