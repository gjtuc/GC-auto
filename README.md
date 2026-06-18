# chemstation-gc-automation

> **GitHub 업로드 출처: GC2 PC (kimcha)** — 2026-06-18  
> 계정 `gjtuc` · push는 **GC2 PC**에서 수행. **GC1 PC에서 올린 것이 아님.**

GC1(박은규) PC는 이 repo를 **받아서 통합·배포**하는 쪽입니다.

---

## 이 repo에 들어 있는 것

| 구분 | 내용 |
|------|------|
| **GC1 원본** | Autochro→PDF→엑셀→메일 (`gc_autochro`, `gc_gc1`) — GC1에서 최적화·검증 완료 |
| **GC2 추가** | merge 후 8860 회귀 테스트 + 운영 중 안정화 (`gc_work_job`, `gc_watchdog`, pending 메일 재시도 등) |
| **공통** | `gc_watch`, `gc_state`, `gc_mailer`, `gc_profiles` — GC1/GC2/GC3 분기 |

---

## PC별 역할

| PC | 운영자 | 프로필 | 출력·env |
|----|--------|--------|----------|
| **GC1** | 박은규 | `gc1` | `Desktop\박은규`, iPhone, john3556 |
| **GC2** | kimcha | `gc2` | `Desktop\KCH`, AndroidHotspot5841, 8860 |
| **GC3** | kimcha | `gc3` | `Desktop\KCH`, Chem32 Report |

한 repo, **PC마다 env만 다름** (`gc_profiles.py`).

---

## GC1 PC — 처음 받을 때

```powershell
git clone https://github.com/gjtuc/GC-auto.git
cd GC-auto
# Desktop\박은규\gc_automation.env 는 기존 운영값 유지 (덮어쓰지 않음)
gc1_setup.bat
python gc_automation.py --show-profile   # gc1, iPhone 확인
```

**상세 절차·체크리스트**: [`deploy/GC1_Cursor_핸드오프.md`](deploy/GC1_Cursor_핸드오프.md)  
(GC1 Cursor 채팅에 전체 붙여넣기 가능)

---

## GC2 PC — 수정 후 올릴 때

```powershell
cd C:\Users\User\chemstation-gc-automation
git add .
git commit -m "변경 요약"
git push
```

---

## GC1 PC — 이후 업데이트

```powershell
cd chemstation-gc-automation
git pull
```

---

## 문서·구조

| 파일 | 용도 |
|------|------|
| `gc_architecture.py` | 전체 맵·함정 (실행 코드 없음) |
| `deploy/GC1_Cursor_핸드오프.md` | GC1 통합·배포 가이드 |
| `deploy/GC2_Cursor_핸드오프.md` | GC2 역배포 참고 |
| `.cursor/rules/gc-initiation-force.mdc` | Cursor 「진행」→ force |

**비밀번호 env는 Git에 없음** — 각 PC의 `gc_automation.env`만 로컬 유지.
