# Origin PE 폴더 — 반응×장비 + 최신 opju 템플릿

> 확인·수동 정리: 2026-11-18 (차헌 데이터 PC).  
> 관련 규칙: `.cursor/rules/origin-book-not-graph.mdc`

---

## 1. 목표

| 예전 | 지금 |
|------|------|
| 반응마다 opju 계보 (DRE→DRE→DRE) | **메일/최신 기준** 가장 최근 opju를 템플릿으로 복사 |
| A / AB·B 이중 Long Name | PE 폴더를 **`반응-장비`** 로 나눔 (`DRE-GC3`, `DRME-GC3`) |
| 같은 Long Name 북을 전부 갱신 | **해당 PE 폴더 안** 북만 갱신 |

한 `.opju` 안에 DRE·DRME(·DRM) 데이터를 같이 둔다. 실험 폴더(G:)는 여전히 반응별 루트에 만들지만, **파일 내용은 교차 복사**한다.

---

## 2. PE 트리 예시

```
20261115 DRME(1.5) Ni(0.1g-1.5g)-Al2O3.opju
├─ DRME-GC3    ← DRME + GC3 북·그래프
└─ DRE-GC3     ← DRE + GC3 (다른 날짜 실험에서 Append/이관)
```

- 레거시 `Folder1` / A 쪽 북은 정리 대상 (수동 삭제·이관 후).
- 폴더 이름 규칙: `{반응}-{장비}` → `DRE-GC3`, `DRME-GC3`, `DRM-GC2` …

---

## 3. 3단계 — 템플릿 선택

코드: `촉매 반응 계산.py` → `_find_latest_experiment_folder` / `setup_experiment_folder`

1. **전 반응** `REACTION_ROOTS` 아래 opju 있는 실험 폴더를 모은다.
2. 점수: **메일 수신 epoch** (`PEG/inbox/.gc_mail_received.json`) > 폴더명(날짜) > opju mtime.
3. 최고 점수 폴더를 템플릿으로 **복사** → 이번 반응 루트에 새/기존 실험 폴더로 저장.
4. 예: 직전이 DRME인데 이번이 DRE → DRME opju를 DRE 실험 폴더에 복사.  
   로그: `템플릿 반응 교차: DRME → DRE`.

기존 실험 폴더가 이미 있으면 **복사하지 않고** 그 폴더의 opju만 갱신한다 (xlsx 사이클 가드 동일).

---

## 4. 4단계 — 쓰기 범위

코드: `data_pc_origin/o0_pe_folder.py` → `o5_match` / `o5_duplicate_books` / `o8_job`

| 입력 | PE 폴더 |
|------|---------|
| `reaction_type=DRE`, `equipment=GC3` | `DRE-GC3` |
| `source_excel` 파일명 `_GC3_DRME_` | `DRME-GC3` |

- `find_all_worksheets_for_keyword(..., pe_folder=)` — 그 폴더 경로의 북만.
- `row_count_conflict_groups(..., pe_folder=)` — **폴더 안에서만** 행 수 충돌 검사.  
  `DRE-GC3`의 CO yield(80행)와 `DRME-GC3`의 CO yield(34행)는 서로 막지 않음.
- `pe_folder`를 못 정하면(장비 미상) 예전처럼 전체 북을 본다.

---

## 5. 수동으로 폴더 합치기 (GUI)

창 간 PE 드래그는 **안 됨**.

1. 소스에서 폴더 우클릭 → **Save As Project…** (또는 파일 복사본 Append)  
2. 대상 opju에서 **Append Project…** → 새 폴더로 받기  
3. 루트로 옮긴 뒤 이름을 `DRE-GC3` 등으로 변경  
4. LabTalk/COM: `pe_move`, `active_folder().name = "DRE-GC3"`

상세 실습은 2026-11-18 세션 (`20260716` Folder1 → `20261115` 의 `DRE-GC3`).

---

## 6. 관련 파일

| 경로 | 역할 |
|------|------|
| `data_pc_origin/o0_pe_folder.py` | 폴더 라벨·경로 필터 |
| `data_pc_origin/o5_match.py` | pe_folder 필터 매칭 |
| `data_pc_origin/o5_duplicate_books.py` | 폴더 범위 행 수 게이트 |
| `촉매 반응 계산.py` | 교차 템플릿 복사 · `update_origin(..., reaction/equipment)` |
| `.cursor/rules/origin-book-not-graph.mdc` | 북시트만 쓰기 · 레거시 A/AB 참고 |
