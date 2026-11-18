# Origin — 엑셀까지 자동, Origin은 GUI 위탁

> 잠정 운영 방침 (2026-11-19, 차헌 데이터 PC 실증 후).  
> 코드 기본값을 바꾸기 전에 **이 가이드대로** 돌린다.

관련: [`ORIGIN_PE_FOLDER.md`](ORIGIN_PE_FOLDER.md) · [`.cursor/rules/origin-book-not-graph.mdc`](../.cursor/rules/origin-book-not-graph.mdc) · [`DATA_PC_ORIGIN_SAVE.md`](DATA_PC_ORIGIN_SAVE.md)

---

## 1. 한 줄 방침

| 구간 | 담당 |
|------|------|
| 메일 → 계산 → 엑셀 → 연구노트/G: 실험 폴더(xlsx·opju 템플릿 복사) | **`.py` 자동** |
| Origin 북시트에 숫자·Comments 넣기 | **GUI** (복사·붙여넣기) |
| 그래프에 곡선(Plot) 추가·정리 | **GUI** (원래도 코드가 Plot을 안 만듦) |

**4단계 Origin COM 쓰기(`update_origin`)는 당분간 쓰지 않는다.**

---

## 2. 왜 이렇게 나누나

COM으로 북시트에 쓸 때와 GUI로 다룰 때 차이가 컸다 (2026-11-19 `COyieldAB` / `Graph19B` 실측).

| 현상 | 의미 |
|------|------|
| 짧은 `from_list` | 열 뒤쪽이 **잘릴** 수 있음 |
| `start=` 행 번호 | 주석(1-based)과 실제 동작이 어긋날 수 있음 |
| 시트에서 숫자만 지움 | 그래프 **Plot은 그대로** 남음 |
| 열 자체를 삭제 | 그 열 Plot은 같이 사라짐 (COM `del_col`) |
| Y축·잘못된 열(CM vs CN) | “그래프가 안 바뀐다”처럼 보이기 쉬움 |

사람이 GUI로 붙이고, 곡선도 GUI로 관리하는 편이 지금 단계에선 안전하다.

---

## 3. 자동 구간 — 어떻게 실행

Origin만 건너뛰고, 메일·계산·엑셀·실험 폴더(xlsx)까지 돌린다.

```powershell
# 한 번 실행 (차헌: Desktop\.cursor 또는 repo data_pc)
python "촉매 반응 계산.py" --no-origin

# 또는 env (supervisor / 상시 watch 에도 적용)
# gc_automation.env 에:
DATA_PC_SKIP_ORIGIN=1
```

| 플래그·env | 하는 일 |
|------------|---------|
| `--no-origin` / `DATA_PC_SKIP_ORIGIN=1` | **4단계 Origin만** 생략. G:·연구노트 폴더·xlsx는 유지 |
| `--no-archive` | G: 폴더·Origin **둘 다** 생략 (계산·엑셀만). 이번 위탁 방침의 기본은 아님 |

로그에 `[4단계] Origin 건너뜀` 이 보이면 정상.

은규 PC: `gc-data-pc\촉매 반응 계산.py` 동일.  
차헌 PC 로컬 env·은규 템플릿에는 **이미 `DATA_PC_SKIP_ORIGIN=1`** 반영 (2026-11-19). 은규 운영 `gc-data-pc\gc_automation.env` 는 이식/수동으로 맞출 것.

---

## 4. GUI 구간 — 체크리스트

자동이 끝난 뒤 실험 폴더의 **계산 완료 xlsx**와 **opju**를 연다.

### 4-0. Comments ≠ 엑셀 파일명 (반드시 확인)

엑셀/메일 파일명과 Origin **Comments** 문자열이 **항상 같지는 않다.**

| 이유 | 결과 |
|------|------|
| GC 쪽 이름 **약 40글자 제한** | 파일명이 짧거나 잘림 |
| Windows 파일명에 못 쓰는 문자 (`:`, `/`, `°` 등) | 엑셀 저장 시 치환·생략 |

