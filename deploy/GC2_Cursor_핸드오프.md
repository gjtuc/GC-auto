# GC2 Cursor AI 핸드오프 — chemstation-gc-automation

> **용도**: 이 문서 전체를 GC2 PC의 Cursor AI 채팅에 붙여넣기 하세요.  
> **작성 시점**: 2026-06-17 (GC1 최적화 baseline 기준)  
> **작성 PC**: GC1 (박은규 운영 PC에서 작업 후 GC2로 역배포)

---

## 1. 프로젝트 한 줄 요약

| PC | 운영자 | GC 장비 | 데이터 소스 | 출력 폴더 |
|----|--------|---------|-------------|-----------|
| **GC1** | 박은규 | YL6500GC (영린 Autochro-3000) | Autochro UI → PDF | `Desktop\박은규` |
| **GC2** | kimcha | Agilent 8860 ChemStation | `sequence.acam_` (ACAML XML) | `Desktop\KCH` |
| **GC3** | kimcha | Chem32 Report | `Report.txt` | `Desktop\KCH` |

**한 repo, PC별 env로 분기** — `gc_profiles.py`가 `Desktop\박은규` vs `Desktop\KCH`의 `gc_automation.env`를 탐색해 GC1/GC2/GC3를 자동 판별합니다.

공통 CLI: `gc_automation.py`  
**코드 읽기 순서**: `gc_architecture.py` (문서 전용, import 불필요) → `gc_automation.py` → 해당 모드 모듈

---

## 2. 지금까지 완료된 작업 (GC1)

GC1 PC에서 아래 기능이 **운영 검증 완료** 상태입니다.

### 전체 파이프라인 (GC1)
- **Autochro UI 자동화** (`gc_autochro.py`): 제어목록 → Ctrl+A → 초기화+정량 → Hancom PDF 저장
- **PDF 파싱·trim** (`gc_gc1.py`): FID(A)/TCD(C) 피크 추출, 환원·전환·첫 반응 제거
- **엑셀 생성**: FID/TCD 2시트, GC2와 달리 **「분석된 원소」** 열 사용
- **네이버 SMTP 메일** (`gc_mailer.py`)

### PDF 파일명 자동화
- `AUTOCHRO_DATA_NAME` 하드코딩이 아님
- 제어목록 **파란 선택 데이터명** + 창 제목에서 읽어 `260616 dre@(3) ni-ce.pdf` 형식으로 저장

### Trim / B채널 마지막 사이클
- 환원 구간·전환 1주입·**첫 반응 1주입** 제거 (H2 area 기준)
- 마지막 주입 incomplete 판별: **B 채널(크로마토그램만) 전압선 x축 길이** 측정
- `GC1_LAST_CYCLE_MIN_SCAN_MIN`(기본 18분) 미만이면 마지막 3페이지 분 drop

### UI 안정화
- **창 위치 복원**: `AUTOCHRO_AUTO_POSITION`, 상대 좌표 list/tree 탐색
- **Ctrl+A 수정**: 소유자 ID 열 드롭다운 회피 → `AUTOCHRO_LIST_NEUTRAL_X_FRAC=0.78`
- **피크 overflow 페이지 병합**: C채널 적분표가 다음 페이지로 이어질 때 CO/CO2 누락 방지
- **PDF 잠금 대기**: `GC1_PDF_READY_WAIT_SEC`, Hancom 창 닫힘 대기

### Watch 세션 규칙 (GC1)
- 핫스팟 **연결 edge**에서만 pipeline 실행 (연결 유지 중 반복 없음)
- **세션당 1회** PDF·엑셀·메일 (GC2의 오전/오후 슬롯 한도 없음)
- **90초 reconnect debounce** (`GC1_HOTSPOT_RECONNECT_MIN_SEC=90`): 짧은 끊김=동일 세션, 길게 껐다 켜면 1회 더
- 순간 flicker(약한 신호) 무시

### Cursor 개시 → force
- `gc_request.message_is_initiation()`: 「진행」「시작」「go」 등 → **force 모드** (watch·한도 무시)
- `.cursor/rules/gc-initiation-force.mdc` alwaysApply 규칙
- exit 0/1/2 → heartbeat 검증 후 Cursor 후속 행동

