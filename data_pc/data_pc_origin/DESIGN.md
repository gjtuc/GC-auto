# data_pc_origin — 전체 설계 (극세분)

> 파이프라인(`촉매 반응 계산.py`)과 **완전 분리**.  
> 규칙: **마이크로 단계 구현 → 해당 verify PASS → 주석/LAYER_STATUS 갱신 → 사용자 승인 → 다음 마이크로만.**

| 단계 | 문서 |
|------|------|
| L0~L2 | 본 문서 |
| L4 나노 (~320) | [`DESIGN_ATOMIC.md`](DESIGN_ATOMIC.md) |
| L5/L6 (~900/450) | [`DESIGN_NANO.md`](DESIGN_NANO.md) |
| L7/L8 (~2400/1200) | [`DESIGN_LEPTON.md`](DESIGN_LEPTON.md) |
| 리프 카탈로그 | [`design/catalog/_INDEX.md`](design/catalog/_INDEX.md) |

현재: **O0 합본 PASS** (`--o0`) · L4 리프별 `--gate` 분리는 **미구현** · O1~O9 LOCKED

---

## 의존 규칙

```
O0.* → (originpro 없음)
O1.* → O0.* 만 참조 가능
O2.* → O1.* + O0.*
O3.* → O2.* (게이트 통과 후) + O0.*
...
O9.* → O8.* 만 (파이프라인 훅)
```

**상위 ID 코드는 하위 ID 미통과 시 import 금지** (`verify.py`가 강제).

---

## 패키지 트리 (목표)

```
data_pc_origin/
  DESIGN.md              ← 본 문서
  LAYER_STATUS.md        ← 마이크로 PASS 표
  verify.py              ← --o0-1, --o0-2, … --o9

  # O0 — Pure (originpro 금지)
  o0_keys.py
  o0_identity.py
  o0_comments.py
  o0_series.py
  o0_mapping.py
  o0_types.py            ← IdentityKey, OriginPath, … TypedDict/NamedTuple

  # O1 — Probes (읽기만, 부작용 없음)
  o1_opju_path.py
  o1_opju_writable.py
  o1_origin_install.py
  o1_origin_process.py
  o1_probes.py           ← aggregate

  # O2 — Gate + Lock
  o2_env.py              ← SKIP_ORIGIN, ENABLED
  o2_pipeline_lock.py    ← data_pc_runtime 락 상태 **조회만**
  o2_origin_lock.py      ← .origin_update.lock (플러그인)
  o2_gates.py
  o2_verdict.py

  # O3 — Session (originpro 수명)
  o3_import.py
  o3_show.py
  o3_exit.py
  o3_session.py          ← context manager
  o3_plugins/
    __init__.py
    dialog_readonly.py   ← 기본 OFF
    retry_open.py        ← 기본 OFF

  # O4 — Project (.opju)
  o4_path_validate.py
  o4_open.py
  o4_save.py
  o4_save_as.py
  o4_project.py          ← open/save 조합

  # O5 — Page / Worksheet 탐색
  o5_iter_pages.py
  o5_worksheet_text.py
  o5_match_keyword.py
  o5_resolve_mapping.py

  # O6 — Column 계획 (originpro wks 객체 조작)
  o6_scan_comments.py
  o6_find_exact.py
  o6_find_identity.py
  o6_plan_insert.py
  o6_insert_lt.py        ← LT_execute
  o6_column.py           ← resolve_target_column

  # O7 — Write
  o7_prepare_list.py     ← O0 column_to_origin_list 래핑
  o7_from_list.py
  o7_write_one.py
  o7_write_mapping.py

  # O8 — Sample Job
  o8_context.py
  o8_job.py
  o8_result.py

  # O9 — Facade
  o9_facade.py
  o9_result.py

  tests/
    test_o0_*.py
    test_o1_*.py
    ...
```

---

## O0 — Pure (이미 구현됨, verify 세분화)

| ID | 모듈·함수 | 한 줄 책임 | verify |
|----|-----------|------------|--------|
| **O0-T** | `o0_types.py` | `IdentityKey`, `GapPolicy` 타입 정의 | `--o0-t` |
| **O0-K** | `o0_keys.normalize_origin_key` | 공백 제거·소문자 | `--o0-k` |
| **O0-I** | `o0_identity.identity_match_tokens` | 시료 토큰 집합 | `--o0-i` |
| **O0-C1** | `parse_comment_date` | Comments → YYYYMMDD | `--o0-c` |
| **O0-C2** | `comment_matches_identity` | 재전송 열 매칭 | `--o0-c` |
| **O0-S1** | `GapPolicy.AS_EMPTY` | NaN→`''`, 길이 유지 | `--o0-s` |
| **O0-S2** | `GapPolicy.AS_NAN` | NaN 유지 | `--o0-s` |
| **O0-S3** | `GapPolicy.SKIP_ROWS` | NaN 행 제거(비권장) | `--o0-s` |
| **O0-M1** | `DEFAULT_ORIGIN_MAPPING` | 8열 매핑 상수 | `--o0-m` |
| **O0-M2** | `validate_mapping` | 빈 키·중복 키워드 거부 | `--o0-m` |
| **O0** | 전체 | `verify --o0` = O0-* 전부 | `--o0` ✅ PASS |

