# data_pc_origin — 원자(Atomic) 설계 트리

> **4단계 분해:** L0 도메인 → L1 모듈 → L2 함수 → L3 스텝 → L4 나노(단일 불변식·단일 테스트)  
> 규칙: **리프(L4) PASS → 부모(L3) PASS → … → L0 PASS**. 형제 노드는 선행 형제 PASS 후에만 구현.  
> 상위: `DESIGN.md` · L5/L6: `DESIGN_NANO.md` · L7/L8: `DESIGN_LEPTON.md` · 리프: `design/catalog/` · 상태: `LAYER_STATUS.md`

---

## ID 규칙

```
O{L0}-{L1}-{L2}-{L3}-{L4}
예: O0-K-01-a-1
    │  │  │  │ └─ 나노: assert 1개
    │  │  │  └── 스텝: 함수 내부 1동작
    │  │  └───── 함수 1개
    │  └──────── 모듈 그룹 (K=keys, …)
    └─────────── 대층 O0~O9
```

**verify:** `python -m data_pc_origin.verify --gate O0-K-01-a-1`  
**잠금:** 부모 미PASS → 자식 `--gate` 실행 시 exit 2 `LOCKED`

---

## L0 = O0 — Pure（originpro import 금지）

### L1 = O0-T — Types

| L2 | L3 | L4 (나노·테스트 1개) | verify gate |
|----|-----|----------------------|-------------|
| **O0-T-01** `IdentityKey` | a | `tuple[str,str]` 2원소 | O0-T-01-a-1 |
| | b | date 8자리 숫자 str | O0-T-01-b-1 |
| **O0-T-02** `GapPolicy` | a | Enum 3값 존재 | O0-T-02-a-1 |
| | b | `str` Enum 상속 | O0-T-02-b-1 |
| **O0-T-03** `ProbeResult` | a | `ok: bool`, `detail: str` | O0-T-03-a-1 |
| **O0-T-04** `OriginPath` | a | `NewType(str)` 또는 alias | O0-T-04-a-1 |

### L1 = O0-K — Keys

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O0-K-01** `normalize_origin_key` | a | `None` → `""` | O0-K-01-a-1 |
| | b | `""` → `""` | O0-K-01-b-1 |
| | c | 공백만 → `""` | O0-K-01-c-1 |
| | d | `"H2 yield"` → `"h2yield"` | O0-K-01-d-1 |
| | e | `"  CO2 conversion "` → `"co2conversion"` | O0-K-01-e-1 |
| | f | 대문자 유지 안 함 (전부 lower) | O0-K-01-f-1 |
| | g | 탭·연속공백 제거 | O0-K-01-g-1 |
| **O0-K-02** `keys_match` | a | norm(a)==norm(b) → True | O0-K-02-a-1 |
| | b | 부분문자열 `in` 판정 헬퍼 | O0-K-02-b-1 |

### L1 = O0-I — Identity tokens

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O0-I-01** `identity_match_tokens` | a | 빈 str → 빈 set | O0-I-01-a-1 |
| | b | `dre` 토큰 추출 | O0-I-01-b-1 |
| | c | `drme` 토큰 추출 | O0-I-01-c-1 |
| | d | `@600` 온도 토큰 | O0-I-01-d-1 |
| | e | `ni5` 촉매 토큰 | O0-I-01-e-1 |
| | f | 1글자 토큰 제외 (규칙) | O0-I-01-f-1 |
| | g | `0.15g` 끝 g 허용 | O0-I-01-g-1 |
| **O0-I-02** `token_match_score` | a | matched/total 비율 | O0-I-02-a-1 |
| | b | threshold `max(2, 0.6*n)` | O0-I-02-b-1 |

