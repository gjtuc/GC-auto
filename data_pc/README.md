# 데이터 PC — `촉매 반응 계산.py` 안내

> **GitHub:** https://github.com/gjtuc/GC-auto/tree/main/data_pc  
> **전체 맥락:** [`docs/CODEBASE_GUIDE.md`](../docs/CODEBASE_GUIDE.md)

## 이 PC의 역할

**은규의 일반 업무 PC (데이터 PC)** 입니다.  
GC1 장비 PC가 보낸 메일을 받아 **계산 → G: → Origin** 까지 처리합니다.

| 단계 | 작업 |
|------|------|
| 1 | 네이버 IMAP 메일 수신 → `KCH/inbox/` |
| 2 | 수율·전환율 계산 → `KCH/processed/` |
| 3 | G: 실험 폴더 생성·갱신 |
| 4 | Origin `.opju` 워크시트 열 추가 |

---

## 권장 설치 위치

```
Desktop\.cursor\
  촉매 반응 계산.py
  gc_automation.env          ← example 복사 후 작성
  KCH\
    inbox\
    processed\
    machine_profile.json     ← template 복사 후 작성
```

스크립트는 `SCRIPT_DIR` 기준으로 `KCH\` 를 찾습니다.  
**바탕화면 `.cursor` 폴더 안**에 두는 것을 권장합니다.

---

## 최초 설정

### 1. 환경 파일

```powershell
copy gc_automation.env.example gc_automation.env
# 메모장으로 은규 네이버 메일·앱비밀번호 입력
```

### 2. machine_profile.json

`KCH/machine_profile.template.json` 을 복사한 뒤, 은규 PC에서:

```powershell
Get-CimInstance Win32_ComputerSystemProduct | Select-Object UUID
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Cryptography' | Select-Object MachineGuid
```

값을 채워 `machine_profile.json` 으로 저장합니다.

### 3. GC1 교정 상수

`촉매 반응 계산.py` 상단 USER SETTINGS 의 **GC2/GC3 블록은 차헌용**입니다.  
GC1 RT·CALIB를 실측한 뒤 **GC1 전용 블록**을 추가하거나 기존 블록을 교체해야 합니다.

---

## 실행

```powershell
python "c:\Users\user\Desktop\.cursor\촉매 반응 계산.py"
```

옵션:

| 옵션 | 의미 |
|------|------|
| (없음) | 메일 → 계산 → G: → Origin 전체 |
| `--no-archive` | 계산만 (G:·Origin 생략) |
| `--manual 파일.xlsx` | 지정 엑셀만 처리 |

G:가 없으면 SecuYouSB 로그인 후 재실행.

---

## 메일 수신 규칙 (차헌과 동일 로직)

- **받은메일함:** 제목에 `GC 분석 결과` 포함 또는 xlsx 첨부
- **보낸·내게쓴:** 미읽음 + xlsx 첨부 (내게쓴은 키워드 없어도 처리)
- 같은 시료 메일 여러 통 → **오래된 순** 전건 반영
- 시료명이 다르면 **별도 실험**으로 처리

---

## 주의

- 이 PC에서 **gc_automation.py 를 실행하지 마세요** (ChemStation·장비 PC 전용)
- 차헌 `gc_automation.env` 비밀번호는 패키지에 **포함되지 않음**
- Origin·G: 는 은규 PC 환경에서 직접 확인
