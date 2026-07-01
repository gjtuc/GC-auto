# 데이터 PC 자동 감시 (`--watch`)

> 차헌 PC / 은규 PC — `Desktop\.cursor\촉매 반응 계산.py --watch`  
> PC 명칭: [`docs/PC_NAMING.md`](../docs/PC_NAMING.md)

## 한 줄 요약

연구실 Wi-Fi(차헌) 또는 iPhone 핫스팟(은규) 연결을 감시하고, **메일 → 계산 → G: → Origin** 을 사람 개입 없이 실행합니다.

| 상황 | 재시도 간격 |
|------|-------------|
| 정상 완료 · 새 메일 없음 | **1시간** (`DATA_PC_AUTO_MAIL_COOLDOWN_HOURS`) |
| **G: 잠금** (SecuYouSB 미로그인) | **15분** (`DATA_PC_GDRIVE_RETRY_SEC=900`) — 1시간 쿨다운 **미적용** |
| G: 로그인 해제됨 | **즉시** 재시도 |

---

## 모듈 구성 (2026-06 — data_pc_runtime)

```
Desktop\.cursor\  (또는 %USERPROFILE%\gc-data-pc\)
  촉매 반응 계산.py          process_new_gc_emails — 메일·계산·G:·Origin
  data_pc_runtime\           L0~L4 계층형 감시 (supervisor 1프로세스)
    layer0_probes.py         Wi-Fi · G: · IMAP TCP · PID (읽기 전용)
    layer1_state.py          쿨다운·G:재시도 상태 JSON
    layer2_gates.py          Wi-Fi → 락 → 쿨다운 게이트
    layer2_lock.py           .data_pc_pipeline.lock
    layer3_job.py            JobRunner → process_new_gc_emails
    layer4_supervisor.py     폴링 루프 + Ensure 재기동
  data_pc_watchdog.py        [레거시] → data_pc_runtime 위임만
  data_pc_wifi_autoconnect.py  부팅 시 iptime WLAN 자동 연결
  gc_wifi.py                 GC2/GC3·데이터 PC 공통 Wi-Fi 모듈
  gc_data_pc_*.bat/vbs       Windows 자동 시작 (차헌)
  gc_automation.env          DATA_PC_* 설정
  KCH\
    .data_pc_runtime_status.json   supervisor heartbeat
    .data_pc_runtime_state.json    쿨다운·G: 재시도
    .data_pc_pipeline.lock         파이프라인 동시 실행 방지
    .origin_update.lock            Origin 4단계 직렬화 (촉매 반응 계산.py)
```

**사용자 관점 흐름은 동일:** 로그인 → Wi-Fi → 백그라운드 감시 → 메일 → 엑셀 → G: → Origin.

**Origin Read-Only 팝업:** `촉매 반응 계산.py` 가 `.origin_update.lock` + 자동 Yes 클릭으로 처리 (수동 개입 불필요).

---

## env 설정 (`gc_automation.env`)

| 키 | 기본 | 설명 |
|----|------|------|
| `REQUIRED_HOTSPOT` | 차헌: `iptime,iptime 2,iptime_5G` | Wi-Fi 게이트 SSID (쉼표 구분) |
| `IPTIME_WIFI_PSK` | `12121212` | 부팅 시 WLAN 프로필 등록·자동 연결 |
| `DATA_PC_AUTO_MAIL_COOLDOWN_HOURS` | `1` | 정상 시 파이프라인 최소 간격 (GC2/GC3 메일 쿨다운과 동일) |
| `DATA_PC_GDRIVE_RETRY_SEC` | `900` | G: 잠금 시 재시도 간격(초). 작업 스케줄러 Ensure(15분)와 맞춤 |
| `DATA_PC_WATCH_INTERVAL_SEC` | `15` | Wi-Fi 폴링 간격 |
| `DATA_PC_HOTSPOT_RECONNECT_MIN_SEC` | `90` | 순간 끊김 동일 세션 처리 |
| `DATA_PC_BOOT_MAIL_CHECK` | `1` | 로그인 직후 미처리 메일 1회 |
| `DATA_PC_WATCH_HEARTBEAT_STALE_SEC` | `180` | watchdog 이 간격보다 heartbeat 없으면 재시작 |

차헌 템플릿: `deploy/gc_automation.env.chaheon.example`

---

## Windows 자동 시작 (차헌 PC)

```bat
deploy\gc_data_pc_install_autostart_chaheon.bat
```

등록되는 작업:

| 작업 이름 | 주기 | 동작 |
|-----------|------|------|
| `Chaheon_GC_DataPC_WiFi` | 로그인 | iptime WLAN 자동 연결 |
| `Chaheon_GC_DataPC_Watch` | 로그인 | `pythonw -m data_pc_runtime` — **콘솔 창 없음** |
| `Chaheon_GC_DataPC_Watch_Ensure` | 15분 | supervisor 죽었으면 `--ensure-once` — **hidden VBS** |

은규 PC: `deploy\gc_data_pc_install_autostart.bat` (`%USERPROFILE%\gc-data-pc`)

---

## 로그·상태 확인

| 파일 | 내용 |
|------|------|
| `%USERPROFILE%\.cursor\gc-runtime-temp\data_pc_runtime.log` | supervisor · 게이트 · 파이프라인 이벤트 |
| `%USERPROFILE%\.cursor\gc-runtime-temp\origin_automation.log` | Origin Read-Only 자동 Yes 등 |
| `%USERPROFILE%\.cursor\gc-runtime-temp\data_pc_watchdog.log` | 레거시 watchdog 위임 기록 |
| `KCH\.data_pc_runtime_status.json` | `status_code`, `cooldown_remaining_sec`, `wifi_ready` |
| `KCH\.data_pc_runtime_state.json` | `gdrive_retry_pending`, `last_pipeline_at` |

수동 확인:

```powershell
Get-Content "$env:USERPROFILE\.cursor\gc-runtime-temp\data_pc_runtime.log" -Tail 30
Get-Content "$env:USERPROFILE\Desktop\.cursor\KCH\.data_pc_runtime_status.json"
python -m data_pc_runtime.verify --live --dry-job --dry-supervisor
```

---

## G: 잠금 시 동작 (상세)

1. 메일 수신 → **2단계 계산**까지는 로컬 `KCH\processed\` 에 저장
2. G: 없으면 `PipelineRunResult(gdrive_retry_needed=True)` → 메일 **미처리** 유지
3. watch: `gdrive_retry_pending=true`, **1시간 쿨다운 기록 안 함**
4. 15분(또는 env) 후 다시 IMAP → G: → Origin 시도
5. SecuYouSB 로그인으로 G: 보이면 **즉시** 재시도

메일이 없을 때는 오류 없이 `0건` 완료 — 1시간 쿨다운만 적용.

---

## 수동 실행·검증

```powershell
# 1회 메일 확인 (비대화형)
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py" --poll-once

# 감시 (콘솔 표시, 테스트)
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py" --watch --no-wifi-check

# repo 검증
cd chemstation-gc-automation
python -m unittest test_data_pc_watch -v
python scripts/verify_data_pc_watch.py
```

---

## 장비 PC watch 와 비교

| | GC2/GC3 장비 PC | 데이터 PC (차헌) |
|--|-----------------|-------------------|
| 스크립트 | `gc_automation.py --watch` | `촉매 반응 계산.py --watch` |
| Wi-Fi | iptime 3종 | iptime 3종 |
| 쿨다운 | 1시간 (메일 발송) | 1시간 (메일 수신·Origin) |
| G: 재시도 | 해당 없음 | 15분 (잠금 시) |