### 운영 환경 (GC1 production)
- 핫스팟: **iPhone**
- 메일: **john3556@naver.com**
- 테스트용 Android+kimcha 설정은 env에서 **주석 처리** 상태

---

## 3. 아키텍처

### 실행 모드 3가지

| 모드 | 진입 | 동작 |
|------|------|------|
| **watch** | `--watch`, `GC1_감시시작.bat` | 핫스팟 edge에서 자동 처리 |
| **force** | `--force`, `--request`, `GC1_동작해줘.bat` | 핫스팟·일일한도 무시, 전체 pipeline |
| **Cursor 개시** | `--user-message "진행"` | force와 동일 + heartbeat 검증 |

### 모듈 맵

```
gc_automation.py     ← CLI 진입, watch/force/user-message 분기
├── gc_watch.py      ← 핫스팟 edge tick, GC1/GC2 분기
├── gc_request.py    ← 개시 문구 → force
├── gc_pipeline.py   ← run_processing_gc1 / chem32 / 8860
│   ├── gc_autochro.py   (GC1 PDF UI)
│   ├── gc_gc1.py        (GC1 PDF 파싱·trim·엑셀)
│   ├── gc_chemstation.py (GC2 acam)
│   └── gc_chem32.py     (GC3 Report)
├── gc_state.py      ← .gc_send_state.json
├── gc_wifi.py       ← SSID·SMTP 게이트
├── gc_mailer.py     ← 네이버 SMTP
├── gc_profiles.py   ← GC1/GC2/GC3 env 탐색
├── gc_config.py     ← AppConfig, 상수
└── gc_status.py     ← MMDDHHmm.txt heartbeat
```

### 진입점 (bat)

**repo 루트 (공통/GC2용)**:
- `gc_start_watch.bat` / `gc_stop_watch.bat` — watch 시작·중지
- `gc_동작해줘.bat` — `--request` (force)
- `gc_verify.bat` — heartbeat·설정 검증
- `gc_watch_status.bat` — 감시 상태 확인

**GC1 전용 (Desktop\박은규, gc1_setup.bat으로 생성)**:
- `GC1_감시시작.bat` — watch
- `GC1_동작해줘.bat` — force
- `GC1_데이터갱신.bat` — Autochro PDF만
- `GC1_PDF분석.bat` — PDF→엑셀만
- `GC1_상태확인.bat` — 상태 출력

---

## 4. 핵심 파일과 역할

| 파일 | 역할 |
|------|------|
| `gc_architecture.py` | **문서 전용** — 구조·흐름·함정 정리 (실행 코드 없음) |
| `gc_automation.py` | CLI 진입점 |
| `gc_watch.py` | 핫스팟 edge 감시, GC1 세션 vs GC2 am/pm 슬롯 |
| `gc_pipeline.py` | 모드별 처리 오케스트레이션 |
| `gc_autochro.py` | GC1 Autochro-3000 UI 5단계 PDF보내기 |
| `gc_gc1.py` | GC1 PDF 파싱, overflow 병합, trim, 엑셀, cleanup |
| `gc_chemstation.py` | GC2 `sequence.acam_` XML 파싱 |
| `gc_chem32.py` | GC3 Report.txt 파싱 |
| `gc_state.py` | `.gc_send_state.json` — 일일한도, mtime, pending 메일 |
| `gc_request.py` | 개시 문구 판별 → force |
| `gc_profiles.py` | PC별 env·핫스팟·모드 해석 |
| `gc_wifi.py` | REQUIRED_HOTSPOT SSID 확인, SMTP 인터넷 게이트 |
| `gc_mailer.py` | 네이버 SMTP 발송 |
| `gc_config.py` | AppConfig, reconnect 시간, 슬롯 상수 |
| `gc_status.py` | `MMDDHHmm.txt` heartbeat, verify |
| `gc_force_auth.py` | 선택적 `GC_FORCE_TOKEN` 보호 |
| `gc_sanitize.py` | 시료명·시퀀스 폴더 검증 |
| `gc_kch.py` | GC2/GC3 시료명 사전 검사 |
| `gc_instance.py` | watch PID lock |
| `.cursor/rules/gc-initiation-force.mdc` | Cursor alwaysApply: 개시→force |
| `deploy/gc_automation.env` | GC1 PC 배포용 env 템플릿 |
| `deploy/gc_automation.env.gc2` | GC2/GC3 env 템플릿 |
| `deploy/gc_automation.env.gc1` | GC1 env 템플릿 (비밀번호 placeholder) |
| `.env.example` | 전체 env 변수 설명 |