### L1 = O0-C — Comments

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O0-C-01** `parse_comment_date` | a | `None` → None | O0-C-01-a-1 |
| | b | 선두 8숫자 추출 | O0-C-01-b-1 |
| | c | 중간 8숫자 무시 (선두만) | O0-C-01-c-1 |
| | d | 7자리 → None | O0-C-01-d-1 |
| | e | 공백 trim 후 매칭 | O0-C-01-e-1 |
| **O0-C-02** `comment_matches_identity` | a | comment None → False | O0-C-02-a-1 |
| | b | key None → False | O0-C-02-b-1 |
| | c | date 불일치 → False | O0-C-02-c-1 |
| | d | date 일치+토큰 충분 → True | O0-C-02-d-1 |
| | e | case insensitive | O0-C-02-e-1 |
| **O0-C-03** `sort_key_from_comment` | a | date 없으면 맨 뒤 정렬키 | O0-C-03-a-1 |

### L1 = O0-S — Series / Gap

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O0-S-01** `_is_missing` | a | None → True | O0-S-01-a-1 |
| | b | `float('nan')` → True | O0-S-01-b-1 |
| | c | `0.0` → False | O0-S-01-c-1 |
| | d | `""` → False (missing 아님) | O0-S-01-d-1 |
| **O0-S-02** `AS_EMPTY` | a | len 유지 | O0-S-02-a-1 |
| | b | NaN → `""` | O0-S-02-b-1 |
| | c | 정상값 유지 | O0-S-02-c-1 |
| **O0-S-03** `AS_NAN` | a | len 유지 | O0-S-03-a-1 |
| | b | `math.isnan` True | O0-S-03-b-1 |
| **O0-S-04** `SKIP_ROWS` | a | len 감소 | O0-S-04-a-1 |
| | b | 갭만 제거 | O0-S-04-b-1 |
| **O0-S-05** `column_to_origin_list` | a | list 입력 | O0-S-05-a-1 |
| | b | pandas Series `.tolist()` | O0-S-05-b-1 |
| | c | 빈 iterable → `[]` | O0-S-05-c-1 |
| **O0-S-06** 갭 시나리오 | a | Cycle99~100 AS_EMPTY 107행 | O0-S-06-a-1 |
| | b | AS_EMPTY 시 index 99,100 `""` | O0-S-06-b-1 |

### L1 = O0-M — Mapping

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O0-M-01** `DEFAULT_ORIGIN_MAPPING` | a | len == 8 | O0-M-01-a-1 |
| | b | `H2 Yield (%)` 키 존재 | O0-M-01-b-1 |
| | c | DRM `CH4 Conversion` 키 존재 | O0-M-01-c-1 |
| **O0-M-02** `validate_mapping` | a | 빈 dict 거부 | O0-M-02-a-1 |
| | b | 빈 df_col 거부 | O0-M-02-b-1 |
| | c | 빈 origin_kw 거부 | O0-M-02-c-1 |
| | d | 정규화 후 중복 kw 거부 | O0-M-02-d-1 |
| | e | 성공 시 복사본 반환 (mutate 안 함) | O0-M-02-e-1 |
| **O0-M-03** `mapping_for_df` | a | df에 없는 열 스킵 목록 | O0-M-03-a-1 |
| | b | 있는 열만 subset | O0-M-03-b-1 |

### O0 합본 게이트

| ID | 조건 |
|----|------|
| **O0-L1-K** | O0-K-* 전부 PASS |
| **O0-L1-I** | O0-I-* 전부 PASS |
| **O0-L1-C** | O0-C-* 전부 PASS |
| **O0-L1-S** | O0-S-* 전부 PASS |
| **O0-L1-M** | O0-M-* 전부 PASS |
| **O0** | O0-L1-* 전부 PASS → ✅ (현재 `--o0` 합본) |

---

## L0 = O1 — Probes（읽기만）

