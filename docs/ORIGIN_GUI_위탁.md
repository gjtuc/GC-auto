# Origin — 엑셀까지 자동, Origin은 GUI 위탁

> **마스터 운영 가이드** (2026-11-19 차헌 데이터 PC 실증·합의).  
> 에이전트·사람 모두 이 문서를 Origin 구간 기준으로 본다.

관련: [`ORIGIN_PE_FOLDER.md`](ORIGIN_PE_FOLDER.md) · [`.cursor/rules/origin-book-not-graph.mdc`](../.cursor/rules/origin-book-not-graph.mdc) · [`DATA_PC_ORIGIN_SAVE.md`](DATA_PC_ORIGIN_SAVE.md) · 매핑 `data_pc_origin/o0_mapping.py`

---

## 0. 한 줄 요약

| 구간 | 담당 |
|------|------|
| 메일 → 계산 → 엑셀 → G:/연구노트 실험 폴더 | **`.py`** (`DATA_PC_SKIP_ORIGIN=1`) |
| 북시트 숫자·Comments · 그래프 Plot | **확인 후 GUI** (COM 일상 쓰기 금지) |

COM으로 Origin을 쓰다 **열 절단·행 밀림·축 깨짐·오삭제**가 반복되어 위탁으로 나눴다.

### 0-1. 트리거 — 「GC 작업해줘」

데이터 PC(차헌·은규)에서 사용자가 **「GC 작업해줘」** / **「gc 작업해줘」** 라고 하면, 아래를 **이어서** 진행한다 (한 시료 단위·위탁 규칙 전부 적용).

1. 처리할 메일/시료 파악 — 종류가 여러 개면 **어느 시료인지 질문** 후 하나만  
2. `.py` 자동 (`DATA_PC_SKIP_ORIGIN=1`) — 메일→계산→엑셀→실험 폴더  
3. Origin: opju·PE·Comments·기존/새 열 **확인** (새 열이면 왼쪽 Comments+파일명 **제안**)  
4. 확인 후 북시트 반영 (매핑·PE)  
5. 새 열이면 Plot (전 성분 그래프, **Rescale 금지**, §7-4 색)  
6. 색 적용 후 **반드시** 「색 바꾸고 싶으면 말해 주세요」라고 안내  
7. opju 저장(Ctrl+S) 안내  

차완 PC의 「GC 작업해줘」는 Downloads 파이프라인(`chawan-pc-entry`) — **별도**.

---

## 1. 왜 COM을 일상에서 끄나 (실증)

| 현상 | 주의 |
|------|------|
| 짧은 `from_list` | 열 길이가 리스트 끝으로 **잘림** |
| `start=` | 문서(1-based)와 실제가 어긋날 수 있음 → 한 칸 밀림 |
| 셀 Clear(숫자만 삭제) | 그래프 **Plot은 남음** (“지웠는데 131까지” 체감) |
| `del_col`로 열 삭제 | 해당 Plot은 같이 사라지는 편 |
| Plot 추가 + Rescale on Apply | **축 스케일 깨짐** |
| 잘못된 열(CM vs CN)·Y축 잘림 | “그래프가 안 바뀐다”처럼 보임 |

**주의:** Plot 추가는 COM `add_plot`으로도 되지만, 축·실수 위험 때문에 **기본은 GUI**. 에이전트가 보조할 때도 **Rescale 금지·축 복구** 필수.

---

## 2. 자동 구간 (엑셀까지)

```powershell
python "촉매 반응 계산.py" --no-origin
# 또는 gc_automation.env:
DATA_PC_SKIP_ORIGIN=1
```

| 설정 | 의미 |
|------|------|
| `--no-origin` / `DATA_PC_SKIP_ORIGIN=1` | Origin 4단계만 생략 (폴더·xlsx 유지) |
| `--no-archive` | 폴더·Origin 둘 다 생략 — 위탁 기본 아님 |

로그: `[4단계] Origin 건너뜀` → 정상.  
차헌 `Desktop\.cursor\gc_automation.env`, 은규 템플릿에 `=1` 반영. 은규 운영 env는 로컬에서 맞출 것.

**검증 쪼개기 예:** (1) env skip 인식 (2) inbox/profile (3) `--no-origin` 실행.

**짜잘:** 스크립트 끝 `메일 다시 확인 Enter/q` 는 비대화형에서 EOF → exit 1 날 수 있음 (본 작업 실패와 무관할 수 있음).

---

## 3. 구분 규칙 (확인 전에 이미 정해진 것)

### 3-1. 엑셀 열 → 북시트 Long Name

코드: `DEFAULT_ORIGIN_MAPPING` (`o0_mapping.py`)

| 엑셀 | Origin 북 |
|------|-----------|
| C2H6 Conversion (%) | C2H6 conversion |
| CH4 Conversion (%) | CH4 conversion |
| CO2 Conversion (%) | CO2 conversion |
| H2 Yield (%) | H2 yield |
| CO Yield (%) | CO yield |
| CH4 (%) | CH4 |
| C2H4 (%) | C2H4 |
| C2H6 (%) | C2H6 |

