# Agent 작업 큐

> **시작:** Agent 채팅에 `큐 시작` 한 번만 입력.  
> (은규 PC 일상 파이프라인 `진행`/`시작`과 별개 — 코드 작업 큐는 **`큐 시작`**)

| 파일 | 역할 |
|------|------|
| 본 문서 | 단계 목록 (`[ ]` / `[x]`) |
| `.cursor/agent_queue_state.json` | armed / complete / blocked |
| `.cursor/hooks/task_queue_continue.ps1` | 턴 끝에 다음 단계 자동 전송 |

**끝나면:** Hook이 `{}`만 내서 자동 멈춤. `status: complete` 확인.

---

## 단계 (기초 → 고급, 한 턴에 하나)

- [x] **T01** `task_queue_continue.ps1` + `hooks.json` 등록 — stop Hook이 followup 또는 `{}` 반환하는지 stdin 시뮬레이션으로 실행 검증
- [ ] **T02** `agent-task-queue.mdc` Rule — `큐 시작` 시 `armed:true` 쓰기, 첫 `[ ]` 단계만 수행, 완료 시 `[x]`
- [ ] **T03** Hook 통합 dry-run — `armed`+미완료 큐 → followup JSON; 큐 전부 `[x]` → `complete`+`{}`
- [ ] **T04** `deploy/ROADMAP.md` Step 8 — repo 내 E2E 보조 스크립트·테스트 정리 (`verify_e2e_prerequisites.ps1`, `test_e2e_mail_auth.py` 문서·주석 정합)
- [ ] **T05** `data_pc/` — `--help`·`--no-archive` 경로 단위 테스트 스크립트 또는 pytest 추가 (실행 검증 포함)
- [ ] **T06** `deploy/STEP7_gc1_calib.md` — CALIB 실측 전 repo 측 RT 검증 유틸·주석 (PC 실측은 블로커 시 `blocked`)
- [ ] **T07** `deploy/GC3_SCREEN_REGION_READ.md` — 캡처·OCR 프로토타입 스켈레톤 모듈 (`gc3_screen_read.py` 등) + 단위 실행 테스트
- [ ] **T08** `run_gc2_regression.ps1` / `verify_gc2_setup.ps1` — 회귀 스크립트 dry-run·주석 (GC2 장비 PC 실행은 별도)

---

## 큐 수정 방법

- 새 단계 추가: 위 목록에 `- [ ] **Txx** ...` 한 줄 추가
- 다시 돌리기: 완료한 줄을 `[ ]`로 되돌리고 `agent_queue_state.json` → `"armed": false, "status": "idle"`