---

## 5. GC1 vs GC2 차이 — GC2에서 절대 깨지면 안 되는 것

| 항목 | GC1 | GC2/GC3 |
|------|-----|---------|
| 데이터 소스 | Autochro PDF | ChemStation `.D` / acam / Report |
| 핫스팟 | `iPhone` | `AndroidHotspot5841` |
| env 위치 | `Desktop\박은규\gc_automation.env` | `Desktop\KCH\gc_automation.env` |
| watch 트리거 | 핫스팟 **세션당 1회** | 새 acam mtime + **오전/오후 각 1회** |
| reconnect debounce | 90초 | 45초 |
| 메일 한도 | 슬롯 없음 (세션 1회) | `DAILY_SEND_LIMIT=2` (am/pm) |
| 파이프라인 | `run_processing_gc1()` | `run_processing()` → 8860/chem32 |
| 엑셀 열 | 「분석된 원소」 | Width 등 GC2 형식 |
| Autochro 모듈 | **GC1 전용** — GC2에서 호출 금지 | 해당 없음 |

### merge 시 주의
- `gc_gc1.py`, `gc_autochro.py` 변경은 GC2에 영향 없어야 함 (분기 유지)
- `gc_watch.py`, `gc_pipeline.py`, `gc_state.py` 수정 시 **GC2 am/pm 슬롯 로직** regression 테스트 필수
- `gc_profiles.py`의 GC2/GC3 기본값(`AndroidHotspot5841`, `Desktop\KCH`) 변경 금지
- GC1 env (`iPhone`, `john3556`)가 GC2 PC의 `Desktop\KCH\gc_automation.env`에 섞이지 않게 할 것

---

## 6. 역배포 절차 (GC2로)

### 6.1 GC2 PC에서 baseline zip 받기

**ZIP 위치** (동일 파일 2곳):
```
C:\Users\User\Desktop\박은규\GC1_baseline_chemstation-gc-automation.zip
C:\Users\User\chemstation-gc-automation\deploy\GC1_baseline_chemstation-gc-automation.zip
```

**ZIP 내용** (43개 파일, ~94KB):
- Python 소스 22개 (`*.py` — `gc_architecture.py` 포함)
- bat 13개 (repo 루트)
- `requirements.txt`
- `test_gc_sanitize.py`, `test_gc_force_auth.py`
- `.env.example`
- `.cursor/rules/gc-initiation-force.mdc`
- `deploy/` — `gc_automation.env`, `gc_automation.env.gc1`, `gc_automation.env.gc2`, `make_gc2_baseline_zip.ps1`

**제외됨**: `__pycache__`, `.git`, `*.pyc`, `.gc_send_state.json`, Desktop 사용자 env, PDF/엑셀 산출물, venv, 중첩 baseline zip

### 6.2 GC2 PC repo에 merge

```powershell
# 1) 기존 repo 백업 (GC2 동작 확인용)
Copy-Item -Recurse C:\Users\User\chemstation-gc-automation C:\Users\User\chemstation-gc-automation_backup_YYYYMMDD

# 2) zip 압축 해제 (임시 폴더)
$tmp = "$env:TEMP\gc1_baseline_extract"
Expand-Archive -Path "C:\Users\User\chemstation-gc-automation\deploy\GC1_baseline_chemstation-gc-automation.zip" -DestinationPath $tmp -Force

# 3) merge — GC2 PC의 Desktop\KCH\gc_automation.env 는 덮어쓰지 말 것!
Copy-Item -Path "$tmp\*" -Destination "C:\Users\User\chemstation-gc-automation" -Recurse -Force
# deploy\gc_automation.env (GC1용)는 repo에만 두고 Desktop에는 복사하지 않음
```