### L1 = O1-P — Opju path

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O1-P-01** `path_is_nonempty` | a | `""` → fail | O1-P-01-a-1 |
| **O1-P-02** `path_exists` | a | 없는 파일 → fail | O1-P-02-a-1 |
| **O1-P-03** `path_is_file` | a | 디렉터리 → fail | O1-P-03-a-1 |
| **O1-P-04** `path_suffix_opju` | a | `.opju` 대소문자 | O1-P-04-a-1 |
| **O1-P-05** `path_on_g_drive` | a | `G:` 시작 | O1-P-05-a-1 |
| **O1-P-06** `g_drive_root_accessible` | a | EXPERIMENT_DATA_ROOT isdir | O1-P-06-a-1 |
| **O1-P-07** `probe_opju_path` | a | aggregate OK | O1-P-07-a-1 |
| | b | aggregate 첫 실패 detail | O1-P-07-b-1 |

### L1 = O1-W — Writable

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O1-W-01** `file_readable` | a | os.access R_OK | O1-W-01-a-1 |
| **O1-W-02** `file_writable` | a | os.access W_OK | O1-W-02-a-1 |
| **O1-W-03** `not_readonly_attr` | a | win32 ATTR_READONLY | O1-W-03-a-1 |
| **O1-W-04** `probe_opju_writable` | a | 합본 | O1-W-04-a-1 |

### L1 = O1-I — Origin install

| L2 | L3 | L4 | verify |
|----|-----|-----|--------|
| **O1-I-01** `try_import_originpro` | a | ImportError → ok=False | O1-I-01-a-1 |
| | b | 성공 시 module ref | O1-I-01-b-1 |
| **O1-I-02** `origin_exe_running` | a | tasklist Origin64 | O1-I-02-a-1 |
| | b | 없어도 probe ok (정보) | O1-I-02-b-1 |
| **O1-I-03** `probe_origin_install` | a | 합본 | O1-I-03-a-1 |

### O1 합본

| ID | 조건 |
|----|------|
| **O1-P** | O1-P-* PASS |
| **O1-W** | O1-W-* PASS |
| **O1-I** | O1-I-* PASS |
| **O1** | O1-P+W+I + `--live` 1파일 |

---

## L0 = O2 — Gate

### L1 = O2-E — Env

| L2 | L3 | L4 |
|----|-----|-----|
| **O2-E-01** `read_env_raw` | a | unset → `""` |
| | b | strip lower |
| **O2-E-02** `parse_bool_env` | a | `1,true,yes,on` |
| | b | else False |
| **O2-E-03** `skip_origin_active` | a | DATA_PC_SKIP_ORIGIN |
| **O2-E-04** `origin_feature_enabled` | a | not skip |

### L1 = O2-L — Lock (조회·옵션 획득)

| L2 | L3 | L4 |
|----|-----|-----|
| **O2-L-01** `read_pipeline_lock` | a | runtime lock path exists |
| | b | pid parse |
| | c | pid alive |
| **O2-L-02** `pipeline_busy` | a | lock+alive → busy |
| **O2-L-03** `origin_lock_path` | a | KCH/.origin_update.lock |
| **O2-L-04** `origin_lock_acquire` | a | O_EXCL |
| | b | stale pid unlink |
| | c | timeout |
| **O2-L-05** `origin_lock_release` | a | unlink in finally |

### L1 = O2-G — Gate chain

| L2 | 순서 | L4 |
|----|------|-----|
| **O2-G-01** | skip_origin → SKIP | verdict.code=skip_origin |
| **O2-G-02** | probes_fail → WAIT | detail에 probe |
| **O2-G-03** | pipeline_busy → WAIT | |
| **O2-G-04** | origin_lock_fail → WAIT | |
| **O2-G-05** | READY → RUN | |
| **O2-G-06** | `GateVerdict` frozen dataclass | |

---

## L0 = O3 — Session

### L1 = O3-S — Session core

