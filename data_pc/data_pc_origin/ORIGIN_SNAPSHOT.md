# Origin 자동화 스냅샷 — `feat/data-pc-origin`

> **main에 병합하지 않은 백업 브랜치** (2026-06). 문제 시 이 브랜치에서 복구.

## 포함

- `data_pc/data_pc_origin/` — O0~O9 + live harness + 게이트 검증
- `data_pc/촉매 반응 계산.py` — `update_origin()` → `pipeline_bridge.run_origin_update`

## 검증 (repo `data_pc` 기준)

```bash
cd data_pc
python -m data_pc_origin.verify --o9
python -m data_pc_origin.verify --o9-live
```

## Live (Origin·G: 필요)

```bash
set DATA_PC_SKIP_ORIGIN=0
python -m data_pc_origin.live_run "G:\...\실험.opju"
```

## 운영 PC 배치

차헌 PC 실사용 경로는 `Desktop\.cursor\` — 이 브랜치는 **GitHub 백업**; 로컬 `.cursor`와 동기화는 pull/checkout 후 수동 복사 또는 merge 시 반영.