### 6.3 env 파일 정리

| PC | env 파일 | 내용 |
|----|----------|------|
| GC2/GC3 | `Desktop\KCH\gc_automation.env` | `deploy\gc_automation.env.gc2` 참고, **기존 GC2 운영값 유지** |
| GC1 | `Desktop\박은규\gc_automation.env` | `deploy\gc_automation.env` 또는 `.gc1` 템플릿 + 실제 비밀번호 |

```ini
# GC2 운영 (Desktop\KCH\gc_automation.env) — 이 값을 GC2 PC에서 유지!
GC_INSTANCE=gc2
EXCEL_OUTPUT_DIR=C:\Users\User\Desktop\KCH
CHEMSTATION_MODE=8860
REQUIRED_HOTSPOT=AndroidHotspot5841
NAVER_EMAIL=kimcha0809@naver.com
NAVER_APP_PASSWORD=<실제 앱비밀번호>
MAIL_TO=kimcha0809@naver.com
```

```ini
# GC1 운영 (Desktop\박은규\gc_automation.env) — GC1 PC에만 존재
GC_INSTANCE=gc1
EXCEL_OUTPUT_DIR=C:\Users\User\Desktop\박은규
CHEMSTATION_MODE=gc1
REQUIRED_HOTSPOT=iPhone
NAVER_EMAIL=john3556@naver.com
NAVER_APP_PASSWORD=<실제 앱비밀번호>
MAIL_TO=john3556@naver.com
AUTOCHRO_ENABLED=1
AUTOCHRO_DATA_NAME=260616dre(3)ni-ce
```

### 6.4 GC2 regression 확인 (merge 직후)

```bat
cd C:\Users\User\chemstation-gc-automation
python gc_automation.py --show-profile
python gc_automation.py --verify
```

- `GC_INSTANCE=gc2`, `Desktop\KCH`, `AndroidHotspot5841` 확인
- GC2 watch가 기존처럼 acam mtime + am/pm 슬롯 동작하는지 확인

### 6.5 GC1 PC로 forward deploy

kimcha(GC2)가 merge·검증 후, **동일 baseline zip**을 GC1 PC(박은규)에 전달:

```powershell
# GC1 PC에서
Expand-Archive -Path "<zip경로>\GC1_baseline_chemstation-gc-automation.zip" -DestinationPath "$env:TEMP\gc1_deploy" -Force
Copy-Item -Recurse "$env:TEMP\gc1_deploy\*" "C:\Users\User\chemstation-gc-automation" -Force

# env는 Desktop\박은규\gc_automation.env 유지 (덮어쓰지 않음)
Copy-Item "C:\Users\User\chemstation-gc-automation\deploy\gc_automation.env" "C:\Users\User\Desktop\박은규\gc_automation.env" -Force
# ↑ 최초 설치 시만. 이미 운영 env가 있으면 diff 후 선택 merge

# GC1 바탕화면 bat 생성/갱신
gc1_setup.bat
```

---

## 7. 환경 변수 정리

### GC1 production (운영)
```ini
GC_INSTANCE=gc1
EXCEL_OUTPUT_DIR=C:\Users\User\Desktop\박은규
CHEMSTATION_MODE=gc1
REQUIRED_HOTSPOT=iPhone
NAVER_EMAIL=john3556@naver.com
MAIL_TO=john3556@naver.com
AUTOCHRO_ENABLED=1
AUTOCHRO_DATA_NAME=260616dre(3)ni-ce
AUTOCHRO_WINDOW_TITLE_PATTERN=Autochro-3000
```

### GC1 test (주석 처리 — Android + kimcha 연습용)
```ini
# REQUIRED_HOTSPOT=AndroidHotspot5841
# NAVER_EMAIL=kimcha0809@naver.com
# MAIL_TO=kimcha0809@naver.com
```

