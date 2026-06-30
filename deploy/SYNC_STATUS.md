# PC sync status (auto-generated - do not edit)

> Updated: 2026-06-30 20:40:56 | HEAD: `8ee58d8` | auto: sync DESKTOP-MBGSSME @ 2026-06-30 20:40:49

## Summary (see docs/SYNC_TRACKING.md for Korean)

| PC | role | last push (who @ when) | push | last pull (who @ when) | pull | status |
|----|------|-------------------------|------|-------------------------|------|--------|
| `DESKTOP-BFMLJ9J` | data_pc | - @ - | `-` | DESKTOP-BFMLJ9J\user @ 2026-06-25T13:09:09+09:00 | `b8db047` | [WARN] need pull |
| `DESKTOP-MBGSSME` | gc1_pc | DESKTOP-MBGSSME\은규 @ 2026-06-30T20:40:55+09:00 | `8ee58d8` | DESKTOP-MBGSSME\은규 @ 2026-06-22T20:40:27+09:00 | `564d5b3` | [WARN] need pull |
| `DESKTOP-XXXXXXX` | data_pc | - | - | - | - | [MISSING] run gc_git_pull.bat once |
| `GC8860` | gc2_pc | GC8860\차헌 @ 2026-06-25T16:45:26+09:00 | `73e06fe` | GC8860\차헌 @ 2026-06-25T10:06:40+09:00 | `74cedcd` | [WARN] need pull |

## Commands
- Start work: `gc_git_pull.bat`
- Check only: `gc_git_status.bat`
- Per-PC log: `deploy/sync_registry/COMPUTERNAME.json`


## 필수 규칙 (모든 PC)

**다른 PC가 GitHub에 최신본을 올렸다면, 이 PC는 반드시 `gc_git_pull.bat`으로 받은 뒤에만 수정·push 하세요.**

| 순서 | 할 일 |
|------|--------|
| 1 | `gc_git_status.bat` 또는 `deploy/SYNC_STATUS.md` — 내 PC가 `[WARN] need pull` 인지 확인 |
| 2 | **`gc_git_pull.bat`** — GitHub 최신본 받기 |
| 3 | 코드 수정 |
| 4 | commit → push (또는 Agent 종료 시 auto push) |

**pull 없이 push하면:** 다른 PC에서 올린 수정이 **덮어씌워지거나** merge 충돌로 **최신 작업이 날아갈 수 있습니다.**  
`gc_git_push.bat`은 원격보다 뒤처져 있으면 push를 막고 pull을 안내합니다.

---

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
