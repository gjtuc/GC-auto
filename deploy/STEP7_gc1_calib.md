# Step 7 — GC1 CALIB / TIME (`촉매 반응 계산.py`)

> **작업 PC:** GC1 장비 PC에서 RT·표준가스 실측 → repo 반영 → **은규 PC**에서 `--no-archive` 검증  
> **금지:** GC2/GC3 CALIB·TIME 숫자를 GC1에 복사

---

## 7.1 — GC1과 GC2/GC3 차이 (전제)

| | GC1 (은규, YL6500) | GC2 (8860) | GC3 (Chem32) |
|---|-------------------|------------|--------------|
| 장비 PC 출력 | Autochro PDF → xlsx | ChemStation acam | Report |
| 엑셀 시트 | **FID + TCD** 2장 | 1장 통합 | FID + TCD |
| H2 RT (대략) | **~2.0분** | ~0.5분 | ~0.7분 |
| CALIB 방식 | **나눗셈** (GC3와 동일, 표준가스로 확인) | 곱셈 | 나눗셈 |
| 계산 출력 접미사 | `_GC1_DRE_` / `_GC1_DRM_` | `_GC2_DRE_` / `_GC2_DRM_` | `_GC3_DRME_` |

GC1 담당 반응(현재 env 기준 DRE 위주): 파일명 `... DRE@온도` 또는 `... DRM@...` — `get_reaction_type_from_filename()` 동일.

---

## 7.2 — TIME (RT 구간) 실측

### A) 1차값 (코드에 반영됨)

`gc_gc1.py` `DEFAULT_FID_WINDOWS` / `DEFAULT_TCD_WINDOWS` 와 동일:

| 검출기 | 성분 | 중심 RT (분) | ± | TIME 구간 |
|--------|------|-------------|---|-----------|
| TCD | H2 | 2.0 | 0.35 | 1.65 – 2.35 |
| TCD | CO | 6.6 | 0.8 | 5.8 – 7.4 |
| TCD | CO2 | 16.2 | 1.2 | 15.0 – 17.4 |
| FID | CH4 | 1.4 | 0.35 | 1.05 – 1.75 |
| FID | C2H6 | 1.9 | 0.35 | 1.55 – 2.25 |
| FID | C2H4 | 2.3 | 0.35 | 1.95 – 2.65 |

### B) GC1 장비 PC에서 검증 (필수)

```powershell
cd C:\Users\User\chemstation-gc-automation
git pull

# GC1이 만든 KCH 원본 xlsx 1개 (Desktop\박은규 또는 메일 첨부)
python scripts/extract_gc1_rt_from_xlsx.py "C:\path\to\YYYYMMDD ... DRE@600.xlsx"
```

출력 RT가 위 표와 **0.1분 이상** 어긋나면 `data_pc/촉매 반응 계산.py` 의 `GC1_TIME_TCD` / `GC1_TIME_FID` 수정.

---

## 7.3 — CALIB (Area ↔ ppm) 실측

`GC1_CALIB_READY = False` 인 동안 GC1 파일 계산은 **중단**되고 안내 메시지가 나옵니다.

### 절차

1. **표준가스** 또는 **알려진 feed 농도** 1주입이 있는 GC1 KCH xlsx 준비  
2. 각 성분의 **Area**와 **실제 ppm**(또는 %×10000) 기록  
3. 나눗셈 교정: `GC1_CALIB[gas] = Area / ppm` (GC3와 동일)

```powershell
python scripts/suggest_gc1_calib.py "표준가스.xlsx" --gas H2 --ppm 50000 --cycle 1
python scripts/suggest_gc1_calib.py "표준가스.xlsx" --gas CO --ppm 10000 --cycle 1
# ... CH4, CO2, C2H6, C2H4
```

4. `data_pc/촉매 반응 계산.py` USER SETTINGS:

```python
GC1_CALIB = {
    'H2': ..., 'CO': ..., 'CO2': ...,
    'CH4': ..., 'C2H6': ..., 'C2H4': ...,
}
GC1_CALIB_READY = True   # 실측 완료 후만 True
```

5. feed fallback (파일명에 % 없을 때):

```python
GC1_INITIAL_C2H6 = 15000   # DRE 1.5% — 실험 기본값에 맞게
GC1_INITIAL_CO2  = 30000
GC1_DRM_INITIAL_CH4 = 50000
GC1_DRM_INITIAL_CO2 = 50000
```

---

## 7.4 — 코드 반영 (repo)

| 파일 | 내용 |
|------|------|
| `data_pc/촉매 반응 계산.py` | `GC1_TIME_*`, `GC1_CALIB`, `process_excel` GC1 분기 |
| `scripts/extract_gc1_rt_from_xlsx.py` | RT 실측 도우미 |
| `scripts/suggest_gc1_calib.py` | CALIB 산출 도우미 |

반영 후:

```powershell
Copy-Item -LiteralPath "data_pc\촉매 반응 계산.py" "$env:USERPROFILE\Desktop\.cursor\" -Force
```

---

## 7.5 — 검증 (`--no-archive`)

**은규 PC**(또는 `Desktop\.cursor\`)에서 G:/Origin 없이:

```powershell
python "Desktop\.cursor\촉매 반응 계산.py" --manual
# GC1 KCH xlsx 경로 입력

python "Desktop\.cursor\촉매 반응 계산.py" --no-archive
# 또는 inbox에 GC1 메일 xlsx 넣고 실행
```

**PASS 기준:**

- 장비 판별 `GC1` (GC2/GC3와 혼동 없음)
- `KCH/processed/*_GC1_DRE_계산완료.xlsx` 생성
- 수율/전환율이 Origin 수동값과 **대략 일치** (CALIB 오차 ±몇 %p 이내)

---

## 7.6 — GitHub 반영

```powershell
gc_git_pull.bat
# 수정 후 commit
gc_git_push.bat
```

다른 PC(GC2/GC3 장비 PC, 차헌 PC)는 **pull 후** 작업.

---

## Step 7 체크리스트

- [x] 7.1 문서·GC1 TIME 1차값 (`gc_gc1` 동기화)
- [x] 7.2 RT 추출 스크립트
- [x] 7.3 CALIB 제안 스크립트
- [x] 7.4 `process_excel` GC1 분기 (CALIB 미완 시 안전 중단)
- [ ] 7.5 GC1 KCH xlsx로 RT 실측 검증 (**GC1 장비 PC — 사용자**)
- [ ] 7.6 표준가스로 CALIB 입력 + `GC1_CALIB_READY = True` (**사용자**)
- [ ] 7.7 `--no-archive` 계산 검증 (**은규 PC**)

---

## 다음: Step 8

[`deploy/STEP8_e2e.md`](STEP8_e2e.md) — GC1 메일 → 은규 PC → G: → Origin (Step 7 CALIB 완료 후)
