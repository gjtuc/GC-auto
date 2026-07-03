# GC1 Cursor AI 핸드오프 — chemstation-gc-automation (GC2 → GC1 forward)

> **GitHub 업로드 출처: GC2/GC3 장비 PC (kimcha) — 2026-06-18**  
> Repo `https://github.com/gjtuc/GC-auto` 의 초기 push는 **GC2/GC3 장비 PC**에서 수행 (`gjtuc` 계정).  
> **GC1 장비 PC에서 올린 것이 아님.** GC1은 이 repo를 clone/pull 하여 **통합·배포**합니다.

> **용도**: 이 문서 전체를 **GC1 장비 PC(박은규)** Cursor AI 채팅에 붙여넣기 하세요.  
> **작성 시점**: 2026-06-18  
> **작성 PC**: GC2 (kimcha) — GC1 baseline 수신·merge·운영 검증·추가 수정 후 GC1에 재배포

---

## 0. 먼저 읽을 것 (오해 금지)

| 맞음 | 아님 |
|------|------|
| **같은 통합 repo** — GC1/GC2/GC3 코드가 한 폴더에 공존 | GC1 코드를 GC2 ChemStation으로 **교체**한 것 |
| GC1 장비 PC는 `GC_INSTANCE=gc1` + `Desktop\박은규` env만 사용 | GC2/GC3 장비 PC 설정(AndroidHotspot, KCH)을 GC1에 넣는 것 |
| 이번 zip = **GC1이 보냈던 최적화 + GC2에서 검증·추가한 안정화** | GC1이 보낸 zip과 **완전 동일**한 스냅샷 |

**GC1이 모르는 일 (요약)**  
1. GC1이 6/17에 `GC2_baseline` zip을 GC2에 보냄  
2. GC2가 merge 후 **8860 파이프라인·메일 회귀 테스트 통과**  
3. GC2 실운영 중 **핫스팟 불안정·SMTP 지연·watch 멈춤** 등을 겪으며 **공통 모듈 추가 수정**  
4. 그 결과물을 **이 zip + 이 문서**로 GC1에 다시 보냄  

GC1 Autochro→PDF→엑셀→메일 **핵심 로직(`gc_autochro`, `gc_gc1`)은 GC1 baseline 그대로**이며, watch·메일·프로세스 관리가 강화되었습니다.

---

## 1. 프로젝트 한 줄 요약

| PC | 운영자 | GC 장비 | 데이터 소스 | 출력 폴더 |
|----|--------|---------|-------------|-----------|
| **GC1** | 박은규 | YL6500GC (영린 Autochro-3000) | Autochro UI → PDF | `Desktop\박은규` |
| **GC2** | kimcha | Agilent 8860 ChemStation | `sequence.acam_` | `Desktop\KCH` |
| **GC3** | kimcha | Chem32 Report | `Report.txt` | `Desktop\KCH` |

**한 repo, PC별 env로 분기** — `gc_profiles.py`가 `Desktop\박은규` vs `Desktop\KCH`의 `gc_automation.env`를 탐색합니다.

공통 CLI: `gc_automation.py`  
**코드 읽기 순서**: `gc_architecture.py` → `gc_automation.py` → 해당 모드 모듈

---

## 2. GC1 baseline (이미 GC1에서 완료·운영 검증된 것)

아래는 **6/17 GC1 장비 PC에서 끝낸 작업**입니다. 이번 zip에도 **그대로 포함**되어 있습니다.

### GC1 파이프라인
- **Autochro UI** (`gc_autochro.py`): 제어목록 → Ctrl+A → 초기화+정량 → Hancom PDF
- **PDF 파싱·trim** (`gc_gc1.py`): FID/TCD, overflow 병합, 환원·전환·첫 반응 제거, B채널 incomplete 판별
- **엑셀**: FID/TCD 2시트, 「분석된 원소」 열
- **메일**: 네이버 SMTP