엑셀에 없는 열은 그 북은 **스킵**. 숫자는 **그래프가 아니라 북시트**에만.

### 3-2. 반응·장비 → opju / PE

| 구분 | 규칙 |
|------|------|
| 실험 폴더·opju | G: 반응 루트(DRE/DRM/DRME) + 날짜 폴더 |
| 한 opju 안 | PE `{반응}-{장비}` → `DRME-GC3`, `DRE-GC3` … |
| 장비 | 파일명·메일 GC (예 `_GC3_`) |

동명 Long Name(`CO yield`)이라도 **PE 폴더가 다르면 다른 북**. 상세 [`ORIGIN_PE_FOLDER.md`](ORIGIN_PE_FOLDER.md).

---

## 4. Comments — 반드시 사용자 확인

### 4-1. 파일명 ≠ Comments (정상인 경우 많음)

| 원인 | 결과 |
|------|------|
| GC 이름 **~40자 제한** | 파일명 잘림 |
| 파일명 금지 문자 (`:`, `/`, `°` …) | 엑셀 저장 시 치환 |

- 파일명을 Comments에 **기계 복사 금지**
- 매번 **Comments 후보를 제안 → 사용자 OK**
- 틀리면 **사용자가 Comments를 고쳐도 됨**

### 4-2. 기존 열 갱신 vs 새 열

| 경우 | 에이전트 |
|------|----------|
| **기존 열** (Comments에 이미 시료) | 그 Comments·열 번호를 보여 주고 유지/수정 확인 → 숫자만 반영 |
| **새 샘플·새 열** | **바로 왼쪽 열 Comments** 문체 읽기 + 엑셀/메일 파일명 정보 → Comments **제안** → OK 후 기입 |

확인할 세 가지: (1) opju·PE (2) Comments 최종 문구 (3) 기존 열 vs 새 열.

---

## 5. 한 번에 시료 하나

| 규칙 | 내용 |
|------|------|
| Origin 붙이기 | **시료 하나씩** (한 턴에 여러 시료 연속 금지) |
| 메일 | 처리할 메일에 **시료 종류가 둘 이상**이면 목록 요약 후 **어느 시료인지 질문** |
| 동일 시료 구버전만 여러 통 | 최신 1건 규칙은 OK. **다른 시료** 섞이면 질문 |

흐름: 메일 요약 → 「어느 시료?」 → Comments 확인 → 북시트 → (새 열이면) Plot → 저장.

---

## 5-1. 값 수정 · 행 줄이기 (연습·운영 공통)

열을 **깨지 않으려면** 짧은 조각만 `from_list` 하지 않는다.

| 목적 | 방법 |
|------|------|
| **한 행 값 변경** | 열 전체 `to_list` → 해당 인덱스만 수정 → **전체**를 Comments와 함께 `from_list` |
| **앞 N행만 남김** | 열 전체 읽기 → `vals[:N]` → Comments와 함께 `from_list` (뒤 행 삭제) |
| **열 자체 삭제** | `del_col` (문자/인덱스). Plot은 같이 사라지는지 확인·필요 시 Layer에서 제거 |

금지: `[한 값]`만 `from_list` / 짧은 리스트로 덮어쓰기 → **열 절단**.

---

## 6. 북시트 붙이기 체크리스트

1. PE `DRME-GC3` 등만 연다.
2. 매핑된 **북시트**만 (그래프 Long Name에 숫자 넣지 않음).
3. 확인받은 Comments 열 (또는 새 열).
4. 계산완료 xlsx → 해당 지표 열 전체 행 복사/기입.
5. 같은 PE·같은 Long Name 북이 둘이고 행 수 같으면 **양쪽**. 행 수 다르면 멈춤.
6. **Ctrl+S** 저장.

실측 예 (20261115): 기존 CN(col91) Comments 확인 후 6개 북 34→78행 갱신.

---

## 7. 그래프 Plot

### 7-1. 규칙

1. 새 열 → 해당 지표 그래프 Layer에 Plot 추가 (성분마다 그래프가 다름).
2. 시트 Clear만 하면 Plot은 남음 → 정리 시 Object Manager에서 Plot 제거.
3. **Rescale on Apply / 자동 Rescale 금지** — Plot만 추가, **축 유지**.  
   에이전트 보조 시: `add_plot` 직전 `ylim`/`xlim` 저장 → 추가 후 **즉시 복구**. `layer.rescale()` 호출 금지.
4. 축을 바꿀지는 **사용자 의도**일 때만.
5. **색** — §7-4.

### 7-4. Plot 색 (새 시료)

새 열에 Plot을 붙일 때 **색을 지정할 수 있다** (GUI 또는 COM 선 색). 규칙:

