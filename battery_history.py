#!/usr/bin/env python3
"""
Battery History Manager
배터리 데이터 히스토리 관리, 저장, 백업 및 복원 기능
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from typing import Dict, List, Optional, Tuple

class BatteryHistoryManager:
    def __init__(self, db_path: str = None):
        """
        배터리 히스토리 매니저 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로 (기본값: ~/Library/Application Support/BatteryMonitor/battery_history.db)
        """
        if db_path is None:
            # macOS 표준 위치에 데이터베이스 저장
            app_support = Path.home() / "Library" / "Application Support" / "BatteryMonitor"
            app_support.mkdir(parents=True, exist_ok=True)
            db_path = app_support / "battery_history.db"
        
        self.db_path = str(db_path)
        self.backup_dir = Path(self.db_path).parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Mac 배터리 히스토리 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mac_battery_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    device_name TEXT,
                    device_identifier TEXT,
                    serial_number TEXT,
                    os_version TEXT,
                    current_capacity INTEGER,
                    max_capacity INTEGER,
                    design_capacity INTEGER,
                    cycle_count INTEGER,
                    battery_health REAL,
                    temperature REAL,
                    voltage REAL,
                    amperage INTEGER,
                    is_charging BOOLEAN,
                    fully_charged BOOLEAN,
                    external_connected BOOLEAN,
                    time_remaining INTEGER,
                    manufacture_date TEXT,
                    battery_serial TEXT,
                    condition TEXT,
                    data_version TEXT DEFAULT '1.0'
                )
            ''')
            
            # iOS 디바이스 배터리 히스토리 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ios_battery_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    device_id TEXT NOT NULL,
                    device_name TEXT,
                    device_model TEXT,
                    ios_version TEXT,
                    device_serial TEXT,
                    storage_capacity TEXT,
                    battery_charge INTEGER,
                    battery_health REAL,
                    full_charge_capacity INTEGER,
                    design_capacity INTEGER,
                    manufacture_date TEXT,
                    charge_cycles INTEGER,
                    battery_temperature REAL,
                    charging_power INTEGER,
                    is_charging BOOLEAN,
                    last_seen DATETIME,
                    connection_type TEXT,
                    data_version TEXT DEFAULT '1.0'
                )
            ''')
            
            # 인덱스 생성 (성능 최적화)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mac_timestamp ON mac_battery_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ios_timestamp ON ios_battery_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ios_device ON ios_battery_history(device_id)')
            
            conn.commit()
    
    def save_mac_battery_data(self, battery_data: Dict) -> bool:
        """
        Mac 배터리 데이터 저장
        
        Args:
            battery_data: 배터리 정보 딕셔너리
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 현재 시간
                timestamp = datetime.now()
                
                # 데이터 변환 및 정리
                data = {
                    'timestamp': timestamp,
                    'device_name': battery_data.get('device_name'),
                    'device_identifier': self._get_device_identifier(),
                    'serial_number': battery_data.get('serial'),
                    'os_version': self._get_os_version(),
                    'current_capacity': self._safe_int(battery_data.get('apple_raw_current_capacity')),
                    'max_capacity': self._safe_int(battery_data.get('apple_raw_max_capacity')),
                    'design_capacity': self._safe_int(battery_data.get('design_capacity')),
                    'cycle_count': self._safe_int(battery_data.get('cycle_count')),
                    'battery_health': self._calculate_health(battery_data),
                    'temperature': self._safe_float(battery_data.get('temperature')),
                    'voltage': self._safe_float(battery_data.get('voltage')),
                    'amperage': self._safe_int(battery_data.get('amperage')),
                    'is_charging': self._parse_bool(battery_data.get('is_charging')),
                    'fully_charged': self._parse_bool(battery_data.get('fully_charged')),
                    'external_connected': self._parse_bool(battery_data.get('external_connected')),
                    'time_remaining': self._safe_int(battery_data.get('time_remaining')),
                    'manufacture_date': battery_data.get('manufacture_date'),
                    'battery_serial': battery_data.get('serial'),
                    'condition': battery_data.get('condition'),
                }
                
                cursor.execute('''
                    INSERT INTO mac_battery_history 
                    (timestamp, device_name, device_identifier, serial_number, os_version,
                     current_capacity, max_capacity, design_capacity, cycle_count, battery_health,
                     temperature, voltage, amperage, is_charging, fully_charged, external_connected,
                     time_remaining, manufacture_date, battery_serial, condition)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['timestamp'], data['device_name'], data['device_identifier'], 
                    data['serial_number'], data['os_version'], data['current_capacity'],
                    data['max_capacity'], data['design_capacity'], data['cycle_count'],
                    data['battery_health'], data['temperature'], data['voltage'],
                    data['amperage'], data['is_charging'], data['fully_charged'],
                    data['external_connected'], data['time_remaining'], data['manufacture_date'],
                    data['battery_serial'], data['condition']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Mac 배터리 데이터 저장 오류: {e}")
            return False
    
    def save_ios_battery_data(self, device_data: Dict) -> bool:
        """
        iOS 디바이스 배터리 데이터 저장
        
        Args:
            device_data: iOS 디바이스 정보 딕셔너리
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                timestamp = datetime.now()
                
                data = {
                    'timestamp': timestamp,
                    'device_id': device_data.get('device_id', device_data.get('serial', 'unknown')),
                    'device_name': device_data.get('name'),
                    'device_model': device_data.get('model'),
                    'ios_version': device_data.get('ios_version'),
                    'device_serial': device_data.get('serial'),
                    'storage_capacity': device_data.get('storage_capacity'),
                    'battery_charge': self._safe_int(device_data.get('battery_capacity')),
                    'battery_health': self._safe_float(device_data.get('battery_health')),
                    'full_charge_capacity': self._safe_int(device_data.get('full_charge_capacity')),
                    'design_capacity': self._safe_int(device_data.get('design_capacity')),
                    'manufacture_date': device_data.get('manufacture_date'),
                    'charge_cycles': self._safe_int(device_data.get('charge_cycles')),
                    'battery_temperature': self._safe_float(device_data.get('battery_temperature')),
                    'charging_power': self._safe_int(device_data.get('charging_power')),
                    'is_charging': self._parse_bool(device_data.get('battery_charging')),
                    'last_seen': timestamp,
                    'connection_type': device_data.get('connection', 'USB'),
                }
                
                cursor.execute('''
                    INSERT INTO ios_battery_history 
                    (timestamp, device_id, device_name, device_model, ios_version, device_serial,
                     storage_capacity, battery_charge, battery_health, full_charge_capacity,
                     design_capacity, manufacture_date, charge_cycles, battery_temperature,
                     charging_power, is_charging, last_seen, connection_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['timestamp'], data['device_id'], data['device_name'],
                    data['device_model'], data['ios_version'], data['device_serial'],
                    data['storage_capacity'], data['battery_charge'], data['battery_health'],
                    data['full_charge_capacity'], data['design_capacity'], data['manufacture_date'],
                    data['charge_cycles'], data['battery_temperature'], data['charging_power'],
                    data['is_charging'], data['last_seen'], data['connection_type']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"iOS 배터리 데이터 저장 오류: {e}")
            return False
    
    def get_mac_history(self, days: int = 30) -> List[Dict]:
        """
        Mac 배터리 히스토리 조회
        
        Args:
            days: 조회할 일수 (기본값: 30일)
            
        Returns:
            List[Dict]: 히스토리 데이터 리스트
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    SELECT * FROM mac_battery_history 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (cutoff_date,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Mac 히스토리 조회 오류: {e}")
            return []
    
    def get_ios_history(self, device_id: str = None, days: int = 30) -> List[Dict]:
        """
        iOS 디바이스 배터리 히스토리 조회
        
        Args:
            device_id: 특정 디바이스 ID (None이면 모든 디바이스)
            days: 조회할 일수
            
        Returns:
            List[Dict]: 히스토리 데이터 리스트
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                if device_id:
                    cursor.execute('''
                        SELECT * FROM ios_battery_history 
                        WHERE device_id = ? AND timestamp >= ?
                        ORDER BY timestamp DESC
                    ''', (device_id, cutoff_date))
                else:
                    cursor.execute('''
                        SELECT * FROM ios_battery_history 
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                    ''', (cutoff_date,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"iOS 히스토리 조회 오류: {e}")
            return []
    
    def get_monthly_summary(self) -> Dict:
        """
        월별 요약 데이터 조회
        
        Returns:
            Dict: 월별 요약 정보
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Mac 월별 요약
                cursor.execute('''
                    SELECT 
                        strftime('%Y-%m', timestamp) as month,
                        AVG(battery_health) as avg_health,
                        MAX(cycle_count) as max_cycles,
                        COUNT(*) as record_count
                    FROM mac_battery_history 
                    WHERE timestamp >= date('now', '-12 months')
                    GROUP BY strftime('%Y-%m', timestamp)
                    ORDER BY month DESC
                ''')
                
                mac_summary = [dict(row) for row in cursor.fetchall()]
                
                # iOS 월별 요약 (디바이스별)
                cursor.execute('''
                    SELECT 
                        device_name,
                        device_model,
                        strftime('%Y-%m', timestamp) as month,
                        AVG(battery_health) as avg_health,
                        MAX(charge_cycles) as max_cycles,
                        COUNT(*) as record_count
                    FROM ios_battery_history 
                    WHERE timestamp >= date('now', '-12 months')
                    GROUP BY device_id, strftime('%Y-%m', timestamp)
                    ORDER BY device_name, month DESC
                ''')
                
                ios_summary = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'mac': mac_summary,
                    'ios': ios_summary
                }
                
        except Exception as e:
            print(f"월별 요약 조회 오류: {e}")
            return {'mac': [], 'ios': []}
    
    def create_backup(self) -> str:
        """
        데이터베이스 백업 생성
        
        Returns:
            str: 백업 파일 경로
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"battery_history_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(self.db_path, backup_path)
            
            # JSON 형태로도 백업 생성
            json_backup_path = self.backup_dir / f"battery_history_backup_{timestamp}.json"
            self._export_to_json(json_backup_path)
            
            return str(backup_path)
            
        except Exception as e:
            print(f"백업 생성 오류: {e}")
            return ""
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        백업에서 데이터베이스 복원
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        try:
            if not os.path.exists(backup_path):
                return False
            
            # 현재 데이터베이스 백업
            current_backup = self.create_backup()
            print(f"현재 데이터베이스를 {current_backup}에 백업했습니다.")
            
            # 백업에서 복원
            shutil.copy2(backup_path, self.db_path)
            
            return True
            
        except Exception as e:
            print(f"백업 복원 오류: {e}")
            return False
    
    def _export_to_json(self, json_path: Path):
        """JSON 형태로 데이터 내보내기"""
        try:
            mac_history = self.get_mac_history(days=365)  # 1년치
            ios_history = self.get_ios_history(days=365)
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                'mac_battery_history': mac_history,
                'ios_battery_history': ios_history
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            print(f"JSON 내보내기 오류: {e}")
    
    def get_device_list(self) -> Dict[str, List[Dict]]:
        """
        히스토리에 기록된 모든 디바이스 목록 조회
        
        Returns:
            Dict: Mac 및 iOS 디바이스 목록
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Mac 정보
                cursor.execute('''
                    SELECT DISTINCT 
                        device_name, device_identifier, serial_number,
                        MIN(timestamp) as first_seen,
                        MAX(timestamp) as last_seen,
                        COUNT(*) as record_count
                    FROM mac_battery_history 
                    GROUP BY device_identifier
                    ORDER BY last_seen DESC
                ''')
                
                mac_devices = [dict(row) for row in cursor.fetchall()]
                
                # iOS 디바이스 정보
                cursor.execute('''
                    SELECT DISTINCT 
                        device_id, device_name, device_model, device_serial,
                        MIN(timestamp) as first_seen,
                        MAX(timestamp) as last_seen,
                        COUNT(*) as record_count
                    FROM ios_battery_history 
                    GROUP BY device_id
                    ORDER BY last_seen DESC
                ''')
                
                ios_devices = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'mac': mac_devices,
                    'ios': ios_devices
                }
                
        except Exception as e:
            print(f"디바이스 목록 조회 오류: {e}")
            return {'mac': [], 'ios': []}
    
    # 유틸리티 메서드들
    def _safe_int(self, value) -> Optional[int]:
        """안전하게 정수로 변환"""
        try:
            if value is None:
                return None
            int_val = int(value)
            # SQLite INTEGER 범위 확인 (-2^63 ~ 2^63-1)
            if int_val > 2**63 - 1:
                # 2의 보수 방식으로 변환 (amperage 등에서 사용)
                int_val = int_val - 2**64
            elif int_val < -2**63:
                int_val = int_val + 2**64
            return int_val
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value) -> Optional[float]:
        """안전하게 실수로 변환"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def _parse_bool(self, value) -> Optional[bool]:
        """문자열을 bool로 변환"""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('yes', 'true', '1')
        return bool(value)
    
    def _calculate_health(self, battery_data: Dict) -> Optional[float]:
        """배터리 건강도 계산"""
        try:
            max_cap = self._safe_int(battery_data.get('apple_raw_max_capacity'))
            design_cap = self._safe_int(battery_data.get('design_capacity'))
            
            if max_cap and design_cap:
                return round((max_cap / design_cap) * 100, 1)
        except:
            pass
        return None
    
    def _get_device_identifier(self) -> str:
        """디바이스 식별자 가져오기"""
        try:
            import subprocess
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True, check=True)
            
            # Model Identifier 추출
            for line in result.stdout.split('\n'):
                if 'Model Identifier' in line:
                    return line.split(':')[1].strip()
        except:
            pass
        return "Unknown"
    
    def _get_os_version(self) -> str:
        """macOS 버전 가져오기"""
        try:
            import subprocess
            result = subprocess.run(['sw_vers', '-productVersion'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            pass
        return "Unknown"


# 사용 예제
if __name__ == "__main__":
    history_manager = BatteryHistoryManager()
    
    # 테스트 데이터
    test_mac_data = {
        'device_name': 'MacBook Pro',
        'serial': 'ABC123456',
        'design_capacity': '5000',
        'apple_raw_max_capacity': '4800',
        'apple_raw_current_capacity': '3600',
        'cycle_count': '150',
        'is_charging': 'Yes',
        'temperature': '2950',
        'voltage': '12500',
        'amperage': '-1250'
    }
    
    # 데이터 저장 테스트
    success = history_manager.save_mac_battery_data(test_mac_data)
    print(f"Mac 데이터 저장: {'성공' if success else '실패'}")
    
    # 히스토리 조회 테스트
    history = history_manager.get_mac_history(days=1)
    print(f"저장된 히스토리 레코드 수: {len(history)}")
    
    # 백업 테스트
    backup_path = history_manager.create_backup()
    print(f"백업 생성: {backup_path}")
