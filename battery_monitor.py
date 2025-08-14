#!/usr/bin/env python3
"""
macOS Battery Monitor
Coconut Battery와 유사한 배터리 정보 모니터링 도구
"""

import subprocess
import json
import re
import sys
import shutil
import ctypes
from ctypes import c_int, c_void_p, c_char_p, c_uint32, POINTER, Structure, CFUNCTYPE
import time
from datetime import datetime, timedelta

class BatteryMonitor:
    def __init__(self):
        self.battery_data = {}
        self.ios_devices = []
        
    def get_system_profiler_data(self):
        """system_profiler를 사용하여 배터리 정보 가져오기"""
        try:
            result = subprocess.run(['system_profiler', 'SPPowerDataType'], 
                                 capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running system_profiler: {e}")
            return None
    
    def get_ioreg_data(self):
        """ioreg를 사용하여 더 상세한 배터리 정보 가져오기"""
        try:
            result = subprocess.run(['ioreg', '-rc', 'AppleSmartBattery'], 
                                 capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running ioreg: {e}")
            return None
    
    def get_power_management_data(self):
        """pmset을 사용하여 전력 관리 정보 가져오기 (Low Power Mode 등)"""
        try:
            result = subprocess.run(['pmset', '-g', 'batt'], 
                                 capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running pmset: {e}")
            return None
    
    def get_hardware_info(self):
        """시스템 하드웨어 정보 가져오기"""
        try:
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                 capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running system_profiler for hardware: {e}")
            return None
    
    def check_ios_devices(self):
        """연결된 iOS 디바이스 확인"""
        try:
            # GUI에서 사용할 때는 MobileDevice.framework 호출을 건너뛰고
            # 더 안전한 방법들만 사용
            
            # 1. libimobiledevice 사용 (가장 안전)
            if shutil.which('ideviceinfo'):
                return self._get_ios_devices_libimobiledevice()
            
            # 2. system_profiler 사용 (기본 정보만)
            return self._get_ios_devices_system_profiler()
            
            # MobileDevice.framework는 CLI에서만 사용하도록 임시로 비활성화
            # ios_devices = self._get_ios_devices_mobiledevice()
            # if ios_devices:
            #     return ios_devices
        except Exception as e:
            print(f"iOS 디바이스 확인 중 오류: {e}")
            return []
    
    def _get_ios_devices_libimobiledevice(self):
        """libimobiledevice를 사용하여 iOS 디바이스 정보 가져오기"""
        devices = []
        try:
            # 연결된 디바이스 ID 목록 가져오기
            result = subprocess.run(['idevice_id', '-l'], 
                                 capture_output=True, text=True, check=True)
            device_ids = result.stdout.strip().split('\n')
            
            for device_id in device_ids:
                if device_id.strip():
                    device_info = self._get_ios_device_info(device_id.strip())
                    if device_info:
                        devices.append(device_info)
                        
        except subprocess.CalledProcessError:
            pass
        
        return devices
    
    def _get_ios_device_info(self, device_id):
        """특정 iOS 디바이스의 배터리 정보 가져오기"""
        device_info = {'device_id': device_id}
        
        try:
            # 기본 디바이스 정보
            result = subprocess.run(['ideviceinfo', '-u', device_id], 
                                 capture_output=True, text=True, check=True)
            
            info_lines = result.stdout.split('\n')
            for line in info_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'DeviceName':
                        device_info['name'] = value
                    elif key == 'ProductType':
                        device_info['model'] = value
                    elif key == 'ProductVersion':
                        device_info['ios_version'] = value
                    elif key == 'SerialNumber':
                        device_info['serial'] = value
            
            # 배터리 정보 (iOS에서 직접 가져오기는 제한적)
            # 일반적으로는 디바이스가 충전 중인지 여부만 확인 가능
            
        except subprocess.CalledProcessError:
            return None
        
        return device_info
    
    def _get_ios_devices_system_profiler(self):
        """system_profiler를 사용하여 연결된 iOS 디바이스 확인"""
        devices = []
        try:
            result = subprocess.run(['system_profiler', 'SPUSBDataType'], 
                                 capture_output=True, text=True, check=True)
            
            # iOS 디바이스 패턴 찾기
            ios_patterns = [
                r'iPhone',
                r'iPad',
                r'iPod',
            ]
            
            for pattern in ios_patterns:
                matches = re.finditer(pattern, result.stdout, re.IGNORECASE)
                for match in matches:
                    # 간단한 디바이스 정보만 수집
                    device_info = {
                        'name': pattern,
                        'type': 'iOS Device',
                        'connection': 'USB'
                    }
                    devices.append(device_info)
                    
        except subprocess.CalledProcessError:
            pass
        
        return devices
    
    def _get_ios_devices_mobiledevice(self):
        """매OS MobileDevice.framework를 사용하여 iOS 디바이스 정보 가져오기 (CoconutBattery 방식)"""
        devices = []
        
        try:
            # MobileDevice.framework 로드 시도
            framework_path = "/System/Library/PrivateFrameworks/MobileDevice.framework/MobileDevice"
            mobile_device_lib = ctypes.CDLL(framework_path)
            
            # 기본 구조체 정의
            class AMDeviceNotification(Structure):
                _fields_ = [
                    ("unknown0", c_uint32),
                    ("unknown1", c_uint32),
                    ("unknown2", c_uint32),
                    ("callback", c_void_p),
                    ("unknown3", c_uint32),
                ]
            
            # 콜백 함수 타입
            AMDeviceNotificationCallback = CFUNCTYPE(None, POINTER(AMDeviceNotification), c_void_p)
            
            # 전역 디바이스 리스트
            found_devices = []
            
            def device_callback(notification_ptr, device_ptr):
                if device_ptr:
                    # 디바이스 연결 시도 및 배터리 정보 가져오기
                    battery_info = self._get_ios_battery_info_from_device(mobile_device_lib, device_ptr)
                    
                    device_info = {
                        'name': battery_info.get('DeviceName', 'iOS Device'),
                        'model': battery_info.get('ProductType', 'Unknown'),
                        'ios_version': battery_info.get('ProductVersion', 'Unknown'),
                        'serial': battery_info.get('SerialNumber', 'Unknown'),
                        'type': 'iOS Device',
                        'connection': 'USB',
                        'method': 'MobileDevice.framework',
                        'device_ptr': device_ptr,
                        'battery_capacity': battery_info.get('BatteryCurrentCapacity', 'Unknown'),
                        'battery_charging': battery_info.get('BatteryIsCharging', 'Unknown'),
                        'battery_voltage': battery_info.get('BatteryVoltage', 'Unknown'),
                    }
                    found_devices.append(device_info)
            
            # API 함수 설정
            try:
                mobile_device_lib.AMDeviceNotificationSubscribe.argtypes = [
                    AMDeviceNotificationCallback,
                    c_uint32,
                    c_uint32,
                    c_void_p,
                    POINTER(c_void_p)
                ]
                mobile_device_lib.AMDeviceNotificationSubscribe.restype = c_int
                
                # 콜백 생성 및 등록
                callback_func = AMDeviceNotificationCallback(device_callback)
                notification_ptr = c_void_p()
                
                # 디바이스 모니터링 시작
                result = mobile_device_lib.AMDeviceNotificationSubscribe(
                    callback_func,
                    0,
                    0,
                    None,
                    ctypes.byref(notification_ptr)
                )
                
                if result == 0:
                    # 매우 짧은 대기 시간으로 변경 (GUI 응답성 향상)
                    time.sleep(0.1)
                    devices = found_devices.copy()
                    
            except AttributeError:
                # API 함수를 찾을 수 없는 경우
                pass
                
        except OSError:
            # 프레임워크 로드 실패
            pass
        except Exception:
            # 기타 오류
            pass
        
        return devices
    
    def _get_ios_battery_info_from_device(self, mobile_device_lib, device_ptr):
        """비공개 MobileDevice.framework를 사용하여 iOS 디바이스에서 배터리 정보 추출"""
        battery_info = {}
        
        try:
            # API 함수 설정 시도
            mobile_device_lib.AMDeviceConnect.argtypes = [c_void_p]
            mobile_device_lib.AMDeviceConnect.restype = c_int
            
            mobile_device_lib.AMDeviceStartSession.argtypes = [c_void_p]
            mobile_device_lib.AMDeviceStartSession.restype = c_int
            
            mobile_device_lib.AMDeviceCopyValue.argtypes = [c_void_p, c_void_p, c_char_p]
            mobile_device_lib.AMDeviceCopyValue.restype = c_void_p
            
            mobile_device_lib.AMDeviceStopSession.argtypes = [c_void_p]
            mobile_device_lib.AMDeviceStopSession.restype = c_int
            
            mobile_device_lib.AMDeviceDisconnect.argtypes = [c_void_p]
            mobile_device_lib.AMDeviceDisconnect.restype = c_int
            
            # 1. 디바이스 연결
            connect_result = mobile_device_lib.AMDeviceConnect(device_ptr)
            if connect_result != 0:
                return battery_info
            
            # 2. 세션 시작
            session_result = mobile_device_lib.AMDeviceStartSession(device_ptr)
            if session_result != 0:
                mobile_device_lib.AMDeviceDisconnect(device_ptr)
                return battery_info
            
            # 3. 배터리 정보 요청
            battery_keys = [
                b"BatteryCurrentCapacity",   # 현재 용량 %
                b"BatteryIsCharging",        # 충전 상태
                b"BatteryVoltage",           # 전압
                b"DeviceName",               # 디바이스 이름
                b"ProductType",              # 모델명  
                b"ProductVersion",           # iOS 버전
                b"SerialNumber",             # 시리얼 번호
            ]
            
            for key in battery_keys:
                try:
                    value_ptr = mobile_device_lib.AMDeviceCopyValue(
                        device_ptr,
                        None,  # domain (None = 기본 도메인)
                        key
                    )
                    
                    if value_ptr:
                        # CoreFoundation 객체를 Python 값으로 변환
                        # 실제 구현에서는 CFStringGetCStringPtr, CFNumberGetValue 등 사용
                        # 여기서는 일단 포인터 주소만 저장
                        battery_info[key.decode()] = self._parse_cf_value(value_ptr)
                        
                except Exception:
                    # 개별 키 오류는 무시하고 계속
                    pass
            
            # 4. 세션 종료 및 연결 해제
            mobile_device_lib.AMDeviceStopSession(device_ptr)
            mobile_device_lib.AMDeviceDisconnect(device_ptr)
            
        except Exception:
            # 전체 과정에서 오류가 발생하면 마지막에 정리
            try:
                mobile_device_lib.AMDeviceStopSession(device_ptr)
                mobile_device_lib.AMDeviceDisconnect(device_ptr)
            except:
                pass
        
        return battery_info
    
    def _parse_cf_value(self, cf_value_ptr):
        """비공개 CoreFoundation 객체를 Python 값으로 변환 (간단한 구현)"""
        # 실제로는 CoreFoundation 함수들을 사용해야 하지만
        # 여기서는 일단 더미 값으로 처리
        if cf_value_ptr:
            try:
                # CoreFoundation 라이브러리 로드 시도
                cf_lib = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
                
                # CFString인지 CFNumber인지 확인하는 기능 추가 필요
                # 지금은 일단 포인터 주소만 반환
                return f"CF_Value_{hex(cf_value_ptr)}"
            except:
                return "Unknown"
        return "None"
    
    def parse_system_profiler(self, data):
        """system_profiler 출력에서 배터리 정보 파싱"""
        if not data:
            return {}
        
        battery_info = {}
        
        # 기본 정보 추출
        patterns = {
            'serial_number': r'Serial Number:\s*(\S+)',
            'device_name': r'Device Name:\s*(\S+)',
            'firmware_version': r'Firmware Version:\s*(\S+)',
            'cycle_count': r'Cycle Count:\s*(\d+)',
            'condition': r'Condition:\s*(\w+)',
            'max_capacity': r'Maximum Capacity:\s*(\d+)%',
            'state_of_charge': r'State of Charge \(%\):\s*(\d+)',
            'fully_charged': r'Fully Charged:\s*(\w+)',
            'charging': r'Charging:\s*(\w+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, data)
            if match:
                battery_info[key] = match.group(1)
        
        return battery_info
    
    def parse_ioreg_data(self, data):
        """ioreg 출력에서 배터리 정보 파싱"""
        if not data:
            return {}
        
        ioreg_info = {}
        
        # 주요 필드들 추출
        patterns = {
            'current_capacity': r'"CurrentCapacity"\s*=\s*(\d+)',
            'max_capacity': r'"MaxCapacity"\s*=\s*(\d+)', 
            'design_capacity': r'"DesignCapacity"\s*=\s*(\d+)',
            'cycle_count': r'"CycleCount"\s*=\s*(\d+)',
            'temperature': r'"Temperature"\s*=\s*(\d+)',
            'voltage': r'"Voltage"\s*=\s*(\d+)',
            'amperage': r'"Amperage"\s*=\s*(\d+)',
            'time_remaining': r'"TimeRemaining"\s*=\s*(\d+)',
            'is_charging': r'"IsCharging"\s*=\s*(\w+)',
            'fully_charged': r'"FullyCharged"\s*=\s*(\w+)',
            'external_connected': r'"ExternalConnected"\s*=\s*(\w+)',
            'apple_raw_current_capacity': r'"AppleRawCurrentCapacity"\s*=\s*(\d+)',
            'apple_raw_max_capacity': r'"AppleRawMaxCapacity"\s*=\s*(\d+)',
            'nominal_charge_capacity': r'"NominalChargeCapacity"\s*=\s*(\d+)',
            'serial': r'"Serial"\s*=\s*"([^"]+)"',
            'device_name': r'"DeviceName"\s*=\s*"([^"]+)"',
            # LifetimeData에서 더 합리적인 온도 값 추출
            'average_temperature': r'"AverageTemperature"\s*=\s*(\d+)',
            'max_temperature': r'"MaximumTemperature"\s*=\s*(\d+)',
            'min_temperature': r'"MinimumTemperature"\s*=\s*(\d+)',
            # 배터리 제조 정보
            'manufacture_date': r'"ManufactureDate"\s*=\s*(\d+)',
            'manufacturer': r'"Manufacturer"\s*=\s*"([^"]+)"',
            'pack_lot_code': r'"PackLotCode"\s*=\s*"([^"]+)"',
            'battery_serial': r'"BatterySerialNumber"\s*=\s*"([^"]+)"',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, data)
            if match:
                ioreg_info[key] = match.group(1)
        
        return ioreg_info
    
    def parse_power_management_data(self, data):
        """pmset 출력에서 전력 관리 정보 파싱 (Low Power Mode 등)"""
        if not data:
            return {}
        
        pm_info = {}
        
        # Low Power Mode 감지
        if 'lowpowermode' in data.lower():
            # macOS에서 Low Power Mode 상태 확인
            if re.search(r'lowpowermode\s+1', data, re.IGNORECASE):
                pm_info['low_power_mode'] = True
            else:
                pm_info['low_power_mode'] = False
        else:
            pm_info['low_power_mode'] = False
        
        # 배터리 상태에서 현재 전력 사용량 추출
        power_match = re.search(r'(\d+)W', data)
        if power_match:
            pm_info['current_power_usage'] = int(power_match.group(1))
        
        # 어댑터 연결 상태
        if "AC Power" in data:
            pm_info['power_adapter_connected'] = True
        elif "Battery Power" in data:
            pm_info['power_adapter_connected'] = False
        
        return pm_info
    
    def parse_hardware_info(self, data):
        """하드웨어 정보 파싱"""
        if not data:
            return {}
        
        hw_info = {}
        
        patterns = {
            'model_name': r'Model Name:\s*(.+)',
            'model_identifier': r'Model Identifier:\s*(.+)',
            'processor': r'Processor Name:\s*(.+)',
            'processor_speed': r'Processor Speed:\s*(.+)',
            'number_of_processors': r'Number of Processors:\s*(\d+)',
            'total_cores': r'Total Number of Cores:\s*(\d+)',
            'memory': r'Memory:\s*(.+)',
            'boot_rom': r'Boot ROM Version:\s*(.+)',
            'serial': r'Serial Number \(system\):\s*(.+)',
            'hardware_uuid': r'Hardware UUID:\s*(.+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, data)
            if match:
                hw_info[key] = match.group(1).strip()
        
        return hw_info
    
    def format_manufacture_date(self, date_raw):
        """제조일 포맷팅 (UNIX timestamp에서 날짜로)"""
        if date_raw:
            try:
                # macOS 배터리 제조일은 보통 Mac Epoch (2001-01-01 기준)에서의 초
                timestamp = int(date_raw)
                # Mac Epoch는 2001-01-01 00:00:00 UTC
                import calendar
                from datetime import datetime, timezone
                
                mac_epoch = datetime(2001, 1, 1, tzinfo=timezone.utc)
                manufacture_date = mac_epoch + timedelta(seconds=timestamp)
                return manufacture_date.strftime('%Y-%m-%d')
            except:
                return date_raw
        return None
    
    def calculate_battery_age(self):
        """배터리 나이 계산 (제조일 기준)"""
        manufacture_date = self.battery_data.get('manufacture_date')
        if manufacture_date:
            formatted_date = self.format_manufacture_date(manufacture_date)
            if formatted_date:
                try:
                    from datetime import datetime
                    mfg_date = datetime.strptime(formatted_date, '%Y-%m-%d')
                    age = datetime.now() - mfg_date
                    return age.days
                except:
                    pass
        return None
    
    def calculate_battery_health(self):
        """배터리 건강도 계산"""
        if 'apple_raw_max_capacity' in self.battery_data and 'design_capacity' in self.battery_data:
            current_max = int(self.battery_data['apple_raw_max_capacity'])
            design = int(self.battery_data['design_capacity'])
            health_percentage = round((current_max / design) * 100, 1)
            return health_percentage
        return None
    
    def format_temperature(self, temp_raw):
        """온도 포맷팅 - macOS 배터리 온도는 켈빈의 10배 단위"""
        if temp_raw:
            temp_value = int(temp_raw)
            # LifetimeData의 온도 값은 섭씨로 보임 (합리적 범위)
            if temp_value < 100:  # 섭씨로 추정되는 경우 (LifetimeData)
                return temp_value
            else:  # 켈빈의 10배로 추정되는 경우 (Temperature 필드)
                temp_kelvin = temp_value / 10.0
                temp_celsius = temp_kelvin - 273.15
                return round(temp_celsius, 1)
        return None
    
    def format_voltage(self, voltage_raw):
        """전압 포맷팅"""
        if voltage_raw:
            voltage_mv = int(voltage_raw)
            voltage_v = voltage_mv / 1000.0
            return round(voltage_v, 3)
        return None
    
    def format_amperage(self, amperage_raw):
        """전류 포맷팅 (음수 처리)"""
        if amperage_raw:
            amperage = int(amperage_raw)
            # 64비트 음수 처리 (2의 보수)
            if amperage > 2**63:
                amperage = amperage - 2**64
            amperage_ma = amperage
            return amperage_ma
        return None
    
    def format_time_remaining(self, time_raw):
        """남은 시간 포맷팅 (분 → 시:분)"""
        if time_raw and int(time_raw) != 65535:  # 65535는 무한대 표시
            minutes = int(time_raw)
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}:{mins:02d}"
        return "Calculating..."
    
    def collect_all_data(self):
        """모든 배터리 데이터 수집"""
        print("배터리 정보를 수집하는 중...")
        
        # system_profiler 데이터
        sp_data = self.get_system_profiler_data()
        sp_info = self.parse_system_profiler(sp_data)
        
        # ioreg 데이터
        ioreg_data = self.get_ioreg_data()
        ioreg_info = self.parse_ioreg_data(ioreg_data)
        
        # 전력 관리 데이터 (Low Power Mode 등)
        pm_data = self.get_power_management_data()
        pm_info = self.parse_power_management_data(pm_data)
        
        # 하드웨어 정보
        hw_data = self.get_hardware_info()
        hw_info = self.parse_hardware_info(hw_data)
        
        # iOS 디바이스 확인
        self.ios_devices = self.check_ios_devices()
        
        # 데이터 합치기
        self.battery_data.update(sp_info)
        self.battery_data.update(ioreg_info)
        self.battery_data.update(pm_info)
        self.battery_data.update(hw_info)
        
    def display_battery_info(self):
        """배터리 정보를 보기 좋게 표시"""
        if not self.battery_data:
            print("배터리 정보를 가져올 수 없습니다.")
            return
        
        print("\n" + "="*60)
        print("🔋 배터리 모니터 - macOS Battery Info")
        print("="*60)
        
        # 기본 정보
        print(f"📱 디바이스: {self.battery_data.get('device_name', 'N/A')}")
        print(f"🔢 시리얼: {self.battery_data.get('serial', 'N/A')}")
        print(f"💾 펌웨어: {self.battery_data.get('firmware_version', 'N/A')}")
        
        print("\n" + "-"*40)
        print("📊 현재 상태")
        print("-"*40)
        
        # 현재 충전량
        current_capacity = self.battery_data.get('current_capacity')
        if current_capacity:
            print(f"🔋 현재 충전량: {current_capacity}%")
        
        # 충전 상태
        is_charging = self.battery_data.get('is_charging', self.battery_data.get('charging'))
        fully_charged = self.battery_data.get('fully_charged')
        external_connected = self.battery_data.get('external_connected')
        
        if is_charging == 'Yes':
            print("⚡ 상태: 충전 중")
        elif fully_charged == 'Yes':
            print("✅ 상태: 충전 완료")
        elif external_connected == 'Yes':
            print("🔌 상태: 어댑터 연결됨 (충전 안함)")
        else:
            print("🔋 상태: 배터리 사용 중")
        
        # 남은 시간
        time_remaining = self.battery_data.get('time_remaining')
        if time_remaining:
            formatted_time = self.format_time_remaining(time_remaining)
            print(f"⏱️  남은 시간: {formatted_time}")
        
        print("\n" + "-"*40)
        print("🏥 배터리 건강도")
        print("-"*40)
        
        # 사이클 수
        cycle_count = self.battery_data.get('cycle_count')
        if cycle_count:
            print(f"🔄 사이클 수: {cycle_count}회")
        
        # 최대 용량 (건강도)
        health = self.calculate_battery_health()
        if health:
            print(f"💚 배터리 건강도: {health}%")
        
        condition = self.battery_data.get('condition')
        if condition:
            print(f"🏥 컨디션: {condition}")
        
        print("\n" + "-"*40)
        print("🔧 기술적 정보")
        print("-"*40)
        
        # 설계 용량 vs 현재 최대 용량
        design_capacity = self.battery_data.get('design_capacity')
        apple_raw_max = self.battery_data.get('apple_raw_max_capacity')
        apple_raw_current = self.battery_data.get('apple_raw_current_capacity')
        
        if design_capacity:
            print(f"🏭 설계 용량: {design_capacity} mAh")
        if apple_raw_max:
            print(f"📊 현재 최대 용량: {apple_raw_max} mAh")
        if apple_raw_current:
            print(f"⚡ 현재 용량: {apple_raw_current} mAh")
        
        # 온도 표시 (임시 주석 처리 - 단위 변환 문제로 인해)
        # avg_temp = self.battery_data.get('average_temperature')
        # temperature = self.battery_data.get('temperature')
        # 
        # if avg_temp:
        #     temp_celsius = self.format_temperature(avg_temp)
        #     print(f"🌡️  평균 온도: {temp_celsius}°C")
        # elif temperature:
        #     temp_celsius = self.format_temperature(temperature)
        #     print(f"🌡️  온도: {temp_celsius}°C")
        
        # 전압
        voltage = self.battery_data.get('voltage')
        if voltage:
            voltage_v = self.format_voltage(voltage)
            print(f"⚡ 전압: {voltage_v}V")
        
        # 전류
        amperage = self.battery_data.get('amperage')
        if amperage:
            amperage_ma = self.format_amperage(amperage)
            print(f"🔌 전류: {amperage_ma} mA")
        
        # iOS 디바이스 정보 표시
        if self.ios_devices:
            print("\n" + "-"*40)
            print("📱 연결된 iOS 디바이스")
            print("-"*40)
            
            for i, device in enumerate(self.ios_devices, 1):
                print(f"📱 디바이스 #{i}:")
                print(f"  • 이름: {device.get('name', 'N/A')}")
                print(f"  • 모델: {device.get('model', 'N/A')}")
                if 'ios_version' in device and device['ios_version'] != 'Unknown':
                    print(f"  • iOS: {device['ios_version']}")
                if 'serial' in device and device['serial'] != 'Unknown':
                    print(f"  • 시리얼: {device['serial']}")
                print(f"  • 연결: {device.get('connection', 'USB')}")
                
                # 배터리 정보 표시 (MobileDevice.framework로 가져온 경우)
                if 'battery_capacity' in device and device['battery_capacity'] != 'Unknown':
                    print(f"  🔋 배터리 잘어용 %: {device['battery_capacity']}")
                if 'battery_charging' in device and device['battery_charging'] != 'Unknown':
                    charging_status = "충전 중" if device['battery_charging'] == 'True' else "방전 중"
                    print(f"  ⚡ 충전 상태: {charging_status}")
                if 'battery_voltage' in device and device['battery_voltage'] != 'Unknown':
                    print(f"  ⚡ 전압: {device['battery_voltage']}V")
                
                # 방식에 따른 알림 메시지
                if device.get('method') == 'MobileDevice.framework':
                    print(f"  ✅ CoconutBattery 방식으로 연결 성공!")
                elif not shutil.which('ideviceinfo'):
                    print(f"  ⚠️  상세 정보를 위해 'brew install libimobiledevice' 설치 권장")
                print()
        else:
            if not shutil.which('ideviceinfo'):
                print("\n" + "-"*40)
                print("📱 iOS 디바이스")
                print("-"*40)
                print("🔍 연결된 iOS 디바이스가 없습니다.")
                print("📝 디바이스 연결 후 'brew install libimobiledevice'로 더 상세한 정보를 얻을 수 있습니다.")
        
        print("\n" + "="*60)
        print(f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

def main():
    """메인 함수"""
    try:
        monitor = BatteryMonitor()
        monitor.collect_all_data()
        monitor.display_battery_info()
        
    except KeyboardInterrupt:
        print("\n프로그램이 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