| L2 | L3 | L4 |
|----|-----|-----|
| **O3-S-01** `import_originpro` | a | singleton cache |
| | b | ImportError propagate |
| **O3-S-02** `set_show_false` | a | op.set_show(False) |
| **O3-S-03** `session_enter` | a | oext False→True |
| **O3-S-04** `session_exit` | a | op.exit() |
| | b | oext False after |
| **O3-S-05** `exit_on_exception` | a | raise 후에도 exit |
| **O3-S-06** `OriginSession` CM | a | with 블록 |

### L1 = O3-P — Plugins（기본 빈 리스트）

| L2 | L3 | L4 |
|----|-----|-----|
| **O3-P-01** `PluginProtocol` | a | on_open_start/end |
| **O3-P-02** `PluginRegistry` | a | register/unregister |
| **O3-P-03** `DialogReadonlyPlugin` | a | 기본 미등록 |
| **O3-P-04** `RetryOpenPlugin` | a | max_retries=0 기본 |

---

## L0 = O4 — Project

| L2 | L3 (스텝) | L4 |
|----|-----------|-----|
| **O4-V-01** delegate O1-P-07 | a | |
| **O4-O-01** `open(path)` | a | asksave 미사용 |
| | b | return bool |
| | c | fail → OriginOpenError |
| **O4-O-02** `open_retry` | a | 1회 (플러그인) |
| **O4-S-01** `save(same path)` | a | |
| **O4-S-02** `save_as(new)` | a | |
| **O4-R-01** roundtrip | a | open→save→exit |

---

## L0 = O5 — Worksheet find (**105 core L4** + 5 DEBUG + 3 E2E + 4 R)

> **마스터 순서:** [`design/catalog/O5-REGISTRY.md`](design/catalog/O5-REGISTRY.md) (117 gate IDs)

| L1 | L2 | L4 수 | L3 스텝 요약 |
|----|-----|-------|-------------|
| **I** | I-01 iter_pages_w | 12 | attr→callable→'w'→1call→lazy→empty→spy… |
| | I-02 iter_worksheets | 12 | tuple→identity→ORD→8wks→count |
| **T** | T-01 book_name | 5 | str/None/empty/raw |
| | T-02 book_lname | 5 | str/empty/None/unicode |
| | T-03 wks_name | 5 | golden names |
| | T-04 compose | 12 | 3×CALL→f-string→촉매 L1709→golden |
| **M** | M-01 keyword_in_text | 14 | guard→2×norm→in→FX C1–C5→delegate |
| | M-02 find_first | 14 | iter→compose→match→break×2→spy |
| | M-03 resolve | 18 | mapping loop→df skip→hits/misses→symptom |
| | M-04 report_missing | 8 | WKS_MISS→aggregate |
| DBG | DEBUG | 5 | search/norm/hit/miss log |
| E2E | E2E mock | 3 | 8/8 · 0/8 · partial |
| R | rollup smoke | 4 | L1-I/T/M + O5 AND |

카탈로그: `O5-REGISTRY.md` · `O5-I/T/M.md` · `gates/O5/*.yaml` · `FX-O5-opju-mock.yaml`

---

## L0 = O6 — Column

| L2 | L3 | L4 |
|----|-----|-----|
| **O6-S-01** `iter_col_comments` | a | get_label(i,"C") |
| **O6-S-02** `dated_columns` | a | O0-C-01 |
| **O6-F-01** `exact_comment` | a | strip == sample |
| **O6-F-02** `identity_comment` | a | O0-C-02 |
| **O6-P-01** `new_date` | a | sample_name에서 |
| **O6-P-02** `insert_before_date` | a | date 비교 |
| **O6-P-03** `append_if_no_dated` | a | |
| **O6-P-04** `col_occupied` | a | label nonempty |
| **O6-I-01** `lt_execute_insert` | a | LT_execute GCData |
| **O6-I-02** `insert_if_occupied` | a | |
| **O6-R-01** `resolve_column` | a | 우선순위 exact>identity>insert |

---

## L0 = O7 — Write

