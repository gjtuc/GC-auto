# Step 3 — 은규 PC / 차헌 PC (`data_pc/`)

> PC 명칭: [`docs/PC_NAMING.md`](../docs/PC_NAMING.md)

## 역할

GC **장비 PC**가 보낸 KCH 원본 메일을 받아:

1. IMAP 수신 → `KCH/inbox/`
2. 수율·전환율 계산 → `KCH/processed/`
3. G: 실험 폴더
4. Origin `.opju` 업데이트

## repo 구조

```
data_pc/
├── 촉매 반응 계산.py          ← 메인 스크립트
├── gc_automation.env.example
├── README.md
└── KCH/
    ├── inbox/               ← 메일 수신 xlsx
    ├── processed/           ← 계산 완료 사본
    └── machine_profile.template.json
```

## 은규 PC 설치 (한 번)

상세 micro-step: **`deploy/STEP6_data_pc_setup.md`**

### A) repo에서 복사 (권장)

```powershell
cd C:\Users\User\chemstation-gc-automation
git pull

# Desktop\.cursor 에 배치 (차헌 운용과 동일)
mkdir "$env:USERPROFILE\Desktop\.cursor\KCH\inbox" -Force
mkdir "$env:USERPROFILE\Desktop\.cursor\KCH\processed" -Force
Copy-Item data_pc\촉매` 반응` 계산.py "$env:USERPROFILE\Desktop\.cursor\"
Copy-Item data_pc\gc_automation.env.example "$env:USERPROFILE\Desktop\.cursor\gc_automation.env"
Copy-Item data_pc\KCH\machine_profile.template.json "$env:USERPROFILE\Desktop\.cursor\KCH\machine_profile.json"
# machine_profile.json identifiers 채우기
# gc_automation.env 에 은규 네이버 앱비밀번호 입력
```

### B) 실행

```powershell
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py"
```

G: 없으면 SecuYouSB 로그인 후 재실행.

## GC1 vs GC2/GC3 교정

`촉매 반응 계산.py` USER SETTINGS:

| | GC2 | GC3 | GC1 (은규) |
|---|-----|-----|------------|
| CALIB/TIME | 차헌 실측값 | 차헌 실측값 | **실측 후 추가 필요** |

zip 인수인계 문서: `docs/00_인수인계_설명.md` §5

## 장비 PC와 구분

| PC | 실행 스크립트 |
|----|---------------|
| GC1 장비 (Autochro) | repo 루트 `gc_automation.py --watch` |
| 데이터 PC | `data_pc/촉매 반응 계산.py` |

**장비 PC에서 촉매 반응 계산.py 실행 금지** (Origin·G: 환경 다름)

---

## 자동 감시 (`--watch`)

Wi-Fi 연결 시 메일·계산·Origin 자동 실행. 상세: **`deploy/DATA_PC_WATCH.md`**

차헌 PC Windows 등록:

```bat
deploy\gc_data_pc_install_autostart_chaheon.bat
```

| 옵션 | 의미 |
|------|------|
| `--watch` | 백그라운드 감시 (pythonw + 작업 스케줄러 권장) |
| `--poll-once` | 메일 1회 확인 후 종료 |
| `--no-wifi-check` | 테스트용 SSID 검사 생략 |
