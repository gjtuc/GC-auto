# P9-L — Live workflow E2E (L4 #60–63)

| gate_id | symbol | assert |
|---------|--------|--------|
| P9-L-01-a-1 | `prepare_live_workflow` | prep dict |
| P9-L-02-a-1 | `run_live_workflow` | artifact |
| P9-L-03-a-1 | artifact file | prep + mode |
| P9-L-04-a-1 | `resolve_live_excel_path` | empty opju |

Module: `live_workflow.py` · P8 bridge · env `DATA_PC_LIVE_OPJU`

Live 실행: `DATA_PC_SKIP_ORIGIN=0` + `python -m data_pc_origin.live_workflow [--dry] [opju]`

Companion xlsx(계산 결과)는 `make_companion_stage2_runner`로 로드 — KCH 원본 `process_excel` 불필요.
