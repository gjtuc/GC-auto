# GC1 장비 PC — `gc_automation.py` 안내

> **PC 명칭:** GC1 **장비** PC (은규) — [`PC_NAMING.md`](PC_NAMING.md)  
> **오해 금지:** GC1은 **ChemStation이 아닙니다.** YL6500 + **Autochro-3000** UI → PDF → 엑셀입니다.  
> **데이터 처리(계산·G:·Origin)** 는 **은규 PC**에서 `data_pc/촉매 반응 계산.py` 로 합니다.

---

## 이 PC의 역할

**Autochro가 설치된 GC1 장비 옆 PC**입니다.  
여기서는 **KCH 원본 엑셀을 만들고 메일로 보내는 것(1단계)** 까지만 합니다.

| 하는 일 | 안 하는 일 |
|---------|-----------|
| Autochro UI 자동화 → Hancom PDF | 수율/전환율 계산 |
| PDF 파싱·trim → KCH xlsx | G: 드라이브 정리 |
| 네이버 SMTP → **은규 PC** 메일 | Origin `.opju` 수정 |

---

## 동작 요약 (GC1 전용 — GC2와 다름)

1. **iPhone 핫스팟** 연결 edge (또는 `GC1_동작해줘.bat` / Cursor 「진행」 force)
2. `gc_autochro.py` — Autochro 제어목록 → Ctrl+A → 초기화+정량 → **PDF 저장**
3. `gc_gc1.py` — PDF에서 FID/TCD 피크 추출, 환원·첫 반응 trim → **KCH xlsx** (시트 2장)
4. `gc_mailer.py` — xlsx를 **은규 PC 네이버 메일**로 첨부 발송

> GC2/GC3는 ChemStation `sequence.acam_` / `Report.txt` 를 씁니다. **GC1 경로와 혼동하지 마세요.**

---

## env 위치 (장비 PC 전용)

| 파일 | 경로 | Git |
|------|------|-----|
| `gc_automation.env` | `Desktop\박은규\gc_automation.env` | ❌ 로컬만 (비밀번호) |
| `machine_profile.json` | `Desktop\박은규\machine_profile.json` (선택) | ❌ 로컬만 |
| 템플릿 | `deploy/gc_automation.env.gc1` | ✅ repo |

**절대 금지:** `Desktop\KCH\gc_automation.env` (GC2/GC3 장비 PC용) 내용을 GC1에 복사

---

## 은규가 GC1 장비 PC에서 확인·수정할 항목

| 항목 | 설명 |
|------|------|
| `GC_INSTANCE=gc1` | env — 장비 분기 |
| `EXCEL_OUTPUT_DIR` | `Desktop\박은규` (PDF·xlsx·watch 상태) |
| `REQUIRED_HOTSPOT=iPhone` | AndroidHotspot(GC2)과 다름 |
| `MAIL_TO` | **은규 PC**가 IMAP으로 읽는 네이버 주소 |
| `NAVER_EMAIL` / `NAVER_APP_PASSWORD` | 발송용 (장비 PC env) |
| `AUTOCHRO_ENABLED=1` | Autochro UI 자동화 on |

`gc_config.TARGET_EMAIL` 코드 기본값(`kimcha0809@...`)은 **차헌 레거시**입니다.  
실제 발송 주소는 **env `MAIL_TO`** 가 우선합니다.

---

## 실행 예

```powershell
cd C:\Users\User\chemstation-gc-automation
git pull
python gc_automation.py --show-profile   # gc1, iPhone, 박은규 확인

# 일상: 바탕화면 GC1_감시시작.bat (iPhone 연결 시 세션당 1회)
# 수동 전체: GC1_동작해줘.bat 또는
python gc_automation.py --user-message "진행"
```

GC2용 `--sequence-date` / ChemStation Data 폴더는 **GC1에서 사용하지 않습니다.**

---

## 다음 단계

1. `deploy/GC1_Cursor_핸드오프.md` — GC2에서 merge된 안정화 내역
2. `docs/00_인수인계_설명.md` — 2-PC 전체 파이프라인
3. `data_pc/` — **은규 PC**에 복사 후 Step 3·7 (`deploy/STEP3_data_pc.md`, `STEP7_gc1_calib.md`)