---

## O1 — Probes (읽기만)

| ID | 함수 | 입력 | 출력 | verify |
|----|------|------|------|--------|
| **O1-P1** | `probe_opju_exists(path)` | str | `ProbeResult(ok, detail)` | `--o1-p1 --path …` |
| **O1-P2** | `probe_opju_extension(path)` | str | `.opju` 여부 | `--o1-p1` |
| **O1-P3** | `probe_opju_on_g_drive(path)` | str | G: 루트 접근 | `--o1-p1 --live` |
| **O1-P4** | `probe_opju_writable(path)` | str | 읽기전용·잠금 | `--o1-p4 --live` |
| **O1-I1** | `probe_originpro_importable()` | — | import 성공 | `--o1-i1` |
| **O1-I2** | `probe_origin_exe_running()` | — | Origin64.exe PID (정보) | `--o1-i2` |
| **O1** | `run_all_probes(path)` | path | `ProbesReport` | `--o1 --live` |

**O1 통과 조건:** `--o1` 단위 테스트(mock path) + `--o1 --live` 실제 G: `.opju` 1개.

---

## O2 — Gate + Lock

| ID | 함수 | 조건 | verify |
|----|------|------|--------|
| **O2-E1** | `read_skip_origin_env()` | `DATA_PC_SKIP_ORIGIN` | `--o2-e` |
| **O2-E2** | `origin_enabled()` | skip 아니면 True | `--o2-e` |
| **O2-L1** | `pipeline_lock_busy()` | runtime 락 **조회** | `--o2-l1` |
| **O2-L2** | `OriginLock.try_acquire` | `.origin_update.lock` (옵션) | `--o2-l2` |
| **O2-G1** | `Gate: skip_origin` | 즉시 SKIP | `--o2-g` |
| **O2-G2** | `Gate: probes_fail` | O1 실패 시 WAIT | `--o2-g` |
| **O2-G3** | `Gate: pipeline_busy` | 파이프라인 락 | `--o2-g` |
| **O2-G4** | `Gate: READY` | O3 진입 허용 | `--o2-g` |
| **O2** | `GateEvaluator.evaluate` | `GateVerdict` | `--o2` |

---

## O3 — Session (originpro 수명)

| ID | 단계 | 코드 | verify |
|----|------|------|--------|
| **O3-S1** | lazy import | `import_originpro()` | `--o3-s1` |
| **O3-S2** | hide UI | `set_show(False)` | `--o3-s2 --dry` |
| **O3-S3** | enter | `OriginSession.__enter__` | `--o3-s3 --dry` |
| **O3-S4** | exit | `OriginSession.__exit__` → `op.exit()` | `--o3-s3 --dry` |
| **O3-S5** | finally 보장 | 예외 시에도 exit | `--o3-s5` (mock 예외) |
| **O3-P1** | plugin slot | `session.plugins[]` | `--o3-p1` |
| **O3-P2** | `DialogReadonlyPlugin` | 기본 **비활성** | `--o3-p2 --live` (옵션) |
| **O3** | full session | enter→exit 1회 | `--o3 --dry-session` |

---

## O4 — Project (.opju)

| ID | 함수 | verify |
|----|------|--------|
| **O4-V1** | `validate_opju_path(path)` — O1 위임 | `--o4-v1` |
| **O4-O1** | `open_project(session, path)` | `--o4-o1 --live-open-only` |
| **O4-O2** | `open_project_readonly(path)` | `--o4-o2` (미사용 기본) |
| **O4-S1** | `save_project(session, path)` | `--o4-s1 --live` (테스트 opju) |
| **O4-S2** | `save_project_as(session, new_path)` | `--o4-s2` |
| **O4** | open → save → close | `--o4 --live-roundtrip` |

---

## O5 — Worksheet 탐색 (**105 core L4**, registry 117)

| ID | 함수 | L4 | verify |
|----|------|-----|--------|
| **O5-I** | `iter_pages_w` / `iter_worksheets` | 24 | `--rollup O5-L1-I` |
| **O5-T** | name helpers + `compose_search_text` | 27 | `--rollup O5-L1-T` |
| **O5-M** | match / find / resolve / report | 54 | `--rollup O5-L1-M` |
| **O5** | core 합본 | 105 | `--rollup O5` |

마스터: [`design/catalog/O5-REGISTRY.md`](design/catalog/O5-REGISTRY.md)

---

## O6 — Column 계획·삽입

| ID | 함수 | verify |
|----|------|--------|
| **O6-S1** | `scan_dated_columns(wks)` — Comments 날짜 | `--o6-s1 --live` |
| **O6-F1** | `find_column_exact_comment(wks, name)` | `--o6-f1` |
| **O6-F2** | `find_column_by_identity(wks, key)` — O0-C2 | `--o6-f2` |
| **O6-P1** | `plan_insert_index(dated, new_date)` | `--o6-p1` (순수) |
| **O6-P2** | `needs_insert(wks, insert_at)` | `--o6-p2` |
| **O6-I1** | `insert_column_before(wks, col_idx)` — LT_execute | `--o6-i1 --live` |
| **O6-R1** | `resolve_target_column(wks, sample, identity)` | `--o6-r1 --live` |
| **O6** | 시료 1개 열 위치 결정 | `--o6 --live` |

