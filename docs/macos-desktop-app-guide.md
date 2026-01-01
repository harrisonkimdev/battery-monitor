# Python 프로젝트를 macOS 데스크톱 앱으로 빌드하기

이 문서는 Python 프로젝트를 macOS 네이티브 데스크톱 애플리케이션(`.app` 번들)으로 패키징하는 방법을 설명합니다. `py2app`을 사용한 빌드 과정과 발생할 수 있는 문제들의 해결 방법을 다룹니다.

## 📋 목차

1. [개요](#개요)
2. [py2app 이해하기](#py2app-이해하기)
3. [환경 설정](#환경-설정)
4. [setup.py 작성](#setuppy-작성)
5. [빌드 프로세스](#빌드-프로세스)
6. [빌드 후 처리](#빌드-후-처리)
7. [일반적인 문제와 해결방법](#일반적인-문제와-해결방법)
8. [배포 준비](#배포-준비)

## 개요

### py2app이란?

`py2app`은 Python 애플리케이션을 macOS 네이티브 앱 번들(`.app`)로 변환하는 도구입니다. 이를 통해:

- Python 인터프리터와 모든 의존성을 하나의 앱 번들에 포함
- 사용자가 Python을 설치하지 않아도 앱 실행 가능
- Finder에서 더블클릭으로 실행 가능한 네이티브 앱 생성

### 앱 번들 구조

macOS 앱 번들의 기본 구조:

```
YourApp.app/
├── Contents/
    ├── Info.plist              # 앱 메타데이터
    ├── MacOS/
    │   ├── YourApp             # 실행 파일
    │   └── python              # 번들된 Python 인터프리터
    ├── Resources/              # Python 코드와 리소스
    │   ├── __boot__.py
    │   ├── your_script.py
    │   └── lib/
    └── Frameworks/             # 동적 라이브러리 (.dylib)
        ├── libpython3.11.dylib
        ├── libtk8.6.dylib
        └── ...
```

## py2app 이해하기

### 빌드 모드

py2app은 두 가지 빌드 모드를 지원합니다:

1. **Alias Mode** (개발용)
   ```bash
   python setup.py py2app -A
   ```
   - 원본 소스 파일을 심볼릭 링크로 참조
   - 빠른 빌드, 코드 수정 즉시 반영
   - 배포 불가능

2. **Deployment Mode** (배포용)
   ```bash
   python setup.py py2app
   ```
   - 모든 파일을 앱 번들에 복사
   - 독립 실행 가능한 앱 생성
   - 다른 Mac에서 실행 가능

### Standalone vs Semi-Standalone

- **Standalone**: 모든 의존성을 번들에 포함 (권장)
- **Semi-Standalone**: 시스템 Python 프레임워크 사용 (비권장)

## 환경 설정

### 1. 필수 도구 설치

```bash
# Xcode Command Line Tools (코드 서명용)
xcode-select --install

# py2app 설치
pip install py2app
```

### 2. Python 환경 권장사항

**Conda 환경 사용을 강력히 권장합니다:**

```bash
# Conda 환경 생성
conda create -n myapp python=3.11
conda activate myapp

# 필요한 패키지 설치
conda install tk  # Tkinter GUI 사용 시
pip install py2app
```

**이유:**
- Conda는 필요한 모든 동적 라이브러리(`.dylib`)를 환경 내에 포함
- Homebrew Python은 시스템 라이브러리에 의존하여 배포 시 문제 발생 가능
- 환경 격리로 의존성 충돌 방지

## setup.py 작성

### 기본 구조

```python
"""
setup.py for creating macOS app bundle
"""

from setuptools import setup
import os
import sys

APP = ['main.py']  # 메인 실행 파일
DATA_FILES = []    # 리소스 파일 (이미지, 설정 등)

# 아이콘 추가 (선택사항)
if os.path.exists('icon.icns'):
    DATA_FILES.append(('', ['icon.icns']))

OPTIONS = {
    'argv_emulation': True,  # 파일 드래그앤드롭 지원
    'iconfile': 'icon.icns' if os.path.exists('icon.icns') else None,
    'includes': [
        # 명시적으로 포함할 모듈
        'tkinter',
        'tkinter.ttk',
        'sqlite3',
    ],
    'packages': [
        # 패키지 전체를 포함
    ],
    'excludes': [
        # 제외할 불필요한 패키지 (앱 크기 감소)
        'matplotlib',
        'numpy',
        'PIL',
        'PyQt5',
        'PyQt6',
    ],
    'frameworks': [],  # 추가 동적 라이브러리
    'site_packages': False,  # Standalone 모드
    'semi_standalone': False,  # 완전 독립 실행
    'strip': False,  # 디버그 심볼 유지 (개발 시)
    'optimize': 0,  # 최적화 레벨 (0=없음, 1=일부, 2=전체)
    'plist': {
        'CFBundleName': 'MyApp',
        'CFBundleDisplayName': 'My Application',
        'CFBundleIdentifier': 'com.example.myapp',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,  # True면 Dock에 표시 안함
    }
}

setup(
    app=APP,
    name='MyApp',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

### 동적 라이브러리 자동 탐지

Conda 환경의 라이브러리를 자동으로 찾아 포함:

```python
import sys
import os

frameworks = []

# libffi 찾기
libffi_path = os.path.join(os.path.dirname(sys.executable), '../lib/libffi.8.dylib')
if os.path.exists(libffi_path):
    print(f"✅ Found libffi at: {libffi_path}")
    frameworks.append(libffi_path)

# Tcl/Tk 라이브러리 (Tkinter 사용 시 필수)
for lib in ['libtk8.6.dylib', 'libtcl8.6.dylib']:
    lib_path = os.path.join(os.path.dirname(sys.executable), '../lib', lib)
    if os.path.exists(lib_path):
        print(f"✅ Found {lib} at: {lib_path}")
        frameworks.append(lib_path)

# SQLite 라이브러리 (sqlite3 모듈 사용 시 필수)
sqlite_path = os.path.join(os.path.dirname(sys.executable), '../lib/libsqlite3.0.dylib')
if os.path.exists(sqlite_path):
    print(f"✅ Found sqlite3 at: {sqlite_path}")
    frameworks.append(sqlite_path)

OPTIONS = {
    # ... 기타 옵션 ...
    'frameworks': frameworks,
}
```

## 빌드 프로세스

### 1. 이전 빌드 정리

```bash
rm -rf build dist
```

### 2. 앱 빌드

```bash
# Conda 환경 활성화 (사용 시)
conda activate myapp

# 빌드 실행
python setup.py py2app
```

빌드 출력 예시:
```
running py2app
creating build/bdist.macosx-11.1-arm64
creating build/bdist.macosx-11.1-arm64/python3.11-standalone
...
copying libffi.8.dylib -> dist/MyApp.app/Contents/Frameworks/
copying libtk8.6.dylib -> dist/MyApp.app/Contents/Frameworks/
...
Done!
```

### 3. 빌드 확인

```bash
# 앱 번들 구조 확인
ls -R dist/MyApp.app/Contents/

# 필수 라이브러리 확인
ls dist/MyApp.app/Contents/Frameworks/
```

## 빌드 후 처리

### RPATH 설정

동적 라이브러리 로딩 경로를 설정해야 합니다. 이는 py2app이 자동으로 처리하지 못하는 경우가 많습니다.

```bash
# 메인 실행 파일에 RPATH 추가
install_name_tool -add_rpath @executable_path/../Frameworks \
  dist/MyApp.app/Contents/MacOS/MyApp

# 번들된 Python 인터프리터에도 추가
install_name_tool -add_rpath @executable_path/../Frameworks \
  dist/MyApp.app/Contents/MacOS/python
```

**RPATH란?**
- Runtime Search Path: 실행 시 동적 라이브러리를 찾는 경로
- `@executable_path`: 실행 파일의 위치를 기준으로 한 상대 경로
- `@loader_path`: 라이브러리를 로드하는 파일의 위치 기준

### 코드 서명

macOS 보안 정책을 통과하기 위해 앱에 서명해야 합니다:

```bash
# Ad-hoc 서명 (개발용)
codesign --force --deep --sign - dist/MyApp.app
```

**프로덕션 배포 시:**
```bash
# Apple Developer ID로 서명
codesign --force --deep --sign "Developer ID Application: Your Name" dist/MyApp.app

# 공증 (Notarization)
xcrun notarytool submit dist/MyApp.app --apple-id your@email.com --wait
```

### Quarantine 속성 제거

다운로드된 앱의 실행 제한을 해제:

```bash
xattr -cr dist/MyApp.app
```

## 일반적인 문제와 해결방법

### 문제 1: "Library not loaded" 오류

**증상:**
```
ImportError: dlopen(.../_tkinter.so): Library not loaded: @rpath/libtk8.6.dylib
```

**원인:** 동적 라이브러리를 찾을 수 없음

**해결 방법:**

1. 라이브러리가 번들에 포함되었는지 확인:
```bash
ls dist/MyApp.app/Contents/Frameworks/
```

2. RPATH가 설정되었는지 확인:
```bash
otool -l dist/MyApp.app/Contents/MacOS/MyApp | grep -A2 LC_RPATH
```

3. RPATH 추가:
```bash
install_name_tool -add_rpath @executable_path/../Frameworks \
  dist/MyApp.app/Contents/MacOS/MyApp
codesign --force --deep --sign - dist/MyApp.app
```

4. 라이브러리의 install name 확인:
```bash
otool -L dist/MyApp.app/Contents/Resources/lib/python3.11/lib-dynload/_tkinter.so
```

### 문제 2: "Symbol not found" 오류

**증상:**
```
Symbol not found: _sqlite3_enable_load_extension
```

**원인:** 잘못된 버전의 라이브러리 또는 시스템 라이브러리와 충돌

**해결 방법:**

1. Conda 환경의 라이브러리 사용 확인:
```bash
# 현재 환경의 라이브러리 확인
ls -l $CONDA_PREFIX/lib/libsqlite3*

# setup.py에서 올바른 경로 지정
sqlite_path = os.path.join(os.path.dirname(sys.executable), '../lib/libsqlite3.0.dylib')
```

2. 라이브러리 의존성 확인:
```bash
otool -L dist/MyApp.app/Contents/Frameworks/libsqlite3.0.dylib
```

3. 필요시 install name 수정:
```bash
install_name_tool -id @executable_path/../Frameworks/libsqlite3.0.dylib \
  dist/MyApp.app/Contents/Frameworks/libsqlite3.0.dylib
```

### 문제 3: 모듈 Import 실패

**증상:**
```
ModuleNotFoundError: No module named 'your_module'
```

**원인:** py2app이 모듈을 자동으로 감지하지 못함

**해결 방법:**

1. `setup.py`의 `includes`에 명시적으로 추가:
```python
'includes': [
    'your_module',
    'your_module.submodule',
],
```

2. 패키지 전체를 포함:
```python
'packages': [
    'your_package',
],
```

3. 로컬 모듈 경로 추가:
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

setup(
    # ...
    py_modules=['your_module'],  # 로컬 모듈 명시
)
```

### 문제 4: Tkinter 관련 오류

**증상:**
```
ModuleNotFoundError: No module named '_tkinter'
```

**원인:** Tkinter가 제대로 번들되지 않음

**해결 방법:**

1. Conda 환경에서 Tkinter 설치 확인:
```bash
conda activate myapp
python -c "import tkinter; print('OK')"
```

2. tk 패키지 설치:
```bash
conda install tk
```

3. Tcl/Tk 라이브러리를 frameworks에 추가 (위의 setup.py 예시 참조)

4. 환경 변수 설정 확인 (`__boot__.py`에 자동 추가됨):
```python
os.putenv("TCL_LIBRARY", os.path.join(resourcepath, "lib/tcl8"))
os.putenv("TK_LIBRARY", os.path.join(resourcepath, "lib/tk8.6"))
```

### 문제 5: "App is damaged" 경고

**증상:** macOS에서 앱이 손상되었다고 표시

**원인:** 코드 서명 문제 또는 Gatekeeper 제한

**해결 방법:**

1. 코드 재서명:
```bash
codesign --force --deep --sign - dist/MyApp.app
```

2. Quarantine 속성 제거:
```bash
xattr -cr dist/MyApp.app
```

3. 사용자에게 실행 권한 부여 안내:
   - 시스템 환경설정 > 보안 및 개인정보 보호
   - "확인 없이 열기" 클릭

### 문제 6: 앱이 시작되지 않음 (무반응)

**증상:** 앱을 실행해도 아무 반응 없음

**진단 방법:**

1. 터미널에서 직접 실행:
```bash
./dist/MyApp.app/Contents/MacOS/MyApp
```

2. Console.app에서 로그 확인:
   - `/Applications/Utilities/Console.app` 실행
   - "Crash Reports" 또는 "system.log" 확인

3. 번들된 Python으로 직접 테스트:
```bash
./dist/MyApp.app/Contents/MacOS/python -c "import sys; print(sys.path)"
```

## 배포 준비

### 1. 프로덕션 빌드 최적화

```python
OPTIONS = {
    # ...
    'optimize': 2,      # 최대 최적화
    'strip': True,      # 디버그 심볼 제거
    'excludes': [
        # 불필요한 대용량 패키지 제외
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'test',
        'unittest',
    ],
}
```

### 2. 앱 크기 확인

```bash
du -sh dist/MyApp.app
```

### 3. 다른 Mac에서 테스트

- 빌드 환경과 다른 macOS 버전에서 테스트
- Python이 설치되지 않은 환경에서 테스트
- 다양한 하드웨어(Intel/Apple Silicon)에서 테스트

### 4. DMG 생성

배포용 디스크 이미지 생성:

```bash
# create-dmg 설치
brew install create-dmg

# DMG 생성
create-dmg \
  --volname "MyApp" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "MyApp.app" 200 190 \
  --hide-extension "MyApp.app" \
  --app-drop-link 600 185 \
  "MyApp-1.0.0.dmg" \
  "dist/MyApp.app"
```

### 5. 공증 (Notarization)

App Store 외부 배포 시 필수 (macOS 10.15+):

```bash
# 앱 압축
ditto -c -k --keepParent dist/MyApp.app MyApp.zip

# 공증 제출
xcrun notarytool submit MyApp.zip \
  --apple-id your@email.com \
  --team-id TEAMID \
  --password app-specific-password \
  --wait

# 공증 티켓 스테이플
xcrun stapler staple dist/MyApp.app
```

## 디버깅 팁

### 빌드 과정 상세 로그

```bash
python setup.py py2app --verbose
```

### 라이브러리 의존성 추적

```bash
# 실행 파일의 의존성 확인
otool -L dist/MyApp.app/Contents/MacOS/MyApp

# 모든 .dylib 파일의 의존성 확인
find dist/MyApp.app -name "*.dylib" -exec otool -L {} \;

# .so 파일의 의존성 확인
find dist/MyApp.app -name "*.so" -exec otool -L {} \;
```

### Python 경로 확인

```bash
./dist/MyApp.app/Contents/MacOS/python -c "
import sys
print('Python paths:')
for p in sys.path:
    print(f'  {p}')
"
```

## 참고 자료

### 공식 문서
- [py2app 공식 문서](https://py2app.readthedocs.io/)
- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/code_signing_services)
- [macOS App Bundle Structure](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html)

### 유용한 도구
- `otool`: 바이너리 분석 도구 (macOS 기본 제공)
- `install_name_tool`: 동적 라이브러리 경로 수정 도구
- `codesign`: 코드 서명 도구
- `create-dmg`: DMG 생성 도구

### 대안 도구
- **PyInstaller**: 크로스 플랫폼 지원 (macOS, Windows, Linux)
- **Briefcase**: BeeWare 프로젝트의 패키징 도구
- **Nuitka**: Python을 C로 컴파일하여 실행 파일 생성

## 체크리스트

빌드 전:
- [ ] Conda 환경 설정 완료
- [ ] 모든 의존성 설치 확인
- [ ] setup.py 작성 및 검증
- [ ] 아이콘 파일 준비 (.icns)

빌드 후:
- [ ] 앱 번들 구조 확인
- [ ] 필수 라이브러리 포함 확인
- [ ] RPATH 설정 완료
- [ ] 코드 서명 완료
- [ ] 로컬에서 실행 테스트

배포 전:
- [ ] 다른 Mac에서 테스트
- [ ] 앱 크기 최적화
- [ ] DMG 생성 (선택사항)
- [ ] 공증 완료 (필수)
- [ ] 사용자 문서 작성

---

**작성일**: 2026-01-01  
**py2app 버전**: 0.28.x  
**테스트 환경**: macOS 14 Sonoma, Python 3.11