| 규칙 | 내용 |
|------|------|
| **같은 시료** | C2H6 / CO2 / H2 / CO / CH4 / C2H4 … **모든 성분 그래프에서 동일 색** |
| **한 그래프 안** | 이미 Plot된 **다른 시료와는 분명히 다른 색** (구분 가능하게) |
| **금지 색** | 발표·화면에 안 보이는 색 — **노란색**, **형광색**, **채도 매우 낮은 색**, **검정**, **흰색** |

절차 권장:

1. 대상 그래프(예: Graph19B)의 기존 Plot 색 목록을 본다.
2. 금지 목록·기존 색을 피한 **후보 1색**을 고른다 (파랑·빨강·초록·보라·주황·청록 등 채도 있는 계열).
3. (선택) 사용자에게 「이 시료는 ○○색으로 통일」확인.
4. **모든 성분 그래프**의 해당 시료 Plot에 **같은 색**을 적용한다.
5. 색을 적용한 뒤 에이전트는 **매번** 사용자에게 말한다:  
   **「이 색으로 두었는데, 바꾸고 싶으면 말해 주세요.」**

에이전트: 색만 바꾸고 Rescale 하지 말 것. 색 변경 안내를 빼먹지 말 것.

### 7-2. DRME-GC3 실습 대응 (AB 북 ↔ 그래프)

| 북 | 그래프 (예) |
|----|-------------|
| COyieldAB | Graph19B (CO yield) |
| H2yieldAB | Graph15B (H2 yield) |
| C2H6conversiB | Graph1B (C2H6 conversion) |
| CO2conversioB | Graph5B (CO2 conversion) |
| CH4AB | Graph26B (CH4 %) |
| C2H4AB | Graph27B (C2H4 %) |

새 Comments 열이 **여러 북 col에 같이** 있으면, Plot도 **성분 그래프마다** 같은 열(예: `CO`)을 붙여야 한다. CO만 하고 끝내면 안 됨.

### 7-3. 멀티 모니터

에이전트 화면 클릭은 **주 모니터만** 본다. Origin이 다른 디스플레이에 있으면 주 모니터로 옮긴 뒤 GUI 실습. (같은 PC — 도구 제한일 뿐.)

---

## 8. 에이전트 동작 요약

| 단계 | 할 일 |
|------|--------|
| 개시·메일 | 시료 종류 여러 개 → **질문**. 하나(또는 지정)만 진행 |
| 자동 | `--no-origin` / env skip. `gc_automation.py`는 장비 PC만 |
| Origin 전 | opju·PE·Comments·기존/새 열 **확인 요청** |
| 새 열 Comments | 왼쪽 Comments + 파일명 → **제안** |
| 북시트 | 확인 후 매핑대로 기입 (일상 COM `update_origin` 끄기) |
| Plot | GUI 우선. 보조 시 **축 복구·Rescale 금지**. 전 성분 그래프·§7-4 색 |
| 색 후 | **「바꾸고 싶으면 말해 주세요」** 필수 안내 |
| 저장 | 사용자 Ctrl+S 안내 |
| 트리거 | 「GC 작업해줘」→ §0-1 전체 체인 |

PC별 개시: 은규 → `eungyu-pc-initiation.mdc` (위탁·시료 질문 포함). GC4 장비는 변경 없음.

---

## 9. 주의사항 체크리스트 (짧게)

- [ ] `DATA_PC_SKIP_ORIGIN=1` (일상)
- [ ] 시료 여러 종류면 물어보기
- [ ] Comments ≠ 파일명 가정; 항상 확인; 사용자 수정 가능
- [ ] 새 열 → 왼쪽 Comments 참고해 제안
- [ ] 엑셀↔북 매핑·PE 반응×장비 준수
- [ ] 북시트만; 그래프에 숫자 직접 넣지 않음
- [ ] Clear ≠ Plot 제거
- [ ] Plot 시 **Rescale 금지**
- [ ] 새 열 Plot은 **모든 해당 성분 그래프**
- [ ] Plot **색**: 시료 통일 / 그래프 안 구분 / 노랑·형광·저채도·검정·흰색 제외
- [ ] 색 적용 후 **「바꾸고 싶으면 말해 주세요」**
- [ ] 「GC 작업해줘」→ §0-1 전체 체인
- [ ] opju 저장
- [ ] (에이전트) Origin GUI는 주 모니터

---

## 10. COM 4단계 재개 시 (나중)

1. `from_list` 절단·`start=` 수정 후  
2. `DATA_PC_SKIP_ORIGIN=0`  
3. Plot은 계속 수동/`Rescale` 주의 권장  

`workflow_bridge` 의 `skip_peer_sync` 인자는 촉매 스크립트와 맞춰 둘 것 (누락 시 TypeError).

---

## 11. 명령 요약

```powershell
python "촉매 반응 계산.py" --no-origin
# env: DATA_PC_SKIP_ORIGIN=1
```
