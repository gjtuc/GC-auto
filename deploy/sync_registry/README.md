# PC 동기화 기록 (sync_registry)

## 목적

GitHub `GC-auto` repo를 **어느 PC가 언제 올렸고(pull/push), 누가 최신인지** 추적합니다.

| 파일 | 설명 |
|------|------|
| `{COMPUTERNAME}.json` | **PC마다 1개** — 본인 PC만 갱신 (충돌 적음) |
| `EXPECTED_PCS.json` | 연구실에 있어야 할 PC 목록 (수동 편집) |
| `../SYNC_STATUS.md` | **자동 생성** — 전 PC 현황 표 (직접 수정 금지) |

## 자동 갱신 시점

| 이벤트 | 스크립트 |
|--------|----------|
| **push** (코드 올림) | `.cursor/hooks/auto_git_sync.ps1` → `scripts/sync_registry.ps1 -Event push` |
| **pull** (코드 받음) | `gc_git_pull.bat` 또는 git `post-merge` hook |

## PC에서 할 일

```powershell
# 작업 시작 — 반드시 pull (동기화 기록 포함)
.\gc_git_pull.bat

# 현황만 확인
.\gc_git_status.bat
```

## 상태 표시 (SYNC_STATUS.md)

| 표시 | 의미 |
|------|------|
| ✅ 최신 | `last_pull_commit` == repo HEAD |
| ⚠ pull 필요 | 다른 PC가 push 함 — `git pull` |
| 📤 push만 함 | 이 PC는 올렸지만 pull 기록 없음 |
| ❓ 미등록 | EXPECTED_PCS 에는 있으나 json 없음 — 한 번 pull/push |
| — | EXPECTED_PCS 에 없음 — EXPECTED_PCS.json 에 추가 |

## machine_profile 과의 관계

- `Desktop\박은규\machine_profile.json` (장비 PC)
- `Desktop\.cursor\KCH\machine_profile.json` (데이터 PC)

→ sync_registry.ps1 이 있으면 operator/role 자동 채움.

상세: `docs/SYNC_TRACKING.md`