### GC1 Autochro/UI 튜닝 (선택)
```ini
AUTOCHRO_AUTO_POSITION=1
AUTOCHRO_WINDOW_X=40
AUTOCHRO_WINDOW_Y=40
AUTOCHRO_LIST_NEUTRAL_X_FRAC=0.78
AUTOCHRO_HANCOM_WAIT_SEC=180
GC1_PDF_READY_WAIT_SEC=90
GC1_HOTSPOT_RECONNECT_MIN_SEC=90
GC1_LAST_CYCLE_MIN_SCAN_MIN=18
GC1_DROP_LAST_INCOMPLETE_CYCLE=1
```

### GC1 trim 임계값 (기본값으로 충분하면 생략)
```ini
GC1_REDUCTION_H2_AREA=20000
GC1_REDUCTION_H2_TOL=0.35
GC1_NOISE_AREA_MAX=100
GC1_REACTION_CO_MIN=100
```

### GC2/GC3
```ini
GC_INSTANCE=gc2          # GC3: gc3
EXCEL_OUTPUT_DIR=C:\Users\User\Desktop\KCH
CHEMSTATION_MODE=8860    # GC3: chem32
REQUIRED_HOTSPOT=AndroidHotspot5841
```

---

## 8. Watch 동작 규칙

### 공통
- tick 간격: 기본 15초
- `REQUIRED_HOTSPOT` SSID 일치 시에만 pipeline 접근
- 연결 **유지 중**에는 재실행 없음 (edge-trigger)
- `MMDDHHmm.txt` heartbeat — Cursor/verify가 ±5분 검증

### GC1 (iPhone)
1. 핫스팟 **새로 연결** (`just_connected`) → `_on_hotspot_connected()`
2. **세션당 1회** Autochro export + PDF 파싱 + 엑셀 + 메일
3. 90초 미만 끊김 → 동일 세션 (중복 발송 없음)
4. 90초 이상 껐다 켬 → 새 세션, 1회 더 처리 가능
5. 오전/오후 슬롯 **없음** (`gc1_unlimited_auto_send`)

### GC2/GC3 (AndroidHotspot5841)
1. 새 `acam`/`Report` mtime 감지
2. **오전 1회 + 오후 1회** 자동 메일 (`DAILY_SEND_LIMIT=2`, 12시 기준)
3. reconnect debounce: 45초
4. 새 날짜 시퀀스에 시료명 없으면 watch skip (force 시 `--sample-name` 지정)

### force (공통)
- watch·핫스팟·일일한도 **모두 무시**
- GC1 force: Autochro PDF 재보내기 포함 전체 pipeline
- Cursor 개시 문구도 동일하게 force

---

## 9. 테스트 체크리스트

### GC2 regression (merge 후 필수)

- [ ] `python gc_automation.py --show-profile` → gc2, KCH, 8860, AndroidHotspot5841
- [ ] `python gc_automation.py --verify` → heartbeat OK
- [ ] `Desktop\KCH\gc_automation.env`가 GC2 값 유지 (GC1 iPhone 설정 없음)
- [ ] watch 시작 후 acam mtime 변경 시 처리 동작
- [ ] 오전 슬롯 1회, 오후 슬롯 1회 한도 유지
- [ ] force (`gc_동작해줘.bat`) 정상 엑셀+메일
- [ ] GC1 모듈(`gc_autochro`, `gc_gc1`)이 GC2 실행 경로에서 호출되지 않음

### GC1 deploy verification (GC1 PC에 zip 설치 후)

- [ ] `python gc_automation.py --show-profile` → gc1, 박은규, gc1, iPhone
- [ ] `GC1_감시시작.bat` → iPhone 연결 시 세션 1회 처리
- [ ] 90초 이내 flicker → 중복 없음
- [ ] `GC1_동작해줘.bat` 또는 `--user-message "진행"` → Autochro PDF + 엑셀 + john3556 메일
- [ ] PDF 3페이지/주입, overflow 페이지 CO/CO2 포함
- [ ] 마지막 incomplete 사이클 B채널 길이 판별
- [ ] `python gc1_analyze_pdf.py <pdf>` 단독 분석 (선택)

### 단위 테스트
```bat
cd C:\Users\User\chemstation-gc-automation
python -m pytest test_gc_sanitize.py test_gc_force_auth.py -q
```

---

## 10. 알려진 함정 / 버그 수정 이력

