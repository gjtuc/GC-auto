# GC3 장비 PC 설치·운영 (Windows 7)

> **이 PC(GC8860)** 에서 개발 → **GC3 Win7 장비 PC** 로 zip 복사 → 동일 자동화 실행  
> GC3에는 Cursor·Git 없어도 됩니다.

---

## 역할 구분

| PC | 역할 | 배포 방법 |
|----|------|-----------|
| **GC8860** (지금 PC) | GC2 운영 + GC3 코드 개발 | `git pull` / Cursor |
| **GC3 Win7** | Chem32 Report → KCH xlsx + 메일 | USB zip (`gc3_make_deploy_zip.bat`) |

GC2와 GC3는 **같은 repo·같은 bat** (`gc_start_watch.bat`, `gc_동작해줘.bat` 등)을 씁니다.  
차이는 `Desktop\KCH\gc_automation.env` 의 `GC_INSTANCE` / `CHEMSTATION_MODE` / Data 경로뿐입니다.

---

## A. GC8860에서 — 배포 zip 만들기

```bat
cd C:\Users\User\chemstation-gc-automation
gc3_make_deploy_zip.bat
```

생성 파일:

- `deploy\GC3_chem32-gc-automation.zip`
- `Desktop\KCH\GC3_chem32-gc-automation.zip` (복사본)

USB에 zip을 넣어 GC3 PC로 옮깁니다.

코드 수정 후 GC3에 반영할 때마다 **zip 다시 만들고 덮어쓰기** (또는 변경된 `.py`만 복사).

### GC8860에서 GC3 코드 테스트 (mock)

```bat
python -m pytest test_gc_chem32.py -q
python gc_automation.py --chemstation-mode chem32 --data-path test_fixtures\chem32 --force --no-email --no-wifi-check
```

---

## B. GC3 Win7 PC — 최초 설치 (1회)

### B.1 Python 3.8

1. https://www.python.org/downloads/release/python-3810/  
2. **Windows x86-64 executable installer**  
3. 설치 시 **Add python.exe to PATH** 체크

### B.2 zip 풀기

```
C:\Users\User\chemstation-gc-automation\
```

(경로가 다르면 `gc3_바탕화면_바로가기.bat` 안의 `GC_PROJ` 경로를 맞출 것)

### B.3 설치 스크립트

```bat
cd C:\Users\User\chemstation-gc-automation
gc3_setup.bat
```

- `requirements-gc3.txt` 설치 (pandas, openpyxl, python-dotenv)
- `deploy\gc_automation.env.gc3` → `Desktop\KCH\gc_automation.env` 복사
- 바탕화면 바로가기 3개 생성

### B.4 env 수정 (필수)

```bat
notepad %USERPROFILE%\Desktop\KCH\gc_automation.env
```

| 키 | GC3 값 |
|----|--------|
| `GC_INSTANCE` | `gc3` |
| `CHEMSTATION_MODE` | `chem32` |
| `CHEMSTATION_DATA_PATH` | `C:\Chem32\1\Data` |
| `REQUIRED_HOTSPOT` | `iptime,iptime 2,iptime_5G` (GC2와 동일) |
| `IPTIME_WIFI_PSK` | `12121212` — 부팅 시 WLAN 자동 연결 (`gc_wifi_autoconnect.py`) |
| `NAVER_APP_PASSWORD` | 네이버 앱 비밀번호 (실제 값) |

확인:

```bat
python gc_automation.py --show-profile
```

`인스턴스: gc3`, `ChemStation 모드: chem32`, `Data 경로: C:\Chem32\1\Data` 가 나와야 합니다.

### B.5 부팅 시 자동 감시 (1회)

```bat
gc_install_autostart.bat
```

로그인하면 `gc_start_watch.bat` 이 백그라운드로 실행됩니다.

---

## C. GC3 일상 운영 (GC2와 동일)

| 작업 | 방법 |
|------|------|
| 수동 처리 (force) | `Desktop\KCH\GC3_동작해줘.bat` 또는 `gc_동작해줘.bat` |
| 감시 시작 | `GC3_감시시작.bat` / `gc_start_watch.bat` |
| 정상 여부 | `GC3_상태확인.bat` / `gc_verify.bat` (바탕화면 `MMDDHHmm.txt` ±5분) |
| 감시 중지 | `gc_stop_watch.bat` |

동작 요약:

1. 15초마다 핫스팟 연결·heartbeat txt 갱신  
2. 핫스팟 연결 + Chem32 새 Report → 엑셀 생성 + 메일  
3. 자동 메일 **1시간 쿨다운** (기본 `AUTO_MAIL_COOLDOWN_HOURS=1`) — 핫스pot 재연결 불필요, SMTP 검증 성공 후 0/1  
4. 메일 실패 시 인터넷 복구 후 재시도  

---

## D. 업데이트 (코드 변경 시)

**방법 1 — zip 전체 교체 (권장)**

1. GC8860: `gc3_make_deploy_zip.bat`  
2. GC3: 기존 폴더 백업 후 zip 풀기  
3. `Desktop\KCH\gc_automation.env` **덮어쓰지 않기**  
4. `gc3_setup.bat` 의 pip 단계만 다시 실행해도 됨  

**방법 2 — 변경 파일만 복사**

- `gc_*.py`, `gc_*.bat` 만 USB로 복사  
- env·`Desktop\KCH\*.xlsx`·`.gc_send_state.json` 은 유지  

---

## E. 문제 해결

| 증상 | 확인 |
|------|------|
| Data 경로 없음 | Chem32 설치·`C:\Chem32\1\Data` 존재 여부 |
| 프로필이 gc2로 나옴 | env에 `GC_INSTANCE=gc3` 있는지 |
| 메일 안 감 | 핫스팟·DNS·`NAVER_APP_PASSWORD` |
| verify FAIL | `gc_start_watch.bat` 재실행 |
| 한글 깨짐 | bat은 `chcp 949` — 정상 (GC2와 동일) |

---

## F. GC2 env와 공존하지 않음

GC3 PC는 **GC3 전용 장비 PC** 이므로 `Desktop\KCH\gc_automation.env` 하나만 두고  
`GC_INSTANCE=gc3` 로 고정합니다. (GC2 env와 혼용 금지)

---

## G. (미구현) 화면 영역 읽기

Chem32 **Report.TXT** 가 주 경로이지만, UI만 있는 정보·자동 캡처+OCR 아이디어는 별도 기록:

→ [`GC3_SCREEN_REGION_READ.md`](GC3_SCREEN_REGION_READ.md) (2026-06-27 메모, 구현 보류)