그래서 GUI(또는 에이전트)는 **매번 Comments 후보를 사용자에게 확인**받은 뒤 진행한다.  
Comments가 잘못 지어졌으면 **사용자가 Comments 문구를 고칠 수 있다** — 엑셀 파일명을 Comments에 기계적으로 복사하지 말 것.

확인할 것: (1) opju·PE (2) **Comments 최종 문구** (3) 기존 열 갱신 vs 새 열.

**새 샘플 → 새 열**일 때 에이전트:

1. 붙일 위치의 **바로 왼쪽 열 Comments**를 읽는다 (문체·접미사·CVD 표기 관례).
2. 이번 **엑셀/메일 파일명**으로 날짜·반응·농도·촉매 정보를 파악한다 (40자·특수문자로 잘린 이름일 수 있음).
3. 왼쪽 관례 + 파일명 정보를 합쳐 **이번 Comments 문구를 제안**하고, 사용자 확인 후에만 기입한다.  
   기존 열 갱신이면 그 열 Comments를 보여 주고 유지·수정 여부를 묻는다.

### 4-1. 북시트에 붙이기

1. PE에서 반응×장비 폴더만 연다 (`DRME-GC3`, `DRE-GC3` …). → [`ORIGIN_PE_FOLDER.md`](ORIGIN_PE_FOLDER.md)
2. **워크북(북시트)** 만 고친다. 그래프 창 Long Name에 숫자를 넣지 않는다.
3. Comments가 **확인받은 시료명**인 열을 찾거나, 맨 뒤에 새 열을 만든다.
4. xlsx의 해당 지표 열(CO Yield, H2 Yield …)을 복사해 북시트에 붙여넣는다.
5. 같은 Long Name 북이 **같은 PE 폴더 안에** 둘 있으면(행 수 같을 때) **양쪽**에 같은 값을 넣는다. 행 수가 다르면 임의로 한쪽만 고르지 말고 멈춘다.

### 4-2. 그래프

1. 시트를 고쳤다고 곡선이 자동으로 생기지는 않을 수 있다. 새 열이면 Layer에 **Plot 추가**를 GUI로 한다.
2. “최근 시료만 보고 싶다” → 시트에서 열을 비우기만 하면 **Plot 목록은 남는다**.  
   Object Manager / Layer Contents에서 **해당 Plot을 제거**해야 그래프도 깔끔해진다.
3. 세로축 범위에 새 값이 안 보이면 Rescale 또는 Y 최대값을 조정한다.

### 4-3. 저장

- opju는 **Ctrl+S** 로 저장한 뒤 닫는다.
- 파이프라인이 Origin을 건드리지 않으므로, 미저장 상태로 두면 다음 자동 실행이 파일을 덮어쓰지 않는다 (템플릿 복사는 기존 폴더가 있으면 건너뜀).

---

## 5. 에이전트·일상 개시와의 관계

| PC | 「진행」「시작」 등 | 이 방침에서 |
|----|-------------------|-------------|
| 은규 / 차헌 데이터 PC | `촉매 반응 계산.py` | `DATA_PC_SKIP_ORIGIN=1` 이면 엑셀·폴더까지, Origin은 사람 |
| GC4 장비 PC | `gc_automation.py` | **변경 없음** (PDF→엑셀→메일) |

에이전트는 Origin COM으로 열을 쓰지 말고, 자동 구간 결과(xlsx 경로)만 안내한 뒤 GUI 체크리스트(§4)를 따르면 된다.

---

## 6. 나중에 코드로 되돌릴 때

다시 COM 4단계를 켜려면:

1. `DATA_PC_SKIP_ORIGIN` 제거 / `--no-origin` 없이 실행  
2. `from_list` 절단·`start=` 보정을 코드에서 먼저 고친 뒤  
3. Plot은 계속 수동(현행 주석과 동일)으로 두는 것을 권장  

이 문서는 그전까지의 **운영 가이드**이다. 코드 기본값 변경 여부는 별도 작업.

---

## 7. 관련 명령 요약

```powershell
# 위탁 모드 (권장)
python "촉매 반응 계산.py" --no-origin

# 계산·엑셀만 (폴더 복사도 안 함)
python "촉매 반응 계산.py" --no-archive

# env
set DATA_PC_SKIP_ORIGIN=1
```