### GC1 watch (2026-06 업데이트)
- 핫스팟 **iPhone** 연결 edge → **Cursor 에이전트「동작해」** 또는 **OCR force 폴백**
- **30분** reconnect / 에이전트 쿨다운 (`GC1_HOTSPOT_RECONNECT_MIN_SEC=1800`)
- 자동화 파일: `Desktop\박은규\_GC자동화\` — 데이터(xlsx·pdf)는 `박은규` 루트만
- 상세: **`deploy/GC1_FEAT_2026-06.md`**, `deploy/GC1_DATA_FOLDER_LAYOUT.md`

### GC1 watch (기존)
- 핫스팟 **iPhone** 연결 edge → 세션당 1회 처리
- 메일 쿨다운·오전/오후 슬롯 **없음** (GC1 전용)

### GC1 env (운영)
```ini
GC_INSTANCE=gc1
EXCEL_OUTPUT_DIR=C:\Users\User\Desktop\박은규
CHEMSTATION_MODE=gc1
REQUIRED_HOTSPOT=iPhone
```
(env 파일 실제 위치: `Desktop\박은규\_GC자동화\gc_automation.env`)

---

## 3. GC2에서 추가·변경된 것 (이번 zip에 포함 — GC1에도 적용)

GC2가 GC1 baseline을 merge한 뒤 **실운영·테스트**하면서 넣은 개선입니다. GC1 장비 PC에도 **동일하게 동작**합니다.

### 3.1 작업 세션·단계별 재개 (`gc_work_job.py`) — **신규**
- 핫스팟 끊김·SMTP 실패 시 **미완료 작업 유지** (`.gc_send_state.json`의 `active_work_job`)
- 재연결 시 **prepare → excel → mail** 단계 중 **끊긴 곳부터 재개**
- 메일만 실패했으면 **엑셀 다시 만들지 않고** 메일만 재시도
- 메일 성공 시에만 세션 완료 기록

### 3.2 미발송 메일 자동 재시도 (핫스팟 불안정 대응)
- 엑셀 OK · SMTP 실패 → `pending_email_retry` 등록
- 핫스팟 **붙어 있는 동안** 30초마다 재발송 (성공까지)
- **순간 끊김**(45초 미만, GC1은 90초) 시 pipeline 중복 없이 **메일만 즉시 재시도**
- env: `PENDING_EMAIL_RETRY_INTERVAL_SEC`, `PENDING_EMAIL_SMTP_WAIT_MAX_SEC`

### 3.3 Watchdog 자동 재시작 (`gc_watchdog.py`) — **신규**
- heartbeat 3분 이상 멈추면 watch **강제 종료 후 재시작**
- `gc_watch_loop.bat` → `gc_watchdog.py --supervise` 경유
- env: `WATCH_HEARTBEAT_STALE_SEC=180`

### 3.4 중복 watch 창 자동 정리 (`gc_instance.py` 강화)
- `--watch` 중복 실행 시 **즉시 종료** (사용자에게 “닫아도 됩니다” 안 함)
- `gc_start_watch.bat` — 이미 watchdog 떠 있으면 **새 창 안 열음**
- `gc_stop_watch.bat` → `python gc_instance.py --stop-watch`

### 3.5 SMTP 대기·재시도 강화 (`gc_mailer.py`, `gc_wifi.py`)
- 핫스팟 직후 DNS/SMTP 준비 대기 (기본 120초)
- 일시 오류 451/timeout 시 재시도
- env: `SMTP_INTERNET_WAIT_MAX_SEC`, `SMTP_SEND_RETRIES`

### 3.6 자동 메일 한도 정책 (`gc_state.py`)
- **GC1**: 쿨다운·슬롯 없음 — 핫스팟 **세션당 1회** 자동 처리·메일
- **GC2/GC3**: **3시간 쿨다운 슬롯 1/1** (`AUTO_MAIL_COOLDOWN_HOURS`, 기본 3) — SMTP 발송+검증 성공 후 0/1
- `force`(`GC1_동작해줘.bat`, Cursor 「진행」)는 쿨다운·슬롯 무시

### 3.7 GC2 전용 코드는 GC1 실행 경로에서 호출 안 함
- `gc_chemstation.py`, `gc_chem32.py` — GC1 profile에서 미사용
- merge로 GC1 모듈 삭제·교체 **없음**

---

## 4. 이번에 GC1로 가져갈 파일

| 파일 | 용도 |
|------|------|
| `GC1_forward_chemstation-gc-automation.zip` | 통합 코드 (~50개 파일) |
| `GC1_Cursor_핸드오프.md` | **이 문서** — GC1 Cursor에 붙여넣기 |

**zip 포함**: Python 전부, bat, `gc_watchdog.py`, `gc_work_job.py`, `.cursor/rules`, `deploy/*.env.gc1` 템플릿  
**zip 제외**: 비밀번호 env, `__pycache__`, `.gc_send_state.json`, PDF/엑셀 산출물

---

## 5. GC1 장비 PC 배포 절차

### 5.1 사전 준비
- Python 3.10+ (3.12 권장), PATH 등록
- Autochro-3000, Hancom PDF, iPhone 핫스팟

### 5.2 zip 설치

```powershell
# 1) 기존 repo 백업 (선택)
Copy-Item -Recurse C:\Users\User\chemstation-gc-automation C:\Users\User\chemstation-gc-automation_backup_20260618

# 2) zip 압축 해제
$tmp = "$env:TEMP\gc1_forward_extract"
Expand-Archive -Path "<zip경로>\GC1_forward_chemstation-gc-automation.zip" -DestinationPath $tmp -Force

# 3) merge — Desktop\박은규\gc_automation.env 는 덮어쓰지 말 것!
Copy-Item -Path "$tmp\*" -Destination "C:\Users\User\chemstation-gc-automation" -Recurse -Force
```

### 5.3 env (중요)

| 파일 | 처리 |
|------|------|
| `Desktop\박은규\gc_automation.env` | **기존 운영값 유지** (iPhone, john3556, 실제 앱비밀번호) |
| `deploy\gc_automation.env.gc1` | 최초 설치 시에만 참고·복사 |

**절대 하지 말 것**: GC2용 `Desktop\KCH\gc_automation.env` 내용을 GC1에 복사

### 5.4 설치·바로가기

```bat
cd C:\Users\User\chemstation-gc-automation
gc1_setup.bat
```

- `pip install -r requirements.txt` (pymupdf, pywinauto 포함)
- 바탕화면 `GC1_감시시작.bat`, `GC1_동작해줘.bat` 등 생성

### 5.5 검증

```bat
python gc_automation.py --show-profile
python gc_automation.py --verify
```

기대값:
- `GC_INSTANCE=gc1`
- `EXCEL_OUTPUT_DIR=...\Desktop\박은규`
- `핫스팟 SSID: iPhone`
- `CHEMSTATION_MODE=gc1`

### 5.6 (선택) 로그인 시 자동 감시
`gc_install_autostart.bat` — `GC1_감시시작.bat` 연동

---

## 6. GC1 운영 env 참고

```ini
GC_INSTANCE=gc1
EXCEL_OUTPUT_DIR=C:\Users\User\Desktop\박은규
CHEMSTATION_MODE=gc1
REQUIRED_HOTSPOT=iPhone
NAVER_EMAIL=john3556@naver.com
MAIL_TO=john3556@naver.com
AUTOCHRO_ENABLED=1
AUTOCHRO_DATA_NAME=260616dre(3)ni-ce

# 선택 — GC2에서 검증된 안정화 (필요 시 추가)
# GC1_HOTSPOT_RECONNECT_MIN_SEC=90
# PENDING_EMAIL_RETRY_INTERVAL_SEC=30
# SMTP_INTERNET_WAIT_MAX_SEC=120
# WATCH_HEARTBEAT_STALE_SEC=180
```

---

## 7. Watch / force / Cursor 개시 (GC1)

### watch (`GC1_감시시작.bat`)
1. iPhone 핫스팟 **새로 연결** → Autochro export + PDF + 엑셀 + 메일
2. **세션당 1회** (연결 유지 중 중복 없음)
3. 90초 미만 끊김 → 동일 세션; 메일 pending 있으면 **재시도만**
4. heartbeat: 바탕화면 `MMDDHHmm.txt` ±5분
5. 멈춤 3분 → watchdog 자동 재시작

### force (`GC1_동작해줘.bat` 또는 Cursor)
```bat
python gc_automation.py --user-message "진행"
```
- 핫스팟·한도 무시, 전체 pipeline
- exit 0 = 성공 / 1 = heartbeat 수리 필요 / 2 = 개시 문구 아님
- `.cursor/rules/gc-initiation-force.mdc` — 「시작」「진행」「go」 등 → force

---

## 8. GC1 배포 후 체크리스트

- [ ] `--show-profile` → gc1, 박은규, iPhone
- [ ] `Desktop\박은규\gc_automation.env` 유지 (GC2 설정 없음)
- [ ] `gc1_setup.bat` 완료, pymupdf·pywinauto 설치
- [ ] iPhone 연결 시 `GC1_감시시작` → 세션 1회 처리
- [ ] `GC1_동작해줘.bat` 또는 `--user-message "진행"` → PDF + 엑셀 + john3556 메일
- [ ] SMTP 일시 실패 시 pending → 자동 재발송 (사람 개입 없이)
- [ ] `python -m unittest test_gc_sanitize test_gc_force_auth -q`

---

## 9. 모듈 맵 (GC1 관점)

```
gc_automation.py     ← CLI
├── gc_watch.py      ← 핫스팟 edge, pending 메일 재시도, GC1 세션
├── gc_watchdog.py   ← 멈춤 시 자동 재시작 (신규)
├── gc_work_job.py   ← 단계별 작업 재개 (신규)
├── gc_pipeline.py   ← run_processing_gc1()
│   ├── gc_autochro.py
│   └── gc_gc1.py
├── gc_instance.py   ← watch 단일 실행·종료
├── gc_state.py      ← .gc_send_state.json
├── gc_profiles.py   ← GC1/GC2/GC3 판별
└── gc_mailer.py     ← SMTP + 재시도
```

**문서**: `gc_architecture.py` (실행 코드 없음, 전체 맵)

---

## 10. GC1 Cursor에 붙여넣을 짧은 버전

```
chemstation-gc-automation 통합 repo — GC1 장비 PC(박은규) forward 배포.

상황: GC1이 6/17 baseline을 GC2에 보냄 → GC2 merge·8860 회귀 OK → GC2 실운영 중
watch/메일/작업재개 안정화 추가 → 이 zip이 그 결과물.

GC1_forward zip 풀어 C:\Users\User\chemstation-gc-automation merge.
Desktop\박은규\gc_automation.env 는 덮어쓰지 말 것 (iPhone, john3556).
gc1_setup.bat → --show-profile gc1 확인.

신규/강화: gc_work_job.py, gc_watchdog.py, pending 메일 자동재시도, 중복 watch 자동종료.
GC1 핵심(gc_autochro, gc_gc1)은 baseline 그대로.

상세: deploy\GC1_Cursor_핸드오프.md
```

---

## 부록: 빠른 명령

```bat
python gc_automation.py --show-profile
GC1_감시시작.bat
GC1_동작해줘.bat
gc_verify.bat
python gc_automation.py --user-message "진행"
python gc_instance.py --stop-watch
```

---

*이 문서와 `GC1_forward_chemstation-gc-automation.zip`을 GC1 장비 PC로 전달하세요.*
