# 데이터 PC — Origin 저장 후 종료 (차헌 PC · 은규 PC)

> **문제:** 파이프라인이 Origin COM 작업 전에 GUI를 정리할 때, 저장 없이 `taskkill` 되거나 저장 대화상자에 멈춰 **미저장 .opju 가 날아감**.  
> **해결:** `data_pc_origin/o3_session.py` 의 `save_and_force_quit_origin_gui()` — **디스크 저장 성공 후에만** 종료.

---

## 1. 언제 호출되나

| 시점 | 호출 위치 |
|------|-----------|
| 엑셀 배치 끝 → Origin 4단계 직전 | `촉매 반응 계산.py` → `_finalize_deferred_origin_batch()` |
| 시료별 Origin 작업 사이 | 같은 함수 (시료 간 정리) |
| COM 타임아웃 복구 | `o9_facade.py` (예전: 바로 kill → 지금: 저장·종료 함수) |
| COM attach 전 GUI 점유 | `ensure_origin_gui_clear_for_com()` |

새 메일이 없으면 Origin 단계 자체를 건너뛴다 (`DATA_PC_ORIGIN_PIPELINE` 등).

---

## 2. 예전 버그 vs 수정 후

| | 예전 | 수정 후 |
|--|------|---------|
| 저장 | `doc -s` (dirty 플래그만 해제, **파일 저장 아님**) | `project.save(명시적경로)` |
| 경로 없음 | 실패 후 kill | `DATA_PC_ORIGIN_RECOVERY_DIR` 에 `.opju` 백업 |
| 종료 | `taskkill /F` 우선 | `lt_exec('exit')` → 저장 확인 시 `o3_ui_win32.ps1` |
| 저장 실패 | kill 계속 | **`OriginGuiBusyError` — kill 안 함** |
| graceful kill | `taskkill /IM` (대화상자 유발) | 사용 안 함 |

---

## 3. 저장·종료 알고리즘 (요약)

```
Origin GUI 실행 중?
  └─ DATA_PC_KEEP_ORIGIN_GUI=1 → 예외 (사용자 작업 보호)
  └─ headless Origin64 (창 없음) → PID kill (COM 방해용 고아만)
  └─ COM attach (기존 GUI에 op.attach)
  └─ 창 제목에서 .opju 경로 추출
  └─ project.save(경로)  [untitled → recovery 경로]
  └─ 실패 시 o3_ui_win32.ps1 CtrlS / AnswerSaveYes
  └─ lt_exec('exit')
  └─ 창 제목에 '*' 없고 save_result가 ok: → taskkill /F
  └─ 그 외 → OriginGuiBusyError (수동 저장 요청)
```

**미저장 판별:** 창 제목에 `.opju *` 또는 `.opj *` 가 있으면 아직 저장 안 됨.

---

## 4. 은규 PC 배포 (필수)

