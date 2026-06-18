# GitHub 자동 동기화 — 모든 PC 공통

> **한 줄:** 작업 시작 = 최신본 pull · 작업 끝 = GitHub auto push  
> **PC 명칭:** [`PC_NAMING.md`](PC_NAMING.md)

---

## 파이프라인 (자동)

```
[Cursor 채팅/Agent 시작]
    sessionStart hook → scripts/git_auto_sync.ps1 -Mode ensure-latest
    → fetch → 뒤처지면 pull --rebase → sync_registry pull

[코드 수정 · Agent 작업]

[Agent 종료]
    stop hook → scripts/git_auto_sync.ps1 -Mode stop
    → (필요 시 pull) → commit → sync_registry push → push origin main
```

**수동으로 할 때** (Cursor 없이 PowerShell만 쓸 때):

| 시점 | 명령 |
|------|------|
| 작업 시작 | `gc_git_begin.bat` 또는 `gc_git_pull.bat` |
| 작업 끝 | `gc_git_push.bat` (변경 있을 때) |
| 현황만 | `gc_git_status.bat` |

---

## PC별 최초 1회 설정 (4종 PC 공통)

repo clone 후 **한 번만**:

```powershell
cd C:\Users\User\chemstation-gc-automation
gc_git_init.bat          # .githooks/post-merge → pull 기록
gc_git_pull.bat          # sync_registry\{COMPUTERNAME}.json 생성
```

확인:

```powershell
gc_git_status.bat        # deploy\SYNC_STATUS.md — 내 PC [OK] latest
```

`.cursor/hooks.json` 은 **repo에 포함** — Cursor로 이 폴더를 열면 hook 자동 적용.

---

## PC 종류별 추가 (로컬만, Git 제외)

| PC | machine_profile | env |
|----|-----------------|-----|
| GC1 장비 PC | `Desktop\박은규\machine_profile.json` | `Desktop\박은규\gc_automation.env` |
| GC2/GC3 장비 PC | `Desktop\KCH\machine_profile.json` | `Desktop\KCH\gc_automation.env` |
| 은규 PC / 차헌 PC | `Desktop\.cursor\PEG\` 또는 `Desktop\.cursor\KCH\machine_profile.json` | `Desktop\.cursor\gc_automation.env` |

---

## 필수 규칙

1. **`[WARN] need pull` 이면 수정·push 금지** → `gc_git_pull.bat` 먼저  
2. **비밀번호·env·machine_profile 은 절대 commit 안 됨** (`.gitignore`)  
3. **다른 PC가 push 했으면** 이 PC는 sessionStart 또는 `gc_git_pull` 로 받은 뒤 작업  
4. **zip만 복사하지 말 것** — 항상 `git pull`

---

## 구현 파일

| 파일 | 역할 |
|------|------|
| `scripts/git_auto_sync.ps1` | **공통 엔진** (pull / push / stop / ensure-latest) |
| `.cursor/hooks/session_start_git_pull.ps1` | Cursor 시작 시 pull |
| `.cursor/hooks/auto_git_sync.ps1` | Cursor 종료 시 push |
| `scripts/sync_registry.ps1` | PC별 pull/push 시각 → `SYNC_STATUS.md` |
| `gc_git_pull.bat` / `gc_git_push.bat` | 수동 동기화 |
| `gc_git_begin.bat` | 작업 시작 (pull + status) |
| `.githooks/post-merge` | `git pull` 시 registry 기록 |

---

## 로그 (문제 시)

| 로그 | 위치 |
|------|------|
| Agent 종료 push | `.cursor/hooks/auto_git_sync.log` |
| 세션 시작 pull | `.cursor/hooks/session_start_git.log` |

push 실패 시: GitHub 로그인(`gh auth` / Git Credential Manager) 확인.

---

## Cursor Agent 규칙

`.cursor/rules/git-auto-sync.mdc` — Agent가 코드 수정 전 pull·종료 시 push 하도록 안내.

---

## 다른 PC에 이 기능 배포

1. `gc_git_pull.bat` — 최신 코드 + hook 수신  
2. `gc_git_init.bat` — 1회  
3. `gc_git_status.bat` — `[OK] latest` 확인  
4. 이후 Cursor Agent 사용 시 **자동** sessionStart/stop 동기화

상세 PC 목록: `deploy/sync_registry/EXPECTED_PCS.json`
