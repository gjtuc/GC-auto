# PC 간 GitHub 동기화 추적

> **한눈에 보기:** [`deploy/SYNC_STATUS.md`](../deploy/SYNC_STATUS.md)  
> **PC별 상세:** `deploy/sync_registry/{컴퓨터이름}.json`

---

## 왜 필요한가

코드가 **한 repo**로 통합되면:

- 은규 PC(GC1)가 수정 → push  
- 차헌 PC(GC2)가 아직 `pull` 안 함 → **구버전으로 작업** 위험  

이를 막기 위해 **누가·언제·어떤 commit까지** 올리고 받았는지 repo 안에 기록합니다.

---

## 파일 구조

```
deploy/
├── SYNC_STATUS.md              ← 자동 생성 표 (수정 금지)
└── sync_registry/
    ├── README.md
    ├── EXPECTED_PCS.json       ← 연구실 PC 목록 (수동 편집)
    ├── DESKTOP-MBGSSME.json    ← PC마다 1개 (자동)
    └── _template.json

scripts/sync_registry.ps1       ← 기록 + SYNC_STATUS 갱신 엔진
```

### `{COMPUTERNAME}.json` 예시

```json
{
  "pc_id": "DESKTOP-MBGSSME",
  "label": "은규 — GC1 PC",
  "role": "gc1_pc",
  "operator": "은규",
  "sync": {
    "last_push_at": "2026-06-18T14:40:00+09:00",
    "last_push_commit": "abc1234",
    "last_push_by": "DESKTOP-MBGSSME\\은규",
    "last_pull_at": "2026-06-18T09:00:00+09:00",
    "last_pull_commit": "def5678",
    "last_pull_by": "DESKTOP-MBGSSME\\User"
  },
  "history": [
    { "event": "push", "at": "...", "commit": "abc1234", "by": "..." }
  ]
}
```

---

## 매일 루틴

| 시점 | 명령 | 기록 |
|------|------|------|
| **작업 시작** | `gc_git_pull.bat` | `last_pull_*` 갱신 → GitHub push |
| **작업 종료** | Commit/Push 또는 Agent auto hook | `last_push_*` 갱신 |
| **현황만** | `gc_git_status.bat` | SYNC_STATUS.md 출력 |

---

## SYNC_STATUS.md 상태 표

| 표시 | 의미 | 할 일 |
|------|------|--------|
| ✅ 최신 | pull commit == repo HEAD | 작업 계속 |
| ⚠ **pull 필요** | 다른 PC가 push 함 | **`gc_git_pull.bat`** |
| 📤 push만 | 올리기만 하고 pull 기록 없음 | pull 한 번 |
| ❓ **미등록** | EXPECTED_PCS 에만 있고 json 없음 | pull/push 1회 |

---

## 새 PC 등록 (차헌 GC2 PC 등)

1. `git clone` 또는 `git pull`
2. `Desktop\...\machine_profile.json` 작성 (Step 2)
3. **`gc_git_pull.bat`** 한 번 실행 → `{COMPUTERNAME}.json` 자동 생성
4. `deploy/sync_registry/EXPECTED_PCS.json` 에 PC 한 줄 추가 (pc_id = 컴퓨터 이름)

```powershell
# PC ID 확인
$env:COMPUTERNAME
Get-CimInstance Win32_ComputerSystemProduct | Select UUID
```

---

## Git hook (선택)

```powershell
git config core.hooksPath .githooks
```

→ `git pull` merge 후 `post-merge` 가 pull 기록 ( `gc_git_pull.bat` 과 중복 가능)

---

## commit 메시지 규칙

| 패턴 | 의미 |
|------|------|
| `auto: sync DESKTOP-XXX @ ...` | Agent 자동 코드 sync |
| `sync: registry DESKTOP-XXX push` | push 수신 기록 |
| `sync: registry DESKTOP-XXX pull` | pull 수신 기록 |

`git log` 만 봐도 **어느 PC가 올렸는지** 알 수 있습니다.

---

## 주의

- `SYNC_STATUS.md` 는 **직접 수정하지 마세요** — 다음 pull/push 때 덮어씀
- registry json 은 **본인 PC 것만** 갱신 (파일명 = COMPUTERNAME)
- 비밀번호·env 는 여전히 Git 제외
