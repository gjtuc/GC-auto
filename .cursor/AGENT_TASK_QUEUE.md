# Agent 작업 큐

> **시작:** Agent 채팅에 `큐 시작` (또는 [INIT_MESSAGE.md](https://github.com/gjtuc/hook/blob/main/INIT_MESSAGE.md) 긴 개시제)  
> **가이드:** https://github.com/gjtuc/hook/blob/main/docs/GUIDE.md  
> (은규 PC 일상 `진행`/`시작` ≠ 본 큐 — 코드 작업은 **`큐 시작`**)

| 파일 | 역할 |
|------|------|
| 본 문서 | 단계 목록 (`[ ]` / `[x]`) — **한 턴에 첫 `[ ]` 한 줄만** |
| `.cursor/agent_queue_state.json` | armed / running / complete / blocked |
| `.cursor/hooks/task_queue_continue.py` | 미완료 → followup 자동 |
| `.cursor/hooks/task_queue_quit_cursor.py` | 전부 `[x]` → Cursor 종료 (`GC_AGENT_QUEUE_QUIT_CURSOR=0` 으로 끄기) |

**목표:** GC1 Autochro **체질 개선** — 규칙(R) 유지, 지하(Ω-B)→L0→L2→L4 leaf 설계·구현.  
**설계 leaf ID:** `Ω.A.L4.Px…` (대화·설계서와 동일)

---

## A. Hook 인프라 (완료)

- [x] **T01** `task_queue_continue` + `hooks.json` — stdin 시뮬 followup/`{}` 검증
- [x] **T02** `agent-task-queue.mdc` — `큐 시작` → armed, 첫 `[ ]`만, `[x]` 표시
- [x] **T03** `test_task_queue_continue.ps1` ALL PASS
- [x] **T03b** quit Hook — 큐 전부 `[x]` 시 Cursor 종료

---

## B. 설계 고정 (코드 없음 — leaf 스펙 문서)

- [x] **T10** `deploy/GC1_RUNTIME_DESIGN.md` — Ω-1~4(원자 종료·ID·7필드·R/C 경계) + Ω-B(B-IDENT~B-CLK leaf 표)
- [x] **T11** 동 문서 — Ω-L0 전 leaf(WIFI/WIN/LV/TR/TAB/DN/MTD/PDF/SCR/TASK/FOCUS)
- [x] **T12** 동 문서 — Ω-L2 게이트(G-EX, G-ATOM) + Ω-ERR 코드↔은규 한 줄 메시지表
- [x] **T13** 동 문서 — Ω-L4 **P0~P4** leaf 전개(번호·pre/post probe ID만, ~150 leaf)
- [x] **T14** 동 문서 — Ω-L4 **P5~P9** + Ω-L6-CLEAN/PARSE leaf + `.gc_autochro_job.json` 스키마 JSON 예시

---

## C. 패키지 골격 (실행 없음·import만)

- [x] **T20** `gc1_runtime/` 패키지 생성 — `__init__.py`, `README` docstring(레이어 의존 방향), 빈 `layer0`~`layer4` 모듈
- [x] **T21** `gc1_runtime/layer0_probes.py` — B-HOST leaf: `platform`, `python_bitness`, `display_metrics` dataclass + 단위 테스트
- [x] **T22** `gc1_runtime/layer0_config.py` — B-CFG env 키 leaf별 `read_*` (AUTOCHRO_*, GC1_*) + invalid fallback 테스트
- [x] **T23** `gc1_runtime/layer1_state.py` — `.gc_autochro_job.json` `StateStore` (atoms 7필드) + roundtrip unittest
- [x] **T24** `gc1_runtime/layer2_gates.py` — `GateEvaluator` G-EX + G-PRE/G-POST stub + gate unittest

---

## D. L0 프로브 이전 (Autochro UI 읽기)

- [x] **T30** `gc1_runtime/layer0_win.py` — L0-WIN.01~07 (findwindows, score, rect) — pywinauto mock 테스트
- [x] **T31** `gc1_runtime/layer0_ctl.py` — L0-LV.* + L0-LV-PICK.* + L0-TR.* + L0-TAB.* — geometry unittest (기존 `gc_autochro` 로직 이전)
- [x] **T32** `gc1_runtime/layer0_data.py` — L0-DN.* + L0-MTD.* + `tree_label_matches` — 기존 `test_gc_autochro_prep` 이전·확장

---

## E. L3 액추에이터 (손·눈 채널 분리)

- [x] **T40** `gc1_runtime/layer3_hand.py` — W32 leaf 래퍼: `set_focus`, `click`, `send_keys`, `menu_popup_pick` (matcher 인터페이스)
- [x] **T41** `gc1_runtime/layer3_eye.py` — `gc_screen_read`에서 L0-SCR-GEO/CAP/ZOOM/OCR 래핑 (Tesseract 없이 geometry·token filter 테스트)
- [x] **T42** `gc1_runtime/layer3_file.py` — L0-PDF + Hancom/dialog FS leaf + `wait_for_pdf_file_ready` thin wrapper

---

## F. L4 페이즈 원자 (state machine)

- [x] **T50** `gc1_runtime/layer4_atoms_p0_p1.py` — P0 JOB_PRELUDE + P1 sync (atom ID별 pre/post, StateStore 기록) + dry-run unittest
- [x] **T51** `gc1_runtime/layer4_atoms_p2_p3.py` — P2 select_all + P3 context_initialize
- [x] **T52** `gc1_runtime/layer4_atoms_p4.py` — P4 load_analysis_method (MTD dialog)
- [x] **T53** `gc1_runtime/layer4_atoms_p5_p7.py` — P5~P6 재사용 + P7 initialize_quantify
- [x] **T54** `gc1_runtime/layer4_atoms_p8_p9.py` — P8 print + P9 save (Hancom loop leaf 분리)
- [x] **T55** `gc1_runtime/layer4_job.py` — `run_autochro_export` 대체 진입: phase 순차 + resume_from + prep env

---

## G. L6·버그·연동 (기존 모듈 유지)

- [x] **T60** `gc_gc1.cleanup_superseded_gc1_files` — CL.05 verbatim PDF 오판 수정 + unittest (잘못된 PDF 삭제 재현 케이스)
- [x] **T61** `gc_autochro.py` — `GC1_USE_RUNTIME=1` 일 때 `gc1_runtime.layer4_job` 위임 (기본 0, 회귀 없음)
- [x] **T62** P4/P3/P7 사후 — `layer3_eye` TASK verify_peak_* 게이트 연결 (`GC1_RUNTIME_VERIFY_EYE=1`)
- [x] **T63** `test_gc1_runtime_e2e.py` — `AUTOCHRO_DRY_RUN=1` 전 phase atom status=ok 시뮬레이션

---

## H. 사용자 수정사항 슬롯 (내용은 다음 대화에서 채움)

- [x] **T70** **MOD-1** — MOD registry 인프라 (`gc1_mod_slots.json`, `mod_registry.py`, `validate_gc1_mod_slots.py`) — **atom 구현은 MOD-1 내용 입력 후**
- [x] **T71** **MOD-2** — MOD apply dry-run (`mod_apply.py`, `apply_gc1_mod.py`, `test_gc1_mod_apply.py`) — **atom 패치는 MOD-2 내용 입력 후**
- [x] **T72** **MOD-3** — MOD lifecycle (`mod_lifecycle.py`, `status_gc1_mod.py`, `close_gc1_mod.py`, `test_gc1_mod_lifecycle.py`) — **atom 패치는 MOD-3 내용 입력 후**

---

## I. 보류 (본 큐 완료 후 또는 blocked)

- [x] **T80** `deploy/ROADMAP.md` Step 8 E2E 보조 스크립트 문서 정합 — `scripts/run_gc1_runtime_e2e.py` + STEP8 §8.3d
- [x] **T81** `data_pc/` `--help`·`--no-archive` pytest — `test_data_pc_cli.py` + `build_cli_parser()`
- [x] **T82** `deploy/STEP7_gc1_calib.md` RT 검증 유틸 — `gc1_rt_validate.py` + `validate_gc1_rt.py` + `test_gc1_rt_validate.py` (실측 xlsx는 GC1 PC)
- [x] **T83** GC3 `gc3_screen_read.py` 스켈레톤 — `deploy/screen_regions.gc3.json` + `test_gc3_screen_read.py`
- [x] **T84** GC2 회귀 스크립트 dry-run 주석 — `run_gc2_regression.ps1` + `test_gc2_regression_script.py`

---

## J. 큐 완료 후 (회귀)

- [x] **T85** `scripts/run_gc1_queue_verify.py` — T20~T84 + MOD 파이프라인 일괄 검증 (`test_gc1_queue_verify.py`)
- [x] **T86** MOD intake CLI — `mod_intake.py`, `intake_gc1_mod.py`, `gc1_mod_slots.example.json` (`test_gc1_mod_intake.py`)
- [x] **T87** MOD pipeline runner — `mod_pipeline.py`, `run_gc1_mod_pipeline.py` (`test_gc1_mod_pipeline.py`)

---

- 새 단계: `- [ ] **Txx** …` 한 줄 추가 (한 턴 = 한 결과물)
- 처음부터: 완료 줄 `[ ]` 복원 + `agent_queue_state.json` → `"armed": false, "status": "idle"`
- Autochro 실장비·Origin GUI 필요 시: `"status": "blocked"` (Hook 중단)
