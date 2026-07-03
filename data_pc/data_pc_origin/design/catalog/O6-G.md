# O6-G — 장비·날짜 열 삽입 가드 (4 L4)

> modules: `o0_equipment_day` · `o6_guard` · `o6_resolve`

연구실 규칙: **같은 장비에서 하루 2회 실험 불가.** 새 열 추가 시 왼쪽 이웃 Comments 와 비교.

## O6-G-01-a-1 — 같은 날짜

동일 장비 + 동일 YYYYMMDD → `needs_user_confirm`

## O6-G-02-a-1 — 왼쪽 날짜가 더 최근

`left_date > new_date` → 날짜순 역전 의심

## O6-G-03-a-1 — 다음 날 OK

다음 날짜 + 같은 장비 → 가드 통과

## O6-G-04-a-1 — resolve 차단

`column_guard_confirm` 없이 `OriginColumnGuardError`

확인 UI: 터미널 대화형 `y/N` (`o9_facade`). watch/비대화형은 Origin 건너뜀.
env: `DATA_PC_SKIP_EQUIPMENT_DAY_GUARD=1` (테스트·긴급만).

```bash
python -m data_pc_origin.live_equipment_day_guard
python -m unittest data_pc_origin.tests.test_o6_equipment_guard data_pc_origin.tests.test_live_equipment_day_guard -v
```
