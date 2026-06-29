# P3-S — Stage4 skip / DATA_PC_SKIP_ORIGIN (L4 #25–28)

| gate_id | symbol | assert |
|---------|--------|--------|
| P3-S-01-a-1 | `resolve_skip_stage4` | env `1` → skip |
| P3-S-02-a-1 | `resolve_skip_stage4` | explicit overrides env |
| P3-S-03-a-1 | `should_execute_stage4` | skip → False |
| P3-S-04-a-1 | `stage4_skip_reason` | UX 문자열 |

Module: `p3_skip.py` · O2 `skip_origin_active` 위임

촉매 `_skip_origin_enabled(explicit)` (L368–375) 와 동일 우선순위.
