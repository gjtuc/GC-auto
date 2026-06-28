# P층 — 메일·엑셀 ↔ Origin 연결 (Pipeline Integration)

> **O0~O9** = Origin COM 내부. **P층** = `촉매 반응 계산.py` 2~4단계와 O9 사이 **오케스트레이션**.  
> **originpro 금지:** P0~P3 · **mock만:** P4~P7.

## 경계

```
[1 메일 IMAP]  ← 촉매 (P층 밖, P7에서 훅만)
[2 process_excel] → df, saved_excel, warnings
[3 setup_experiment_folder] → G:, target_opju, archive_xlsx
[4 update_origin] → pipeline_bridge → O9
```

P층이 소유하는 것: **2의 산출물 타입화 · 3/4 분기 · skip_origin · O9 호출 인자 조립**.

## L0 모듈 (목표)

| L0 | module | 역할 |
|----|--------|------|
| P0 | `p0_types.py`, `p0_routing.py` | 순수 타입·경로 모드 (촉매/import 금지) |
| P1 | `p1_payload.py` | Stage2 → `OriginJobPayload` |
| P2 | `p2_paths.py` | opju 검증·`save_in_place` 규칙 |
| P3 | `p3_skip.py` | `DATA_PC_SKIP_ORIGIN` (O2 위임) |
| P4 | `p4_origin_stage.py` | `run_origin_update` 1회 (mock/live) |
| P5 | `p5_workflow.py` | `run_workflow_stages` (2→3→4 조합) |
| P6 | `p6_catalyst_adapter.py` | `촉매 반응 계산.py` 함수 importlib |
| P7 | `p7_mail_hook.py` | 메일 1건 → P5 (mock E2E) |

## L1 rollup

| rollup | L0 | L4(설계) |
|--------|-----|----------|
| P0 | pure | 10 |
| P1 | payload | 8 |
| P2 | paths | 6 |
| P3 | skip | 4 |
| P4 | origin stage | 6 |
| P5 | workflow | 9 |
| P6 | catalyst adapter | 8 |
| P7 | mail E2E | 4 |
| **P** | 합본 | **55** |

마스터 순서: [`design/catalog/P-REGISTRY.md`](design/catalog/P-REGISTRY.md)

## 의존

```
P0 → (없음, originpro·촉매 금지)
P1 → P0, O0 mapping (열 이름만)
P2 → P0, O1 probe (opju)
P3 → P0, O2 env
P4 → P1–P3, O9 pipeline_bridge
P5 → P1–P4
P6 → P5 + 촉매 (importlib, 테스트는 mock)
P7 → P6
```

## 검증

```bash
python -m data_pc_origin.verify --p0
python -m data_pc_origin.verify --p     # P0..P7 전부 (목표)
```

## 현재 포인터

```
DONE: O0..O9 + P0..P8 (59 L4) — verify --p PASS
LIVE: 촉매 run_workflow_for_file → workflow_bridge (P8)
```
