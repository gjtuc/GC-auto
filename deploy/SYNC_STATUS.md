# PC sync status (auto-generated - do not edit)

> Updated: 2026-06-18 14:47:21 | HEAD: `e5d3c5c` | feat: PC sync tracking ??who pushed/pulled and who is behind

## Summary (see docs/SYNC_TRACKING.md for Korean)

| PC | role | last push (who @ when) | push | last pull (who @ when) | pull | status |
|----|------|-------------------------|------|-------------------------|------|--------|
| `DESKTOP-BFMLJ9J` | data_pc | - | - | - | - | [MISSING] run gc_git_pull.bat once |
| `DESKTOP-MBGSSME` | gc1_pc | DESKTOP-MBGSSME\User @ 2026-06-18T14:47:20+09:00 | `e5d3c5c` | DESKTOP-MBGSSME\User @ 2026-06-18T14:46:21+09:00 | `dff49c2` | [WARN] need pull |
| `DESKTOP-XXXXXXX` | gc2_pc | - | - | - | - | [MISSING] run gc_git_pull.bat once |

## Commands
- Start work: `gc_git_pull.bat`
- Check only: `gc_git_status.bat`
- Per-PC log: `deploy/sync_registry/COMPUTERNAME.json`


## 상태 표 (한글)

| 표시 | 의미 | 할 일 |
|------|------|--------|
| [OK] latest | 이 PC pull commit == repo 최신 HEAD | 작업 계속 |
| [WARN] need pull | 다른 PC가 push 함, 아직 pull 안 함 | **gc_git_pull.bat** |
| [PUSH] pushed only | push 기록만 있고 pull 기록 없음 | pull 한 번 |
| [MISSING] | EXPECTED_PCS 에만 있고 json 없음 | gc_git_pull.bat 1회 |
| [?] check | 수동 확인 | gc_git_status.bat |

## PC별 json 필드

- `last_push_at` / `last_push_by` / `last_push_commit` — 이 PC가 GitHub에 **올린** 시각·담당·commit
- `last_pull_at` / `last_pull_by` / `last_pull_commit` — 이 PC가 GitHub에서 **받은** 시각·담당·commit
- `history[]` — 최근 20건 (push/pull 이벤트)

상세: docs/SYNC_TRACKING.md