| 문제 | 원인 | 해결 |
|------|------|------|
| PDF 3페이지만 저장 | Ctrl+A가 소유자 ID 드롭다운 위에서 실행 | `AUTOCHRO_LIST_NEUTRAL_X_FRAC`, `_focus_list_for_ctrl_a()` |
| Autochro 창 화면 밖 | 절대좌표 list/tree 탐색 실패 | `AUTOCHRO_AUTO_POSITION`, 창 내부 상대 좌표 |
| CO/CO2 누락 | C채널 피크표 overflow 페이지 미병합 | `_merge_peak_continuation_pages()` |
| 마지막 주입 오판 | 시간 기준만 사용 | B채널 전압선 x축 분 측정 (`GC1_LAST_CYCLE_MIN_SCAN_MIN`) |
| Hancom 창 잔류 | 다음 실행 블록 | `AUTOCHRO_HANCOM_WAIT_SEC`, `_wait_and_close_all_hancom_pdf()` |
| PDF 잠금 | 저장 중 Acrobat 오류 | `GC1_PDF_READY_WAIT_SEC`, `wait_for_pdf_file_ready()` |
| 핫스팟 flicker 중복 | 짧은 끊김을 새 세션으로 처리 | `GC1_HOTSPOT_RECONNECT_MIN_SEC=90` |
| Cursor "진행" 무시 | 개시 문구 미인식 | `gc_request.py` + `.cursor/rules/gc-initiation-force.mdc` |
| 잘못된 PDF/xlsx 누적 | Autochro 제목 파싱 오류, 구버전 파일 | `cleanup_superseded_gc1_files()` |

---

## 11. 앞으로 GC2 Cursor가 해야 할 일

1. **GC2/GC3 운영 유지** — merge 후 regression 체크리스트 통과 확인
2. **GC1 baseline zip 관리** — `deploy\GC1_baseline_chemstation-gc-automation.zip`을 GC1 PC 배포 기준으로 사용
3. **merge 전략** — GC1 전용 변경(`gc_autochro`, `gc_gc1`)과 GC2 공통 변경 분리 인지; 공통 모듈 수정 시 GC2 테스트 우선
4. **env 분리** — `Desktop\KCH` (GC2) vs `Desktop\박은규` (GC1) 절대 혼동 금지
5. **비밀번호** — env 비밀번호를 채팅/커밋에 붙이지 말 것; `deploy/*.env` 템플릿은 placeholder 사용
6. **개시 요청** — 사용자가 「진행」「시작」만 말하면 `python gc_automation.py --user-message "..."` force 우선
7. **문서 갱신** — 구조 변경 시 `gc_architecture.py` docstring 동기화
8. **Git** — 이 PC에 git CLI 미설치 가능; 변경사항은 **uncommitted** 일 수 있음. GC2에서 버전 관리 시 diff 확인 후 커밋

---

## 부록 A: 사용자 컨텍스트

| 사람 | 역할 | PC |
|------|------|-----|
| **박은규** | GC1 운영자, YL6500GC 실험·메일 수신 | GC1 PC |
| **kimcha** | GC2/GC3 설정·코드 merge·GC1 배포 지원 | GC2 PC |

---

## 부록 B: Git 상태 참고

- GC1 작업 PC에서 `git` CLI가 PATH에 없을 수 있음
- baseline zip은 **현재 워킹 트리 스냅샷** (커밋 여부와 무관)
- GC2에서 merge 전 `git status` / `git diff`로 GC2 로컬 변경과 baseline diff 권장

---

## 부록 C: 빠른 명령 참조

```bat
REM 프로필 확인
python gc_automation.py --show-profile

REM GC2 watch
gc_start_watch.bat

REM GC2 force
gc_동작해줘.bat

REM heartbeat 검증
gc_verify.bat

REM GC1 Cursor 개시
python gc_automation.py --user-message "진행"

REM 개시 문구 테스트
python -c "from gc_request import message_is_initiation; print(message_is_initiation('진행'))"
```

---

*이 문서와 `GC1_baseline_chemstation-gc-automation.zip`을 함께 GC2 Cursor에 전달하세요.*
