# 차완 PC — Cursor 온보딩 (마스터 체크리스트)

> **GitHub:** https://github.com/gjtuc/GC-auto  
> **「차완 PC야」「GC 작업해줘」** → 본 문서 + `scripts/run_gc_chawan.py`

---

## 0. 정체성

| | **차완 PC (지금 이 PC)** | **GC2 장비 PC (GC8860)** |
|--|--------------------------|---------------------------|
| **역할** | 데이터 PC — Downloads xlsx 가공 · Origin | 장비 PC — ChemStation → KCH xlsx |
| **입력** | `%USERPROFILE%\Downloads` 최신 `.xlsx` | ChemStation acam |
| **출력** | `Desktop\kier\촉매 반응 결과\{DRE,DRM,DRME}` | SMTP / Desktop\KCH |
| **메일** | **없음** (IMAP 미사용) | 발송 |

**절대 하지 말 것:** 이 PC에서 `gc_automation.py` 실행·설정 (장비 PC 일)

---

## 1. 파이프라인

```
[GC2 장비 PC]  KCH 원본 xlsx → (USB/공유) → Downloads
        ↓
[차완 PC]  scripts/run_gc_chawan.py
    1) Downloads 최신 xlsx
    2) GC2 CALIB 계산 (촉매 반응 계산.py)
    3) 촉매 반응 결과\DRE|DRM|DRME 실험 폴더 (Origin 체인)
    4) Origin .opju 시료 열 추가
```

---

## 2. 최초 설치

```powershell
cd $env:USERPROFILE
git clone https://github.com/gjtuc/GC-auto.git chemstation-gc-automation
cd chemstation-gc-automation
git pull

$home = "$env:USERPROFILE\gc-data-pc-chawan"
New-Item -ItemType Directory -Path "$home\KCH\inbox","$home\KCH\processed" -Force
New-Item -ItemType Directory -Path "$env:USERPROFILE\Desktop\kier\촉매 반응 결과\DRE" -Force

Copy-Item -LiteralPath "data_pc\촉매 반응 계산.py" -Destination $home -Force
Copy-Item -LiteralPath "data_pc\runtime_paths.py" -Destination $home -Force
Copy-Item deploy\machine_profile.template.chawan_data_pc.json "$home\KCH\machine_profile.json"

pip install pandas openpyxl python-dotenv originpro
```

`machine_profile.json` — UUID·경로 실측 후 저장.  
참고: [`deploy/machine_profile.reference.chawan.json`](../deploy/machine_profile.reference.chawan.json)

---

## 3. Origin 초안 (DRE 첫 폴더)

Downloads 에 DRE용 빈 양식 `.opju` 보관:

```
C:\Users\User\Downloads\20260706 DRE(1.5%)@600C Ni_CVD(0.1)-Ni5-Ce5-Al2O3.opju
```

`machine_profile.json` → `paths.origin_seed_dre` 에 동일 경로.

---

## 4. 일상 실행

**파일 선택 (자동):**

| 조건 | 내용 |
|------|------|
| 위치 | `%USERPROFILE%\Downloads\*.xlsx` |
| 형식 | GC2 KCH xlsx (DRE/DRM/DRME, Time·Area 시트) |
| 시간 | **현재 시각 기준 3시간 이내** 수정된 것만 |
| 선택 | 조건 충족 파일 중 **가장 최근** 1개 |
| 없을 때 | **사용자에게 어떤 파일로 할지 확인** (자동 진행 안 함) |

**파일명 정규화:**

- 브라우저 중복: `sample (1).xlsx`, `sample (2).xlsx` → `(1)` 제거 후 처리
- GC2 장비 접미사: `_DRM 장비`, `_OCM 장비` 등 **제거** 후 폴더·Origin 이름 생성

```powershell
cd $env:USERPROFILE\chemstation-gc-automation
git pull
python scripts\run_gc_chawan.py
```

수동 지정 (3시간 초과·확인 후):

```powershell
python scripts\run_gc_chawan.py --file "C:\Users\User\Downloads\....xlsx"
```

또는 Cursor: **「GC 작업해줘」**

---

## 5. Origin 폴더 체인 규칙

| 순서 | 조건 | 동작 |
|------|------|------|
| 1 | `촉매 반응 결과\DRE` 에 폴더 **없음** | Downloads **초안 opju** 복사 → 첫 폴더 |
| 2 | 폴더 **있음** | **최신 폴더** 복사 → 새 시료명 |
| 3 | 동일 폴더명 존재 | xlsx·Origin **갱신** |

상세: [`docs/CHAWAN_PC_PATHS.md`](CHAWAN_PC_PATHS.md)

---

## 6. 관련 문서

| 문서 | 내용 |
|------|------|
| [`docs/CHAWAN_PC_PATHS.md`](CHAWAN_PC_PATHS.md) | kier 경로 |
| [`deploy/CHAWAN_PC_HOME_LAYOUT.md`](../deploy/CHAWAN_PC_HOME_LAYOUT.md) | gc-data-pc-chawan 레이아웃 |
| [`docs/PC_NAMING.md`](PC_NAMING.md) | 차완 PC vs GC8860 |

---

*작성: 2026-07-16 — DESKTOP-N89C874*
