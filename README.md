# 🔋 Battery Monitor

macOS용 배터리 모니터링 도구 - CoconutBattery의 오픈소스 대안

## ✨ 주요 기능

- **macOS 배터리 정보**: 현재 충전량, 건강도, 사이클 수, 온도, 전압 등
- **iOS 디바이스 지원**: 연결된 iPhone/iPad의 배터리 정보 (MobileDevice.framework 사용)
- **실시간 모니터링**: 자동 새로고침으로 실시간 정보 업데이트
- **GUI 인터페이스**: 사용하기 쉬운 그래픽 인터페이스
- **CLI 버전**: 터미널에서 사용 가능한 명령줄 버전

## 🚀 사용 방법

### GUI 버전 (권장)
```bash
python3 battery_monitor_gui.py
```

### CLI 버전
```bash
python3 battery_monitor.py
```

## 📱 iOS 디바이스 지원

이 앱은 CoconutBattery와 동일한 방식으로 iOS 디바이스의 배터리 정보를 가져옵니다:

1. **MobileDevice.framework** (최우선): Apple의 비공개 프레임워크를 직접 사용
2. **libimobiledevice** (대체): `brew install libimobiledevice` 설치 후 사용
3. **system_profiler** (기본): 제한적이지만 기본적인 디바이스 감지

### iOS 디바이스 연결하기
1. Lightning/USB-C 케이블로 iOS 디바이스를 Mac에 연결
2. "이 컴퓨터를 신뢰하시겠습니까?" 메시지에서 "신뢰" 선택
3. Battery Monitor 실행

## 🏗️ 앱 번들 생성

macOS 네이티브 앱으로 만들려면:

1. py2app 설치:
   ```bash
   pip3 install py2app
   ```

2. 앱 번들 생성:
   ```bash
   python3 setup.py py2app
   ```

3. 생성된 앱은 `dist/Battery Monitor.app`에 있습니다

## 📋 시스템 요구사항

- macOS 10.15 Catalina 이상
- Python 3.7 이상
- Tkinter (Python 기본 포함)

## 🔧 기술적 세부사항

### macOS 배터리 정보
- `system_profiler SPPowerDataType`: 기본 배터리 정보
- `ioreg -rc AppleSmartBattery`: 상세 기술 정보

### iOS 배터리 정보
- **MobileDevice.framework**: Apple 비공개 API 직접 호출
  - `AMDeviceNotificationSubscribe`: 디바이스 연결 모니터링
  - `AMDeviceConnect`: 디바이스 연결
  - `AMDeviceCopyValue`: 배터리 정보 추출
- **ctypes**: Python에서 C 라이브러리 호출
- **CoreFoundation**: Apple 객체 파싱

## 📊 표시 정보

### macOS 배터리
- 현재 충전량 (%)
- 충전 상태 (충전 중/완료/배터리 사용)
- 남은 시간
- 사이클 수
- 배터리 건강도 (%)
- 설계/현재/최대 용량 (mAh)
- 전압 (V) / 전류 (mA)

### iOS 디바이스
- 디바이스 이름, 모델, iOS 버전
- 배터리 충전량 (%)
- 충전 상태
- 전압
- 연결 방식

## ⚠️ 주의사항

- iOS 배터리 정보는 Apple의 비공개 API를 사용하므로 향후 macOS 업데이트에서 동작하지 않을 수 있습니다
- 일부 기능은 관리자 권한이 필요할 수 있습니다
- MobileDevice.framework는 Apple 개발자만 문서화된 API이므로 예상과 다르게 동작할 수 있습니다

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 만듭니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 만듭니다

## 🐛 버그 리포트 / 기능 요청

[GitHub Issues](https://github.com/harrisonkim/battery-monitor/issues)에서 버그를 신고하거나 새로운 기능을 요청해주세요.

---

**CoconutBattery**의 오픈소스 대안으로 만들어진 프로젝트입니다. 💚
