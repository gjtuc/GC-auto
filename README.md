# GC-auto (chemstation-gc-automation)

> **통합 GitHub:** https://github.com/gjtuc/GC-auto  
> GC1·GC2·GC3 **장비 PC 코드** + **데이터 PC 계산** + 문서를 **한 repo**에 모읍니다.

---

## 전체 그림

```
GitHub GC-auto (클라우드 — 모든 코드·문서)
        │
        ├── GC1 장비 PC (은규)     gc_automation.py — Autochro→PDF→메일
        ├── GC2/GC3 장비 PC (차헌) gc_automation.py — ChemStation→메일
        └── 데이터 PC (은규/차헌)  data_pc/촉매 반응 계산.py — 메일→G:→Origin
```

| PC | `machine_profile` / env | 실행 |
|----|-------------------------|------|
| GC1 장비 | `Desktop\박은규\gc_automation.env` | repo `gc_automation.py --watch` |
| GC2/GC3 | `Desktop\KCH\gc_automation.env` | repo `gc_automation.py --watch` |
| 데이터 PC | `Desktop\.cursor\gc_automation.env` | `data_pc/촉매 반응 계산.py` |

**비밀번호·machine_profile.json 실본은 Git에 없음** — 템플릿만 repo.

---

## PC 간 Git 필수 규칙

**어느 PC든 GitHub에 최신본을 올린 뒤, 다른 PC는 반드시 `pull` 받고 나서 수정·`push` 하세요.**  
pull 없이 push하면 **다른 PC에서 올린 수정이 덮어씌워지거나 날아갈 수 있습니다.**

```powershell
.\gc_git_pull.bat      # 1. 작업 시작 — 항상 먼저
# ... 수정 ...
git commit / Agent 종료  # 2. 올리기
.\gc_git_status.bat      # 3. 다른 PC도 [OK] latest 인지 확인
```

- 현황: [`deploy/SYNC_STATUS.md`](deploy/SYNC_STATUS.md) — `[WARN] need pull` 이면 **push 금지**, pull 먼저  
- 상세: [`docs/SYNC_TRACKING.md`](docs/SYNC_TRACKING.md)  
- **E2E 테스트:** [`deploy/STEP8_e2e.md`](deploy/STEP8_e2e.md)

---

## repo 구조

| 경로 | 내용 |
|------|------|
| `gc_*.py`, `gc_automation.py` | GC1/2/3 **장비 PC** 통합 CLI |
| `data_pc/` | **데이터 PC** — 촉매 반응 계산, KCH inbox/processed |
| `deploy/` | env 템플릿, PC별 핸드오프, Step 가이드 |
| `docs/` | 인수인계 설명 (차헌→은규) |
| `.cursor/hooks/` | Agent 종료 시 auto commit+push |

---

## 설정 진행 (Step)

| Step | 내용 | 문서 |
|------|------|------|
| 1 | GitHub 연동 | ✅ 완료 |
| 2 | PC 식별 `machine_profile` | [`deploy/STEP2_machine_profile.md`](deploy/STEP2_machine_profile.md) |
| 3 | 데이터 PC `data_pc/` | [`deploy/STEP3_data_pc.md`](deploy/STEP3_data_pc.md) |
| 4 | 인수인계·README | [`docs/00_인수인계_설명.md`](docs/00_인수인계_설명.md) |

---

## GC1 PC (은규) — 매일

```powershell
cd C:\Users\User\chemstation-gc-automation
git pull
python gc_automation.py --show-profile   # gc1, iPhone
```

- env: `Desktop\박은규\gc_automation.env` (덮어쓰지 않음)
- PC ID: `Desktop\박은규\machine_profile.json` (로컬)

---

## GC2 PC (차헌) — 수정 후

```powershell
git pull
# ... 수정 ...
git add .
git commit -m "변경 요약"
git push
```

---

## 자동 GitHub 업로드

- Agent 작업 **종료 시** → auto commit + push + **PC 동기화 기록**
- **`deploy/SYNC_STATUS.md`** — 어느 PC가 pull/push 했는지 표
- 작업 시작: **`gc_git_pull.bat`** | 현황: **`gc_git_status.bat`**
- 상세: [`docs/SYNC_TRACKING.md`](docs/SYNC_TRACKING.md)

---

## 문서

| 파일 | 용도 |
|------|------|
| **`docs/CODEBASE_GUIDE.md`** | **다른 PC에서 처음 읽을 때 (PC·파일·Git)** |
| `gc_architecture.py` | 장비 PC 코드 맵 (실행 없음) |
| `deploy/GC1_Cursor_핸드오프.md` | GC1 통합 체크리스트 |
| `deploy/GC2_Cursor_핸드오프.md` | GC2 역배포 |
| `docs/00_인수인계_설명.md` | 2-PC 파이프라인 전체 설명 |

---

## GC1 vs GC2/GC3 (장비)

| | GC1 | GC2 | GC3 |
|---|-----|-----|-----|
| 데이터 | Autochro PDF | ChemStation acam | Chem32 Report |
| 모듈 | `gc_autochro`, `gc_gc1` | `gc_chemstation` | `gc_chem32` |
| 분기 | `gc_profiles.py` + env | 동일 | `GC_INSTANCE=gc3` |