| L2 | L3 | L4 |
|----|-----|-----|
| **O7-P-01** `select_gap_policy` | a | default AS_EMPTY |
| **O7-P-02** `prepare_list` | a | O0-S-05 |
| **O7-W-01** `from_list` | a | col_idx, values, comments |
| **O7-W-02** `one_column_h2` | a | 스모크 |
| **O7-W-03** `all_mapping_cols` | a | loop df_col |
| **O7-G-01** `gap_rows_empty` | a | idx 99,100 `""` |
| **O7-G-02** `gap_rows_not_zero` | a | 0.0 아님 |

---

## L0 = O8 — Job

| L2 | L3 | L4 |
|----|-----|-----|
| **O8-C-01** `SampleContext` fields | a | opju,df,sample,identity |
| **O8-C-02** `build_context` | a | validate_mapping |
| **O8-J-01** `gate O2` | a | |
| **O8-J-02** `with OriginSession` | a | |
| **O8-J-03** `open_project` | a | O4 |
| **O8-J-04** `resolve_column once` | a | same col all sheets |
| **O8-J-05** `per_mapping write` | a | O5→O7 |
| **O8-J-06** `save_in_place` | a | |
| **O8-J-07** `collect warnings` | a | partial ok |
| **O8-J-08** `SampleJobResult` | a | counts |
| **O8-J-09** `finally save+exit` | a | |

---

## L0 = O9 — Facade

| L2 | L3 | L4 |
|----|-----|-----|
| **O9-F-01** signature | a | opju,df,sample,* |
| **O9-F-02** call O8 | a | |
| **O9-F-03** `OriginUpdateResult` | a | ok,sheets,rows,warns |
| **O9-F-04** log prefix `[Origin]` | a | |
| **O9-F-05** print 4단계 메시지 | a | 촉매와 동일 UX |
| **O9-E2E-01** real xlsx+opju | a | Ni5_Ce5 샘플 |
| **O9-E2E-02** gap NaN preserved | a | |

---

## 구현·검증 순서 (전체 리프 열거 — 선두 30개)

```
1.  O0-T-01-a-1 … O0-T-04-a-1   (types)
2.  O0-K-01-a-1 … O0-K-02-b-1   (keys)
3.  O0-I-01-a-1 … O0-I-02-b-1   (identity)
4.  O0-C-01-a-1 … O0-C-03-a-1   (comments)
5.  O0-S-01-a-1 … O0-S-06-b-1   (series/gap)
6.  O0-M-01-a-1 … O0-M-03-b-1   (mapping)
7.  O0-L1-K … O0-L1-M → O0      (합본) ✅ 일부 완료
8.  O1-P-01-a-1 …               (O0 PASS + 승인 후)
…
```

**현재 코드:** O0 리프 중 약 **40%** 가 `--o0` 합본 테스트로 커버.  
**다음 리팩터:** 리프마다 `tests/gates/O0_K_01_a_1.py` + `verify --gate`.

---

## 디렉터리 (리프 테스트 분리 목표)

```
data_pc_origin/
  gates/
    registry.py          # 부모 PASS 맵, LOCKED 검사
    O0/
      O0_K_01_a_1.py     # 단일 assert
      ...
    O1/
      ...
  o0_keys.py
  ...
```

---

## 파이프라인 연결 (O9-E2E-02 PASS + 승인)

```python
# 촉매 반응 계산.py — 단 1곳
if not _skip_origin_enabled():
    from data_pc_origin.o9_facade import update_from_dataframe
    update_from_dataframe(...)
```

`DATA_PC_SKIP_ORIGIN=1` 유지 중 — O9 전까지 변경 없음.

---

## 요약 수치

| 레벨 | 개수(설계) |
|------|------------|
| L0 대층 | 10 (O0~O9) |
| L1 모듈 | ~35 |
| L2 함수 | ~90 |
| L3 스텝 | ~180 |
| L4 나노(테스트) | **~250+** |

각 L4 = **정확히 1개 assert** = **1개 verify gate**.
