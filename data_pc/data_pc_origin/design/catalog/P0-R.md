# P0-R — Workflow routing (L4 #7–10)

촉매 `run_workflow_for_file` 분기와 1:1 대응.

| gate_id | 조건 | `WorkflowMode` |
|---------|------|----------------|
| P0-R-01-a-1 | `opju_path` non-empty | `OPJU_ONLY` |
| P0-R-02-a-1 | `auto_archive is False` | `CALC_ONLY` |
| P0-R-03-a-1 | else | `FULL_ARCHIVE` |
| P0-R-04-a-1 | `skip_stage4` / env | options flag |

Module: `p0_routing.py` · `resolve_workflow_mode(options)`

우선순위: **OPJU_ONLY > CALC_ONLY > FULL_ARCHIVE** (촉매 L2227–2245 동일).