은규 PC는 script_dir 가 `%USERPROFILE%\gc-data-pc\` 이다. **메인 스크립트만** 복사하면 Origin 저장 수정이 반영되지 않는다.

### 4.1 자동 (권장)

```powershell
cd $env:USERPROFILE\chemstation-gc-automation
git pull origin main
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\port_eungyu_data_pc.ps1
python -m data_pc_runtime --restart --script-dir "$env:USERPROFILE\gc-data-pc"
```

`port_eungyu_data_pc.ps1` 은 `data_pc_origin\` **폴더 전체**를 복사한다 (`o3_ui_win32.ps1` 포함).

### 4.2 수동

```powershell
$repo = "$env:USERPROFILE\chemstation-gc-automation"
$home = "$env:USERPROFILE\gc-data-pc"
Copy-Item -LiteralPath "$repo\data_pc\촉매 반응 계산.py" -Destination $home -Force
Copy-Item -LiteralPath "$repo\data_pc\runtime_paths.py" -Destination $home -Force
Copy-Item -Recurse -Force "$repo\data_pc\data_pc_origin" "$home\"
```

### 4.3 차헌 PC (Desktop\.cursor)

```powershell
cd C:\Users\user\chemstation-gc-automation   # 또는 GC-auto-push 클론 경로
git pull
Copy-Item -Recurse -Force data_pc\data_pc_origin C:\Users\user\Desktop\.cursor\
python -m data_pc_runtime --restart --script-dir "C:\Users\user\Desktop\.cursor"
```

---

## 5. 환경 변수

| 변수 | 기본 | 의미 |
|------|------|------|
| `DATA_PC_ORIGIN_AUTO_KILL` | `1` | COM 전 저장·종료 시도 |
| `DATA_PC_KEEP_ORIGIN_GUI` | `0` | `1` = 사용자 Origin 절대 종료 안 함 (4단계 스킵) |
| `DATA_PC_ORIGIN_RECOVERY_DIR` | `~/Documents/Origin Recovery/gc_automation` | 제목에 경로 없는 프로젝트 백업 |
| `DATA_PC_ORIGIN_PER_MAIL` | `0` | `1` = 메일마다 즉시 Origin (배치 아님) |
| `DATA_PC_SKIP_ORIGIN` | `0` | `1` = Origin 전체 생략 |

`gc_automation.env` (script_dir) 에 설정.

---

## 6. 수동 검증

Origin 에 **의도적으로 미저장** `.opju` 를 연 뒤:

```powershell
cd $env:USERPROFILE\gc-data-pc   # 은규
# 또는 cd C:\Users\user\Desktop\.cursor   # 차헌

python -c "
from data_pc_origin.o3_session import save_and_force_quit_origin_gui, is_origin_gui_running
save_and_force_quit_origin_gui(log=print)
print('gui:', is_origin_gui_running())
"
```

**기대:** 터미널에 `[Origin] 프로젝트 저장: ...` → `Origin64.exe 종료` → `gui: False`.  
파일 탐색기에서 `.opju` 수정 시각이 갱신됐는지 확인.

저장 실패 시: `Origin 저장 실패 — taskkill 생략` 메시지와 함께 Origin 이 **열려 있음** (작업 보호).

---

## 7. 문제 해결

| 증상 | 확인 |
|------|------|
| 여전히 저장 없이 꺼짐 | `data_pc_origin/o3_session.py` 가 구버전인지 (`doc -s` 검색) |
| `ModuleNotFoundError: data_pc_origin` | script_dir 에 `data_pc_origin` 패키지 폴더 없음 → §4 복사 |
| Ctrl+S 안 됨 | `o3_ui_win32.ps1` 이 `o3_session.py` 와 **같은 폴더**인지 |
| 저장 대화상자에서 멈춤 | supervisor 재시작 후 재시도; 남은 대화상자는 수동 [예] |
| COM attach 실패 | headless Origin64 — 로그에 `headless 인스턴스 종료` 있는지 |
| 파이프라인은 옛 코드 | `data_pc_runtime` supervisor 재시작 (`--restart`) |
| **G: 잠금 후 엑셀만 갱신·Origin 안 됨** | supervisor `waiting_gdrive` 해제 후에도 `workflows=0` — Origin 실패 시 메일 재시도 (`--force-mail`) |

---

## 8. 관련 파일 (repo `data_pc/`)

| 파일 | 역할 |
|------|------|
| `data_pc_origin/o3_session.py` | 저장·종료 핵심 |
| `data_pc_origin/o3_ui_win32.ps1` | Win32 UI 폴백 (Ctrl+S, 저장 대화상자) |
| `data_pc_origin/o9_facade.py` | COM 타임아웃 시 저장·종료 |
| `촉매 반응 계산.py` | `_finalize_deferred_origin_batch` |
| `data_pc_origin/tests/test_o3_session.py` | 단위 테스트 |

---

*차헌 PC 런타임 검증 후 main 반영. 은규 PC는 `git pull` + `port_eungyu_data_pc.ps1`.*
