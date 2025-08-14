#!/usr/bin/env python3
"""
Battery History Viewer GUI
배터리 히스토리 시각화 및 관리 도구
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
        """History Viewer 초기화"""
        self.parent = parent
        
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
            
        self.window.title("🔋 Battery History Viewer")
        self.window.geometry("1000x700")
        
        # History Manager 초기화
        self.history_manager = BatteryHistoryManager()
        
        # GUI 구성
        self.create_widgets()
        self.load_data()
        
    def create_widgets(self):
        """GUI 위젯 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="🔋 Battery History Viewer", 
                               font=('SF Pro Display', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 컨트롤 프레임
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(control_frame, text="🔄 새로고침", command=self.load_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="💾 백업", command=self.create_backup).pack(side=tk.LEFT)
        
        # 차트 프레임
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_chart()
        
    def create_chart(self):
        """차트 생성"""
        # matplotlib Figure 생성
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(1, 1, 1)
        
        # 캔버스 생성
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def load_data(self):
        """데이터 로드 및 차트 업데이트"""
        try:
            # Mac 배터리 히스토리 가져오기
            history_data = self.history_manager.get_mac_history(days=30)
            
            if not history_data:
                self.ax.clear()
                self.ax.text(0.5, 0.5, '히스토리 데이터가 없습니다\n\n배터리 모니터를 실행하여\n데이터를 수집해주세요', 
                           ha='center', va='center', transform=self.ax.transAxes, fontsize=14)
                self.canvas.draw()
                return
            
            # 차트 그리기
            self.update_chart(history_data)
            
        except Exception as e:
            messagebox.showerror("오류", f"데이터를 로드할 수 없습니다: {e}")
    
    def update_chart(self, history_data):
        """차트 업데이트"""
        self.ax.clear()
        
        # 데이터 준비
        timestamps = []
        health_values = []
        cycle_values = []
        
        for record in history_data:
            if record.get('timestamp') and record.get('battery_health'):
                try:
                    # 타임스탬프 파싱
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
            self.ax.text(0.5, 0.5, '유효한 데이터가 없습니다', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        # 배터리 건강도 차트
        self.ax.plot(timestamps, health_values, 'b-', linewidth=2, marker='o', markersize=4, label='배터리 건강도')
        
        # 보조 y축 생성 (사이클 수)
        ax2 = self.ax.twinx()
        ax2.plot(timestamps, cycle_values, 'r-', linewidth=2, marker='s', markersize=4, label='사이클 수')
        
        # 축 설정
        self.ax.set_xlabel('날짜', fontsize=12)
        self.ax.set_ylabel('배터리 건강도 (%)', color='b', fontsize=12)
        ax2.set_ylabel('사이클 수', color='r', fontsize=12)
        
        self.ax.set_title('배터리 히스토리 (최근 30일)', fontsize=14, fontweight='bold')
        
        # 그리드
        self.ax.grid(True, alpha=0.3)
        
        # 범례
        lines1, labels1 = self.ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # 날짜 형식 설정
        self.fig.autofmt_xdate()
        
        # 레이아웃 조정
        self.fig.tight_layout()
        self.canvas.draw()
    
    def create_backup(self):
        """백업 생성"""
        try:
            backup_path = self.history_manager.create_backup()
            messagebox.showinfo("백업 완료", f"백업이 생성되었습니다:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("백업 오류", f"백업을 생성할 수 없습니다: {e}")
    
    def run(self):
        """애플리케이션 실행"""
        if not self.parent:
            self.window.protocol("WM_DELETE_WINDOW", self.window.quit)
            self.window.mainloop()

def main():
    """메인 함수"""
    app = HistoryViewer()
    app.run()

if __name__ == "__main__":
    main()