---

## O7 — Write

| ID | 함수 | verify |
|----|------|--------|
| **O7-P1** | `prepare_column_values(series, GapPolicy)` — O0-S | `--o7-p1` |
| **O7-W1** | `write_column(wks, col, values, comments)` | `--o7-w1 --live-one-col` |
| **O7-W2** | `write_h2_only` (스모크) | `--o7-w2 --live` |
| **O7-W3** | `write_full_mapping(wks, col, df, mapping)` | `--o7-w3 --live` |
| **O7-G1** | 갭 행(99~100) AS_EMPTY 확인 | `--o7-g1 --live` |
| **O7** | mapping 8열 1시료 | `--o7 --live` |

---

## O8 — Sample Job (메일 1건 = Job 1회)

| ID | 구조 | verify |
|----|------|--------|
| **O8-C1** | `SampleContext` dataclass | `--o8-c1` |
| **O8-C2** | `build_context(opju, df, sample, identity)` | `--o8-c2` |
| **O8-J1** | 루프: mapping → O5 → O6 → O7 | `--o8-j1 --dry` |
| **O8-J2** | `updated_sheet_count`, `row_count` | `--o8-j2` |
| **O8-J3** | `save_in_place` / `save_as` 분기 | `--o8-j3` |
| **O8-J4** | 경고·부분 실패 수집 | `--o8-j4` |
| **O8** | 실제 opju 1시료 전체 | `--o8 --live-job` |

---

## O9 — Facade (파이프라인 유일 진입)

| ID | API | verify |
|----|-----|--------|
| **O9-F1** | `update_from_dataframe(...)` | `--o9-f1 --live` |
| **O9-F2** | `OriginUpdateResult` (ok, sheets, warnings) | `--o9-f2` |
| **O9-F3** | 실패 시 originpro exit 보장 | `--o9-f3` |
| **O9** | E2E: xlsx → opju (촉매와 동일 입력) | `--o9 --live-e2e` |

**파이프라인 연결 (O9 PASS + 사용자 승인 후 1줄):**

```python
from data_pc_origin import update_from_dataframe
update_from_dataframe(target_opju, df_final, sample_name, identity_key=...)
```

---

## verify CLI (목표)

```bash
# 마이크로 (하나씩)
python -m data_pc_origin.verify --o0-k
python -m data_pc_origin.verify --o1-p1 --live --opju "G:\...\file.opju"

# 층 합본 (하위 마이크로 전부 PASS 후에만 의미)
python -m data_pc_origin.verify --o0      # ✅ 현재
python -m data_pc_origin.verify --o1 --live
...
python -m data_pc_origin.verify --all --live-e2e   # 최종 (O9 이후)
```

**잠금:** `--o1` 스크립트는 `LAYER_STATUS`에서 O0≠PASS면 exit 1 + "LOCKED".

---

## 파이프라인 통합 타임라인

| 단계 | env | 파이프라인 |
|------|-----|------------|
| 지금 | `SKIP_ORIGIN=1` | 메일·엑셀·G: |
| O0~O2 PASS | `SKIP_ORIGIN=1` | 변경 없음 |
| O3~O4 PASS | `SKIP_ORIGIN=1` | Origin 열기만 수동 verify |
| O5~O7 PASS | `SKIP_ORIGIN=1` | 한 열 live write |
| O8 PASS | `SKIP_ORIGIN=0` **시험 1건** | 승인 후 |
| O9 PASS | `SKIP_ORIGIN=0` | `update_origin` → facade 교체 |

---

## O0 추가 세분 (다음 구현 후보)

현재 `verify --o0`는 한 번에 13테스트. 아래처럼 **파일·테스트 분리** 예정:

| 파일 | 테스트 파일 |
|------|-------------|
| `tests/test_o0_keys.py` | O0-K |
| `tests/test_o0_identity.py` | O0-I |
| `tests/test_o0_comments.py` | O0-C |
| `tests/test_o0_series.py` | O0-S |
| `tests/test_o0_mapping.py` | O0-M |

→ `verify --o0-k` 실패 시 `--o0-c` 실행 자체를 막는 **마이크로 잠금**.

---

## 요약

- **10개 대층 (O0~O9)** × **층당 5~10 마이크로** ≈ **70+ 검증 게이트**
- 각 게이트: 구현 → verify → LAYER_STATUS → **사용자 승인** → 다음만
- Origin 락·Read-Only 자동 Yes는 **O2-L2 / O3-P2 플러그인** (기본 OFF)
- 갭 NaN 정책은 **O0-S**에서 확정 → **O7**만 사용 (한 곳에서만 결정)

다음 작업 후보 (승인 필요):
1. O0 마이크로 verify 분리 (`--o0-k` …) — O0 리팩터만
2. O1-P1부터 구현
