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
