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

## 모듈 구성

```
Desktop\.cursor\
  촉매 반응 계산.py      --watch 진입
  data_pc_watch.py       Wi-Fi poll · 쿨다운 · 파이프라인 호출
  data_pc_watchdog.py    watch 프로세스 감시·재시작
  gc_data_pc_*.bat/vbs   Windows 자동 시작 (차헌)
  gc_automation.env      아래 DATA_PC_* 설정
  KCH\
    .data_pc_watch_status.json   실시간 heartbeat (감시 살아있음)
    .data_pc_watch_state.json    쿨다운·G: 재시도 상태
```

---

## env 설정 (`gc_automation.env`)

| 키 | 기본 | 설명 |
|----|------|------|
| `REQUIRED_HOTSPOT` | 차헌: `iptime,iptime 2,iptime_5G` | Wi-Fi 게이트 SSID (쉼표 구분) |
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
| `Chaheon_GC_DataPC_Watch` | 로그인 | `pythonw` + VBS — **콘솔 창 없음** |
| `Chaheon_GC_DataPC_Watch_Ensure` | 15분 | watch 죽었으면 재기동 |

은규 PC: `deploy\gc_data_pc_install_autostart.bat` (`%USERPROFILE%\gc-data-pc`)

---

## 로그·상태 확인

| 파일 | 내용 |
|------|------|
| `%USERPROFILE%\.cursor\gc-runtime-temp\data_pc_watch.log` | watch 이벤트 (G: 재시도·쿨다운·파이프라인) |
| `%USERPROFILE%\.cursor\gc-runtime-temp\data_pc_watchdog.log` | watchdog 재시작 |
| `KCH\.data_pc_watch_status.json` | `status_code`, `cooldown_remaining_sec`, `wifi_ready` |
| `KCH\.data_pc_watch_state.json` | `gdrive_retry_pending`, `last_pipeline_at` |

수동 확인:

```powershell
Get-Content "$env:USERPROFILE\.cursor\gc-runtime-temp\data_pc_watch.log" -Tail 30
Get-Content "$env:USERPROFILE\Desktop\.cursor\KCH\.data_pc_watch_status.json"
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
